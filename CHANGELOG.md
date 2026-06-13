# Changelog

All notable changes to `rutextnorm`. This project follows [Semantic Versioning](https://semver.org).

## [2.1.0] — 2026-06-13

Version jumps to 2.x to stay above the legacy `2.0` GitHub tag (which carried older,
pre-`flag_uncertain` code): version numbers only ever increase, so the newest code
always has the highest number. No API changes; `normalize_russian` and
`flag_uncertain` keep their signatures. Measured against the `ru_2026.csv` gold
(artifact-free Kaggle set), the trusted (non-escalated) accuracy rose to 98.2% while
the escalation rate fell to 9.1%.

### Normalization
- **Fractions**: a numerator ending in 1 now takes the singular denominator
  (`1/2` → «одна вторая», previously the ungrammatical «одна вторых»). Added
  Unicode vulgar fractions (`½ ⅓ ⅔ ¼ ¾ ⅛ …` → «одна вторая», «две третьих», …).
- **Currency**: `руб.`/`долл.` left after a multiplier now expand
  (`24,9 млрд руб.` → «… миллиарда рублей»). A currency symbol on a multiplied
  amount reads correctly (`$1 млрд` → «один миллиард долларов»,
  `$10 миллионов` → «десять миллионов долларов»), instead of leaving the symbol
  or mis-ordering the words.
- **Measurements**: a unit abbreviation's trailing dot is consumed
  (`7 км.` → «семь километров», previously «… километров.»).
- **Decimals**: an all-zero fraction is dropped (`938,00` → «девятьсот тридцать восемь»).
- **Time**: one o'clock drops «один» (`1:15` → «час пятнадцать минут»).

### Uncertainty router (`flag_uncertain`)
- A multi-sense abbreviation governed by a number is no longer flagged
  (`82 т.` → «тонны» is the rules' committed reading) — fixes the measurement
  router's false rejections.
- Only prepositions the rules actually decline count as resolving a number's case;
  a bare number after `в`/`на`/`за`/`по`/`у` is now flagged, since the rules leave
  it nominative while the gold may want an oblique case.

## [1.1.0]

- Added `flag_uncertain()`: an uncertainty router that returns the spans the rules
  can't resolve from the text, for routing to a stronger method.
- Feminine currency subunits count in the feminine (`… двадцать одна копейка`).
- Package and module renamed to `rutextnorm` (PyPI name == import name).

## [1.0.0]

- Initial release: single self-contained file, no dependencies — numbers, dates,
  currency, units, ordinals, decimals, fractions, times, abbreviations, acronyms,
  symbols, and Latin/Cyrillic handling for Russian TTS.

[2.1.0]: https://github.com/shigabeev/russian_tts_normalization/releases/tag/v2.1.0
[1.1.0]: https://pypi.org/project/rutextnorm/1.1.0/
[1.0.0]: https://pypi.org/project/rutextnorm/1.0.0/
