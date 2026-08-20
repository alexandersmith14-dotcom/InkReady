"""EU Packaging and Packaging Waste Regulation (PPWR) tracker — EPR fees.

Solid Ink ships ink bottles/tubes into the EU; several member states charge
sellers Extended Producer Responsibility fees for packaging waste. The EU
harmonized this with Regulation (EU) 2025/40 (PPWR), which is actively being
implemented — a genuinely live document, not settled law like the Consumer
Rights Directive. Reachable via the same Cellar technique. Self-contained
enough (1.2MB, one regulation) for a whole-document hash-diff to be a
reasonable signal, unlike CLP/REACH.
"""

import hashlib
import json
import os
import re
import urllib.request
from datetime import datetime, timezone

CELEX = "32025R0040"
CELEX_RESOLVER = f"http://publications.europa.eu/resource/celex/{CELEX}"

HEADERS = {
    "Accept": "application/xhtml+xml",
    "Accept-Language": "eng",
}

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "packaging_waste_state.json")
REPORT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "packaging_waste_report.json")

TAG = re.compile(r"<[^>]+>")


def text_of(html):
    return " ".join(re.sub(TAG, " ", html).split())


def fetch_doc(timeout=45):
    req = urllib.request.Request(CELEX_RESOLVER, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        html = r.read().decode("utf-8", "ignore")
    if "packaging" not in html.lower():
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
        print(f"  FAIL  EU PPWR  {e}")
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            json.dump({"checked_at": now, "error": str(e)}, f, indent=2)
        raise

    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    changed = False

    if prior is None:
        print("  NEW   EU PPWR  baseline recorded")
    elif prior["hash"] != digest:
        changed = True
        print("  CHANGED  EU PPWR  — review")
    else:
        print(f"  OK    EU PPWR  unchanged since {prior['checked_at']}")

    save_state({"hash": digest, "checked_at": now})
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump({"checked_at": now, "changed": changed, "celex": CELEX}, f, indent=2)


if __name__ == "__main__":
    main()
