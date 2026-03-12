"""
send_campaign_emails.py

Bulk-send a personalized HTML campaign email to companies stored in MySQL.
Dynamic placeholder: {company_name}
"""

from __future__ import annotations

import argparse
import mimetypes
import os
import re
import smtplib
import ssl
import time
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

from database import get_connection

EMAIL_PATTERN = re.compile(
    r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)


def _is_valid_email(email: str) -> bool:
    email = (email or "").strip().lower()
    if not email:
        return False
    if not EMAIL_PATTERN.fullmatch(email):
        return False
    if email.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".js", ".css")):
        return False
    return True


def _extract_emails(raw: str) -> list[str]:
    if not raw:
        return []
    parts = EMAIL_PATTERN.findall(raw)
    clean = []
    seen = set()
    for item in parts:
        e = item.strip().lower()
        if not _is_valid_email(e) or e in seen:
            continue
        seen.add(e)
        clean.append(e)
    return clean


def _default_html(
    company_name: str,
    logo_cid: str | None = None,
    asset_cids: dict[str, str] | None = None,
) -> str:
    safe_name = company_name.strip() or "Team"
    asset_cids = asset_cids or {}
    logo_html = (
        f'<img src="cid:{logo_cid}" alt="Vivan" style="height:54px;max-width:220px;width:auto;display:block;margin:0 auto;border:0;">'
        if logo_cid
        else '<div style="font-size:34px;font-weight:700;color:#2d2d2d;line-height:1;">Vivan</div>'
    )
    gf_html = (
        f'<img src="cid:{asset_cids["goodfirms"]}" alt="GoodFirms" style="height:32px;width:auto;vertical-align:middle;border:0;">'
        if asset_cids.get("goodfirms")
        else '<span style="color:#346ea5;">GoodFirms</span>'
    )
    upwork_html = (
        f'<img src="cid:{asset_cids["upwork"]}" alt="Upwork" style="height:26px;width:auto;vertical-align:middle;border:0;">'
        if asset_cids.get("upwork")
        else '<span style="color:#7bb340;">upwork</span>'
    )
    clutch_html = (
        f'<img src="cid:{asset_cids["clutch"]}" alt="Clutch" style="height:32px;width:auto;vertical-align:middle;border:0;">'
        if asset_cids.get("clutch")
        else '<span style="color:#255f66;">Clutch</span>'
    )
    fb_html = (
        f'<img src="cid:{asset_cids["facebook"]}" alt="Facebook" style="height:22px;width:auto;vertical-align:middle;border:0;">'
        if asset_cids.get("facebook")
        else '<span style="font-weight:700;color:#1b4f9c;">facebook</span>'
    )
    ig_html = (
        f'<img src="cid:{asset_cids["instagram"]}" alt="Instagram" style="height:22px;width:auto;vertical-align:middle;border:0;">'
        if asset_cids.get("instagram")
        else '<span style="font-weight:700;color:#cf2e7e;">Instagram</span>'
    )
    li_html = (
        f'<img src="cid:{asset_cids["linkedin"]}" alt="LinkedIn" style="height:22px;width:auto;vertical-align:middle;border:0;">'
        if asset_cids.get("linkedin")
        else '<span style="font-weight:700;color:#1d63ab;">LinkedIn</span>'
    )
    return f"""\
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
</head>
<body style="margin:0;padding:0;background:#e9e9e9;font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#e9e9e9;padding:10px 0;">
    <tr>
      <td align="center">
        <table role="presentation" width="680" cellspacing="0" cellpadding="0" style="max-width:680px;background:#e9e9e9;">
          <tr>
            <td style="padding:8px 10px 10px 10px;text-align:center;">
              {logo_html}
            </td>
          </tr>
          <tr>
            <td style="padding:0 12px 6px 12px;">
              <p style="margin:0;color:#1e88e5;font-size:32px;line-height:1.2;font-weight:500;">Hello, {safe_name}</p>
            </td>
          </tr>
          <tr>
            <td style="padding:0 12px 10px 12px;">
              <div style="height:3px;background:#1e88e5;"></div>
            </td>
          </tr>
          <tr>
            <td style="padding:0 12px 8px 12px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f1f1f1;border-radius:3px;">
                <tr>
                  <td style="padding:14px;color:#323232;font-size:20px;line-height:1.6;">
                I hope this email finds you well. I represent Vivan Web Solution Pvt. Ltd.,
                an innovative IT web development company based in India, specialized in crafting
                exceptional web experiences.
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:0 12px 8px 12px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f1f1f1;border-radius:3px;">
                <tr>
                  <td style="padding:14px;color:#323232;font-size:20px;line-height:1.6;">
                Our dynamic team consists of 20+ skilled developers dedicated to converting ideas
                into high-performance web products.
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:0 12px 8px 12px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f1f1f1;border-radius:3px;">
                <tr>
                  <td style="padding:14px;color:#323232;font-size:20px;line-height:1.6;">
                We believe you are an ideal client for us, and we are enthusiastic about creating
                a valuable web app that surpasses your expectations.
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:0 12px 8px 12px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f1f1f1;border-radius:3px;">
                <tr>
                  <td style="padding:18px 14px;text-align:center;">
                    <p style="margin:0 0 10px 0;color:#2b8bd8;font-size:28px;font-weight:700;">Discover what our clients say:</p>
                    <p style="margin:0;line-height:1.1;">
                      {gf_html}
                      <span style="display:inline-block;width:14px;"></span>
                      {upwork_html}
                      <span style="display:inline-block;width:14px;"></span>
                      {clutch_html}
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 12px;color:#2b8bd8;font-size:30px;font-weight:700;">Connect with us on Social Media:</td>
          </tr>
          <tr>
            <td style="padding:0 12px 8px 12px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f1f1f1;border-radius:3px;">
                <tr>
                  <td style="padding:16px;text-align:center;color:#1e1e1e;font-size:26px;">
                    {fb_html}
                    <span style="display:inline-block;width:14px;"></span>
                    {ig_html}
                    <span style="display:inline-block;width:14px;"></span>
                    {li_html}
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:0 12px 8px 12px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f1f1f1;border-radius:3px;">
                <tr>
                  <td style="padding:14px;color:#323232;font-size:20px;line-height:1.6;text-align:center;">
                    If our services intrigue you, please don't hesitate to contact us for further discussions.
                    We are excited to hear from you.
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:4px 12px 0 12px;">
              <a href="https://vivanwebsolution.com/portfolio"
                 style="display:block;background:#2d8bda;color:#fff;text-decoration:none;text-align:center;padding:14px 16px;margin:0 0 8px 0;font-size:28px;border-radius:2px;">
                 Discover Our Portfolio
              </a>
              <a href="https://vivanwebsolution.com/company-brochure"
                 style="display:block;background:#2d8bda;color:#fff;text-decoration:none;text-align:center;padding:14px 16px;margin:0 0 8px 0;font-size:28px;border-radius:2px;">
                 Company Brochure
              </a>
              <a href="https://vivanwebsolution.com/"
                 style="display:block;background:#2d8bda;color:#fff;text-decoration:none;text-align:center;padding:14px 16px;margin:0;font-size:28px;border-radius:2px;">
                 Visit Our Website
              </a>
            </td>
          </tr>
          <tr>
            <td style="padding:14px 12px 10px 12px;text-align:center;color:#2f2f2f;font-size:14px;">
              To stop receiving these emails, reply with "Unsubscribe".
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def _screenshot_html(company_name: str, screenshot_cid: str) -> str:
    safe_name = company_name.strip() or "Team"
    return f"""\
