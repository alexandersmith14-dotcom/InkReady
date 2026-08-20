"""MOCRA / FDA cosmetic-tattoo-ink guidance tracker.

Unlike ECHA (one legal document) and Prop 65 (one structured chemical list),
there is no single MOCRA "list" to fetch — it's an ongoing thread of FDA
guidance documents, draft/final notices, and rulemaking in the Federal
Register. The Federal Register API (already used elsewhere in the Klearance
codebase for FinCEN/NCUA) is not gated at all — no WAF, no bot challenge,
plain JSON — and its `conditions[term]` full-text search finds the right
documents directly: a query for "tattoo" against the FDA agency alone
surfaces the actual Insanitary Conditions in Tattoo Inks guidance (both the
2023 draft and 2024 final) and the Microneedling guidance that creates the
cosmetic-vs-device tension noted in formulation/sources/mocra.md.

New items are the signal here (a running feed of guidance activity), not a
hash-diff of one document — closer to Klearance's fetch_fedreg than to the
ECHA fetcher.
"""

import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

FEDREG_API = "https://www.federalregister.gov/api/v1/documents.json"
FEDREG_FIELDS = ["title", "publication_date", "type", "html_url", "abstract", "document_number"]

# Two angles: tattoo-ink-specific guidance, and the broader MOCRA facility
# registration/listing thread that applies to Solid Ink as a brand seller
# even when a given notice never says "tattoo".
#
# The multi-word term is quoted deliberately: the Federal Register API treats
# an unquoted multi-word term as an OR of individual words, not a phrase, so
# "cosmetic product facility registration" unquoted matched drug/device user
# fee schedules and tobacco product registration notices on "facility" or
# "registration" alone — pure noise. Quoting forces an exact-phrase match.
SEARCH_TERMS = [
    "tattoo",
    '"cosmetic product facility registration"',
    "MOCRA",
]

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mocra_state.json")
REPORT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mocra_report.json")


def fetch_with_retry(url, timeout, attempts=5, pause=5):
    last_err = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            last_err = e
            if attempt < attempts - 1:
                time.sleep(pause * (2 ** attempt))
    raise RuntimeError(f"failed after {attempts} attempts: {last_err}")


def fetch_term(term, timeout=45):
    query = {
        "conditions[agencies][]": "food-and-drug-administration",
        "conditions[term]": term,
        "order": "newest",
        "per_page": "100",
        "fields[]": FEDREG_FIELDS,
    }
    url = FEDREG_API + "?" + urllib.parse.urlencode(query, doseq=True)
    data = json.loads(fetch_with_retry(url, timeout).decode("utf-8"))
    return data.get("results") or []


def fetch_all():
    seen_ids = set()
    items = []
    for term in SEARCH_TERMS:
        for d in fetch_term(term):
            doc_id = d.get("document_number")
            if not doc_id or doc_id in seen_ids:
                continue
            seen_ids.add(doc_id)
            items.append({
                "document_number": doc_id,
                "title": d.get("title", ""),
                "date": d.get("publication_date", ""),
                "type": d.get("type", ""),
                "url": d.get("html_url", ""),
                "summary": (d.get("abstract") or "")[:500],
            })
    if not items:
        raise RuntimeError("all search terms returned 0 results — API or query may be broken")
    items.sort(key=lambda x: x["date"], reverse=True)
    return items


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)


def main():
    prior = load_state()

    try:
        items = fetch_all()
    except Exception as e:
        print(f"  FAIL  MOCRA/FDA  {e}")
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            json.dump({"checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                       "error": str(e)}, f, indent=2)
        raise

    current = {i["document_number"]: i for i in items}
    new_items = [i for i in items if i["document_number"] not in prior]

    if not prior:
        print(f"  NEW   MOCRA/FDA  baseline recorded — {len(items)} documents")
    else:
        print(f"  OK    MOCRA/FDA  {len(items)} documents, {len(new_items)} new")
        for i in new_items:
            print(f"    + [{i['date']}] {i['title']}")

    save_state(current)

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "total_documents": len(items),
            "new_items": new_items,
        }, f, indent=2)


if __name__ == "__main__":
    main()
