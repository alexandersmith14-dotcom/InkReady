# ECHA REACH Annex XVII — Entry 75

Restricts 4,000+ substances (carcinogens, mutagens, reproductive toxicants, allergenic colorants) in tattoo/permanent make-up ink. Base restriction entered force 2022, amended since (e.g. 2023 blue/green pigment concentration extension).

- Legal text: ECHA Annex XVII table page + EUR-Lex consolidated regulation text
- No official API or bulk download — page content changes are the signal to catch
- Appendix 13 holds the substance-specific concentration limit list

## Fetch approach

Scrape/diff the ECHA Annex XVII table page (entry 75 section) and the EUR-Lex consolidated text on a schedule. Same pattern as Klearance's `regref.py` — text diff, not structured JSON.
