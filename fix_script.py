import sys

with open('send_campaign_emails.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '    msg.set_content("Please view this email in HTML mode.")'

replacement = '''    fallback_text = (
        "Hello,\\n\\n"
        "We have sent an HTML email. If you cannot view it, please enable HTML or contact us at info@vivanwebsolution.com.\\n\\n"
        "Best regards,\\n"
        "Vivan Web Solution Pvt. Ltd."
    )
    msg.set_content(fallback_text)'''

if target in content:
    content = content.replace(target, replacement)
    
    # Also fix the logo html 
    logo_target = '        html = html.replace("{logo_html}", logo_html)'
    logo_replacement = '''        html = html.replace("{logo_html}", logo_html)
    else:
        html = html.replace("{logo_html}", \'<div style="display:inline-flex;align-items:center;justify-content:center;gap:15px;"><div style="background:linear-gradient(135deg,#0052cc 0%,#002b66 100%);color:white;font-size:32px;font-weight:900;font-family:\\\'Roboto\\\',sans-serif;width:65px;height:65px;display:flex;align-items:center;justify-content:center;border-radius:16px;box-shadow:0 6px 15px rgba(0,82,204,0.2);">VM</div><div style="text-align:left;display:flex;flex-direction:column;justify-content:center;"><h2 style="font-family:\\\'Roboto\\\',sans-serif;font-size:42px;font-weight:900;color:#003380;margin:0;line-height:1;letter-spacing:-1px;">Vivan</h2><span style="font-size:11px;color:#4d7cc7;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;margin-top:4px;">WEB SOLUTION PVT. LTD.</span></div></div>\')'''
    if logo_target in content:
        content = content.replace(logo_target, logo_replacement)
    
    with open('send_campaign_emails.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Success')
else:
    print('Target not found')
