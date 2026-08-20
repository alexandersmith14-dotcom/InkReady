"""Generate a self-contained HTML dashboard from the formulation/ fetcher
state files and the commerce/ checklist.

    python dashboard.py            # writes dashboard.html

No server, no network calls — regenerate after running the fetchers. Brand
mimics thesolidink.com (see assets/brand.md): black nav, off-white body,
orange for flagged/changed items, Abel for display type.
"""

import json
import os
import re
from datetime import datetime, timezone
from html import escape as hesc

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(ROOT, "dashboard.html")

ECHA_STATE = os.path.join(ROOT, "formulation", "echa_state.json")
ECHA_REPORT = os.path.join(ROOT, "formulation", "echa_report.json")
PROP65_STATE = os.path.join(ROOT, "formulation", "prop65_state.json")
PROP65_REPORT = os.path.join(ROOT, "formulation", "prop65_report.json")
MOCRA_STATE = os.path.join(ROOT, "formulation", "mocra_state.json")
MOCRA_REPORT = os.path.join(ROOT, "formulation", "mocra_report.json")
UK_REACH_STATE = os.path.join(ROOT, "formulation", "uk_reach_state.json")
UK_REACH_REPORT = os.path.join(ROOT, "formulation", "uk_reach_report.json")
CANADA_STATE = os.path.join(ROOT, "formulation", "canada_state.json")
CANADA_REPORT = os.path.join(ROOT, "formulation", "canada_report.json")
AUSTRALIA_STATE = os.path.join(ROOT, "formulation", "australia_state.json")
AUSTRALIA_REPORT = os.path.join(ROOT, "formulation", "australia_report.json")
BRAZIL_STATE = os.path.join(ROOT, "formulation", "brazil_state.json")
BRAZIL_REPORT = os.path.join(ROOT, "formulation", "brazil_report.json")
KOREA_STATE = os.path.join(ROOT, "formulation", "korea_state.json")
KOREA_REPORT = os.path.join(ROOT, "formulation", "korea_report.json")
CHECKLIST_PATH = os.path.join(ROOT, "commerce", "checklist.md")

CHECK_ITEM = re.compile(r"^-\s*\[([ xX])\]\s*(.+)$")
BOLD_DASH = re.compile(r"^\*\*(.+?)\*\*\s*(?:—|--|-)\s*(.*)$")


def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def parse_checklist(path):
    """Sections of {title, items: [{title, desc, checked}], notes: [str]}."""
    if not os.path.exists(path):
        return []
    sections = []
    current = None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("## "):
            current = {"title": line[3:].strip(), "items": [], "notes": []}
            sections.append(current)
            continue
        if current is None:
            continue
        m = CHECK_ITEM.match(line.strip())
        if m:
            checked = m.group(1).lower() == "x"
            body = m.group(2)
            bm = BOLD_DASH.match(body)
            if bm:
                current["items"].append({"title": bm.group(1), "desc": bm.group(2), "checked": checked})
            else:
                current["items"].append({"title": body, "desc": "", "checked": checked})
            continue
        stripped = line.strip()
        if stripped.startswith("- "):
            current["notes"].append(stripped[2:])
    return sections


def echa_card():
    state = load_json(ECHA_STATE) or {}
    report = load_json(ECHA_REPORT) or {}
    changes = report.get("changes", [])
    rows = []
    for celex, rec in state.items():
        flagged = any(c["celex"] == celex for c in changes)
        rows.append(f"""
        <div class="doc-row{' flagged' if flagged else ''}">
          <div class="doc-title">{hesc(rec['title'])}</div>
          <div class="doc-meta">CELEX {hesc(celex)} &middot; checked {hesc(rec['checked_at'])}
            {'&middot; <span class="flag">CHANGED — review</span>' if flagged else ''}</div>
        </div>""")
    return card("ECHA REACH — Annex XVII Entry 75", "EU &middot; formulation restriction",
                "".join(rows) or '<p class="empty">No data yet — run formulation/echa_fetcher.py</p>')


def prop65_card():
    state = load_json(PROP65_STATE) or {}
    report = load_json(PROP65_REPORT) or {}
    added, removed = report.get("added", []), report.get("removed", [])
    body = f'<p class="stat">{len(state)} chemicals tracked</p>'
    if added or removed:
        body += '<div class="changes">'
        for r in added:
            body += (f'<div class="change-row added">+ {hesc(r["chemical"])} '
                      f'(CAS {hesc(r.get("cas_no") or "—")}, listed {hesc(r.get("date_listed") or "—")})</div>')
        for r in removed:
            body += f'<div class="change-row removed">&minus; {hesc(r["chemical"])} (CAS {hesc(r.get("cas_no") or "—")})</div>'
        body += "</div>"
    else:
        checked = report.get("checked_at", "—")
        body += f'<p class="empty">No changes since last check ({hesc(checked)})</p>'
    return card("California Prop 65", "US (state) &middot; formulation restriction", body)


