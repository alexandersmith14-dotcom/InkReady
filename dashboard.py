"""Generate a self-contained HTML dashboard from the formulation/ fetcher
state files and the commerce/ checklist.

    python dashboard.py            # writes dashboard.html and index.html

No server, no network calls — regenerate after running the fetchers. Brand
mimics thesolidink.com (see assets/brand.md): black nav, off-white body,
orange for flagged/changed items, Abel for display type.

Includes an interactive "Browse by country" section: a clickable world map
(assets/world-map.svg, CC BY-SA 3.0) plus a synced dropdown. Countries with
a dedicated tracker (EU bloc, US, UK, Canada, Australia, NZ, Brazil, Korea,
Japan, China) show their existing card content in a side panel; every other
country falls back to a generic message cross-referenced against the global
recalls feed by country name.
"""

import json
import os
import re
from datetime import datetime, timezone
from html import escape as hesc

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(ROOT, "dashboard.html")
# GitHub Pages serves index.html at the site root — write both so the repo's
# own dashboard.html link keeps working and the Pages URL resolves directly.
INDEX_PATH = os.path.join(ROOT, "index.html")

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
GLOBAL_RECALLS_STATE = os.path.join(ROOT, "formulation", "global_recalls_state.json")
GLOBAL_RECALLS_REPORT = os.path.join(ROOT, "formulation", "global_recalls_report.json")
NZ_STATE = os.path.join(ROOT, "formulation", "newzealand_state.json")
NZ_REPORT = os.path.join(ROOT, "formulation", "newzealand_report.json")
CHILE_STATE = os.path.join(ROOT, "formulation", "chile_state.json")
CHILE_REPORT = os.path.join(ROOT, "formulation", "chile_report.json")
CHECKLIST_PATH = os.path.join(ROOT, "commerce", "checklist.md")

CLP_STATE = os.path.join(ROOT, "commerce", "clp_state.json")
CLP_REPORT = os.path.join(ROOT, "commerce", "clp_report.json")
CONSUMER_RIGHTS_STATE = os.path.join(ROOT, "commerce", "consumer_rights_state.json")
CONSUMER_RIGHTS_REPORT = os.path.join(ROOT, "commerce", "consumer_rights_report.json")
PACKAGING_WASTE_STATE = os.path.join(ROOT, "commerce", "packaging_waste_state.json")
PACKAGING_WASTE_REPORT = os.path.join(ROOT, "commerce", "packaging_waste_report.json")
HAZMAT_STATE = os.path.join(ROOT, "commerce", "hazmat_state.json")
HAZMAT_REPORT = os.path.join(ROOT, "commerce", "hazmat_report.json")
CUSTOMS_STATE = os.path.join(ROOT, "commerce", "customs_state.json")
CUSTOMS_REPORT = os.path.join(ROOT, "commerce", "customs_report.json")

CHECK_ITEM = re.compile(r"^-\s*\[([ xX])\]\s*(.+)$")
# Optional "(aside)" between the bold title and the dash — e.g.
# "**Hazmat classification** (DOT/IATA/IMDG) — some pigments...". Without
# the optional group, those three checklist items silently fell through to
# the plain-text branch below and rendered as literal "**Title**" asterisks
# instead of bold — found by eyeballing the live site's rendered text.
BOLD_DASH = re.compile(r"^\*\*(.+?)\*\*(\s*\([^)]*\))?\s*(?:—|--|-)\s*(.*)$")

WORLD_MAP_SVG_PATH = os.path.join(ROOT, "assets", "world-map.svg")

