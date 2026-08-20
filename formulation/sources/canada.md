# Canada — Health Canada

Tattoo ink is regulated as a cosmetic in Canada (explicitly excepted from the general rule that injected products aren't cosmetics). The Canadian equivalent of EU Annex XVII is the **Cosmetic Ingredient Hotlist** — ~500 prohibited/restricted substances.

## Access — verified 2026-08-20

**Hotlist itself: not machine-accessible.** The canada.ca page hosting it consistently times out on a plain request — 5/5 attempts over ~40-45s each with zero response body, an Akamai-style tarpit. Not a clean 403 like ECHA/EUR-Lex, but the same practical effect. No CSV/JSON/API version exists anywhere, including Canada's own open data portal (open.canada.ca — searched directly via its CKAN API, not published there). This is a documented gap, not a workaround — same precedent as Klearance leaving FFIEC/NYDFS out rather than fetching them.

**What IS reachable:** Health Canada's **Recalls & Safety Alerts** open dataset, on a different subdomain (`recalls-rappels.canada.ca`) that isn't gated — plain request works, ~34,000 recalls across every consumer product category, JSON/CSV both available. Filtered to title/product/issue text containing "tattoo," this surfaces real signal: e.g. a 2024 recall of Bloodline brand Tattoo Pigments for microbial contamination. Enforcement/recall radar, same spirit as the EU Safety Gate source in `commerce/`, not a formulation restriction list.

## Fetch approach

Implemented: `formulation/canada_fetcher.py`. New-item diff on tattoo-keyword-matched recalls (3 currently, out of ~34k total scanned). Verified live: baseline recorded, rerun confirmed 0 false positives. The Hotlist gap is recorded in every report's `hotlist_note` field rather than silently omitted.
