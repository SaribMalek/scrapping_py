"""
export_csv.py - Export company records from DB to CSV.
"""

import csv
import os
from datetime import datetime

from config import CSV_OUTPUT_PATH
from database import get_all_companies

FIELDNAMES = [
    "id",
    "source",
    "company_name",
    "country",
    "city",
    "website_url",
    "phone",
    "email",
    "scraped_at",
]


def _dedupe_rows(rows: list[dict]) -> list[dict]:
    deduped = []
    seen = set()
    for row in rows:
        key = (
            (row.get("source") or "").strip().lower(),
            (row.get("company_name") or "").strip().lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def _write_csv(path: str, rows: list[dict]) -> str:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    target_path = path

    def _write_to(dest: str):
        with open(dest, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            for row in rows:
                row_copy = dict(row)
                if hasattr(row_copy.get("scraped_at"), "strftime"):
                    row_copy["scraped_at"] = row_copy["scraped_at"].strftime("%Y-%m-%d %H:%M:%S")
                filtered = {k: row_copy.get(k, "") for k in FIELDNAMES}
                writer.writerow(filtered)

    try:
        _write_to(target_path)
    except PermissionError:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        root, ext = os.path.splitext(path)
        fallback = f"{root}_{stamp}{ext}"
        print(f"[CSV] File locked: {os.path.abspath(path)}")
        print(f"[CSV] Writing to fallback file instead: {os.path.abspath(fallback)}")
        _write_to(fallback)
        target_path = fallback

    return target_path


def export_to_csv(output_path: str = None):
    """Backward-compatible combined export to one CSV."""
    path = output_path or CSV_OUTPUT_PATH
    rows = get_all_companies()
    if not rows:
        print("[CSV] No data found in database.")
        return

    deduped = _dedupe_rows(rows)
    actual_path = _write_csv(path, deduped)
    print(f"[CSV] Exported {len(deduped)} unique records to: {os.path.abspath(actual_path)}")


def export_source_csvs(base_output_path: str = None):
    """Export separate CSV files for Clutch and GoodFirms."""
    rows = get_all_companies()
    if not rows:
        print("[CSV] No data found in database.")
        return

    deduped = _dedupe_rows(rows)
    base = base_output_path or CSV_OUTPUT_PATH
    out_dir = os.path.dirname(base) or "."

    clutch_rows = [r for r in deduped if (r.get("source") or "").strip().lower() == "clutch"]
    goodfirms_rows = [r for r in deduped if (r.get("source") or "").strip().lower() == "goodfirms"]

    clutch_path = os.path.join(out_dir, "companies_clutch.csv")
    goodfirms_path = os.path.join(out_dir, "companies_goodfirms.csv")

    actual_clutch = _write_csv(clutch_path, clutch_rows)
    actual_goodfirms = _write_csv(goodfirms_path, goodfirms_rows)

    print(f"[CSV] Clutch: {len(clutch_rows)} rows -> {os.path.abspath(actual_clutch)}")
    print(f"[CSV] GoodFirms: {len(goodfirms_rows)} rows -> {os.path.abspath(actual_goodfirms)}")


if __name__ == "__main__":
    export_source_csvs()
