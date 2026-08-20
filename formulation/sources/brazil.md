# Brazil — ANVISA

Brazil regulates tattoo ink differently from the EU/US model: **RDC 55/2008** (in force since 2010, amended by RDC 64/2016) classifies tattoo pigments as high-risk implantable products requiring individual ANVISA registration — closer to a premarket-approval regime than a substance restriction list. ANVISA has "update the regulatory framework for tattoo pigments" listed as a 2026-2027 priority.

## Access — verified 2026-08-20

None of ANVISA's own structured access points are reachable:

- `consultas.anvisa.gov.br` (the product registry API) — Cloudflare hard block ("you have been blocked").
- `bvsms.saude.gov.br` (the RDC 55/2008 legal text host) — TLS-level connection reset on every attempt (server closes the connection abruptly right after the request, not a timeout).
- `dados.gov.br` (Brazil's open data portal, CKAN-based) — 401, requires auth now.

**What worked instead:** the Diario Oficial da Uniao (DOU) search itself, at `in.gov.br/consulta/-/buscar/dou`. It looks like a JS-rendered SPA, but the search results are actually embedded server-side in a `<script type="application/json" id="_br_com_seatecnologia_in_buscadou_BuscaDouPortlet_params">` tag on the same page — a plain GET plus regex extraction, no separate XHR/API call needed. Found using [reverse-api-engineer](https://github.com/kalil0321/reverse-api-engineer) (a local HAR-capture tool at `C:\Users\alexa\OneDrive\Documents 1\Default Project\reverse-api-engineer`) after RAE's own automated test run hit repeated 502s and didn't cleanly finish — the generated client was still correct, just needed retry-with-backoff wrapped around it, verified independently.

**The DOU backend is genuinely flaky** — Azion CDN, intermittent 502s that clear on a plain retry with no change in approach (confirmed: same request failed 3x in a row, then a fresh attempt seconds later worked). Not bot-blocking (the error page is a generic Azion default-error page, not a challenge page) — real backend instability. Handled with the same retry-with-backoff shape as Klearance's `fetch_with_retry`.

Searching "tatuagem" returns results from unrelated ministries too (Ministério da Cultura grant notices, a labor union notice, a Ministry of Defense edital all showed up in the raw 20-result sample) — filtered to `hierarchyStr` containing "Vigilância" (matches "Agência Nacional de Vigilância Sanitária" / ANVISA), which cleanly separates real ANVISA hits from noise. Verified against real data: 14 of 20 raw results were genuinely ANVISA (mostly `RESOLUÇÃO-RE` individual product registrations under RDC 55/2008, dated as recently as August 2026).

## Fetch approach

Implemented: `formulation/brazil_fetcher.py`. New-item diff keyed by DOU's internal `classPK`, retry-with-backoff (5 attempts, exponential 5/10/20/40s) around the flaky backend. Verified live: baseline recorded (14 items), rerun confirmed 0 false positives.
