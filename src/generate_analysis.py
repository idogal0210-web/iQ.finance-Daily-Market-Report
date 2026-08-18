"""
generate_analysis.py — v3
==========================
שולח נתוני שוק עשירים ל-Gemini ומקבל ניתוח מלא ומעמיק.
"""

import json
import re
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold


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



def _smart_dynamic_fallback(market_data: dict) -> dict:
    """Generates a rich, data-driven analysis from real market metrics if Gemini API is unavailable."""
    indices = market_data.get("indices", {})
    companies = market_data.get("companies", {})
    commodities = market_data.get("commodities", {})

    sp500 = indices.get("sp500", {})
    nasdaq = indices.get("nasdaq", {})
    dow = indices.get("dow", {})
    ta125 = indices.get("ta125", {})
    usdils = indices.get("usdils", {})

    # Build US Macro
    us_parts = []
    if sp500.get("price"):
        us_parts.append(f"מדד S&P 500 נסחר ברמה של {sp500['price']} נקודות (שינוי יומי של {sp500['change']}).")
    if nasdaq.get("price"):
        us_parts.append(f"מדד הנאסד\"ק נסחר ברמה של {nasdaq['price']} ({nasdaq['change']}).")
    if dow.get("price"):
        us_parts.append(f"מדד דאו ג'ונס נסחר ברמה של {dow['price']} ({dow['change']}).")
    us_parts.append("המסחר בוול סטריט מושפע מציפיות הריבית של הפד ומנתוני המאקרו העדכניים בארה\"ב.")
    us_parts.append("המשקיעים בוחנים את מרווחי התשואות בשוק האג\"ח ואת התקדמות עונת הדוחות של חברות הטכנולוגיה.")
    us_macro = " ".join(us_parts)

    # Build Israel Macro
    il_parts = []
    if ta125.get("price"):
        il_parts.append(f"מדד ת\"א-125 נסחר ברמת {ta125['price']} נקודות עם שינוי של {ta125['change']}.")
    if usdils.get("price"):
        il_parts.append(f"שער הדולר/שקל עומד על {usdils['price']} ש\"ח לדולר ({usdils['change']}).")
    il_parts.append("השוק המקומי ממשיך להגיב להתפתחויות הגיאופוליטיות ולהחלטות הריבית של בנק ישראל.")
    il_macro = " ".join(il_parts)

    # Build Company Analyses
    us_companies = []
    il_companies = []

    for key, c in companies.items():
        if not c.get("verified"):
            continue
        p = c.get("price", "—")
        chg = c.get("change", "—")
        mc = c.get("market_cap", "")
        yr_h = c.get("year_high")
        
        extra = []
        if mc: extra.append(f"שווי שוק {mc}")
        if yr_h: 
            try: extra.append(f"שיא 52 שבועות {float(yr_h):.2f}")
            except Exception: pass
        extra_str = f" ({', '.join(extra)})" if extra else ""

        entry = {
            "name": c["label"],
            "ticker": c.get("ticker_fmp") or c.get("ticker_yf", ""),
            "direction": c.get("direction", "flat"),
            "analysis": f"המניה נסחרת במחיר של ${p} בשינוי של {chg}{extra_str}. החברה מרכזת עניין רב בקרב המשקיעים בעקבות תנודות השוק והמגמות הסקטוריאליות."
        }
        if c.get("country") == "il":
            il_companies.append(entry)
        else:
            us_companies.append(entry)

    # Commodities overview for TLDR
    oil = commodities.get("wti", {})
    gold = commodities.get("gold", {})
    oil_str = f"נפט WTI ברמת ${oil.get('price','—')} ({oil.get('change','—')})" if oil else "תנודתיות במחירי האנרגיה"
    gold_str = f"זהב ברמת ${gold.get('price','—')} ({gold.get('change','—')})" if gold else "ביקוש יציב לנכסי מקלט"

    return {
        "reading_time": "6",
        "focus_companies_count": str(len(us_companies) + len(il_companies)),
        "tldr": [
            f"תנועות בשוקי המניות: {us_macro[:130]}...",
            f"שוק הסחורות והאנרגיה: {oil_str}, {gold_str}.",
            f"השוק המקומי והמט״ח: שער דולר/שקל ב-USD/ILS {usdils.get('price','—')} ש״ח."
        ],
        "us_market": {
            "macro_analysis": us_macro,
            "insight": "תובנה: התנודתיות בשווקים משקפת את האיזון העדין בין תחזיות הצמיחה לציפיות הריבית.",
            "companies": us_companies,
            "watch_levels": f"🎯 למעקב: S&P 500 ברמות מפתח — פריצה למעלה מעידה על המשך המומנטום החיובי."
        },
        "israel_market": {
            "macro_analysis": il_macro,
            "insight": "תובנה: שער החליפין דולר/שקל ממשיך להוות אינדיקטור מרכזי לרמת הסיכון בשוק המקומי.",
            "companies": il_companies,
            "watch_levels": f"🎯 למעקב: ת\"א-125 ושער הדולר/שקל ברמת {usdils.get('price','—')} ש\"ח."
        },
        "geopolitical": {
            "event_color": "🟠",
            "main_event": f"המתח הגיאופוליטי העולמי משפיע ישירות על נתיבי הסחר הימי ומחירי האנרגיה, כאשר WTI נסחר ב-${oil.get('price','—')} וזהב ב-${gold.get('price','—')}.",
            "verified_fact": f"✅ עובדה מאומתת: מחירי הנפט והזהב משקפים פרמיית סיכון גיאופוליטית פעילה.",
            "structural_meaning": "🧭 משמעות מבנית: שינויים בשרשראות האספקה העולמיות מייצרים הזדמנויות ואתגרים לחברות הספנות והאנרגיה.",
            "bottlenecks": [
                {
                    "type": "main",
                    "title": "נתיבי שינוע אנרגיה וסחורות",
                    "educational": "📘 הסבר לימודי: שיבושים בצווארי בקבוק ימיים גורמים להארכת מסלולי השייט, הגדלת עלויות הדלק והובלת המכולות, מה שמתרגם לעליית מחירי הסחורות.",
                    "benefiting": [c for c in us_companies if c["ticker"] in ("FRO", "FANG", "FCX")],
                    "at_risk": [c for c in us_companies if c["ticker"] in ("DAL",)],
                    "conclusion": "🎯 מסקנה לפעולה: מעקב צמוד אחר מחירי הנפט והספנות הימית לצורך ניהול סיכוני פוזיציה."
                }
            ]
        }
    }