<!doctype html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin:0;padding:20px;background:#efefef;font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
    <tr>
      <td align="center">
        <table role="presentation" width="680" cellspacing="0" cellpadding="0" style="max-width:680px;background:#fff;border:1px solid #ddd;">
          <tr>
            <td style="padding:20px;color:#1f77d0;font-size:18px;">Hello, {safe_name}</td>
          </tr>
          <tr>
            <td style="padding:0 20px 20px 20px;">
              <img src="cid:{screenshot_cid}" alt="Campaign Image" style="width:100%;height:auto;display:block;border:0;">
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def _load_html_template(
    template_path: str | None,
    company_name: str,
    screenshot_cid: str | None = None,
    logo_cid: str | None = None,
    asset_cids: dict[str, str] | None = None,
) -> str:
    if not template_path:
        if screenshot_cid:
            return _screenshot_html(company_name, screenshot_cid=screenshot_cid)
        return _default_html(company_name, logo_cid=logo_cid, asset_cids=asset_cids)
    text = Path(template_path).read_text(encoding="utf-8")
    html = text.replace("{company_name}", company_name.strip() or "Team")
    if screenshot_cid:
        screenshot_html = f'<img src="cid:{screenshot_cid}" alt="Campaign Image" style="max-width:100%;height:auto;">'
        html = html.replace("{screenshot_html}", screenshot_html)
    if logo_cid:
        logo_html = f'<img src="cid:{logo_cid}" alt="Vivan" style="height:48px;max-width:260px;width:auto;">'
        html = html.replace("{logo_html}", logo_html)
    return html