def mocra_card():
    state = load_json(MOCRA_STATE) or {}
    report = load_json(MOCRA_REPORT) or {}
    new_items = report.get("new_items", [])
    items = sorted(state.values(), key=lambda x: x.get("date", ""), reverse=True)[:10]
    body = f'<p class="stat">{len(state)} documents tracked, {len(new_items)} new since last check</p>'
    body += '<div class="doc-list">'
    for i in items:
        flagged = i["document_number"] in {n["document_number"] for n in new_items}
        url = hesc(i.get("url", ""))
        body += f"""
        <div class="doc-row{' flagged' if flagged else ''}">
          <a class="doc-title" href="{url}" target="_blank" rel="noopener">{hesc(i['title'])}</a>
          <div class="doc-meta">{hesc(i.get('date', ''))} &middot; {hesc(i.get('type', ''))}
            {'&middot; <span class="flag">NEW</span>' if flagged else ''}</div>
        </div>"""
    body += "</div>"
    return card("MOCRA / FDA guidance", "US &middot; formulation + registration thread", body)


def uk_reach_card():
    state = load_json(UK_REACH_STATE) or {}
    report = load_json(UK_REACH_REPORT) or {}
    changed = report.get("hse_status_changed", False)
    new_uksi = report.get("new_uksi", [])
    known = state.get("known_uksi", {})

    body = f"""<p class="stat">No restriction currently in force — HSE's 2023 recommendation is
      still awaiting a Defra ministerial decision. Do not assume this mirrors the EU restriction.</p>"""
    if changed:
        body += '<p class="change-row added">HSE status page changed since last check — review for a possible decision.</p>'
    else:
        checked = state.get("hse_checked_at", "—")
        body += f'<p class="empty">HSE status page unchanged (checked {hesc(checked)})</p>'

    body += f'<p class="stat">{len(known)} REACH-titled UK SIs tracked, {len(new_uksi)} new since last check</p>'
    if new_uksi:
        body += '<div class="doc-list">'
        for i in new_uksi:
            flag = ' <span class="flag">MENTIONS TATTOO</span>' if i.get("mentions_tattoo") else ""
            body += f'<div class="doc-row flagged"><div class="doc-title">{hesc(i["title"])}</div>{flag}</div>'
        body += "</div>"
    return card("UK REACH — tattoo ink restriction status", "UK &middot; NOT in force, watch only", body)


def canada_card():
    state = load_json(CANADA_STATE) or {}
    report = load_json(CANADA_REPORT) or {}
    new_items = report.get("new_items", [])
    total_scanned = report.get("total_recalls_scanned")

    body = ('<p class="stat">Cosmetic Ingredient Hotlist (the substance restriction list) is NOT '
            'machine-accessible — canada.ca blocks automated access. Documented gap, not tracked here.</p>')
    body += f'<p class="stat">{len(state)} tattoo-related recalls tracked'
    if total_scanned:
        body += f' (of {total_scanned:,} recalls scanned)'
    body += f', {len(new_items)} new since last check</p>'

    items = sorted(state.values(), key=lambda x: x.get("last_updated", ""), reverse=True)
    if items:
        body += '<div class="doc-list">'
        for i in items:
            flagged = i["nid"] in {n["nid"] for n in new_items}
            url = hesc(i.get("url", ""))
            body += f"""
            <div class="doc-row{' flagged' if flagged else ''}">
              <a class="doc-title" href="{url}" target="_blank" rel="noopener">{hesc(i['title'])}</a>
              <div class="doc-meta">{hesc(i.get('last_updated', ''))}
                {'&middot; <span class="flag">NEW</span>' if flagged else ''}</div>
            </div>"""
        body += "</div>"
    return card("Canada — Health Canada recalls", "Canada &middot; recall/enforcement radar", body)


