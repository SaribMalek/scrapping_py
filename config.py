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
    "chrome_version": 146,  # Match your installed Chrome major version
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
    "justdial_scroll_pause": 2,  # Seconds to wait after each listing-page scroll
    "justdial_max_scrolls": 8,  # Scroll attempts before trying pagination
    "justdial_detail_limit": 100,  # Safety cap per search term for detail scraping
    "justdial_detail_workers": 8,  # Parallel workers for Justdial detail-page fetches
    "justdial_website_enrich": True,  # Visit company website if Justdial page misses phone/email
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

JUSTDIAL_DEFAULT_SEARCH_TERMS = [
    "Restaurants",
    "Hospitals",
    "Schools",
    "Travel Agents",
    "Interior Designers",
    "Digital Marketing Services",
    "Web Designing Services",
    "Packers And Movers",
    "Courier Services",
    "CA",
]

JUSTDIAL_ALL_BUSINESS_TERMS = [
    "Restaurants",
    "Hotels",
    "Hospitals",
    "Doctors",
    "Dentists",
    "Schools",
    "Colleges",
    "Coaching Classes",
    "Travel Agents",
    "Tour Operators",
    "Car Rental",
    "Packers And Movers",
    "Courier Services",
    "Cargo Services",
    "Interior Designers",
    "Architects",
    "Civil Contractors",
    "Building Contractors",
    "Electricians",
    "Plumbers",
    "Carpenters",
    "Painters",
    "Caterers",
    "Banquet Halls",
    "Event Organisers",
    "Wedding Planners",
    "Beauty Parlours",
    "Salons",
    "Spa Centres",
    "Gym",
    "Yoga Classes",
    "Pet Shops",
    "Grocery Stores",
    "Supermarkets",
    "Stationery Shops",
    "Mobile Phone Dealers",
    "Laptop Dealers",
    "Computer Repair Services",
    "AC Repair Services",
    "Home Appliances Repair Services",
    "Real Estate Agents",
    "Property Dealers",
    "Insurance Agents",
    "Loan Consultants",
    "Chartered Accountants",
    "Advocates",
    "Web Designing Services",
    "Digital Marketing Services",
    "Software Companies",
    "IT Companies",
    "SEO Services",
    "Graphic Designers",
    "Printers",
    "Advertising Agencies",
    "Manufacturers",
    "Wholesalers",
    "Exporters",
    "Importers",
    "Chemical Dealers",
    "Pharmaceutical Companies",
    "Medical Stores",
    "Laboratories",
]
