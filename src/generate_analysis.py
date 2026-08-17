"""
generate_analysis.py — v3
==========================
שולח נתוני שוק עשירים ל-Gemini 1.5 Pro ומקבל ניתוח מלא ומעמיק.
"""

import json
import google.generativeai as genai


# ── Context builders ───────────────────────────────────────────────────────────
def _rich_company_line(v: dict) -> str:
    """Builds a rich single-line summary of a company for the prompt."""
    parts = [f"  {'🇺🇸' if v['country']=='us' else '🇮🇱'} {v['label']:22} ({v.get('ticker_fmp') or v.get('ticker_yf','?'):6})"]
    parts.append(f"  price=${v['price']}  change={v['change']}")
    if v.get("year_high") and v.get("year_low"):
        parts.append(f"  52wk=[{v['year_low']:.2f}–{v['year_high']:.2f}]")
    if v.get("ma50"):
        rel_ma50 = ((v["price_raw"] / v["ma50"]) - 1) * 100
        parts.append(f"  vs_MA50={rel_ma50:+.1f}%")
    if v.get("market_cap"):
        parts.append(f"  mktcap={v['market_cap']}")
    if v.get("volume"):
        parts.append(f"  vol={v['volume']}")
    return "".join(parts)


def _build_context(market_data: dict) -> str:
    lines = []

    lines.append("📈 מדדים:")
    for v in market_data["indices"].values():
        flag = "🇺🇸" if v["country"] == "us" else "🇮🇱"
        yr_h = f"  52wk_high={v['year_high']:.2f}" if v.get("year_high") else ""
        ma50 = f"  MA50={v['ma50']:.2f}" if v.get("ma50") else ""
        lines.append(f"  {flag} {v['label']:15} price={v['price']}  chg={v['change']}{yr_h}{ma50}")

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

    # Use Pro for maximum quality — 1 request/day is well within free quota
    model = genai.GenerativeModel(
        "gemini-1.5-pro",
        generation_config={
            "temperature":          0.5,
            "response_mime_type":   "application/json",
            "max_output_tokens":    8192,
        },
    )

    context   = _build_context(market_data)
    movers    = _build_movers(market_data)
    headlines = "\n".join(f"  • {h[:220]}" for h in market_data["headlines"][:12]) or "אין כותרות."
    date_str  = market_data["date"]

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
  • macro_analysis (US):     לפחות 5 משפטים מלאים עם מספרים ספציפיים
  • macro_analysis (Israel): לפחות 3 משפטים מלאים עם מספרים
  • כל company analysis:     2-3 משפטים: מחיר, שינוי%, רמת 52-שבועות, ממוצע נע 50, קטליזטור
  • educational (bottleneck): לפחות 3 משפטים עם מנגנון שוק ספציפי
  • watch_levels:            לפחות 2 תנאים עם רמות מחיר מדויקות
  • קריאה מוערכת: 7-8 דקות → כתוב בהתאם!

🔵 כללי כתיבה:
  • כל הטקסט בעברית בלבד
  • השתמש במספרים המדויקים מהנתונים (52-week highs/lows, MA50, market cap, volume)
  • מידע שאינו בנתונים: סמן ⚪
  • סגנון: ישיר, מספרי, מניע לפעולה
  • company direction: "up"/"down"/"flat"

