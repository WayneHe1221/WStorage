#!/usr/bin/env python3
"""Entry point for refreshing the local Weiss Schwarz card dataset."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _import_importer_modules():
    """Ensure the importer package is on ``sys.path`` and import its helpers."""

    importer_dir = Path(__file__).resolve().parent / "ws-card-importer"
    if str(importer_dir) not in sys.path:
        sys.path.insert(0, str(importer_dir))

    from download_official_cards import load_set_bundle, merge_bundles
    from import_cards import mirror_android_assets_if_applicable

    return importer_dir, load_set_bundle, merge_bundles, mirror_android_assets_if_applicable


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Download Weiss Schwarz card data for the configured sets and refresh "
            "the application's bundled dataset."
        )
    )
    parser.add_argument(
        "sets",
        nargs="*",
        default=("DDD", "SFN"),
        help="Set codes to download (default: DDD SFN)",
    )
    default_output = (
        Path(__file__).resolve().parents[1]
        / "composeApp"
        / "src"
        / "commonMain"
        / "resources"
        / "cards.json"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
        help=(
            "Destination of the aggregated cards.json file (default: "
            "composeApp/src/commonMain/resources/cards.json)"
        ),
    )
    parser.add_argument(
        "--language",
        default="ja",
        help="Language code for crawler detail pages (default: ja)",
    )
    parser.add_argument(
        "--offline-dir",
        type=Path,
        help="Directory containing offline fallbacks (default: tools/ws-card-importer/offline)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the generated JSON",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    importer_dir, load_set_bundle, merge_bundles, mirror_android_assets_if_applicable = (
        _import_importer_modules()
    )
    args = parse_args(argv)
    offline_dir = args.offline_dir or (importer_dir / "offline")

    bundles = []
    for set_code in args.sets:
        bundle = load_set_bundle(set_code, offline_dir=offline_dir, language=args.language)
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


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

