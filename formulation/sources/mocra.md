# MOCRA (Modernization of Cosmetics Regulation Act, 2022)

Verified 2026-08-20: tattoo ink is in scope. FD&C Act cosmetic definition covers "introduced into" the body; FDA's 2023 draft guidance treats tattoo ink as a cosmetic.

Applies to Solid Ink directly, as both manufacturer and distributor:

- **Facility registration + product listing** required — applies to anyone selling under their own brand, not just formulators.
- **No small-business GMP exemption** — MOCRA excludes injectable cosmetics from the small-business carve-out, and FDA's tattoo guidance calls ink injectable. Full GMP applies regardless of company size.
- Tension flagged in industry/legal commentary: FDA's own microneedling guidance treats anything past the stratum corneum as drug/device territory, but tattoo ink guidance calls it cosmetic anyway — regulatory ground here could still shift, don't treat as permanently settled.

## Access — verified 2026-08-20

No single MOCRA "list" exists — it's an ongoing thread of FDA guidance documents and rulemaking. The **Federal Register API** (federalregister.gov/api/v1/documents.json) is not gated at all — no WAF, plain JSON — and its full-text search finds the right documents directly. Querying the FDA agency for "tattoo" alone surfaces the actual Insanitary Conditions in Tattoo Inks guidance (2023 draft + 2024 final) and the Microneedling guidance that creates the cosmetic-vs-device tension noted above.

## Fetch approach

Implemented: `formulation/mocra_fetcher.py`. Three search terms against the FDA agency (tattoo, cosmetic product facility registration, MOCRA), deduped by document number, new-item diffing — a running feed like Klearance's `fetch_fedreg`, not a hash-diff like the ECHA source. Verified live: 120 documents baselined, rerun confirmed 0 false-positive new items.
