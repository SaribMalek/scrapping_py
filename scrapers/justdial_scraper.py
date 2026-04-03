"""
scrapers/justdial_scraper.py

Scrapes Justdial listing pages for a city + search term combination and returns
business details suitable for database persistence.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import re
import time
import urllib.parse

import requests
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from contact_extractor import extract_contacts, extract_contacts_from_html
from config import HEADERS, SCRAPER_SETTINGS

JUSTDIAL_HOME_URL = "https://www.justdial.com"
_LISTING_BLOCK_SELECTORS = [
    "[data-testid*='listing']",
    "[class*='resultbox']",
    "[class*='resultBox']",
    "[class*='listing_card']",
    "[class*='cardWrapper']",
    "[class*='results_card']",
]
_DETAIL_LINK_PATTERNS = (
    "_BZDET",
    "/Ahmedabad/",
    "/search",
)
_BLOCKED_EXTERNAL_HOST_TOKENS = (
    "zomato.",
    "swiggy.",
    "magicpin.",
    "dineout.",
    "eazydiner.",
    "tripadvisor.",
    "justdial.",
    "facebook.",
    "instagram.",
    "youtube.",
    "linkedin.",
    "wa.me",
    "whatsapp.",
    "goo.gl",
    "g.page",
    "google.",
)
_GENERIC_NAME_PATTERNS = (
    "follow us on",
    "popular ",
    "travel guide",
    "are you ",
    "currently showing",
    "unveiling the",
    "learn to ",
    "justdial - ",
    "all specialists",
    "home decor",
    "repairs services",
    "education",
    "contractors",
    "hospitals",
    "courier",
    "caterer",
)


class SafeChrome(uc.Chrome):
    def __del__(self):
        try:
            self.quit()
        except Exception:
            pass


def _build_driver(headless_override=None):
    options = uc.ChromeOptions()
    headless = (
        SCRAPER_SETTINGS.get("headless", False)
        if headless_override is None
        else headless_override
    )
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    max_tries = 3
    for attempt in range(1, max_tries + 1):
        try:
            return SafeChrome(
                options=options,
                version_main=SCRAPER_SETTINGS["chrome_version"],
            )
        except OSError as e:
            if getattr(e, "winerror", None) != 183 or attempt == max_tries:
                raise
            uc_target = os.path.join(
                os.environ.get("APPDATA", ""),
                "undetected_chromedriver",
                "undetected_chromedriver.exe",
            )
            try:
                if os.path.exists(uc_target):
                    os.remove(uc_target)
            except OSError:
                pass
            time.sleep(1.0)


def _is_challenge_page(driver) -> bool:
    source = (driver.page_source or "").lower()
    title = (driver.title or "").lower()
    return "cloudflare" in source or "just a moment" in title or "captcha" in source


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "")).strip()


def _slugify_city(city: str) -> str:
    return urllib.parse.quote((city or "").strip().replace(" ", "-"))


def _slugify_query(query: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9\s&-]+", " ", (query or "").strip())
    cleaned = re.sub(r"\s+", "-", cleaned).strip("-")
    return urllib.parse.quote(cleaned)


def _clean_phone(value: str) -> str:
    raw = _normalize_whitespace(value)
    if not raw:
        return ""
    digits = re.sub(r"\D", "", raw)
    mobile_match = re.search(r"(0?[6-9]\d{9})", digits)
    if mobile_match:
        mobile = mobile_match.group(1)
        return mobile if mobile.startswith("0") else f"0{mobile}"
    if len(digits) < 7:
        return ""
    if len(digits) > 12 and not raw.startswith(("+", "00")):
        return ""
    return raw


def _choose_best_phone(primary: str, fallback: str) -> str:
    primary = _clean_phone(primary)
    fallback = _clean_phone(fallback)
    if primary:
        digits = re.sub(r"\D", "", primary)
        if 7 <= len(digits) <= 12:
            return primary
    return fallback or primary


def _extract_rating_count(text: str) -> int | None:
    match = re.search(r"([\d,]+)\s+Ratings?", text, flags=re.IGNORECASE)
    if not match:
        return None
    try:
        return int(match.group(1).replace(",", ""))
    except ValueError:
        return None


def _extract_detail_url(anchor_href: str) -> str:
    href = (anchor_href or "").strip()
    if not href:
        return ""
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return urllib.parse.urljoin(JUSTDIAL_HOME_URL, href)
    return href


def _fetch_html(url: str) -> str:
    if not url or not url.startswith("http"):
        return ""
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=max(3, int(SCRAPER_SETTINGS.get("request_timeout", 8))),
            allow_redirects=True,
        )
        if response.ok and "text/html" in response.headers.get("Content-Type", ""):
            return response.text
    except Exception:
        pass
    return ""


def _wait_for_results(driver, timeout_seconds: int = 30) -> bool:
    end_time = time.time() + timeout_seconds
    while time.time() < end_time:
        page_source = driver.page_source or ""
        if any(token in page_source for token in ("Ratings", "Show Number", "WhatsApp")):
            return True
        if _is_challenge_page(driver):
            time.sleep(2)
            continue
        time.sleep(1)
    return False


def _looks_like_results_page(url: str, city: str, query: str) -> bool:
    lower_url = (url or "").lower()
    city_token = (city or "").strip().lower().replace(" ", "-")
    query_token = (query or "").strip().lower().replace(" ", "-")
    return (
        city_token in lower_url
        and query_token in lower_url
        and "justdial.com" in lower_url
        and lower_url.rstrip("/") != f"{JUSTDIAL_HOME_URL}/{city_token}"
    )


def _dismiss_login_popup(driver) -> None:
    """Close Justdial login/signup popups that block page interaction."""
    popup_selectors = [
        "#loginPop",
        ".loginPop",
        "[class*='loginPop']",
        "[class*='jd_modal']",
        "[role='dialog']",
    ]
    close_selectors = [
        "button[aria-label='Close']",
        "button[class*='close']",
        "[class*='close']",
        "[data-testid*='close']",
        "svg[class*='close']",
    ]

    # First try normal close buttons inside visible modals.
    for popup_selector in popup_selectors:
        for popup in driver.find_elements(By.CSS_SELECTOR, popup_selector):
            try:
                if not popup.is_displayed():
                    continue
                for close_selector in close_selectors:
                    for close_btn in popup.find_elements(By.CSS_SELECTOR, close_selector):
                        try:
                            if close_btn.is_displayed():
                                driver.execute_script("arguments[0].click();", close_btn)
                                time.sleep(1)
                                return
                        except Exception:
                            continue
            except Exception:
                continue

    # Escape key sometimes dismisses the overlay.
    try:
        driver.switch_to.active_element.send_keys(Keys.ESCAPE)
        time.sleep(0.5)
    except Exception:
        pass

    # Final fallback: hide the modal/backdrop via JS if Justdial leaves it open.
    js = """
        const selectors = ['#loginPop', '.loginPop', '[class*="loginPop"]', '[class*="jd_modal"]'];
        for (const sel of selectors) {
            document.querySelectorAll(sel).forEach((el) => {
                el.style.display = 'none';
                el.style.visibility = 'hidden';
                el.classList.remove('show', 'active');
            });
        }
        document.querySelectorAll('[class*="backdrop"], [class*="overlay"], .modal-backdrop').forEach((el) => {
            el.style.display = 'none';
            el.style.visibility = 'hidden';
        });
        if (document.body) {
            document.body.style.overflow = 'auto';
        }
    """
    try:
        driver.execute_script(js)
        time.sleep(0.5)
    except Exception:
        pass


def _find_search_box(driver):
    input_selectors = [
        "input#main-auto",
        "input[placeholder*='Search']",
        "input[aria-label*='Search']",
        "input[name*='search']",
        "input[type='text']",
    ]
    for selector in input_selectors:
        matches = driver.find_elements(By.CSS_SELECTOR, selector)
        for candidate in matches:
            try:
                if candidate.is_displayed() and candidate.is_enabled():
                    return candidate
            except Exception:
                continue
    return None


def _open_search_results(driver, city: str, query: str, listing_url: str = "") -> str:
    if listing_url:
        driver.get(listing_url)
        time.sleep(SCRAPER_SETTINGS.get("page_load_wait", 6))
        _wait_for_results(driver)
        return driver.current_url

    direct_url = f"{JUSTDIAL_HOME_URL}/{_slugify_city(city)}/{_slugify_query(query)}"
    driver.get(direct_url)
    time.sleep(SCRAPER_SETTINGS.get("page_load_wait", 6))
    _dismiss_login_popup(driver)
    _wait_for_results(driver, timeout_seconds=10)
    if _looks_like_results_page(driver.current_url, city, query):
        return driver.current_url

    city_url = f"{JUSTDIAL_HOME_URL}/{_slugify_city(city)}"
    driver.get(city_url)
    time.sleep(SCRAPER_SETTINGS.get("page_load_wait", 6))
    _dismiss_login_popup(driver)
    search_box = _find_search_box(driver)

    if not search_box:
        raise RuntimeError("Could not find Justdial search input on the page.")

    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", search_box)
        search_box.click()
    except ElementClickInterceptedException:
        _dismiss_login_popup(driver)
        search_box = _find_search_box(driver)
        if not search_box:
            raise RuntimeError("Search input disappeared after dismissing Justdial popup.")
        driver.execute_script("arguments[0].focus();", search_box)
    except Exception:
        driver.execute_script("arguments[0].focus();", search_box)
    try:
        search_box.send_keys(Keys.CONTROL, "a")
        search_box.send_keys(Keys.DELETE)
    except Exception:
        pass
    search_box.send_keys(query)
    search_box.send_keys(Keys.ENTER)
    time.sleep(SCRAPER_SETTINGS.get("page_load_wait", 6))
    _wait_for_results(driver)
    return driver.current_url


def _is_valid_business_name(name: str) -> bool:
    normalized = _normalize_whitespace(name).lower()
    if len(normalized) < 3:
        return False
    if any(token in normalized for token in _GENERIC_NAME_PATTERNS):
        return False
    return True


def _is_business_detail_url(url: str) -> bool:
    lower = (url or "").lower()
    return "_bzdet" in lower and "justdial.com" in lower


def _extract_listing_cards(driver, max_scrolls: int) -> list[dict]:
    seen_urls = set()
    items: list[dict] = []

    for _ in range(max_scrolls):
        page_html = driver.page_source or ""
        soup = BeautifulSoup(page_html, "html.parser")

        for selector in _LISTING_BLOCK_SELECTORS:
            for block in soup.select(selector):
                record = _parse_listing_block(block)
                detail_url = record.get("detail_url", "")
                if (
                    not detail_url
                    or detail_url in seen_urls
                    or not _is_business_detail_url(detail_url)
                    or not _is_valid_business_name(record.get("business_name", ""))
                ):
                    continue
                seen_urls.add(detail_url)
                items.append(record)

        last_height = driver.execute_script("return document.body.scrollHeight")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCRAPER_SETTINGS.get("justdial_scroll_pause", 2))
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break

    if items:
        return items

    soup = BeautifulSoup(driver.page_source or "", "html.parser")
    for anchor in soup.select("a[href]"):
        href = _extract_detail_url(anchor.get("href"))
        if not href or href in seen_urls:
            continue
        if not any(token.lower() in href.lower() for token in _DETAIL_LINK_PATTERNS):
            continue
        name = _normalize_whitespace(anchor.get_text(" ", strip=True))
        if not _is_business_detail_url(href) or not _is_valid_business_name(name):
            continue
        seen_urls.add(href)
        items.append(
            {
                "business_name": name,
                "detail_url": href,
                "area": "",
                "category": "",
                "rating": None,
                "rating_count": None,
            }
        )
    return items


def _parse_listing_block(block) -> dict:
    name = ""
    detail_url = ""
    for selector in ("h2 a[href]", "h3 a[href]", "a[href]"):
        link = block.select_one(selector)
        if not link:
            continue
        detail_url = _extract_detail_url(link.get("href"))
        name = _normalize_whitespace(link.get_text(" ", strip=True))
        if name and _is_business_detail_url(detail_url):
            break

    text = _normalize_whitespace(block.get_text(" ", strip=True))
    area = ""
    for piece in [p.strip() for p in text.split("  ") if p.strip()]:
        if "Ratings" in piece or "Years" in piece or "WhatsApp" in piece:
            continue
        if piece != name and len(piece) <= 80:
            area = piece
            break

    rating = None
    rating_match = re.search(r"\b([1-5]\.\d)\b", text)
    if rating_match:
        try:
            rating = float(rating_match.group(1))
        except ValueError:
            rating = None

    category = ""
    category_match = re.search(r"in Business (.+?)(?:Show Number|WhatsApp|$)", text, flags=re.IGNORECASE)
    if category_match:
        category = _normalize_whitespace(category_match.group(1))

    return {
        "business_name": name,
        "detail_url": detail_url,
        "area": area,
        "category": category,
        "rating": rating,
        "rating_count": _extract_rating_count(text),
    }


def _click_next_page(driver) -> bool:
    selectors = [
        "a[aria-label='Next']",
        "button[aria-label='Next']",
        "a[title='Next']",
        "button[title='Next']",
    ]
    for selector in selectors:
        for element in driver.find_elements(By.CSS_SELECTOR, selector):
            try:
                if not element.is_displayed() or not element.is_enabled():
                    continue
                driver.execute_script("arguments[0].click();", element)
                time.sleep(SCRAPER_SETTINGS.get("page_load_wait", 6))
                _wait_for_results(driver)
                return True
            except Exception:
                continue

    xpaths = [
        "//a[contains(translate(normalize-space(.), 'NEXT', 'next'), 'next')]",
        "//button[contains(translate(normalize-space(.), 'NEXT', 'next'), 'next')]",
    ]
    for xpath in xpaths:
        for element in driver.find_elements(By.XPATH, xpath):
            try:
                if not element.is_displayed() or not element.is_enabled():
                    continue
                driver.execute_script("arguments[0].click();", element)
                time.sleep(SCRAPER_SETTINGS.get("page_load_wait", 6))
                _wait_for_results(driver)
                return True
            except Exception:
                continue
    return False


def _extract_external_website(soup: BeautifulSoup) -> str:
    for anchor in soup.select("a[href]"):
        href = _extract_detail_url(anchor.get("href"))
        lower = href.lower()
        if not href:
            continue
        if lower.startswith("tel:") or lower.startswith("mailto:"):
            continue
        if any(token in lower for token in _BLOCKED_EXTERNAL_HOST_TOKENS):
            continue
        if href.startswith("http"):
            return href
    return ""


def _extract_phone_from_detail(soup: BeautifulSoup, text: str) -> str:
    for anchor in soup.select("a[href^='tel:']"):
        href = anchor.get("href") or ""
        phone = href.split(":", 1)[1] if ":" in href else href
        phone = _clean_phone(phone)
        if phone:
            return phone

    patterns = [
        r"(?:\+91[\s-]?)?[6-9]\d{9}",
        r"(?:\+91[\s-]?)?\d{3,5}[\s-]?\d{5,8}",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            phone = _clean_phone(match.group(0))
            if phone:
                return phone
    return ""


def _extract_email_from_detail(soup: BeautifulSoup, text: str) -> str:
    for anchor in soup.select("a[href^='mailto:']"):
        href = (anchor.get("href") or "").strip()
        email = href.split(":", 1)[1].split("?")[0].strip() if ":" in href else ""
        if "@" in email:
            return email

    match = re.search(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", text)
    if match:
        return match.group(0).strip()
    return ""


def _extract_address(text: str) -> str:
    patterns = [
        r"Address\s*[:\-]?\s*(.+?)(?:Open Now|Show Number|Get Directions|Website|Call|$)",
        r"Contact Information Of .+?\s+(.+?)(?:Show Number|Get Directions|Website|Call|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return _normalize_whitespace(match.group(1))
    return ""


def _extract_name_from_detail(soup: BeautifulSoup) -> str:
    for selector in ("h1", "h2", "[itemprop='name']"):
        node = soup.select_one(selector)
        if node:
            name = _normalize_whitespace(node.get_text(" ", strip=True))
            if name:
                return name
    title = _normalize_whitespace(soup.title.get_text(" ", strip=True)) if soup.title else ""
    return title.split("- Justdial")[0].strip()


def _build_detail_record_from_html(html: str, listing: dict, city: str, search_term: str, detail_url: str) -> dict:
    if not html:
        return {}

    soup = BeautifulSoup(html, "html.parser")
    text = _normalize_whitespace(soup.get_text(" ", strip=True))
    business_name = _extract_name_from_detail(soup) or listing.get("business_name", "")
    website_url = _extract_external_website(soup)
    robust_phone, robust_email = extract_contacts_from_html(html, detail_url)
    detail_phone = _extract_phone_from_detail(soup, text)
    phone = _choose_best_phone(robust_phone, detail_phone)
    email = robust_email or _extract_email_from_detail(soup, text)

    if website_url and (not phone or not email) and SCRAPER_SETTINGS.get("justdial_website_enrich", True):
        try:
            website_phone, website_email = extract_contacts(
                website_url,
                deep_lookup_override=True,
                contact_page_limit_override=5,
            )
            if website_phone and not phone:
                phone = website_phone
            if website_email and not email:
                email = website_email
        except Exception:
            pass

    return {
        "source_platform": "justdial",
        "city": city,
        "search_term": search_term,
        "business_name": business_name,
        "category": listing.get("category", ""),
        "area": listing.get("area", ""),
        "address": _extract_address(text),
        "detail_url": detail_url,
        "website_url": website_url,
        "phone": phone,
        "email": email,
        "rating": listing.get("rating"),
        "rating_count": listing.get("rating_count"),
    }


def _extract_detail_record(driver, listing: dict, city: str, search_term: str) -> dict:
    detail_url = listing.get("detail_url", "")
    if not detail_url:
        return {}

    driver.get(detail_url)
    time.sleep(SCRAPER_SETTINGS.get("page_load_wait", 6))
    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except TimeoutException:
        return {}

    return _build_detail_record_from_html(driver.page_source or "", listing, city, search_term, detail_url)


def _extract_detail_record_via_http(listing: dict, city: str, search_term: str) -> dict:
    detail_url = listing.get("detail_url", "")
    if not detail_url:
        return {}
    html = _fetch_html(detail_url)
    return _build_detail_record_from_html(html, listing, city, search_term, detail_url)


def scrape_justdial(
    city: str,
    search_term: str,
    max_pages: int = 1,
    listing_url: str = "",
) -> list[dict]:
    """Scrape one Justdial search term for a single city."""
    driver = _build_driver()
    results: list[dict] = []
    seen_detail_urls = set()
    detail_limit = max(1, int(SCRAPER_SETTINGS.get("justdial_detail_limit", 100)))

    try:
        current_url = _open_search_results(driver, city=city, query=search_term, listing_url=listing_url)
        print(f"[Justdial] Results URL: {current_url}")

        listing_rows: list[dict] = []
        total_pages = max(1, int(max_pages or 1))
        for page_num in range(1, total_pages + 1):
            print(f"[Justdial] Parsing listing page {page_num} for '{search_term}' in {city}")
            page_items = _extract_listing_cards(
                driver,
                max_scrolls=max(1, int(SCRAPER_SETTINGS.get("justdial_max_scrolls", 8))),
            )
            if not page_items:
                print(f"[Justdial] No listing cards found on page {page_num}.")
                break

            added = 0
            for item in page_items:
                detail_url = item.get("detail_url", "")
                if not detail_url or detail_url in seen_detail_urls:
                    continue
                seen_detail_urls.add(detail_url)
                listing_rows.append(item)
                added += 1

            print(f"[Justdial] Page {page_num}: collected {added} new listing URLs")
            if len(listing_rows) >= detail_limit:
                listing_rows = listing_rows[:detail_limit]
                break

            if page_num < total_pages and not _click_next_page(driver):
                print("[Justdial] Next page not available; stopping pagination.")
                break

        selected_rows = listing_rows[:detail_limit]
        worker_count = max(1, int(SCRAPER_SETTINGS.get("justdial_detail_workers", 8)))
        print(f"[Justdial] Fetching {len(selected_rows)} detail pages with {worker_count} workers")

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = {
                executor.submit(_extract_detail_record_via_http, listing, city, search_term): listing
                for listing in selected_rows
            }
            for idx, future in enumerate(as_completed(futures), start=1):
                listing = futures[future]
                detail_url = listing.get("detail_url", "")
                try:
                    record = future.result()
                    if not record.get("business_name"):
                        record = _extract_detail_record(driver, listing, city=city, search_term=search_term)
                    if record.get("business_name"):
                        results.append(record)
                        print(
                            f"[Justdial] [{idx}/{len(selected_rows)}] "
                            f"{record.get('business_name')} | "
                            f"Phone: {'Y' if record.get('phone') else 'N'} | "
                            f"Email: {'Y' if record.get('email') else 'N'}"
                        )
                except Exception as exc:
                    print(f"[Justdial] Detail scrape failed for {detail_url}: {exc}")
                    continue
    finally:
        try:
            driver.quit()
        except Exception:
            pass

    print(f"[Justdial] Done '{search_term}' in {city}: {len(results)} records.")
    return results