def australia_card():
    state = load_json(AUSTRALIA_STATE)
    report = load_json(AUSTRALIA_REPORT) or {}
    state = state if state is not None else {}
    new_items = report.get("new_items", [])
    total_window = report.get("total_recalls_in_window")

    body = ('<p class="stat">No binding federal restriction list exists — Australia relies on '
            'voluntary compliance. AICIS, Queensland Health, and Queensland legislation sites are '
            'all unreachable; documented gaps, not tracked here.</p>')
    body += f'<p class="stat">{len(state)} tattoo-related recalls tracked'
    if total_window:
        body += f' (of {total_window} in feed window)'
    body += f', {len(new_items)} new since last check</p>'

    items = sorted(state.values(), key=lambda x: x.get("pub_date", ""), reverse=True)
    if items:
        body += '<div class="doc-list">'
        for i in items:
            flagged = i["guid"] in {n["guid"] for n in new_items}
            url = hesc(i.get("url", ""))
            body += f"""
            <div class="doc-row{' flagged' if flagged else ''}">
              <a class="doc-title" href="{url}" target="_blank" rel="noopener">{hesc(i['title'])}</a>
              <div class="doc-meta">{hesc(i.get('pub_date', ''))}
                {'&middot; <span class="flag">NEW</span>' if flagged else ''}</div>
            </div>"""
        body += "</div>"
    else:
        body += '<p class="empty">No tattoo-related recalls found yet — watching for the first one.</p>'
    return card("Australia — Product Safety recalls", "Australia &middot; recall/enforcement radar", body)


def brazil_card():
    state = load_json(BRAZIL_STATE)
    report = load_json(BRAZIL_REPORT) or {}
    state = state if state is not None else {}
    new_items = report.get("new_items", [])

    body = ('<p class="stat">RDC 55/2008 (in force since 2010) requires individual ANVISA '
            'registration for tattoo pigments — a registration regime, not a substance '
            'restriction list. ANVISA\'s registry/legal-text hosts are unreachable; tracked via '
            'Diário Oficial search instead.</p>')
    body += f'<p class="stat">{len(state)} ANVISA resolutions tracked, {len(new_items)} new since last check</p>'

    items = sorted(state.values(), key=lambda x: x.get("pub_date", ""), reverse=True)
    if items:
        body += '<div class="doc-list">'
        for i in items:
            flagged = i["class_pk"] in {n["class_pk"] for n in new_items}
            url = hesc(i.get("url", ""))
            body += f"""
            <div class="doc-row{' flagged' if flagged else ''}">
              <a class="doc-title" href="{url}" target="_blank" rel="noopener">{hesc(i['title'])}</a>
              <div class="doc-meta">{hesc(i.get('pub_date', ''))}
                {'&middot; <span class="flag">NEW</span>' if flagged else ''}</div>
            </div>"""
        body += "</div>"
    return card("Brazil — ANVISA (via Diário Oficial)", "Brazil &middot; registration regime", body)


def korea_card():
    state = load_json(KOREA_STATE)
    report = load_json(KOREA_REPORT) or {}
    changed = report.get("changed", False)

    body = ('<p class="stat">Tattooist Act (Law No. 21070, promulgated 2025-10-28) legalizes and '
            'licenses non-medical tattooists. Not a substance restriction list, and not yet in '
            'force — takes effect 2027-10-29.</p>')
    if changed:
        body += '<p class="change-row added">Law page changed since last check — review for an amendment or the in-force transition.</p>'
    elif state:
        body += f'<p class="empty">Unchanged since {hesc(state.get("checked_at", "—"))}</p>'
    else:
        body += '<p class="empty">No data yet — run formulation/korea_fetcher.py</p>'
    return card("South Korea — Tattooist Act", "Korea &middot; passed, not yet in force", body)


def card(title, subtitle, body_html):
    return f"""
    <section class="card">
      <h3>{hesc(title)}</h3>
      <div class="subtitle">{subtitle}</div>
      {body_html}
    </section>"""


def commerce_section():
    sections = parse_checklist(CHECKLIST_PATH)
    out = []
    for s in sections:
        if s["title"].lower() == "notes":
            notes = "".join(f"<li>{hesc(n)}</li>" for n in s["notes"])
            out.append(f'<div class="commerce-notes"><h4>Notes</h4><ul>{notes}</ul></div>')
            continue
        items = "".join(f"""
          <label class="checklist-item">
            <input type="checkbox" {"checked" if it["checked"] else ""} disabled>
            <span><strong>{hesc(it['title'])}</strong> — {hesc(it['desc'])}</span>
          </label>""" for it in s["items"])
        out.append(f'<div class="commerce-group"><h4>{hesc(s["title"])}</h4>{items}</div>')
    return "".join(out)


PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>InkReady</title>
<link href="https://fonts.googleapis.com/css2?family=Abel&display=swap" rel="stylesheet">
<style>
  :root {{
    --black: #000000;
    --offwhite: #f4f4f4;
    --white: #ffffff;
    --orange: #ff6700;
    --border: #d8d8d8;
  }}
  * {{ box-sizing: border-box; }}
  html {{ overflow-x: hidden; }}
  body {{
    margin: 0;
    background: var(--offwhite);
    color: #1a1a1a;
    font-family: Abel, Oswald, 'Bebas Neue', sans-serif;
    overflow-x: hidden;
  }}
  header {{
    background: var(--black);
    color: var(--white);
    padding: 28px 32px;
  }}
  header .brand {{
    font-size: 32px;
    letter-spacing: 1px;
    text-transform: uppercase;
  }}
  header .tagline {{
    color: #b8b8b8;
    margin-top: 4px;
    font-size: 15px;
  }}
  main {{
    max-width: 1100px;
    margin: 0 auto;
    padding: 32px;
  }}
  h2 {{
    text-transform: uppercase;
    letter-spacing: 1px;
    border-bottom: 3px solid var(--orange);
    padding-bottom: 8px;
    margin-top: 40px;
  }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 20px;
    margin-top: 20px;
  }}
  .card {{
    background: var(--white);
    border: 1px solid var(--border);
    padding: 20px;
  }}
  .card h3 {{
    margin: 0 0 4px 0;
    text-transform: uppercase;
  }}
  .subtitle {{
    color: #777;
    font-size: 13px;
    margin-bottom: 14px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .stat {{
    font-size: 15px;
    margin: 0 0 10px 0;
  }}
  .empty {{
    color: #999;
    font-style: italic;
  }}
  .doc-row {{
    padding: 8px 0;
    border-top: 1px solid var(--border);
  }}
  .doc-row:first-child {{ border-top: none; }}
  .doc-row.flagged {{
    background: #fff3ea;
    padding-left: 8px;
    border-left: 3px solid var(--orange);
  }}
  .doc-title {{
    font-weight: bold;
    color: inherit;
    text-decoration: none;
    display: block;
    word-break: break-word;
  }}
  a.doc-title:hover {{ color: var(--orange); }}
  .doc-meta {{
    font-size: 12px;
    color: #777;
  }}
  .flag {{
    color: var(--orange);
    font-weight: bold;
  }}
  .change-row {{
    font-size: 13px;
    padding: 4px 0;
  }}
  .change-row.added {{ color: #2a7a2a; }}
  .change-row.removed {{ color: #b02a2a; }}
  .commerce-group {{
    background: var(--white);
    border: 1px solid var(--border);
    padding: 16px 20px;
    margin-top: 16px;
  }}
  .commerce-group h4 {{
    margin-top: 0;
    text-transform: uppercase;
    color: var(--orange);
    font-size: 14px;
    letter-spacing: 0.5px;
  }}
  .checklist-item {{
    display: flex;
    gap: 10px;
    align-items: flex-start;
    padding: 6px 0;
    font-size: 14px;
  }}
  .commerce-notes {{
    background: var(--black);
    color: var(--white);
    padding: 16px 20px;
    margin-top: 16px;
  }}
  .commerce-notes h4 {{
    margin-top: 0;
    color: var(--orange);
    text-transform: uppercase;
    font-size: 14px;
  }}
  .commerce-notes ul {{
    margin: 8px 0 0 0;
    padding-left: 20px;
    font-size: 14px;
    color: #ddd;
  }}
  footer {{
    text-align: center;
    color: #999;
    font-size: 12px;
    padding: 32px;
  }}

  @media (max-width: 640px) {{
    header {{ padding: 20px 16px; }}
    header .brand {{ font-size: 24px; }}
    header .tagline {{ font-size: 13px; }}
    main {{ padding: 16px; }}
    h2 {{ font-size: 18px; margin-top: 28px; }}
    .grid {{ grid-template-columns: 1fr; gap: 14px; }}
    .card, .commerce-group, .commerce-notes {{ padding: 14px; }}
    .checklist-item {{ font-size: 13px; }}
    .doc-title {{ font-size: 14px; }}
  }}
</style>
</head>
<body>
<header>
  <div class="brand">InkReady</div>
  <div class="tagline">Tattoo ink regulatory compliance — formulation &amp; sale, EU + US + global. Updated {generated_at}.</div>
</header>
<main>
  <h2>Formulation — what's allowed in the ink</h2>
  <div class="grid">
    {echa_card}
    {prop65_card}
    {mocra_card}
    {uk_reach_card}
    {canada_card}
    {australia_card}
    {brazil_card}
    {korea_card}
  </div>

  <h2>Commerce — rules on selling it</h2>
  {commerce}
</main>
<footer>InkReady &middot; internal use &middot; github.com/alexandersmith14-dotcom/InkReady</footer>
</body>
</html>
"""


def main():
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    page = PAGE_TEMPLATE.format(
        generated_at=generated_at,
        echa_card=echa_card(),
        prop65_card=prop65_card(),
        mocra_card=mocra_card(),
        uk_reach_card=uk_reach_card(),
        canada_card=canada_card(),
        australia_card=australia_card(),
        brazil_card=brazil_card(),
        korea_card=korea_card(),
        commerce=commerce_section(),
    )
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
