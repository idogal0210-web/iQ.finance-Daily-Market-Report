"""
fetch_data.py — v2
==================
אוסף נתוני שוק מקיפים:
  • מדדים:  S&P 500, נאסד"ק, ת"א-125
  • סחורות: נפט, גז, זהב, נחושת, חיטה, ICL
  • 10 חברות מפתח
  • כותרות חדשות (NewsAPI)
"""

import os
import yfinance as yf
import requests
from datetime import datetime, timedelta

UNVERIFIED = "⚪ לא אומת"

# ── Commodity tickers ──────────────────────────────────────────────────────────
COMMODITIES_META = {
    "wti":     {"ticker": "CL=F",  "label": "WTI",                  "unit": "$/bbl",    "sector": "energy"},
    "brent":   {"ticker": "BZ=F",  "label": "Brent",                 "unit": "$/bbl",    "sector": "energy"},
    "nat_gas": {"ticker": "NG=F",  "label": "גז טבעי (Henry Hub)",   "unit": "$/MMBtu",  "sector": "energy"},
    "gold":    {"ticker": "GC=F",  "label": "זהב",                   "unit": "$/אונקיה", "sector": "metals"},
    "copper":  {"ticker": "HG=F",  "label": "נחושת (COMEX)",         "unit": "$/lb",     "sector": "metals"},
    "wheat":   {"ticker": "ZW=F",  "label": "חיטה",                  "unit": "cents/bu", "sector": "agri"},
    "potash":  {"ticker": "ICL",   "label": "ICL (אשלגן proxy)",     "unit": "$",        "sector": "agri"},
}

# ── Index tickers ──────────────────────────────────────────────────────────────
INDICES_META = {
    "sp500":  {"ticker": "^GSPC",     "label": "S&P 500",   "country": "us"},
    "nasdaq": {"ticker": "^IXIC",     "label": 'נאסד"ק',    "country": "us"},
    "ta125":  {"ticker": "^TA125.TA", "label": 'ת"א-125',   "country": "il"},
}

# ── Company tickers ────────────────────────────────────────────────────────────
COMPANIES_META = {
    "nvda":  {"ticker": "NVDA",  "label": "Nvidia",            "sector": "tech",     "country": "us"},
    "vst":   {"ticker": "VST",   "label": "Vistra",            "sector": "energy",   "country": "us"},
    "lmt":   {"ticker": "LMT",   "label": "Lockheed Martin",   "sector": "defense",  "country": "us"},
    "dal":   {"ticker": "DAL",   "label": "Delta Air Lines",   "sector": "airlines", "country": "us"},
    "fro":   {"ticker": "FRO",   "label": "Frontline",         "sector": "tankers",  "country": "us"},
    "fang":  {"ticker": "FANG",  "label": "Diamondback Energy","sector": "energy",   "country": "us"},
    "fcx":   {"ticker": "FCX",   "label": "Freeport-McMoRan",  "sector": "mining",   "country": "us"},
    "scco":  {"ticker": "SCCO",  "label": "Southern Copper",   "sector": "mining",   "country": "us"},
    "eslt":  {"ticker": "ESLT",  "label": "אלביט מערכות",     "sector": "defense",  "country": "il"},
    "icl":   {"ticker": "ICL",   "label": "ICL Group",         "sector": "agri",     "country": "il"},
}


# ── Generic fetch ──────────────────────────────────────────────────────────────
def _fetch_one(ticker_sym: str) -> dict | None:
    """
    Fetches close price + daily % change for any ticker.
    Uses 5-day window to survive weekends and market holidays.
    Returns None on any failure.
    """
    try:
        t = yf.Ticker(ticker_sym)
        hist = t.history(period="5d")
        hist = hist.dropna(subset=["Close"])
        if hist.empty:
            raise ValueError("empty")

        close = float(hist["Close"].iloc[-1])
        if len(hist) >= 2:
            prev = float(hist["Close"].iloc[-2])
            pct = ((close - prev) / prev) * 100
            direction = "up" if pct > 0.05 else ("down" if pct < -0.05 else "flat")
            change_str = f"{pct:+.2f}%"
        else:
            direction = "flat"
            change_str = "0.00%"

        return {"price_raw": close, "change": change_str, "direction": direction}
    except Exception as e:
        print(f"  [WARN] {ticker_sym}: {e}")
        return None


