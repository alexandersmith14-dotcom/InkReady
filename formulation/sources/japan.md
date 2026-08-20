# Japan — confirmed gap, no fetcher

**No dedicated tattoo ink regulation exists.** Confirmed via e-Gov (Japan's official law database) full-text search API — a real, working, ungated API covering the entire body of Japanese law — not assumed from secondary sources.

## Research — verified 2026-08-20

Searched e-Gov (`laws.e-gov.go.jp/api/2/keyword`) for multiple terms:

- "タトゥー" (tattoo, katakana loanword) — 0 results.
- "刺青" (irezumi, traditional term) — 0 results.
- "タトゥーインク" (tattoo ink) — 0 results.
- "入れ墨" (tattoo, alternate traditional term) — 10 results, but all irrelevant on inspection: Installment Sales Act, Specified Commercial Transactions Act, the Act on Prevention of Unjust Acts by Organized Crime Group Members (mentions tattoos as an identifying mark of yakuza members), and an agricultural chattel mortgage registration rule. None regulate tattoo ink or pigments.

Separately confirmed: in April 2022 Japan's Ministry of Health, Labour and Welfare excluded tattooing needles and machines from medical device classification — the general regulatory trend is toward *less* tattoo-specific oversight, not more.

No recall/enforcement fallback found either — `recall.go.jp` doesn't resolve (DNS failure) and the Consumer Affairs Agency's product recall page 403'd on a plain request.

## Conclusion

Genuine regulatory gap, not a reachability problem — the e-Gov full-text search is authoritative and ungated, and it found nothing. No fetcher built. Revisit only if Japan legislates something new (same trigger condition as any other gap in this repo).