def _load_targets(source: str | None, country: str | None, limit: int | None) -> list[tuple[str, str]]:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    clauses = ["email IS NOT NULL", "TRIM(email) <> ''"]
    params: list[str] = []

    if source:
        clauses.append("source = %s")
        params.append(source)
    if country:
        clauses.append("country = %s")
        params.append(country)

    sql = (
        "SELECT company_name, email FROM companies "
        f"WHERE {' AND '.join(clauses)} "
        "ORDER BY id ASC"
    )
    if limit and limit > 0:
        sql += f" LIMIT {int(limit)}"
    sql += ";"

    cursor.execute(sql, tuple(params))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    seen = set()
    out: list[tuple[str, str]] = []
    for row in rows:
        company_name = (row.get("company_name") or "").strip() or "Team"
        for email in _extract_emails(row.get("email") or ""):
            key = email.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append((company_name, email))
    return out


def _build_message(
    from_addr: str,
    to_addr: str,
    subject: str,
    html_body: str,
    from_name: str | None = None,
    reply_to: str | None = None,
    screenshot_path: str | None = None,
    screenshot_cid: str = "campaign_screenshot",
    logo_path: str | None = None,
    logo_cid: str = "campaign_logo",
    asset_paths: dict[str, str] | None = None,
    asset_cids: dict[str, str] | None = None,
) -> EmailMessage:
    msg = EmailMessage()
    msg["To"] = to_addr
    msg["From"] = f"{from_name} <{from_addr}>" if from_name else from_addr
    msg["Subject"] = subject
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content("Please view this email in HTML mode.")
    msg.add_alternative(html_body, subtype="html")

    if screenshot_path:
        path = Path(screenshot_path)
        if path.exists():
            ctype, _ = mimetypes.guess_type(str(path))
            maintype, subtype = ("image", "png")
            if ctype and "/" in ctype:
                maintype, subtype = ctype.split("/", 1)
            if maintype == "image":
                with path.open("rb") as fh:
                    data = fh.read()
                html_part = msg.get_payload()[-1]
                html_part.add_related(data, maintype=maintype, subtype=subtype, cid=f"<{screenshot_cid}>")
    if logo_path:
        path = Path(logo_path)
        if path.exists():
            ctype, _ = mimetypes.guess_type(str(path))
            maintype, subtype = ("image", "png")
            if ctype and "/" in ctype:
                maintype, subtype = ctype.split("/", 1)
            if maintype == "image":
                with path.open("rb") as fh:
                    data = fh.read()
                html_part = msg.get_payload()[-1]
                html_part.add_related(data, maintype=maintype, subtype=subtype, cid=f"<{logo_cid}>")
    if asset_paths and asset_cids:
        for key, rel_path in asset_paths.items():
            cid = asset_cids.get(key)
            if not cid:
                continue
            path = Path(rel_path)
            if not path.exists():
                continue
            ctype, _ = mimetypes.guess_type(str(path))
            maintype, subtype = ("image", "png")
            if ctype and "/" in ctype:
                maintype, subtype = ctype.split("/", 1)
            if maintype != "image":
                continue
            with path.open("rb") as fh:
                data = fh.read()
            html_part = msg.get_payload()[-1]
            html_part.add_related(data, maintype=maintype, subtype=subtype, cid=f"<{cid}>")
    return msg


