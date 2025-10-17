# Weiss Schwarz Card Importer

A small Python utility that converts Weiss Schwarz card information from a CSV file into
`cards.json`, the data file consumed by the app. The script is designed for datasets that are
hand-curated or exported from the official website.

## CSV format

The importer expects the CSV to use UTF-8 encoding with the following headers:

| Column         | Description |
| -------------- | ----------- |
| `series_id`    | Unique identifier for the series (lowercase with dashes recommended). |
| `series_name`  | Human-readable series title. |
| `set_code`     | Set code such as `SAO/S100`. |
| `release_year` | Year the set was released, as an integer. |
| `card_id`      | Stable identifier for the card. |
| `card_code`    | Printed card number, e.g. `SAO/S100-001`. |
| `title`        | Card name displayed in-game. |
| `rarity`       | Rarity string (`C`, `U`, `R`, `SR`, `SP`, etc.). |
| `description`  | Free-form description text. |
| `color`        | Card color (`YELLOW`, `BLUE`, etc.). Leave blank if unknown. |
| `level`        | Card level as an integer. Leave blank if the card has no level. |
| `cost`         | Play cost as an integer. Leave blank if the card has no cost. |
| `image_url`    | Direct link to the official card image. |

See [`sample_cards.csv`](./sample_cards.csv) for an example.

## Usage

From the project root:

```bash
python tools/ws-card-importer/import_cards.py tools/ws-card-importer/sample_cards.csv
```

By default the script writes to `composeApp/src/commonMain/resources/cards.json`. Use `--output`
to write elsewhere, and `--pretty` for a formatted JSON file. The script automatically creates the
output directory if it is missing.

When new data becomes available:

1. Prepare or download the CSV file with the headers listed above.
2. Run the importer to regenerate `cards.json`.
3. Commit the updated `cards.json` together with any notes about the source of the data.
4. Rebuild the application to confirm the new cards appear correctly.

If you fetch data directly from the official website, download or export it as CSV before running
the importer. This keeps the script light-weight and avoids depending on fragile HTML scraping.
