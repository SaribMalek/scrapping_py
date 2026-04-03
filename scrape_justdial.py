"""
scrape_justdial.py

Dedicated command for scraping Justdial business listings by city and search term,
then storing them in the `justdial_companies` MySQL table.
"""

from __future__ import annotations

import argparse

from config import JUSTDIAL_ALL_BUSINESS_TERMS, JUSTDIAL_DEFAULT_SEARCH_TERMS, SCRAPER_SETTINGS
from database import init_db, save_companies_batch, save_justdial_companies_batch
from scrapers.justdial_scraper import scrape_justdial


def _resolve_search_terms(args) -> list[str]:
    terms = [term.strip() for term in (args.search_term or []) if term and term.strip()]
    if terms:
        return terms
    if args.all_business_types:
        return JUSTDIAL_ALL_BUSINESS_TERMS
    return JUSTDIAL_DEFAULT_SEARCH_TERMS


def main():
    parser = argparse.ArgumentParser(
        description="Scrape Justdial businesses for a city and save them into MySQL."
    )
    parser.add_argument(
        "--city",
        default="Ahmedabad",
        help="City to scrape from Justdial (default: Ahmedabad)",
    )
    parser.add_argument(
        "--search-term",
        action="append",
        help="Business category/search term. Repeat this argument for multiple terms.",
    )
    parser.add_argument(
        "--all-business-types",
        action="store_true",
        help="Scrape a broad preset list of Ahmedabad business categories.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=1,
        help="Maximum Justdial result pages to process per search term (default: 1)",
    )
    parser.add_argument(
        "--listing-url",
        default="",
        help="Optional direct Justdial listing URL. If passed, it is used for the first search term.",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Faster scrape: lower waits, fewer scrolls, and skip company website enrichment.",
    )
    parser.add_argument(
        "--detail-limit",
        type=int,
        default=None,
        help="Maximum number of detail pages to process per search term.",
    )
    parser.add_argument(
        "--max-terms",
        type=int,
        default=None,
        help="Optional cap on how many search terms/categories to process in this run.",
    )
    args = parser.parse_args()

    search_terms = _resolve_search_terms(args)
    if args.max_terms is not None:
        search_terms = search_terms[: max(1, args.max_terms)]

    if args.fast:
        SCRAPER_SETTINGS["page_load_wait"] = min(SCRAPER_SETTINGS.get("page_load_wait", 6), 2)
        SCRAPER_SETTINGS["justdial_scroll_pause"] = min(SCRAPER_SETTINGS.get("justdial_scroll_pause", 2), 1)
        SCRAPER_SETTINGS["justdial_max_scrolls"] = min(SCRAPER_SETTINGS.get("justdial_max_scrolls", 8), 4)
        SCRAPER_SETTINGS["request_timeout"] = min(SCRAPER_SETTINGS.get("request_timeout", 8), 5)
        SCRAPER_SETTINGS["justdial_website_enrich"] = False
        print(
            "[Justdial Command] FAST mode enabled: "
            f"page_load_wait={SCRAPER_SETTINGS['page_load_wait']}, "
            f"scroll_pause={SCRAPER_SETTINGS['justdial_scroll_pause']}, "
            f"max_scrolls={SCRAPER_SETTINGS['justdial_max_scrolls']}, "
            f"website_enrich={SCRAPER_SETTINGS['justdial_website_enrich']}"
        )

    if args.detail_limit is not None:
        SCRAPER_SETTINGS["justdial_detail_limit"] = max(1, args.detail_limit)
        print(f"[Justdial Command] detail_limit={SCRAPER_SETTINGS['justdial_detail_limit']}")

    print("[Justdial Command] Initialising database...")
    init_db()

    total_saved = 0
    for index, term in enumerate(search_terms, start=1):
        print(f"\n[Justdial Command] {index}/{len(search_terms)} - {term} ({args.city})")
        listing_url = args.listing_url if index == 1 else ""
        rows = scrape_justdial(
            city=args.city,
            search_term=term,
            max_pages=max(1, args.max_pages),
            listing_url=listing_url,
        )
        if not rows:
            print(f"[Justdial Command] No rows found for '{term}'.")
            continue

        save_justdial_companies_batch(rows)
        save_companies_batch(
            [
                {
                    "source": "justdial",
                    "company_name": row.get("business_name", ""),
                    "country": "India",
                    "city": row.get("city", ""),
                    "website_url": row.get("website_url") or row.get("detail_url") or "",
                    "phone": row.get("phone", ""),
                    "email": row.get("email", ""),
                }
                for row in rows
            ]
        )
        total_saved += len(rows)
        print(f"[Justdial Command] Saved {len(rows)} rows for '{term}' into justdial_companies and companies.")

    print(f"\n[Justdial Command] Completed. Total saved rows: {total_saved}")


if __name__ == "__main__":
    main()
