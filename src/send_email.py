"""
send_email.py
=============
שולח את דוח ה-HTML כמייל HTML דרך Gmail SMTP.
דורש App Password (לא סיסמת Gmail רגילה).
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime


def send_report(html_content: str) -> None:
    """שולח את ה-HTML כמייל."""
    gmail_user      = os.environ.get("GMAIL_USER")
    gmail_password  = os.environ.get("GMAIL_APP_PASSWORD")
    recipient       = os.environ.get("RECIPIENT_EMAIL")

    if not gmail_user or not gmail_password or not recipient:
        print("  ⚠️ [WARN] פרטי שליחת מייל (GMAIL_USER / GMAIL_APP_PASSWORD / RECIPIENT_EMAIL) לא הוגדרו — מדלג על שליחת המייל.")
        return

    today = datetime.now().strftime("%d/%m/%Y")
    subject = f"📊 דו״ח שוק וסחורות — {today}"

    # Build MIME message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"iQ.finance <{gmail_user}>"
    msg["To"]      = recipient

    # Plain-text fallback
    plain = (
        f"דו״ח שוק וסחורות — {today}\n"
        "פתח את המייל בלקוח שתומך ב-HTML כדי לצפות בדוח המלא."
    )
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    # Send via Gmail SMTP TLS
    print(f"📧 שולח מייל אל {recipient}...")
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, recipient, msg.as_string())

    print("✅ המייל נשלח בהצלחה!")


if __name__ == "__main__":
    # בדיקה מהירה — שולח HTML פשוט
    test_html = "<h1 dir='rtl'>בדיקת שליחת מייל ✅</h1><p dir='rtl'>המייל עובד כמו שצריך.</p>"
    send_report(test_html)
