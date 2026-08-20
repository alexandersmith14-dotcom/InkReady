"""US customs/HS code duty tracker — import cost for tattoo pigments.

Scoped to the US (primary market) via the USITC Harmonized Tariff Schedule
API — real, ungated, live duty rate data. HS/customs classification and
duty rates are genuinely per-destination-country, so this doesn't attempt
global coverage; it tracks the codes Solid Ink's own imports would fall
under (HTS Chapter 32: dyes, pigments, coloring matter) and flags rate
changes, including the "9902.xx" special/temporary tariff provisions that
get added and removed independent of the base schedule.

WCO's global HS nomenclature (the structure other countries' tariff codes
are built on) doesn't have duty rates of its own — those are set per
country — so a "global" version of this tracker isn't really a coherent
single source the way EU/US law is. Scoped deliberately, not left out
accidentally.
"""

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone

SEARCH_API = "https://hts.usitc.gov/reststop/search"

# HTS headings covering synthetic dyes/pigments and coloring preparations —
# the category tattoo ink pigments fall under.
HTS_QUERIES = ["3204.15", "3204.17", "3204.90"]

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "customs_state.json")
REPORT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "customs_report.json")


def fetch_query(keyword, timeout=30):
    url = SEARCH_API + "?" + urllib.parse.urlencode({"keyword": keyword, "type": "HTS"})
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_all():
    entries = {}
    for q in HTS_QUERIES:
        for item in fetch_query(q):
            code = item.get("htsno")
            if not code:
                continue
            entries[code] = {
                "htsno": code,
                "description": item.get("description", ""),
                "general_duty": item.get("general", ""),
                "special_duty": item.get("special", ""),
                "other_duty": item.get("other", ""),
            }
    if not entries:
        raise RuntimeError("0 HTS entries returned — API or queries may be broken")
    return entries


def load_state():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)


def main():
    prior = load_state()

    try:
        current = fetch_all()
    except Exception as e:
        print(f"  FAIL  US Customs/HTS  {e}")
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            json.dump({"checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                       "error": str(e)}, f, indent=2)
        raise

    changes, new_codes = [], []
    if prior is not None:
        for code, rec in current.items():
            if code not in prior:
                new_codes.append(rec)
            elif prior[code] != rec:
                changes.append({"htsno": code, "before": prior[code], "after": rec})

    if prior is None:
        print(f"  NEW   US Customs/HTS  baseline recorded — {len(current)} codes tracked")
    else:
        print(f"  OK    US Customs/HTS  {len(current)} codes, {len(changes)} changed, {len(new_codes)} new")
        for c in changes:
            print(f"    ~ {c['htsno']}: {c['before']['general_duty']} -> {c['after']['general_duty']}")
        for n in new_codes:
            print(f"    + {n['htsno']}: {n['description'][:60]}")

    save_state(current)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "total_codes": len(current),
            "changes": changes,
            "new_codes": new_codes,
            "note": "US only — duty rates and HS classification are per-destination-country, "
                    "no single global source. Tracks HTS Chapter 32 dye/pigment codes.",
        }, f, indent=2)


if __name__ == "__main__":
    main()