# ── Context builders ───────────────────────────────────────────────────────────
def _rich_company_line(v: dict) -> str:
    """Builds a rich single-line summary of a company for the prompt."""
    parts = [f"  {'🇺🇸' if v.get('country')=='us' else '🇮🇱'} {v['label']:22} ({v.get('ticker_fmp') or v.get('ticker_yf','?'):6})"]
    parts.append(f"  price=${v['price']}  change={v['change']}")
    if v.get("year_high") and v.get("year_low"):
        try:
            parts.append(f"  52wk=[{float(v['year_low']):.2f}–{float(v['year_high']):.2f}]")
        except Exception:
            parts.append(f"  52wk=[{v['year_low']}–{v['year_high']}]")
    if v.get("ma50") and v.get("price_raw"):
        try:
            rel_ma50 = ((float(v["price_raw"]) / float(v["ma50"])) - 1) * 100
            parts.append(f"  vs_MA50={rel_ma50:+.1f}%")
        except Exception:
            pass
    if v.get("market_cap"):
        parts.append(f"  mktcap={v['market_cap']}")
    if v.get("volume"):
        parts.append(f"  vol={v['volume']}")
    return "".join(parts)


def _build_context(market_data: dict) -> str:
    lines = []

    lines.append("📈 מדדים ומט״ח:")
    for v in market_data.get("indices", {}).values():
        flag = "🇺🇸" if v.get("country") == "us" else "🇮🇱"
        yr_h = ""
        if v.get("year_high"):
            try: yr_h = f"  52wk_high={float(v['year_high']):.2f}"
            except Exception: yr_h = f"  52wk_high={v['year_high']}"
        ma50 = ""
        if v.get("ma50"):
            try: ma50 = f"  MA50={float(v['ma50']):.2f}"
            except Exception: ma50 = f"  MA50={v['ma50']}"
        lines.append(f"  {flag} {v['label']:18} price={v['price']}  chg={v['change']}{yr_h}{ma50}")

    lines.append("\n🏢 מניות חברות:")
    for v in market_data.get("companies", {}).values():
        if v.get("verified"):
            lines.append(_rich_company_line(v))
        else:
            lines.append(f"  {v['label']:22} ⚪ לא זמין")

    lines.append("\n⛽ סחורות:")
    for v in market_data.get("commodities", {}).values():
        lines.append(f"  {v['label']:28} {v['price']:>12}  chg={v['change']}  ({v.get('unit', '')})")

    return "\n".join(lines)


