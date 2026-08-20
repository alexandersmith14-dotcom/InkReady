"""EU Consumer Rights Directive tracker — distance-selling rules.

Relevant if Solid Ink sells direct-to-consumer online into the EU: the
Consumer Rights Directive (2011/83/EU) sets the return/cooling-off period
and pre-contract information duties for online sales. Reachable and
appropriately sized via the same Cellar content-negotiation technique as the
other EU fetchers here — a directive, not a sprawling regulation, so a
whole-document hash-diff is a reasonable signal (unlike CLP/REACH, which are
too broad for that).
"""

import hashlib
import json
import os
import re
import time
import urllib.request
from datetime import datetime, timezone

CELEX = "32011L0083"
CELEX_RESOLVER = f"http://publications.europa.eu/resource/celex/{CELEX}"

HEADERS = {
    "Accept": "application/xhtml+xml",
    "Accept-Language": "eng",
}

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "consumer_rights_state.json")
REPORT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "consumer_rights_report.json")

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


def fetch_doc(timeout=45):
    req = urllib.request.Request(CELEX_RESOLVER, headers=HEADERS)
    html = fetch_with_retry(req, timeout).decode("utf-8", "ignore")
    if "consumer" not in html.lower():
        raise RuntimeError("fetched content doesn't look right (page layout may have changed)")
    return text_of(html)


def load_state():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def main():
    prior = load_state()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    try:
        text = fetch_doc()
    except Exception as e:
        print(f"  FAIL  EU Consumer Rights Directive  {e}")
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            json.dump({"checked_at": now, "error": str(e)}, f, indent=2)
        raise

    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    changed = False

    if prior is None:
        print("  NEW   EU Consumer Rights Directive  baseline recorded")
    elif prior["hash"] != digest:
        changed = True
        print("  CHANGED  EU Consumer Rights Directive  — review")
    else:
        print(f"  OK    EU Consumer Rights Directive  unchanged since {prior['checked_at']}")

    save_state({"hash": digest, "checked_at": now})
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump({"checked_at": now, "changed": changed, "celex": CELEX}, f, indent=2)


if __name__ == "__main__":
    main()
