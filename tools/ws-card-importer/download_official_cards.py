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
from urllib.request import Request, urlopen

from cardlist_search import CardSearchClient, CardSearchError
from card_page import CardPageFetchError, CardPageFetcher
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


_SEARCH_CLIENT: CardSearchClient | object | None = None
_SEARCH_CLIENT_FAILED = object()
_CARD_PAGE_FETCHER: CardPageFetcher | object | None = None
_CARD_PAGE_FETCHER_FAILED = object()


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
        "--language",
        default="ja",
        help="Language code used for the search crawler (default: ja for Japanese)",
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
    language = (args.language or "ja").strip() or "ja"
    bundles = []
    for set_code in args.sets:
        bundle = load_set_bundle(set_code, args.offline_dir, language)
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


def load_set_bundle(set_code: str, offline_dir: Path, language: str) -> ExportBundle:
    search_error: Exception | None = None
    try:
        return fetch_from_search(set_code, language)
    except CardSearchError as exc:
        search_error = exc
        print(
            f"Warning: search crawler failed for {set_code}: {exc}. Falling back to export.",
            file=sys.stderr,
        )
    except Exception as exc:  # pragma: no cover - unexpected runtime error
        search_error = exc
        print(
            f"Warning: unexpected search error for {set_code}: {exc}. Falling back to export.",
            file=sys.stderr,
        )

    try:
        return fetch_from_official(set_code)
    except Exception as exc:  # pragma: no cover - network branch
        if search_error:
            print(
                f"Note: card search also failed for {set_code}: {search_error}",
                file=sys.stderr,
            )
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


def fetch_from_search(set_code: str, language: str) -> ExportBundle:
    client = _ensure_search_client()
    try:
        result = client.fetch_cards(set_code, language=language)
    except CardSearchError:
        raise

    info = dict(result.info or {})
    cards_raw = list(result.cards)
    series_row = build_series_row(info, cards_raw, set_code)
    detail_language = _normalise_detail_language(language)
    fetcher = _ensure_card_page_fetcher()
    cards: list[CardRow] = []
    for raw in cards_raw:
        card = build_card_row(
            raw,
            series_row.id,
            series_row.setCode,
            detail_fetcher=fetcher,
            detail_language=detail_language,
        )
        if card is not None:
            cards.append(card)
    if not cards:
        raise CardSearchError(f"Search data for set {set_code} did not include any cards")
    return ExportBundle(series=[series_row], cards=cards)


def _ensure_search_client() -> CardSearchClient:
    global _SEARCH_CLIENT
    if isinstance(_SEARCH_CLIENT, CardSearchClient):
        return _SEARCH_CLIENT
    if _SEARCH_CLIENT is _SEARCH_CLIENT_FAILED:
        raise CardSearchError("Card search crawler initialisation previously failed")
    try:
        client = CardSearchClient(user_agent=USER_AGENT)
    except CardSearchError as error:
        _SEARCH_CLIENT = _SEARCH_CLIENT_FAILED
        raise
    _SEARCH_CLIENT = client
    return client


def _ensure_card_page_fetcher() -> CardPageFetcher:
    global _CARD_PAGE_FETCHER
    if isinstance(_CARD_PAGE_FETCHER, CardPageFetcher):
        return _CARD_PAGE_FETCHER
    if _CARD_PAGE_FETCHER is _CARD_PAGE_FETCHER_FAILED:
        raise CardPageFetchError("Card detail fetcher initialisation previously failed")
    try:
        fetcher = CardPageFetcher(user_agent=USER_AGENT)
    except CardPageFetchError:
        _CARD_PAGE_FETCHER = _CARD_PAGE_FETCHER_FAILED
        raise
    _CARD_PAGE_FETCHER = fetcher
    return fetcher


def _normalise_detail_language(language: str) -> str:
    lang = (language or "").strip().lower()
    if lang in {"", "ja", "jp", "japanese"}:
        return "ja"
    return lang


