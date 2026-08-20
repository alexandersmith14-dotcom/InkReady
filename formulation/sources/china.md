# China — confirmed gap, no fetcher

**No dedicated tattoo ink regulation exists.** Confirmed via two independent research angles, not assumed.

## Research — verified 2026-08-20

**Cosmetics regulation angle:** China's NMPA regulates cosmetics under two tracks — 特殊化妆品 (special cosmetics, registration-required) and 普通化妆品 (general cosmetics, filing-required). Searched for tattoo pigment (纹身颜料) coverage under either track — no dedicated provision found. Tattoo ink is not classified under China's cosmetics framework at all.

**Customs/import angle:** China does regulate imported hazardous chemicals generally (batch-by-batch inspection, hazard classification declarations, Chinese-language SDS requirements) — but this is a generic chemical-import regime that would apply to any hazardous substance, not a tattoo-ink-specific rule. No tattoo-ink-specific customs restriction found.

## Access notes

- `www.nmpa.gov.cn` returns 412 (Precondition Failed) on a plain request — likely a missing-header WAF-lite check, not fully investigated further since the cosmetics-framework research already showed no tattoo-specific content to look for.
- `flk.npc.gov.cn` (China's official law database) is reachable (200) but is a JS-rendered SPA — the real search API wasn't found without HAR-capture-style reverse engineering (same category of effort as [Brazil's DOU source](brazil.md)), not attempted here since there's no confirmed regulatory content to justify it.
- `samr.gov.cn` (product recalls) is reachable at the root but no direct recall-listing path was found in a quick check.

## Conclusion

Genuine regulatory gap on the strongest available evidence (two independent angles both came up empty), though less exhaustively confirmed than [Japan's](japan.md) — China's actual law database wasn't fully searchable due to its JS-SPA frontend. No fetcher built. Worth a deeper pass (RAE-style HAR capture on `flk.npc.gov.cn`) only if there's reason to suspect content exists that this research missed.
