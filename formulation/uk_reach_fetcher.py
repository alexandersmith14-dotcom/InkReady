"""UK REACH tattoo ink restriction tracker.

Genuinely different situation from the EU: UK REACH did NOT carry over the
EU's Annex XVII Entry 75 restriction as retained law after Brexit. HSE (the
UK REACH agency) proposed its own restriction in June 2023 — looser than the
EU's, per public commentary — and as of this writing it is STILL awaiting a
Defra ministerial decision. There is no restriction in force and no legal
text to diff. Don't assume UK mirrors the EU restriction (see
formulation/sources/echa_annex_xvii.md) — it currently doesn't exist at all.

Two things worth tracking, both ungated (no WAF, plain requests work):

1. HSE's restriction-proposal status page — the authoritative live status.
   Hash-diffed like the ECHA fetcher: when this page's text changes, that's
   the signal a ministerial decision may have happened.
2. legislation.gov.uk's Atom search API, title-scoped to "REACH" — catches
   any new UK Statutory Instrument amending REACH, tattoo-specific or not.
   Full text of each is checked for "tattoo" as a triage signal, but this is
   NOT a substitute for a human reading it — a new REACH SI is flagged
   regardless of that match, since HSE's tattoo restriction, if enacted,
   might not use that exact word in the operative text.
"""

import json
import os
import re
import time
import urllib.request
from datetime import datetime, timezone

HSE_STATUS_URL = "https://consultations.hse.gov.uk/crd-reach/reach-restriction-tattoo-ink-pmu-substances/"
UKSI_SEARCH_URL = "https://www.legislation.gov.uk/uksi?title=REACH"

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uk_reach_state.json")
REPORT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uk_reach_report.json")

TAG = re.compile(r"<[^>]+>")
ENTRY = re.compile(r"<entry>(.*?)</entry>", re.S)
ID_TAG = re.compile(r"<id>(.*?)</id>")
TITLE_TAG = re.compile(r"<title>(.*?)</title>")
DATA_LINK = re.compile(r'<link[^>]*type="application/xhtml\+xml"[^>]*href="([^"]+)"')


def text_of(html):
    return " ".join(re.sub(TAG, " ", html).split())


def get(url, timeout=45, attempts=5, pause=5):
    req = urllib.request.Request(url, headers=UA)
    last_err = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception as e:
            last_err = e
            if attempt < attempts - 1:
                time.sleep(pause * (2 ** attempt))
    raise RuntimeError(f"failed after {attempts} attempts: {last_err}")


def fetch_hse_status():
    html = get(HSE_STATUS_URL)
    if "tattoo" not in html.lower():
        raise RuntimeError("HSE status page fetched but doesn't mention tattoo — page may have changed")
    return text_of(html)


def fetch_uksi_reach_list():
    xml = get(UKSI_SEARCH_URL + "&data.feed=true" if "?" not in UKSI_SEARCH_URL else UKSI_SEARCH_URL,
              timeout=45)
    # Atom content negotiation: legislation.gov.uk returns Atom for this path
    # by default over a plain UA-only request in practice; re-fetch explicitly
    # asking for it if we somehow got HTML instead.
    if "<feed" not in xml:
        req = urllib.request.Request(UKSI_SEARCH_URL, headers={**UA, "Accept": "application/atom+xml"})
        with urllib.request.urlopen(req, timeout=45) as r:
            xml = r.read().decode("utf-8", "ignore")

    items = []
    for m in ENTRY.finditer(xml):
        chunk = m.group(1)
        id_m, title_m, link_m = ID_TAG.search(chunk), TITLE_TAG.search(chunk), DATA_LINK.search(chunk)
        if not (id_m and title_m):
            continue
        items.append({
            "id": id_m.group(1),
            "title": title_m.group(1),
            "data_url": link_m.group(1) if link_m else None,
        })
    if not items:
        raise RuntimeError("0 REACH-titled UK SIs found — search may be broken (layout/API change)")
    return items


def check_mentions_tattoo(item):
    if not item.get("data_url"):
        return False
    try:
        html = get(item["data_url"], timeout=30)
        return "tattoo" in html.lower()
    except Exception:
        return False


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"hse_status_hash": None, "hse_checked_at": None, "known_uksi": {}}
    with open(STATE_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)


def main():
    import hashlib

    state = load_state()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    report = {"checked_at": now, "hse_status_changed": False, "new_uksi": []}

    try:
        hse_text = fetch_hse_status()
        digest = hashlib.sha256(hse_text.encode("utf-8")).hexdigest()
        if state["hse_status_hash"] is None:
            print("  NEW   HSE status page  baseline recorded")
        elif state["hse_status_hash"] != digest:
            report["hse_status_changed"] = True
            print("  CHANGED  HSE status page  — review, may mean a ministerial decision happened")
        else:
            print(f"  OK    HSE status page  unchanged since {state['hse_checked_at']}")
        state["hse_status_hash"] = digest
        state["hse_checked_at"] = now
    except Exception as e:
        print(f"  FAIL  HSE status page  {e}")
        report["hse_status_error"] = str(e)

    try:
        current_uksi = fetch_uksi_reach_list()
        new_uksi = [i for i in current_uksi if i["id"] not in state["known_uksi"]]
        for item in new_uksi:
            item["mentions_tattoo"] = check_mentions_tattoo(item)
        if not state["known_uksi"]:
            print(f"  NEW   UK REACH SIs  baseline recorded — {len(current_uksi)} instruments")
        else:
            print(f"  OK    UK REACH SIs  {len(current_uksi)} total, {len(new_uksi)} new")
            for i in new_uksi:
                flag = " *** MENTIONS TATTOO ***" if i["mentions_tattoo"] else ""
                print(f"    + {i['title']}{flag}")
        state["known_uksi"] = {i["id"]: i["title"] for i in current_uksi}
        report["new_uksi"] = new_uksi
    except Exception as e:
        print(f"  FAIL  UK REACH SIs  {e}")
        report["uksi_error"] = str(e)

    save_state(state)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)


if __name__ == "__main__":
    main()
