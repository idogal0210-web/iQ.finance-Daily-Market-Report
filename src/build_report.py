"""
build_report.py — Reference Template Perfect Match
==================================================
בונה דוח HTML מעוצב, מותאם RTL ולמובייל:
  - כותרת וזמן קריאה (דו״ח שוק וסחורות — סקירה)
  - 🔥 בקצרה — 3 דברים לדעת היום
  - חלק א׳: שוק המניות — ארה"ב וישראל
    • 🇺🇸 השוק האמריקאי (מאקרו, תובנה, חברות בפוקוס, 🎯 למעקב)
    • 🇮🇱 השוק הישראלי (מאקרו, תובנה, חברות בפוקוס, 🎯 למעקב)
  - חלק ב׳: סחורות, גיאופוליטיקה וצווארי בקבוק
    • טבלאות: ⛽ אנרגיה, 🔩 מתכות, 🌾 חקלאות ואשלגן
    • 🌍 מגמה גיאופוליטית מתפתחת (אירוע, עובדה מאומתת, משמעות מבנית)
    • ⚠️ צוואר בקבוק ראשי (הסבר לימודי, מרוויחות/בסיכון, מסקנה לפעולה)
    • ⚠️ צוואר בקבוק משני (הסבר לימודי, מרוויחות/בסיכון, מסקנה לפעולה)
"""

from datetime import datetime

# ── Design tokens ─────────────────────────────────────────────────────────────
C = {
    "bg":            "#262624",
    "header_bg":     "#201f1d",
    "accent":        "#D97757",
    "accent_dark":   "#3a2a20",
    "accent_border": "#6b4a3a",
    "card":          "#30302e",
    "row1":          "#2a2a28",
    "row2":          "#242422",
    "text":          "#e8e6e1",
    "muted":         "#a8a29e",
    "dim":           "#7a7670",
    "green":         "#4ade80",
    "red":           "#f87171",
    "amber":         "#f59e0b",
    "blue":          "#60a5fa",
}

FONT = "font-family:Arial,Helvetica,sans-serif;"


# ── Micro helpers ──────────────────────────────────────────────────────────────
def _change_span(change: str, direction: str) -> str:
    if direction == "up":
        return f'<span style="color:{C["green"]};font-weight:bold;">▲ {change}</span>'
    if direction == "down":
        return f'<span style="color:{C["red"]};font-weight:bold;">▼ {change}</span>'
    return f'<span style="color:{C["muted"]};">{change}</span>'


def _spacer(h: int = 10) -> str:
    return f'<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{C["bg"]};"><tr><td style="height:{h}px;"></td></tr></table>'


def _text_p(content: str, extra_style: str = "") -> str:
    if not content:
        return ""
    return (f'<p style="margin:0 0 8px;font-size:13.5px;color:{C["text"]};'
            f'line-height:1.65;{FONT}{extra_style}">{content}</p>')


# ── HEADER ────────────────────────────────────────────────────────────────────
def _header(date: str, reading_time: str, companies_count: str) -> str:
    return f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0"
       style="background:{C['header_bg']};border-bottom:4px solid {C['accent']};">
  <tr>
    <td dir="rtl" style="text-align:center;padding:28px 20px 20px;">
      <h1 style="color:{C['accent']};margin:0 0 4px;font-size:22px;
                 letter-spacing:-0.3px;{FONT}">📊 דו״ח שוק וסחורות — סקירה</h1>
      <p style="color:{C['muted']};font-size:13px;margin:0 0 12px;{FONT}">{date} · iQ.finance</p>
      <span style="display:inline-block;background:{C['accent_dark']};color:{C['accent']};
                   border:1px solid {C['accent_border']};border-radius:20px;
                   padding:5px 16px;font-size:12px;font-weight:bold;{FONT}">
        ⏱ {reading_time} דקות קריאה · {companies_count} חברות בפוקוס
      </span>
    </td>
  </tr>