def _disable_card_page_fetcher() -> None:
    global _CARD_PAGE_FETCHER
    _CARD_PAGE_FETCHER = _CARD_PAGE_FETCHER_FAILED


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


def build_card_row(
    raw: object,
    series_id: str,
    set_code: str,
    *,
    detail_fetcher: CardPageFetcher | None = None,
    detail_language: str = "ja",
) -> CardRow | None:
    if not isinstance(raw, dict):
        return None
    card_code = _first_str(raw, ["card_no", "cardNo", "cardCode", "card_code", "number"])
    title = _first_str(raw, ["card_name", "cardName", "name", "title"])
    if not card_code or not title:
        return None

    rarity = normalise_rarity(_first_str(raw, ["rarity", "rare", "rar"]))
    description = build_description(raw)
    effect_text: str | None = None
    color = _first_str(raw, ["color", "colour", "card_color", "attribute"])
    level = parse_optional_int(_first_str(raw, ["level", "lv"]))
    cost = parse_optional_int(_first_str(raw, ["cost", "c"]))
    image_url = _first_str(raw, ["image", "imageUrl", "image_url", "card_image"])
    detail = None
    if detail_fetcher is not None:
        try:
            detail = detail_fetcher.fetch(card_code, language=detail_language)
        except CardPageFetchError as exc:
            print(
                f"Warning: failed to fetch detail page for {card_code}: {exc}",
                file=sys.stderr,
            )
            _disable_card_page_fetcher()
    if detail is not None:
        if detail.title:
            title = detail.title
        if detail.effect:
            effect_text = detail.effect.strip()
            description = merge_descriptions(detail.effect, description)
        if detail.image_url:
            image_url = detail.image_url
    if effect_text is None:
        effect_text = description or None
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
        effect=effect_text,
    )


def merge_descriptions(primary: str, secondary: str) -> str:
    primary = (primary or "").strip()
    secondary = (secondary or "").strip()
    if not primary:
        return secondary
    if not secondary:
        return primary
    if primary == secondary:
        return primary
    if secondary in primary:
        return primary
    parts = [primary]
    if secondary and secondary not in parts:
        parts.append(secondary)
    return "\n\n".join(part for part in parts if part)


def normalise_image_url(image_url: str | None, card_code: str, set_code: str) -> str | None:
    canonical_url = build_default_image_url(card_code, set_code)
    if not image_url:
        return canonical_url
    image_url = image_url.strip()
    if not image_url:
        return canonical_url
    if image_url.startswith("//"):
        image_url = "https:" + image_url
    if image_url.startswith("http://") or image_url.startswith("https://"):
        if "/cardlist/cardimages/" in image_url:
            return canonical_url
        return image_url
    return canonical_url


def build_default_image_url(card_code: str, set_code: str) -> str:
    set_slug = _slugify_set_code(set_code)
    card_slug = _slugify_card_code(card_code)
    prefix = _first_alpha(set_slug) if set_slug else "card"
    return (
        "https://ws-tcg.com/wordpress/wp-content/images/cardlist/"
        f"{prefix}/{set_slug}/{card_slug}.png"
    )


def _slugify_set_code(set_code: str) -> str:
    value = set_code.lower().strip()
    value = value.replace("/", "_")
    return _collapse_identifier(value)


def _slugify_card_code(card_code: str) -> str:
    value = card_code.lower().strip()
    value = value.replace("/", "_").replace("-", "_")
    return _collapse_identifier(value)


def _collapse_identifier(value: str) -> str:
    value = re.sub(r"[^0-9a-z_]+", "_", value)
    value = re.sub(r"_+", "_", value)
    return value.strip("_")


def _first_alpha(value: str) -> str:
    for char in value:
        if char.isalpha():
            return char
    return value[0] if value else "card"


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
            effect=item.get("effect"),
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
