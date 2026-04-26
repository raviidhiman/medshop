import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date, timedelta
import os

GMAIL_ADDRESS  = os.environ.get("GMAIL_ADDRESS",  "ravidhiman8673@gmail.com")
GMAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD", "your_app_password_here")
NOTIFY_EMAIL   = os.environ.get("NOTIFY_EMAIL",   "ravicsc444@gmail.com")

EXPIRY_WARNING_DAYS = 30
LOW_STOCK_THRESHOLD = 10


def get_alerts(db):
    col   = db.medicines
    today = date.today().isoformat()
    soon  = (date.today() + timedelta(days=EXPIRY_WARNING_DAYS)).isoformat()
    out_of_stock  = list(col.find({'quantity': 0}).sort('name', 1))
    low_stock     = list(col.find({'quantity': {'$gt': 0, '$lte': LOW_STOCK_THRESHOLD}}).sort('quantity', 1))
    expired       = list(col.find({'expiry_date': {'$lt': today}}).sort('expiry_date', 1))
    expiring_soon = list(col.find({'expiry_date': {'$gte': today, '$lte': soon}}).sort('expiry_date', 1))
    return {
        'out_of_stock':  out_of_stock,
        'low_stock':     low_stock,
        'expired':       expired,
        'expiring_soon': expiring_soon,
        'has_alerts':    any([out_of_stock, low_stock, expired, expiring_soon])
    }


def _rows(medicines, cols):
    if not medicines:
        return '<tr><td colspan="3" style="text-align:center;color:#64748b;padding:12px;">None</td></tr>'
    rows = ''
    for m in medicines:
        row = '<tr>'
        for c in cols:
            val = m.get(c, '—')
            if c == 'quantity':
                color = '#ef4444' if val == 0 else '#f97316'
                val = f'<span style="color:{color};font-weight:600;">{val} units</span>'
            elif c == 'expiry_date':
                color = '#ef4444' if str(val) < date.today().isoformat() else '#f97316'
                val = f'<span style="color:{color};">{val}</span>'
            elif c == 'price':
                val = f'₹{float(val):.2f}'
            row += f'<td style="padding:10px 14px;border-bottom:1px solid #1e293b;font-size:13px;">{val}</td>'
        row += '</tr>'
        rows += row
    return rows


def _section(title, color, icon, medicines, cols):
    if not medicines:
        return ''
    count   = len(medicines)
    headers = ''.join(
        f'<th style="text-align:left;padding:10px 14px;font-size:11px;text-transform:uppercase;'
        f'letter-spacing:0.08em;color:#94a3b8;font-weight:600;border-bottom:2px solid {color}22;">'
        f'{h.replace("_"," ").title()}</th>'
        for h in cols
    )
    rows = _rows(medicines, cols)
    return f'''
    <div style="margin-bottom:28px;">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
        <span style="font-size:22px;">{icon}</span>
        <h2 style="margin:0;font-size:16px;color:{color};">{title}</h2>
        <span style="margin-left:auto;background:{color}22;color:{color};
                     padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600;">
          {count} item{"s" if count > 1 else ""}
        </span>
      </div>
      <table width="100%" cellpadding="0" cellspacing="0"
             style="border-collapse:collapse;background:#0f172a;border-radius:10px;
                    overflow:hidden;border:1px solid #1e293b;">
        <thead><tr>{headers}</tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    '''


