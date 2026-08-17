"""
fetch_data.py
=============
אוסף נתוני שוק בזמן אמת:
  - yfinance  → מחירי סחורות ושינויים
  - NewsAPI   → כותרות שוק אחרונות (אנגלית)
  - Gemini AI → TL;DR בעברית (3 נקודות)
"""

import os
import yfinance as yf
import requests
import google.generativeai as genai
from datetime import datetime, timedelta


# ─── Tickers ──────────────────────────────────────────────────────────────────
COMMODITIES = {
    "wti":      {"ticker": "CL=F",  "label": "WTI Crude",   "sector": "energy"},
    "brent":    {"ticker": "BZ=F",  "label": "Brent Crude",  "sector": "energy"},
    "nat_gas":  {"ticker": "NG=F",  "label": "Natural Gas",  "sector": "energy"},
    "gold":     {"ticker": "GC=F",  "label": "Gold",         "sector": "metals"},
    "nickel":   {"ticker": "NI=F",  "label": "Nickel",       "sector": "metals"},
    "wheat":    {"ticker": "ZW=F",  "label": "Wheat",        "sector": "agri"},
    "potash":   {"ticker": "ICL",   "label": "ICL (אשלגן)", "sector": "agri"},
}

UNVERIFIED_LABEL = "⚪ לא אומת"


# ─── Commodities ──────────────────────────────────────────────────────────────
def fetch_commodities() -> dict:
    """מחזיר dict עם מחיר + שינוי % לכל סחורה."""
    results = {}
    for key, meta in COMMODITIES.items():
        try:
            ticker = yf.Ticker(meta["ticker"])
            hist = ticker.history(period="2d")
            if hist.empty or len(hist) < 1:
                raise ValueError("no data")

            close_today = hist["Close"].iloc[-1]

            if len(hist) >= 2:
                close_prev = hist["Close"].iloc[-2]
                change_pct = ((close_today - close_prev) / close_prev) * 100
                change_str = f"{change_pct:+.1f}%"
                direction = "up" if change_pct >= 0 else "down"
            else:
                change_str = "0.0%"
                direction = "flat"

            # פורמט מחיר
            if close_today >= 1000:
                price_str = f"{close_today:,.2f}"
            else:
                price_str = f"{close_today:.2f}"

            results[key] = {
                "price":     price_str,
                "change":    change_str,
                "direction": direction,
                "sector":    meta["sector"],
                "label":     meta["label"],
            }
        except Exception as e:
            print(f"[WARN] {key} ({meta['ticker']}): {e}")
            results[key] = {
                "price":     UNVERIFIED_LABEL,
                "change":    "—",
                "direction": "flat",
                "sector":    meta["sector"],
                "label":     meta["label"],
            }
    return results


# ─── News ─────────────────────────────────────────────────────────────────────
def fetch_headlines(api_key: str, max_articles: int = 8) -> list[str]:
    """מביא כותרות שוק/סחורות מ-NewsAPI."""
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "(oil OR energy OR commodities OR wheat OR gold) AND (market OR price OR stocks)",
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": max_articles,
        "from": yesterday,
        "apiKey": api_key,
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
        return [a["title"] for a in articles if a.get("title")]
    except Exception as e:
        print(f"[WARN] NewsAPI: {e}")
        return []


# ─── Gemini TL;DR ─────────────────────────────────────────────────────────────
def generate_tldr(api_key: str, headlines: list[str], commodities: dict) -> list[str]:
    """
    שולח כותרות ונתוני סחורות ל-Gemini ומקבל 3 נקודות TL;DR בעברית.
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    # בניית קונטקסט
    commodity_summary = "\n".join(
        f"- {v['label']}: {v['price']} ({v['change']})"
        for v in commodities.values()
        if v["price"] != UNVERIFIED_LABEL
    )
    headlines_text = "\n".join(f"- {h}" for h in headlines[:8]) if headlines else "אין כותרות זמינות."

    prompt = f"""אתה אנליסט שוק המון ישראלי. 
בהתבסס על הנתונים הבאים, כתוב בדיוק 3 נקודות TL;DR בעברית — כל נקודה משפט אחד קצר וחד.
אל תכלול מספרים, רק תובנה/מגמה כללית.
פורמט: שלוש שורות בלבד, ללא כותרות, ללא נקודות/bullets.

📈 מחירי סחורות היום:
{commodity_summary}

📰 כותרות שוק:
{headlines_text}

כתוב 3 נקודות TL;DR בעברית:"""

    try:
        response = model.generate_content(prompt)
        lines = [l.strip() for l in response.text.strip().split("\n") if l.strip()]
        # לקחת רק 3 שורות ראשונות, לנקות מספרים/bullets
        clean = []
        for line in lines[:3]:
            line = line.lstrip("123456789.-) ").strip()
            if line:
                clean.append(line)
        # אם יש פחות מ-3, נוסיף fallback
        while len(clean) < 3:
            clean.append("שוק הסחורות הגלובלי ממשיך להיות מושפע מגורמים גיאופוליטיים ומקרו-כלכליים.")
        return clean[:3]
    except Exception as e:
        print(f"[WARN] Gemini: {e}")
        return [
            "שוק הסחורות הגלובלי מציג תנועות מעורבות בפתיחת המסחר.",
            "נתוני המאקרו האחרונים משפיעים על מגמות האנרגיה והמתכות.",
            "מניות הבורסה המקומית נסחרות בהתאם לאינדיקטורים הגלובליים.",
        ]


# ─── Main entry ───────────────────────────────────────────────────────────────
def collect_all_data() -> dict:
    """נקודת כניסה ראשית — מחזירה dict מלא לשימוש ב-build_report."""
    news_api_key   = os.environ["NEWS_API_KEY"]
    gemini_api_key = os.environ["GEMINI_API_KEY"]

    print("📡 שואב נתוני סחורות (yfinance)...")
    commodities = fetch_commodities()

    print("📰 שואב כותרות שוק (NewsAPI)...")
    headlines = fetch_headlines(news_api_key)

    print("🤖 מייצר TL;DR בעברית (Gemini)...")
    tldr = generate_tldr(gemini_api_key, headlines, commodities)

    return {
        "date":        datetime.now().strftime("%d/%m/%Y"),
        "commodities": commodities,
        "tldr":        tldr,
    }


if __name__ == "__main__":
    import json
    data = collect_all_data()
    print(json.dumps(data, ensure_ascii=False, indent=2))
