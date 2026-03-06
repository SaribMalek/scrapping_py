"""
cleanup_it_data.py - Remove non-IT rows from existing DB data and regenerate CSVs.
"""

from __future__ import annotations

import argparse

from database import get_all_companies, get_connection, init_db
from export_csv import export_source_csvs, export_to_csv
from it_company_filter import filter_it_companies


def _delete_ids(ids: list[int], chunk_size: int = 500) -> int:
    if not ids:
        return 0

    deleted = 0
    conn = get_connection()
    cursor = conn.cursor()
    try:
        for i in range(0, len(ids), chunk_size):
            chunk = ids[i : i + chunk_size]
            placeholders = ",".join(["%s"] * len(chunk))
            sql = f"DELETE FROM companies WHERE id IN ({placeholders})"
            cursor.execute(sql, chunk)
            deleted += cursor.rowcount or 0
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return deleted


def main():
    parser = argparse.ArgumentParser(
        description="Clean existing companies data by removing clearly non-IT records."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without deleting anything.",
    )
    args = parser.parse_args()

    init_db()
    rows = get_all_companies()
    if not rows:
        print("[CLEANUP] No rows found in database.")
        return

    kept, dropped = filter_it_companies(rows)
    print(f"[CLEANUP] Total rows: {len(rows)}")
    print(f"[CLEANUP] Keep rows:  {len(kept)}")
    print(f"[CLEANUP] Drop rows:  {len(dropped)}")

    if dropped:
        print("[CLEANUP] Sample dropped rows:")
        for row in dropped[:20]:
            print(
                f"  id={row.get('id')} | {row.get('source')} | "
                f"{row.get('company_name')} | reason={row.get('_it_filter_reason')}"
            )

    if args.dry_run:
        print("[CLEANUP] Dry run complete. No DB changes applied.")
        return

    to_delete = [int(r["id"]) for r in dropped if r.get("id") is not None]
    deleted = _delete_ids(to_delete)
    print(f"[CLEANUP] Deleted rows: {deleted}")

    print("[CLEANUP] Regenerating CSV exports...")
    export_to_csv()
    export_source_csvs()
    print("[CLEANUP] Done.")


if __name__ == "__main__":
    main()
