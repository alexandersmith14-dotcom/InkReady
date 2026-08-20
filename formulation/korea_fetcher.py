"""South Korea tattoo ink tracker — the Tattooist Act (문신사법).

Korea passed a real law (Law No. 21070, promulgated 2025-10-28) legalizing
and licensing non-medical tattooists after 33 years of tattooing being
medical-professional-only. It requires a national licensing exam (run by the
Ministry of Health and Welfare, not the drug/cosmetics regulator MFDS),
hygiene/safety training, and record-keeping of each procedure including the
type and quantity of ink used. It is NOT a substance restriction list — no
Annex-XVII-style ink ingredient ban was found in it — and it is NOT YET IN
FORCE: it takes effect 2027-10-29, two years after promulgation. Same
"passed but dormant" situation as UK REACH's tattoo ink restriction, just
with a known future date instead of open-ended limbo.

law.go.kr (Korea's official law database) is genuinely reachable, unlike
most of the other blocked hosts in this repo (ECHA, EUR-Lex, ANVISA, Canada's
Hotlist, Australia's AICIS) — but intermittently flaky (SSL connect errors
observed, cleared on retry), so this uses the same retry-with-backoff shape
as the other fetchers here.

Hash-diffed like the ECHA and UK REACH HSE-status sources: the law's own
text rarely changes, so the signal is "did this page change" (an amendment,
or eventually the transition from pending to in-force as the 2027 date
approaches), not a stream of new items.
"""

import hashlib
import json
import os
import re
import time
import urllib.request
from datetime import datetime, timezone

LAW_URL = "https://law.go.kr/LSW/lsRvsDocListP.do?lsId=014953&chrClsCd=010202&lsRvsGubun=all"

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "korea_state.json")
REPORT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "korea_report.json")

TAG = re.compile(r"<[^>]+>")


def text_of(html):
    return " ".join(re.sub(TAG, " ", html).split())


def fetch_with_retry(url, attempts=5, pause=5, timeout=30):
    last_err = None
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception as e:
            last_err = e
            if attempt < attempts - 1:
                time.sleep(pause * (2 ** attempt))
    raise RuntimeError(f"failed after {attempts} attempts: {last_err}")


def fetch_law_text():
    html = fetch_with_retry(LAW_URL)
    if "문신사법" not in html:
        raise RuntimeError("fetched page doesn't mention 문신사법 — layout or law ID may have changed")
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
        text = fetch_law_text()
    except Exception as e:
        print(f"  FAIL  Korea Tattooist Act  {e}")
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            json.dump({"checked_at": now, "error": str(e)}, f, indent=2)
        raise

    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    changed = False

    if prior is None:
        print("  NEW   Korea Tattooist Act  baseline recorded")
    elif prior["hash"] != digest:
        changed = True
        print("  CHANGED  Korea Tattooist Act  — review, may mean an amendment or the "
              "2027-10-29 in-force transition")
    else:
        print(f"  OK    Korea Tattooist Act  unchanged since {prior['checked_at']}")

    save_state({"hash": digest, "checked_at": now})
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "checked_at": now,
            "changed": changed,
            "note": "Law No. 21070, promulgated 2025-10-28, takes effect 2027-10-29. Not a "
                    "substance restriction list — a tattooist licensing regime. Tracked via "
                    "hash-diff since the text itself rarely changes.",
        }, f, indent=2)


if __name__ == "__main__":
    main()
