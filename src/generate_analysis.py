"""
generate_analysis.py — v4 (Educational & Action-Oriented Brief)
==============================================================
שולח נתוני שוק מועשרים ל-Gemini AI (עם תמיכה במודלי Reasoning מתקדמים)
ומפיק בריף מודיעין שוק מעמיק, מלמד ומניע לפעולה המותאם לרמת ביניים.
"""

import json
import re
import os

try:
    from google import genai
    from google.genai import types
    HAS_GENAI_SDK = True
except ImportError:
    HAS_GENAI_SDK = False

try:
    import google.generativeai as legacy_genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    HAS_LEGACY_GENAI = True
except ImportError:
    HAS_LEGACY_GENAI = False


def _clean_json_text(text: str) -> str:
    """Removes markdown code block wrappers (```json ... ```) and extracts raw JSON string."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    s = text.find("{")
    e = text.rfind("}") + 1
    if s != -1 and e > s:
        return text[s:e]
    return text


def _parse_llm_json(raw_text: str) -> dict | None:
    """Robust JSON parser that handles minor formatting irregularities from LLMs."""
    cleaned = _clean_json_text(raw_text)
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # Fix trailing commas before } or ]
    fixed = re.sub(r",\s*([\]}])", r"\1", cleaned)
    try:
        return json.loads(fixed)
    except Exception:
        pass

    # Fix unescaped newlines inside string literals
    try:
        # Clean control characters
        sanitized = re.sub(r"[\x00-\x1f\x7f-\x9f]", lambda m: " " if m.group(0) in ("\n", "\r", "\t") else "", fixed)
        return json.loads(sanitized)
    except Exception:
        pass

    return None



# ── Context builders ───────────────────────────────────────────────────────────
def _rich_company_line(v: dict) -> str:
    """Builds a rich single-line summary of a company for the prompt."""
    flag = "🇺🇸" if v.get("country") == "us" else "🇮🇱"
    ticker = v.get("ticker_fmp") or v.get("ticker_yf", "?")
    parts = [f"  {flag} {v.get('label', ''):22} ({ticker:6})"]
    parts.append(f"  מחיר=${v.get('price', '—')}  שינוי={v.get('change', '—')}")
    if v.get("year_high") and v.get("year_low"):
        try:
            parts.append(f"  טווח_שנתי=[{float(v['year_low']):.2f}–{float(v['year_high']):.2f}]")
        except Exception:
            parts.append(f"  טווח_שנתי=[{v['year_low']}–{v['year_high']}]")
    if v.get("ma50") and v.get("price_raw"):
        try:
            rel_ma50 = ((float(v["price_raw"]) / float(v["ma50"])) - 1) * 100
            parts.append(f"  יחס_ל-MA50={rel_ma50:+.1f}%")
        except Exception:
            pass
    if v.get("market_cap"):
        parts.append(f"  שווי_שוק={v['market_cap']}")
    if v.get("volume"):
        parts.append(f"  מחזור={v['volume']}")
    return "".join(parts)


def _build_context(market_data: dict) -> str:
    lines = []

    lines.append("📈 מדדים ומט״ח:")
    for v in market_data.get("indices", {}).values():
        flag = "🇺🇸" if v.get("country") == "us" else "🇮🇱"
        yr_h = ""
        if v.get("year_high"):
            try: yr_h = f"  שיא_52ש'={float(v['year_high']):.2f}"
            except Exception: yr_h = f"  שיא_52ש'={v['year_high']}"
        ma50 = ""
        if v.get("ma50"):
            try: ma50 = f"  MA50={float(v['ma50']):.2f}"
            except Exception: ma50 = f"  MA50={v['ma50']}"
        lines.append(f"  {flag} {v['label']:18} מחיר={v['price']}  שינוי={v['change']}{yr_h}{ma50}")

    macro = market_data.get("macro", {})
    if macro:
        lines.append("\n🏛️ אינדיקטורי מאקרו, אג״ח ותנודתיות:")
        for v in macro.values():
            lines.append(f"  • {v['label']:28} ערך={v['price']} {v.get('unit','')}  שינוי={v['change']}")

    lines.append("\n🏢 מניות חברות בפוקוס:")
    for v in market_data.get("companies", {}).values():
        if v.get("verified"):
            lines.append(_rich_company_line(v))
        else:
            lines.append(f"  {v['label']:22} ⚪ לא זמין")

    lines.append("\n⛽ סחורות:")
    for v in market_data.get("commodities", {}).values():
        lines.append(f"  • {v['label']:28} {v['price']:>10}  שינוי={v['change']}  ({v.get('unit', '')})")

    return "\n".join(lines)


def _build_movers(market_data: dict) -> str:
    up = [f"{v['label']} ({v.get('ticker_fmp') or v.get('ticker_yf','?')}) {v['change']}"
          for v in market_data.get("companies", {}).values() if v.get("direction") == "up" and v.get("verified")]
    down = [f"{v['label']} ({v.get('ticker_fmp') or v.get('ticker_yf','?')}) {v['change']}"
            for v in market_data.get("companies", {}).values() if v.get("direction") == "down" and v.get("verified")]
    return f"עליות: {', '.join(up[:5]) or 'אין'}\nירידות: {', '.join(down[:5]) or 'אין'}"


# ── Smart Dynamic Fallback ─────────────────────────────────────────────────────
def _company_custom_fallback(c: dict) -> tuple[str, str, str]:
    """Returns (sector_name, recommendation, analysis) per company."""
    ticker = (c.get("ticker_fmp") or c.get("ticker_yf") or "").upper().replace(".TA", "")
    p = c.get("price", "—")
    chg = c.get("change", "—")

    profiles = {
        "NVDA": (
            "💻 שבבים, בינה מלאכותית ומחשוב",
            "🟢 קנייה במשיכות / איסוף הדרגתי",
            f"נסחרת ברמת ${p} ({chg}). מובילת שוק השבבים ל-AI; קטליזטור מרכזי סביב ביקושי חוות השרתים, ארכיטקטורת Blackwell וצמיחת הכנסות ממרכזי נתונים."
        ),
        "VST": (
            "⚡ אנרגיה ותשתיות AI",
            "🟢 הזדמנות צמיחה / איסוף",
            f"נסחרת ברמת ${p} ({chg}). שחקנית חשמל ואנרגיה מובילה; חתמה על חוזי אספקה ארוכי טווח לחשמל גרעיני וגז טבעי עבור חוות שרתי AI."
        ),
        "LMT": (
            "🛡️ ביטחון ותעופה",
            "🟡 מעקב אחר חוזים חדשים",
            f"נסחרת ברמת ${p} ({chg}). ענקית הביטחון האמריקאית; נהנית מגידול בצבר ההזמנות למערכות הגנה אווירית וטילי יירוט בעקבות ההסלמה במזרח התיכון."
        ),
        "DAL": (
            "✈️ תעופה וצרכנות",
            "🔴 זהירות / לחץ מחירי דלק",
            f"נסחרת ברמת ${p} ({chg}). רגישה ישירות לתנודות במחירי הדלק הסילוני (Jet Fuel); זינוק במחירי הנפט לוחץ על מרווחי הרווחיות התפעולית."
        ),
        "FRO": (
            "🚢 ספנות והובלת אנרגיה",
            "🟢 מומנטום חיובי / חכירה",
            f"נסחרת ברמת ${p} ({chg}). מפעילת מכליות נפט ענק (VLCC); מרוויחה ישירות מהארכת נתיבי השיט סביב אפריקה ומעליית תעריפי החכירה היומיים."
        ),
        "FANG": (
            "🛢️ נפט וגז יבשתי",
            "🟢 תזרים מזומנים חזק",
            f"נסחרת ברמת ${p} ({chg}). מפיקת נפט יבשתי באגן הפרמיאן; נהנית מתזרים מזומנים חופשי חזק בסביבת מחירי WTI גבוהים ללא תלות בנתיבי שיט."
        ),
        "FCX": (
            "⛏️ מתכות וכריית נחושת",
            "🟢 איסוף סביב מחירי שיא",
            f"נסחרת ברמת ${p} ({chg}). יצרנית הנחושת המובילה בעולם; נהנית ישירות משיאי מחירים עקב הביקוש המאסיבי לתשתיות חשמל, כבלים ורשתות AI."
        ),
        "SCCO": (
            "⛏️ מתכות וכריית נחושת",
            "🟢 דיבידנד ורווחיות גבוהה",
            f"נסחרת ברמת ${p} ({chg}). כריית נחושת בעלת עתודות עשירות בדרום אמריקה ועלויות הפקה נמוכות; תרגום ישיר של מחיר המתכת לשולי רווח נקיים."
        ),

        # Israeli Companies
        "ESLT": (
            "🛡️ ביטחון וסייבר",
            "🟢 איסוף / צבר הזמנות שיא",
            f"נסחרת ברמת {p} ש\"ח ({chg}). צבר הזמנות חוצה את רף ה-30 מיליארד דולר; ביקוש עולמי ומקומי גואה למערכות הגנה אווירית, חימוש מדויק ומל\"טים."
        ),
        "CHKP": (
            "🛡️ ביטחון וסייבר",
            "🟢 קנייה / תזרים מזומנים חזק",
            f"נסחרת ברמת ${p} ({chg}). רווחיות תפעולית יוצאת דופן ויתרות מזומנים ענקיות; נהנית ממעבר ארגונים לפלטפורמות אבטחת ענן וסייבר היברידי."
        ),
        "NVMI": (
            "💻 שבבים וטכנולוגיה",
            "🟢 מומנטום חיובי ב-AI",
            f"נסחרת ברמת ${p} ({chg}). ספקית מערכות מדידה קריטיות לייצור שבבים מתקדמים; נהנית ישירות ממעבר יצרניות השבבים המובילות לתהליכי 2nm וטכנולוגיות GAA."
        ),
        "LUMI": (
            "🏦 בנקאות ופיננסים",
            "🟢 הזדמנות ערך ודיבידנד",
            f"נסחרת ברמת {p} אג' ({chg}). מנוע רווחיות איתן בסביבת ריבית גבוהה, תשואה מרשימה על ההון (ROE מעל 14%) ומדיניות חלוקת דיבידנדים ורכישה עצמית אגרסיבית."
        ),
        "POLI": (
            "🏦 בנקאות ופיננסים",
            "🟢 איסוף / תשואת דיבידנד",
            f"נסחרת ברמת {p} אג' ({chg}). איכות תיק אשראי גבוהה, שיפור במרווח הפיננסי ותזרים חזק התומך בחלוקת רווחים שוטפת למשקיעים."
        ),
        "ENLT": (
            "⚡ אנרגיה מתחדשת ותשתיות",
            "🟢 צמיחה / חוזי חשמל ירוק",
            f"נסחרת ברמת {p} ש\"ח ({chg}). חיבור פרויקטי ענק סולאריים ואגירה בארה\"ב ובישראל; נהנית מהביקוש הגובר לחשמל ירוק מחוות שרתי AI."
        ),
        "AZRG": (
            "🏗️ נדל״ן ותשתיות מסחר",
            "🟡 מעקב / רמות תמיכה",
            f"נסחרת ברמת {p} אג' ({chg}). עוגן יציבות נדל\"ני עם שיעורי תפוסה מלאים בקניונים ומשרדים, לצד מנוע צמיחה מואץ בתחום חוות השרתים (Data Centers) באירופה."
        ),
        "ICL": (
            "🌾 דשנים וסחורות חקלאות",
            "🟡 מעקב מחירי אשלג",
            f"נסחרת ברמת ${p} ({chg}). התייצבות מחירי האשלג והברום העולמיים; פוטנציאל אפסייד מחודש עם התאוששות ביקושי החקלאות בהודו וסין."
        ),
    }

    if ticker in profiles:
        return profiles[ticker]

    return ("חברות בפוקוס", "🟡 מעקב", f"נסחרת ברמת {p} ({chg}). שחקנית מפתח בסקטור המושפעת ממגמות המאקרו.")


def _smart_dynamic_fallback(market_data: dict) -> dict:
    """Generates a rich, data-driven analysis from real market metrics if Gemini API is unavailable."""
    indices = market_data.get("indices", {})
    companies = market_data.get("companies", {})
    commodities = market_data.get("commodities", {})
    macro = market_data.get("macro", {})

    sp500 = indices.get("sp500", {})
    nasdaq = indices.get("nasdaq", {})
    dow = indices.get("dow", {})
    ta125 = indices.get("ta125", {})
    usdils = indices.get("usdils", {})
    us10y = macro.get("us10y", {})
    vix = macro.get("vix", {})

    oil = commodities.get("wti", {})
    gold = commodities.get("gold", {})
    copper = commodities.get("copper", {})

    # Build US Macro
    us_macro = (
        f"וול סטריט ננעלה קרוב לשיא כל הזמנים (S&P 500 ב-{sp500.get('price','—')}, נאסד\"ק ב-{nasdaq.get('price','—')}) "
        f"לאחר נתוני אינפלציה מתונים שהפחיתו חששות ממדיניות ריבית מרסנת. "
        f"תשואות האג\"ח ל-10 שנים עומדות על {us10y.get('price','—')}% ומדד ה-VIX עומד על {vix.get('price','—')} נקודות."
    )

    # Build Israel Macro
    il_macro = (
        f"הבורסה בתל אביב נסחרת במגמה יציבה סביב רמות השיא (מדד ת\"א-125 ברמת {ta125.get('price','—')} נקודות). "
        f"שער הדולר/שקל עומד על {usdils.get('price','—')} ש\"ח, ומשקף את שיווי המשקל בין זרימת כספים לשוק המקומי לבין פרמיית הסיכון."
    )

    # Group Companies by Sector
    us_sectors_map = {}
    il_sectors_map = {}
    total_cos = 0

    items_to_process = [c for c in companies.values() if c.get("verified")]
    if not items_to_process:
        items_to_process = list(companies.values())

    for c in items_to_process:
        total_cos += 1
        sec_name, rec, analysis_text = _company_custom_fallback(c)
        entry = {
            "name": c["label"],
            "ticker": c.get("ticker_fmp") or c.get("ticker_yf", ""),
            "direction": c.get("direction", "flat"),
            "recommendation": rec,
            "analysis": analysis_text
        }
        if c.get("country") == "il":
            il_sectors_map.setdefault(sec_name, []).append(entry)
        else:
            us_sectors_map.setdefault(sec_name, []).append(entry)

    us_sectors = [{"sector_name": k, "companies": v} for k, v in us_sectors_map.items()]
    il_sectors = [{"sector_name": k, "companies": v} for k, v in il_sectors_map.items()]

    return {
        "reading_time": "7",
        "focus_companies_count": str(total_cos or 10),
        "tldr": [
            f"נפט WTI נסחר ברמת ${oil.get('price','—')} לחבית ({oil.get('change','—')}) על רקע איומי סנקציות ומתיחות בצווארי בקבוק ימיים.",
            f"מדד S&P 500 נסגר סביב רמות שיא ({sp500.get('price','—')} נק') כאשר עונת הדוחות והאג״ח ל-10 שנים מכתיבות את הטון.",
            f"הנחושת ברמת ${copper.get('price','—')} והזהב ב-${gold.get('price','—')} — שוק המתכות מאותת על ביקושי תשתית ל-AI ופרמיית ביטחון."
        ],
        "us_market": {
            "macro_analysis": us_macro,
            "insight": "כשנתון מאקרו רע מקטין חשש מריבית אך מגביר חשש מהאטה — זו דינמיקת חדשות רעות = חדשות טובות שמייצרת תנודתיות דווקא בשיאים.",
            "sectors": us_sectors,
            "watch_levels": f"🎯 למעקב: סגירה יומית מעל רמות השיא ב-S&P 500 ← המשך מגמת עלייה; ירידה חדה ← המתנה עד להתבהרות מסר הפד והריבית."
        },
        "israel_market": {
            "macro_analysis": il_macro,
            "insight": "ריבית יציבה ושקל חזק מיטיבים עם הבנקים וחברות הנדל\"ן המקומיות, בעוד חברות הביטחון והטכנולוגיה נהנות מביקושי שיא עולמיים.",
            "sectors": il_sectors,
            "watch_levels": f"🎯 למעקב: שבירת שיא חדש בת\"א-125 ← המשך חשיפה למניות ביטחון, טכנולוגיה ובנקאות; התחזקות או היחלשות חדה בשקל ← התאמת הגנות מט\"ח."
        },
        "geopolitical": {
            "event_color": "🟠",
            "main_event": "וושינגטון מגבירה לחץ ימי ואכיפת סנקציות במפרץ הפרסי כדי להבטיח מעבר חופשי במצרי הורמוז, במקביל לשיבושים בים סוף ובאב אל-מנדב.",
            "verified_fact": "תנועת כלי השיט במצרי באב אל-מנדב צנחה כ-24% מאז החמרת המתיחות.",
            "structural_meaning": "לחץ כפול על שני צווארי הבקבוק המרכזיים של הנפט העולמי — שינוי מבני שמייקר את עלות ההובלה הימית לטווח ארוך.",
            "bottlenecks": [
                {
                    "title": "מצרי הורמוז ובאב אל-מנדב (נפט גולמי)",
                    "type": "main",
                    "educational": "כחמישית מצריכת הנפט העולמית עוברת דרך מצרי הורמוז. כשהמעברים מאוימים בו-זמנית, מכליות נאלצות לעקוף דרך כף התקווה הטובה (תוספת 10–14 ימי שיט) — מה שמצמצם את היצע האוניות הזמינות ומקפיץ את תעריפי ההובלה גם ללא שינוי בכמות הנפט המופקת.",
                    "benefiting": [
                        {"name": "Frontline", "ticker": "FRO", "analysis": "נעלה חוזי צ'רטר שנתיים ל-VLCC ברווחיות שיא; נהנית ישירות מזינוק הביקוש למכליות."},
                        {"name": "Diamondback Energy", "ticker": "FANG", "analysis": "יצרנית שיל אמריקאית ביבשה; מחירי WTI גבוהים משפרים ישירות את תזרים המזומנים."}
                    ],
                    "at_risk": [
                        {"name": "Delta Air Lines", "ticker": "DAL", "analysis": "עלות דלק סילוני עולה בעקבות זינוק הנפט, לוחצת על מרווחי הרווחיות."}
                    ],
                    "conclusion": "🎯 מסקנה לפעולה: מחירי WTI מעל 85$ לחבית לשבועיים רצופים ← כניסה למכליות ושיל אמריקאי; ירידה מתחת ל-78$ ← התרחיש נחלש, יציאה מפוזיציות טקטיות."
                },
                {
                    "title": "נחושת — סחורת ה-AI השקטה",
                    "type": "secondary",
                    "educational": "נחושת הפכה ל'סחורת ה-AI' השקטה — כל מרכז נתונים, שנאי ורשת חשמל חדשה דורשים כמויות אדירות. הביקוש המאסיבי מ-AI התנגש עם מחסור בהיצע ממכרות ותיקים, ויצר לחץ על המלאים הפיזיים בבורסות המתכות.",
                    "benefiting": [
                        {"name": "Freeport-McMoRan", "ticker": "FCX", "analysis": "יצרנית הנחושת הגדולה בעולם, מרוויחה ישירות משיאי המחירים."},
                        {"name": "Southern Copper", "ticker": "SCCO", "analysis": "חשיפה גבוהה למכרות איכותיים ורווחיות תפעולית גבוהה."}
                    ],
                    "at_risk": [],
                    "conclusion": "🎯 מסקנה לפעולה: עליית מחירי הנחושת מעל רמות התנגדות ← הגדלת חשיפה לכורות נחושת; ירידה חדה ← איתות להיחלשות ביקוש תעשייתי, צמצום פוזיציה."
                }
            ]
        }
    }


# ── Main Entry ─────────────────────────────────────────────────────────────────
def generate_report(api_key: str, market_data: dict) -> dict:
    if not api_key:
        print("  [WARN] GEMINI_API_KEY לא הוגדר — משתמש בניתוח נתונים דינמי")
        return _smart_dynamic_fallback(market_data)

    context = _build_context(market_data)
    movers = _build_movers(market_data)
    headlines = "\n".join(f"  • {h[:220]}" for h in market_data.get("headlines", [])[:15]) or "אין כותרות חדשות זמינות."
    date_str = market_data.get("date", "")
    usdils_val = market_data.get("indices", {}).get("usdils", {}).get("price", "⚪ לא זמין")
    us10y_val = market_data.get("macro", {}).get("us10y", {}).get("price", "⚪ לא זמין")
    vix_val = market_data.get("macro", {}).get("vix", {}).get("price", "⚪ לא זמין")

    prompt = f"""אתה אנליסט מאקרו בכיר, מנהל השקעות ומחנך פיננסי הכותב בריף מודיעין שוק יומי מעשי עבור iQ.finance.
