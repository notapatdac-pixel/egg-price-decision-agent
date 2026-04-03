"""
Download egg price **data** from Thailand DIT pricelist (https://pricelist.dit.go.th).

Uses a single GET to **exportexcel.php** (official tabular export the site uses for Excel).
This returns a small HTML table payload only — **not** the full main_price.php report page.

Query params use Buddhist Era dates: from/to as **dd/mm/BBBB**.

Defaults: retail ไข่ไก่ เบอร์ 2 → product_id **P11027** (override with --product-id).

Output CSV (data/raw/egg_prices.csv style):
- date (ISO Gregorian), price_thb_per_egg, price_thb_per_kg (estimated), region, source,
  product_id, price_range_thb, product_name_th, unit_th
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

DEFAULT_BASE = "https://pricelist.dit.go.th"
DEFAULT_PROTYPE = "1"
DEFAULT_PROGROUP = "P11000"
DEFAULT_PRODUCT = "P11027"

_THAI_MONTHS = {
    "ม.ค.": 1,
    "ก.พ.": 2,
    "มี.ค.": 3,
    "เม.ย.": 4,
    "พ.ค.": 5,
    "มิ.ย.": 6,
    "ก.ค.": 7,
    "ส.ค.": 8,
    "ก.ย.": 9,
    "ต.ค.": 10,
    "พ.ย.": 11,
    "ธ.ค.": 12,
}


def _gregorian_to_be_str(d: date) -> str:
    be_year = d.year + 543
    return f"{d.day:02d}/{d.month:02d}/{be_year}"


def _parse_thai_display_date(cell: str) -> date | None:
    cell = " ".join(cell.split())
    m = re.match(r"^(\d{1,2})\s+(.+?)\s+(\d{4})$", cell)
    if not m:
        return None
    _day_s, mon_token, year_s = m.groups()
    day = int(_day_s)
    be_year = int(year_s)
    mon_key = mon_token.strip()
    if mon_key not in _THAI_MONTHS:
        for k in _THAI_MONTHS:
            if mon_key.startswith(k.rstrip(".")):
                mon_key = k
                break
        else:
            return None
    month = _THAI_MONTHS[mon_key]
    g_year = be_year - 543
    try:
        return date(g_year, month, day)
    except ValueError:
        return None


def _parse_float_cell(text: str) -> float | None:
    text = text.replace("\xa0", " ").strip()
    if not text or text == "-":
        return None
    m = re.search(r"(\d+(?:\.\d+)?)", text.replace(",", ""))
    return float(m.group(1)) if m else None


def fetch_export_document(
    base_url: str,
    day1_be: str,
    day2_be: str,
    protype: str,
    progroup: str,
    proname: str,
    seltime: str,
    timeout: int,
) -> str:
    """GET exportexcel.php — tabular data only (no main_price.php UI)."""
    url = f"{base_url.rstrip('/')}/exportexcel.php"
    params = {
        "settime": seltime,
        "from": day1_be,
        "to": day2_be,
        "type": protype,
        "group": progroup,
        "name": proname,
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; EggPriceDecisionAgent/1.0)",
        "Accept-Language": "th,en;q=0.9",
    }
    r = requests.get(url, params=params, headers=headers, timeout=timeout)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or "utf-8"
    return r.text


def parse_export_table(html: str, egg_grams: float) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return []

    rows_out: list[dict] = []
    for tr in table.find_all("tr"):
        cells = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
        if len(cells) < 7:
            continue
        # Header row: first cell is วันที่
        if "วันที่" in cells[0] or cells[0].lower() == "date":
            continue

        d = _parse_thai_display_date(cells[0])
        if d is None:
            continue

        product_name, unit = cells[2], cells[3]
        low = _parse_float_cell(cells[4])
        high = _parse_float_cell(cells[5])
        avg = _parse_float_cell(cells[6])
        if avg is None:
            continue

        range_text = (
            f"{low} - {high}" if low is not None and high is not None else cells[4] + " - " + cells[5]
        )
        kg_est = round(avg * (1000.0 / egg_grams), 2) if egg_grams > 0 else None

        rows_out.append(
            {
                "date": d.isoformat(),
                "price_thb_per_kg": kg_est,
                "price_thb_per_egg": avg,
                "price_range_thb": range_text.strip(),
                "product_name_th": product_name,
                "unit_th": unit,
            }
        )
    return rows_out


def run(
    output: Path,
    base_url: str,
    day1_be: str,
    day2_be: str,
    protype: str,
    progroup: str,
    proname: str,
    seltime: str,
    egg_grams: float,
    timeout: int,
    append: bool,
) -> int:
    html = fetch_export_document(
        base_url, day1_be, day2_be, protype, progroup, proname, seltime, timeout
    )
    rows = parse_export_table(html, egg_grams)
    if not rows:
        print(
            "No rows parsed from export. Check BE dates (dd/mm/BBBB), product id, and site.",
            file=sys.stderr,
        )
        return 2

    region = "bangkok_retail" if protype == "1" else "bangkok_wholesale"
    for r in rows:
        r["region"] = region
        r["source"] = "dit_exportexcel"
        r["product_id"] = proname

    new_df = pd.DataFrame(rows)
    cols = [
        "date",
        "price_thb_per_kg",
        "price_thb_per_egg",
        "region",
        "source",
        "product_id",
        "price_range_thb",
        "product_name_th",
        "unit_th",
    ]
    new_df = new_df[[c for c in cols if c in new_df.columns]]

    output.parent.mkdir(parents=True, exist_ok=True)
    if append and output.exists():
        old = pd.read_csv(output)
        merged = pd.concat([old, new_df], ignore_index=True)
        merged = merged.drop_duplicates(subset=["date", "product_id"], keep="last")
        merged = merged.sort_values("date")
        merged.to_csv(output, index=False)
        print(f"Wrote {len(merged)} rows to {output} (merged)")
    else:
        new_df = new_df.drop_duplicates(subset=["date", "product_id"], keep="last")
        new_df = new_df.sort_values("date")
        new_df.to_csv(output, index=False)
        print(f"Wrote {len(new_df)} rows to {output}")
    return 0


def main() -> None:
    p = argparse.ArgumentParser(
        description="Download DIT egg prices via exportexcel.php (tabular export, not full HTML page)."
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "raw" / "egg_prices.csv",
        help="Output CSV path",
    )
    p.add_argument("--base-url", default=DEFAULT_BASE)
    p.add_argument(
        "--day1",
        help="Start dd/mm/BBBB (BE). Default: ~90 days ago (BE).",
    )
    p.add_argument(
        "--day2",
        help="End dd/mm/BBBB (BE). Default: today (BE).",
    )
    p.add_argument("--protype", default=DEFAULT_PROTYPE, help="1=ขายปลีก, 2=ขายส่ง")
    p.add_argument("--progroup", default=DEFAULT_PROGROUP)
    p.add_argument("--product-id", default=DEFAULT_PRODUCT, dest="proname")
    p.add_argument(
        "--seltime",
        default="day",
        choices=("day", "week", "month", "quarter", "year"),
    )
    p.add_argument(
        "--egg-grams",
        type=float,
        default=58.0,
        help="Avg egg mass (g) to estimate THB/kg from THB/egg",
    )
    p.add_argument("--timeout", type=int, default=60)
    p.add_argument(
        "--append",
        action="store_true",
        help="Merge with existing CSV (dedupe on date+product_id)",
    )
    args = p.parse_args()

    today = date.today()
    day2_be = args.day2 or _gregorian_to_be_str(today)
    if args.day1:
        day1_be = args.day1
    else:
        d1 = date.fromordinal(today.toordinal() - 90)
        day1_be = _gregorian_to_be_str(d1)

    sys.exit(
        run(
            args.output,
            args.base_url,
            day1_be,
            day2_be,
            args.protype,
            args.progroup,
            args.proname,
            args.seltime,
            args.egg_grams,
            args.timeout,
            args.append,
        )
    )


if __name__ == "__main__":
    main()
