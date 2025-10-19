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

By default the script writes to `composeApp/src/commonMain/resources/cards.json`. When this default
location is used the tool also mirrors the file to `composeApp/src/androidMain/assets/cards.json`
so Android builds include the same dataset. Use `--output` to write elsewhere, and `--pretty` for a
formatted JSON file. The script automatically creates the output directory if it is missing.

When new data becomes available:

1. Prepare or download the CSV file with the headers listed above.
2. Run the importer to regenerate `cards.json`.
3. Commit the updated `cards.json` together with any notes about the source of the data.
4. Rebuild the application to confirm the new cards appear correctly.

If you fetch data directly from the official website, download or export it as CSV before running
the importer. This keeps the script light-weight and avoids depending on fragile HTML scraping.

### Verifying your Python installation

If your machine only provides the `python3` binary, or if module resolution differs between shells,
run the bundled helper to ensure all importer scripts compile cleanly:

```bash
python3 tools/ws-card-importer/verify_compile.py
```

The helper resolves the importer directory automatically so it works regardless of the current
working directory.

## Downloading official datasets

The repository also provides `download_official_cards.py`, a helper that mimics the
official Weiss Schwarz card search flow. The script loads
[`https://ws-tcg.com/cardlist/search/`](https://ws-tcg.com/cardlist/search/) to discover the
same AJAX endpoint used by the website, issues the necessary paginated search requests for
each set code, and finally falls back to the legacy pack export endpoint when needed. The
merged data is written to `cards.json` (mirroring to the Android assets directory when
using the default location):

```bash
python tools/ws-card-importer/download_official_cards.py DDD SFN --pretty
```

The crawler mirrors the JavaScript logic from the site, traverses each card’s dedicated
detail page to capture Japanese names, effect text, and canonical artwork URLs, and prefers
Japanese metadata by default. Supply `--language en` to request English strings when
available. If neither the search API nor the pack export can be reached, the script falls
back to the `offline/` directory. These JSON files contain curated snapshots for each set so
that development can proceed even without internet access. Run the script with `--pretty`
to produce formatted JSON while debugging the crawler output.

### Refreshing offline snapshots

When you successfully download new data (for example from a machine that can reach the
official endpoint), run the helper below to rebuild the offline fallbacks bundled with
the repository:

```bash
python tools/ws-card-importer/refresh_offline_data.py
```

The script rewrites `offline/ddd.json`, `offline/sfn.json`, and prints a summary of the
cards captured for each set. Afterwards, execute `download_official_cards.py` to merge
the refreshed datasets into `cards.json` for the app.