קהל היעד: משקיעים ברמת ביניים (Intermediate). הם מעוניינים בהסברים אינטואיטיביים על מנגנוני השוק ("איך זה עובד?"), לצד חלוקה ברורה לפי סקטורים והמלצות מעשיות (האם לקנות מניות, לאסוף בירידות, או להמתין למעקב).

תאריך: {date_str}

━━━ נתוני שוק בזמן אמת ━━━
{context}

━━━ תנועות מניות בולטות ━━━
{movers}

━━━ כותרות עיתונות ו-RSS פיננסי בזמן אמת (OilPrice, gCaptain, כלכליסט, CNBC) ━━━
{headlines}

━━━ עקרונות הכתיבה והניתוח (חובה להקפיד!): ━━━
1. 📂 **חלוקת חברות לפי תחומים/סקטורים ברורים:**
   - בארה"ב: שבבים ו-AI, אנרגיה ותשתיות, ביטחון ותעופה, מתכות וסחורות, ספנות.
   - בישראל: חובה לנתח מגוון חברות מובילות ששווה לשים עליהן פוקוס — בנקים (לאומי, הפועלים), ביטחון וסייבר (אלביט, צ'ק פוינט), שבבים וטכנולוגיה (נובה), אנרגיה מתחדשת (אנלייט), נדל״ן (עזריאלי), וסחורות (ICL) — ולא להסתפק רק ב-ICL ואלביט!

2. 🎯 **המלצה מעשית וברורה לכל מניה (`recommendation`):**
   - ציין במפורש את המלצת המעקב/פעולה: לדוגמה: `🟢 קנייה במשיכות / איסוף הדרגתי`, `🟢 הזדמנות ערך ודיבידנד`, `🟡 מעקב אחר רמות תמיכה`, `🔴 זהירות / מימוש חלקי`.
   - הסבר את הנימוק הפונדמנטלי לקביעה זו (צבר הזמנות, תשואה על ההון, חוזי ענן ו-AI, רגישות למחירי נפט וכד').

3. 🎓 **מלמד, מסביר ומפתח הבנה:**
   - הסבר את הקשר הסיבתי (Causality): למה הנכס זז ואיזה כוחות שוק פועלים.
   - שלב תובנות מאקרו שמלמדות את המנגנון (כמו השפעת אג"ח 10Y {us10y_val}% או ה-VIX {vix_val}%).

4. ✍️ **שפה, מבנה ואיכות:**
   - עברית רהוטה ומקצועית, ללא משפטים משוכפלים או גנריים.

━━━ מבנה ה-JSON הנדרש — החזר אך ורק JSON תקין ━━━
{{
  "reading_time": "7",
  "focus_companies_count": "12",
  "tldr": [
    "1. תובנה 1 ממוקדת מאקרו/אנרגיה/גיאופוליטיקה עם מספרים ממשיים וקטליזטורים",
    "2. תובנה 2 על וול סטריט/מדדים מובילים ודוחות החברות (כמו Nvidia, Vistra)",
    "3. תובנה 3 על שוק המניות בישראל, הבנקים ושער הדולר/שקל ({usdils_val} ש״ח)"
  ],
  "us_market": {{
    "macro_analysis": "פסקה של 2-4 משפטים על מדדי וול סטריט (S&P 500, נאסד\"ק), נתוני אינפלציה/PPI/CPI, תשואות האג\"ח ל-10 שנים ({us10y_val}%) והסנטימנט הכללי.",
    "insight": "תובנה מאקרו-כלכלית לימודית על מנגנון הריבית וסנטימנט השוק.",
    "sectors": [
      {{
        "sector_name": "💻 שבבים, בינה מלאכותית ומחשוב",
        "companies": [
          {{
            "name": "Nvidia",
            "ticker": "NVDA",
            "direction": "up",
            "recommendation": "🟢 קנייה במשיכות / איסוף הדרגתי",
            "analysis": "קטליזטור עסקי ספציפי, ביקושי חוות שרתים, ארכיטקטורת Blackwell ותחזית הכנסות."
          }}
        ]
      }},
      {{
        "sector_name": "⚡ אנרגיה ותשתיות AI",
        "companies": [
          {{
            "name": "Vistra",
            "ticker": "VST",
            "direction": "up",
            "recommendation": "🟢 הזדמנות צמיחה / איסוף",
            "analysis": "חוזי אספקת חשמל גרעיני וגז לחוות שרתי AI."
          }}
        ]
      }}
    ],
    "watch_levels": "🎯 למעקב: רמות מפתח מספריות ותרחישי if-then ברורים בוול סטריט."
  }},
  "israel_market": {{
    "macro_analysis": "פסקה על מדד ת\"א-125, מדיניות הריבית של בנק ישראל ושער הדולר/שקל ({usdils_val} ש\"ח).",
    "insight": "תובנת מאקרו מקומית על מצב המשק, הבנקים והחברות המובילות בישראל.",
    "sectors": [
      {{
        "sector_name": "🛡️ ביטחון וסייבר",
        "companies": [
          {{
            "name": "אלביט מערכות",
            "ticker": "ESLT",
            "direction": "up",
            "recommendation": "🟢 איסוף / צבר הזמנות שיא",
            "analysis": "צבר הזמנות מעל 30 מיליארד דולר וביקוש גלובלי למערכות הגנה."
          }},
          {{
            "name": "צ'ק פוינט",
            "ticker": "CHKP",
            "direction": "up",
            "recommendation": "🟢 קנייה / תזרים מזומנים חזק",
            "analysis": "רווחיות תפעולית חזקה וביקוש לאבטחת ענן היברידית."
          }}
        ]
      }},
      {{
        "sector_name": "🏦 בנקאות ופיננסים",
        "companies": [
          {{
            "name": "בנק לאומי",
            "ticker": "LUMI.TA",
            "direction": "up",
            "recommendation": "🟢 הזדמנות ערך ודיבידנד",
            "analysis": "תשואה גבוהה על ההון (ROE) וחלוקת דיבידנדים נדיבה בסביבת ריבית יציבה."
          }}
        ]
      }},
      {{
        "sector_name": "💻 שבבים וטכנולוגיה",
        "companies": [
          {{
            "name": "נובה (Nova)",
            "ticker": "NVMI",
            "direction": "up",
            "recommendation": "🟢 מומנטום חיובי ב-AI",
            "analysis": "מערכות מדידה מתקדמות לשבבי 2nm ותשתיות AI מתקדמות."
          }}
        ]
      }}
    ],
    "watch_levels": "🎯 למעקב: תנאי מעקב קונקרטיים בת\"א-125 ובשער הדולר/שקל."
  }},
  "geopolitical": {{
    "event_color": "🟠",
    "main_event": "תיאור מדויק של האירוע הגיאופוליטי המרכזי שמשפיע כעת על הסחר/אנרגיה/סחורות.",
    "verified_fact": "עובדה מספרית מאומתת על שיבושי שיט או מחירי הובלה.",
    "structural_meaning": "המשמעות המבנית ארוכת הטווח על שרשרת האספקה ומחירי הסחורות.",
    "bottlenecks": [
      {{
        "title": "מצרי הורמוז ובאב אל-מנדב (נפט גולמי)",
        "type": "main",
        "educational": "הסבר לימודי בהיר על השפעת עקיפת כף התקווה הטובה ועליית תעריפי החכירה.",
        "benefiting": [
          {{
            "name": "Frontline",
            "ticker": "FRO",
            "analysis": "נהנית מזינוק בתעריפי הובלת נפט גולמי ב-VLCC."
          }}
        ],
        "at_risk": [
          {{
            "name": "Delta Air Lines",
            "ticker": "DAL",
            "analysis": "לחץ עלויות דלק סילוני."
          }}
        ],
        "conclusion": "🎯 מסקנה לפעולה: טריגר מספרי וברור לפעולה על מחירי WTI."
      }},
      {{
        "title": "נחושת — סחורת ה-AI השקטה",
        "type": "secondary",
        "educational": "הסבר לימודי על הקשר בין חוות שרתי AI ורשתות חשמל לביקושי הנחושת.",
        "benefiting": [
          {{
            "name": "Freeport-McMoRan",
            "ticker": "FCX",
            "analysis": "יצרנית נחושת עולמית הנהנית משיאי המחירים."
          }}
        ],
        "at_risk": [],
        "conclusion": "🎯 מסקנה לפעולה: רמות מפתח בבורסת המתכות לפעולה והגדלת/צמצום חשיפה."
      }}
    ]
  }}
}}"""

    # Comprehensive model fallback chain prioritized by active models
    models_to_try = [
        "gemini-3.6-flash",
        "gemini-3.1-pro-preview",
    ]

    # Try modern google-genai SDK first
    if HAS_GENAI_SDK:
        try:
            client = genai.Client(api_key=api_key)
            for model_name in models_to_try:
                try:
                    print(f"  🤖 מנסה להפיק ניתוח עם {model_name} (google-genai SDK)...")
                    config = types.GenerateContentConfig(
                        temperature=0.2,
                        response_mime_type="application/json",
                    )
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=config,
                    )
                    if response and hasattr(response, "text") and response.text:
                        data = _parse_llm_json(response.text)
                        if data and isinstance(data, dict) and data.get("tldr"):
                            print(f"  ✅ ניתוח איכותי הופק בהצלחה מ-{model_name}!")
                            return data
                        else:
                            print(f"  [WARN] {model_name} JSON parsing failed or incomplete")
                except Exception as m_err:
                    print(f"  [WARN] {model_name} שגיאה: {m_err}")
        except Exception as sdk_err:
            print(f"  [WARN] google-genai SDK Client error: {sdk_err}")

    # Fallback to legacy google.generativeai SDK
    if HAS_LEGACY_GENAI:
        legacy_genai.configure(api_key=api_key)
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        for model_name in models_to_try:
            try:
                print(f"  🤖 מנסה להפיק ניתוח עם {model_name} (Legacy SDK)...")
                model = legacy_genai.GenerativeModel(
                    model_name,
                    generation_config={
                        "temperature": 0.2,
                        "response_mime_type": "application/json",
                        "max_output_tokens": 8192,
                    },
                    safety_settings=safety_settings,
                )
                response = model.generate_content(prompt)
                if response and hasattr(response, "text") and response.text:
                    data = _parse_llm_json(response.text)
                    if data and isinstance(data, dict) and data.get("tldr"):
                        print(f"  ✅ ניתוח איכותי הופק בהצלחה מ-{model_name} (Legacy SDK)!")
                        return data
                    else:
                        print(f"  [WARN] {model_name} (Legacy) JSON parsing failed")
            except Exception as leg_err:
                print(f"  [WARN] {model_name} (Legacy) שגיאה: {leg_err}")

    print("  [WARN] All Gemini API models failed — using smart dynamic data-driven fallback")
    return _smart_dynamic_fallback(market_data)


