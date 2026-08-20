# SDS provision & MOCRA facility registration

Two checklist items that reuse work already done elsewhere in this repo, documented here rather than rebuilt.

## SDS provision

B2B sale to studios/distributors requires a safety data sheet in most markets, formatted per the GHS (Globally Harmonized System). GHS itself is revised biennially by UNECE — `unece.org` returned 403 on a plain request (checked 2026-08-20), same as the hazmat check. No open API or feed found for GHS revision announcements. Reference-only: check the current GHS revision manually when formatting SDS documents.

## MOCRA facility registration + product listing

This checklist item ("required for anyone selling under their own brand in the US") is **already tracked** — `formulation/mocra_fetcher.py` searches the Federal Register for `"cosmetic product facility registration"` as one of its three terms, and that's the exact same registration requirement this commerce checklist item refers to. No separate fetcher needed here; see [formulation/sources/mocra.md](../../formulation/sources/mocra.md) for the live tracking, and the dashboard's MOCRA/FDA card for current status.
