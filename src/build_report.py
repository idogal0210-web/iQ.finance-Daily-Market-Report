"""
build_report.py — v4 (Educational & Actionable Layout)
=====================================================
בונה דוח HTML מעוצב, מותאם RTL ולמובייל:
  - כותרת וזמן קריאה
  - 🔥 בקצרה — 3 דברים לדעת היום
  - ⚡ תובנות טקטיות ומטריצת פעולה (Executive Action Playbook)
  - 🌐 תמונת המאקרו הגלובלית + 💡 איך המנגנון עובד?
  - חלק א׳: שוק המניות — ארה"ב וישראל (חברות בפוקוס, קטליזטורים ושורה תחתונה)
  - חלק ב׳: סחורות, אג״ח, גיאופוליטיקה וצווארי בקבוק (עם הסבר לימודי מעמיק)
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
    "card_dark":     "#1f1f1d",
    "row1":          "#2a2a28",
    "row2":          "#242422",
    "text":          "#e8e6e1",
    "muted":         "#a8a29e",
    "dim":           "#7a7670",
    "green":         "#4ade80",
    "green_bg":      "#1a3322",
    "red":           "#f87171",
    "red_bg":        "#381e1e",
    "amber":         "#f59e0b",
    "amber_bg":      "#382914",
    "blue":          "#60a5fa",
    "blue_bg":       "#172738",
    "border":        "#3d3d3a",
}

FONT = "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;"


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
    <td dir="rtl" style="text-align:center;padding:28px 20px 22px;">
      <h1 style="color:{C['accent']};margin:0 0 4px;font-size:23px;
                 letter-spacing:-0.3px;{FONT}">📊 בריף שוק אסטרטגי — iQ.finance</h1>
      <p style="color:{C['muted']};font-size:13px;margin:0 0 12px;{FONT}">{date} · מודיעין שוק ומנוע החלטות</p>
      <span style="display:inline-block;background:{C['accent_dark']};color:{C['accent']};
                   border:1px solid {C['accent_border']};border-radius:20px;
                   padding:5px 16px;font-size:12px;font-weight:bold;{FONT}">
        ⏱ {reading_time} דקות קריאה · {companies_count} מניות בפוקוס
      </span>
    </td>
  </tr>
</table>"""


# ── TL;DR ─────────────────────────────────────────────────────────────────────
def _tldr(points: list[str]) -> str:
    items = "".join(
        f'<p style="margin:0 0 8px;font-size:13.5px;color:{C["text"]};line-height:1.65;{FONT}">'
        f'<strong style="color:{C["accent"]};">{i + 1}.</strong> {pt}</p>'
        for i, pt in enumerate(points[:3])
    )
    return f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{C['bg']};">
  <tr>
    <td dir="rtl" style="padding:14px 20px 6px;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="background:{C['card']};border-right:4px solid {C['accent']};border-radius:8px;">
        <tr>
          <td style="padding:16px 18px;">
            <p style="margin:0 0 10px;color:{C['accent']};font-weight:bold;font-size:14.5px;{FONT}">
              🔥 בקצרה — 3 נקודות מפתח להיום
            </p>
            {items}
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>"""


# ── TACTICAL ACTION PLAYBOOK ───────────────────────────────────────────────────
def _tactical_playbook(tac: dict) -> str:
    if not tac:
        return ""
    
    regime = tac.get("market_regime", "")
    opps = tac.get("key_opportunities", [])
    risks = tac.get("key_risks", [])
    bottom_line = tac.get("action_bottom_line", "")

    opp_html = "".join(
        f'<p style="margin:0 0 6px;font-size:13px;color:{C["text"]};line-height:1.6;{FONT}">'
        f'<span style="color:{C["green"]};font-weight:bold;">🟢 הזדמנות:</span> {o}</p>'
        for o in opps
    )
    risk_html = "".join(
        f'<p style="margin:0 0 6px;font-size:13px;color:{C["text"]};line-height:1.6;{FONT}">'
        f'<span style="color:{C["amber"]};font-weight:bold;">🟠 נקודת סיכון/מעקב:</span> {r}</p>'
        for r in risks
    )

    regime_html = f"""
    <div style="background:{C['accent_dark']};border:1px solid {C['accent_border']};
                border-radius:6px;padding:8px 12px;margin-bottom:12px;">
      <span style="color:{C['accent']};font-weight:bold;font-size:12.5px;{FONT}">
        ⚡ משטר שוק נוכחי:
      </span>
      <span style="color:{C['text']};font-size:13px;{FONT}"> {regime}</span>
    </div>
    """ if regime else ""

    bottom_html = f"""
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:10px;">
      <tr>
        <td style="background:{C['header_bg']};border-right:3px solid {C['green']};border-radius:6px;padding:10px 14px;">
          <p style="margin:0;font-size:13px;color:{C['text']};line-height:1.6;{FONT}">
            <strong style="color:{C['green']};">🎯 שורה תחתונה לפעולה:</strong> {bottom_line}
          </p>
        </td>
      </tr>
    </table>
    """ if bottom_line else ""

    return f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{C['bg']};">
  <tr>
    <td dir="rtl" style="padding:8px 20px 8px;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="background:{C['card']};border:1px solid {C['border']};border-radius:8px;">
        <tr>
          <td style="padding:16px 18px;">
            <p style="margin:0 0 10px;color:{C['text']};font-weight:bold;font-size:15px;{FONT}">
              ⚡ תובנות טקטיות ומטריצת החלטות (Tactical Playbook)
            </p>
            {regime_html}
            {opp_html}
            {risk_html}
            {bottom_html}
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>"""