# ISO 3166-1 alpha-2 -> display name, for every country present in
# assets/world-map.svg (Simple World Map, Al MacDonald / Fritz Lekschas,
# CC BY-SA 3.0 — see the file's own <desc> for the license).
COUNTRY_NAMES = {
    "ae": "United Arab Emirates", "af": "Afghanistan", "al": "Albania", "am": "Armenia",
    "ao": "Angola", "ar": "Argentina", "at": "Austria", "au": "Australia", "az": "Azerbaijan",
    "ba": "Bosnia and Herzegovina", "bd": "Bangladesh", "be": "Belgium", "bf": "Burkina Faso",
    "bg": "Bulgaria", "bi": "Burundi", "bj": "Benin", "bn": "Brunei", "bo": "Bolivia",
    "br": "Brazil", "bs": "Bahamas", "bt": "Bhutan", "bw": "Botswana", "by": "Belarus",
    "bz": "Belize", "ca": "Canada", "cd": "DR Congo", "cf": "Central African Republic",
    "cg": "Republic of Congo", "ch": "Switzerland", "ci": "Côte d'Ivoire", "cl": "Chile",
    "cm": "Cameroon", "cn": "China", "co": "Colombia", "cr": "Costa Rica", "cu": "Cuba",
    "cv": "Cabo Verde", "cy": "Cyprus", "cz": "Czechia", "de": "Germany", "dj": "Djibouti",
    "dk": "Denmark", "dm": "Dominica", "do": "Dominican Republic", "dz": "Algeria",
    "ec": "Ecuador", "ee": "Estonia", "eg": "Egypt", "er": "Eritrea", "es": "Spain",
    "et": "Ethiopia", "fi": "Finland", "fk": "Falkland Islands", "fr": "France",
    "ga": "Gabon", "gb": "United Kingdom", "ge": "Georgia", "gh": "Ghana",
    "gl": "Greenland", "gm": "Gambia", "gn": "Guinea", "gq": "Equatorial Guinea",
    "gr": "Greece", "gt": "Guatemala", "gw": "Guinea-Bissau", "gy": "Guyana",
    "hn": "Honduras", "hr": "Croatia", "ht": "Haiti", "hu": "Hungary", "id": "Indonesia",
    "ie": "Ireland", "il": "Israel", "in": "India", "iq": "Iraq", "ir": "Iran",
    "is": "Iceland", "it": "Italy", "jm": "Jamaica", "jo": "Jordan", "jp": "Japan",
    "ke": "Kenya", "kg": "Kyrgyzstan", "kh": "Cambodia", "km": "Comoros",
    "kp": "North Korea", "kr": "South Korea", "kw": "Kuwait", "kz": "Kazakhstan",
    "la": "Laos", "lb": "Lebanon", "lc": "Saint Lucia", "lk": "Sri Lanka",
    "lr": "Liberia", "ls": "Lesotho", "lt": "Lithuania", "lu": "Luxembourg",
    "lv": "Latvia", "ly": "Libya", "ma": "Morocco", "md": "Moldova", "me": "Montenegro",
    "mg": "Madagascar", "mk": "North Macedonia", "ml": "Mali", "mm": "Myanmar",
    "mn": "Mongolia", "mr": "Mauritania", "mt": "Malta", "mu": "Mauritius",
    "mv": "Maldives", "mw": "Malawi", "mx": "Mexico", "my": "Malaysia",
    "mz": "Mozambique", "na": "Namibia", "nc": "New Caledonia", "ne": "Niger",
    "ng": "Nigeria", "ni": "Nicaragua", "nl": "Netherlands", "no": "Norway",
    "np": "Nepal", "nz": "New Zealand", "om": "Oman", "pa": "Panama", "pe": "Peru",
    "pg": "Papua New Guinea", "ph": "Philippines", "pk": "Pakistan", "pl": "Poland",
    "pr": "Puerto Rico", "pt": "Portugal", "py": "Paraguay", "qa": "Qatar",
    "ro": "Romania", "rs": "Serbia", "ru": "Russia", "rw": "Rwanda",
    "sa": "Saudi Arabia", "sb": "Solomon Islands", "sc": "Seychelles", "sd": "Sudan",
    "se": "Sweden", "sg": "Singapore", "si": "Slovenia", "sk": "Slovakia",
    "sl": "Sierra Leone", "sn": "Senegal", "so": "Somalia", "sr": "Suriname",
    "ss": "South Sudan", "st": "São Tomé and Príncipe", "sv": "El Salvador",
    "sy": "Syria", "sz": "Eswatini", "td": "Chad", "tg": "Togo", "th": "Thailand",
    "tj": "Tajikistan", "tm": "Turkmenistan", "tn": "Tunisia", "tr": "Turkey",
    "tt": "Trinidad and Tobago", "tw": "Taiwan", "tz": "Tanzania", "ua": "Ukraine",
    "ug": "Uganda", "us": "United States", "uy": "Uruguay", "uz": "Uzbekistan",
    "vc": "Saint Vincent and the Grenadines", "ve": "Venezuela", "vn": "Vietnam",
    "vu": "Vanuatu", "ye": "Yemen", "za": "South Africa", "zm": "Zambia", "zw": "Zimbabwe",
}

