# Chile — ISP Sanitary Control Regime

Found during the "full sweep on the rest of the world" pass (2026-08-20), not part of the original scoping — and genuinely new, not a long-standing law that was missed. On **2025-08-28** Chile's Instituto de Salud Pública (ISP, under the Ministry of Health) published **Resolución Exenta E6717-25**, formally determining a "Régimen de Control Sanitario" (sanitary control regime) for tattoo inks (TINTAS PARA TATUAJES) — evaluation dated July 2025. Registration-based model, similar in spirit to Brazil's ANVISA (see [brazil.md](brazil.md)).

## Access — verified 2026-08-20

The resolution PDF is hosted as a direct asset on `ispch.cl` and is **not gated** — plain request works, no WAF/Incapsula/Cloudflare block encountered. Notably easier to reach than most of the other Latin American sources checked during this project.

## Fetch approach

Implemented: `formulation/chile_fetcher.py`. Hash-diff via PyMuPDF text extraction, same pattern as the ECHA and NZ fetchers. Verified live: baseline recorded, rerun confirmed unchanged detection works.
