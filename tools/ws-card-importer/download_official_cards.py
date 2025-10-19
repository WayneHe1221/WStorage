#!/usr/bin/env python3
"""Download Weiss Schwarz card data from the official site for selected sets."""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path
from typing import Iterable, Sequence
from urllib.error import URLError, HTTPError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from import_cards import CardRow, ExportBundle, SeriesRow, mirror_android_assets_if_applicable

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# Official endpoint observed on the card list website. Each set code such as
# ``DDD`` or ``SFN`` corresponds to a JSON payload that includes the cards in
# that product line.
OFFICIAL_EXPORT_TEMPLATE = "https://ws-tcg.com/wp/wp-content/cardlist/db/export/pack/{set_code}.json"

RARITY_NORMALISATION = {
    "C": "C",
    "U": "U",
    "R": "R",
    "SR": "SR",
    "RR": "SR",
    "RRR": "SP",
    "SEC": "SP",
    "SP": "SP",
    "SSP": "SP",
}

SET_NAME_OVERRIDES: dict[str, str] = {
    "DDD": "ダンダダン / DAN DA DAN",
    "SFN": "葬送のフリーレン / Frieren: Beyond Journey's End",
}


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download Weiss Schwarz card data")
    parser.add_argument(
        "sets",
        nargs="*",
        default=("DDD", "SFN"),
        help="Set codes to download (default: DDD SFN)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("composeApp/src/commonMain/resources/cards.json"),
        help="Destination of the aggregated cards.json file",
    )
    parser.add_argument(
        "--offline-dir",
        type=Path,
        default=Path(__file__).parent / "offline",
        help="Directory containing offline fallbacks (default: tools/ws-card-importer/offline)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the generated JSON",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    bundles = []
    for set_code in args.sets:
        bundle = load_set_bundle(set_code, args.offline_dir)
        bundles.append(bundle)

    merged = merge_bundles(bundles)
    output_text = merged.to_json(pretty=args.pretty)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output_text, encoding="utf-8")
    mirror_android_assets_if_applicable(args.output, output_text)
    print(
        f"Wrote {len(merged.series)} series and {len(merged.cards)} cards to {args.output}",
        file=sys.stderr,
    )
    return 0


def load_set_bundle(set_code: str, offline_dir: Path) -> ExportBundle:
    try:
        return fetch_from_official(set_code)
    except Exception as exc:  # pragma: no cover - network branch
        print(
            f"Warning: could not download set {set_code}: {exc}. Using offline fallback.",
            file=sys.stderr,
        )
        return load_offline_bundle(set_code, offline_dir)


def fetch_from_official(set_code: str) -> ExportBundle:
    url = OFFICIAL_EXPORT_TEMPLATE.format(set_code=set_code)
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urlopen(request, timeout=30) as response:  # nosec: B310 - trusted host provided by user
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:  # pragma: no cover - network branch
        raise RuntimeError(f"HTTP error {error.code} when fetching {url}") from error
    except URLError as error:  # pragma: no cover - network branch
        raise RuntimeError(f"Failed to reach {url}: {error.reason}") from error
    except json.JSONDecodeError as error:  # pragma: no cover - depends on remote data
        raise RuntimeError(f"Invalid JSON payload for {set_code}: {error}") from error

    return parse_official_payload(payload, set_code)


def parse_official_payload(payload: object, set_code: str) -> ExportBundle:
    if isinstance(payload, list):
        cards_raw = payload
        info: dict[str, object] = {}
    elif isinstance(payload, dict):
        info = _first_dict(payload, ["pack", "info", "product", "meta", "header"])
        cards_raw = _extract_cards_array(payload)
    else:
        raise ValueError("Unsupported payload type from official export")

    if not isinstance(cards_raw, list):
        raise ValueError("Card list not found in official payload")

    series_row = build_series_row(info, cards_raw, set_code)
    cards = [
        card
        for raw in cards_raw
        if (card := build_card_row(raw, series_row.id, series_row.setCode)) is not None
    ]

    if not cards:
        raise ValueError(f"No cards could be parsed for set {set_code}")

    return ExportBundle(series=[series_row], cards=cards)


def _extract_cards_array(payload: dict[str, object]) -> object:
    candidates = [
        payload.get("data"),
        payload.get("cards"),
        payload.get("cardList"),
        payload.get("list"),
        payload.get("items"),
    ]
    for candidate in candidates:
        if isinstance(candidate, list):
            return candidate
        if isinstance(candidate, dict):
            nested = _first_dict(candidate, ["items", "rows", "list", "data"])
            if isinstance(nested, list):
                return nested
    return None


def build_series_row(info: dict[str, object], cards_raw: list[object], set_code: str) -> SeriesRow:
    info = info or {}
    title = _first_str(info, ["name", "title", "packTitle", "productName", "product_title"]) or set_code
    set_code_value = (
        _first_str(info, ["setCode", "set_code", "productCode", "product_code", "series", "series_id"])
        or derive_set_code_from_cards(cards_raw, set_code)
    )
    if not isinstance(set_code_value, str):
        set_code_value = str(set_code_value)
    release_year = _extract_year(
        _first_str(info, ["release", "releaseDate", "release_date", "date"])
    )
    if release_year is None:
        release_year = _dt.date.today().year

    set_family = set_code_value.split("/")[0].upper()
    title = SET_NAME_OVERRIDES.get(set_family, title)

    series_id = slugify_series_id(set_code_value)
    return SeriesRow(id=series_id, name=title, setCode=set_code_value, releaseYear=release_year)