EU_COUNTRIES = ["at", "be", "bg", "hr", "cy", "cz", "dk", "ee", "fi", "fr", "de", "gr",
                "hu", "ie", "it", "lv", "lt", "lu", "mt", "nl", "pl", "pt", "ro", "sk",
                "si", "es", "se"]

# iso2 -> tracker key. Every EU member state maps to "eu" (one shared panel);
# everything else is 1:1. Countries not in this dict fall back to a generic
# "no dedicated tracker" panel, cross-referenced against the global recalls
# feed by country name.
TRACKER_MAP = {c: "eu" for c in EU_COUNTRIES}
TRACKER_MAP.update({
    "us": "us", "gb": "gb", "ca": "ca", "au": "au", "nz": "nz",
    "br": "br", "kr": "kr", "jp": "jp", "cn": "cn", "cl": "cl",
})

# Secondary-source survey notes for countries with no dedicated tracker —
# from a "181-nation" comparative writeup (xtremeinks.com/blogs/artists-corner,
# a tattoo-ink retailer's blog, not a primary government source). Genuinely
# useful as a starting signal (most entries land on "no comprehensive
# framework," consistent with what verified per-country research found for
# Japan/China), but NOT independently confirmed against primary law the way
# the dedicated trackers are — every panel using this says so explicitly.
# Compiled 2026-08-20 during the "full sweep on the rest of the world" pass.
SURVEY_NOTES = {
    "al": "Trending toward European norms.",
    "ar": "Local health departments oversee tattoo studios; sanitary licenses required, but ink-specific regulation is less stringent.",
    "bd": "Emerging industry; urban centers tend to follow international ink standards.",
    "bn": "Limited framework; general health standards apply.",
    "bt": "No strict ink regulations; traditional/cultural context.",
    "bw": "No specific ink regulations; general health standards apply.",
    "bz": "Not stringent; general guidelines enforced.",
    "cd": "No standardized acceptable-ingredients list.",
    "ci": "No comprehensive framework.",
    "cm": "No robust framework; growing emphasis on standards.",
    "co": "Local health departments regulate; trend toward imported (internationally compliant) inks.",
    "dm": "No comprehensive system.",
    "eg": "Ministry of Health sets regulations, but no comprehensive banned-substance list.",
    "et": "No specific regulations; general sanitary guidelines apply.",
    "fk": "Likely aligns with UK guidelines (no direct source).",
    "ga": "Lacks a robust framework; general health guidelines only.",
    "gh": "Not heavily regulated; traditional practice context.",
    "gl": "Aligns with Danish/European guidelines.",
    "gm": "Not well-defined; traditional practice context.",
    "gn": "No detailed framework; traditional practice context.",
    "hn": "No robust framework; health department oversight.",
    "id": "No specific regulations found.",
    "in": "Largely unregulated; some state governments issue guidelines.",
    "ir": "No specific national regulations; imported inks preferred.",
    "is": "Adheres to European guidelines.",
    "jm": "No specific regulations; general health/sanitation guidelines.",
    "jo": "No detailed framework; health oversight of cleanliness/safety.",
    "kh": "No exhaustive framework; emphasis on cleanliness.",
    "lb": "No comprehensive system; subject to general health/sanitation checks.",
    "lc": "Not stringent; general guidelines apply.",
    "ls": "No specific ink regulations; traditional practice context.",
    "ly": "Lacks detailed regulations.",
    "me": "No stringent framework dedicated to inks specifically.",
    "mg": "Not heavily regulated; general standards emphasized.",
    "mk": "European alignment likely (no direct source).",
    "ml": "No robust framework; general guidelines apply.",
    "mr": "Not strict; general health standards, traditional practice context.",
    "mv": "No robust framework; health emphasis concentrated in tourist zones.",
    "mx": "Ministry of Health guidelines exist; sanitary licenses required for studios, but no strict rule on which ink components are permitted.",
    "my": "Guidelines exist; imported inks tend to already meet international standards.",
    "mz": "No specific national regulations found.",
    "na": "Not well-defined; general health standards enforced.",
    "nc": "Follows French regulations.",
    "ne": "Lacks a comprehensive modern framework.",
    "ng": "No strict national regulation; practices vary widely.",
    "ni": "No detailed system; many studios use international-standard imports.",
    "np": "No rigorous framework; hygiene emphasized over ink composition.",
    "pe": "Local health departments focus on sanitation; market relies on imported inks.",
    "ph": "Department of Health has issued guidelines/standards.",
    "pk": "Not heavily regulated; increasing calls for safety standards.",
    "pr": "Subject to health/safety regulation aligned with the US mainland (see the US panel).",
    "qa": "Limited regulation; imported inks used.",
    "ru": "Health/sanitation standards apply, described as less stringent than Western countries.",
    "rw": "No strict regulations; professionals prefer international-standard imports.",
    "sl": "Not governed by a specific framework; traditional practice context.",
    "sn": "No comprehensive framework.",
    "so": "Tattooing is not mainstream; no robust regulatory system.",
    "sr": "General health/safety standards apply.",
    "sv": "Not well-documented; general health/sanitation guidelines apply.",
    "td": "No specific ink regulations; traditional practice context.",
    "tg": "Not heavily regulated; traditional practice context.",
    "tn": "No comprehensive system; subject to general health inspections.",
    "tr": "Licensed studios must adhere to Ministry of Health regulations.",
    "tt": "Not well-documented; general guidelines apply.",
    "tw": "Regulations reportedly being implemented; most studios use compliant imported inks.",
    "ua": "No exhaustive framework; many studios use European-standard imports.",
    "ug": "No comprehensive framework; some health ministry guidance exists.",
    "vc": "No specific framework; general standards enforced.",
    "ve": "Health/sanitation guidelines apply; international ink brands prevalent.",
    "vn": "Business license required for studios; no centralized framework for ink composition specifically.",
    "ye": "No detailed regulations found.",
    "za": "Regulated at the provincial level; no national guidelines specific to ink, though international practices are generally followed.",
    "zw": "No specific regulatory focus on inks found.",
}


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
                title = bm.group(1) + (bm.group(2) or "")
                current["items"].append({"title": title, "desc": bm.group(3), "checked": checked})
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