</table>"""


# ── TL;DR ─────────────────────────────────────────────────────────────────────
def _tldr(points: list[str]) -> str:
    items = "".join(
        f'<p style="margin:0 0 7px;font-size:13.5px;color:{C["text"]};line-height:1.65;{FONT}">'
        f'{i + 1}. {pt}</p>'
        for i, pt in enumerate(points[:3])
    )
    return f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{C['bg']};">
  <tr>
    <td dir="rtl" style="padding:14px 22px 6px;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="background:{C['card']};border-right:4px solid {C['accent']};border-radius:6px;">
        <tr>
          <td style="padding:16px 18px;">
            <p style="margin:0 0 10px;color:{C['accent']};font-weight:bold;font-size:14px;{FONT}">
              🔥 בקצרה — 3 דברים לדעת היום
            </p>
            {items}
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>"""


# ── Part header (א׳ / ב׳) ─────────────────────────────────────────────────────
def _part_header(num: str, title: str, subtitle: str = "") -> str:
    sub_html = (f'<p style="margin:2px 0 0;color:{C["muted"]};font-size:12px;{FONT}">{subtitle}</p>'
                if subtitle else "")
    return f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0"
       style="background:{C['accent_dark']};border-top:3px solid {C['accent']};
              border-bottom:1px solid #4a3520;">
  <tr>
    <td dir="rtl" style="padding:12px 22px;">
      <p style="margin:0;color:{C['muted']};font-size:11px;{FONT}">חלק {num}</p>
      <h2 style="margin:2px 0 0;color:{C['accent']};font-size:16px;{FONT}">{title}</h2>
      {sub_html}
    </td>
  </tr>
</table>"""


# ── Sub-section header (country flag) ────────────────────────────────────────
def _subsection_header(flag: str, title: str) -> str:
    return f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{C['bg']};">
  <tr>
    <td dir="rtl" style="padding:16px 22px 6px;">
      <h3 style="color:{C['text']};font-size:15px;margin:0 0 6px;{FONT}">{flag} {title}</h3>
      <hr style="border:none;border-top:1px solid #3a3a38;margin:0;">
    </td>
  </tr>
</table>"""


# ── Company Card with Recommendation Badge ─────────────────────────────────────
def _render_company_card(c: dict) -> str:
    d = c.get("direction", "flat")
    border_color = C["green"] if d == "up" else (C["red"] if d == "down" else C["muted"])
    emoji = "🔹" if d in ("up", "flat") else "🔻"
    name   = c.get("name", "")
    ticker = c.get("ticker", "")
    rec    = c.get("recommendation") or c.get("stance", "")
    body   = c.get("analysis") or c.get("catalyst_and_analysis", "")
    
    rec_badge = ""
    if rec:
        if any(w in rec for w in ("קנייה", "איסוף", "🟢", "חיובי")):
            rec_badge = f' <span style="display:inline-block;background:#1e3825;color:#4ade80;border:1px solid #2d6a3f;padding:1px 7px;border-radius:10px;font-size:11px;font-weight:bold;margin:0 4px;{FONT}">{rec}</span>'
        elif any(w in rec for w in ("מעקב", "המתנה", "🟡", "ניטרלי")):
            rec_badge = f' <span style="display:inline-block;background:#3b3218;color:#facc15;border:1px solid #715b18;padding:1px 7px;border-radius:10px;font-size:11px;font-weight:bold;margin:0 4px;{FONT}">{rec}</span>'
        elif any(w in rec for w in ("זהירות", "מימוש", "🔴", "שלילי")):
            rec_badge = f' <span style="display:inline-block;background:#3b1e1e;color:#f87171;border:1px solid #712828;padding:1px 7px;border-radius:10px;font-size:11px;font-weight:bold;margin:0 4px;{FONT}">{rec}</span>'
        else:
            rec_badge = f' <span style="display:inline-block;background:#2a2a28;color:#d1d5db;padding:1px 7px;border-radius:10px;font-size:11px;font-weight:bold;margin:0 4px;{FONT}">{rec}</span>'

    return (
        f'<div style="margin:0 0 9px;font-size:13.5px;color:{C["text"]};'
        f'line-height:1.6;padding-right:10px;border-right:3px solid {border_color}40;{FONT}">'
        f'{emoji} <strong style="color:{C["text"]};">{name}</strong>'
        f' <span style="color:{C["muted"]};font-size:12px;font-weight:normal;">{ticker}</span>'
        f'{rec_badge}'
        f' — {body}</div>'
    )


