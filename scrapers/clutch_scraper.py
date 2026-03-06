"""
scrapers/clutch_scraper.py

Scrapes Clutch IT-services listings and extracts company name, location, and website.
Includes Cloudflare challenge detection with an automatic headless->headed retry.
"""

import time
import os
import urllib.parse

import undetected_chromedriver as uc
import requests
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import SCRAPER_SETTINGS, HEADERS

BASE_URL = "https://clutch.co/it-services"


class SafeChrome(uc.Chrome):
    def __del__(self):
        # undetected_chromedriver can call quit() again during GC and throw
        # WinError 6 on Windows; suppress destructor-time cleanup errors.
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
            # Work around uc binary rename race on Windows:
            # ...chromedriver.exe -> ...undetected_chromedriver.exe (already exists).
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


def _is_cloudflare_challenge(driver) -> bool:
    source = (driver.page_source or "").lower()
    title = (driver.title or "").lower()
    return (
        "cdn-cgi/challenge-platform" in source
        or "cf-chl-" in source
        or "cloudflare" in source
        or "just a moment" in title
    )


def _wait_for_cards_after_challenge(driver, timeout_seconds: int = 45) -> bool:
    """Wait for challenge to clear and listing cards to appear."""
    end_time = time.time() + timeout_seconds
    while time.time() < end_time:
        cards = driver.find_elements(By.CSS_SELECTOR, "div.provider-row")
        if cards:
            return True
        if not _is_cloudflare_challenge(driver):
            return False
        time.sleep(2)
    return False


def _extract_real_url(redirect_url: str) -> str:
    """Extract real company URL from Clutch redirect links that include u=..."""
    try:
        parsed = urllib.parse.urlparse(redirect_url)
        params = urllib.parse.parse_qs(parsed.query)
        u = params.get("u", [""])[0]
        if u and u.startswith("http"):
            inner = urllib.parse.parse_qs(urllib.parse.urlparse(u).query)
            final = inner.get("u", [u])[0]
            return final
        return u or redirect_url
    except Exception:
        return redirect_url


def _resolve_tracking_url(url: str) -> str:
    """Resolve r.clutch.co / ppc.clutch.co tracking URLs to final destination."""
    if not url:
        return url
    lower = url.lower()
    if "r.clutch.co" not in lower and "ppc.clutch.co" not in lower:
        return url
    try:
        resp = requests.get(
            url,
            headers=HEADERS,
            timeout=max(5, SCRAPER_SETTINGS.get("request_timeout", 8)),
            allow_redirects=True,
        )
        final = (resp.url or "").strip()
        if final and "clutch.co" not in final.lower():
            return final
    except Exception:
        pass
    return url


