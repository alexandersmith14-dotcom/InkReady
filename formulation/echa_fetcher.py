"""ECHA REACH Annex XVII Entry 75 (tattoo ink substance restrictions) tracker.

echa.europa.eu and eur-lex.europa.eu both sit behind a CloudFront/AWS WAF bot
challenge — plain requests get a 403 or an empty 202. publications.europa.eu
(the Cellar document store behind EUR-Lex) is not gated the same way: content
negotiation against /resource/celex/{CELEX} 303-redirects to the real document
and returns real text with a plain UA-less request.

Cellar's SPARQL endpoint is reachable too, but a literal search for a CELEX id
across all named graphs (`GRAPH ?g { ... }`) returns empty rather than erroring
— the store is federated per-document and an unscoped scan is too expensive to
run inline. There is no working query here for "what later regulation amends
this one" — that discovery has to stay a human job. KNOWN_DOCS below is the
verified, curated list; add to it by hand when a new amendment is found.
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

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "echa_state.json")

# Verified against the live document 2026-08-20 (74 mentions of "tattoo").
# The 2023 Pigment Blue 15:3 / Pigment Green 7 date is a transition period
# written into this same regulation, not a separate amending act — do not add
# a second entry for it without checking EUR-Lex first.
KNOWN_DOCS = [
    {
        "celex": "32020R2081",
        "title": "Commission Regulation (EU) 2020/2081 — REACH Annex XVII Entry 75, "
                  "substances in tattoo inks and permanent make-up",
        "note": "Base restriction. In force 2022-01-04, Pigment Blue 15:3 / "
                "Pigment Green 7 transition to 2023-01-04.",
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


def fetch_doc(celex, timeout=30):
    url = CELEX_RESOLVER.format(celex=celex)
    req = urllib.request.Request(url, headers=HEADERS)
    html = fetch_with_retry(req, timeout).decode("utf-8", "ignore")
    if "tattoo" not in html.lower() and "reach" not in html.lower():
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

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "echa_report.json"),
              "w", encoding="utf-8") as f:
        json.dump({
            "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "docs_checked": len(KNOWN_DOCS),
            "changes": changes,
            "failures": failures,
        }, f, indent=2)

    if changes:
        print(f"\n{len(changes)} document(s) changed since last check — review before relying on cached text.")
    if failures:
        print(f"\n{len(failures)} document(s) failed to fetch.")


if __name__ == "__main__":
    main()