def _build_html(alerts):
    today_str  = date.today().strftime('%d %B %Y')
    out_sec    = _section('Out of Stock',  '#ef4444', '❌', alerts['out_of_stock'],  ['name', 'manufacturer', 'quantity'])
    exp_sec    = _section('Expired',       '#dc2626', '🚫', alerts['expired'],       ['name', 'manufacturer', 'expiry_date'])
    low_sec    = _section('Low Stock',     '#f97316', '⚠️', alerts['low_stock'],     ['name', 'manufacturer', 'quantity'])
    soon_sec   = _section('Expiring Soon', '#f59e0b', '⏳', alerts['expiring_soon'], ['name', 'manufacturer', 'expiry_date'])
    total      = sum(len(alerts[k]) for k in ['out_of_stock', 'low_stock', 'expired', 'expiring_soon'])
    return f'''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#020817;font-family:'Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#020817;padding:32px 16px;">
<tr><td align="center">
<table width="100%" style="max-width:620px;" cellpadding="0" cellspacing="0">
  <tr><td style="background:linear-gradient(135deg,#0f2744,#0c1a2e);border-radius:16px 16px 0 0;
                 padding:28px;border:1px solid #1e3a5f;border-bottom:none;">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
      <span style="font-size:32px;">💊</span>
      <div>
        <div style="font-size:20px;font-weight:700;color:#e2eaf4;">MedStock Pro</div>
        <div style="font-size:12px;color:#3dd6f5;letter-spacing:0.08em;text-transform:uppercase;">Inventory Alert System</div>
      </div>
    </div>
    <h1 style="margin:0;font-size:22px;color:#ffffff;">🔔 Inventory Alert — Action Required</h1>
    <p style="margin:8px 0 0;color:#8ba0b8;font-size:13px;">
      Generated on {today_str} &nbsp;·&nbsp;
      <span style="color:#ef4444;font-weight:600;">{total} item(s) need attention</span>
    </p>
  </td></tr>
  <tr><td style="background:#0a0e14;padding:28px;border:1px solid #1e293b;border-top:none;border-bottom:none;">
    {out_sec}{exp_sec}{low_sec}{soon_sec}
  </td></tr>
  <tr><td style="background:#0f172a;border-radius:0 0 16px 16px;padding:20px 28px;
                 border:1px solid #1e293b;border-top:2px solid #1e3a5f;text-align:center;">
    <p style="margin:0;font-size:12px;color:#4a6278;">
      Automated alert from MedStock Pro. Please update your inventory at the earliest.
    </p>
  </td></tr>
</table>
</td></tr>
</table>
</body>
</html>'''


def send_alert_email(db):
    alerts = get_alerts(db)
    if not alerts['has_alerts']:
        return {'sent': False, 'message': 'No alerts — inventory looks healthy! ✅', 'alerts': alerts}
    if GMAIL_ADDRESS == 'your_gmail@gmail.com' or GMAIL_PASSWORD == 'your_app_password_here':
        return {'sent': False, 'message': 'Email not configured. Go to Email Alerts in sidebar to set up.', 'alerts': alerts}
    try:
        total   = sum(len(alerts[k]) for k in ['out_of_stock', 'low_stock', 'expired', 'expiring_soon'])
        msg     = MIMEMultipart('alternative')
        msg['Subject'] = f"🔔 MedStock Alert — {date.today().strftime('%d %b %Y')} — {total} item(s) need attention"
        msg['From']    = GMAIL_ADDRESS
        msg['To']      = NOTIFY_EMAIL
        plain = (
            f"MedStock Pro — Inventory Alert ({date.today().strftime('%d %B %Y')})\n\n"
            f"{total} item(s) need your attention:\n\n"
            f"Out of Stock   : {len(alerts['out_of_stock'])} medicines\n"
            f"Expired        : {len(alerts['expired'])} medicines\n"
            f"Low Stock      : {len(alerts['low_stock'])} medicines\n"
            f"Expiring Soon  : {len(alerts['expiring_soon'])} medicines\n\n"
            f"Please log in to MedStock Pro to take action."
        )
        msg.attach(MIMEText(plain, 'plain'))
        msg.attach(MIMEText(_build_html(alerts), 'html'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, NOTIFY_EMAIL, msg.as_string())
        return {'sent': True, 'message': f'Alert email sent to {NOTIFY_EMAIL} ✅', 'alerts': alerts}
    except smtplib.SMTPAuthenticationError:
        return {'sent': False, 'message': 'Gmail authentication failed. Check your App Password.', 'alerts': alerts}
    except Exception as e:
        return {'sent': False, 'message': f'Email error: {str(e)}', 'alerts': alerts}
