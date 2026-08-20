# California Prop 65 (OEHHA)

State-level heavy metal/carcinogen list. ~826 chemicals, structured table (name, CAS, listing mechanism, date, NSRL/MADL). California is a large enough single-state market to track independently even though it's not federal.

## Access — verified 2026-08-20

The listing page (oehha.ca.gov/proposition-65/proposition-65-list) is behind an Incapsula bot challenge — returns a 200 with an empty JS-redirect stub, no content. The actual data file isn't gated: OEHHA serves the current list at a **stable, non-dated** Excel URL —
`https://oehha.ca.gov/sites/default/files/media/downloads/proposition-65/p65chemicalslist.xlsx` — plain request works, no WAF. (A dated CSV also exists but its path changes on every republish, e.g. `/media/2025-01/...` — don't hardcode that one.)

Header row is at worksheet row 12 in the current layout (6 rows of preamble text above it). If OEHHA changes the preamble length this shifts — `formulation/prop65_fetcher.py` checks for it and fails loudly rather than silently misreading columns.

## Fetch approach

Implemented: `formulation/prop65_fetcher.py`. Structured source, so the diff is real added/removed chemical detection (keyed by CAS number, falling back to name for the handful of multi-substance listings with no CAS) — not just a hash flag like the ECHA source. State committed in `prop65_state.json`.