def _connect_smtp(host: str, port: int, user: str, password: str, use_ssl: bool, use_tls: bool):
    if use_ssl:
        smtp = smtplib.SMTP_SSL(host, port, context=ssl.create_default_context(), timeout=30)
    else:
        smtp = smtplib.SMTP(host, port, timeout=30)
        smtp.ehlo()
        if use_tls:
            smtp.starttls(context=ssl.create_default_context())
            smtp.ehlo()
    smtp.login(user, password)
    return smtp


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Send campaign email to companies stored in DB.")
    parser.add_argument("--subject", required=True, help="Email subject line.")
    parser.add_argument("--source", choices=["clutch", "goodfirms"], help="Filter companies by source.")
    parser.add_argument("--country", help="Filter companies by country.")
    parser.add_argument("--limit", type=int, default=None, help="Max companies from DB before dedupe.")
    parser.add_argument("--batch-size", type=int, default=50, help="Emails per SMTP connection batch.")
    parser.add_argument("--pause-seconds", type=float, default=2.0, help="Pause between batches.")
    parser.add_argument("--template-file", help="Optional HTML file with {company_name} placeholder.")
    parser.add_argument(
        "--screenshot-path",
        help="Optional local image path to embed as the main campaign screenshot.",
    )
    parser.add_argument("--from-name", default=os.getenv("SMTP_FROM_NAME", "Vivan Web Solution"))
    parser.add_argument("--dry-run", action="store_true", help="Print targets without sending.")
    args = parser.parse_args()

    smtp_host = (os.getenv("SMTP_HOST") or "").strip()
    smtp_port = int((os.getenv("SMTP_PORT") or "587").strip())
    smtp_user = (os.getenv("SMTP_USER") or "").strip()
    smtp_pass = (os.getenv("SMTP_PASS") or "").strip()
    smtp_from = (os.getenv("SMTP_FROM") or smtp_user).strip()
    smtp_reply_to = (os.getenv("SMTP_REPLY_TO") or "").strip() or None
    smtp_use_ssl = (os.getenv("SMTP_USE_SSL") or "0").strip() in {"1", "true", "True", "yes", "YES"}
    smtp_use_tls = (os.getenv("SMTP_USE_TLS") or "1").strip() in {"1", "true", "True", "yes", "YES"}

    targets = _load_targets(args.source, args.country, args.limit)
    if not targets:
        print("[MAIL] No valid recipients found.")
        return

    print(f"[MAIL] Total unique recipients: {len(targets)}")
    for i, (company_name, email) in enumerate(targets[:10], start=1):
        print(f"  [{i}] {company_name} <{email}>")
    if len(targets) > 10:
        print(f"  ... and {len(targets) - 10} more")

    if args.dry_run:
        print("[MAIL] Dry run only. No email was sent.")
        return

    missing = [name for name, value in [
        ("SMTP_HOST", smtp_host),
        ("SMTP_USER", smtp_user),
        ("SMTP_PASS", smtp_pass),
        ("SMTP_FROM", smtp_from),
    ] if not value]
    if missing:
        raise SystemExit(f"[MAIL] Missing SMTP config: {', '.join(missing)}")

    batch_size = max(1, int(args.batch_size))
    screenshot_cid = "campaign_screenshot"
    logo_cid = "campaign_logo"
    default_logo = Path("vivan.png")
    logo_path = str(default_logo) if default_logo.exists() else None
    asset_paths = {
        "goodfirms": "goodfirms.png",
        "upwork": "upwork.png",
        "clutch": "clutch.png",
        "facebook": "facebook.png",
        "instagram": "instagram.png",
        "linkedin": "linkedin.png",
    }
    asset_cids = {
        "goodfirms": "asset_goodfirms",
        "upwork": "asset_upwork",
        "clutch": "asset_clutch",
        "facebook": "asset_facebook",
        "instagram": "asset_instagram",
        "linkedin": "asset_linkedin",
    }
    sent = 0
    failed = 0

    for start in range(0, len(targets), batch_size):
        batch = targets[start:start + batch_size]
        print(f"[MAIL] Sending batch {start + 1}-{start + len(batch)}...")
        smtp = None
        try:
            smtp = _connect_smtp(
                host=smtp_host,
                port=smtp_port,
                user=smtp_user,
                password=smtp_pass,
                use_ssl=smtp_use_ssl,
                use_tls=smtp_use_tls,
            )
            for company_name, email in batch:
                try:
                    html_body = _load_html_template(
                        args.template_file,
                        company_name=company_name,
                        logo_cid=logo_cid if logo_path else None,
                        asset_cids=asset_cids,
                    )
                    if args.screenshot_path:
                        html_body = _load_html_template(
                            args.template_file,
                            company_name=company_name,
                            screenshot_cid=screenshot_cid,
                            logo_cid=logo_cid if logo_path else None,
                            asset_cids=asset_cids,
                        )
                    msg = _build_message(
                        from_addr=smtp_from,
                        to_addr=email,
                        subject=args.subject,
                        html_body=html_body,
                        from_name=args.from_name,
                        reply_to=smtp_reply_to,
                        screenshot_path=args.screenshot_path,
                        screenshot_cid=screenshot_cid,
                        logo_path=logo_path,
                        logo_cid=logo_cid,
                        asset_paths=asset_paths,
                        asset_cids=asset_cids,
                    smtp.send_message(msg)
                    )
                    sent += 1
                    print(f"  [OK] {email}")
                except Exception as err:
                    failed += 1
                    print(f"  [FAIL] {email} | {err}")
        finally:
            if smtp is not None:
                try:
                    smtp.quit()
                except Exception:
                    pass

        if start + batch_size < len(targets):
            time.sleep(max(0.0, args.pause_seconds))

    print(f"[MAIL] Done. Sent={sent}, Failed={failed}, Total={len(targets)}")


if __name__ == "__main__":
    main()
  