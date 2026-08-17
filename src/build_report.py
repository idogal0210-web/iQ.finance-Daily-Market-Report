"""
build_report.py
===============
בונה את קובץ ה-HTML הסופי מהנתונים שנאספו.
"""

from datetime import datetime


# ─── Color helpers ────────────────────────────────────────────────────────────
def _change_html(change_str: str, direction: str) -> str:
    """מחזיר span מעוצב בהתאם לכיוון המחיר."""
    if direction == "up":
        return f'<span style="color:#4ade80; font-weight:bold;">▲ {change_str}</span>'
    elif direction == "down":
        return f'<span style="color:#f87171; font-weight:bold;">▼ {change_str}</span>'
    else:
        return f'<span style="color:#a8a29e;">{change_str}</span>'


def _row(label: str, price: str, change_str: str, direction: str, bg: str) -> str:
    change_html = _change_html(change_str, direction)
    return f"""
          <tr style="background-color:{bg};">
            <td style="font-weight:bold; color:#e8e6e1; padding:9px 10px;">{label}</td>
            <td style="color:#e8e6e1; padding:9px 10px;">{price}</td>
            <td style="padding:9px 10px;">{change_html}</td>
          </tr>"""


def _section(title: str, rows_html: str) -> str:
    return f"""
  <!-- SECTION: {title} -->
  <table width="100%" cellpadding="0" cellspacing="0" border="0"
         style="background-color:#262624;">
    <tr>
      <td dir="rtl" style="padding:14px 22px 4px;">
        <h4 style="color:#D97757; font-size:14.5px; margin:0 0 8px;">{title}</h4>
        <table width="100%" cellpadding="0" cellspacing="0" border="0"
               style="font-size:13.5px; border-radius:6px; overflow:hidden;">
          <tr style="background-color:#3a2a20; border-bottom:2px solid #D97757;">
            <td style="color:#D97757; font-weight:bold; padding:8px 10px;">סחורה</td>
            <td style="color:#D97757; font-weight:bold; padding:8px 10px;">מחיר</td>
            <td style="color:#D97757; font-weight:bold; padding:8px 10px;">שינוי</td>
          </tr>
          {rows_html}
        </table>
      </td>
    </tr>
  </table>"""


# ─── Main builder ─────────────────────────────────────────────────────────────
def build_html(data: dict) -> str:
    """
    מקבל את ה-dict מ-collect_all_data() ומחזיר מחרוזת HTML מלאה.
    """
    date_str   = data["date"]
    tldr       = data["tldr"]
    comms      = data["commodities"]

    # ─ TL;DR lines
    tldr_1 = tldr[0] if len(tldr) > 0 else ""
    tldr_2 = tldr[1] if len(tldr) > 1 else ""
    tldr_3 = tldr[2] if len(tldr) > 2 else ""

    # ─ Build commodity rows by sector
    def rows_for_sector(sector: str) -> str:
        items = [(k, v) for k, v in comms.items() if v["sector"] == sector]
        html = ""
        for i, (key, v) in enumerate(items):
            bg = "#2a2a28" if i % 2 == 0 else "#242422"
            html += _row(v["label"], v["price"], v["change"], v["direction"], bg)
        return html

    energy_rows = rows_for_sector("energy")
    metals_rows = rows_for_sector("metals")
    agri_rows   = rows_for_sector("agri")

    energy_section = _section("⛽ אנרגיה", energy_rows)
    metals_section = _section("🥇 מתכות", metals_rows)
    agri_section   = _section("🌾 חקלאות ואשלגן", agri_rows)

    # ─ Unverified note
    unverified = [v["label"] for v in comms.values() if v["price"] == "⚪ לא אומת"]
    if unverified:
        unverified_note = "· נתונים שלא עברו אימות כפול מסומנים ⚪"
    else:
        unverified_note = "· כל הנתונים אומתו בהצלחה"

    html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>דו״ח שוק וסחורות — {date_str}</title>
