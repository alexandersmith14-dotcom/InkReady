# UK REACH — tattoo ink restriction

**No restriction currently in force.** UK REACH did NOT carry over the EU's Annex XVII Entry 75 restriction as retained law after Brexit. Do not assume UK obligations mirror the EU — see [echa_annex_xvii.md](echa_annex_xvii.md).

## Timeline (verified 2026-08-20)

- 2021-04-29: Defra asked HSE (the UK REACH agency) to prepare a restriction dossier.
- 2023-06-08: HSE published its recommendation — looser than the EU restriction in scope, per public commentary. Proposed a 2-year transition + 1 year of stock use-up, targeting ~2027 full compliance.
- As of 2026-08-20: still awaiting a Defra ministerial decision. No statutory instrument has been made. Three years since the recommendation, no legal text exists to track.

## Access — verified 2026-08-20

Two sources, both reachable with a plain request, no WAF:

- **HSE restriction status page** — `consultations.hse.gov.uk/crd-reach/reach-restriction-tattoo-ink-pmu-substances/` (note the trailing slash; without it, 302s). Authoritative live status — hash-diffed like the ECHA fetcher.
- **legislation.gov.uk Atom search**, title-scoped to "REACH" — `legislation.gov.uk/uksi?title=REACH`. Full-text search alone ("tattoo") is too broad — it matches livestock ear-tattoo identification regulations (sheep/goats marking), not ink. Title-scoping to "REACH" gives 15 instruments currently, a workable watch list. Each new item's full text is checked for "tattoo" as a triage signal, but flagged regardless — the eventual restriction SI might not use that exact word in its operative text, so this isn't a substitute for a human reading new REACH SIs.

## Fetch approach

Implemented: `formulation/uk_reach_fetcher.py`. Two independent checks in one script — HSE page hash-diff, UK SI new-item diff. Verified live: both baselined clean, rerun confirmed 0 false positives. A recent SI (`The REACH (Amendment) (No. 2) Regulations 2026`, made 2026-07-16) was checked and confirmed unrelated (0 "tattoo" mentions) — the fetcher's auto-triage worked correctly on a real example.
