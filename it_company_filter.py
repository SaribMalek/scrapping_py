"""
it_company_filter.py - Heuristic IT-company classifier.

Goal: keep likely IT/software companies and drop clearly non-IT businesses.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

IT_STRONG_INCLUDE_TERMS = [
    "software",
    "saas",
    "web development",
    "app development",
    "mobile app",
    "application development",
    "custom software",
    "product engineering",
    "devops",
    "cloud",
    "cybersecurity",
    "cyber security",
    "data engineering",
    "data science",
    "ai ",
    " machine learning",
    "ml ",
    "qa testing",
    "quality assurance",
    "ui ux",
    "ui/ux",
    "blockchain",
    "iot",
    "managed it",
    "it services",
    "it support",
    "digital engineering",
]

IT_WEAK_INCLUDE_TERMS = [
    "tech",
    "technology",
]

NON_IT_EXCLUDE_TERMS = [
    "digital marketing",
    "marketing agency",
    "seo agency",
    "seo company",
    "ppc agency",
    "social media marketing",
    "branding agency",
    "pr agency",
    "virtual assistant",
    "accounting",
    "bookkeeping",
    "tax",
    "taxation",
    "payroll",
    "law firm",
    "attorney",
    "real estate",
    "realtor",
    "insurance agency",
    "travel agency",
    "event management",
]


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _url_tokens(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    try:
        parsed = urlparse(raw)
        host = (parsed.netloc or "").replace("www.", "")
        path = parsed.path or ""
        return _norm(f"{host} {path}")
    except Exception:
        return _norm(raw)


def _contains_any(haystack: str, terms: list[str]) -> str:
    for term in terms:
        # Match as phrase/token boundaries to avoid substring accidents
        # like "datax" matching "tax".
        pattern = r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])"
        if re.search(pattern, haystack):
            return term
    return ""


def is_it_company(company_name: str, website_url: str = "", source: str = "") -> tuple[bool, str]:
    """
    Returns (is_it, reason).
    Conservative policy:
    - Drop only clearly non-IT terms when no IT signal is present.
    - Keep unknowns to avoid deleting legitimate IT firms with generic names.
    """
    name = _norm(company_name)
    url = _url_tokens(website_url)
    src = _norm(source)
    haystack = _norm(f"{name} {url}")

    strong_include_hit = _contains_any(haystack, IT_STRONG_INCLUDE_TERMS)
    weak_include_hit = _contains_any(haystack, IT_WEAK_INCLUDE_TERMS)
    exclude_hit = _contains_any(haystack, NON_IT_EXCLUDE_TERMS)

    if strong_include_hit:
        return True, f"include:{strong_include_hit}"

    # Clear non-IT intent should win over weak words like "tech/technology".
    if exclude_hit:
        return False, f"exclude:{exclude_hit}"

    if weak_include_hit:
        return True, f"include:{weak_include_hit}"

    # Source pages are IT-focused; keep ambiguous names rather than over-pruning.
    if src in {"clutch", "goodfirms"}:
        return True, "source-default-allow"

    return True, "default-allow"


def filter_it_companies(companies: list[dict], source: str = "") -> tuple[list[dict], list[dict]]:
    """Split rows into (kept, dropped) using is_it_company()."""
    kept = []
    dropped = []
    for row in companies:
        ok, reason = is_it_company(
            company_name=row.get("company_name", ""),
            website_url=row.get("website_url", ""),
            source=source or row.get("source", ""),
        )
        row_with_reason = dict(row)
        row_with_reason["_it_filter_reason"] = reason
        if ok:
            kept.append(row_with_reason)
        else:
            dropped.append(row_with_reason)
    return kept, dropped