━━━ JSON Schema — החזר JSON בלבד ━━━
{{
  "reading_time": "7",
  "focus_companies_count": "10",
  "tldr": [
    "נקודה 1 עם מספרים ממשיים מהנתונים: מדד/מחיר/מניה + הסבר",
    "נקודה 2 — מגמה גלובלית או גיאופוליטית עם נתון ספציפי",
    "נקודה 3 — אירוע ישראלי / מאקרו + מספר"
  ],
  "us_market": {{
    "macro_analysis": "לפחות 5 משפטים: מה עשו S&P 500 ({market_data['indices'].get('sp500', {}).get('price','?')}), נאסד\"ק ({market_data['indices'].get('nasdaq', {}).get('price','?')}), ודאו ({market_data['indices'].get('dow', {}).get('price','?')}) — הסיבה, גורמים מניעים, מה הניע את המסחר, תחזיות ריבית, Jackson Hole/CPI/PPI אם רלוונטי. השתמש ברמות 52-שבועות.",
    "insight": "תובנה: משפט חד שמסביר דינמיקה לא-מובנת-מאליה",
    "companies": [
      {{
        "name": "Nvidia",
        "ticker": "NVDA",
        "direction": "up",
        "analysis": "2-3 משפטים: מחיר ${market_data['companies'].get('nvda', {}).get('price','?')} ({market_data['companies'].get('nvda', {}).get('change','?')} ביום), יחס לממוצע 50 יום ולשיא 52 שבועות, קטליזטור עיקרי."
      }},
      {{
        "name": "Lockheed Martin",
        "ticker": "LMT",
        "direction": "up",
        "analysis": "2-3 משפטים עם מחיר ${market_data['companies'].get('lmt', {}).get('price','?')} ({market_data['companies'].get('lmt', {}).get('change','?')}), רמות 52 שבועות, וגורם גיאופוליטי/ביטחוני."
      }},
      {{
        "name": "Delta Air Lines",
        "ticker": "DAL",
        "direction": "down",
        "analysis": "2-3 משפטים עם מחיר ${market_data['companies'].get('dal', {}).get('price','?')} ({market_data['companies'].get('dal', {}).get('change','?')}), השפעת עלות דלק, רמת ביקוש."
      }},
      {{
        "name": "Vistra",
        "ticker": "VST",
        "direction": "up",
        "analysis": "..."
      }},
      {{
        "name": "Frontline",
        "ticker": "FRO",
        "direction": "up",
        "analysis": "..."
      }},
      {{
        "name": "Freeport-McMoRan",
        "ticker": "FCX",
        "direction": "up",
        "analysis": "..."
      }},
      {{
        "name": "Diamondback Energy",
        "ticker": "FANG",
        "direction": "up",
        "analysis": "..."
      }}
    ],
    "watch_levels": "🎯 למעקב: תנאי 1 עם רמת מחיר ← פעולה מומלצת; תנאי 2 עם רמת מחיר שנייה ← פעולה אחרת."
  }},
  "israel_market": {{
    "macro_analysis": "לפחות 3 משפטים: ת\"א-125 ({market_data['indices'].get('ta125', {}).get('price','?')}), ריבית בנק ישראל (אחרון), שקל/דולר, כלכלה מקומית וגיאופוליטיקה.",
    "insight": "תובנה: ...",
    "companies": [
      {{
        "name": "אלביט מערכות",
        "ticker": "ESLT",
        "direction": "up",
        "analysis": "2-3 משפטים: צבר הזמנות, הכנסות, קשר לגיאופוליטיקה."
      }},
      {{
        "name": "ICL Group",
        "ticker": "ICL",
        "direction": "up",
        "analysis": "2-3 משפטים: אשלגן/דשנים, הסכמי אספקה, מחיר ICL proxy מהנתונים."
      }},
      {{
        "name": "Southern Copper",
        "ticker": "SCCO",
        "direction": "up",
        "analysis": "..."
      }}
    ],
    "watch_levels": "🎯 למעקב: ..."
  }},
  "geopolitical": {{
    "event_color": "🟠",
    "main_event": "2-3 משפטים: האירוע הגיאופוליטי הדומיננטי, פרטים ומספרים ספציפיים.",
    "verified_fact": "✅ עובדה מאומתת: עובדה קונקרטית ומספרית.",
    "structural_meaning": "🧭 משמעות מבנית: 2 משפטים על ההשלכה ארוכת הטווח על שווקים.",
    "bottlenecks": [
      {{
        "type": "main",
        "title": "שם מדויק של צוואר הבקבוק הראשי",
        "educational": "📘 הסבר לימודי: לפחות 3 משפטים המסבירים את מנגנון השוק בפירוט — כיצד הגיאופוליטיקה מחוללת עלייה בעלויות, מה מנגנון ה-ton-mile / backwardation / שוק החוזים.",
        "benefiting": [
          {{
            "name": "Frontline",
            "ticker": "FRO",
            "analysis": "ניתוח 2 משפטים עם מספרים."
          }},
          {{
            "name": "Diamondback Energy",
            "ticker": "FANG",
            "analysis": "..."
          }}
        ],
        "at_risk": [
          {{
            "name": "Delta Air Lines",
            "ticker": "DAL",
            "analysis": "..."
          }}
        ],
        "conclusion": "🎯 מסקנה לפעולה: רמה X ← כניסה/הגדלה; רמה Y ← יציאה/צמצום."
      }},
      {{
        "type": "secondary",
        "title": "שם צוואר בקבוק משני (סחורה שונה מהראשון)",
        "educational": "📘 הסבר לימודי: לפחות 3 משפטים.",
        "benefiting": [
          {{"name": "Freeport-McMoRan", "ticker": "FCX", "analysis": "..."}},
          {{"name": "Southern Copper",   "ticker": "SCCO","analysis": "..."}}
        ],
        "at_risk": [],
        "conclusion": "🎯 מסקנה לפעולה: ..."
      }}
    ]
  }}
}}"""

    try:
        response = model.generate_content(prompt)
        result   = json.loads(response.text)
        print("  ✅ Gemini Pro: ניתוח נוצר בהצלחה")
        return result
    except json.JSONDecodeError:
        text = getattr(response, "text", "")
        s, e = text.find("{"), text.rfind("}") + 1
        if s != -1 and e > s:
            try:
                return json.loads(text[s:e])
            except Exception:
                pass
        print("  [WARN] JSON parse failed — using fallback")
        return _fallback(market_data)
    except Exception as ex:
        print(f"  [WARN] Gemini error: {ex}")
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