def newzealand_card():
    state = load_json(NZ_STATE)
    report = load_json(NZ_REPORT) or {}
    changed = report.get("changed", False)

    body = ('<p class="stat">Tattoo and Permanent Makeup Substances Group Standard 2020 '
            '(HSR100580, amended 2022-11-24) — in force. Concentration limits on PAHs, heavy '
            'metals, aromatic amines (&lt;5ppm), colouring agents (&lt;0.1% by weight). Separate '
            'regulator from Australia\'s AICIS — was missed in original project scoping.</p>')
    if changed:
        body += '<p class="change-row added">Standard changed since last check — review, may mean an amendment.</p>'
    elif state:
        body += f'<p class="empty">Unchanged since {hesc(state.get("checked_at", "—"))}</p>'
    else:
        body += '<p class="empty">No data yet — run formulation/newzealand_fetcher.py</p>'
    return card("New Zealand — EPA Group Standard", "New Zealand &middot; formulation restriction", body)


def chile_card():
    state = load_json(CHILE_STATE)
    report = load_json(CHILE_REPORT) or {}
    changed = report.get("changed", False)

    body = ('<p class="stat">Resolución Exenta E6717-25 (ISP), published 2025-08-28 — '
            'establishes a Sanitary Control Regime for tattoo inks. Registration-based model, '
            'similar in spirit to Brazil\'s ANVISA. Found during the "full sweep" pass — '
            'genuinely new (evaluation dated July 2025), not a long-standing law that was missed.</p>')
    if changed:
        body += '<p class="change-row added">Resolution changed since last check — review, may mean an amendment.</p>'
    elif state:
        body += f'<p class="empty">Unchanged since {hesc(state.get("checked_at", "—"))}</p>'
    else:
        body += '<p class="empty">No data yet — run formulation/chile_fetcher.py</p>'
    return card("Chile — ISP Sanitary Control Regime", "Chile &middot; formulation restriction", body)


