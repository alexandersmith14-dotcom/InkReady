"""Canada tattoo ink tracker — Health Canada Recalls & Safety Alerts.

Tattoo ink is regulated as a cosmetic in Canada (explicitly excepted from the
general "injected products aren't cosmetics" rule), and the Cosmetic
Ingredient Hotlist (~500 prohibited/restricted substances) is the Canadian
equivalent of EU Annex XVII. It is NOT machine-accessible: the canada.ca page
hosting it consistently times out on a plain request (5/5 attempts, ~40-45s
each, no response body) — an Akamai-style tarpit, not a clean 403 like
ECHA/EUR-Lex but the same practical effect. No CSV/JSON/API version exists
anywhere, including Canada's own open data portal (open.canada.ca) — checked
directly, not published there. Left unreachable rather than worked around,
same precedent as Klearance leaving FFIEC/NYDFS out.

What IS reachable and genuinely useful: Health Canada's Recalls & Safety
Alerts open dataset, on a different subdomain (recalls-rappels.canada.ca)
that isn't gated. ~34,000 recalls across every consumer product category;
filtered here to ones whose title/product/issue text mentions "tattoo" — a
real enforcement signal (e.g. a 2024 tattoo pigment recall for microbial
contamination), same spirit as the EU Safety Gate source in commerce/.
This is a recall/enforcement radar, not a formulation restriction list — the
Hotlist itself stays a documented gap until Health Canada publishes it
somewhere reachable.
"""

import json
import os
import time
import urllib.request
from datetime import datetime, timezone

RECALLS_URL = "https://recalls-rappels.canada.ca/sites/default/files/opendata-donneesouvertes/HCRSAMOpenData.json"

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "canada_state.json")
REPORT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "canada_report.json")


def s(x):
    return x or ""


def fetch_recalls(timeout=60, attempts=5, pause=5):
    # ~15MB single-shot download — a GitHub Actions run hit IncompleteRead
    # here (8MB of 15MB before the connection dropped) with no retry logic
    # at all, so this got the same shape as every other fetcher in this repo.
    last_err = None
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(RECALLS_URL, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read().decode("utf-8-sig"))
            if not isinstance(data, list) or not data:
                raise RuntimeError("recalls feed returned no usable data — format may have changed")
            return data
        except Exception as e:
            last_err = e
            if attempt < attempts - 1:
                time.sleep(pause * (2 ** attempt))
    raise RuntimeError(f"failed after {attempts} attempts: {last_err}")


def filter_tattoo(recalls):
    matches = {}
    for r in recalls:
        haystack = (s(r.get("Title")) + " " + s(r.get("Product")) + " " + s(r.get("Issue"))).lower()
        if "tattoo" in haystack:
            matches[r["NID"]] = {
                "nid": r["NID"],
                "title": s(r.get("Title")).strip(),
                "url": s(r.get("URL")),
                "category": s(r.get("Category")),
                "last_updated": s(r.get("Last updated")),
            }
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
        recalls = fetch_recalls()
        current = filter_tattoo(recalls)
    except Exception as e:
        print(f"  FAIL  Canada recalls  {e}")
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            json.dump({"checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                       "error": str(e)}, f, indent=2)
        raise

    new_items = [v for k, v in current.items() if prior is None or k not in prior]

    if prior is None:
        print(f"  NEW   Canada recalls  baseline recorded — {len(current)} tattoo-related recalls "
              f"(of {len(recalls)} total)")
    else:
        print(f"  OK    Canada recalls  {len(current)} tattoo-related, {len(new_items)} new")
        for i in new_items:
            print(f"    + [{i['last_updated']}] {i['title']}")

    save_state(current)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "total_tattoo_related": len(current),
            "total_recalls_scanned": len(recalls),
            "new_items": new_items,
            "hotlist_note": "Cosmetic Ingredient Hotlist substance list is not machine-accessible "
                             "(canada.ca times out on plain requests, no open-data copy exists) — "
                             "documented gap, not tracked here.",
        }, f, indent=2)


if __name__ == "__main__":
    main()