def _render_companies_by_sector(companies: list, sectors: list = None) -> str:
    if sectors and isinstance(sectors, list):
        out = ""
        for sec in sectors:
            s_name = sec.get("sector_name", "")
            s_cos = sec.get("companies", [])
            if not s_cos:
                continue
            out += f'<p style="margin:12px 0 6px;color:{C["accent"]};font-size:12.5px;font-weight:bold;{FONT}">📂 {s_name}</p>'
            for c in s_cos:
                out += _render_company_card(c)
        return out

    if companies:
        grouped = {}
        for c in companies:
            sec = c.get("sector") or "חברות בפוקוס"
            grouped.setdefault(sec, []).append(c)

        out = ""
        for sec_name, c_list in grouped.items():
            if len(grouped) > 1 or sec_name != "חברות בפוקוס":
                out += f'<p style="margin:12px 0 6px;color:{C["accent"]};font-size:12.5px;font-weight:bold;{FONT}">📂 {sec_name}</p>'
            for c in c_list:
                out += _render_company_card(c)
        return out

    return ""


# ── Market section (US or IL) ─────────────────────────────────────────────────
def _market_section(macro: str, insight: str, companies: list, watch: str, sectors: list = None) -> str:
    # Macro paragraph
    macro_html = f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{C['bg']};">
  <tr>
    <td dir="rtl" style="padding:10px 22px 4px;{FONT}">
      {_text_p(macro)}
      {(_text_p(f'<strong style="color:{C["text"]};">תובנה:</strong> {insight}') if insight else "")}
    </td>
  </tr>
</table>"""

    # Company cards grouped by sector
    co_content = _render_companies_by_sector(companies, sectors)
    co_html = ""
    if co_content:
        co_html = f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{C['bg']};">
  <tr>
    <td dir="rtl" style="padding:4px 22px 4px;">
      <p style="margin:0 0 4px;color:{C['muted']};font-size:12px;font-weight:bold;{FONT}">
        חברות בפוקוס — לפי סקטורים:
      </p>
      {co_content}
    </td>
  </tr>
</table>"""

    # Watch levels box
    watch_html = ""
    if watch:
        watch_html = f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{C['bg']};">
  <tr>
    <td dir="rtl" style="padding:4px 22px 14px;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="background:{C['accent_dark']};border-right:3px solid {C['accent']};border-radius:6px;">
        <tr>
          <td style="padding:10px 14px;font-size:13px;color:{C['text']};line-height:1.6;{FONT}">
            {watch}
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>"""

    return macro_html + co_html + watch_html


# ── Commodity table ────────────────────────────────────────────────────────────
def _commodity_table(title: str, items: list) -> str:
    rows = ""
    for i, v in enumerate(items):
        bg = C["row1"] if i % 2 == 0 else C["row2"]
        rows += (
            f'<tr style="background:{bg};">'
            f'<td style="font-weight:bold;color:{C["text"]};padding:9px 10px;{FONT}">{v["label"]}</td>'
            f'<td style="color:{C["text"]};padding:9px 10px;{FONT}">{v["price"]}</td>'
            f'<td style="padding:9px 10px;{FONT}">{_change_span(v["change"], v["direction"])}</td>'
            f'</tr>'
        )
    return f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{C['bg']};">
  <tr>
    <td dir="rtl" style="padding:14px 22px 4px;">
      <h4 style="color:{C['accent']};font-size:14.5px;margin:0 0 8px;{FONT}">{title}</h4>
      <table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-radius:6px;overflow:hidden;">
        <tr style="background:{C['accent_dark']};">
          <td style="color:{C['accent']};font-weight:bold;padding:8px 10px;{FONT}">סחורה</td>
          <td style="color:{C['accent']};font-weight:bold;padding:8px 10px;{FONT}">מחיר</td>
          <td style="color:{C['accent']};font-weight:bold;padding:8px 10px;{FONT}">שינוי</td>
        </tr>
        {rows}
      </table>
    </td>
  </tr>
</table>"""


