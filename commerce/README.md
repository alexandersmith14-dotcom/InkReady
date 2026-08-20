# commerce/

Rules on *selling and shipping* tattoo ink, distinct from what's legally allowed in the formulation. Relevant to Solid Ink specifically since they're both manufacturer and distributor, shipping to 190+ territories.

Unlike formulation/, not every item here has a single "one government source, changes over time" story — automated where a real reachable source exists, documented honestly where one doesn't. See [checklist.md](checklist.md) for the full list.

## Automated (fetchers)

| Item | Fetcher | Scope |
|---|---|---|
| CLP labeling | [clp_fetcher.py](clp_fetcher.py) | EU |
| Distance-selling rules | [consumer_rights_fetcher.py](consumer_rights_fetcher.py) | EU |
| EPR/packaging waste | [packaging_waste_fetcher.py](packaging_waste_fetcher.py) | EU |
| Hazmat shipping classification | [hazmat_fetcher.py](hazmat_fetcher.py) | US (PHMSA/DOT) |
| Customs/HS code + import duty | [customs_fetcher.py](customs_fetcher.py) | US (HTS) |

## Already covered elsewhere

| Item | Where |
|---|---|
| MOCRA facility registration | `formulation/mocra_fetcher.py` — same source already tracks this |

## Reference only — no live source, or not yet verified

| Item | Why | Details |
|---|---|---|
| REACH Title II | Static fact (>1 tonne/year threshold), base regulation doesn't resolve via Cellar | [sources/reach_title_ii.md](sources/reach_title_ii.md) |
| SDS provision (GHS) | UNECE blocked (403), no open API found | [sources/sds_and_mocra_registration.md](sources/sds_and_mocra_registration.md) |
| IATA DGR / IMO IMDG | Commercial/international-body publications, no open API | [sources/hazmat.md](sources/hazmat.md) |
| Professional-only sale | **Not yet verified for any jurisdiction** — flagged, not faked | [sources/sale_restrictions.md](sources/sale_restrictions.md) |
| Age-restricted sale | **Not yet verified for any jurisdiction** — flagged, not faked | [sources/sale_restrictions.md](sources/sale_restrictions.md) |
