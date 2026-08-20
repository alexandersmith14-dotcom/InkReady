# Australia — AICIS / Product Safety Australia

**No binding federal restriction list exists.** Confirmed by research, not assumed: Australia relies on voluntary compliance and occasional government characterisation studies for tattoo ink safety. AICIS (the federal industrial chemicals regulator) publishes consumer guidance on tattoo/PMU inks but doesn't restrict specific substances the way EU Annex XVII does. Queensland is the first state moving toward EU-aligned pigment rules, but as of this writing it's still at the public-consultation stage — not in force.

## Access — verified 2026-08-20

None of the primary government pages are reachable with a plain request:

- `industrialchemicals.gov.au` (AICIS) — times out, 2/2 attempts, ~40s each.
- `health.qld.gov.au` — 403.
- `legislation.qld.gov.au` — connection failure.

All three documented as gaps here, not worked around — same precedent as Klearance leaving FFIEC/NYDFS out, and this repo's own Canada/UK sources.

**What IS reachable:** the ACCC's Product Safety Australia recall RSS feed — `productsafety.gov.au/rss/feed.xml/psa_recall`. Plain request works, no gate. Filtered to "tattoo" in title/description, same recall/enforcement radar pattern as the Canada and EU Safety Gate sources.

## Fetch approach

Implemented: `formulation/australia_fetcher.py`. New-item diff on tattoo-keyword-matched recalls. Currently 0 matches in the visible recent window (100 items) — a legitimate finding, not a fetch failure; the value is catching the first one that appears. Verified live: baseline recorded, rerun confirmed correct 0-match-but-checked state (this required a real fix — see below).

**Bug found and fixed during build:** the original diff logic used `if not prior` to distinguish "never run" from "ran before," which is wrong when a legitimate result is an empty dict — a 0-match baseline could never graduate to "OK, still zero" on the next run, it just kept reporting "NEW baseline" forever. Fixed by having `load_state()` return `None` (not `{}`) when the state file doesn't exist yet, and checking `prior is None` instead of `not prior`. Same latent bug existed in `canada_fetcher.py` (masked there because it found 3 matches, never actually zero) — fixed there too.
