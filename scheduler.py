"""
scheduler.py — Automatic daily email alert system
Uses Python's built-in threading — no extra packages needed.

How it works:
- Runs a background thread when the Flask app starts
- Checks inventory every day at 9:00 AM
- Sends email automatically if any medicines are expired or low stock
- Logs everything to console so you can see it working
"""

import threading
import time
import logging
from datetime import datetime, date
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s [SCHEDULER] %(message)s')
log = logging.getLogger('scheduler')

# ── CONFIGURATION ──────────────────────────────────────────
# What time to send the daily alert (24-hour format)
ALERT_HOUR   = int(os.environ.get('ALERT_HOUR',   9))   # 9 = 9:00 AM
ALERT_MINUTE = int(os.environ.get('ALERT_MINUTE', 0))   # 0 = :00

# How often the scheduler wakes up to check if it's time (seconds)
CHECK_INTERVAL = 60   # check every 60 seconds


class DailyAlertScheduler:
    def __init__(self):
        self.thread       = None
        self.running      = False
        self.last_sent    = None   # tracks date of last sent email (avoid duplicates)

    def start(self, app):
        """Start the background scheduler thread."""
        if self.running:
            return
        self.running = True
        self.thread  = threading.Thread(
            target=self._run_loop,
            args=(app,),
            daemon=True   # daemon=True means thread dies when main app dies
        )
        self.thread.start()
        log.info(f"✅ Scheduler started — daily alerts at {ALERT_HOUR:02d}:{ALERT_MINUTE:02d}")

    def stop(self):
        self.running = False
        log.info("Scheduler stopped.")

    def _run_loop(self, app):
        """Main loop — runs forever in background thread."""
        while self.running:
            try:
                now   = datetime.now()
                today = date.today()

                # Check if it's alert time AND we haven't sent today
                is_alert_time = (now.hour == ALERT_HOUR and now.minute == ALERT_MINUTE)
                already_sent  = (self.last_sent == today)

                if is_alert_time and not already_sent:
                    log.info("⏰ Alert time reached — checking inventory...")
                    with app.app_context():
                        self._send_scheduled_alert()
                    self.last_sent = today
                    log.info(f"✅ Next alert scheduled for tomorrow at {ALERT_HOUR:02d}:{ALERT_MINUTE:02d}")

            except Exception as e:
                log.error(f"Scheduler error: {e}")

            time.sleep(CHECK_INTERVAL)

    def _send_scheduled_alert(self):
        """Check inventory and send email if needed."""
        from database import get_db
        from notifier import send_alert_email, get_alerts, GMAIL_ADDRESS, GMAIL_PASSWORD

        # Don't attempt if email is not configured
        if GMAIL_ADDRESS == 'your_gmail@gmail.com' or GMAIL_PASSWORD == 'your_app_password_here':
            log.warning("⚠️  Email not configured — skipping scheduled alert.")
            log.warning("    Go to Email Alerts page in your app to configure Gmail.")
            return

        db     = get_db()
        alerts = get_alerts(db)

        if not alerts['has_alerts']:
            log.info("✅ Inventory healthy — no alert email needed today.")
            return

        # Log what was found
        log.info(f"   Found: {len(alerts['expired'])} expired, "
                 f"{len(alerts['out_of_stock'])} out of stock, "
                 f"{len(alerts['low_stock'])} low stock, "
                 f"{len(alerts['expiring_soon'])} expiring soon")

        result = send_alert_email(db)
        if result['sent']:
            log.info(f"📧 Alert email sent successfully! → {result['message']}")
        else:
            log.error(f"❌ Failed to send alert: {result['message']}")


# Global scheduler instance
scheduler = DailyAlertScheduler()


def start_scheduler(app):
    """Call this from app.py to start the scheduler."""
    scheduler.start(app)
