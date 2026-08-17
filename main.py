"""
main.py — v2
============
פייפליין מלא:
  1. אסוף נתוני שוק (yfinance + NewsAPI)
  2. ייצר ניתוח מלא (Gemini AI)
  3. בנה HTML
  4. שלח מייל
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from fetch_data import collect_all_market_data
from generate_analysis import generate_report
from build_report import build_html, save_report
from send_email import send_report as email_send


def main():
    print("=" * 55)
    print("🚀 iQ.finance Daily Report v2")
    print("=" * 55)

    # 1. Collect market data
    print("\n[1/4] 📡 אוסף נתוני שוק...")
    market_data = collect_all_market_data()
    print(
        f"  ✓ {len(market_data['commodities'])} סחורות | "
        f"{len(market_data['indices'])} מדדים | "
        f"{len(market_data['companies'])} חברות | "
        f"{len(market_data['headlines'])} כותרות"
    )

    # 2. Generate Gemini analysis
    print("\n[2/4] 🤖 מייצר ניתוח עם Gemini AI...")
    analysis = generate_report(
        api_key=os.environ["GEMINI_API_KEY"],
        market_data=market_data,
    )

    # 3. Build HTML
    print("\n[3/4] 🔨 בונה HTML...")
    html = build_html(analysis, market_data)
    save_report(html, ".")

    # 4. Send email
    print("\n[4/4] 📬 שולח מייל...")
    email_send(html)

    print("\n" + "=" * 55)
    print("✅ הדוח היומי נשלח בהצלחה!")
    print("=" * 55)


if __name__ == "__main__":
    main()
