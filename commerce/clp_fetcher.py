"""EU CLP Annex VI (harmonised classification and labelling) tracker.

Distinct from formulation/echa_fetcher.py: that tracks what's ALLOWED IN the
ink (Annex XVII Entry 75 restriction). This tracks the labelling/
classification duty on the substances themselves — a commerce/sale
obligation (what hazard classification and label the seller must apply),
not a formulation restriction.

The base CLP Regulation (CELEX 32008R1272) is reachable via the same Cellar
content-negotiation technique as the ECHA fetcher, but it's 23MB — the full
Annex VI table of thousands of harmonised entries across every hazard class,
not just pigments. Hash-diffing the whole thing would flag "changed" on any
edit anywhere in EU chemical classification, which is real but far too noisy
to be useful here.

Tracked instead: known amending regulations (Adaptation to Technical
Progress / ATP regulations) by CELEX, same curated-list pattern as
formulation/echa_fetcher.py's KNOWN_DOCS. Discovering NEW ATPs automatically
hit the same wall as ECHA's amendment-discovery — Cellar's SPARQL endpoint
returns empty on an unscoped literal search across all named graphs rather
than erroring, so there's no reliable "what's the latest ATP" query. Add new
ATP CELEX numbers here by hand when found, same documented limitation as the
ECHA fetcher.
"""

import hashlib
import json
import os
import re
import time
import urllib.request
from datetime import datetime, timezone

CELEX_RESOLVER = "http://publications.europa.eu/resource/celex/{celex}"

HEADERS = {
    "Accept": "application/xhtml+xml",
    "Accept-Language": "eng",
}

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clp_state.json")
REPORT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clp_report.json")

# Verified 2026-08-20 against the live document.
KNOWN_DOCS = [
    {
        "celex": "32024R0197",
        "title": "Commission Delegated Regulation (EU) 2024/197 — amends CLP Annex VI "
                  "harmonised classification/labelling for certain substances",
        "note": "Published 2024-01-05, applies from 2025-09-01.",
    },
]

TAG = re.compile(r"<[^>]+>")


def text_of(html):
    return " ".join(re.sub(TAG, " ", html).split())


def fetch_with_retry(req, timeout, attempts=5, pause=5):
    last_err = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            last_err = e
            if attempt < attempts - 1:
                time.sleep(pause * (2 ** attempt))
    raise RuntimeError(f"failed after {attempts} attempts: {last_err}")


def fetch_doc(celex, timeout=45):
    url = CELEX_RESOLVER.format(celex=celex)
    req = urllib.request.Request(url, headers=HEADERS)
    html = fetch_with_retry(req, timeout).decode("utf-8", "ignore")
    if "1272/2008" not in html and "classification" not in html.lower():
        raise RuntimeError(f"CELEX {celex}: fetched content doesn't look right (page layout may have changed)")
    return text_of(html)


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def main():
    state = load_state()
    changes = []
    failures = []

    for doc in KNOWN_DOCS:
        celex = doc["celex"]
        try:
            text = fetch_doc(celex)
        except Exception as e:
            failures.append({"celex": celex, "error": str(e)})
            print(f"  FAIL  {celex}  {e}")
            continue

        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        prior = state.get(celex)
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")

        if prior is None:
            print(f"  NEW   {celex}  baseline recorded")
        elif prior["hash"] != digest:
            changes.append({"celex": celex, "title": doc["title"],
                             "prior_hash": prior["hash"], "new_hash": digest,
                             "prior_checked": prior["checked_at"]})
            print(f"  CHANGED  {celex}  {doc['title']}")
        else:
            print(f"  OK    {celex}  unchanged since {prior['checked_at']}")

        state[celex] = {"hash": digest, "checked_at": now, "title": doc["title"]}

    save_state(state)

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "docs_checked": len(KNOWN_DOCS),
            "changes": changes,
            "failures": failures,
            "note": "Tracks known ATP amendments by CELEX only — new ATPs must be added to "
                    "KNOWN_DOCS by hand, no reliable automated discovery found.",
        }, f, indent=2)

    if changes:
        print(f"\n{len(changes)} document(s) changed since last check.")
    if failures:
        print(f"\n{len(failures)} document(s) failed to fetch.")


if __name__ == "__main__":
    main()