def _parse_companies_on_page(driver) -> list:
    """Extract all company cards visible on the current page."""
    companies = []
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.provider-row"))
        )
    except TimeoutException:
        source = (driver.page_source or "").lower()
        if "cdn-cgi/challenge-platform" in source or "cloudflare" in source:
            print("[Clutch] Blocked by Cloudflare challenge (try headless=False).")
        else:
            print("[Clutch] Timed out waiting for company cards (page blocked or no results).")
        return companies

    cards = driver.find_elements(By.CSS_SELECTOR, "div.provider-row")
    print(f"[Clutch] Found {len(cards)} cards on this page")

    for card in cards:
        try:
            name = card.get_attribute("data-title") or ""
            if not name:
                try:
                    h3 = card.find_element(By.CSS_SELECTOR, "h3")
                    name = h3.text.strip()
                except NoSuchElementException:
                    pass

            country_text, city_text = "", ""
            try:
                loc_el = card.find_element(By.CSS_SELECTOR, ".location")
                loc_raw = loc_el.text.strip()
                parts = [p.strip() for p in loc_raw.split(",")]
                city_text = parts[0] if parts else ""
                country_text = parts[-1] if len(parts) > 1 else loc_raw
            except NoSuchElementException:
                pass

            # Clutch listing cards often expose phone via schema meta.
            listing_phone = ""
            try:
                tel_meta = card.find_element(By.CSS_SELECTOR, "meta[itemprop='telephone']")
                listing_phone = (tel_meta.get_attribute("content") or "").strip()
            except NoSuchElementException:
                listing_phone = ""

            website = ""
            data_link = card.get_attribute("data-link") or ""
            if data_link:
                website = _extract_real_url(data_link)

            # Sponsored cards often provide ppc.clutch.co links; those are not good contact targets.
            if "ppc.clutch.co" in (website or "").lower():
                website = ""

            if not website or "clutch.co" in website:
                try:
                    site_els = card.find_elements(
                        By.CSS_SELECTOR,
                        "[class*='website'] a, "
                        "a[class*='website'], "
                        "a.provider__cta-link[href], "
                        "a[title*='Visit'][href]",
                    )
                    for site_el in site_els:
                        href = site_el.get_attribute("href") or ""
                        if "ppc.clutch.co" in href:
                            continue
                        if href and "r.clutch.co" in href:
                            candidate = _extract_real_url(href)
                            if "ppc.clutch.co" in (candidate or "").lower():
                                continue
                            website = candidate
                            if website:
                                break
                        if href and "clutch.co" not in href:
                            website = href
                            break
                        # Some cards keep external target in data-link on the anchor.
                        data_href = site_el.get_attribute("data-link") or ""
                        if data_href and "r.clutch.co" in data_href:
                            candidate = _extract_real_url(data_href)
                            if candidate and "ppc.clutch.co" not in candidate.lower():
                                website = candidate
                                break
                except Exception:
                    pass

            # Fallback to provider profile URL on Clutch; contact extractor resolves real site from profile.
            if not website:
                try:
                    profile_el = card.find_element(By.CSS_SELECTOR, "h3 a[href], h2 a[href]")
                    profile_href = (profile_el.get_attribute("href") or "").strip()
                    if profile_href:
                        if profile_href.startswith("http"):
                            website = profile_href
                        else:
                            website = urllib.parse.urljoin("https://clutch.co", profile_href)
                except NoSuchElementException:
                    pass

            website = _resolve_tracking_url(website)

            if name:
                companies.append(
                    {
                        "company_name": name,
                        "country": country_text,
                        "city": city_text,
                        "website_url": website,
                        "phone": listing_phone,
                    }
                )
        except Exception:
            continue

    return companies


def scrape_clutch(
    country: str,
    max_pages: int = None,
    start_page: int = 1,
    progress_callback=None,
) -> list:
    """Scrape Clutch IT-services listings for a given country."""
    max_pages = max_pages or SCRAPER_SETTINGS.get("max_pages_per_country", 10)
    start_page = max(1, start_page)
    end_page = start_page + max_pages - 1
    all_companies = []

    print(f"[Clutch] Scraping country: '{country}' (pages {start_page} to {end_page})")
    driver = _build_driver()

    try:
        for page_num in range(start_page, end_page + 1):
            url = (
                f"{BASE_URL}"
                f"?country%5B%5D={urllib.parse.quote(country)}"
                f"&sort_by=sponsored"
                f"&page={page_num}"
            )
            print(f"[Clutch] Loading page {page_num}: {url}")
            driver.get(url)
            time.sleep(SCRAPER_SETTINGS["page_load_wait"])

            if _is_cloudflare_challenge(driver):
                print("[Clutch] Cloudflare challenge detected.")
                challenge_wait = SCRAPER_SETTINGS.get("challenge_wait_seconds", 45)

                if SCRAPER_SETTINGS.get("headless", False):
                    print("[Clutch] Retrying this page in visible browser mode...")
                    try:
                        driver.quit()
                    except Exception:
                        pass
                    driver = _build_driver(headless_override=False)
                    driver.get(url)

                if _wait_for_cards_after_challenge(driver, timeout_seconds=challenge_wait):
                    print("[Clutch] Challenge cleared, continuing scrape.")
                else:
                    print("[Clutch] Challenge not cleared in time - stopping this country.")
                    break

            companies = _parse_companies_on_page(driver)
            if not companies:
                print(f"[Clutch] No companies on page {page_num} - stopping.")
                break

            all_companies.extend(companies)
            print(
                f"[Clutch] Page {page_num}: {len(companies)} companies "
                f"(total: {len(all_companies)})"
            )
            if progress_callback:
                try:
                    progress_callback(page_num, len(companies))
                except Exception:
                    pass

            # Clutch pagination controls are inconsistent; trust explicit page numbers.
            if page_num < end_page:
                time.sleep(SCRAPER_SETTINGS["between_requests"])

    except Exception as e:
        print(f"[Clutch] Error: {e}")
    finally:
        try:
            driver.quit()
        except Exception:
            pass

    print(f"[Clutch] Done '{country}': {len(all_companies)} total companies.")
    return all_companies

