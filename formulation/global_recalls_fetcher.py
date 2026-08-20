"""Global tattoo ink recall tracker — OECD Global Portal on Product Recalls.

The country-specific fetchers in this repo (Canada, Australia, Brazil) each
needed their own research pass to find a reachable source, and most of the
world's 190+ markets Solid Ink ships to don't have one at all worth
building individually. This is the actual scalable answer: the OECD's
Global Portal on Product Recalls (globalrecalls.oecd.org) aggregates recall
notices FROM many national systems (EU Safety Gate, and others) into one
feed. One fetcher here effectively covers dozens of countries at once,
instead of a dedicated one-off build per market.

The portal itself is a pure JS SPA (a 541-byte shell, all data loaded via a
hidden API) — found via reverse-api-engineer (see
C:\\Users\\alexa\\OneDrive\\Documents 1\\Default Project\\reverse-api-engineer),
which discovered the real endpoint: GET /ws/search.xqy, no authentication.
Verified independently: a plain "tattoo" search returned 341 real results
spanning France, the UK, Italy, and more, including real tattoo ink brands
(World Famous Tattoo Ink, Dynamic, Kuro Sumi) with recent dates.
"""

import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BASE_URL = "https://globalrecalls.oecd.org"
SEARCH_ENDPOINT = f"{BASE_URL}/ws/search.xqy"

UA = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://globalrecalls.oecd.org/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
}

QUERY = "tattoo"
# Requested as a hint but the server silently caps each page at 20 results
# regardless of what's asked for (verified: requesting end=100 still returns
# only 20 and reports "end": 100 in the response as if it complied) - so
# pagination advances by however many results actually came back, not by
# this requested size, or results between pages get silently skipped.
PAGE_SIZE = 100

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "global_recalls_state.json")
REPORT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "global_recalls_report.json")


def fetch_with_retry(url, attempts=5, pause=5, timeout=30):
    last_err = None
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            last_err = e
            if attempt < attempts - 1:
                time.sleep(pause * (2 ** attempt))
    raise RuntimeError(f"failed after {attempts} attempts: {last_err}")


def fetch_all_recalls():
    all_results, start = [], 0
    while True:
        params = {"q": QUERY, "start": start, "end": PAGE_SIZE, "lang": "en",
                   "uiLang": "en", "sort": "date", "order": "desc"}
        url = SEARCH_ENDPOINT + "?" + urllib.parse.urlencode(params)
        data = fetch_with_retry(url)
        results = data.get("results", [])
        all_results.extend(results)
        total = data.get("total", 0)
        if start + len(results) >= total or not results:
            break
        start += len(results)
    if not all_results:
        raise RuntimeError(f"0 results for '{QUERY}' — expected some (API or query may be broken)")

    entries = {}
    for r in all_results:
        rid = r.get("id")
        if not rid:
            continue
        entries[rid] = {
            "id": rid,
            "date": r.get("date", ""),
            "country": r.get("countryName", ""),
            "product": r.get("product.name", ""),
            "url": r.get("extUrl", ""),
        }
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
        current = fetch_all_recalls()
    except Exception as e:
        print(f"  FAIL  Global recalls (OECD)  {e}")
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            json.dump({"checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                       "error": str(e)}, f, indent=2)
        raise

    new_items = [v for k, v in current.items() if prior is None or k not in prior]

    if prior is None:
        print(f"  NEW   Global recalls (OECD)  baseline recorded — {len(current)} tattoo-related recalls")
    else:
        print(f"  OK    Global recalls (OECD)  {len(current)} tracked, {len(new_items)} new")
        for i in new_items[:20]:
            print(f"    + [{i['date']}] {i['country']}: {i['product']}")

    save_state(current)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "total_tracked": len(current),
            "new_items": new_items,
            "note": "Aggregates recall notices from many national systems (EU Safety Gate and "
                    "others feed into this portal) into one search. Covers far more markets than "
                    "the country-specific fetchers in this repo, at the cost of depending on "
                    "whichever countries actually report into OECD's system.",
        }, f, indent=2)


if __name__ == "__main__":
    main()