def global_recalls_card():
    state = load_json(GLOBAL_RECALLS_STATE)
    report = load_json(GLOBAL_RECALLS_REPORT) or {}
    state = state if state is not None else {}
    new_items = report.get("new_items", [])

    body = ('<p class="stat">Aggregates recall notices across many national systems (EU Safety '
            'Gate and others feed into this) into one search — covers far more markets than any '
            'single-country fetcher here.</p>')
    body += f'<p class="stat">{len(state)} tattoo-related recalls tracked, {len(new_items)} new since last check</p>'

    items = sorted(state.values(), key=lambda x: x.get("date", ""), reverse=True)[:15]
    if items:
        body += '<div class="doc-list">'
        for i in items:
            flagged = i["id"] in {n["id"] for n in new_items}
            url = hesc(i.get("url", ""))
            body += f"""
            <div class="doc-row{' flagged' if flagged else ''}">
              <a class="doc-title" href="{url}" target="_blank" rel="noopener">{hesc(i['country'])}: {hesc(i['product'])}</a>
              <div class="doc-meta">{hesc(i.get('date', ''))}
                {'&middot; <span class="flag">NEW</span>' if flagged else ''}</div>
            </div>"""
        body += "</div>"
    return card("Global recalls (OECD)", "Multi-country &middot; recall/enforcement radar", body)


def simple_doc_card(title, subtitle, note, state, report, changed_key="changed", label="document"):
    """Small helper for the single-document hash-diff commerce cards (CLP,
    Consumer Rights, PPWR) — they all share the same shape."""
    changed = report.get(changed_key, False) if report else False
    body = f'<p class="stat">{note}</p>'
    if changed:
        body += '<p class="change-row added">Changed since last check — review.</p>'
    elif state:
        body += f'<p class="empty">Unchanged since {hesc(state.get("checked_at", "—"))}</p>'
    else:
        body += f'<p class="empty">No data yet — run {hesc(label)}</p>'
    return card(title, subtitle, body)


def clp_card():
    state = load_json(CLP_STATE) or {}
    report = load_json(CLP_REPORT) or {}
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
    body = '<p class="stat">Substance classification/labeling duty at point of sale — distinct from the Annex XVII formulation restriction.</p>'
    body += "".join(rows) or '<p class="empty">No data yet — run commerce/clp_fetcher.py</p>'
    return card("EU CLP Annex VI", "EU &middot; labeling duty", body)


def consumer_rights_card():
    state = load_json(CONSUMER_RIGHTS_STATE)
    report = load_json(CONSUMER_RIGHTS_REPORT) or {}
    note = "Return/cooling-off period and pre-contract info duties for direct-to-consumer online sale into the EU."
    return simple_doc_card("EU Consumer Rights Directive", "EU &middot; distance-selling rules",
                            note, state, report, label="commerce/consumer_rights_fetcher.py")


def packaging_waste_card():
    state = load_json(PACKAGING_WASTE_STATE)
    report = load_json(PACKAGING_WASTE_REPORT) or {}
    note = "EPR packaging waste fees — Regulation (EU) 2025/40 (PPWR), actively being implemented."
    return simple_doc_card("EU Packaging Waste Regulation", "EU &middot; EPR fees",
                            note, state, report, label="commerce/packaging_waste_fetcher.py")


def hazmat_card():
    state = load_json(HAZMAT_STATE) or {}
    report = load_json(HAZMAT_REPORT) or {}
    new_items = report.get("new_items", [])
    body = ('<p class="stat">US (PHMSA/DOT) only — some pigments classify as dangerous goods for '
            'transport. IATA DGR / IMO IMDG Code have no open API, reference-only.</p>')
    body += f'<p class="stat">{len(state)} documents tracked, {len(new_items)} new since last check</p>'
    items = sorted(state.values(), key=lambda x: x.get("date", ""), reverse=True)[:8]
    if items:
        body += '<div class="doc-list">'
        for i in items:
            flagged = i["document_number"] in {n["document_number"] for n in new_items}
            url = hesc(i.get("url", ""))
            body += f"""
            <div class="doc-row{' flagged' if flagged else ''}">
              <a class="doc-title" href="{url}" target="_blank" rel="noopener">{hesc(i['title'])}</a>
              <div class="doc-meta">{hesc(i.get('date', ''))}
                {'&middot; <span class="flag">NEW</span>' if flagged else ''}</div>
            </div>"""
        body += "</div>"
    return card("US Hazmat (PHMSA)", "US &middot; shipping classification", body)


