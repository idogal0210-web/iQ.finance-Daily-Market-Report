"""
fetch_data.py — v3
==================
FMP API    → מניות ומדדים (נתונים עשירים: 52-week, MA, volume, market cap)
yfinance   → סחורות (fallback גם למניות שFMP לא תומך בחינם)
NewsAPI    → כותרות עיתונות
"""

import os
import requests
import yfinance as yf
from datetime import datetime, timedelta

UNVERIFIED = "⚪ לא אומת"
FMP_BASE   = "https://financialmodelingprep.com/stable"


# ── Metadata ──────────────────────────────────────────────────────────────────
COMMODITIES_META = {
    "wti":     {"ticker_yf": "CL=F",  "label": "WTI",                   "unit": "$/bbl",    "sector": "energy"},
    "brent":   {"ticker_yf": "BZ=F",  "label": "Brent",                  "unit": "$/bbl",    "sector": "energy"},
    "nat_gas": {"ticker_yf": "NG=F",  "label": "גז טבעי (Henry Hub)",    "unit": "$/MMBtu",  "sector": "energy"},
    "gold":    {"ticker_yf": "GC=F",  "label": "זהב",                    "unit": "$/אונקיה", "sector": "metals"},
    "copper":  {"ticker_yf": "HG=F",  "label": "נחושת (COMEX)",          "unit": "$/lb",     "sector": "metals"},
    "wheat":   {"ticker_yf": "ZW=F",  "label": "חיטה",                   "unit": "cents/bu", "sector": "agri"},
    "potash":  {"ticker_yf": "ICL",   "label": "ICL (אשלגן proxy)",      "unit": "$",        "sector": "agri"},
}

INDICES_META = {
    "sp500":  {"ticker_fmp": "^GSPC",  "ticker_yf": "^GSPC",  "label": "S&P 500",   "country": "us"},
    "nasdaq": {"ticker_fmp": "^IXIC",  "ticker_yf": "^IXIC",  "label": 'נאסד"ק',    "country": "us"},
    "dow":    {"ticker_fmp": "^DJI",   "ticker_yf": "^DJI",   "label": "דאו ג'ונס", "country": "us"},
    "ta125":  {"ticker_fmp": None,     "ticker_yf": "^TA125.TA","label": 'ת"א-125',  "country": "il"},
}

COMPANIES_META = {
    "nvda":  {"ticker_fmp": "NVDA",  "ticker_yf": "NVDA",  "label": "Nvidia",            "sector": "tech",     "country": "us"},
    "lmt":   {"ticker_fmp": "LMT",   "ticker_yf": "LMT",   "label": "Lockheed Martin",   "sector": "defense",  "country": "us"},
    "dal":   {"ticker_fmp": "DAL",   "ticker_yf": "DAL",   "label": "Delta Air Lines",   "sector": "airlines", "country": "us"},
    "vst":   {"ticker_fmp": None,    "ticker_yf": "VST",   "label": "Vistra",            "sector": "energy",   "country": "us"},
    "fro":   {"ticker_fmp": None,    "ticker_yf": "FRO",   "label": "Frontline",         "sector": "tankers",  "country": "us"},
    "fang":  {"ticker_fmp": None,    "ticker_yf": "FANG",  "label": "Diamondback Energy","sector": "energy",   "country": "us"},
    "fcx":   {"ticker_fmp": None,    "ticker_yf": "FCX",   "label": "Freeport-McMoRan",  "sector": "mining",   "country": "us"},
    "scco":  {"ticker_fmp": None,    "ticker_yf": "SCCO",  "label": "Southern Copper",   "sector": "mining",   "country": "us"},
    "eslt":  {"ticker_fmp": None,    "ticker_yf": "ESLT",  "label": "אלביט מערכות",     "sector": "defense",  "country": "il"},
    "icl":   {"ticker_fmp": None,    "ticker_yf": "ICL",   "label": "ICL Group",         "sector": "agri",     "country": "il"},
}


# ── Price formatter ────────────────────────────────────────────────────────────
def _fmt(price: float) -> str:
    if price >= 100_000:  return f"{price:,.0f}"
    if price >= 10_000:   return f"{price:,.2f}"
    if price >= 100:      return f"{price:,.2f}"
    if price >= 1:        return f"{price:.2f}"
    return f"{price:.4f}"


# ── FMP fetch (rich data) ──────────────────────────────────────────────────────
def _fetch_fmp(ticker: str, api_key: str) -> dict | None:
    """
    Returns rich dict from FMP stable/quote endpoint:
    price, change%, direction, 52-week range, MAs, volume, market cap.
    """
    try:
        url = f"{FMP_BASE}/quote?symbol={ticker}&apikey={api_key}"
        resp = requests.get(url, timeout=12)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if not isinstance(data, list) or not data:
            return None
        d = data[0]
        price = float(d["price"])
        pct   = float(d.get("changePercentage", 0))
        direction = "up" if pct > 0.05 else ("down" if pct < -0.05 else "flat")
        mc = d.get("marketCap", 0) or 0
        return {
            "price":      _fmt(price),
            "price_raw":  price,
            "change":     f"{pct:+.2f}%",
            "direction":  direction,
            "day_low":    d.get("dayLow"),
            "day_high":   d.get("dayHigh"),
            "year_low":   d.get("yearLow"),
            "year_high":  d.get("yearHigh"),
            "ma50":       d.get("priceAvg50"),
            "ma200":      d.get("priceAvg200"),
            "market_cap": f"${mc/1e9:.1f}B" if mc > 1e9 else (f"${mc/1e6:.0f}M" if mc > 0 else None),
            "volume":     f"{int(d.get('volume', 0)):,}" if d.get("volume") else None,
            "open":       d.get("open"),
            "prev_close": d.get("previousClose"),
            "verified":   True,
            "source":     "FMP",
        }
    except Exception as e:
        print(f"  [FMP WARN] {ticker}: {e}")
        return None


