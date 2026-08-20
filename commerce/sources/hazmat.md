# Hazmat shipping classification

Some pigments classify as dangerous goods for transport, independent of formulation legality.

## Access — verified 2026-08-20

- **US (DOT/PHMSA)**: tracked. See [hazmat_fetcher.py](../hazmat_fetcher.py) — Federal Register API, same ungated/reliable source as `formulation/mocra_fetcher.py`.
- **IATA Dangerous Goods Regulations (DGR)** — air transport. Commercial publication (IATA sells it), no open API or feed found. New editions are announced but not fetchable.
- **IMO IMDG Code** — sea transport. Published by the International Maritime Organization, biennial amendments. `unece.org` (which hosts related UN Model Regulations content) returned 403 on a plain request; not investigated further since IMDG itself isn't published there.

Both IATA and IMO sources are reference-only here — check their current edition manually when needed, not auto-tracked.