def customs_card():
    state = load_json(CUSTOMS_STATE) or {}
    report = load_json(CUSTOMS_REPORT) or {}
    changes = report.get("changes", [])
    new_codes = report.get("new_codes", [])
    body = ('<p class="stat">US only — HS/customs classification and duty rates are per-country, '
            'no single global source. Tracks HTS Chapter 32 dye/pigment codes.</p>')
    body += f'<p class="stat">{len(state)} codes tracked, {len(changes)} changed, {len(new_codes)} new</p>'
    if changes:
        body += '<div class="changes">'
        for c in changes:
            body += (f'<div class="change-row added">~ {hesc(c["htsno"])}: '
                      f'{hesc(c["before"]["general_duty"])} &rarr; {hesc(c["after"]["general_duty"])}</div>')
        body += "</div>"
    return card("US Customs/HTS", "US &middot; import duty", body)


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


SVG_OUTER = re.compile(r"<svg[^>]*>.*?<desc>.*?</desc>\s*(.*)</svg>", re.S)


def get_map_svg_inner():
    """Strip the XML prolog/DOCTYPE/svg-wrapper/title/desc from the source
    map file, keeping just the country <path>/<g> elements, so it can be
    re-wrapped in our own <svg> with our own viewBox/classes."""
    raw = open(WORLD_MAP_SVG_PATH, encoding="utf-8").read()
    m = SVG_OUTER.search(raw)
    if not m:
        raise RuntimeError("assets/world-map.svg structure changed — SVG_OUTER regex no longer matches")
    return m.group(1)


def japan_panel():
    body = ('<p class="stat">Confirmed gap, not a reachability problem — searched e-Gov '
            '(Japan\'s official law database, full-text, ungated) for "tattoo" across 4 '
            'terms. Zero relevant hits. "入れ墨" (tattoo) only appears in unrelated law '
            '(anti-yakuza statute, as an identifying-mark description). Tattoo needles/'
            'machines were excluded from medical device classification in 2022 — the trend '
            'is toward less oversight, not more.</p>')
    return card("Japan", "Japan &middot; confirmed gap, no tracker", body)


def china_panel():
    body = ('<p class="stat">Confirmed gap via two independent angles: no tattoo pigment '
            'coverage under NMPA\'s cosmetics registration/filing framework, and no '
            'tattoo-specific customs restriction (only generic hazmat import rules that\'d '
            'apply to any chemical). Less exhaustively confirmed than Japan\'s — China\'s '
            'law database is a JS SPA not fully searched.</p>')
    return card("China", "China &middot; confirmed gap, no tracker", body)


