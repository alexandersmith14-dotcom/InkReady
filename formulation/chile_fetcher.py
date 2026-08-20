"""Chile tattoo ink tracker — ISP Sanitary Control Regime.

Real, current find from the "full sweep on the rest of the world" pass: on
2025-08-28 Chile's Instituto de Salud Pública (ISP, under the Ministry of
Health) published Resolución Exenta E6717-25, formally determining a
"Régimen de Control Sanitario" (sanitary control regime) for tattoo inks
(TINTAS PARA TATUAJES) — a pharmaceutical-adjacent registration model,
similar in spirit to Brazil's ANVISA (see formulation/sources/brazil.md).
Genuinely new (evaluation dated July 2025), not a long-standing law that was
simply missed.

The PDF is hosted as a direct asset on ispch.cl and is NOT gated — plain
request works, no WAF/Incapsula/Cloudflare block encountered (unlike most of
the other Latin American/harder-to-reach sources in this repo). Hash-diffed
via PyMuPDF text extraction, same shape as the ECHA and NZ fetchers — a
legal document that rarely changes.
"""

import hashlib
import json
import os
import urllib.request
from datetime import datetime, timezone
from io import BytesIO

import pymupdf

PDF_URL = ("https://www.ispch.cl/wp-content/uploads/resoluciones/"
           "35847_RESOL.%20EX.%20E6717-25%20-%20TINTAS%20PARA%20TATUAJES.pdf")

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chile_state.json")
REPORT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chile_report.json")


def fetch_text(timeout=45):
    req = urllib.request.Request(PDF_URL, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    doc = pymupdf.open(stream=BytesIO(data), filetype="pdf")
    text = "".join(page.get_text() for page in doc)
    if "tatuaje" not in text.lower():
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
        print(f"  FAIL  Chile ISP resolution  {e}")
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            json.dump({"checked_at": now, "error": str(e)}, f, indent=2)
        raise

    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    changed = False

    if prior is None:
        print("  NEW   Chile ISP resolution  baseline recorded")
    elif prior["hash"] != digest:
        changed = True
        print("  CHANGED  Chile ISP resolution  — review, may mean an amendment")
    else:
        print(f"  OK    Chile ISP resolution  unchanged since {prior['checked_at']}")

    save_state({"hash": digest, "checked_at": now})
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "checked_at": now,
            "changed": changed,
            "note": "Resolución Exenta E6717-25 (ISP), published 2025-08-28 — establishes a "
                    "Sanitary Control Regime for tattoo inks in Chile. Registration-based model, "
                    "similar in spirit to Brazil's ANVISA.",
        }, f, indent=2)


if __name__ == "__main__":
    main()