# ── MACRO CANVAS & EDUCATIONAL CALLOUT ─────────────────────────────────────────
def _macro_canvas_section(macro_canvas: dict, macro_data: dict) -> str:
    if not macro_canvas:
        return ""
    
    title = macro_canvas.get("title", "🌐 בריף מאקרו גלובלי ומנגנוני השוק")
    analysis = macro_canvas.get("analysis", "")
    mechanism = macro_canvas.get("mechanism_explained", "")
    takeaway = macro_canvas.get("takeaway", "")

    # Macro indicators table
    macro_rows = ""
    if macro_data:
        for i, (k, v) in enumerate(macro_data.items()):
            bg = C["row1"] if i % 2 == 0 else C["row2"]
            macro_rows += (
                f'<tr style="background:{bg};">'
                f'<td style="font-weight:bold;color:{C["text"]};padding:8px 10px;{FONT}">{v.get("label","")}</td>'
                f'<td style="color:{C["text"]};padding:8px 10px;{FONT}">{v.get("price","—")} {v.get("unit","")}</td>'
                f'<td style="padding:8px 10px;{FONT}">{_change_span(v.get("change","—"), v.get("direction","flat"))}</td>'
                f'</tr>'
            )

    macro_table = f"""
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:12px 0 10px;border-radius:6px;overflow:hidden;">
      <tr style="background:{C['accent_dark']};">
        <td style="color:{C['accent']};font-weight:bold;padding:7px 10px;font-size:12px;{FONT}">אינדיקטור מאקרו</td>
        <td style="color:{C['accent']};font-weight:bold;padding:7px 10px;font-size:12px;{FONT}">ערך נוכחי</td>
        <td style="color:{C['accent']};font-weight:bold;padding:7px 10px;font-size:12px;{FONT}">שינוי</td>
      </tr>
      {macro_rows}
    </table>
    """ if macro_rows else ""

    edu_html = f"""
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:10px 0 6px;">
      <tr>
        <td style="background:{C['blue_bg']};border-right:3px solid {C['blue']};border-radius:6px;padding:10px 14px;">
          <p style="margin:0;font-size:13px;color:{C['text']};line-height:1.65;{FONT}">
            <strong style="color:{C['blue']};">{mechanism[:22]}</strong> {mechanism[22:] if len(mechanism)>22 else mechanism}
          </p>
        </td>
      </tr>
    </table>
    """ if mechanism else ""

    takeaway_html = f"""
    <p style="margin:8px 0 0;font-size:13px;color:{C['accent']};font-weight:bold;line-height:1.6;{FONT}">
      {takeaway}
    </p>
    """ if takeaway else ""

    return f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{C['bg']};">
  <tr>
    <td dir="rtl" style="padding:10px 20px 6px;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="background:{C['card']};border-radius:8px;">
        <tr>
          <td style="padding:16px 18px;">
            <h3 style="color:{C['accent']};font-size:15px;margin:0 0 8px;{FONT}">{title}</h3>
            {_text_p(analysis)}
            {macro_table}
            {edu_html}
            {takeaway_html}
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
              border-bottom:1px solid #4a3520;margin-top:10px;">
  <tr>
    <td dir="rtl" style="padding:12px 20px;">
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
    <td dir="rtl" style="padding:14px 20px 4px;">
      <h3 style="color:{C['text']};font-size:15px;margin:0 0 6px;{FONT}">{flag} {title}</h3>
      <hr style="border:none;border-top:1px solid #3a3a38;margin:0;">
    </td>
  </tr>