def build_country_browser(tracker_cards, global_recalls_state):
    """tracker_cards: dict of tracker_key -> list of pre-rendered card() HTML
    strings (reusing the exact same output already shown in the grids above,
    so there's one source of truth per source, not a second copy)."""
    # The OECD feed's country names don't always match COUNTRY_NAMES exactly
    # (e.g. "Slovak Republic" vs "Slovakia") — normalize known variants so
    # the cross-reference below doesn't silently miss a match. Currently
    # harmless for Slovakia specifically (it's EU-tracked, so the fallback
    # path never runs for it), but the matching itself needs to be correct
    # for any future untracked country with a similar name discrepancy.
    COUNTRY_NAME_ALIASES = {
        "Slovak Republic": "Slovakia",
        "Korea, Republic of": "South Korea",
        "Republic of Korea": "South Korea",
        "United States of America": "United States",
        "Czech Republic": "Czechia",
        "Russian Federation": "Russia",
    }
    global_recalls_state = global_recalls_state or {}
    recalls_by_country = {}
    for rec in global_recalls_state.values():
        name = rec.get("country", "")
        name = COUNTRY_NAME_ALIASES.get(name, name)
        recalls_by_country.setdefault(name, []).append(rec)

    panels = []
    tracked_codes = set(TRACKER_MAP.keys())
    for code, name in sorted(COUNTRY_NAMES.items(), key=lambda x: x[1]):
        tracker = TRACKER_MAP.get(code)
        if tracker:
            body = "".join(tracker_cards.get(tracker, []))
        else:
            hits = recalls_by_country.get(name, [])
            body = f'<p class="empty">No dedicated tracker for {hesc(name)} in InkReady.</p>'
            survey_note = SURVEY_NOTES.get(code)
            if survey_note:
                body += (f'<p class="stat">Unverified secondary-source note (not confirmed '
                          f'against primary law, unlike the dedicated trackers): {hesc(survey_note)}</p>')
            if hits:
                body += (f'<p class="stat">{len(hits)} tattoo-related recall(s) for {hesc(name)} '
                          f'in the global recalls feed:</p><div class="doc-list">')
                for h in sorted(hits, key=lambda x: x.get("date", ""), reverse=True)[:10]:
                    url = hesc(h.get("url", ""))
                    body += (f'<div class="doc-row"><a class="doc-title" href="{url}" '
                              f'target="_blank" rel="noopener">{hesc(h.get("product", ""))}</a>'
                              f'<div class="doc-meta">{hesc(h.get("date", ""))}</div></div>')
                body += "</div>"
        panels.append(f'<div class="country-panel" id="panel-{code}" style="display:none">{body}</div>')

    options = "".join(
        f'<option value="{code}">{"★ " if code in tracked_codes else ""}{hesc(name)}</option>'
        for code, name in sorted(COUNTRY_NAMES.items(), key=lambda x: x[1])
    )

    return f"""
  <h2>Browse by country</h2>
  <div class="country-browser">
    <div class="country-browser-controls">
      <label for="country-select">Jump to a country (&#9733; = has a dedicated tracker)</label>
      <select id="country-select" onchange="selectCountry(this.value)">
        <option value="">— Select a country —</option>
        {options}
      </select>
      <div class="map-wrap">
        <svg id="world-map-svg" viewBox="30.767 241.591 784.077 458.627" xmlns="http://www.w3.org/2000/svg">
          {get_map_svg_inner()}
        </svg>
      </div>
      <p class="map-caption">Map: Simple World Map (Al MacDonald / Fritz Lekschas, CC BY-SA 3.0).
        Colored countries have a dedicated InkReady tracker — click one, or use the dropdown.</p>
    </div>
    <div class="country-browser-panel">
      <div id="panel-empty" class="country-panel-placeholder">Click a country on the map, or pick one from the dropdown.</div>
      {"".join(panels)}
    </div>
  </div>
  <style>
    .country-browser {{
      display: grid;
      grid-template-columns: minmax(280px, 480px) 1fr;
      gap: 24px;
      margin-top: 20px;
      align-items: start;
    }}
    .country-browser-controls label {{
      display: block;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #777;
      margin-bottom: 6px;
    }}
    #country-select {{
      width: 100%;
      padding: 8px;
      font-family: inherit;
      font-size: 15px;
      border: 1px solid var(--border);
      background: var(--white);
      margin-bottom: 14px;
    }}
    .map-wrap {{
      background: var(--white);
      border: 1px solid var(--border);
      padding: 8px;
    }}
    #world-map-svg {{ width: 100%; height: auto; display: block; }}
    /* 37 of the 179 countries (US, Canada, Indonesia, ...) are <g id="xx">
       wrapping several UN-id'd child <path>s (mainland, islands, etc).
       Styling with a blanket "path, g" selector paints those inner paths
       directly, which beats SVG's inherited fill from the id'd parent group
       — the country silently stays gray even though its <g> has the right
       class. Fix: only style elements that actually carry an id (real
       country nodes); un-id'd children then correctly inherit from their
       parent group instead of getting their own conflicting fill. */
    #world-map-svg [id] {{
      fill: #e0e0e0;
      stroke: var(--white);
      stroke-width: 0.5;
      transition: fill 0.15s;
    }}
    #world-map-svg [id].tracked {{ fill: #ffcda3; cursor: pointer; }}
    #world-map-svg [id].tracked:hover {{ fill: var(--orange); }}
    #world-map-svg [id].untracked {{ cursor: pointer; }}
    #world-map-svg [id].untracked:hover {{ fill: #bbb; }}
    #world-map-svg [id].selected {{ fill: var(--black) !important; }}
    .map-caption {{
      font-size: 12px;
      color: #999;
      margin-top: 8px;
    }}
    .country-browser-panel {{ min-height: 200px; }}
    .country-panel-placeholder {{
      background: var(--white);
      border: 1px dashed var(--border);
      padding: 40px 20px;
      text-align: center;
      color: #999;
      font-style: italic;
    }}
    .country-panel .card {{ margin-bottom: 16px; }}
    .country-panel .card:last-child {{ margin-bottom: 0; }}
    @media (max-width: 800px) {{
      .country-browser {{ grid-template-columns: 1fr; }}
    }}
  </style>
  <script>
    (function() {{
      var trackedCodes = {json.dumps(sorted(tracked_codes))};
      var svg = document.getElementById('world-map-svg');
      trackedCodes.forEach(function(code) {{
        var el = svg.querySelector('[id="' + code + '"]');
        if (el) el.classList.add('tracked');
      }});
      Array.prototype.forEach.call(svg.querySelectorAll('[id]'), function(el) {{
        if (!el.classList.contains('tracked')) el.classList.add('untracked');
      }});

      var currentSelected = null;

      window.selectCountry = function(code) {{
        document.getElementById('panel-empty').style.display = code ? 'none' : '';
        Array.prototype.forEach.call(document.querySelectorAll('.country-panel'), function(p) {{
          p.style.display = 'none';
        }});
        if (currentSelected) {{
          var prev = svg.querySelector('[id="' + currentSelected + '"]');
          if (prev) prev.classList.remove('selected');
        }}
        if (!code) {{ currentSelected = null; return; }}
        var panel = document.getElementById('panel-' + code);
        if (panel) panel.style.display = '';
        var el = svg.querySelector('[id="' + code + '"]');
        if (el) el.classList.add('selected');
        currentSelected = code;
        document.getElementById('country-select').value = code;
      }};

      svg.addEventListener('click', function(ev) {{
        var target = ev.target.closest('[id]');
        if (!target || !target.id) return;
        selectCountry(target.id);
      }});
    }})();
  </script>
"""


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
  {country_browser}

  <h2>Formulation — what's allowed in the ink</h2>
  <div class="grid">
    {echa_card}
    {prop65_card}
    {mocra_card}
    {uk_reach_card}
    {canada_card}
    {australia_card}
    {newzealand_card}
    {brazil_card}
    {korea_card}
    {chile_card}
    {global_recalls_card}
  </div>

  <h2>Commerce — rules on selling it</h2>
  <div class="grid">
    {clp_card}
    {consumer_rights_card}
    {packaging_waste_card}
    {hazmat_card}
    {customs_card}
  </div>
  {commerce}
