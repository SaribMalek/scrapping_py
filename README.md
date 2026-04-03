# 🕷️ Web Scraper — Clutch.co & GoodFirms.co

Scrapes IT company listings from **Clutch.co** and **GoodFirms.co** by country,
visits each company's website to extract **phone numbers** and **email addresses**,
stores everything in **MySQL**, and exports a **CSV** file.

---

## 📋 Requirements

- Python 3.10+
- Google Chrome (for Selenium)
- WAMP (MySQL running on localhost)

---

## ⚙️ Setup

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure database
Edit `config.py` if your MySQL password is different from the default (empty).

### 3. Initialise the database
```bash
python database.py
```
This creates the `scrapper_db` database, the `companies` table, and the
`justdial_companies` table in MySQL.

---

## 🚀 Usage

### Scrape a single country (Clutch):
```bash
python main.py --source clutch --country "India"
```

### Scrape a single country (GoodFirms):
```bash
python main.py --source goodfirms --country "United States"
```

### Scrape a single country from BOTH sites (one command):
```bash
python main.py --source both --country "United States" --max-pages 1
```

### Same as above (because `--source` defaults to `both`):
```bash
python main.py --country "United States" --max-pages 1
```

### Scrape one specific page (GoodFirms):
```bash
python main.py --source goodfirms --country "India" --start-page 3 --max-pages 1
```

### Run multiple single-page jobs (GoodFirms, PowerShell):
```powershell
.\run_goodfirms_pages.ps1 -Country "India" -FromPage 1 -ToPage 10
```

### Clean existing data to keep IT-focused records only:
```bash
python cleanup_it_data.py
```

### Preview cleanup without deleting anything:
```bash
python cleanup_it_data.py --dry-run
```

### Scrape all countries from both sites:
```bash
python main.py --all
```

### Limit pages per country (faster testing):
```bash
python main.py --source clutch --country "India" --max-pages 2
```

### Scrape Justdial businesses for Ahmedabad and store them in MySQL:
```bash
python scrape_justdial.py --city "Ahmedabad" --max-pages 1
```

### Scrape specific Justdial categories:
```bash
python scrape_justdial.py --city "Ahmedabad" --search-term "Restaurants" --search-term "Hospitals" --max-pages 2
```

### Scrape from a direct Justdial listing URL:
```bash
python scrape_justdial.py --city "Ahmedabad" --search-term "Restaurants" --listing-url "https://www.justdial.com/Ahmedabad/Restaurants-in-Ode/nct-10408936"
```

### Send personalized campaign emails to scraped companies:
1) Configure SMTP in `.env`:
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
SMTP_FROM=your-email@gmail.com
SMTP_FROM_NAME=Vivan Web Solution
SMTP_REPLY_TO=your-email@gmail.com
SMTP_USE_TLS=1
SMTP_USE_SSL=0
```

2) Dry run (preview recipients, no send):
```bash
python send_campaign_emails.py --subject "Quick Introduction from Vivan Web Solution" --dry-run
```

3) Send to all recipients from DB:
```bash
python send_campaign_emails.py --subject "Quick Introduction from Vivan Web Solution"
```

Send using your screenshot/design image (with dynamic company name greeting):
```bash
python send_campaign_emails.py --subject "Quick Introduction from Vivan Web Solution" --screenshot-path "C:\path\to\campaign.png"
```

Optional filters:
```bash
python send_campaign_emails.py --subject "Quick Introduction from Vivan Web Solution" --source clutch --country "United Kingdom" --batch-size 40 --pause-seconds 3
```

Daily send example with automatic invalid-email skipping:
```bash
python send_campaign_emails.py --limit 50 --batch-size 50 --campaign-id "fresh-50-2026-03-19"
```

When you run the normal send command, it now:
- validates email format
- checks MX records before sending
- skips invalid emails automatically
- stores exact bad addresses in `output/invalid_emails.log` so they are skipped next time too

Validate email addresses before sending:
```bash
python send_campaign_emails.py --validate-email sales@keyideas.com someone@gmail.com hello@notexist123.com
```

Validate email addresses directly from the `companies` table:
```bash
python send_campaign_emails.py --validate-db-emails
```

Validate only a filtered slice of DB emails:
```bash
python send_campaign_emails.py --validate-db-emails --source clutch --country "United States" --limit 50
```

This validation command checks:
- Email format
- MX records for the email domain

If `dnspython` is not installed yet:
```bash
pip install -r requirements.txt
```

---

## 📤 Export CSV

Results are auto-exported after each run. To manually export:
```bash
python export_csv.py
```
Outputs:
- `output/companies_clutch.csv`
- `output/companies_goodfirms.csv`
- `output/companies_emails.csv` (plugin-ready format: `No,Name,Type,Mail`)

## 📊 Export Excel

To export Excel files:
```bash
python export_excel.py
```
Outputs:
- `output/companies.xlsx` (ALL, CLUTCH, GOODFIRMS sheets)
- `output/companies_clutch.xlsx`
- `output/companies_goodfirms.xlsx`

---

## 🗄️ Database Schema

| Column | Description |
|--------|-------------|
| id | Auto-increment primary key |
| source | `clutch` or `goodfirms` |
| company_name | Name of the company |
| country | Country from listing |
| city | City from listing |
| website_url | Company website URL |
| phone | Extracted phone number |
| email | Extracted email address |
| scraped_at | Timestamp when scraped |

---

## Justdial Schema

| Column | Description |
|--------|-------------|
| source_platform | Always `justdial` so the source is clearly marked |
| city | City used for the Justdial search |
| search_term | Category / keyword used in the command |
| business_name | Business name from Justdial |
| category | Category text found on the listing |
| area | Area or locality from the listing |
| address | Address from the detail page |
| detail_url | Justdial detail page URL |
| website_url | External business website if available |
| phone | Phone number if available |
| rating | Business rating |
| rating_count | Total ratings count |
| scraped_at | Timestamp when the record was scraped |

---

## 📁 Project Structure

```
scrapping_py/
├── config.py              # DB config, countries list, settings
├── database.py            # MySQL helpers
├── contact_extractor.py   # Phone/email extraction from websites
├── main.py                # CLI entry point
├── export_csv.py          # CSV export
├── requirements.txt       # Python dependencies
├── scrapers/
│   ├── clutch_scraper.py
│   └── goodfirms_scraper.py
└── output/
    └── companies.csv      # Generated after running
```
