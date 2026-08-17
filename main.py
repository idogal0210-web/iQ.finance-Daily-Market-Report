"""
main.py
=======
נקודת כניסה ראשית — מריץ את כל הפייפליין:
  1. אסיפת נתונים
  2. בניית HTML
  3. שליחת מייל
"""

import sys
import os

# הוספת src ל-path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from fetch_data import collect_all_data
from build_report import build_html, save_report
from send_email import send_report


def main():
    print("=" * 50)
    print("🚀 iQ.finance Daily Report — מתחיל...")
    print("=" * 50)

    # שלב 1: אסוף נתונים
    data = collect_all_data()

    # שלב 2: בנה HTML
    print("\n🔨 בונה דוח HTML...")
    html = build_html(data)

    # שלב 3: שמור לקובץ (לשמירה מקומית / artifact ב-Actions)
    save_report(html, ".")

    # שלב 4: שלח מייל
    print("\n📬 שולח מייל...")
    send_report(html)

    print("\n✅ הדוח היומי נשלח בהצלחה!")
    print("=" * 50)


if __name__ == "__main__":
    main()
