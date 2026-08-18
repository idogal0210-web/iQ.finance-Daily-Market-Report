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
    dxy = macro.get("dxy", {})

    oil = commodities.get("wti", {})
    gold = commodities.get("gold", {})
    copper = commodities.get("copper", {})

    # Build US Macro
    us_parts = []
    if sp500.get("price"):
        us_parts.append(f"מדד S&P 500 נסחר ברמה של {sp500['price']} נקודות ({sp500['change']}), בעוד הנאסד\"ק עומד על {nasdaq.get('price','—')} ({nasdaq.get('change','—')}).")
    if us10y.get("price"):
        us_parts.append(f"תשואת אג\"ח ממשלת ארה\"ב ל-10 שנים נסחרת ברמת {us10y['price']}% ({us10y.get('change','—')}), נתון המהווה עוגן לתמחור כלל נכסי הסיכון.")
    if vix.get("price"):
        us_parts.append(f"מדד התנודתיות (VIX) עומד על {vix['price']} נקודות, ומעיד על רמת הדריכות של המשקיעים.")
    us_parts.append("הסנטימנט הכללי מושפע משיווי המשקל בין נתוני האינפלציה לקצב הורדות הריבית הצפוי של הפד.")
    us_macro = " ".join(us_parts)

    # Build Israel Macro
    il_parts = []
    if ta125.get("price"):
        il_parts.append(f"מדד ת\"א-125 עומד על {ta125['price']} נקודות ({ta125['change']}).")
    if usdils.get("price"):
        il_parts.append(f"שער הדולר/שקל נסחר ברמה של {usdils['price']} ש\"ח ({usdils['change']}).")
    il_parts.append("השוק המקומי ממשיך לנוע בין השפעות המומנטום מוול-סטריט לבין פרמיית הסיכון הגיאופוליטית ומדיניות בנק ישראל.")
    il_macro = " ".join(il_parts)

    # Build Companies
    us_companies = []
    il_companies = []

    for key, c in companies.items():
        if not c.get("verified"):
            continue
        p = c.get("price", "—")
        chg = c.get("change", "—")
        mc = c.get("market_cap", "")
        ma50_info = f" | MA50: {c['ma50']}" if c.get("ma50") else ""
        
        entry = {
            "name": c["label"],
            "ticker": c.get("ticker_fmp") or c.get("ticker_yf", ""),
            "direction": c.get("direction", "flat"),
            "catalyst_and_analysis": f"המניה נסחרת ברמת ${p} ({chg}). שווי שוק: {mc or 'לא זמין'}{ma50_info}. התנועה במניה משקפת את יחסי הכוחות בסקטור ואת זרימת ההון מצד מוסדיים.",
            "actionable_takeaway": f"מומלץ לעקוב אחר תמיכות המחיר הקרובות ויחס הסיכון/סיכוי ביחס לממוצע 50 יום."
        }
        if c.get("country") == "il":
            il_companies.append(entry)
        else:
            us_companies.append(entry)

    return {
        "reading_time": "7-8",
        "focus_companies_count": str(len(us_companies) + len(il_companies)),
        "tldr": [
            f"וול סטריט והאג״ח: מדד S&P 500 ב-{sp500.get('price','—')} נקודות, כאשר תשואות האג״ח ל-10 שנים עומדות על {us10y.get('price','—')}% ומכתיבות את תמחור מניות הצמיחה.",
            f"סחורות ואנרגיה: נפט WTI ברמת ${oil.get('price','—')} וזהב ברמת ${gold.get('price','—')} — שוק הסחורות מאותת על איזון בין ביקושים תעשייתיים לפרמיית סיכון.",
            f"ישראל והמט״ח: שער הדולר/שקל ב-{usdils.get('price','—')} ש״ח, אינדיקטור מרכזי לרמת הסיכון והסנטימנט במשק המקומי."
        ],
        "tactical_takeaways": {
            "market_regime": "סביבת מסחר סלקטיבית — תשואות האג״ח ומדדי התנודתיות מחייבים משמעת ומיקוד בחברות בעלות תזרים מזומנים חזק.",
            "key_opportunities": [
                "סקטור האנרגיה והתשתיות — נהנה מביקוש קשיח ומרווחי זיקוק/שינוע בריאים.",
                "הייטק ו-AI איכותי — חברות מבוססות מובילות שוק מציגות עמידות תפעולית."
            ],
            "key_risks": [
                "קפיצה אפשרית בתשואות האג״ח ל-10 שנים שתלחץ על מכפילי הרווח של מניות הצמיחה.",
                "הסלמה בנתיבי שיט ימיים שתייקר עלויות שילוח וביטוח."
            ],
            "action_bottom_line": "שמור על פיזור מושכל בין חברות ערך ואנרגיה לבין מובילות טכנולוגיה, תוך הקפדה על ניהול סיכונים ורמות כניסה מוגדרות מראש."
        },
        "macro_canvas": {
            "title": "🌐 בריף מאקרו גלובלי ומנגנוני השוק",
            "analysis": us_macro,
            "mechanism_explained": "💡 איך המנגנון עובד? כאשר תשואות האג״ח הממשלתיות עולות, המשקיעים מקבלים תשואה מובטחת וגבוהה יותר ללא סיכון, מה שמקטין את האטרקטיביות של מניות יקרות ומייקר את עלויות המימון לחברות.",
            "takeaway": "🎯 שורה תחתונה: עקוב מקרוב אחר מגמת תשואות ה-10Y — ירידה בהן תהווה רוח גבית למניות הטכנולוגיה."
        },
        "us_market": {
            "macro_analysis": f"המסחר בוול סטריט מתנהל על רקע עונת הדוחות וסנטימנט הריבית. מדד S&P 500 ברמת {sp500.get('price','—')} והנאסד\"ק ב-{nasdaq.get('price','—')}. מדד ה-VIX ברמת {vix.get('price','—')} מצביע על שוק מאוזן ללא פאניקה.",
            "insight": "התנהגות השוק מדגישה את ההבדל בין חברות שנהנות מתמחור יתר לחברות עם צמיחה ריאלית ברווחים.",
            "companies": us_companies,
            "watch_levels": f"🎯 למעקב: רמות שיא 52 שבועות במדדים המובילים ותנועות חדות במחזורי המסחר."
        },
        "israel_market": {
            "macro_analysis": il_macro,
            "insight": "יציבות שער החליפין דולר/שקל היא המפתח העיקרי לזרימת כספים מוסדיים חזרה למניות המקומיות.",
            "companies": il_companies,
            "watch_levels": f"🎯 למעקב: שער הדולר/שקל ברמת {usdils.get('price','—')} ומדד ת\"א-125."
        },
        "commodities_and_geopolitics": {
            "energy_and_metals": f"שוק הסחורות מציג נפט WTI ב-${oil.get('price','—')}, נפט ברנט ב-${commodities.get('brent',{}).get('price','—')}, זהב ב-${gold.get('price','—')} ונחושת ב-${copper.get('price','—')}.",
            "geopolitical_event": "צווארי בקבוק ונתיבי סחר ימי ממשיכים לייצר תנודתיות בעלויות השילוח והאנרגיה.",
            "mechanism_educational": "📘 הסבר לימודי: שיבוש בצוואר בקבוק ימי מאלץ אוניות להקיף יבשות, מאריך את ימי ההפלגה בעד שבועיים ומקטין את היצע האוניות הפנויות — מה שמזניק את דמי ההובלה והביטוח.",
            "benefiting_companies": [
                {"name": "Frontline", "ticker": "FRO", "rationale": "עליית תעריפי ההובלה של מכליות נפט מגדילה ישירות את הרווחיות."},
                {"name": "Diamondback Energy", "ticker": "FANG", "rationale": "הפקת נפט ביבשה בארה״ב ללא תלות בנתיבי שיט מאוימים."}
            ],
            "at_risk_companies": [
                {"name": "Delta Air Lines", "ticker": "DAL", "rationale": "התייקרות הדלק הסילוני (Jet Fuel) מהווה את אחד מסעיפי ההוצאה הגדולים ביותר."}
            ],
            "conclusion": "🎯 מסקנה לפעולה: מעקב צמוד אחר מחירי ההובלה הימית והדלקים מספק התרעה מוקדמת על לחצי אינפלציה מתחדשים."
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

━━━ כותרות עיתונות פיננסית בזמן אמת ━━━
{headlines}

━━━ עקרונות הכתיבה והניתוח (חובה להקפיד!): ━━━
1. 🎓 **מלמד, מסביר ומפתח הבנה:**
   - אל תסתפק בדיווח יבש על שינויי מחירים.
   - הסבר את הקשר הסיבתי (Causality): *למה* הנכס זז, *איזה כוחות שוק* פועלים כאן (היצע/ביקוש, שערי ריבית, אינפלציה, שרשראות אספקה).
   - שלב הסברים לימודיים קצרים וברורים (בגובה העיניים) על מונחים מרכזיים (כמו השפעת תשואות אג"ח 10Y {us10y_val}% על מניות צמיחה, משמעות ה-VIX {vix_val}, וכוחו של הדולר).

2. 🧠 **חשיבה מחוץ לקופסה והשפעות עקיפות (2nd & 3rd Order Effects):**
   - חבר בין שווקים: איך מחירי האנרגיה והמתכות (נחושת, זהב, נפט) משפיעים על סקטורים תעשייתיים ועל שוק המניות בישראל ובארה"ב.
   - איך שער הדולר/שקל ({usdils_val} ש"ח) משקף את תיאבון הסיכון והמצב הגיאופוליטי המקומי.

3. ⚡ **מניע לפעולה (Actionable Takeaways & Decisions):**
   - כל סקשן חייב להסתיים בשורה תחתונה ברורה: "מה זה אומר מבחינתך?".
   - ספק רמות מפתח למעקב, טריגרים לפעולה ותרחישי סיכון/סיכוי אסימטריים.

4. ✍️ **שפה וסגנון:**
   - עברית רהוטה, עשירה, מקצועית ומעוצבת היטב.
   - השתמש במספרים המדויקים שנמסרו בנתונים.

━━━ מבנה ה-JSON הנדרש — החזר אך ורק JSON תקין ━━━
{{
  "reading_time": "7-8",
  "focus_companies_count": "10",
  "tldr": [
    "תובנה 1 ממוקדת מאקרו/אג״ח עם מספרים ממשיים: מה קרה ומה המשמעות להיום",
    "תובנה 2 על שוק הסחורות/אנרגיה/גיאופוליטיקה והשלכותיה",
    "תובנה 3 על שוק המניות הישראלי, שער הדולר/שקל ({usdils_val} ש״ח) ופעולה נדרשת"
  ],
  "tactical_takeaways": {{
    "market_regime": "משפט חד שמגדיר את משטר השוק הנוכחי (תיאבון סיכון, זהירות, רוטציה סקטוריאלית)",
    "key_opportunities": [
        "הזדמנות קונקרטית 1 עם רציונל כלכלי/עסקי",
        "הזדמנות קונקרטית 2 עם רציונל כלכלי/עסקי"
    ],
    "key_risks": [
        "סיכון/נורת אזהרה 1 ומה הטריגר שיעיד על החמרה",
        "סיכון/נורת אזהרה 2 ומה הטריגר שיעיד על החמרה"
    ],
    "action_bottom_line": "2-3 משפטים של הנחיה ישירה למשקיע: איך לנהוג היום בתיק ועל מה להסתכל."
  }},
  "macro_canvas": {{
    "title": "🌐 בריף מאקרו גלובלי ומנגנוני השוק",
    "analysis": "ניתוח מעמיק של 4-6 משפטים: מצב תשואות האג\"ח ל-10 שנים ({us10y_val}%), מדד ה-VIX ({vix_val}), הדולר העולמי והסנטימנט בוול-סטריט.",
    "mechanism_explained": "💡 איך המנגנון עובד? הסבר לימודי בהיר של 2-3 משפטים שמסביר למשקיע ברמת ביניים איך תשואות האג\"ח או מדד הפחד משפיעים ישירות על השוק.",
    "takeaway": "🎯 שורה תחתונה לפעולה: מסקנה מעשית ברורה של 1-2 משפטים."
  }},
  "us_market": {{
    "macro_analysis": "ניתוח מקיף של 4-5 משפטים על מדדי וול סטריט (S&P 500, נאסד\"ק, דאו) עם נתונים מספריים, זרימת כספים סקטוריאלית ומגמות מובילות.",
    "insight": "תובנת מאקרו חדה על מבנה השוק האמריקאי.",
    "companies": [
      {{
        "name": "שם החברה (לדוגמה Nvidia)",
        "ticker": "NVDA",
        "direction": "up",
        "catalyst_and_analysis": "ניתוח מעמיק של 2-3 משפטים: מחיר נוכחי, שינוי%, יחס ל-52 שבועות/MA50, מהו הקטליזטור העסקי/טכנולוגי שהניע את המניה ומה לבדוק.",
        "actionable_takeaway": "שורה תחתונה לפעולה ומעקב עבור המניה."
      }}
    ],
    "watch_levels": "🎯 למעקב: לפחות 2 רמות מחיר ותרחישים למעקב בוול סטריט."
  }},
  "israel_market": {{
    "macro_analysis": "ניתוח מאקרו מקיף של 3-4 משפטים על מדד ת\"א-125, שער דולר/שקל ({usdils_val} ש\"ח), השפעות מדיניות בנק ישראל ופרמיית הסיכון הגיאופוליטית.",
    "insight": "תובנת מאקרו מקומית חדה ומלמדת.",
    "companies": [
      {{
        "name": "שם החברה (לדוגמה אלביט מערכות)",
        "ticker": "ESLT",
        "direction": "up",
        "catalyst_and_analysis": "ניתוח מעמיק ומלמד של 2-3 משפטים כולל נתונים, פעילות עסקית והקשר למצב המאקרו.",
        "actionable_takeaway": "שורה תחתונה לפעולה."
      }}
    ],
    "watch_levels": "🎯 למעקב: רמות מפתח בשער הדולר/שקל ובמדדי תל אביב."
  }},
  "commodities_and_geopolitics": {{
    "energy_and_metals": "ניתוח מקיף של 3-4 משפטים על נפט (WTI, ברנט), גז טבעי, זהב ונחושת — ומה התנועות שלהם מלמדות על הכלכלה העולמית.",
    "geopolitical_event": "תיאור 2-3 משפטים של האירוע או צוואר הבקבוק הגיאופוליטי המרכזי.",
    "mechanism_educational": "📘 הסבר לימודי — מנגנון צוואר הבקבוק: 3-4 משפטים המפרקים בפשטות איך סגירת נתיב שיט או חרם מסחרי מתגלגלים מעליית מחירי שינוע וביטוח ועד לאינפלציה ושולי רווח של חברות.",
    "benefiting_companies": [
      {{
        "name": "שם חברה מרוויחה",
        "ticker": "TICKER",
        "rationale": "הסבר מנומק של 2 משפטים מדוע החברה נהנית מהמצב."
      }}
    ],
    "at_risk_companies": [
      {{
        "name": "שם חברה בסיכון",
        "ticker": "TICKER",
        "rationale": "הסבר מנומק של 2 משפטים איזה לחץ עלויות נוצר על החברה."
      }}
    ],
    "conclusion": "🎯 מסקנה לפעולה: לקח מעשי למשקיע."
  }}
}}"""

    # Model priority: Thinking & Reasoning models first, then fast fallbacks
    models_to_try = [
        "gemini-2.5-pro",
        "gemini-2.0-flash-thinking-exp",
        "gemini-2.0-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ]

    # Try modern google-genai SDK first
    if HAS_GENAI_SDK:
        try:
            client = genai.Client(api_key=api_key)
            for model_name in models_to_try:
                try:
                    print(f"  🤖 מנסה להפיק ניתוח עם {model_name} (google-genai SDK)...")
                    config = types.GenerateContentConfig(
                        temperature=0.3,
                        response_mime_type="application/json",
                    )
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=config,
                    )
                    if response and hasattr(response, "text") and response.text:
                        cleaned = _clean_json_text(response.text)
                        data = json.loads(cleaned)
                        print(f"  ✅ ניתוח איכותי הופק בהצלחה מ-{model_name}!")
                        return data
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
                        "temperature": 0.3,
                        "response_mime_type": "application/json",
                        "max_output_tokens": 8192,
                    },
                    safety_settings=safety_settings,
                )
                response = model.generate_content(prompt)
                if response and hasattr(response, "text") and response.text:
                    cleaned = _clean_json_text(response.text)
                    data = json.loads(cleaned)
                    print(f"  ✅ ניתוח איכותי הופק בהצלחה מ-{model_name} (Legacy SDK)!")
                    return data
            except Exception as leg_err:
                print(f"  [WARN] {model_name} (Legacy) שגיאה: {leg_err}")

    print("  [WARN] All Gemini API models failed — using smart dynamic data-driven fallback")
    return _smart_dynamic_fallback(market_data)