</table>"""


# ── Market section (US or IL) ─────────────────────────────────────────────────
def _market_section(macro: str, insight: str, companies: list, watch: str) -> str:
    # Macro paragraph
    macro_html = f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{C['bg']};">
  <tr>
    <td dir="rtl" style="padding:8px 20px 4px;{FONT}">
      {_text_p(macro)}
      {(_text_p(f'<span style="color:{C["accent"]};font-weight:bold;">💡 תובנת מפתח:</span> {insight}') if insight else "")}
    </td>
  </tr>
</table>"""

    # Company cards
    co_html = ""
    if companies:
        cards = ""
        for c in companies:
            d = c.get("direction", "flat")
            border_color = C["green"] if d == "up" else (C["red"] if d == "down" else C["muted"])
            emoji = "🟢" if d == "up" else ("🔴" if d == "down" else "⚪")
            name = c.get("name", "")
            ticker = c.get("ticker", "")
            body = c.get("catalyst_and_analysis") or c.get("analysis", "")
            takeaway = c.get("actionable_takeaway", "")

            takeaway_str = f'<div style="margin-top:4px;font-size:12.5px;color:{C["accent"]};font-weight:bold;">🎯 לפעולה: {takeaway}</div>' if takeaway else ""

            cards += f"""
            <div style="margin:0 0 10px;padding:10px 14px;background:{C['card_dark']};border-right:3px solid {border_color};border-radius:6px;{FONT}">
              <div style="font-size:13.5px;color:{C['text']};margin-bottom:4px;">
                {emoji} <strong style="color:{C['text']};font-size:14px;">{name}</strong>
                <span style="color:{C['muted']};font-size:12px;">({ticker})</span>
              </div>
              <p style="margin:0;font-size:13px;color:{C['text']};line-height:1.6;">{body}</p>
              {takeaway_str}
            </div>
            """
        co_html = f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{C['bg']};">
  <tr>
    <td dir="rtl" style="padding:4px 20px 4px;">
      <p style="margin:0 0 8px;color:{C['muted']};font-size:12.5px;font-weight:bold;{FONT}">
        חברות בפוקוס וקטליזטורים:
      </p>
      {cards}
    </td>
  </tr>
</table>"""

    # Watch levels box
    watch_html = ""
    if watch:
        watch_html = f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{C['bg']};">
  <tr>
    <td dir="rtl" style="padding:4px 20px 12px;">
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
            f'<td style="font-weight:bold;color:{C["text"]};padding:8px 10px;{FONT}">{v["label"]}</td>'
            f'<td style="color:{C["text"]};padding:8px 10px;{FONT}">{v["price"]}</td>'
            f'<td style="padding:8px 10px;{FONT}">{_change_span(v["change"], v["direction"])}</td>'
            f'</tr>'
        )
    return f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{C['bg']};">
  <tr>
    <td dir="rtl" style="padding:8px 20px 4px;">
      <h4 style="color:{C['accent']};font-size:14px;margin:0 0 6px;{FONT}">{title}</h4>
      <table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-radius:6px;overflow:hidden;">
        <tr style="background:{C['accent_dark']};">
          <td style="color:{C['accent']};font-weight:bold;padding:7px 10px;font-size:12px;{FONT}">סחורה</td>
          <td style="color:{C['accent']};font-weight:bold;padding:7px 10px;font-size:12px;{FONT}">מחיר</td>
          <td style="color:{C['accent']};font-weight:bold;padding:7px 10px;font-size:12px;{FONT}">שינוי</td>
        </tr>
        {rows}
      </table>
    </td>
  </tr>
</table>"""


