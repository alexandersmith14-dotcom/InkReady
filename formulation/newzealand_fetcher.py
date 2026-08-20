"""New Zealand tattoo ink tracker — EPA Group Standard under HSNO.

Fixes a real gap: NZ was bundled with Australia in this project's original
scoping ("Australia/NZ, AICIS") but AICIS is Australia-only — NZ has its own
separate regulator, the Environmental Protection Authority (EPA), under the
Hazardous Substances and New Organisms Act 1996 (HSNO Act). Never actually
researched until this fetcher was built.

Unlike Australia (confirmed no binding restriction) or the UK (restriction
proposed but never enacted), NZ has a REAL, IN-FORCE substance restriction:
the Tattoo and Permanent Makeup Substances Group Standard 2020 (HSR100580,
amended 2022-11-24) — concentration limits on PAHs, heavy metals, aromatic
amines (<5ppm), and colouring agents (<0.1% by weight). Genuinely comparable
in kind to EU Annex XVII, just a different country's version of the same
idea.

EPA's own guidance pages (epa.govt.nz/industry-areas/... and
epa.govt.nz/hazardous-substances/...) are Incapsula-walled — same bot
challenge as OEHHA's Prop 65 page and Queensland Health. But the actual
Group Standard PDF, hosted as a direct asset file rather than served through
the page, is NOT gated — same pattern as OEHHA's xlsx file bypassing its own
blocked listing page. Hash-diffed like the ECHA fetcher (a legal document
that rarely changes, not a stream of new items), but needs PDF text
extraction (PyMuPDF) rather than HTML parsing.
"""

import hashlib
import json
import os
import time
import urllib.request
from datetime import datetime, timezone
from io import BytesIO

import pymupdf

PDF_URL = ("https://www.epa.govt.nz/assets/RecordsAPI/"
           "Tattoo-and-Permanent-Makeup-Substances-Group-Standard-2020_HSR100580-Amended-August-2022.pdf")

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "newzealand_state.json")
REPORT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "newzealand_report.json")


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


def fetch_text(timeout=45):
    req = urllib.request.Request(PDF_URL, headers=UA)
    data = fetch_with_retry(req, timeout)
    doc = pymupdf.open(stream=BytesIO(data), filetype="pdf")
    text = "".join(page.get_text() for page in doc)
    if "tattoo" not in text.lower() or "HSNO" not in text:
        raise RuntimeError("fetched PDF doesn't look right (source may have changed)")
    return text


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
        text = fetch_text()
    except Exception as e:
        print(f"  FAIL  NZ EPA Group Standard  {e}")
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            json.dump({"checked_at": now, "error": str(e)}, f, indent=2)
        raise

    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    changed = False

    if prior is None:
        print("  NEW   NZ EPA Group Standard  baseline recorded")
    elif prior["hash"] != digest:
        changed = True
        print("  CHANGED  NZ EPA Group Standard  — review, may mean an amendment")
    else:
        print(f"  OK    NZ EPA Group Standard  unchanged since {prior['checked_at']}")

    save_state({"hash": digest, "checked_at": now})
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "checked_at": now,
            "changed": changed,
            "note": "Tattoo and Permanent Makeup Substances Group Standard 2020 (HSR100580), "
                    "under the Hazardous Substances and New Organisms Act 1996. In force, "
                    "amended 2022-11-24. Concentration limits on PAHs, heavy metals, aromatic "
                    "amines (<5ppm), colouring agents (<0.1% by weight).",
        }, f, indent=2)


if __name__ == "__main__":
    main()
