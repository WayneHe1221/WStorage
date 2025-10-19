#!/usr/bin/env python3
"""Generate curated offline JSON bundles for WS sets when network access is unavailable."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from import_cards import CardRow, ExportBundle, SeriesRow

ROOT = Path(__file__).parent
OFFLINE_DIR = ROOT / "offline"


def parse_table(table: str, series: SeriesRow) -> ExportBundle:
    cards: list[CardRow] = []
    for line in table.strip().splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != 7:
            raise ValueError(f"Expected 7 columns per line, got {len(parts)}: {line}")
        card_code, title, rarity, color, level_text, cost_text, description = parts
        level = None if level_text == "" else int(level_text)
        cost = None if cost_text == "" else int(cost_text)
        card_id = card_code.lower().replace("/", "-")
        family, _, product = series.setCode.partition("/")
        image_code = card_code.replace("/", "-")
        image_url = f"https://ws-tcg.com/wp/wp-content/cardlist/cardimages/{family}/{product}/{image_code}.png"
        cards.append(
            CardRow(
                id=card_id,
                seriesId=series.id,
                cardCode=card_code,
                title=title,
                rarity=rarity,
                description=description,
                color=color or None,
                level=level,
                cost=cost,
                imageUrl=image_url,
            )
        )
    return ExportBundle(series=[series], cards=cards)


def write_bundle(bundle: ExportBundle, filename: str) -> None:
    path = OFFLINE_DIR / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "series": asdict(bundle.series[0]),
        "cards": [asdict(card) for card in bundle.cards],
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(bundle.cards)} cards for {bundle.series[0].name} -> {path}")


if __name__ == "__main__":
    raise SystemExit("This helper is meant to be imported and used from another script")
