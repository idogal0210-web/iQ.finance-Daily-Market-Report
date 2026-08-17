"""
generate_analysis.py
====================
מייצר ניתוח שוק מלא ומובנה בעברית עם Gemini AI.
מחזיר dict שמכיל את כל חלקי הדוח לשימוש ב-build_report.
"""

import json
import google.generativeai as genai


# ── Context builders ───────────────────────────────────────────────────────────
def _market_context(market_data: dict) -> str:
    lines = []

    lines.append("📈 מדדי מניות:")
    for v in market_data["indices"].values():
        p = v["price"] if v["verified"] else "לא זמין"
        lines.append(f"  {v['label']:15} {p:>12}  שינוי: {v['change']}")

    lines.append("\n🏢 מניות חברות:")
    for v in market_data["companies"].values():
        flag = "🇺🇸" if v["country"] == "us" else "🇮🇱"
        p = v["price"] if v["verified"] else "לא זמין"
        lines.append(f"  {flag} {v['label']:22} ({v['ticker']:6})  ${p}  {v['change']}")

    lines.append("\n⛽ סחורות:")
    for v in market_data["commodities"].values():
        p = v["price"] if v["verified"] else "לא זמין"
        lines.append(f"  {v['label']:28} {p:>12} {v['change']:>10}  ({v['unit']})")

    return "\n".join(lines)


def _movers(market_data: dict) -> str:
    ups = [
        f"{v['label']} ({v['ticker']}) {v['change']}"
        for v in market_data["companies"].values()
        if v["direction"] == "up" and v["verified"]
    ][:5]
    downs = [
        f"{v['label']} ({v['ticker']}) {v['change']}"
        for v in market_data["companies"].values()
        if v["direction"] == "down" and v["verified"]
    ][:5]
    return (
        f"עליות: {', '.join(ups) if ups else 'אין'}\n"
        f"ירידות: {', '.join(downs) if downs else 'אין'}"
    )


# ── Main function ──────────────────────────────────────────────────────────────
def generate_report(api_key: str, market_data: dict) -> dict:
    """
    Calls Gemini with all market data → returns structured analysis dict.
    Uses JSON mode for reliable output parsing.
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config={
            "temperature": 0.45,
            "response_mime_type": "application/json",
            "max_output_tokens": 4096,
        },
    )

    context   = _market_context(market_data)
    movers    = _movers(market_data)
    headlines = "\n".join(f"  • {h[:220]}" for h in market_data["headlines"][:10]) or "אין כותרות זמינות."
    date_str  = market_data["date"]

    prompt = f"""אתה אנליסט פיננסי ישראלי בכיר שכותב דוחות שוק יומיים מקצועיים ב-iQ.finance.
היום: {date_str}

━━━ נתוני שוק אמיתיים ━━━
{context}

━━━ תנועות בולטות היום ━━━
{movers}

━━━ כותרות עיתונות (אנגלית) ━━━
{headlines}

━━━ הוראות כתיבה ━━━
• כל הטקסט בעברית בלבד.
• השתמש במספרים המדויקים מהנתונים לעיל בכל מקום אפשרי.
• כשאתה מוסיף מידע שאינו בנתונים (כגון תאריכי דוחות, צבר הזמנות, נתוני רבעון) — סמן ב-⚪.
• כל ניתוח חברה: ציין מחיר + שינוי יומי + קטליזטור עיקרי.
• כתוב בסגנון ישיר, מספרי, מניע לפעולה.
• אורך כל ניתוח חברה: 1-2 משפטים.
• בסעיפי "למעקב": ציין רמות מחיר קונקרטיות שמגדירות עלייה/ירידה.