def derive_set_code_from_cards(cards_raw: list[object], default: str) -> str:
    for raw in cards_raw:
        if isinstance(raw, dict):
            code = _first_str(raw, ["card_no", "cardNo", "cardCode", "card_code", "number"])
            if code:
                parts = code.split("-")
                if len(parts) >= 2:
                    return f"{parts[0]}/{parts[1]}"
                return code
    return default


def build_card_row(raw: object, series_id: str, set_code: str) -> CardRow | None:
    if not isinstance(raw, dict):
        return None
    card_code = _first_str(raw, ["card_no", "cardNo", "cardCode", "card_code", "number"])
    title = _first_str(raw, ["card_name", "cardName", "name", "title"])
    if not card_code or not title:
        return None

    rarity = normalise_rarity(_first_str(raw, ["rarity", "rare", "rar"]))
    description = build_description(raw)
    color = _first_str(raw, ["color", "colour", "card_color", "attribute"])
    level = parse_optional_int(_first_str(raw, ["level", "lv"]))
    cost = parse_optional_int(_first_str(raw, ["cost", "c"]))
    image_url = _first_str(raw, ["image", "imageUrl", "image_url", "card_image"])
    image_url = normalise_image_url(image_url, card_code, set_code)

    card_id = slugify_card_code(card_code)
    return CardRow(
        id=card_id,
        seriesId=series_id,
        cardCode=card_code,
        title=title.strip(),
        rarity=rarity,
        description=description,
        color=color.upper() if color else None,
        level=level,
        cost=cost,
        imageUrl=image_url,
    )


def normalise_image_url(image_url: str | None, card_code: str, set_code: str) -> str | None:
    if not image_url:
        return build_default_image_url(card_code, set_code)
    image_url = image_url.strip()
    if image_url.startswith("//"):
        return "https:" + image_url
    if image_url.startswith("http://") or image_url.startswith("https://"):
        return image_url
    base = "https://ws-tcg.com/wp/wp-content/cardlist/"
    return urljoin(base, image_url)


def build_default_image_url(card_code: str, set_code: str) -> str:
    sanitized = card_code.replace("/", "-")
    parts = set_code.split("/")
    if len(parts) == 2:
        return f"https://ws-tcg.com/wp/wp-content/cardlist/cardimages/{parts[0]}/{parts[1]}/{sanitized}.png"
    return f"https://ws-tcg.com/wp/wp-content/cardlist/cardimages/{set_code}/{sanitized}.png"


def build_description(raw: dict[str, object]) -> str:
    parts = []
    for key in [
        "ability",
        "ability1",
        "ability2",
        "ability_text",
        "text",
        "effect",
        "flavor",
        "flavor_text",
        "ability_en",
    ]:
        value = _first_str(raw, [key])
        if value:
            stripped = value.strip()
            if stripped and stripped not in parts:
                parts.append(stripped)
    return "\n\n".join(parts) if parts else ""


def normalise_rarity(value: str | None) -> str:
    if not value:
        return "C"
    value = value.strip().upper()
    return RARITY_NORMALISATION.get(value, "R")


def merge_bundles(bundles: Iterable[ExportBundle]) -> ExportBundle:
    series: list[SeriesRow] = []
    cards: list[CardRow] = []
    seen_series: set[str] = set()
    seen_cards: set[tuple[str, str]] = set()

    for bundle in bundles:
        for item in bundle.series:
            if item.id not in seen_series:
                series.append(item)
                seen_series.add(item.id)
        for card in bundle.cards:
            key = (card.id, card.cardCode)
            if key not in seen_cards:
                cards.append(card)
                seen_cards.add(key)

    cards.sort(key=lambda c: (c.seriesId, c.cardCode))
    return ExportBundle(series=series, cards=cards)


def load_offline_bundle(set_code: str, offline_dir: Path) -> ExportBundle:
    path = offline_dir / f"{set_code.lower()}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Offline data for set {set_code!r} not found at {path}"  # pragma: no cover - configuration issue
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    series_data = data.get("series")
    cards_data = data.get("cards", [])
    if not series_data:
        raise ValueError(f"Offline data for {set_code} is missing the series object")
    series = SeriesRow(
        id=series_data["id"],
        name=series_data["name"],
        setCode=series_data["setCode"],
        releaseYear=int(series_data["releaseYear"]),
    )
    cards = [
        CardRow(
            id=item["id"],
            seriesId=item["seriesId"],
            cardCode=item["cardCode"],
            title=item["title"],
            rarity=item["rarity"],
            description=item.get("description", ""),
            color=item.get("color"),
            level=item.get("level"),
            cost=item.get("cost"),
            imageUrl=item.get("imageUrl"),
        )
        for item in cards_data
    ]
    return ExportBundle(series=[series], cards=cards)


def slugify_card_code(card_code: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", card_code.lower())
    return normalized.strip("-")


def slugify_series_id(set_code: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", set_code.lower())
    return normalized.strip("-")


def parse_optional_int(value: str | None) -> int | None:
    if value is None:
        return None
    value = value.strip()
    if not value or value == "-":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _first_str(source: dict[str, object], keys: Iterable[str]) -> str | None:
    for key in keys:
        value = source.get(key)
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
    return None


def _first_dict(source: dict[str, object], keys: Iterable[str]) -> dict[str, object]:
    for key in keys:
        value = source.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _extract_year(value: str | None) -> int | None:
    if not value:
        return None
    match = re.search(r"(20\d{2}|19\d{2})", value)
    if match:
        return int(match.group(1))
    return None


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
