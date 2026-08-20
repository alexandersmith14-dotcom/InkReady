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

ispch.cl serves a cert from GlobalSign (GCC R6 AlphaSSL CA 2025, a real,
publicly-trusted CA) but OMITS the intermediate from its handshake — worked
fine locally on Windows (which fetches the missing intermediate itself via
the cert's AIA extension) but failed on the GitHub Actions Ubuntu runner
with "unable to get local issuer certificate", since Python/OpenSSL on
Linux won't do that automatically. Same root cause as Klearance's
dob.texas.gov fix (see that repo's fetcher.py _dob_context). We bundle the
intermediate and complete the chain ourselves — this is PROPER verification
against the GlobalSign root in certifi, exactly what a browser does, NOT
verification disabled.
"""

import hashlib
import json
import os
import ssl
import urllib.request
from datetime import datetime, timezone
from io import BytesIO

import certifi
import pymupdf

ISP_HOST = "www.ispch.cl"
ISP_INTERMEDIATE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "certs-globalsign-gcc-r6-alphassl-2025.pem")
# Where to re-fetch the intermediate if the bundled copy is ever missing or
# the CA rotates it. Safe over HTTP: the cert self-verifies by signature.
ISP_AIA = "http://secure.globalsign.com/cacert/gsgccr6alphasslca2025.crt"
_isp_ctx = None


def _isp_context():
    """SSL context that trusts the GlobalSign root (via certifi) AND
    supplies the intermediate the server omits, so the chain verifies.
    Built once; auto-heals from the AIA URL if the bundled intermediate is
    missing (that download is DER, not PEM — converted on the fly)."""
    global _isp_ctx
    if _isp_ctx is not None:
        return _isp_ctx
    ctx = ssl.create_default_context(cafile=certifi.where())
    try:
        ctx.load_verify_locations(ISP_INTERMEDIATE)
    except (FileNotFoundError, ssl.SSLError):
        der = urllib.request.urlopen(ISP_AIA, timeout=30).read()
        cert = ssl.DER_cert_to_PEM_cert(der)
        ctx.load_verify_locations(cadata=cert)
    _isp_ctx = ctx
    return _isp_ctx

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
    with urllib.request.urlopen(req, timeout=timeout, context=_isp_context()) as r:
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