# ── Geopolitical & Educational Bottlenecks ─────────────────────────────────────
def _geo_section(geo: dict) -> str:
    if not geo:
        return ""
    
    event = geo.get("geopolitical_event") or geo.get("main_event", "")
    edu = geo.get("mechanism_educational") or geo.get("educational", "")
    energy_metals = geo.get("energy_and_metals", "")
    conc = geo.get("conclusion", "")
    benefiting = geo.get("benefiting_companies", [])
    at_risk = geo.get("at_risk_companies", [])

    # Energy & Metals overview
    em_html = f"""
    <div style="margin-bottom:10px;">
      <p style="margin:0;font-size:13px;color:{C['text']};line-height:1.65;{FONT}">
        <strong style="color:{C['accent']};">ניתוח אותות שוק הסחורות:</strong> {energy_metals}
      </p>
    </div>
    """ if energy_metals else ""

    # Main event card
    event_card = f"""
    <div style="background:{C['card_dark']};border-right:3px solid {C['amber']};border-radius:6px;padding:10px 14px;margin-bottom:10px;">
      <p style="margin:0;font-size:13px;color:{C['text']};line-height:1.6;{FONT}">
        <strong style="color:{C['amber']};">🌍 אירוע גיאופוליטי / צוואר בקבוק:</strong> {event}
      </p>
    </div>
    """ if event else ""

    # Educational Mechanism Breakdown
    edu_card = f"""
    <div style="background:{C['blue_bg']};border-right:3px solid {C['blue']};border-radius:6px;padding:10px 14px;margin-bottom:10px;">
      <p style="margin:0;font-size:13px;color:{C['text']};line-height:1.65;{FONT}">
        {edu}
      </p>
    </div>
    """ if edu else ""

    # Benefiting & At Risk Companies
    companies_html = ""
    for c in benefiting:
        companies_html += (
            f'<p style="margin:0 0 6px;font-size:13px;color:{C["text"]};line-height:1.6;{FONT}">'
            f'🟢 <strong style="color:{C["text"]};">{c.get("name","")}</strong> '
            f'<span style="color:{C["muted"]};font-size:12px;">({c.get("ticker","")})</span> '
            f'— {c.get("rationale") or c.get("analysis","")}</p>'
        )
    for c in at_risk:
        companies_html += (
            f'<p style="margin:0 0 6px;font-size:13px;color:{C["text"]};line-height:1.6;{FONT}">'
            f'🔴 <strong style="color:{C["text"]};">{c.get("name","")}</strong> '
            f'<span style="color:{C["muted"]};font-size:12px;">({c.get("ticker","")})</span> '
            f'— {c.get("rationale") or c.get("analysis","")}</p>'
        )

    co_block = f"""
    <div style="margin:10px 0 8px;">
      <p style="margin:0 0 6px;color:{C['muted']};font-size:12.5px;font-weight:bold;{FONT}">
        חברות מרוויחות מול חברות בסיכון:
      </p>
      {companies_html}
    </div>
    """ if companies_html else ""

    # Conclusion
    conc_html = f"""
    <div style="background:{C['accent_dark']};border-right:3px solid {C['accent']};border-radius:6px;padding:10px 14px;margin-top:10px;">
      <p style="margin:0;font-size:13px;color:{C['text']};line-height:1.6;{FONT}">
        {conc}
      </p>
    </div>
    """ if conc else ""

    return f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{C['bg']};">
  <tr>
    <td dir="rtl" style="padding:10px 20px 12px;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="background:{C['card']};border-radius:8px;">
        <tr>
          <td style="padding:16px 18px;">
            <h4 style="color:{C['accent']};font-size:15px;margin:0 0 10px;{FONT}">
              🌍 גיאופוליטיקה, שרשראות אספקה וצווארי בקבוק
            </h4>
            {em_html}
            {event_card}
            {edu_card}
            {co_block}
            {conc_html}
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>"""


# ── Footer ─────────────────────────────────────────────────────────────────────
def _footer(note: str) -> str:
    return f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0"
       style="background:{C['header_bg']};border-top:4px solid {C['accent']};margin-top:14px;">
  <tr>
    <td dir="rtl" style="text-align:center;padding:20px 20px;">
      <p style="font-size:11.5px;color:{C['dim']};margin:0 0 6px;{FONT}">
        מקורות נתונים: FMP API · Yahoo Finance · Gemini AI {note}
      </p>
      <p style="font-size:12px;color:{C['muted']};margin:0;{FONT}">
        ⚠️ הדו״ח מיועד למטרות לימוד ומידע בלבד, ואינו מהווה ייעוץ השקעות או המלצה לפעולה
      </p>
    </td>
  </tr>
</table>"""


