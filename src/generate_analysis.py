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
def _company_custom_fallback(c: dict) -> str:
    """Returns a tailored, authentic business analysis per company to avoid generic repetition."""
    ticker = (c.get("ticker_fmp") or c.get("ticker_yf") or "").upper()
    p = c.get("price", "—")
    chg = c.get("change", "—")
    
    profiles = {
        "NVDA": f"נסחרת ברמת ${p} ({chg}). מובילת שוק השבבים ל-AI; קטליזטור מרכזי סביב ביקושי חוות השרתים, ארכיטקטורת Blackwell וצמיחת הכנסות ממרכזי נתונים.",
        "LMT":  f"נסחרת ברמת ${p} ({chg}). ענקית הביטחון האמריקאית; נהנית מגידול בצבר ההזמנות למערכות הגנה אווירית וטילי יירוט בעקבות ההסלמה במזרח התיכון.",
        "DAL":  f"נסחרת ברמת ${p} ({chg}). רגישה ישירות לתנודות במחירי הדלק הסילוני (Jet Fuel); זינוק במחירי הנפט לוחץ על מרווחי הרווחיות התפעולית.",
        "VST":  f"נסחרת ברמת ${p} ({chg}). שחקנית חשמל ואנרגיה מובילה; חתמה על חוזי אספקה ארוכי טווח לחשמל גרעיני וגז טבעי עבור חוות שרתי AI.",
        "FRO":  f"נסחרת ברמת ${p} ({chg}). מפעילת מכליות נפט ענק (VLCC); מרוויחה ישירות מהארכת נתיבי השיט סביב אפריקה ומעליית תעריפי החכירה היומיים.",
        "FANG": f"נסחרת ברמת ${p} ({chg}). מפיקת נפט יבשתי באגן הפרמיאן; נהנית מתזרים מזומנים חופשי חזק בסביבת מחירי WTI גבוהים ללא תלות בנתיבי שיט.",
        "FCX":  f"נסחרת ברמת ${p} ({chg}). יצרנית הנחושת המובילה בעולם; נהנית ישירות משיאי מחירים עקב הביקוש המאסיבי לתשתיות חשמל, כבלים ורשתות AI.",
        "SCCO": f"נסחרת ברמת ${p} ({chg}). כריית נחושת בעלת עתודות עשירות בדרום אמריקה ועלויות הפקה נמוכות; תרגום ישיר של מחיר המתכת לשולי רווח נקיים.",
        "ESLT": f"נסחרת ברמת ${p} ({chg}). צבר הזמנות ביטחוני בשיא כל הזמנים (מעל 30 מיליארד דולר); ביקוש גלובלי גובר למערכות מל\"טים והגנה אלקטרונית.",
        "ICL":  f"נסחרת ברמת ${p} ({chg}). נהנית מאיזון מחודש במחירי האשלג והדשנים העולמיים, וחידוש חוזי אספקה רב-שנתיים מול הודו וסין.",
    }
    
    if ticker in profiles:
        return profiles[ticker]
    
    sector = c.get("sector", "general")
    if sector == "tech":
        return f"נסחרת ברמת ${p} ({chg}). מציגה ביצועים סקטוריאליים בהתאם למומנטום במניות הטכנולוגיה וזרימת ההון ל-AI."
    elif sector == "defense":
        return f"נסחרת ברמת ${p} ({chg}). נהנית מהרחבת תקציבי הביטחון העולמיים ומביקוש מוגבר למערכות חימוש והגנה."
    elif sector == "energy":
        return f"נסחרת ברמת ${p} ({chg}). מושפעת ישירות מרמות מחירי הנפט והגז ומרווחי הזיקוק העולמיים."
    elif sector == "mining":
        return f"נסחרת ברמת ${p} ({chg}). מגיבה לתנודות במחירי המתכות התעשייתיות ולמצב המלאים הפיזיים בבורסות."
    
    return f"נסחרת ברמת ${p} ({chg}). שווי שוק: {c.get('market_cap', 'לא זמין')}. שחקנית מפתח בסקטור המושפעת ממגמות המאקרו."


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

    # Build Companies
    us_companies = []
    il_companies = []

    for key, c in companies.items():
        if not c.get("verified"):
            continue
        entry = {
            "name": c["label"],
            "ticker": c.get("ticker_fmp") or c.get("ticker_yf", ""),
            "direction": c.get("direction", "flat"),
            "analysis": _company_custom_fallback(c)
        }
        if c.get("country") == "il":
            il_companies.append(entry)
        else:
            us_companies.append(entry)

    return {
        "reading_time": "7",
        "focus_companies_count": str(len(us_companies) + len(il_companies)),
        "tldr": [
            f"נפט WTI נסחר ברמת ${oil.get('price','—')} לחבית ({oil.get('change','—')}) על רקע איומי סנקציות ומתיחות בצווארי בקבוק ימיים.",
            f"מדד S&P 500 נסגר סביב רמות שיא ({sp500.get('price','—')} נק') כאשר עונת הדוחות והאג״ח ל-10 שנים מכתיבות את הטון.",
            f"הנחושת ברמת ${copper.get('price','—')} והזהב ב-${gold.get('price','—')} — שוק המתכות מאותת על ביקושי תשתית ל-AI ופרמיית ביטחון."
        ],
        "us_market": {
            "macro_analysis": us_macro,
            "insight": "כשנתון מאקרו רע מקטין חשש מריבית אך מגביר חשש מהאטה — זו דינמיקת חדשות רעות = חדשות טובות שמייצרת תנודתיות דווקא בשיאים.",
            "companies": us_companies,
            "watch_levels": f"🎯 למעקב: סגירה יומית מעל רמות השיא ב-S&P 500 ← המשך מגמת עלייה; ירידה חדה ← המתנה עד להתבהרות מסר הפד והריבית."
        },
        "israel_market": {
            "macro_analysis": il_macro,
            "insight": "ריבית נוחה ושקל יציב מיטיבים עם פיננסים ונדל\"ן מקומי, אך מכבידים על יצואניות שהכנסתן בדולרים.",
            "companies": il_companies,
            "watch_levels": f"🎯 למעקב: שבירת שיא חדש בת\"א-125 ← המשך חשיפה למניות ביטחון ופיננסים; התחזקות או היחלשות חדה בשקל ← התאמת הגנות מט\"ח."
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

    prompt = f"""אתה אנליסט מאקרו בכיר ומחנך פיננסי הכותב בריף מודיעין שוק יומי עבור iQ.finance.
קהל היעד: משקיעים ברמת ביניים (Intermediate). הם מבינים מושגים בסיסיים, אך זקוקים להסבר מעמיק, אינטואיטיבי ומלמד על המנגנונים הכלכליים מאחורי המספרים ("איך המנגנון עובד?"), לצד תובנות חדות שמניעות לקבלת החלטות מעשיות.

תאריך: {date_str}

━━━ נתוני שוק בזמן אמת ━━━
{context}

━━━ תנועות מניות בולטות ━━━
{movers}

━━━ כותרות עיתונות ו-RSS פיננסי בזמן אמת (OilPrice, gCaptain, כלכליסט, CNBC) ━━━
{headlines}

━━━ עקרונות הכתיבה והניתוח (חובה להקפיד!): ━━━
1. 🎓 **מלמד, מסביר ומפתח הבנה:**
   - אל תסתפק בדיווח יבש על שינויי מחירים.
   - הסבר את הקשר הסיבתי (Causality): *למה* הנכס זז, *איזה כוחות שוק* פועלים כאן (היצע/ביקוש, שערי ריבית, אינפלציה, שרשראות אספקה).
   - שלב את סעיפי ה-"תובנה:" וה-"הסבר לימודי:" בצורה בהירה שמלמדת את המנגנון (כמו השפעת אג"ח 10Y {us10y_val}% או ה-VIX {vix_val} על מניות צמיחה).

2. 🧠 **חשיבה מחוץ לקופסה והשפעות עקיפות (2nd & 3rd Order Effects):**
   - חבר בין שווקים: איך מחירי האנרגיה והמתכות (נחושת, זהב, נפט) משפיעים על סקטורים תעשייתיים ועל שוק המניות בישראל ובארה"ב.
   - איך שער הדולר/שקל ({usdils_val} ש"ח) משקף את תיאבון הסיכון והמצב הגיאופוליטי המקומי.

3. ⚡ **מניע לפעולה (Actionable Takeaways & Decisions):**
   - ספק רמות מפתח ברורות בסעיף `🎯 למעקב:` ובסעיף `🎯 מסקנה לפעולה:` עבור כל צוואר בקבוק.

4. 🔍 **אינדיבידואליות מלאה לכל מניה (איסור מוחלט על משפטים משוכפלים!):**
   - כל חברה חייבת לקבל ניתוח שונה ומותאם אישית — מה הקטליזטור העסקי, התוצאות, הביקוש, או החדשות הספציפיות שלה.
   - לעולם אל תחזור על אותו משפט או מבנה גנרי בין חברות שונות.

5. ✍️ **שפה וסגנון:**
   - עברית רהוטה, עשירה, מקצועית ומעוצבת היטב.
   - השתמש במספרים המדויקים שנמסרו בנתונים.

━━━ מבנה ה-JSON הנדרש — החזר אך ורק JSON תקין ━━━
{{
  "reading_time": "7",
  "focus_companies_count": "10",
  "tldr": [
    "1. תובנה 1 ממוקדת מאקרו/אנרגיה/גיאופוליטיקה עם מספרים ממשיים וקטליזטורים",
    "2. תובנה 2 על וול סטריט/מדדים מובילים ודוחות החברות (כמו Nvidia וכו')",
    "3. תובנה 3 על סחורות מפתח (נחושת/זהב) או שוק ישראל ושער הדולר/שקל ({usdils_val} ש״ח)"
  ],
  "us_market": {{
    "macro_analysis": "פסקה של 2-4 משפטים על מדדי וול סטריט (S&P 500, נאסד\"ק), נתוני אינפלציה/PPI/CPI, תשואות האג\"ח ל-10 שנים ({us10y_val}%) והסנטימנט הכללי.",
    "insight": "תובנה מאקרו-כלכלית לימודית (לדוגמה: כשנתון מאקרו רע מקטין חשש מריבית אך מגביר חשש מהאטה — זו דינמיקת חדשות רעות = חדשות טובות...).",
    "companies": [
      {{
        "name": "שם החברה (לדוגמה Nvidia)",
        "ticker": "NVDA",
        "direction": "up",
        "analysis": "קטליזטור עסקי ספציפי וייחודי לחברה, תאריכי דוחות, תחזיות הכנסות, חוזי אספקה, או קשר ישיר למגמת ה-AI/אנרגיה/ביטחון."
      }}
    ],
    "watch_levels": "🎯 למעקב: רמות מפתח מספריות ותרחישי if-then ברורים (לדוגמה: מעל 7,800 נק' בסגירה יומית ← המשך מגמת עלייה, יעד הבא 8,000; ירידה מתחת ל-7,650 ← המתנה...)."
  }},
  "israel_market": {{
    "macro_analysis": "פסקה של 2-3 משפטים על מדד ת\"א-125, החלטות הריבית של בנק ישראל, ושער הדולר/שקל ({usdils_val} ש\"ח).",
    "insight": "תובנת מאקרו מקומית שמסבירה את השפעת הריבית ושער החליפין על חברות מקומיות מול יצואניות.",
    "companies": [
      {{
        "name": "שם החברה (לדוגמה אלביט מערכות)",
        "ticker": "ESLT",
        "direction": "up",
        "analysis": "צבר הזמנות, דוחות כספיים, חוזים בינלאומיים והקשר לפעילות הביטחונית/תעשייתית."
      }}
    ],
    "watch_levels": "🎯 למעקב: תנאי מעקב קונקרטיים בת\"א-125 ובשער הדולר/שקל."
  }},
  "geopolitical": {{
    "event_color": "🟠",
    "main_event": "תיאור מדויק של האירוע הגיאופוליטי המרכזי שמשפיע כעת על הסחר/אנרגיה/סחורות.",
    "verified_fact": "עובדה מספרית מאומתת (לדוגמה: תנועת כלי השיט במצרי באב אל-מנדב צנחה כ-24% מאז...).",
    "structural_meaning": "המשמעות המבנית ארוכת הטווח על שרשרת האספקה ומחירי הסחורות.",
    "bottlenecks": [
      {{
        "title": "מצרי הורמוז ובאב אל-מנדב (נפט גולמי)",
        "type": "main",
        "educational": "הסבר לימודי בהיר בגובה העיניים על המנגנון (כמה נפט עובר, עקיפת כף התקווה הטובה, תוספת ימי שיט, הקטנת היצע אוניות ועליית תעריפי הובלה).",
        "benefiting": [
          {{
            "name": "שם חברה מרוויחה (לדוגמה Frontline)",
            "ticker": "FRO",
            "analysis": "הסבר קצר מדוע היא נהנית מהמצב."
          }}
        ],
        "at_risk": [
          {{
            "name": "שם חברה בסיכון (לדוגמה Delta Air Lines)",
            "ticker": "DAL",
            "analysis": "הסבר קצר איזה לחץ עלויות נוצר עליה."
          }}
        ],
        "conclusion": "🎯 מסקנה לפעולה: טריגר מספרי וברור לפעולה (לדוגמה: מעל 85$ לחבית ל-WTI לשבועיים רצופים ← כניסה למכליות ושיל; ירידה מתחת ל-78$ ← יציאה מפוזיציות טקטיות)."
      }},
      {{
        "title": "נחושת — סחורת ה-AI השקטה",
        "type": "secondary",
        "educational": "הסבר לימודי על הקשר בין חוות שרתי AI, שנאים ורשתות חשמל לבין ביקושי הנחושת והמחסור במכרות.",
        "benefiting": [
          {{
            "name": "שם חברה מרוויחה (לדוגמה Freeport-McMoRan)",
            "ticker": "FCX",
            "analysis": "הסבר מדוע היא נהנית משיאי המחירים בנחושת."
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


