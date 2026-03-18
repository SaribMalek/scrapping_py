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
import uuid
from email.message import EmailMessage
from email.utils import make_msgid, formatdate
from pathlib import Path

from dotenv import load_dotenv

from database import ensure_email_tracking_columns, get_connection, reset_email_flags

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
    tracking_pixel_html: str = "",
) -> str:
    safe_name = company_name.strip() or "Team"
    asset_cids = asset_cids or {}
    
    import random
    
    # Professional color themes (Light Background + High Contrast Bold Theme Color)
    # These are curated pairs to ensure perfect readability and a premium feel
    color_themes = [
        {"bg": "#f0f8ff", "theme": "#0052cc"}, # Alice Blue & Corporate Blue
        {"bg": "#f8f9fa", "theme": "#212529"}, # Off-White & Charcoal Text
        {"bg": "#f5f3ff", "theme": "#5b21b6"}, # Soft Violet & Deep Purple
        {"bg": "#ecfdf5", "theme": "#047857"}, # Mint Forest & Emerald Green
        {"bg": "#fffbeb", "theme": "#b45309"}, # Warm Ivory & Amber/Gold
        {"bg": "#fdf4ff", "theme": "#be185d"}, # Blush Pink & Magenta
        {"bg": "#f0fdf4", "theme": "#15803d"}, # Honeydew & Evergreen
        {"bg": "#eff6ff", "theme": "#4338ca"}, # Ice Blue & Indigo
        {"bg": "#fef2f2", "theme": "#b91c1c"}, # Light Rose & Crimson Red
        {"bg": "#fdf8f6", "theme": "#c2410c"}, # Light Peach & Burnt Orange
    ]
    chosen_theme = random.choice(color_themes)
    bg_color = chosen_theme["bg"]
    theme_color = chosen_theme["theme"]

    # Random font family
    font_options = [
        {
            "css": "'Poppins', 'Segoe UI', Tahoma, Arial, sans-serif",
            "url": "https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap",
        },
        {
            "css": "'Inter', 'Helvetica Neue', Arial, sans-serif",
            "url": "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
        },
        {
            "css": "'Nunito', 'Segoe UI', Arial, sans-serif",
            "url": "https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap",
        },
        {
            "css": "'Lato', 'Helvetica Neue', Arial, sans-serif",
            "url": "https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap",
        },
        {
            "css": "'Raleway', 'Segoe UI', Arial, sans-serif",
            "url": "https://fonts.googleapis.com/css2?family=Raleway:wght@400;500;600;700&display=swap",
        },
    ]
    chosen_font = random.choice(font_options)
    font_stack = chosen_font["css"]
    google_font_url = chosen_font["url"]
    logo_html = (
        f'<img src="cid:{logo_cid}" alt="Vivan Web Solution" style="display:block;width:100%;max-width:280px;height:auto;margin:0 auto;border:0;">'
        if logo_cid
        else (
            '<table role="presentation" cellspacing="0" cellpadding="0" align="center">'
            '<tr>'
            '<td style="background:linear-gradient(135deg,#0052cc 0%,#002b66 100%);color:#ffffff;font-size:26px;'
            'font-weight:900;font-family:\'Segoe UI\',Tahoma,Arial,sans-serif;width:54px;height:54px;text-align:center;'
            'border-radius:12px;box-shadow:0 6px 15px rgba(0,82,204,0.2);">VM</td>'
            '<td style="padding-left:12px;text-align:left;">'
            '<div style="font-family:\'Segoe UI\',Tahoma,Arial,sans-serif;font-size:34px;font-weight:900;color:#003380;line-height:1;">Vivan</div>'
            '<div style="font-size:10px;color:#4d7cc7;font-weight:600;letter-spacing:1.2px;text-transform:uppercase;">WEB SOLUTION PVT. LTD.</div>'
            '</td>'
            '</tr>'
            '</table>'
        )
    )
    review_row_html = (
        f'<a href="https://www.goodfirms.co/company/vivan-web-solution-pvt-ltd" target="_blank" rel="noopener noreferrer" style="display:inline-block;text-decoration:none;">'
        f'<img src="cid:{asset_cids["review_row"]}" alt="GoodFirms, Upwork and Clutch" style="display:block;width:100%;max-width:430px;height:auto;margin:0 auto;border:0;"></a>'
        if asset_cids.get("review_row")
        else None
    )
    gf_html = (
        f'<a href="https://www.goodfirms.co/company/vivan-web-solution-pvt-ltd" target="_blank" rel="noopener noreferrer" style="display:inline-block;text-decoration:none;">'
        f'<img src="cid:{asset_cids["goodfirms"]}" alt="GoodFirms" style="height:30px;max-width:150px;width:auto;vertical-align:middle;border:0;"></a>'
        if asset_cids.get("goodfirms")
        else '<a href="https://www.goodfirms.co/company/vivan-web-solution-pvt-ltd" target="_blank" rel="noopener noreferrer" style="color:#4b8bfa;text-decoration:none;font-weight:700;">GoodFirms</a>'
    )
    upwork_html = (
        f'<a href="https://www.upwork.com/ag/vivan/" target="_blank" rel="noopener noreferrer" style="display:inline-block;text-decoration:none;">'
        f'<img src="cid:{asset_cids["upwork"]}" alt="Upwork" style="height:24px;max-width:112px;width:auto;vertical-align:middle;border:0;"></a>'
        if asset_cids.get("upwork")
        else '<a href="https://www.upwork.com/ag/vivan/" target="_blank" rel="noopener noreferrer" style="color:#6fda44;text-decoration:none;font-weight:700;">Upwork</a>'
    )
    clutch_html = (
        f'<a href="https://clutch.co/profile/vivan-web-solution#highlights" target="_blank" rel="noopener noreferrer" style="display:inline-block;text-decoration:none;">'
        f'<img src="cid:{asset_cids["clutch"]}" alt="Clutch" style="height:26px;max-width:105px;width:auto;vertical-align:middle;border:0;"></a>'
        if asset_cids.get("clutch")
        else '<a href="https://clutch.co/profile/vivan-web-solution#highlights" target="_blank" rel="noopener noreferrer" style="color:#214f52;text-decoration:none;font-weight:900;">Clutch</a>'
    )
    social_row_html = (
        f'<a href="https://www.linkedin.com/company/vivan-websolution-pvt-ltd/" target="_blank" rel="noopener noreferrer" style="display:inline-block;text-decoration:none;">'
        f'<img src="cid:{asset_cids["social_row"]}" alt="Facebook, Instagram and LinkedIn" style="display:block;width:100%;max-width:308px;height:auto;margin:0 auto;border:0;"></a>'
        if asset_cids.get("social_row")
        else None
    )
    fb_html = (
        f'<a href="https://www.facebook.com/VivanWebSolution/" target="_blank" rel="noopener noreferrer" style="display:inline-block;text-decoration:none;">'
        f'<img src="cid:{asset_cids["facebook"]}" alt="Facebook" style="height:22px;max-width:90px;width:auto;vertical-align:middle;border:0;"></a>'
        if asset_cids.get("facebook")
        else '<a href="https://www.facebook.com/VivanWebSolution/" target="_blank" rel="noopener noreferrer" style="font-weight:700;color:#1b4f9c;text-decoration:none;">facebook</a>'
    )
    ig_html = (
        f'<a href="https://www.instagram.com/vivanweb/?hl=en" target="_blank" rel="noopener noreferrer" style="display:inline-block;text-decoration:none;">'
        f'<img src="cid:{asset_cids["instagram"]}" alt="Instagram" style="height:22px;max-width:100px;width:auto;vertical-align:middle;border:0;"></a>'
        if asset_cids.get("instagram")
        else '<a href="https://www.instagram.com/vivanweb/?hl=en" target="_blank" rel="noopener noreferrer" style="font-weight:700;color:#cf2e7e;text-decoration:none;">Instagram</a>'
    )
    li_html = (
        f'<a href="https://www.linkedin.com/company/vivan-websolution-pvt-ltd/" target="_blank" rel="noopener noreferrer" style="display:inline-block;text-decoration:none;">'
        f'<img src="cid:{asset_cids["linkedin"]}" alt="LinkedIn" style="height:22px;max-width:90px;width:auto;vertical-align:middle;border:0;"></a>'
        if asset_cids.get("linkedin")
        else '<a href="https://www.linkedin.com/company/vivan-websolution-pvt-ltd/" target="_blank" rel="noopener noreferrer" style="font-weight:700;color:#1d63ab;text-decoration:none;">LinkedIn</a>'
    )
    return f"""\
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Vivan Web Solution Pvt. Ltd. - Newsletter</title>
  <link href="{google_font_url}" rel="stylesheet">
  <style>
    body {{
      margin: 0;
      padding: 40px 15px;
      background-color: #ffffff;
      font-family: {font_stack};
      color: #1e3a5f;
    }}
    table, td, div, p, a, span, h1, h2 {{
      font-family: {font_stack} !important;
    }}
    .email-container {{
      width: 100%;
      max-width: 650px;
      margin: 0 auto;
      background-color: {bg_color};
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 10px 40px rgba(10, 40, 90, 0.08);
      border: 1px solid #e1eaf5;
    }}
    .header {{
      text-align: center;
      padding: 40px 20px 30px;
      background-color: transparent;
    }}
    .main-divider {{
      height: 4px;
      background: {theme_color};
      width: 100%;
    }}
    .content-body {{
      padding: 40px 50px;
    }}
    .greeting {{
      color: {theme_color};
      font-size: 26px;
      margin: 0 0 12px 0;
      font-weight: 700;
      line-height: 1.3;
    }}
    .greeting-line {{
      height: 2px;
      background-color: {theme_color};
      width: 100%;
      margin-bottom: 30px;
      border-radius: 2px;
    }}
    .info-box {{
      background-color: rgba(255, 255, 255, 0.4);
      border: 1px solid #cce0ff;
      border-radius: 8px;
      padding: 20px 25px;
      margin-bottom: 20px;
      box-shadow: inset 0 2px 4px rgba(0, 82, 204, 0.01);
    }}
    .info-box p {{
      margin: 0;
      font-size: 16px;
      line-height: 1.75;
      color: inherit;
    }}
    .text-primary {{
      color: {theme_color};
      font-weight: 800;
      text-decoration: none;
    }}
    .section-center {{
      text-align: center;
      margin-top: 35px;
    }}
    .pill-btn {{
      display: inline-block;
      padding: 12px 30px;
      border-radius: 50px;
      font-weight: 700;
      font-size: 15px;
      text-decoration: none;
      color: #ffffff !important;
    }}
    .btn-theme {{
      background: {theme_color};
    }}
    .brand-container {{
      display: block;
      border: 1px solid #d1e0ff;
      border-radius: 12px;
      padding: 30px 40px;
      margin-top: 25px;
      background: #ffffff;
      text-align: center;
      max-width: 550px;
      margin-left: auto;
      margin-right: auto;
      box-shadow: none;
    }}
    .footer-section {{
      background-color: #f2f7ff;
      padding: 45px 40px;
      text-align: center;
    }}
    .footer-desc {{
      font-size: 15px;
      color: #3b5f8c;
      line-height: 1.6;
      margin: 0 0 35px 0;
    }}
    .footer-links {{
      text-align: center;
      margin-bottom: 25px;
    }}
    .footer-btn {{
      background-color: #ffffff;
      color: {theme_color} !important;
      border: 1px solid {theme_color};
      padding: 14px 24px;
      font-size: 14px;
      font-weight: 600;
      border-radius: 8px;
      text-decoration: none;
      display: inline-block;
      margin: 6px 4px;
    }}
    .legal-text {{
      font-size: 12px;
      color: #6688b3;
      margin: 0 0 25px 0;
    }}
    .unsubscribe-btn {{
      display: inline-block;
      padding: 10px 30px;
      border: 1.5px solid {theme_color};
      color: {theme_color} !important;
      border-radius: 50px;
      text-decoration: none;
      font-size: 13px;
      font-weight: 600;
      background-color: transparent;
    }}
    @media (max-width: 650px) {{
      body {{
        padding: 18px 8px;
      }}
      .content-body {{
        padding: 30px 20px;
      }}
      .brand-container {{
        padding: 20px;
      }}
      .footer-section {{
        padding: 35px 20px;
      }}
      .footer-btn {{
        width: 100%;
        box-sizing: border-box;
      }}
      .greeting {{
        font-size: 22px;
      }}
    }}
  </style>
</head>
<body>
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#ffffff; font-family:{font_stack};">
    <tr>
      <td align="center" style="padding:0;">
        <table role="presentation" class="email-container" width="650" cellspacing="0" cellpadding="0" style="width:650px;max-width:650px;background:{bg_color};">
          <tr>
            <td class="header">
              {logo_html}
            </td>
          </tr>
          <tr>
            <td><div class="main-divider"></div></td>
          </tr>
          <tr>
            <td class="content-body">
              <h1 class="greeting">Hello {safe_name},</h1>
              <div class="greeting-line"></div>

              <div class="info-box">
                <p>I hope this email finds you well.</p>
              </div>

              <div class="info-box">
                <p>We represent <span class="text-primary">Vivan Web Solution Pvt. Ltd.</span>, an innovative IT and Web Development company based in India, specializing in building high-quality and scalable web applications. With <span class="text-primary">10+ years of experience</span>, we have successfully delivered projects for clients across <span class="text-primary">20+ countries</span>.</p>
              </div>

              <div class="info-box">
                <p>Our team of <span class="text-primary">25+ skilled developers</span> focuses on delivering reliable, high-performance solutions while connecting some of India's top tech talent with global businesses. We work with modern technologies including <span class="text-primary">PHP, Laravel, Symfony, Node.js, React, Vue, and AI-driven solutions</span>.</p>
              </div>

              <div class="info-box">
                <p>We would be excited to collaborate with you and help build a powerful, scalable web application that meets your business goals and exceeds expectations.</p>
              </div>

              <div class="info-box">
                <p>We would be happy to discuss your requirements and explore how we can support your project.</p>
              </div>

              <div class="section-center" style="margin-top:15px;margin-bottom:25px;">
                <span style="display:inline-block;background:{theme_color};color:#ffffff;padding:7px 22px;border-radius:30px;font-size:15px;font-weight:700;letter-spacing:0.3px;margin-bottom:20px;text-transform:uppercase;">
                  &#128197; You can schedule a meeting with me on :
                </span>
                <br />
                <a href="https://calendly.com/nirav-patel-vivanwebsolution/30min" class="footer-btn" target="_blank" rel="noopener noreferrer" style="display:inline-block;font-size:16px;">
                  Schedule a Meeting
                </a>
              </div>

              <div class="section-center" style="margin-top:35px;">
                <div class="pill-btn btn-theme">&#11088; Discover What Our Clients Say</div>
                <div class="brand-container">
                  {review_row_html or f'''
                  <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center" style="margin:0 auto;width:100%;">
                    <tr>
                      <td align="left" style="width:33.33%;vertical-align:middle;padding:0;">{gf_html}</td>
                      <td align="center" style="width:33.33%;vertical-align:middle;padding:0;">{upwork_html}</td>
                      <td align="right" style="width:33.33%;vertical-align:middle;padding:0;">{clutch_html}</td>
                    </tr>
                  </table>
                  '''}
                </div>
              </div>

              <div class="section-center" style="margin-top:35px;margin-bottom:40px;">
                <div class="pill-btn btn-theme">&#128279; Connect With Us On Social Media</div>
                <div class="brand-container">
                  {social_row_html or f'''
                  <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center" style="margin:0 auto;width:100%;">
                    <tr>
                      <td align="left" style="width:33.33%;vertical-align:middle;padding:0;">{fb_html}</td>
                      <td align="center" style="width:33.33%;vertical-align:middle;padding:0;">{ig_html}</td>
                      <td align="right" style="width:33.33%;vertical-align:middle;padding:0;">{li_html}</td>
                    </tr>
                  </table>
                  '''}
                </div>
              </div>
            </td>
          </tr>
          <tr>
            <td class="footer-section">
              <p class="footer-desc">
                If our services intrigue you, please don't hesitate to <a href="mailto:info@vivanwebsolution.com" class="text-primary" style="color:{theme_color};font-weight:700;">contact us</a>
                for further discussions.<br />We are excited to hear from you.
              </p>

              <div class="footer-links">
                <a href="https://vivanwebsolution.com/portfolio/" class="footer-btn" target="_blank" rel="noopener noreferrer">Discover Our Portfolio</a>
                <a href="https://vivanwebsolution.com/vivanwebsolution.pdf" class="footer-btn" target="_blank" rel="noopener noreferrer">Company Brochure</a>
                <a href="https://vivanwebsolution.com/" class="footer-btn" target="_blank" rel="noopener noreferrer">Visit Our Website</a>
              </div>

              <p class="legal-text">You received this email because you are registered with Vivan Web Solution.</p>

              <a href="https://vivanwebsolution.com/unsubscribe/?id=%204135" class="unsubscribe-btn" target="_blank" rel="noopener noreferrer">Unsubscribe</a>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
""".replace("</body>", f"{tracking_pixel_html}</body>")

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
            <td style="padding:10px 12px;color:#1f83d7;font-size:26px;line-height:1.25;font-weight:500;">Hello {safe_name},</td>
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
    tracking_pixel_html: str = "",
) -> str:
    if not template_path:
        if screenshot_cid:
            return _inject_tracking_pixel(
                _screenshot_html(company_name, screenshot_cid=screenshot_cid),
                tracking_pixel_html,
            )
        return _default_html(
            company_name,
            logo_cid=logo_cid,
            asset_cids=asset_cids,
            tracking_pixel_html=tracking_pixel_html,
        )
    text = Path(template_path).read_text(encoding="utf-8")
    html = text.replace("{company_name}", company_name.strip() or "Team")
    if screenshot_cid:
        screenshot_html = f'<img src="cid:{screenshot_cid}" alt="Campaign Image" style="max-width:100%;height:auto;">'
        html = html.replace("{screenshot_html}", screenshot_html)
    if logo_cid:
        logo_html = f'<img src="cid:{logo_cid}" alt="Vivan" style="display:block;width:100%;max-width:280px;height:auto;margin:0 auto;border:0;">'
        html = html.replace("{logo_html}", logo_html)
    else:
        html = html.replace("{logo_html}", '<div style="display:inline-flex;align-items:center;justify-content:center;gap:15px;"><div style="background:linear-gradient(135deg,#0052cc 0%,#002b66 100%);color:white;font-size:32px;font-weight:900;font-family:\'Roboto\',sans-serif;width:65px;height:65px;display:flex;align-items:center;justify-content:center;border-radius:16px;box-shadow:0 6px 15px rgba(0,82,204,0.2);">VM</div><div style="text-align:left;display:flex;flex-direction:column;justify-content:center;"><h2 style="font-family:\'Roboto\',sans-serif;font-size:42px;font-weight:900;color:#003380;margin:0;line-height:1;letter-spacing:-1px;">Vivan</h2><span style="font-size:11px;color:#4d7cc7;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;margin-top:4px;">WEB SOLUTION PVT. LTD.</span></div></div>')

    import random

    # ── Random background colour (very light, professional) ──────────────────
    bg_colors = [
        "#f0f6fc", "#f5f7fa", "#f8f9fa", "#f4f6f8",
        "#fdf6ff", "#fff8f0", "#f0fff4", "#f0f4ff",
        "#fff5f5", "#f5f0ff",
    ]
    bg_color = random.choice(bg_colors)

    # ── Random font family (all web-safe or Google Fonts) ────────────────────
    font_options = [
        {
            "css": "'Poppins', 'Segoe UI', Arial, sans-serif",
            "url": "https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap",
        },
        {
            "css": "'Inter', 'Helvetica Neue', Arial, sans-serif",
            "url": "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
        },
        {
            "css": "'Nunito', 'Segoe UI', Arial, sans-serif",
            "url": "https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap",
        },
        {
            "css": "'Lato', 'Helvetica Neue', Arial, sans-serif",
            "url": "https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap",
        },
        {
            "css": "'Raleway', 'Segoe UI', Arial, sans-serif",
            "url": "https://fonts.googleapis.com/css2?family=Raleway:wght@400;500;600;700&display=swap",
        },
    ]
    chosen_font = random.choice(font_options)

    html = html.replace("{bg_color}", bg_color)
    html = html.replace("{font_family}", chosen_font["css"])
    html = html.replace("{google_font_url}", chosen_font["url"])

    return _inject_tracking_pixel(html, tracking_pixel_html)


