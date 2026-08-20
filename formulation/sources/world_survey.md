# World survey — secondary-source notes for untracked countries

Answers "why doesn't every country have a dedicated tracker" honestly: most of the world's ~195 countries genuinely have no dedicated tattoo ink regulation. That's not a research gap — it's the underlying reality (the same conclusion the fully-verified [Japan](japan.md) and [China](china.md) research reached, via a much slower per-country process).

## What this is

For the map's ~143 untracked country panels, InkReady now shows a short status note sourced from a comparative writeup: ["Tattoo Ink Regulations: A 181-'Nation' International Deep Dive"](https://xtremeinks.com/blogs/artists-corner/tattoo-ink-regulations-an-international-deep-dive-add-number) (xtremeinks.com, a tattoo ink retailer's blog).

**This is explicitly NOT the same confidence tier as the 13 dedicated trackers.** Every panel using this data says so in the UI: *"Unverified secondary-source note (not confirmed against primary law, unlike the dedicated trackers)."* It's a secondary source, not independently checked against a government law database or primary legal text the way Japan/Korea/Brazil/NZ/Chile were.

~90 of the ~143 untracked country codes in `assets/world-map.svg` have a note (`dashboard.py`'s `SURVEY_NOTES` dict); the rest have no data from this source and show only the generic "no dedicated tracker" message.

## Why this is the right tradeoff, not a shortcut

Doing full primary-source verification (the Japan/Korea/Brazil/Chile treatment) for all ~143 remaining countries would mean that same research effort repeated 100+ times — realistically weeks of work, and for the large majority the answer would land on the same place the survey already shows: "no comprehensive framework, general health standards apply." Spending that effort finding the ~2-5 more countries with a real Chile-or-Korea-style hidden gem is worthwhile (that's exactly how Chile was found); spending it re-confirming "yes, still nothing" for the other 95% is not.

## What would upgrade a country from survey-note to dedicated tracker

Same bar as everything else in this repo: find a real, reachable primary source (government law database, health ministry resolution, etc.), verify it live, build a fetcher or a reference doc — same process that turned up Korea, NZ, and Chile. If you have reason to suspect a specific country has more going on than the survey note suggests, say so and it gets the full treatment.
