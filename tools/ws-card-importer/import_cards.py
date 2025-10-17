#!/usr/bin/env python3
"""Utility to convert Weiss Schwarz card data from CSV into the app's JSON format."""
from __future__ import annotations

import argparse
import csv
import json
import sys
import typing as t
from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError
import io

# Expected CSV headers.
REQUIRED_COLUMNS = {
    "series_id",
    "series_name",
    "set_code",
    "release_year",
    "card_id",
    "card_code",
    "title",
    "rarity",
    "description",
    "color",
    "level",
    "cost",
    "image_url",
}


@dataclass
class SeriesRow:
    id: str
    name: str
    setCode: str
    releaseYear: int


@dataclass
class CardRow:
    id: str
    seriesId: str
    cardCode: str
    title: str
    rarity: str
    description: str
    color: t.Optional[str]
    level: t.Optional[int]
    cost: t.Optional[int]
    imageUrl: t.Optional[str]


@dataclass
class ExportBundle:
    series: t.List[SeriesRow]
    cards: t.List[CardRow]

    def to_json(self, pretty: bool = False) -> str:
        data = {
            "series": [asdict(s) for s in self.series],
            "cards": [asdict(c) for c in self.cards],
        }
        if pretty:
            return json.dumps(data, indent=2, ensure_ascii=False)
        return json.dumps(data, separators=(",", ":"), ensure_ascii=False)


class CsvCardImporter:
    def __init__(self, rows: t.Iterable[t.Mapping[str, str]]):
        self._rows = list(rows)
        if not self._rows:
            raise ValueError("CSV file does not contain any data rows")

    def run(self) -> ExportBundle:
        series_map: dict[str, SeriesRow] = {}
        cards: list[CardRow] = []

        for row in self._rows:
            release_year = _to_int(row.get("release_year"), "release_year")
            level = _to_optional_int(row.get("level"))
            cost = _to_optional_int(row.get("cost"))

            series_id = row["series_id"].strip()
            if series_id not in series_map:
                series_map[series_id] = SeriesRow(
                    id=series_id,
                    name=row["series_name"].strip(),
                    setCode=row["set_code"].strip(),
                    releaseYear=release_year,
                )

            cards.append(
                CardRow(
                    id=row["card_id"].strip(),
                    seriesId=series_id,
                    cardCode=row["card_code"].strip(),
                    title=row["title"].strip(),
                    rarity=row["rarity"].strip(),
                    description=row["description"].strip(),
                    color=_to_optional_str(row.get("color")),
                    level=level,
                    cost=cost,
                    imageUrl=_to_optional_str(row.get("image_url")),
                )
            )

        return ExportBundle(series=list(series_map.values()), cards=cards)


def _load_csv(path: str) -> list[dict[str, str]]:
    if path.startswith("http://") or path.startswith("https://"):
        try:
            with urlopen(path) as response:  # nosec: B310 - trusted source controlled by user
                content_bytes = response.read()
        except URLError as exc:  # pragma: no cover - network error branch
            raise RuntimeError(f"Unable to download CSV from {path}: {exc}") from exc
        content = content_bytes.decode("utf-8-sig")
        stream = io.StringIO(content)
    else:
        csv_path = Path(path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        stream = csv_path.open("r", encoding="utf-8-sig", newline="")

    with stream:
        reader = csv.DictReader(stream)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV file is missing required columns: {', '.join(sorted(missing))}")
        return [t.cast(dict[str, str], row) for row in reader]


def _to_int(value: t.Optional[str], field_name: str) -> int:
    if value is None or not value.strip():
        raise ValueError(f"Field '{field_name}' must not be empty")
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Field '{field_name}' must be an integer (got {value!r})") from exc


def _to_optional_int(value: t.Optional[str]) -> t.Optional[int]:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Expected an integer, got {value!r}") from exc


def _to_optional_str(value: t.Optional[str]) -> t.Optional[str]:
    if value is None:
        return None
    text = value.strip()
    return text or None


def parse_args(argv: t.Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert Weiss Schwarz cards CSV to cards.json")
    parser.add_argument("csv", help="Path or URL to the source CSV file")
    parser.add_argument(
        "--output",
        default=Path("composeApp/src/commonMain/resources/cards.json"),
        type=Path,
        help="Where to write the generated JSON (default: composeApp/src/commonMain/resources/cards.json)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the JSON output",
    )
    return parser.parse_args(argv)


def main(argv: t.Sequence[str]) -> int:
    args = parse_args(argv)
    rows = _load_csv(args.csv)
    bundle = CsvCardImporter(rows).run()
    output_text = bundle.to_json(pretty=args.pretty)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output_text, encoding="utf-8")
    print(f"Wrote {len(bundle.series)} series and {len(bundle.cards)} cards to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
