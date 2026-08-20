"""US hazmat shipping classification tracker — PHMSA rulemaking.

Some pigments used in tattoo ink classify as dangerous goods for transport,
a question separate from whether the formulation itself is legal (see
formulation/). Scoped to the US: PHMSA (Pipeline and Hazardous Materials
Safety Administration) sets the DOT Hazardous Materials Table via the same
Federal Register API already used for formulation/mocra_fetcher.py — ungated,
reliable, proven.

IATA's Dangerous Goods Regulations (DGR) and the IMO's IMDG Code (for air and
sea transport respectively) are NOT tracked here — both are commercial/
international-body publications with no open API or feed found. Their new
editions get announced but aren't fetchable the way a government rulemaking
feed is. Documented as reference-only in commerce/sources/hazmat.md, not
worked around.
"""

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone

FEDREG_API = "https://www.federalregister.gov/api/v1/documents.json"
FEDREG_FIELDS = ["title", "publication_date", "type", "html_url", "abstract", "document_number"]

AGENCY = "pipeline-and-hazardous-materials-safety-administration"
# Quoted deliberately — an unquoted multi-word term is OR-of-words on this
# API, not a phrase (see formulation/mocra_fetcher.py for the bug this caused
# there). "hazardous materials table" is the core DOT hazmat classification
# list; pigments/dyes/paint entries live inside it.
SEARCH_TERM = '"hazardous materials table"'

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hazmat_state.json")
REPORT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hazmat_report.json")


def fetch_items(timeout=45):
    query = {
        "conditions[agencies][]": AGENCY,
        "conditions[term]": SEARCH_TERM,
        "order": "newest",
        "per_page": "100",
        "fields[]": FEDREG_FIELDS,
    }
    url = FEDREG_API + "?" + urllib.parse.urlencode(query, doseq=True)
    with urllib.request.urlopen(url, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8"))
    results = data.get("results") or []
    if not results:
        raise RuntimeError("0 results — API or query may be broken")
    return {
        d["document_number"]: {
            "document_number": d["document_number"],
            "title": d.get("title", ""),
            "date": d.get("publication_date", ""),
            "type": d.get("type", ""),
            "url": d.get("html_url", ""),
        }
        for d in results if d.get("document_number")
    }


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
        current = fetch_items()
    except Exception as e:
        print(f"  FAIL  US Hazmat (PHMSA)  {e}")
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            json.dump({"checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                       "error": str(e)}, f, indent=2)
        raise

    new_items = [v for k, v in current.items() if prior is None or k not in prior]

    if prior is None:
        print(f"  NEW   US Hazmat (PHMSA)  baseline recorded — {len(current)} documents")
    else:
        print(f"  OK    US Hazmat (PHMSA)  {len(current)} documents, {len(new_items)} new")
        for i in new_items:
            print(f"    + [{i['date']}] {i['title']}")

    save_state(current)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "total_documents": len(current),
            "new_items": new_items,
            "note": "US (PHMSA/DOT) only. IATA DGR and IMO IMDG Code are commercial/"
                    "international-body publications with no open API found — not tracked.",
        }, f, indent=2)


if __name__ == "__main__":
    main()