def _fmt(price: float) -> str:
    """Human-readable price formatting."""
    if price >= 10_000:
        return f"{price:,.0f}"
    elif price >= 1_000:
        return f"{price:,.2f}"
    elif price >= 10:
        return f"{price:.2f}"
    else:
        return f"{price:.4f}"


# ── Public fetch functions ─────────────────────────────────────────────────────
def fetch_commodities() -> dict:
    out = {}
    for key, meta in COMMODITIES_META.items():
        data = _fetch_one(meta["ticker"])
        if data:
            out[key] = {**meta,
                        "price": _fmt(data["price_raw"]),
                        "price_raw": data["price_raw"],
                        "change": data["change"],
                        "direction": data["direction"],
                        "verified": True}
        else:
            out[key] = {**meta,
                        "price": UNVERIFIED,
                        "price_raw": 0,
                        "change": "—",
                        "direction": "flat",
                        "verified": False}
    return out


def fetch_indices() -> dict:
    out = {}
    for key, meta in INDICES_META.items():
        data = _fetch_one(meta["ticker"])
        if data:
            out[key] = {**meta,
                        "price": _fmt(data["price_raw"]),
                        "price_raw": data["price_raw"],
                        "change": data["change"],
                        "direction": data["direction"],
                        "verified": True}
        else:
            out[key] = {**meta,
                        "price": UNVERIFIED,
                        "price_raw": 0,
                        "change": "—",
                        "direction": "flat",
                        "verified": False}
    return out


def fetch_companies() -> dict:
    out = {}
    for key, meta in COMPANIES_META.items():
        data = _fetch_one(meta["ticker"])
        if data:
            out[key] = {**meta,
                        "price": _fmt(data["price_raw"]),
                        "price_raw": data["price_raw"],
                        "change": data["change"],
                        "direction": data["direction"],
                        "verified": True}
        else:
            out[key] = {**meta,
                        "price": UNVERIFIED,
                        "price_raw": 0,
                        "change": "—",
                        "direction": "flat",
                        "verified": False}
    return out


def fetch_headlines(api_key: str, max_articles: int = 12) -> list[str]:
    """Fetch recent market/energy/commodities headlines from NewsAPI."""
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    params = {
        "q": (
            "(oil OR crude OR 'natural gas' OR gold OR copper OR commodities "
            "OR nvidia OR AI OR 'interest rate' OR 'stock market' OR earnings) "
            "AND (market OR price OR stocks OR fed OR forecast)"
        ),
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": max_articles,
        "from": yesterday,
        "apiKey": api_key,
    }
    try:
        resp = requests.get("https://newsapi.org/v2/everything",
                            params=params, timeout=12)
        resp.raise_for_status()
        arts = resp.json().get("articles", [])
        # Include title + snippet of description for richer context
        return [
            f"{a['title']} — {(a.get('description') or '')[:120]}"
            for a in arts if a.get("title")
        ]
    except Exception as e:
        print(f"  [WARN] NewsAPI: {e}")
        return []


# ── Main entry ─────────────────────────────────────────────────────────────────
def collect_all_market_data() -> dict:
    """Collects and returns all market data as a single dict."""
    news_key = os.environ["NEWS_API_KEY"]

    print("  📈 מדדים (S&P 500, נאסד\"ק, ת\"א-125)...")
    indices = fetch_indices()

    print("  ⛽ סחורות...")
    commodities = fetch_commodities()

    print("  🏢 מניות חברות...")
    companies = fetch_companies()

    print("  📰 כותרות חדשות...")
    headlines = fetch_headlines(news_key)

    return {
        "date":        datetime.now().strftime("%d/%m/%Y"),
        "date_en":     datetime.now().strftime("%Y-%m-%d"),
        "indices":     indices,
        "commodities": commodities,
        "companies":   companies,
        "headlines":   headlines,
    }


if __name__ == "__main__":
    import json, os
    os.environ.setdefault("NEWS_API_KEY", "TEST")
    d = collect_all_market_data()
    print("\n=== סחורות ===")
    for v in d["commodities"].values():
        print(f"  {v['label']:28} {v['price']:>12}  {v['change']:>10}")
    print("\n=== מדדים ===")
    for v in d["indices"].values():
        print(f"  {v['label']:20} {v['price']:>12}  {v['change']:>10}")
    print("\n=== חברות ===")
    for v in d["companies"].values():
        flag = "🇺🇸" if v["country"] == "us" else "🇮🇱"
        print(f"  {flag} {v['label']:22} {v['ticker']:6} {v['price']:>10}  {v['change']:>10}")