</head>
<body style="margin:0; padding:0; background-color:#262624; font-family: Arial, sans-serif;">

  <!-- HEADER -->
  <table width="100%" cellpadding="0" cellspacing="0" border="0"
         style="background-color:#201f1d; border-bottom:4px solid #D97757;">
    <tr>
      <td dir="rtl" style="text-align:center; padding:28px 20px 18px;">
        <h1 style="color:#D97757; margin:0 0 4px; font-size:22px; letter-spacing:-0.3px;">
          📊 דו״ח שוק וסחורות
        </h1>
        <p style="color:#a8a29e; font-size:13px; margin:0 0 12px;">{date_str} · iQ.finance</p>
        <span style="display:inline-block; background-color:#3a2a20; color:#D97757;
                     border:1px solid #6b4a3a; border-radius:20px;
                     padding:5px 16px; font-size:12px; font-weight:bold;">
          ⏱ כ-4 דקות קריאה · סחורות עיקריות
        </span>
      </td>
    </tr>
  </table>

  <!-- DIVIDER -->
  <table width="100%" cellpadding="0" cellspacing="0" border="0"
         style="background-color:#262624;">
    <tr><td style="height:12px;"></td></tr>
  </table>

  <!-- TL;DR BOX -->
  <table width="100%" cellpadding="0" cellspacing="0" border="0"
         style="background-color:#262624;">
    <tr>
      <td dir="rtl" style="padding:6px 22px 10px;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0"
               style="background-color:#30302e; border-right:4px solid #D97757;
                      border-radius:6px;">
          <tr>
            <td style="padding:16px 18px;">
              <p style="margin:0 0 10px; color:#D97757; font-weight:bold; font-size:14px;">
                🔥 בקצרה — 3 דברים לדעת היום
              </p>
              <p style="margin:0 0 6px; font-size:13.5px; color:#e8e6e1; line-height:1.55;">
                1. {tldr_1}
              </p>
              <p style="margin:0 0 6px; font-size:13.5px; color:#e8e6e1; line-height:1.55;">
                2. {tldr_2}
              </p>
              <p style="margin:0; font-size:13.5px; color:#e8e6e1; line-height:1.55;">
                3. {tldr_3}
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>

  <!-- COMMODITY SECTIONS -->
  {energy_section}
  {metals_section}
  {agri_section}

  <!-- SPACER -->
  <table width="100%" cellpadding="0" cellspacing="0" border="0"
         style="background-color:#262624;">
    <tr><td style="height:14px;"></td></tr>
  </table>

  <!-- FOOTER -->
  <table width="100%" cellpadding="0" cellspacing="0" border="0"
         style="background-color:#201f1d; border-top:4px solid #D97757;">
    <tr>
      <td dir="rtl" style="text-align:center; padding:18px 20px;">
        <p style="font-size:11px; color:#7a7670; margin:0 0 6px;">
          מקורות נתונים מתעדכנים יומית {unverified_note}
        </p>
        <p style="font-size:12px; color:#a8a29e; margin:0;">
          ⚠️ הדו״ח משמש למטרות לימוד ומידע בלבד, ואינו מהווה ייעוץ השקעות
        </p>
      </td>
    </tr>
  </table>

</body>
</html>"""

    return html


def save_report(html: str, output_dir: str = ".") -> str:
    filename = f"daily_report_{datetime.now().strftime('%Y-%m-%d')}.html"
    path = f"{output_dir}/{filename}"
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Report saved: {path}")
    return path


if __name__ == "__main__":
    # בדיקה עם נתוני דמה
    dummy = {
        "date": "17/08/2026",
        "tldr": [
            "מחירי הנפט עולים בשל מתיחות גאופוליטית במפרץ הפרסי.",
            "הזהב שומר על יציבות בצל חשש מהאטה כלכלית גלובלית.",
            "מניות החקלאות בלחץ לאחר דוחות יבול מאכזבים מאירופה.",
        ],
        "commodities": {
            "wti":     {"label": "WTI Crude",    "price": "78.40",   "change": "+2.3%", "direction": "up",   "sector": "energy"},
            "brent":   {"label": "Brent Crude",   "price": "82.10",   "change": "-0.5%", "direction": "down", "sector": "energy"},
            "nat_gas": {"label": "Natural Gas",   "price": "3.45",    "change": "+1.1%", "direction": "up",   "sector": "energy"},
            "gold":    {"label": "Gold",          "price": "2,350.20","change": "+1.1%", "direction": "up",   "sector": "metals"},
            "nickel":  {"label": "Nickel",        "price": "⚪ לא אומת","change": "—",  "direction": "flat", "sector": "metals"},
            "wheat":   {"label": "Wheat",         "price": "560.00",  "change": "+0.8%", "direction": "up",   "sector": "agri"},
            "potash":  {"label": "ICL (אשלגן)",  "price": "4.32",    "change": "-0.2%", "direction": "down", "sector": "agri"},
        }
    }
    html = build_html(dummy)
    save_report(html, "/tmp")
    print("Preview saved to /tmp")
