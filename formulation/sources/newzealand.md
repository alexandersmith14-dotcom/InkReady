# New Zealand — EPA (HSNO Act)

**Fixes a real gap in this project's original scoping**: NZ was bundled with Australia early on ("Australia/NZ, AICIS") but AICIS is Australia-only. NZ has its own separate regulator — the Environmental Protection Authority (EPA) — under the Hazardous Substances and New Organisms Act 1996 (HSNO Act). Never actually researched until 2026-08-20, when the user asked "did we miss any jurisdictions?"

Unlike Australia (confirmed no binding restriction) or the UK (proposed but never enacted), **NZ has a real, in-force substance restriction**: the **Tattoo and Permanent Makeup Substances Group Standard 2020** (HSR100580, amended 2022-11-24). Concentration limits on PAHs, heavy metals, aromatic amines (<5ppm), and colouring agents (<0.1% by weight). Genuinely comparable in kind to EU Annex XVII — just NZ's own version.

Also active: in 2025 the EPA called for information on tattoo ink use/import/supply/manufacture in NZ to review whether the current rules are fit for purpose — the standard may be revised. And separately, from 2026-01-01, all companies handling hazardous chemicals in NZ must register business/product info and file annual quantity reports (a MOCRA-style registration duty, not ink-specific).

## Access — verified 2026-08-20

EPA's own guidance pages are Incapsula-walled (same bot challenge as OEHHA's Prop 65 page and Queensland Health) — both `epa.govt.nz/industry-areas/...` and `epa.govt.nz/hazardous-substances/...` return a 212-byte JS-redirect stub. But the actual Group Standard **PDF**, hosted as a direct asset file (`epa.govt.nz/assets/RecordsAPI/...`) rather than served through the page, is NOT gated — same pattern as OEHHA's xlsx bypassing its own blocked listing page.

## Fetch approach

Implemented: `formulation/newzealand_fetcher.py`. Hash-diff on the PDF's extracted text (PyMuPDF), same pattern as the ECHA fetcher — a legal document that rarely changes, not a stream of new items. Verified live: baseline recorded, rerun confirmed unchanged detection works.
