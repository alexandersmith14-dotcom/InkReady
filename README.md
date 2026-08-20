# InkReady

Tattoo ink regulatory compliance tracker for Solid Ink (thesolidink.com). Internal use.

Solid Ink is both a manufacturer and distributor, selling globally (190+ territories, US primary market). Two separate concerns, tracked as two modules:

## Modules

- **[formulation/](formulation/)** — what's legally allowed *in* the ink. Substance restriction lists (EU REACH Annex XVII Entry 75, US MOCRA ingredient rules, California Prop 65). Scrape-and-diff pattern: these sources change periodically and need monitoring, not just a one-time read.
- **[commerce/](commerce/)** — rules on *selling/shipping* the ink. Importer registration, labeling, hazmat shipping, customs. No clean government feed exists for this side — maintained as a curated checklist, reviewed on a schedule rather than auto-diffed.

## Scope

Primary markets: EU, US, UK. Other jurisdictions (Canada, Australia/NZ, Brazil, Japan/Korea/China) tracked at a lighter "status: tracked / not tracked" level rather than full monitoring — see [formulation/sources/](formulation/sources/).

## Brand

Visual direction mimics thesolidink.com — see [assets/brand.md](assets/brand.md).
