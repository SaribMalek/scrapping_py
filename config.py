# Database Configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",  # WAMP default; change if yours differs
    "database": "scrapper_db",
    "charset": "utf8mb4",
}

# Scraper Settings
SCRAPER_SETTINGS = {
    "chrome_version": 145,  # Match your installed Chrome major version
    "page_load_wait": 6,  # Seconds to wait after page load (JS rendering)
    "between_requests": 3,  # Seconds between each HTTP request to a company site
    "max_retries": 1,  # Retries for failed requests
    "request_timeout": 8,  # Seconds before abandoning a company-site fetch
    "headless": False,  # Cloudflare usually clears more reliably in visible mode
    "max_pages_per_country": 10,  # Safety cap per country (set None for unlimited)
    "challenge_wait_seconds": 60,  # Wait for Cloudflare challenge to clear
    "contact_workers": 8,  # Parallel workers for contact extraction
    "contact_request_delay": 0,  # Optional delay between company-site requests
    "deep_contact_lookup": False,  # If True, crawl extra contact/about pages
    "contact_page_limit": 2,  # Number of extra internal pages to probe when deep lookup is on
    "resume_pages": True,  # Resume from last scraped page when start-page is 1
    "clutch_profile_enrich": False,  # Keep default run fast and output concise
    "clutch_profile_enrich_limit": 150,  # Max clutch profile rows to enrich per run
}

# Output
CSV_OUTPUT_PATH = "output/companies.csv"

# Target Countries
# Add/remove countries as needed. These are used as filter query values on the sites.
COUNTRIES = [
    "India",
    "United States",
    "United Kingdom",
    "Canada",
    "Australia",
    "Germany",
    "France",
    "Netherlands",
    "Singapore",
    "United Arab Emirates",
    "Pakistan",
    "Bangladesh",
    "Ukraine",
    "Poland",
    "Brazil",
    "Mexico",
    "Argentina",
    "South Africa",
    "Philippines",
    "Indonesia",
    "Malaysia",
    "Israel",
    "Turkey",
    "Spain",
    "Italy",
    "Sweden",
    "Norway",
    "Denmark",
    "Switzerland",
    "New Zealand",
]

# User-Agent for requests
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}