def _load_targets(source: str | None, country: str | None, limit: int | None) -> list[tuple[int, str, str]]:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    clauses = ["email IS NOT NULL", "TRIM(email) <> ''", "COALESCE(email_sent, 0) = 0"]
    params: list[str] = []

    if source:
        clauses.append("source = %s")
        params.append(source)
    if country:
        clauses.append("country = %s")
        params.append(country)

    sql = (
        "SELECT id, company_name, email FROM companies "
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
    out: list[tuple[int, str, str]] = []
    for row in rows:
        company_id = int(row["id"])
        company_name = (row.get("company_name") or "").strip() or "Team"
        for email in _extract_emails(row.get("email") or ""):
            key = email.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append((company_id, company_name, email))
    return out


def _inject_tracking_pixel(html: str, tracking_pixel_html: str) -> str:
    if not tracking_pixel_html:
        return html
    marker = "</body>"
    lower_html = html.lower()
    idx = lower_html.rfind(marker)
    if idx >= 0:
        return html[:idx] + tracking_pixel_html + html[idx:]
    return html + tracking_pixel_html


def _inject_body_prefix(html: str, body_prefix_html: str) -> str:
    if not body_prefix_html:
        return html
    match = re.search(r"<body\b[^>]*>", html, flags=re.IGNORECASE)
    if not match:
        return body_prefix_html + html
    return html[:match.end()] + body_prefix_html + html[match.end():]


def _generate_tracking_token() -> str:
    return uuid.uuid4().hex


def _build_tracking_pixel_html(base_url: str | None, token: str | None, email: str | None) -> str:
    base = (base_url or "").strip()
    recipient_email = (email or "").strip()
    if not base or not token or not recipient_email:
        return ""
    separator = "&" if "?" in base else "?"
    src = f"{base}{separator}e={recipient_email}&t={token}"
    return (
        f'<img src="{src}" alt="" width="1" height="1" '
        'style="display:block;width:1px;height:1px;border:0;opacity:0;" />'
    )


def _mark_email_sent(company_id: int) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE companies
        SET email_sent = 1,
            email_sent_at = NOW()
        WHERE id = %s
        """,
        (int(company_id),),
    )
    conn.commit()
    cursor.close()
    conn.close()


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
    attachment_paths: list[str] | None = None,
) -> EmailMessage:
    msg = EmailMessage()
    msg["To"] = to_addr
    msg["From"] = f"{from_name} <{from_addr}>" if from_name else from_addr
    msg["Subject"] = subject
    
    domain = from_addr.split('@')[-1] if '@' in from_addr else "vivanwebsolution.com"
    msg["Message-ID"] = make_msgid(domain=domain)
    msg["Date"] = formatdate(localtime=True)
    
    if reply_to:
        msg["Reply-To"] = reply_to
    fallback_text = (
        "Hello,\n\n"
        "We have sent an HTML email. If you cannot view it, please enable HTML or contact us at info@vivanwebsolution.com.\n\n"
        "Best regards,\n"
        "Vivan Web Solution Pvt. Ltd."
    )
    msg.set_content(fallback_text)
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
    if attachment_paths:
        for rel_path in attachment_paths:
            path = Path(rel_path)
            if not path.exists():
                continue
            ctype, _ = mimetypes.guess_type(str(path))
            maintype, subtype = ("application", "octet-stream")
            if ctype and "/" in ctype:
                maintype, subtype = ctype.split("/", 1)
            with path.open("rb") as fh:
                data = fh.read()
            msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=path.name)
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


def _connect_smtp(
    host: str,
    port: int,
    user: str,
    password: str,
    use_ssl: bool,
    use_tls: bool,
    timeout_seconds: float = 180.0,
):
    if use_ssl:
        smtp = smtplib.SMTP_SSL(host, port, context=ssl.create_default_context(), timeout=timeout_seconds)
    else:
        smtp = smtplib.SMTP(host, port, timeout=timeout_seconds)
        smtp.ehlo()
        if use_tls:
            smtp.starttls(context=ssl.create_default_context())
            smtp.ehlo()
    smtp.login(user, password)
    return smtp


def _send_completion_copy(
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_pass: str,
    smtp_use_ssl: bool,
    smtp_use_tls: bool,
    smtp_timeout: float,
    smtp_from: str,
    smtp_reply_to: str | None,
    subject: str,
    from_name: str | None,
    template_file: str | None,
    screenshot_path: str | None,
    logo_path: str | None,
    asset_paths: dict[str, str],
    asset_cids: dict[str, str],
    attachment_paths: list[str] | None,
    completion_copy_email: str | None,
    sent: int,
    failed: int,
    skipped_duplicate: int,
    campaign_id: str,
) -> bool:
    completion_email = (completion_copy_email or "").strip().lower()
    if not completion_email:
        return False
    if not _is_valid_email(completion_email):
        print(f"[MAIL] Skipping completion copy. Invalid email: {completion_copy_email}")
        return False

    screenshot_cid = "campaign_screenshot"
    logo_cid = "campaign_logo"
    summary_html = (
        "<div style=\"margin:0 0 24px 0;padding:16px 18px;border:1px solid #cce0ff;"
        "border-radius:8px;background:#f7fbff;color:#24446b;font-family:Arial,Helvetica,sans-serif;\">"
        "<strong style=\"color:#003380;\">Campaign summary</strong><br>"
        f"Campaign ID: {campaign_id}<br>"
        f"Sent: {sent}<br>"
        f"Failed: {failed}<br>"
        f"Skipped duplicate: {skipped_duplicate}"
        "</div>"
    )
    html_body = _inject_body_prefix(_load_html_template(
        template_file,
        company_name="Sarib",
        logo_cid=logo_cid if logo_path else None,
        asset_cids=asset_cids,
    ), summary_html)
    if screenshot_path:
        html_body = _inject_body_prefix(_load_html_template(
            template_file,
            company_name="Sarib",
            screenshot_cid=screenshot_cid,
            logo_cid=logo_cid if logo_path else None,
            asset_cids=asset_cids,
        ), summary_html)

    msg = _build_message(
        from_addr=smtp_from,
        to_addr=completion_email,
        subject=f"{subject} [Campaign Copy]",
        html_body=html_body,
        from_name=from_name,
        reply_to=smtp_reply_to,
        screenshot_path=screenshot_path,
        screenshot_cid=screenshot_cid,
        logo_path=logo_path,
        logo_cid=logo_cid,
        asset_paths=asset_paths,
        asset_cids=asset_cids,
        attachment_paths=attachment_paths,
    )

    smtp = None
    try:
        smtp = _connect_smtp(
            host=smtp_host,
            port=smtp_port,
            user=smtp_user,
            password=smtp_pass,
            use_ssl=smtp_use_ssl,
            use_tls=smtp_use_tls,
            timeout_seconds=smtp_timeout,
        )
        smtp.send_message(msg)
        print(f"[MAIL] Completion copy sent to {completion_email}")
        return True
    except Exception as err:
        print(f"[MAIL] Failed to send completion copy to {completion_email}: {err}")
        return False
    finally:
        if smtp is not None:
            try:
                smtp.quit()
            except Exception:
                pass


def main():

    load_dotenv()
    ensure_email_tracking_columns()

    parser = argparse.ArgumentParser(description="Send campaign email to companies stored in DB.")
    parser.add_argument(
        "--subject",
        default="Regarding Web Development Services",
        help="Email subject line.",
    )
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
    parser.add_argument("--test-company", default="Team", help="Company name to use for the test email.")
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
    parser.add_argument(
        "--completion-copy-email",
        default=os.getenv("CAMPAIGN_COMPLETION_COPY_EMAIL", "sarib.malek@vivanwebsolution.com"),
        help="Send one final campaign copy to this email after the full run completes.",
    )
    parser.add_argument(
        "--reset-email-flags",
        action="store_true",
        help="Reset DB email_sent/email_sent_at flags before selecting recipients.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print targets without sending.")
    args = parser.parse_args()

    if args.reset_email_flags:
        reset_count = reset_email_flags()
        print(f"[MAIL] Reset DB email flags on {reset_count} rows.")

    smtp_host = (os.getenv("SMTP_HOST") or "").strip()
    smtp_port = int((os.getenv("SMTP_PORT") or "587").strip())
    smtp_user = (os.getenv("SMTP_USER") or "").strip()
    smtp_pass = (os.getenv("SMTP_PASS") or "").strip()
    smtp_from = (os.getenv("SMTP_FROM") or smtp_user).strip()
    smtp_reply_to = (os.getenv("SMTP_REPLY_TO") or "").strip() or None
    smtp_use_ssl = (os.getenv("SMTP_USE_SSL") or "0").strip() in {"1", "true", "True", "yes", "YES"}
    smtp_use_tls = (os.getenv("SMTP_USE_TLS") or "1").strip() in {"1", "true", "True", "yes", "YES"}
    smtp_timeout = float((os.getenv("SMTP_TIMEOUT_SECONDS") or "180").strip())
    tracking_base_url = (
        os.getenv("EMAIL_TRACKING_BASE_URL") or ""
    ).strip()

    if args.test_email:
        test_email = args.test_email.strip().lower()
        if not _is_valid_email(test_email):
            raise SystemExit(f"[MAIL] Invalid --test-email value: {args.test_email}")
        targets = [(0, args.test_company, test_email)]
    else:
        targets = _load_targets(args.source, args.country, args.limit)
        
    if not targets:
        print("[MAIL] No valid recipients found.")
        return

    print(f"[MAIL] Total unique recipients: {len(targets)}")
    for i, (_, company_name, email) in enumerate(targets[:10], start=1):
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
    default_pdf = Path("vivanwebsolution.pdf")
    attachment_paths = [str(default_pdf)] if default_pdf.exists() else []
    if attachment_paths:
        print(f"[MAIL] Attaching PDF: {default_pdf.name}")
    else:
        print(f"[MAIL] Warning: {default_pdf.name} not found, emails will be sent without attachment.")
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
    filtered_targets: list[tuple[int, str, str]] = []

    for company_id, company_name, email in targets:
        if not args.test_email:
            key = _dedupe_key(campaign_id, email)
            if key in send_history:
                skipped_duplicate += 1
                continue
        filtered_targets.append((company_id, company_name, email))

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
                timeout_seconds=smtp_timeout,
            )
        except Exception as err:
            failed += len(batch)
            print(f"[MAIL] Batch connection failed ({len(batch)} recipients): {err}")
            continue

        try:
            for company_id, company_name, email in batch:
                try:
                    dedupe_key = _dedupe_key(campaign_id, email)
                    tracking_token = None
                    tracking_pixel_html = ""
                    if tracking_base_url:
                        tracking_token = _generate_tracking_token()
                        tracking_pixel_html = _build_tracking_pixel_html(tracking_base_url, tracking_token, email)
                    html_body = _load_html_template(
                        args.template_file,
                        company_name=company_name,
                        logo_cid=logo_cid if logo_path else None,
                        asset_cids=asset_cids,
                        tracking_pixel_html=tracking_pixel_html,
                    )
                    if args.screenshot_path:
                        html_body = _load_html_template(
                            args.template_file,
                            company_name=company_name,
                            screenshot_cid=screenshot_cid,
                            logo_cid=logo_cid if logo_path else None,
                            asset_cids=asset_cids,
                            tracking_pixel_html=tracking_pixel_html,
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
                        attachment_paths=attachment_paths or None,
                    )
                    smtp.send_message(msg)
                    if company_id > 0:
                        _mark_email_sent(company_id)
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
    _send_completion_copy(
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_user=smtp_user,
        smtp_pass=smtp_pass,
        smtp_use_ssl=smtp_use_ssl,
        smtp_use_tls=smtp_use_tls,
        smtp_timeout=smtp_timeout,
        smtp_from=smtp_from,
        smtp_reply_to=smtp_reply_to,
        subject=args.subject,
        from_name=args.from_name,
        template_file=args.template_file,
        screenshot_path=args.screenshot_path,
        logo_path=logo_path,
        asset_paths=asset_paths,
        asset_cids=asset_cids,
        attachment_paths=attachment_paths or None,
        completion_copy_email=args.completion_copy_email,
        sent=sent,
        failed=failed,
        skipped_duplicate=skipped_duplicate,
        campaign_id=campaign_id,
    )


if __name__ == "__main__":
    main()