# ── Geopolitical section ───────────────────────────────────────────────────────
def _geo_section(geo: dict) -> str:
    color  = geo.get("event_color", "🟠")
    event  = geo.get("main_event") or geo.get("geopolitical_event", "")
    fact   = geo.get("verified_fact", "")
    struct = geo.get("structural_meaning", "")

    # Main event card
    event_card = f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{C['bg']};">
  <tr>
    <td dir="rtl" style="padding:14px 22px 6px;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="background:{C['card']};border-right:4px solid {C['amber']};border-radius:6px;">
        <tr>
          <td style="padding:14px 18px;">
            <p style="margin:0 0 8px;color:{C['amber']};font-weight:bold;font-size:14px;{FONT}">
              {color} אירוע: {event}
            </p>
            {"<p style='margin:0 0 6px;font-size:13px;color:" + C["green"] + ";" + FONT + "'>✅ עובדה מאומתת: " + fact + "</p>" if fact else ""}
            {"<p style='margin:0;font-size:13px;color:" + C["text"] + ";line-height:1.6;" + FONT + "'>🧭 משמעות מבנית: " + struct + "</p>" if struct else ""}
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>"""

    # Bottlenecks
    bn_html = ""
    bottlenecks = geo.get("bottlenecks", [])
    
    # If fallback format with single bottleneck
    if not bottlenecks and geo.get("mechanism_educational"):
        bottlenecks = [{
            "type": "main",
            "title": "מצרי הורמוז ובאב אל-מנדב (נפט גולמי)",
            "educational": geo.get("mechanism_educational", ""),
            "benefiting": [{"name": c["name"], "ticker": c["ticker"], "analysis": c.get("rationale", "")} for c in geo.get("benefiting_companies", [])],
            "at_risk": [{"name": c["name"], "ticker": c["ticker"], "analysis": c.get("rationale", "")} for c in geo.get("at_risk_companies", [])],
            "conclusion": geo.get("conclusion", "")
        }]

    for idx, bn in enumerate(bottlenecks):
        bn_type  = "ראשי" if bn.get("type") == "main" else "משני (סחורה פחות מסוקרת)"
        title    = bn.get("title", "")
        edu      = bn.get("educational", "")
        conc     = bn.get("conclusion", "")

        companies_html = ""
        for c in bn.get("benefiting", []):
            companies_html += (
                f'<p style="margin:0 0 8px;font-size:13.5px;color:{C["text"]};line-height:1.6;{FONT}">'
                f'🔹 <strong>{c["name"]}</strong>'
                f' <span style="color:{C["muted"]};font-size:12px;">{c["ticker"]}</span>'
                f' — {c.get("analysis") or c.get("rationale","")}</p>'
            )
        for c in bn.get("at_risk", []):
            companies_html += (
                f'<p style="margin:0 0 8px;font-size:13.5px;color:{C["text"]};line-height:1.6;{FONT}">'
                f'🔻 <strong>{c["name"]}</strong>'
                f' <span style="color:{C["muted"]};font-size:12px;">{c["ticker"]}</span>'
                f' — {c.get("analysis") or c.get("rationale","")}</p>'
            )

        conc_html = ""
        if conc:
            conc_html = (
                f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
                f'<tr><td style="padding:8px 0 0;">'
                f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
                f' style="background:{C["accent_dark"]};border-right:3px solid {C["accent"]};border-radius:6px;">'
                f'<tr><td style="padding:10px 14px;font-size:13px;color:{C["text"]};line-height:1.6;{FONT}">'
                f'{conc}</td></tr></table></td></tr></table>'
            )

        bn_html += f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{C['bg']};">
  <tr>
    <td dir="rtl" style="padding:10px 22px 6px;">
      <p style="margin:0 0 6px;color:{C['accent']};font-weight:bold;font-size:13.5px;{FONT}">
        ⚠️ צוואר בקבוק {bn_type}: {title}
      </p>
      {"<p style='margin:0 0 10px;font-size:13px;color:" + C['muted'] + ";line-height:1.65;" + FONT + "'>📘 הסבר לימודי: " + edu + "</p>" if edu else ""}
      <p style="margin:0 0 6px;color:{C['muted']};font-size:12px;font-weight:bold;{FONT}">
        חברות שעשויות להרוויח / בסיכון:
      </p>
      {companies_html}
      {conc_html}
    </td>
  </tr>
</table>"""

    return event_card + bn_html


