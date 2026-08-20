# REACH Title II — EU importer registration

Importing into the EU above 1 tonne/year of a substance triggers a REACH Title II registration duty, separate from the Annex XVII Entry 75 formulation restriction ([formulation/sources/echa_annex_xvii.md](../../formulation/sources/echa_annex_xvii.md)).

## Why this isn't a live fetcher

Checked 2026-08-20: the base REACH Regulation (CELEX 32006R1907) doesn't resolve via the Cellar content-negotiation technique used elsewhere in this repo (404) — REACH has been amended so many times that the "original" CELEX doesn't serve a coherent current document the way a single amending regulation does. Even if it resolved, Title II itself (the registration mechanism, the 1 tonne threshold) is core structural regulation that's rarely amended — unlike Annex XVII's substance table, which changes often enough to be worth hash-diffing. Whole-document hash-diffing REACH would mostly just re-detect the Annex XVII changes already tracked separately.

**Static fact, not a feed:** the >1 tonne/year threshold is the operative number. No live tracking here; revisit only if there's reason to think the threshold itself has changed (rare — this would be major EU chemicals policy news, not something that needs daily polling).
