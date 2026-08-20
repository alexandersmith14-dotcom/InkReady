# Professional-only sale & age-restricted sale — not automated, and not verified yet

**Honest status as of 2026-08-20: these two checklist items were carried over from the original scoping conversation as general claims ("some jurisdictions restrict ink sale to licensed tattoo artists/studios," "age-restricted sale applies in some states/countries") — neither has actually been verified against real law for any specific jurisdiction.** Unlike every other source in this repo, nothing here has been confirmed real or confirmed a gap.

## Why this one's different from the rest

Every other "not automated" item in this repo (REACH Title II, SDS/GHS, IATA/IMDG) was checked and found to be either a static fact or a source with no accessible feed — a real finding either way. This item hasn't had that pass yet. Doing it properly means per-jurisdiction legal research (which US states, which countries) — the same scale of work as the Japan/Korea/China research, but potentially across dozens of jurisdictions instead of three, since "professional-only sale of ink" is a distinct legal question from "who can perform tattooing" (already covered by licensing law in most places) and would need separate verification.

## What would need to happen to automate this properly

1. Confirm, jurisdiction by jurisdiction (starting with markets already covered: EU member states, US states, UK, Canada, Australia, Brazil, Korea), whether a real professional-only-sale or age-restricted-sale law exists for tattoo ink specifically.
2. For any jurisdiction where one is confirmed, find its actual source and decide fetcher vs. static reference the same way every other source here was evaluated.
3. Build a `sale_restrictions.py` reference table (Klearance's `regref.py` pattern — a maintained lookup, not necessarily a live diff, since these facts likely change rarely once established) once the facts are real.

Flagged here explicitly rather than silently building a table with unverified claims baked into it.
