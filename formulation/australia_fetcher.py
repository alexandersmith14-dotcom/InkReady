"""Australia tattoo ink tracker — Product Safety Australia recalls.

Australia has NO binding federal restriction list for tattoo ink — confirmed
by research, not assumed: "no binding national regulatory framework... relies
on voluntary compliance and the occasional government characterisation
study." AICIS (the federal industrial chemicals regulator) publishes consumer
guidance on tattoo/PMU inks but doesn't restrict specific substances the way
EU Annex XVII or even the (still-unenacted) UK proposal does. Queensland is
the first state moving toward EU-aligned pigment rules, but as of this
writing it's still at the public-consultation stage, not in force.

None of the primary government pages are reachable with a plain request:
- industrialchemicals.gov.au (AICIS): times out, 2/2 attempts, ~40s each
- health.qld.gov.au: 403
- legislation.qld.gov.au: connection failure
All three are documented gaps here, not worked around — same precedent as
Klearance leaving FFIEC/NYDFS out and this repo's own Canada/UK sources.

What IS reachable: the ACCC's Product Safety Australia recall RSS feed
(productsafety.gov.au/rss/feed.xml/psa_recall) — plain request works, no
gate. Filtered to "tattoo" in title/description, same recall/enforcement
radar pattern as the Canada and EU Safety Gate sources. Currently 0 matches
in the visible recent window, which is a legitimate finding, not a fetch
failure — the value is catching the first one that appears.
"""

import json
import os
import re
import time
import urllib.request
from datetime import datetime, timezone

RSS_URL = "https://www.productsafety.gov.au/rss/feed.xml/psa_recall"

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "australia_state.json")
REPORT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "australia_report.json")

ITEM = re.compile(r"<item>(.*?)</item>", re.S)
TITLE = re.compile(r"<title>(.*?)</title>", re.S)
LINK = re.compile(r"<link>(.*?)</link>", re.S)
GUID = re.compile(r"<guid[^>]*>(.*?)</guid>", re.S)
PUBDATE = re.compile(r"<pubDate>(.*?)</pubDate>", re.S)
DESC = re.compile(r"<description>(.*?)</description>", re.S)


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


def fetch_recalls():
    xml = get(RSS_URL)
    items = ITEM.findall(xml)
    if not items:
        raise RuntimeError("0 <item> entries in feed — layout may have changed")

    parsed = []
    for chunk in items:
        title_m, link_m, guid_m = TITLE.search(chunk), LINK.search(chunk), GUID.search(chunk)
        pubdate_m, desc_m = PUBDATE.search(chunk), DESC.search(chunk)
        parsed.append({
            "guid": guid_m.group(1).strip() if guid_m else (link_m.group(1).strip() if link_m else None),
            "title": title_m.group(1).strip() if title_m else "",
            "url": link_m.group(1).strip() if link_m else "",
            "pub_date": pubdate_m.group(1).strip() if pubdate_m else "",
            "description": desc_m.group(1) if desc_m else "",
        })
    return [p for p in parsed if p["guid"]]


def filter_tattoo(items):
    matches = {}
    for i in items:
        haystack = (i["title"] + " " + i["description"]).lower()
        if "tattoo" in haystack:
            matches[i["guid"]] = {"guid": i["guid"], "title": i["title"], "url": i["url"], "pub_date": i["pub_date"]}
    return matches


def load_state():
    # None (never run) vs {} (ran before, found zero matches) must stay
    # distinguishable, or a legitimate 0-match baseline never graduates to
    # "OK, checked, still zero" on the next run.
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
        items = fetch_recalls()
        current = filter_tattoo(items)
    except Exception as e:
        print(f"  FAIL  Australia recalls  {e}")
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            json.dump({"checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                       "error": str(e)}, f, indent=2)
        raise

    new_items = [v for k, v in current.items() if prior is None or k not in prior]

    if prior is None:
        print(f"  NEW   Australia recalls  baseline recorded — {len(current)} tattoo-related "
              f"(of {len(items)} recalls in feed window)")
    else:
        print(f"  OK    Australia recalls  {len(current)} tattoo-related, {len(new_items)} new")
        for i in new_items:
            print(f"    + [{i['pub_date']}] {i['title']}")

    save_state(current)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "total_tattoo_related": len(current),
            "total_recalls_in_window": len(items),
            "new_items": new_items,
            "note": "Australia has no binding federal tattoo ink restriction list (voluntary "
                    "compliance only). AICIS, Queensland Health, and Queensland legislation sites "
                    "are all unreachable with a plain request — documented gaps, not tracked here.",
        }, f, indent=2)


if __name__ == "__main__":
    main()
