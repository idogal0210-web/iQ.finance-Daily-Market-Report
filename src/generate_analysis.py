"""
generate_analysis.py — v3
==========================
שולח נתוני שוק עשירים ל-Gemini ומקבל ניתוח מלא ומעמיק.
"""

import json
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold


# ── Context builders ───────────────────────────────────────────────────────────
def _rich_company_line(v: dict) -> str:
    """Builds a rich single-line summary of a company for the prompt."""
    parts = [f"  {'🇺🇸' if v['country']=='us' else '🇮🇱'} {v['label']:22} ({v.get('ticker_fmp') or v.get('ticker_yf','?'):6})"]
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
    for v in market_data["indices"].values():
        flag = "🇺🇸" if v["country"] == "us" else "🇮🇱"
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
    for v in market_data["companies"].values():
        if v["verified"]:
            lines.append(_rich_company_line(v))
        else:
            lines.append(f"  {v['label']:22} ⚪ לא זמין")

    lines.append("\n⛽ סחורות:")
    for v in market_data["commodities"].values():
        lines.append(f"  {v['label']:28} {v['price']:>12}  chg={v['change']}  ({v['unit']})")

    return "\n".join(lines)


def _build_movers(market_data: dict) -> str:
    up   = [f"{v['label']} ({v.get('ticker_fmp') or v.get('ticker_yf','?')}) {v['change']}"
            for v in market_data["companies"].values() if v["direction"] == "up" and v["verified"]]
    down = [f"{v['label']} ({v.get('ticker_fmp') or v.get('ticker_yf','?')}) {v['change']}"
            for v in market_data["companies"].values() if v["direction"] == "down" and v["verified"]]
    return f"עליות: {', '.join(up[:5]) or 'אין'}\nירידות: {', '.join(down[:5]) or 'אין'}"


# ── Main ───────────────────────────────────────────────────────────────────────
def generate_report(api_key: str, market_data: dict) -> dict:
    genai.configure(api_key=api_key)

    context   = _build_context(market_data)
    movers    = _build_movers(market_data)
    headlines = "\n".join(f"  • {h[:220]}" for h in market_data["headlines"][:12]) or "אין כותרות."
    date_str  = market_data["date"]
    usdils_val = market_data["indices"].get("usdils", {}).get("price", "⚪ לא זמין")

    prompt = f"""אתה אנליסט פיננסי ישראלי בכיר הכותב עבור iQ.finance דוח שוק יומי מקיף ומעמיק.
היום: {date_str}

━━━ נתוני שוק בזמן אמת ━━━
{context}

━━━ תנועות בולטות ━━━
{movers}

━━━ כותרות עיתונות (אנגלית) ━━━
{headlines}

━━━ הוראות חובה ━━━
🔴 CRITICAL — MINIMUM LENGTH REQUIREMENTS (אל תקצר!):
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
        "name": "שם החברה (לדוגמה Nvidia)",
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
        "name": "שם החברה (לדוגמה אלביט מערכות)",
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
            "name": "שם חברה מרוויחה",
            "ticker": "TICKER",
            "analysis": "ניתוח 2 משפטים"
          }}
        ],
        "at_risk": [
          {{
            "name": "שם חברה בסיכון",
            "ticker": "TICKER",
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

    models_to_try = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash"]
    last_ex = None

    for model_name in models_to_try:
        response = None
        try:
            model = genai.GenerativeModel(
                model_name,
                generation_config={
                    "temperature":        0.5,
                    "response_mime_type": "application/json",
                    "max_output_tokens":  8192,
                },
                safety_settings=safety_settings,
            )
            response = model.generate_content(prompt)
            text = getattr(response, "text", "")
            result = json.loads(text)
            print(f"  ✅ {model_name}: ניתוח נוצר בהצלחה")
            return result
        except json.JSONDecodeError:
            if response:
                text = getattr(response, "text", "")
                s, e = text.find("{"), text.rfind("}") + 1
                if s != -1 and e > s:
                    try:
                        res = json.loads(text[s:e])
                        print(f"  ✅ {model_name}: ניתוח חולץ מ-JSON")
                        return res
                    except Exception:
                        pass
        except Exception as ex:
            print(f"  [WARN] {model_name} error: {ex}")
            last_ex = ex

    print("  [WARN] All Gemini models failed — using fallback")
    return _fallback(market_data)


def _fallback(market_data: dict) -> dict:
    return {
        "reading_time": "4", "focus_companies_count": "10",
        "tldr": [
            "שוק הסחורות מציג מגמות מעורבות — ראה טבלאות מחירים.",
            "נתוני מאקרו ממשיכים לעצב ציפיות ריבית גלובליות.",
            "הבורסה הישראלית נסחרת בסמוך לשיאים — ת\"א-125 בטבלה.",
        ],
        "us_market":    {"macro_analysis": "⚪ ניתוח AI לא זמין.", "insight": "", "companies": [], "watch_levels": ""},
        "israel_market":{"macro_analysis": "⚪ ניתוח AI לא זמין.", "insight": "", "companies": [], "watch_levels": ""},
        "geopolitical": {"event_color": "⚪", "main_event": "לא זמין.", "verified_fact": "", "structural_meaning": "", "bottlenecks": []},
    }
