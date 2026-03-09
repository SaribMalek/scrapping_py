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
        f'<img src="cid:{logo_cid}" alt="Vivan Web Solution" style="height:62px;max-width:260px;width:auto;display:block;margin:0 auto;border:0;object-fit:contain;">'
        if logo_cid
        else '<div style="font-size:30px;font-weight:700;color:#2d2d2d;line-height:1;">Vivan</div>'
    )
    gf_html = (
        f'<a href="https://www.goodfirms.co/company/vivan-web-solution-pvt-ltd" target="_blank" rel="noopener noreferrer"><img src="cid:{asset_cids["goodfirms"]}" alt="GoodFirms" style="height:30px;max-width:150px;width:auto;vertical-align:middle;border:0;object-fit:contain;"></a>'
        if asset_cids.get("goodfirms")
        else '<a href="https://www.goodfirms.co/company/vivan-web-solution-pvt-ltd" target="_blank" rel="noopener noreferrer" style="color:#346ea5;text-decoration:none;">GoodFirms</a>'
    )
    upwork_html = (
        f'<a href="https://www.upwork.com/ag/vivan/" target="_blank" rel="noopener noreferrer"><img src="cid:{asset_cids["upwork"]}" alt="Upwork" style="height:24px;max-width:112px;width:auto;vertical-align:middle;border:0;object-fit:contain;"></a>'
        if asset_cids.get("upwork")
        else '<a href="https://www.upwork.com/ag/vivan/" target="_blank" rel="noopener noreferrer" style="color:#7bb340;text-decoration:none;">upwork</a>'
    )
    clutch_html = (
        f'<a href="https://clutch.co/profile/vivan-web-solution#highlights" target="_blank" rel="noopener noreferrer"><img src="cid:{asset_cids["clutch"]}" alt="Clutch" style="height:26px;max-width:105px;width:auto;vertical-align:middle;border:0;object-fit:contain;"></a>'
        if asset_cids.get("clutch")
        else '<a href="https://clutch.co/profile/vivan-web-solution#highlights" target="_blank" rel="noopener noreferrer" style="color:#255f66;text-decoration:none;">Clutch</a>'
    )
    fb_html = (
        f'<a href="https://www.facebook.com/VivanWebSolution/" target="_blank" rel="noopener noreferrer"><img src="cid:{asset_cids["facebook"]}" alt="Facebook" style="height:22px;max-width:90px;width:auto;vertical-align:middle;border:0;object-fit:contain;"></a>'
        if asset_cids.get("facebook")
        else '<a href="https://www.facebook.com/VivanWebSolution/" target="_blank" rel="noopener noreferrer" style="font-weight:700;color:#1b4f9c;text-decoration:none;">facebook</a>'
    )
    ig_html = (
        f'<a href="https://www.instagram.com/vivanweb/?hl=en" target="_blank" rel="noopener noreferrer"><img src="cid:{asset_cids["instagram"]}" alt="Instagram" style="height:22px;max-width:100px;width:auto;vertical-align:middle;border:0;object-fit:contain;"></a>'
        if asset_cids.get("instagram")
        else '<a href="https://www.instagram.com/vivanweb/?hl=en" target="_blank" rel="noopener noreferrer" style="font-weight:700;color:#cf2e7e;text-decoration:none;">Instagram</a>'
    )
    li_html = (
        f'<a href="https://www.linkedin.com/company/vivan-websolution-pvt-ltd/" target="_blank" rel="noopener noreferrer"><img src="cid:{asset_cids["linkedin"]}" alt="LinkedIn" style="height:22px;max-width:90px;width:auto;vertical-align:middle;border:0;object-fit:contain;"></a>'
        if asset_cids.get("linkedin")
        else '<a href="https://www.linkedin.com/company/vivan-websolution-pvt-ltd/" target="_blank" rel="noopener noreferrer" style="font-weight:700;color:#1d63ab;text-decoration:none;">LinkedIn</a>'
    )
    return f"""\
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Vivan Web Solution - Introduction</title>
  <style>
    body {{
      margin: 0;
      padding: 0;
      background-color: #eef2f7;
      font-family: Arial, Helvetica, sans-serif;
    }}
    .email-wrapper {{
      width: 100%;
      max-width: 600px;
      margin: 0 auto;
      background: #ffffff;
      border-radius: 12px;
      overflow: hidden;
    }}
    .header {{
      text-align: center;
      padding: 24px 24px 16px 24px;
      border-bottom: 3px solid #1a73e8;
    }}
    .greeting {{
      padding: 20px 24px 0 24px;
      color: #1a73e8;
      font-size: 28px;
      line-height: 1.3;
      font-weight: 700;
    }}
    .greeting-divider {{
      margin: 10px 24px 18px 24px;
      height: 3px;
      background: linear-gradient(to right, #1a73e8, #90caf9);
    }}
    .card {{
      margin: 0 24px 12px 24px;
      background: #f8faff;
      border: 1px solid #e3ecf8;
      border-radius: 8px;
      padding: 15px 16px;
      color: #2f3640;
      font-size: 14px;
      line-height: 1.75;
    }}
    .section-title {{
      color: #1a73e8;
      font-size: 24px;
      line-height: 1.3;
      font-weight: 700;
      padding: 10px 24px 10px 24px;
      text-align: center;
    }}
    .reviews-card {{
      margin: 0 24px 14px 24px;
      background: #f8faff;
      border: 1px solid #e3ecf8;
      border-radius: 8px;
      padding: 16px 12px;
      text-align: center;
    }}
    .social-title {{
      color: #1a73e8;
      font-size: 24px;
      line-height: 1.3;
      font-weight: 700;
      padding: 10px 24px 10px 24px;
      text-align: center;
    }}
    .footer-card {{
      margin: 8px 0 0 0;
      background: #f0f6ff;
      border-top: 1px solid #dce8fb;
      padding: 18px 22px;
      color: #2f3640;
      font-size: 14px;
      line-height: 1.7;
      text-align: center;
    }}
    .unsubscribe-bar {{
      text-align: center;
      padding: 12px 24px 20px 24px;
      background: #ffffff;
    }}
    .unsubscribe-bar p {{
      font-size: 11.5px;
      color: #999999;
      margin: 0 0 8px 0;
      line-height: 1.5;
    }}
    .unsubscribe-link {{
      font-size: 12px;
      color: #e53935 !important;
      text-decoration: none;
      border: 1px solid #e53935;
      padding: 4px 14px;
      border-radius: 20px;
      display: inline-block;
    }}
  </style>
</head>
<body>
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#eef2f7;">
    <tr>
      <td align="center" style="padding:28px 10px;">
        <table role="presentation" class="email-wrapper" width="600" cellspacing="0" cellpadding="0" style="width:600px;max-width:600px;background:#ffffff;">
          <tr>
            <td class="header">
              {logo_html}
            </td>
          </tr>
          <tr>
            <td class="greeting">
              Hello, {safe_name}
            </td>
          </tr>
          <tr>
            <td>
              <div class="greeting-divider"></div>
            </td>
          </tr>
          <tr>
            <td>
              <div class="card">
                I hope this email finds you well and excited! I represent
                <span style="color:#1a73e8;font-weight:700;">Vivan Web Solution Pvt. Ltd.</span>, an innovative IT Web Development company based in India, specialized in crafting exceptional web experiences. With
                <span style="color:#1a73e8;font-weight:700;">7 years of experience</span>, we've earned the trust of clients from across
                <span style="color:#1a73e8;font-weight:700;">10+ countries</span>.
              </div>
            </td>
          </tr>
          <tr>
            <td>
              <div class="card">
                Our dynamic team consists of
                <span style="color:#1a73e8;font-weight:700;">20+ skilled developers</span> dedicated to connecting India's top
                <span style="color:#1a73e8;font-weight:700;">3.5% tech talents</span> with global opportunities.
              </div>
            </td>
          </tr>
          <tr>
            <td>
              <div class="card">
                We believe you are an ideal client for us, and we are enthusiastic about creating a valuable web app that surpasses your expectations.
              </div>
            </td>
          </tr>
          <tr>
            <td class="section-title">Discover what our clients say:</td>
          </tr>
          <tr>
            <td>
              <div class="reviews-card">
                <table role="presentation" cellspacing="0" cellpadding="0" align="center">
                  <tr>
                    <td style="padding:0 10px;">{gf_html}</td>
                    <td style="padding:0 10px;">{upwork_html}</td>
                    <td style="padding:0 10px;">{clutch_html}</td>
                  </tr>
                </table>
              </div>
            </td>
          </tr>
          <tr>
            <td class="social-title">Connect with us on Social Media:</td>
          </tr>
          <tr>
            <td>
              <div class="reviews-card">
                <table role="presentation" cellspacing="0" cellpadding="0" align="center">
                  <tr>
                    <td style="padding:0 10px;">{fb_html}</td>
                    <td style="padding:0 10px;">{ig_html}</td>
                    <td style="padding:0 10px;">{li_html}</td>
                  </tr>
                </table>
              </div>
            </td>
          </tr>
          <tr>
            <td>
              <div class="footer-card">
                If our services intrigue you, please don't hesitate to
                <a href="mailto:info@vivanwebsolution.com" style="color:#1a73e8;text-decoration:none;font-weight:600;">contact us</a>
                for further discussions. We are excited to hear from you.
              </div>
              <div class="unsubscribe-bar">
                <p>You received this email because you are registered with Vivan Web Solution.</p>
                <a href="https://vivanwebsolution.com/unsubscribe/?id=%204135" class="unsubscribe-link" style="color:#e53935 !important;">Unsubscribe</a>
              </div>
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
<body style="margin:0;padding:0;background:#ebebeb;font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#ebebeb;">
    <tr>
      <td align="center" style="padding:10px 0;">
        <table role="presentation" width="680" cellspacing="0" cellpadding="0" style="width:680px;max-width:680px;background:#f3f3f3;">
          <tr>
            <td style="padding:10px 12px;color:#1f83d7;font-size:26px;line-height:1.25;font-weight:500;">Hello, {safe_name}</td>
          </tr>
          <tr>
            <td style="padding:0 12px 12px 12px;">
              <img src="cid:{screenshot_cid}" alt="Campaign Image" style="width:100%;height:auto;display:block;border:0;background:#ffffff;">
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


def _load_send_history(path: str) -> set[str]:
    p = Path(path)
    if not p.exists():
        return set()
    lines = p.read_text(encoding="utf-8").splitlines()
    out: set[str] = set()
    for line in lines:
        item = line.strip()
        if not item:
            continue
        out.add(item)
    return out


def _append_send_history(path: str, key: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(f"{key}\n")


def _dedupe_key(campaign_id: str, email: str) -> str:
    return f"{campaign_id.strip().lower()}|{email.strip().lower()}"


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
    parser.add_argument("--test-email", help="Send a single test email to this address.")
    parser.add_argument(
        "--dedupe-history-file",
        default="output/email_send_history.log",
        help="Skip emails already sent for the same campaign using this history file.",
    )
    parser.add_argument(
        "--campaign-id",
        default="",
        help="Optional stable campaign ID for dedupe. Default uses normalized subject.",
    )
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

    if args.test_email:
        test_email = args.test_email.strip().lower()
        if not _is_valid_email(test_email):
            raise SystemExit(f"[MAIL] Invalid --test-email value: {args.test_email}")
        targets = [("Team", test_email)]
    else:
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
    campaign_id = (args.campaign_id or "").strip().lower() or args.subject.strip().lower()
    send_history = _load_send_history(args.dedupe_history_file)
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
    skipped_duplicate = 0
    filtered_targets: list[tuple[str, str]] = []

    for company_name, email in targets:
        key = _dedupe_key(campaign_id, email)
        if key in send_history:
            skipped_duplicate += 1
            continue
        filtered_targets.append((company_name, email))

    if skipped_duplicate:
        print(f"[MAIL] Skipping already-sent recipients: {skipped_duplicate}")
    if not filtered_targets:
        print("[MAIL] Nothing to send after duplicate filtering.")
        return

    for start in range(0, len(filtered_targets), batch_size):
        batch = filtered_targets[start:start + batch_size]
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
        except Exception as err:
            failed += len(batch)
            print(f"[MAIL] Batch connection failed ({len(batch)} recipients): {err}")
            continue

        try:
            for company_name, email in batch:
                try:
                    dedupe_key = _dedupe_key(campaign_id, email)
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
                    )
                    smtp.send_message(msg)
                    send_history.add(dedupe_key)
                    _append_send_history(args.dedupe_history_file, dedupe_key)
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

        if start + batch_size < len(filtered_targets):
            time.sleep(max(0.0, args.pause_seconds))

    print(
        f"[MAIL] Done. Sent={sent}, Failed={failed}, SkippedDuplicate={skipped_duplicate}, Total={len(targets)}"
    )


if __name__ == "__main__":
    main()

