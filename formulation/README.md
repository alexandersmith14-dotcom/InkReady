# formulation/

Tracks what's legally allowed *in* tattoo ink — substance restriction lists. These sources change over time (amendments, new restricted substances) so this module is built as a scrape-and-diff pipeline, not a one-time reference.

## Sources

| Source | Jurisdiction | Status | Access |
|---|---|---|---|
| [ECHA REACH Annex XVII Entry 75](sources/echa_annex_xvii.md) | EU | Primary, tracked | No API — scrape ECHA table page + EUR-Lex consolidated text |
| [MOCRA](sources/mocra.md) | US | Primary, tracked | FDA guidance/registration pages — scrape/monitor |
| [California Prop 65](sources/prop65.md) | US (state) | Secondary, tracked | OEHHA structured list |
| [UK REACH](sources/uk_reach.md) | UK | Tracked (no restriction in force) | HSE status page (hash-diff) + legislation.gov.uk REACH SI watch |
| [Health Canada](sources/canada.md) | Canada | Partial — recalls tracked, Hotlist unreachable | Recalls & Safety Alerts open JSON (tattoo-filtered); Hotlist substance list is blocked at the source, not machine-accessible |
| [AICIS / Product Safety Australia](sources/australia.md) | Australia | Partial — recalls tracked, no binding restriction exists | Product Safety Australia recall RSS (tattoo-filtered); AICIS/Queensland sources unreachable |
| [NZ EPA](sources/newzealand.md) | New Zealand | Tracked | Real in-force restriction (Group Standard 2020, HSR100580) — separate regulator from Australia's AICIS, was missed in original scoping |
| [ANVISA](sources/brazil.md) | Brazil | Tracked (via DOU search, no direct API) | ANVISA registry/legal-text hosts unreachable; DOU search for ANVISA resolutions instead |
| [South Korea](sources/korea.md) | Korea | Tracked (law passed, not yet in force) | Tattooist Act (문신사법), law.go.kr hash-diff, effective 2027-10-29 |
| [Japan](sources/japan.md) | Japan | Confirmed gap | No tattoo ink law found via e-Gov full-text search (authoritative, ungated) |
| [China](sources/china.md) | China | Confirmed gap | No tattoo ink regulation under cosmetics or customs frameworks; law database not fully searchable (JS SPA) |
| [Global recalls (OECD)](global_recalls_fetcher.py) | Multi-country | Tracked | Aggregates recall notices from many national systems into one search — the scalable answer for markets without a dedicated fetcher |
| [Chile](sources/chile.md) | Chile | Tracked | Real, new (2025-08-28) ISP Sanitary Control Regime for tattoo inks — found during the full-world-sweep pass |
| [World survey](sources/world_survey.md) | ~143 other countries | Secondary-source notes only, NOT independently verified | Explains why most countries can't have a dedicated tracker — most genuinely have no regulation |

"Status-only" sources show as a tracked/not-tracked flag rather than a monitored feed until built out.
