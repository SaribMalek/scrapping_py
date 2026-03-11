"""
database.py - MySQL schema creation and CRUD helpers
"""

from datetime import datetime

import mysql.connector

from config import DB_CONFIG

CREATE_DB_SQL = "CREATE DATABASE IF NOT EXISTS `scrapper_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS `companies` (
    `id`           INT AUTO_INCREMENT PRIMARY KEY,
    `source`       VARCHAR(50)  NOT NULL COMMENT 'clutch or goodfirms',
    `company_name` VARCHAR(255) NOT NULL,
    `country`      VARCHAR(100) DEFAULT NULL,
    `city`         VARCHAR(100) DEFAULT NULL,
    `website_url`  TEXT         DEFAULT NULL,
    `phone`        VARCHAR(150) DEFAULT NULL,
    `email`        VARCHAR(255) DEFAULT NULL,
    `email_sent`   TINYINT(1)   NOT NULL DEFAULT 0,
    `email_sent_at` DATETIME    DEFAULT NULL,
    `email_tracking_token` VARCHAR(64) DEFAULT NULL,
    `email_opened` TINYINT(1)   NOT NULL DEFAULT 0,
    `email_opened_at` DATETIME  DEFAULT NULL,
    `email_last_opened_at` DATETIME DEFAULT NULL,
    `email_open_count` INT      NOT NULL DEFAULT 0,
    `scraped_at`   DATETIME     DEFAULT NULL,
    UNIQUE KEY `uniq_source_name` (`source`, `company_name`(180)),
    UNIQUE KEY `uniq_email_tracking_token` (`email_tracking_token`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

CREATE_PROGRESS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS `scrape_progress` (
    `id`           INT AUTO_INCREMENT PRIMARY KEY,
    `source`       VARCHAR(50)  NOT NULL,
    `country`      VARCHAR(100) NOT NULL,
    `last_page`    INT          NOT NULL DEFAULT 0,
    `updated_at`   DATETIME     DEFAULT NULL,
    UNIQUE KEY `uniq_source_country` (`source`, `country`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


def get_connection(with_db: bool = True):
    """Return a fresh MySQL connection."""
    cfg = DB_CONFIG.copy()
    if not with_db:
        cfg.pop("database", None)
    return mysql.connector.connect(**cfg)


def init_db():
    """Create database and table if they do not already exist."""
    conn = get_connection(with_db=False)
    cursor = conn.cursor()
    cursor.execute(CREATE_DB_SQL)
    cursor.execute(f"USE `{DB_CONFIG['database']}`;")
    cursor.execute(CREATE_TABLE_SQL)
    cursor.execute(CREATE_PROGRESS_TABLE_SQL)
    # Keep newest row per (source, company_name) so unique index can be enforced safely.
    cursor.execute(
        """
        DELETE c1
        FROM companies c1
        INNER JOIN companies c2
            ON c1.source = c2.source
           AND c1.company_name = c2.company_name
           AND c1.id < c2.id
        """
    )

    cursor.execute(
        """
        SELECT COUNT(1)
        FROM information_schema.statistics
        WHERE table_schema = %s
          AND table_name = 'companies'
          AND index_name = 'uniq_source_name'
        """,
        (DB_CONFIG["database"],),
    )
    has_unique = (cursor.fetchone() or [0])[0] > 0
    if not has_unique:
        cursor.execute(
            "ALTER TABLE companies ADD UNIQUE KEY uniq_source_name (source, company_name(180));"
        )
    _ensure_email_tracking_columns(cursor)
    conn.commit()
    cursor.close()
    conn.close()
    print("[DB] Database and table ready.")


def _ensure_email_tracking_columns(cursor) -> None:
    cursor.execute("SHOW COLUMNS FROM companies LIKE 'email_sent';")
    if not cursor.fetchone():
        cursor.execute(
            "ALTER TABLE companies ADD COLUMN email_sent TINYINT(1) NOT NULL DEFAULT 0 AFTER email;"
        )
    cursor.execute("SHOW COLUMNS FROM companies LIKE 'email_sent_at';")
    if not cursor.fetchone():
        cursor.execute(
            "ALTER TABLE companies ADD COLUMN email_sent_at DATETIME DEFAULT NULL AFTER email_sent;"
        )
    cursor.execute("SHOW COLUMNS FROM companies LIKE 'email_tracking_token';")
    if not cursor.fetchone():
        cursor.execute(
            "ALTER TABLE companies ADD COLUMN email_tracking_token VARCHAR(64) DEFAULT NULL AFTER email_sent_at;"
        )
    cursor.execute("SHOW COLUMNS FROM companies LIKE 'email_opened';")
    if not cursor.fetchone():
        cursor.execute(
            "ALTER TABLE companies ADD COLUMN email_opened TINYINT(1) NOT NULL DEFAULT 0 AFTER email_tracking_token;"
        )
    cursor.execute("SHOW COLUMNS FROM companies LIKE 'email_opened_at';")
    if not cursor.fetchone():
        cursor.execute(
            "ALTER TABLE companies ADD COLUMN email_opened_at DATETIME DEFAULT NULL AFTER email_opened;"
        )
    cursor.execute("SHOW COLUMNS FROM companies LIKE 'email_last_opened_at';")
    if not cursor.fetchone():
        cursor.execute(
            "ALTER TABLE companies ADD COLUMN email_last_opened_at DATETIME DEFAULT NULL AFTER email_opened_at;"
        )
    cursor.execute("SHOW COLUMNS FROM companies LIKE 'email_open_count';")
    if not cursor.fetchone():
        cursor.execute(
            "ALTER TABLE companies ADD COLUMN email_open_count INT NOT NULL DEFAULT 0 AFTER email_last_opened_at;"
        )
    cursor.execute(
        """
        SELECT COUNT(1)
        FROM information_schema.statistics
        WHERE table_schema = %s
          AND table_name = 'companies'
          AND index_name = 'uniq_email_tracking_token'
        """,
        (DB_CONFIG["database"],),
    )
    has_tracking_unique = (cursor.fetchone() or [0])[0] > 0
    if not has_tracking_unique:
        cursor.execute(
            "ALTER TABLE companies ADD UNIQUE KEY uniq_email_tracking_token (email_tracking_token);"
        )


def ensure_email_tracking_columns() -> None:
    conn = get_connection()
    cursor = conn.cursor()
    _ensure_email_tracking_columns(cursor)
    conn.commit()
    cursor.close()
    conn.close()


def reset_email_flags() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE companies
        SET email_sent = 0,
            email_sent_at = NULL
        WHERE COALESCE(email_sent, 0) <> 0
           OR email_sent_at IS NOT NULL
        """
    )
    affected = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    return int(affected)


def _clean(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def _upsert_sql() -> str:
    return """
        INSERT INTO companies (source, company_name, country, city, website_url, phone, email, scraped_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            country     = COALESCE(NULLIF(VALUES(country), ''), country),
            city        = COALESCE(NULLIF(VALUES(city), ''), city),
            website_url = COALESCE(NULLIF(VALUES(website_url), ''), website_url),
            phone       = COALESCE(NULLIF(VALUES(phone), ''), phone),
            email       = COALESCE(NULLIF(VALUES(email), ''), email),
            scraped_at  = VALUES(scraped_at)
    """


def save_company(
    source: str,
    company_name: str,
    country: str = None,
    city: str = None,
    website_url: str = None,
    phone: str = None,
    email: str = None,
):
    """Insert one company or update contact fields if it already exists."""
    values = (
        _clean(source),
        _clean(company_name),
        _clean(country),
        _clean(city),
        _clean(website_url),
        _clean(phone),
        _clean(email),
        datetime.now(),
    )
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(_upsert_sql(), values)
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"[DB ERROR] {err} | company={company_name}")


def save_companies_batch(rows: list[dict]):
    """Bulk insert/update companies with a single DB connection."""
    if not rows:
        return

    now = datetime.now()
    values = [
        (
            _clean(row.get("source")),
            _clean(row.get("company_name")),
            _clean(row.get("country")),
            _clean(row.get("city")),
            _clean(row.get("website_url")),
            _clean(row.get("phone")),
            _clean(row.get("email")),
            now,
        )
        for row in rows
    ]

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.executemany(_upsert_sql(), values)
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"[DB ERROR] Batch save failed: {err}")


def get_all_companies():
    """Fetch all rows from companies table."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM companies ORDER BY id ASC;")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_last_scraped_page(source: str, country: str) -> int:
    """Get the last successfully scraped page for source/country."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT last_page
            FROM scrape_progress
            WHERE source = %s AND country = %s
            LIMIT 1
            """,
            (_clean(source), _clean(country)),
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return int(row[0]) if row and row[0] else 0
    except mysql.connector.Error:
        return 0


def set_last_scraped_page(source: str, country: str, last_page: int):
    """Upsert progress marker for source/country."""
    last_page = max(0, int(last_page or 0))
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO scrape_progress (source, country, last_page, updated_at)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                last_page = VALUES(last_page),
                updated_at = VALUES(updated_at)
            """,
            (_clean(source), _clean(country), last_page, datetime.now()),
        )
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"[DB ERROR] Progress update failed: {err} | {source}/{country} page={last_page}")


if __name__ == "__main__":
    init_db()
    print("[DB] Setup complete. Table 'companies' is ready.")