def _build_movers(market_data: dict) -> str:
    up   = [f"{v['label']} ({v.get('ticker_fmp') or v.get('ticker_yf','?')}) {v['change']}"
            for v in market_data.get("companies", {}).values() if v.get("direction") == "up" and v.get("verified")]
    down = [f"{v['label']} ({v.get('ticker_fmp') or v.get('ticker_yf','?')}) {v['change']}"
            for v in market_data.get("companies", {}).values() if v.get("direction") == "down" and v.get("verified")]
    return f"עליות: {', '.join(up[:5]) or 'אין'}\nירידות: {', '.join(down[:5]) or 'אין'}"


# ── Main ───────────────────────────────────────────────────────────────────────
def generate_report(api_key: str, market_data: dict) -> dict:
    if not api_key:
        print("  [WARN] GEMINI_API_KEY לא הוגדר — משתמש בניתוח נתונים דינמי")
        return _smart_dynamic_fallback(market_data)

    genai.configure(api_key=api_key)

    context   = _build_context(market_data)
    movers    = _build_movers(market_data)
    headlines = "\n".join(f"  • {h[:220]}" for h in market_data.get("headlines", [])[:12]) or "אין כותרות."
    date_str  = market_data.get("date", "")
    usdils_val = market_data.get("indices", {}).get("usdils", {}).get("price", "⚪ לא זמין")

    prompt = f"""אתה אנליסט פיננסי ישראלי בכיר הכותב עבור iQ.finance דוח שוק יומי מקיף ומעמיק.
היום: {date_str}

━━━ נתוני שוק בזמן אמת ━━━
{context}

━━━ תנועות בולטות ━━━
{movers}

━━━ כותרות עיתונות ━━━
{headlines}

━━━ הוראות חובה ━━━
🔴 CRITICAL — MINIMUM LENGTH REQUIREMENTS:
  • macro_analysis (US):     לפחות 5 משפטים מלאים עם מספרים ספציפיים (S&P 500, נאסד"ק, דאו).
  • macro_analysis (Israel): לפחות 3 משפטים מלאים עם מספרים (ת"א-125, שער דולר/שקל {usdils_val}).
  • כל company analysis:     2-3 משפטים: מחיר מדויק, שינוי%, יחס ל-52 שבועות/MA50, וקטליזטור עסקי/מאקרו.
  • educational (bottleneck): לפחות 3 משפטים עם מנגנון שוק ספציפי.
  • watch_levels:            לפחות 2 תנאים עם רמות מחיר מדויקות.
  • קריאה מוערכת: 7-8 דקות → כתוב בהתאם!

🔵 כללי כתיבה:
  • כל הטקסט בעברית בלבד.
  • השתמש במספרים המדויקים המופיעים בנתונים בזמן אמת.
  • אל תוסיף סימני ⚪ אלא אם הנתון חסר לגמרי בנתונים שנמסרו.
  • סגנון: מקצועי, מספרי, מניע לפעולה.
  • company direction: "up" / "down" / "flat"

━━━ JSON Schema — החזר JSON בלבד ━━━
{{
  "reading_time": "7",
  "focus_companies_count": "10",
  "tldr": [
    "נקודה 1 עם מספרים ממשיים מהנתונים: מדד/מחיר/מניה + הסבר",
    "נקודה 2 — מגמה גלובלית או גיאופוליטית עם נתון ספציפי",
    "נקודה 3 — אירוע ישראלי / מאקרו + מספר שער דולר/שקל ({usdils_val})"
  ],
  "us_market": {{
    "macro_analysis": "ניתוח מאקרו מקיף לארה\"ב (לפחות 5 משפטים עם נתונים מספריים)",
    "insight": "תובנת מאקרו חדה",
    "companies": [
      {{
        "name": "Nvidia",
        "ticker": "NVDA",
        "direction": "up",
        "analysis": "ניתוח מקיף בת 2-3 משפטים עם מחיר, שינוי%, וגורם מניע"
      }}
    ],
    "watch_levels": "🎯 למעקב: רמות מחיר ותרחישים למעקב"
  }},
  "israel_market": {{
    "macro_analysis": "ניתוח מאקרו מקיף לישראל (לפחות 3 משפטים כולל ת\"א-125 ושער דולר/שקל {usdils_val})",
    "insight": "תובנת מאקרו מקומית חדה",
    "companies": [
      {{
        "name": "אלביט מערכות",
        "ticker": "ESLT",
        "direction": "up",
        "analysis": "ניתוח מקיף בת 2-3 משפטים"
      }}
    ],
    "watch_levels": "🎯 למעקב: רמות מחיר ותרחישים למעקב"
  }},
  "geopolitical": {{
    "event_color": "🟠",
    "main_event": "תיאור 2-3 משפטים של האירוע הגיאופוליטי הדומיננטי",
    "verified_fact": "✅ עובדה מאומתת: נתון מספרי קונקרטי",
    "structural_meaning": "🧭 משמעות מבנית: השלכות ארוכות טווח",
    "bottlenecks": [
      {{
        "type": "main",
        "title": "שם צוואר הבקבוק הראשי",
        "educational": "📘 הסבר לימודי מפורט (לפחות 3 משפטים)",
        "benefiting": [
          {{
            "name": "Frontline",
            "ticker": "FRO",
            "analysis": "ניתוח 2 משפטים"
          }}
        ],
        "at_risk": [
          {{
            "name": "Delta Air Lines",
            "ticker": "DAL",
            "analysis": "ניתוח 2 משפטים"
          }}
        ],
        "conclusion": "🎯 מסקנה לפעולה"
      }}
    ]
  }}
}}"""

    safety_settings = {
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }

    models_to_try = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-exp"]

    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(
                model_name,
                generation_config={
                    "temperature":        0.4,
                    "response_mime_type": "application/json",
                    "max_output_tokens":  8192,
                },
                safety_settings=safety_settings,
            )
            response = model.generate_content(prompt)
            if not response or not hasattr(response, "text"):
                print(f"  [WARN] {model_name}: תגובה ריקה מ-Gemini")
                continue

            cleaned_text = _clean_json_text(response.text)
            result = json.loads(cleaned_text)
            print(f"  ✅ {model_name}: ניתוח נוצר בהצלחה מ-Gemini")
            return result
        except json.JSONDecodeError as err:
            print(f"  [WARN] {model_name} JSON Decode Error: {err}")
            try:
                if response and hasattr(response, "text"):
                    cleaned_text = _clean_json_text(response.text)
                    res = json.loads(cleaned_text)
                    print(f"  ✅ {model_name}: ניתוח חולץ בהצלחה מ-JSON נקי")
                    return res
            except Exception:
                pass
        except Exception as ex:
            print(f"  [WARN] {model_name} Error: {ex}")

    print("  [WARN] All Gemini API models failed — using smart dynamic data-driven fallback")
    return _smart_dynamic_fallback(market_data)