━━━ JSON Schema (החזר JSON בלבד, ללא טקסט נוסף) ━━━
{{
  "reading_time": "7",
  "focus_companies_count": "10",
  "tldr": [
    "נקודה 1 — עם מספרים ספציפיים מהנתונים האמיתיים (נפט/מדדים/מניה מובילה)",
    "נקודה 2 — מגמה גלובלית מרכזית עם נתונים",
    "נקודה 3 — אירוע ישראלי / מאקרו כלכלי משמעותי"
  ],
  "us_market": {{
    "macro_analysis": "2-4 משפטים: מה עשו המדדים היום, מדוע, ומה הגורם הדומיננטי. כלול מספרים מהנתונים.",
    "insight": "תובנה: משפט אחד חד שמסביר דינמיקה לא-מובנת-מאליה בשוק.",
    "companies": [
      {{
        "name": "Nvidia",
        "ticker": "NVDA",
        "direction": "up",
        "analysis": "ניתוח קצר עם מחיר ($XX.XX, +X.XX% ביום) וקטליזטור עיקרי."
      }},
      {{
        "name": "Vistra",
        "ticker": "VST",
        "direction": "up",
        "analysis": "..."
      }},
      {{
        "name": "Lockheed Martin",
        "ticker": "LMT",
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
        "name": "Diamondback Energy",
        "ticker": "FANG",
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
        "name": "Delta Air Lines",
        "ticker": "DAL",
        "direction": "down",
        "analysis": "..."
      }}
    ],
    "watch_levels": "🎯 למעקב: תנאי עלייה ← פעולה מומלצת; תנאי ירידה ← פעולה מומלצת."
  }},
  "israel_market": {{
    "macro_analysis": "2-3 משפטים: ת\"א-125, מדיניות בנק ישראל, ריבית, שקל/דולר. כלול מספרים.",
    "insight": "תובנה: ...",
    "companies": [
      {{
        "name": "אלביט מערכות",
        "ticker": "ESLT",
        "direction": "up",
        "analysis": "..."
      }},
      {{
        "name": "ICL Group",
        "ticker": "ICL",
        "direction": "up",
        "analysis": "..."
      }}
    ],
    "watch_levels": "🎯 למעקב: ..."
  }},
  "geopolitical": {{
    "event_color": "🟠",
    "main_event": "תיאור האירוע הגיאופוליטי הדומיננטי ביום, עם פרטים ומספרים ספציפיים.",
    "verified_fact": "✅ עובדה מאומתת: עובדה קונקרטית ומספרית שניתן לאמת.",
    "structural_meaning": "🧭 משמעות מבנית: ההשלכה המבנית ארוכת הטווח על השווקים.",
    "bottlenecks": [
      {{
        "type": "main",
        "title": "שם צוואר הבקבוק הראשי — סחורה + אזור גיאוגרפי",
        "educational": "📘 הסבר לימודי: כיצד הגיאופוליטיקה משפיעה על מנגנון השוק הזה. 2-3 משפטים.",
        "benefiting": [
          {{
            "name": "Frontline",
            "ticker": "FRO",
            "analysis": "ניתוח קצר עם מחיר ומספרים."
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
        "conclusion": "🎯 מסקנה לפעולה: רמת X ← כניסה/הגדלה; רמת Y ← יציאה/צמצום."
      }},
      {{
        "type": "secondary",
        "title": "שם צוואר בקבוק משני (סחורה שונה מהראשון)",
        "educational": "📘 הסבר לימודי: ...",
        "benefiting": [
          {{
            "name": "Freeport-McMoRan",
            "ticker": "FCX",
            "analysis": "..."
          }},
          {{
            "name": "Southern Copper",
            "ticker": "SCCO",
            "analysis": "..."
          }}
        ],
        "at_risk": [],
        "conclusion": "🎯 מסקנה לפעולה: ..."
      }}
    ]
  }}
}}"""

    try:
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        print("  ✅ Gemini: ניתוח נוצר בהצלחה")
        return result
    except json.JSONDecodeError:
        # Try to extract valid JSON from partial response
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
    """Minimal fallback when Gemini is unavailable."""
    return {
        "reading_time": "4",
        "focus_companies_count": "10",
        "tldr": [
            "שוק הסחורות מציג מגמות מעורבות בפתיחת יום המסחר.",
            "נתוני מאקרו ממשיכים לעצב ציפיות ריבית גלובליות.",
            "הבורסה הישראלית נסחרת בסמוך לרמות שיא — מדדים ספציפיים בטבלה.",
        ],
        "us_market": {
            "macro_analysis": "⚪ ניתוח AI לא זמין כרגע. ראה נתוני מחירים בטבלאות.",
            "insight": "",
            "companies": [],
            "watch_levels": "",
        },
        "israel_market": {
            "macro_analysis": "⚪ ניתוח AI לא זמין כרגע.",
            "insight": "",
            "companies": [],
            "watch_levels": "",
        },
        "geopolitical": {
            "event_color": "⚪",
            "main_event": "ניתוח גיאופוליטי לא זמין כרגע.",
            "verified_fact": "",
            "structural_meaning": "",
            "bottlenecks": [],
        },
    }
