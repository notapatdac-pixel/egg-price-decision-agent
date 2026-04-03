"""
Data ingestion entry points.

- **Egg prices (live):** run `scrape_dit_egg_prices.py` to GET **`exportexcel.php`**
  (tabular export only) from DIT pricelist (กรมการค้าภายใน — pricelist.dit.go.th).

  Example:

      python data/scripts/scrape_dit_egg_prices.py -o data/raw/egg_prices.csv

  Use `--append` to merge without overwriting older rows.
"""
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    raw = root / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    print(f"Raw data directory: {raw}")
    print("For egg prices: python data/scripts/scrape_dit_egg_prices.py -h")


if __name__ == "__main__":
    main()