</main>
<footer>InkReady &middot; internal use &middot; github.com/alexandersmith14-dotcom/InkReady</footer>
</body>
</html>
"""


def main():
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    echa, prop65, mocra = echa_card(), prop65_card(), mocra_card()
    uk_reach, canada, australia = uk_reach_card(), canada_card(), australia_card()
    newzealand, brazil, korea = newzealand_card(), brazil_card(), korea_card()
    chile = chile_card()
    global_recalls = global_recalls_card()
    clp, consumer_rights = clp_card(), consumer_rights_card()
    packaging_waste, hazmat, customs = packaging_waste_card(), hazmat_card(), customs_card()

    tracker_cards = {
        "eu": [echa, clp, consumer_rights, packaging_waste],
        "us": [prop65, mocra, hazmat, customs],
        "gb": [uk_reach],
        "ca": [canada],
        "au": [australia],
        "nz": [newzealand],
        "br": [brazil],
        "kr": [korea],
        "cl": [chile],
        "jp": [japan_panel()],
        "cn": [china_panel()],
    }
    country_browser = build_country_browser(tracker_cards, load_json(GLOBAL_RECALLS_STATE))

    page = PAGE_TEMPLATE.format(
        generated_at=generated_at,
        country_browser=country_browser,
        echa_card=echa,
        prop65_card=prop65,
        mocra_card=mocra,
        uk_reach_card=uk_reach,
        canada_card=canada,
        australia_card=australia,
        newzealand_card=newzealand,
        brazil_card=brazil,
        korea_card=korea,
        chile_card=chile,
        global_recalls_card=global_recalls,
        clp_card=clp,
        consumer_rights_card=consumer_rights,
        packaging_waste_card=packaging_waste,
        hazmat_card=hazmat,
        customs_card=customs,
        commerce=commerce_section(),
    )
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(page)
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"wrote {OUT_PATH} and {INDEX_PATH}")


if __name__ == "__main__":
    main()