# ── Footer ─────────────────────────────────────────────────────────────────────
def _footer(note: str) -> str:
    return f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0"
       style="background:{C['header_bg']};border-top:4px solid {C['accent']};">
  <tr>
    <td dir="rtl" style="text-align:center;padding:18px 20px;">
      <p style="font-size:11px;color:{C['dim']};margin:0 0 6px;{FONT}">
        מקורות נתונים מאומתים מתעדכנים יומית {note}
      </p>
      <p style="font-size:12px;color:{C['muted']};margin:0;{FONT}">
        ⚠️ הדו״ח משמש למטרות לימוד ומידע בלבד, ואינו מהווה ייעוץ השקעות
      </p>
    </td>
  </tr>
</table>"""


# ── Main builder ───────────────────────────────────────────────────────────────
def build_html(analysis: dict, market_data: dict) -> str:
    """Assembles the full HTML report from Gemini analysis + raw market data."""
    date_str        = market_data.get("date", "")
    reading_time    = analysis.get("reading_time", "7")
    co_count        = analysis.get("focus_companies_count", "10")
    tldr            = analysis.get("tldr", [])
    us              = analysis.get("us_market", {})
    il              = analysis.get("israel_market", {})
    geo             = analysis.get("geopolitical") or analysis.get("commodities_and_geopolitics", {})
    comms           = market_data.get("commodities", {})

    # Commodity groups
    energy = [v for v in comms.values() if v.get("sector") == "energy"]
    metals = [v for v in comms.values() if v.get("sector") == "metals"]
    agri   = [v for v in comms.values() if v.get("sector") == "agri"]

    # Footer note
    unverified = [v["label"] for v in comms.values() if not v.get("verified")]
    note = "· נתונים שלא עברו אימות מסומנים ⚪" if unverified else "· כל הנתונים אומתו בהצלחה"

    body = "\n".join([
        _header(date_str, reading_time, co_count),
        _spacer(10),
        _tldr(tldr),

        # Part A
        _part_header("א׳", "📈 שוק המניות — ארה״ב וישראל",
                     "השפעות מאקרו על חברות מפתח באנרגיה, היי-טק ו-AI, ביטחון, רפואה ונדל״ן."),
        _subsection_header("🇺🇸", "השוק האמריקאי"),
        _market_section(
            us.get("macro_analysis", ""),
            us.get("insight", ""),
            us.get("companies", []),
            us.get("watch_levels", ""),
            us.get("sectors"),
        ),
        _subsection_header("🇮🇱", "השוק הישראלי"),
        _market_section(
            il.get("macro_analysis", ""),
            il.get("insight", ""),
            il.get("companies", []),
            il.get("watch_levels", ""),
            il.get("sectors"),
        ),
        _spacer(6),

        # Part B
        _part_header("ב׳", "📦 סחורות, גיאופוליטיקה וצווארי בקבוק"),
        _commodity_table("⛽ אנרגיה", energy),
        _commodity_table("🔩 מתכות", metals),
        _commodity_table("🌾 חקלאות ואשלגן", agri),
        _spacer(6),

        # Geo header
        """<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#262624;">
  <tr><td dir="rtl" style="padding:14px 22px 4px;">
    <h4 style="color:#D97757;font-size:14.5px;margin:0;font-family:Arial,sans-serif;">
      🌍 מגמה גיאופוליטית מתפתחת
    </h4>
  </td></tr>
</table>""",

        _geo_section(geo),
        _spacer(10),
        _footer(note),
    ])

    return f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>דו״ח שוק וסחורות — {date_str}</title>
</head>
<body style="margin:0;padding:0;background:{C['bg']};">
{body}
</body>
</html>"""


def save_report(html: str, output_dir: str = ".") -> str:
    filename = f"daily_report_{datetime.now().strftime('%Y-%m-%d')}.html"
    path = f"{output_dir}/{filename}"
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✅ Saved: {path}")
    return path

