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

PLUGIN_FIELDNAMES = ["No", "Name", "Type", "Mail"]
CAMPAIGN_FIELDNAMES = ["name", "email", "company", "status"]


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


def _write_plugin_csv(path: str, rows: list[dict], default_type: str = "Subscriber") -> str:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    target_path = path

    plugin_rows = []
    seen_emails = set()
    for row in rows:
        email = (row.get("email") or "").strip()
        company_name = (row.get("company_name") or "").strip()
        if not email or "@" not in email or email.lower() in seen_emails:
            continue
        seen_emails.add(email.lower())
        plugin_rows.append(
            {
                "No": len(plugin_rows) + 1,
                "Name": company_name,
                "Type": default_type,
                "Mail": email,
            }
        )

    def _write_to(dest: str):
        with open(dest, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=PLUGIN_FIELDNAMES)
            writer.writeheader()
            for row in plugin_rows:
                writer.writerow(row)

    try:
        _write_to(target_path)
    except PermissionError:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        root, ext = os.path.splitext(path)
        fallback = f"{root}_{stamp}{ext}"
        print(f"[CSV] File locked: {os.path.abspath(path)}")
        print(f"[CSV] Writing plugin CSV to fallback file instead: {os.path.abspath(fallback)}")
        _write_to(fallback)
        target_path = fallback

    print(f"[CSV] Plugin-ready export: {len(plugin_rows)} rows -> {os.path.abspath(target_path)}")
    return target_path


def _write_campaign_csv(path: str, rows: list[dict], default_status: str = "pending") -> str:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    target_path = path

    campaign_rows = []
    seen_emails = set()
    for row in rows:
        email = (row.get("email") or "").strip()
        company_name = (row.get("company_name") or "").strip()
        if not email or "@" not in email or email.lower() in seen_emails:
            continue
        seen_emails.add(email.lower())
        campaign_rows.append(
            {
                "name": company_name,
                "email": email,
                "company": company_name,
                "status": default_status,
            }
        )

    def _write_to(dest: str):
        with open(dest, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CAMPAIGN_FIELDNAMES)
            writer.writeheader()
            for row in campaign_rows:
                writer.writerow(row)

    try:
        _write_to(target_path)
    except PermissionError:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        root, ext = os.path.splitext(path)
        fallback = f"{root}_{stamp}{ext}"
        print(f"[CSV] File locked: {os.path.abspath(path)}")
        print(f"[CSV] Writing campaign CSV to fallback file instead: {os.path.abspath(fallback)}")
        _write_to(fallback)
        target_path = fallback

    print(f"[CSV] Live-import export: {len(campaign_rows)} rows -> {os.path.abspath(target_path)}")
    return target_path


def _build_campaign_rows(rows: list[dict], default_status: str = "pending") -> list[dict]:
    campaign_rows = []
    seen_emails = set()
    for row in rows:
        email = (row.get("email") or "").strip()
        company_name = (row.get("company_name") or "").strip()
        if not email or "@" not in email or email.lower() in seen_emails:
            continue
        seen_emails.add(email.lower())
        campaign_rows.append(
            {
                "name": company_name,
                "email": email,
                "company": company_name,
                "status": default_status,
            }
        )
    return campaign_rows


def _write_chunked_campaign_csvs(
    out_dir: str,
    rows: list[dict],
    chunk_size: int = 500,
    default_status: str = "pending",
) -> list[str]:
    os.makedirs(out_dir, exist_ok=True)
    campaign_rows = _build_campaign_rows(rows, default_status=default_status)
    if not campaign_rows:
        return []

    written_files = []
    total_chunks = (len(campaign_rows) + chunk_size - 1) // chunk_size
    for index in range(total_chunks):
        start = index * chunk_size
        end = start + chunk_size
        chunk_rows = campaign_rows[start:end]
        chunk_path = os.path.join(out_dir, f"companies_db_import_part_{index + 1:03d}.csv")
        with open(chunk_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CAMPAIGN_FIELDNAMES)
            writer.writeheader()
            for row in chunk_rows:
                writer.writerow(row)
        written_files.append(chunk_path)

    print(
        f"[CSV] Chunked live-import exports: {len(campaign_rows)} rows split into "
        f"{len(written_files)} files at {os.path.abspath(out_dir)}"
    )
    return written_files


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
    plugin_path = os.path.join(out_dir, "companies_emails.csv")
    actual_plugin = _write_plugin_csv(plugin_path, deduped)
    campaign_path = os.path.join(out_dir, "companies_db_import.csv")
    actual_campaign = _write_campaign_csv(campaign_path, deduped)
    chunk_dir = os.path.join(out_dir, "companies_db_import_chunks")
    chunk_files = _write_chunked_campaign_csvs(chunk_dir, deduped, chunk_size=500)

    print(f"[CSV] Clutch: {len(clutch_rows)} rows -> {os.path.abspath(actual_clutch)}")
    print(f"[CSV] GoodFirms: {len(goodfirms_rows)} rows -> {os.path.abspath(actual_goodfirms)}")
    print(f"[CSV] Plugin CSV ready at: {os.path.abspath(actual_plugin)}")
    print(f"[CSV] Live import CSV ready at: {os.path.abspath(actual_campaign)}")
    if chunk_files:
        print(f"[CSV] Chunked live import files ready at: {os.path.abspath(chunk_dir)}")


if __name__ == "__main__":
    export_source_csvs()
