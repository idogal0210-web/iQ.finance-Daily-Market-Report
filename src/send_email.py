"""
send_email.py
=============
שולח את דוח ה-HTML כמייל HTML מעוצב דרך Gmail SMTP.
דורש App Password (לא סיסמת Gmail רגילה).
"""

import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from datetime import datetime


def send_report(html_content: str) -> None:
    """שולח את ה-HTML כמייל מעוצב בצורה מאובטחת ועמידה."""
    gmail_user     = os.environ.get("GMAIL_USER")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient      = os.environ.get("RECIPIENT_EMAIL")

    if not gmail_user or not gmail_password or not recipient:
        print("  ⚠️ [WARN] פרטי שליחת מייל (GMAIL_USER / GMAIL_APP_PASSWORD / RECIPIENT_EMAIL) לא הוגדרו — מדלג על שליחת המייל.")
        return

    # Sanitize html_content: remove any accidental markdown wrappers
    html_content = html_content.strip()
    if html_content.startswith("```"):
        html_content = re.sub(r"^```(?:html)?\s*", "", html_content, flags=re.IGNORECASE)
        html_content = re.sub(r"\s*```$", "", html_content)

    today = datetime.now().strftime("%d/%m/%Y")
    subject_text = f"📊 דו״ח שוק וסחורות — {today}"

    # Build MIME multipart/alternative message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(subject_text, "utf-8")
    msg["From"]    = formataddr((str(Header("iQ.finance", "utf-8")), gmail_user))
    msg["To"]      = recipient

    # Plain-text fallback for non-HTML email clients
    plain_text = (
        f"דו״ח שוק וסחורות — {today}\n\n"
        "אנא פתח את המייל בלקוח דואר התומך ב-HTML לצפייה בדו״ח המלא והמעוצב."
    )
    
    part_plain = MIMEText(plain_text, "plain", "utf-8")
    part_plain.add_header("Content-Disposition", "inline")
    msg.attach(part_plain)

    part_html = MIMEText(html_content, "html", "utf-8")
    part_html.add_header("Content-Disposition", "inline")
    msg.attach(part_html)

    # Send via Gmail SMTP TLS with timeout
    print(f"📧 שולח מייל אל {recipient}...")
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, [recipient], msg.as_string())
        print("✅ המייל נשלח בהצלחה!")
    except Exception as e:
        print(f"  ❌ [ERROR] שגיאה בשליחת מייל: {e}")
        raise e


if __name__ == "__main__":
    # בדיקה מהירה
    test_html = "<!DOCTYPE html><html dir='rtl'><body style='font-family:sans-serif;'><h2>בדיקת שליחת מייל ✅</h2><p>המייל עובד בצורה תקינה ומעוצבת.</p></body></html>"
    send_report(test_html)

