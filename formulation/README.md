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
| [ANVISA](sources/brazil.md) | Brazil | Tracked (via DOU search, no direct API) | ANVISA registry/legal-text hosts unreachable; DOU search for ANVISA resolutions instead |
| Japan / Korea / China | Various | Status-only | Often customs-level restriction rather than dedicated ink law — absence of a feed is itself tracked, not silently skipped |

"Status-only" sources show as a tracked/not-tracked flag rather than a monitored feed until built out.
