# South Korea — Tattooist Act (문신사법)

Korea passed a real law legalizing and licensing non-medical tattooists after 33 years of tattooing being medical-professional-only: **Law No. 21070**, promulgated 2025-10-28. It requires a national licensing exam (run by the Ministry of Health and Welfare, not the drug/cosmetics regulator MFDS), hygiene/safety training, and record-keeping of each procedure including the type and quantity of ink used.

**Not a substance restriction list** — no EU-Annex-XVII-style ink ingredient ban was found in it. **Not yet in force** — it takes effect **2027-10-29**, two years after promulgation. Same "passed but dormant" situation as [UK REACH's tattoo ink restriction](uk_reach.md), just with a known future date instead of open-ended limbo.

## Access — verified 2026-08-20

`law.go.kr` (Korea's official law database) is genuinely reachable, unlike most of the other blocked hosts in this repo (ECHA, EUR-Lex, ANVISA, Canada's Hotlist, Australia's AICIS) — but intermittently flaky (SSL connect errors observed, cleared on a plain retry), so the fetcher uses the same retry-with-backoff shape as the others.

Note: Korea's official law Open API (`law.go.kr/DRF/...`) requires an API key from user registration — not something to set up without asking. Used the plain law detail page instead, which needs no key.

## Fetch approach

Implemented: `formulation/korea_fetcher.py`. Hash-diff on the law's enactment page — the text itself rarely changes, so the signal is "did this page change" (an amendment, or eventually the transition from pending to in-force as the 2027 date approaches), not a stream of new items. Same pattern as ECHA and UK REACH's HSE status page. Verified live: baseline recorded, rerun confirmed unchanged detection works.