# ── yfinance fetch (fallback) ──────────────────────────────────────────────────
def _fetch_yf(ticker: str) -> dict | None:
    """Fallback: yfinance for commodities and unsupported stocks."""
    try:
        t    = yf.Ticker(ticker)
        hist = t.history(period="5d").dropna(subset=["Close"])
        if hist.empty:
            raise ValueError("empty")
        close = float(hist["Close"].iloc[-1])
        if len(hist) >= 2:
            prev = float(hist["Close"].iloc[-2])
            pct  = ((close - prev) / prev) * 100
            direction = "up" if pct > 0.05 else ("down" if pct < -0.05 else "flat")
            chg = f"{pct:+.2f}%"
        else:
            direction, chg = "flat", "0.00%"
        return {
            "price":     _fmt(close),
            "price_raw": close,
            "change":    chg,
            "direction": direction,
            "verified":  True,
            "source":    "yfinance",
        }
    except Exception as e:
        print(f"  [YF WARN] {ticker}: {e}")
        return None


def _empty_record(meta: dict) -> dict:
    return {**meta,
            "price": UNVERIFIED, "price_raw": 0,
            "change": "—", "direction": "flat",
            "verified": False, "source": "none"}


# ── Public fetch functions ─────────────────────────────────────────────────────
def fetch_commodities() -> dict:
    out = {}
    for key, meta in COMMODITIES_META.items():
        data = _fetch_yf(meta["ticker_yf"])
        if data:
            out[key] = {**meta, **data}
        else:
            out[key] = _empty_record(meta)
    return out


def fetch_indices(fmp_key: str) -> dict:
    out = {}
    for key, meta in INDICES_META.items():
        data = None
        if meta["ticker_fmp"]:
            data = _fetch_fmp(meta["ticker_fmp"], fmp_key)
        if not data:
            data = _fetch_yf(meta["ticker_yf"])
        if data:
            out[key] = {**meta, **data}
        else:
            out[key] = _empty_record(meta)
    return out


def fetch_companies(fmp_key: str) -> dict:
    out = {}
    for key, meta in COMPANIES_META.items():
        data = None
        if meta["ticker_fmp"]:
            data = _fetch_fmp(meta["ticker_fmp"], fmp_key)
        if not data:
            data = _fetch_yf(meta["ticker_yf"])
        if data:
            out[key] = {**meta, **data}
        else:
            out[key] = _empty_record(meta)
    return out


def fetch_headlines(news_key: str, max_articles: int = 12) -> list[str]:
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    params = {
        "q": (
            "(oil OR crude OR 'natural gas' OR gold OR copper OR commodities "
            "OR nvidia OR 'artificial intelligence' OR 'interest rate' "
            "OR 'stock market' OR earnings OR 'Federal Reserve' OR geopolitical) "
            "AND (market OR price OR stocks OR forecast OR supply)"
        ),
        "language":  "en",
        "sortBy":    "publishedAt",
        "pageSize":  max_articles,
        "from":      yesterday,
        "apiKey":    news_key,
    }
    try:
        resp = requests.get("https://newsapi.org/v2/everything", params=params, timeout=12)
        resp.raise_for_status()
        arts = resp.json().get("articles", [])
        return [
            f"{a['title']} — {(a.get('description') or '')[:150]}"
            for a in arts if a.get("title")
        ]
    except Exception as e:
        print(f"  [NEWS WARN] {e}")
        return []


# ── Main entry ─────────────────────────────────────────────────────────────────
def collect_all_market_data() -> dict:
    fmp_key  = os.environ["FMP_API_KEY"]
    news_key = os.environ["NEWS_API_KEY"]

    print("  📈 מדדים (FMP + yfinance)...")
    indices = fetch_indices(fmp_key)

    print("  ⛽ סחורות (yfinance)...")
    commodities = fetch_commodities()

    print("  🏢 מניות חברות (FMP + yfinance)...")
    companies = fetch_companies(fmp_key)

    print("  📰 כותרות חדשות (NewsAPI)...")
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
    import json
    d = collect_all_market_data()
    print("\n=== INDICES ===")
    for v in d["indices"].values():
        src = v.get("source","?")
        print(f"  {v['label']:20} {v['price']:>12}  {v['change']:>10}  [{src}]")
    print("\n=== COMMODITIES ===")
    for v in d["commodities"].values():
        print(f"  {v['label']:28} {v['price']:>12}  {v['change']:>10}")
    print("\n=== COMPANIES ===")
    for v in d["companies"].values():
        flag = "🇺🇸" if v["country"] == "us" else "🇮🇱"
        src  = v.get("source", "?")
        mc   = v.get("market_cap", "")
        yr_h = v.get("year_high", "")
        print(f"  {flag} {v['label']:22} {v['price']:>10}  {v['change']:>10}  mktcap={mc}  52H={yr_h}  [{src}]")
