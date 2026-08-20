"""Brazil tattoo ink tracker — ANVISA resolutions via the Diario Oficial (DOU).

Brazil regulates tattoo ink differently from the EU/US model: RDC 55/2008
(in force since 2010, amended by RDC 64/2016) classifies tattoo pigments as
high-risk implantable products requiring individual ANVISA registration —
closer to a premarket-approval regime than a substance restriction list.
ANVISA has "update the regulatory framework for tattoo pigments" listed as a
2026-2027 priority.

None of ANVISA's own structured access points are reachable:
- consultas.anvisa.gov.br (product registry API) — Cloudflare hard block.
- bvsms.saude.gov.br (the RDC 55/2008 legal text host) — TLS-level connection
  reset on every attempt, not just a timeout.
- dados.gov.br (Brazil's open data portal) — 401, requires auth now.

What worked instead: the Diario Oficial da Uniao (DOU) search itself. It
looks like a JS-rendered SPA, but the search results are actually embedded
server-side in a <script type="application/json"> tag on the same page — no
separate XHR/API call needed, just a plain GET and a regex extraction. Found
via reverse-api-engineer (a local HAR-capture-and-generate tool) after the
DOU's own in-app search box was investigated; verified independently here.

The DOU backend itself is genuinely flaky (Azion CDN, intermittent 502s
unrelated to request rate — a fresh single request can 502 then succeed on
retry with no change in approach), so this uses the same retry-with-backoff
shape as Klearance's fetch_with_retry for exactly this kind of transient
failure. Filtered to hierarchy_str containing "Vigilância" (ANVISA/Ministry
of Health) to drop noise from unrelated ministries that also happen to use
the word "tatuagem" in unrelated documents (verified against real data:
Ministério da Cultura grant notices, a labor union notice, a Ministry of
Defense edital all showed up in the raw search and don't belong).
"""

import json
import os
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BASE_URL = "https://www.in.gov.br"
SEARCH_PATH = "/consulta/-/buscar/dou"

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "brazil_state.json")
REPORT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "brazil_report.json")

RELEVANT_HIERARCHY = "vigilância"  # matches "Agência Nacional de Vigilância Sanitária" (ANVISA)

JSON_SCRIPT = re.compile(
    r'<script[^>]*id="_br_com_seatecnologia_in_buscadou_BuscaDouPortlet_params"'
    r'[^>]*type="application/json"[^>]*>\s*(\{.*?\})\s*</script>',
    re.DOTALL,
)
JSON_SCRIPT_FALLBACK = re.compile(
    r'id="_br_com_seatecnologia_in_buscadou_BuscaDouPortlet_params"[^>]*>\s*(\{[^<]*\})\s*</script>',
    re.DOTALL,
)


def build_search_url(query, page=1, page_size=20):
    params = {"q": query, "s": "todos", "exactDate": "all", "sortType": 0,
              "delta": page_size, "currentPage": page}
    return f"{BASE_URL}{SEARCH_PATH}?{urllib.parse.urlencode(params)}"


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


def parse_results(html):
    match = JSON_SCRIPT.search(html) or JSON_SCRIPT_FALLBACK.search(html)
    if not match:
        raise RuntimeError("embedded search JSON not found — DOU page layout may have changed")
    raw = match.group(1).replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("\\/", "/")
    data = json.loads(raw)
    return data.get("jsonArray", [])


def fetch_anvisa_tattoo_items(query="tatuagem"):
    html = fetch_with_retry(build_search_url(query))
    items = parse_results(html)
    if not items:
        raise RuntimeError(f"0 results for '{query}' — expected at least some (query itself may be broken)")

    relevant = {}
    for item in items:
        hierarchy = (item.get("hierarchyStr") or "").lower()
        if RELEVANT_HIERARCHY not in hierarchy:
            continue
        class_pk = item.get("classPK")
        if not class_pk:
            continue
        url_title = item.get("urlTitle", "")
        relevant[class_pk] = {
            "class_pk": class_pk,
            "title": (item.get("title") or "").strip(),
            "pub_date": item.get("pubDate", ""),
            "hierarchy": item.get("hierarchyStr", ""),
            "url": f"{BASE_URL}/web/dou/-/{url_title}" if url_title else "",
        }
    return relevant


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
        current = fetch_anvisa_tattoo_items()
    except Exception as e:
        print(f"  FAIL  Brazil ANVISA/DOU  {e}")
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            json.dump({"checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                       "error": str(e)}, f, indent=2)
        raise

    new_items = [v for k, v in current.items() if prior is None or k not in prior]

    if prior is None:
        print(f"  NEW   Brazil ANVISA/DOU  baseline recorded — {len(current)} ANVISA tattoo-related resolutions")
    else:
        print(f"  OK    Brazil ANVISA/DOU  {len(current)} tracked, {len(new_items)} new")
        for i in new_items:
            print(f"    + [{i['pub_date']}] {i['title']}")

    save_state(current)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "total_tracked": len(current),
            "new_items": new_items,
            "note": "ANVISA's own product registry, legal text host, and Brazil's open data "
                    "portal are all unreachable — this tracks DOU search results for ANVISA "
                    "resolutions mentioning 'tatuagem' instead, filtered by organization "
                    "hierarchy. DOU's backend (Azion CDN) is intermittently flaky — a FAIL here "
                    "may just mean retry exhaustion, not a real change in the source.",
        }, f, indent=2)


if __name__ == "__main__":
    main()