# ── Main builder ───────────────────────────────────────────────────────────────
def build_html(analysis: dict, market_data: dict) -> str:
    """Assembles the full HTML report from Gemini analysis + raw market data."""
    date_str = market_data.get("date", "")
    reading_time = analysis.get("reading_time", "7-8")
    co_count = analysis.get("focus_companies_count", "10")
    tldr = analysis.get("tldr", [])
    tac = analysis.get("tactical_takeaways", {})
    macro_canvas = analysis.get("macro_canvas", {})
    us = analysis.get("us_market", {})
    il = analysis.get("israel_market", {})
    geo = analysis.get("commodities_and_geopolitics") or analysis.get("geopolitical", {})
    comms = market_data.get("commodities", {})
    macro_data = market_data.get("macro", {})

    # Commodity groups
    energy = [v for v in comms.values() if v.get("sector") == "energy"]
    metals = [v for v in comms.values() if v.get("sector") == "metals"]
    agri = [v for v in comms.values() if v.get("sector") == "agri"]

    # Footer note
    unverified = [v["label"] for v in comms.values() if not v.get("verified")]
    note = "· נתונים ללא אימות מסומנים ⚪" if unverified else "· כל הנתונים אומתו בהצלחה"

    body = "\n".join([
        _header(date_str, reading_time, co_count),
        _spacer(8),
        _tldr(tldr),
        _spacer(6),
        _tactical_playbook(tac),
        _spacer(6),
        _macro_canvas_section(macro_canvas, macro_data),
        _spacer(8),

        # Part A
        _part_header("א׳", "📈 שוק המניות — ארה״ב וישראל",
                     "ניתוח מאקרו סקטוריאלי, חברות בפוקוס, קטליזטורים ונקודות מעקב."),
        _subsection_header("🇺🇸", "השוק האמריקאי"),
        _market_section(
            us.get("macro_analysis", ""),
            us.get("insight", ""),
            us.get("companies", []),
            us.get("watch_levels", ""),
        ),
        _subsection_header("🇮🇱", "השוק הישראלי"),
        _market_section(
            il.get("macro_analysis", ""),
            il.get("insight", ""),
            il.get("companies", []),
            il.get("watch_levels", ""),
        ),
        _spacer(6),

        # Part B
        _part_header("ב׳", "📦 סחורות, גיאופוליטיקה וצווארי בקבוק",
                     "ניתוח אותות במחירי האנרגיה והמתכות, השפעות סחר ימי והסבר לימודי."),
        _commodity_table("⛽ אנרגיה", energy),
        _commodity_table("🔩 מתכות", metals),
        _commodity_table("🌾 חקלאות ואשלגן", agri),
        _spacer(6),
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

