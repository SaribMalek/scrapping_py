"""
main.py - Orchestrates the full scraping pipeline.

Default behavior is source-inclusive: if --source is clutch or goodfirms,
both sources are scraped unless --strict-source is provided.
"""

import argparse
import re
import sys
import time
from html import unescape
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup
from config import COUNTRIES, SCRAPER_SETTINGS
from contact_extractor import extract_contacts
from database import (
    get_last_scraped_page,
    init_db,
    save_companies_batch,
    set_last_scraped_page,
)
from export_csv import export_source_csvs
from it_company_filter import filter_it_companies
from scrapers.clutch_scraper import scrape_clutch, _build_driver
from scrapers.goodfirms_scraper import scrape_goodfirms

ALL_SOURCES = ["clutch", "goodfirms"]


def _clean_prefilled_phone(value: str) -> str:
    raw = (value or "").strip()
    if raw in {"-", "--", "N/A", "n/a"}:
        return ""
    digits = re.sub(r"\D", "", raw)
    if len(digits) < 7 or len(digits) > 15:
        return ""
    return raw


def _dedupe_companies(companies: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for company in companies:
        name = (company.get("company_name") or "").strip().lower()
        country = (company.get("country") or "").strip().lower()
        city = (company.get("city") or "").strip().lower()
        website = (company.get("website_url") or "").strip().lower()
        key = website or f"{name}|{city}|{country}"
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(company)
    return out


def _extract_clutch_redirect_target(href: str) -> str:
    try:
        parsed = urlparse(href)
        params = parse_qs(parsed.query)
        target = (params.get("u", [""])[0] or "").strip()
        return target or ""
    except Exception:
        return ""


def _resolve_website_from_clutch_profile_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    selectors = [
        "a.website-link__item[href]",
        "a.provider__cta-link[href]",
        "a[class*='website'][href]",
        "a[title*='Visit'][href]",
    ]
    for selector in selectors:
        for a in soup.select(selector):
            href = (a.get("href") or "").strip()
            if not href:
                continue
            if "r.clutch.co" in href:
                target = _extract_clutch_redirect_target(href)
                if target and target.startswith("http") and "clutch.co" not in target:
                    return target
            if href.startswith("http") and "clutch.co" not in href:
                return href
    return ""


def _extract_email_from_profile_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.select("a[href^='mailto:']"):
        href = (a.get("href") or "").strip()
        mail = unescape(href.split(":", 1)[1].split("?")[0].strip()) if ":" in href else ""
        if "@" in mail:
            return mail
    text = soup.get_text(" ", strip=True)
    m = re.search(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", text)
    return m.group(0) if m else ""


def _extract_phone_from_profile_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    meta_tel = soup.select_one("meta[itemprop='telephone']")
    if meta_tel:
        value = (meta_tel.get("content") or "").strip()
        if value:
            return value
    text = soup.get_text(" ", strip=True)
    m = re.search(r"(?:\+|00)?\d[\d\s().\-]{6,}\d", text)
    return m.group(0).strip() if m else ""


def _enrich_clutch_rows_via_profile_browser(rows: list[dict]):
    """Second pass for Clutch profile URLs to improve missing emails."""
    if not SCRAPER_SETTINGS.get("clutch_profile_enrich", True):
        return

    candidates = [
        row for row in rows
        if "clutch.co/profile/" in (row.get("website_url") or "").lower()
        and not (row.get("email") or "").strip()
    ]
    if not candidates:
        return

    limit = max(0, int(SCRAPER_SETTINGS.get("clutch_profile_enrich_limit", 150)))
    if limit:
        candidates = candidates[:limit]

    print(f"\n  [Clutch Enrich] Profile fallback on {len(candidates)} rows...")
    driver = _build_driver(headless_override=False)
    enriched = 0
    try:
        for idx, row in enumerate(candidates, start=1):
            profile_url = (row.get("website_url") or "").strip()
            try:
                driver.get(profile_url)
                time.sleep(max(2, SCRAPER_SETTINGS.get("page_load_wait", 6)))
                source = driver.page_source or ""
                if "just a moment" in source.lower() and "cloudflare" in source.lower():
                    continue

                p = _extract_phone_from_profile_html(source)
                e = _extract_email_from_profile_html(source)
                external = _resolve_website_from_clutch_profile_html(source)

                if external and (not p or not e):
                    p2, e2 = extract_contacts(external)
                    if p2:
                        p = p2
                    if e2:
                        e = e2
                    row["website_url"] = external

                if p and not row.get("phone"):
                    row["phone"] = _clean_prefilled_phone(p) or row.get("phone", "")
                if e and not row.get("email"):
                    row["email"] = e
                    enriched += 1

                if idx % 20 == 0:
                    print(f"  [Clutch Enrich] Processed {idx}/{len(candidates)}...")
            except Exception:
                continue
    finally:
        try:
            driver.quit()
        except Exception:
            pass

    print(f"  [Clutch Enrich] Added emails for {enriched} rows.")


def process_companies(source: str, companies: list, workers: int):
    """Extract contact info in parallel and save results in one DB batch."""
    companies = _dedupe_companies(companies)
    companies, dropped = filter_it_companies(companies, source=source)
    if dropped:
        print(f"  [IT FILTER] Dropped {len(dropped)} non-IT rows before processing.")
    total = len(companies)
    if total == 0:
        print("  No unique companies to process.")
        return

    workers = max(1, workers)
    print(f"  Processing {total} unique companies with {workers} workers...\n")

    contact_cache: dict[str, tuple[str, str]] = {}

    def task(company: dict) -> dict:
        name = company.get("company_name", "")
        url = company.get("website_url", "")
        country = company.get("country", "")
        city = company.get("city", "")
        base_phone = _clean_prefilled_phone(company.get("phone", "") or "")
        base_email = company.get("email", "") or ""

        phone, email = base_phone, base_email
        if url:
            try:
                if url in contact_cache:
                    p2, e2 = contact_cache[url]
                else:
                    p2, e2 = extract_contacts(url)
                    contact_cache[url] = (p2, e2)
                if p2:
                    phone = p2
                if e2:
                    email = e2
            except Exception:
                pass

        return {
            "source": source,
            "company_name": name,
            "country": country,
            "city": city,
            "website_url": url,
            "phone": phone,
            "email": email,
        }

    rows = []
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(task, company): company for company in companies}
        for future in as_completed(futures):
            company = futures[future]
            name = company.get("company_name", "")
            url = company.get("website_url", "")

            try:
                row = future.result()
                rows.append(row)
                if row.get("phone") or row.get("email"):
                    status = f"Phone: {row.get('phone') or 'N/A'} | Email: {row.get('email') or 'N/A'}"
                else:
                    status = "No contact info found"
            except Exception as e:
                row = {
                    "source": source,
                    "company_name": name,
                    "country": company.get("country", ""),
                    "city": company.get("city", ""),
                    "website_url": url,
                    "phone": "",
                    "email": "",
                }
                rows.append(row)
                status = f"Error: {e}"

            done += 1
            print(f"  [{done}/{total}] {name} - {status}")

    if source == "clutch":
        _enrich_clutch_rows_via_profile_browser(rows)

    save_companies_batch(rows)
    print(f"\n  Saved {len(rows)} records to database.")


def run_source_country(source: str, country: str, max_pages: int, workers: int, start_page: int = 1):
    print(f"\n{'='*60}")
    print(f"  Source: {source.upper()} | Country: {country}")
    print(f"{'='*60}")

    requested_end_page = max(1, max_pages)
    resume_enabled = SCRAPER_SETTINGS.get("resume_pages", True) and start_page == 1
    last_saved_page = get_last_scraped_page(source, country) if resume_enabled else 0

    effective_start = max(1, start_page)
    if resume_enabled and last_saved_page > 0:
        effective_start = max(effective_start, last_saved_page + 1)

    if effective_start > requested_end_page:
        print(
            f"[MAIN] Skipping {source}/{country}: already scraped up to page {last_saved_page}, "
            f"requested end page is {requested_end_page}."
        )
        return

    pages_to_scrape = requested_end_page - effective_start + 1
    last_page_hit = {"value": 0}

    def progress_cb(page_num: int, company_count: int):
        if company_count > 0:
            last_page_hit["value"] = max(last_page_hit["value"], page_num)
            # Persist progress per page so interrupted runs can resume correctly.
            set_last_scraped_page(source, country, last_page_hit["value"])

    print(
        f"[MAIN] Page plan for {source}/{country}: start={effective_start}, "
        f"end={requested_end_page}, count={pages_to_scrape}"
    )

    if source == "clutch":
        companies = scrape_clutch(
            country=country,
            max_pages=pages_to_scrape,
            start_page=effective_start,
            progress_callback=progress_cb,
        )
    elif source == "goodfirms":
        companies = scrape_goodfirms(
            country=country,
            max_pages=pages_to_scrape,
            start_page=effective_start,
            progress_callback=progress_cb,
        )
    else:
        print(f"[ERROR] Unknown source: {source}")
        return

    if not companies:
        print(f"  No companies found for {country} on {source}.")
        return

    process_companies(source=source, companies=companies, workers=workers)
    if last_page_hit["value"] > 0:
        set_last_scraped_page(source, country, last_page_hit["value"])
        print(f"[MAIN] Saved progress {source}/{country}: page {last_page_hit['value']}")


def _resolve_sources(source_arg: str | None, strict_source: bool = False) -> list[str]:
    if source_arg in (None, "both"):
        return ALL_SOURCES
    if not strict_source and source_arg in ("clutch", "goodfirms"):
        print(
            "[MAIN] Source-inclusive mode: scraping BOTH sources. "
            "Use --strict-source to scrape only the selected source."
        )
        return ALL_SOURCES
    return [source_arg]


def main():
    parser = argparse.ArgumentParser(description="Web scraper for Clutch.co and GoodFirms.co")
    parser.add_argument(
        "--source",
        choices=["clutch", "goodfirms", "both"],
        default="both",
        help="Which site to scrape (default: both)",
    )
    parser.add_argument("--country", type=str, help="Country name to filter (e.g. 'India')")
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum pages to scrape per country (default from config)",
    )
    parser.add_argument(
        "--start-page",
        type=int,
        default=1,
        help="Starting page number for pagination (default: 1)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=SCRAPER_SETTINGS.get("contact_workers", 8),
        help="Parallel workers for contact extraction (default from config or 8)",
    )
    parser.add_argument(
        "--strict-source",
        action="store_true",
        help="Scrape only the selected --source (disable source-inclusive mode).",
    )
    parser.add_argument("--all", action="store_true", help="Scrape all countries from selected source(s)")
    parser.add_argument("--export-csv", action="store_true", help="Export results to CSV after scraping")
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Faster run: lower waits, more workers, and no deep contact-page crawling.",
    )
    args = parser.parse_args()

    max_pages = args.max_pages or SCRAPER_SETTINGS.get("max_pages_per_country", 10)
    start_page = max(1, args.start_page)
    workers = max(1, args.workers)

    if args.fast:
        SCRAPER_SETTINGS["page_load_wait"] = min(SCRAPER_SETTINGS.get("page_load_wait", 6), 3)
        SCRAPER_SETTINGS["between_requests"] = min(SCRAPER_SETTINGS.get("between_requests", 3), 1)
        SCRAPER_SETTINGS["request_timeout"] = min(SCRAPER_SETTINGS.get("request_timeout", 8), 6)
        SCRAPER_SETTINGS["max_retries"] = 1
        SCRAPER_SETTINGS["deep_contact_lookup"] = False
        SCRAPER_SETTINGS["contact_request_delay"] = 0
        workers = max(workers, 16)
        print(
            f"[MAIN] FAST mode enabled: workers={workers}, page_load_wait={SCRAPER_SETTINGS['page_load_wait']}, "
            f"between_requests={SCRAPER_SETTINGS['between_requests']}, request_timeout={SCRAPER_SETTINGS['request_timeout']}"
        )

    print("[MAIN] Initialising database...")
    init_db()

    target_sources = _resolve_sources(args.source, strict_source=args.strict_source)

    if args.all:
        for source in target_sources:
            for country in COUNTRIES:
                try:
                    run_source_country(source, country, max_pages, workers, start_page=start_page)
                except Exception as e:
                    print(f"[ERROR] Failed for {source}/{country}: {e}")
                    continue
    elif args.country:
        for source in target_sources:
            try:
                run_source_country(source, args.country, max_pages, workers, start_page=start_page)
            except Exception as e:
                print(f"[ERROR] Failed for {source}/{args.country}: {e}")
                continue
    elif args.source:
        for source in target_sources:
            for country in COUNTRIES:
                try:
                    run_source_country(source, country, max_pages, workers, start_page=start_page)
                except Exception as e:
                    print(f"[ERROR] Failed for {source}/{country}: {e}")
                    continue
    else:
        parser.print_help()
        sys.exit(0)

    if args.export_csv:
        print("\n[MAIN] Exporting results to source-wise CSV files...")
        export_source_csvs()
        print("[MAIN] Done! Check 'output/companies_clutch.csv' and 'output/companies_goodfirms.csv'.")


if __name__ == "__main__":
    main()
