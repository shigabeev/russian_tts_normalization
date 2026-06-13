# rutextnorm — Russian text normalization for TTS

[![PyPI](https://img.shields.io/pypi/v/rutextnorm.svg)](https://pypi.org/project/rutextnorm/)
[![Python](https://img.shields.io/pypi/pyversions/rutextnorm.svg)](https://pypi.org/project/rutextnorm/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Turn written Russian into something a TTS model can *say*: numbers, dates, money,
units, fractions, times, abbreviations, symbols, and mixed Latin/Cyrillic — all
spelled out, in agreement, in words.

```
"В 2024 году инфляция составила 7,5%, а доходы выросли на 3 млрд руб."
        ↓ normalize_russian()
"В две тысячи двадцать четвёртом году инфляция составила семь целых
 и пять десятых процента, а доходы выросли на три миллиарда рублей"
```

- **One file, zero dependencies, no network, no ML.** Pure `re` + lookup tables.
  Deterministic: same input → same output. ~0.17 ms/sentence (~375k chars/s).
- **Knows when it might be wrong.** `flag_uncertain()` returns the spans the rules
  can't resolve from the text, so you can route just those to a slower, stronger
  method (a neural normalizer or LLM) and trust the fast path everywhere else.
- **Built for TTS, not for a benchmark.** Where speakability and a corpus's written
  form disagree, it favours what the synthesizer should pronounce (see
  [Design choices & gotchas](#design-choices--gotchas)).

---

## Install

```bash
pip install rutextnorm
```

The PyPI name and the import name are the same:

```python
from rutextnorm import normalize_russian
```

Or **vendor the single file** — copy `rutextnorm.py` straight into your project
(e.g. into a TTS repo's `text/` folder). Nothing else is required. When vendored,
the import follows wherever you put it:

```python
from text.rutextnorm import normalize_russian
```

Requires Python ≥ 3.8.

---

## Quick start

```python
from rutextnorm import normalize_russian

text = """У меня есть $1234 и 5678 рублей. Кроме того, я должен 90.50€ и взял в долг 4321 GBP.
В моём кошельке было 876 UAH и 543.21 RUB, а также я нашёл 20 центов."""

print(normalize_russian(text))
```

```
У меня есть тысяча двести тридцать четыре доллара и пять тысяч шестьсот семьдесят восемь рублей. Кроме того, я должен девяносто евро пятьдесят евроцентов и взял в долг четыре тысячи триста двадцать один фунт.
В моём кошельке было восемьсот семьдесят шесть гривен и пятьсот сорок три рубля двадцать одна копейка, а также я нашёл двадцать центов.
```

### Command-line filter

```bash
echo "цена 1 500 руб." | python3 -m rutextnorm        # installed
echo "цена 1 500 руб." | python3 rutextnorm.py        # vendored
# -> цена тысяча пятьсот рублей
```

---

## Use cases

- **TTS front-end.** Run text through `normalize_russian` before your G2P /
  acoustic model so the synthesizer never has to guess how to read `7,5%` or `$3 млрд`.
- **Hybrid pipeline.** Use `flag_uncertain` as a router: the rules handle the
  ~90% of text they're confident about instantly; only flagged spans go to an
  expensive neural normalizer ([RUNorm](https://github.com/Den4ikAI/runorm)) or an
  LLM. You pay for the slow path only where it actually helps.
- **Corpus preprocessing.** Normalize a training/eval corpus deterministically and
  reproducibly, with no model weights or API calls in the loop.
- **Drop-in CLI filter** in shell pipelines.

---

## What it normalizes

| | Input → output |
|---|---|
| Cardinals (any size) | `1 234 567` → «один миллион двести тридцать четыре тысячи пятьсот шестьдесят семь» |
| Ordinals (suffix / Roman) | `1-й` → «первый», `XIX` → «девятнадцатый» |
| Dates | `05.08.2008` → «пятое августа две тысячи восьмого года», `2008 г.` → «две тысячи восьмой год» |
| Times | `06:06` → «шесть часов шесть минут», `1:15` → «час пятнадцать минут», `2PM` → «два часа дня» |
| Money | `543.21 RUB` → «пятьсот сорок три рубля двадцать одна копейка», `$1 млрд` → «один миллиард долларов» |
| Units (count agreement) | `5 кг` → «пять килограммов», `90 км/ч` → «девяносто километров в час», `7 км.` → «семь километров» |
| Multipliers | `5 млн` → «пять миллионов», `24,9 млрд руб.` → «двадцать четыре целых и девять десятых миллиарда рублей» |
| Decimals & percent | `1,2` → «одна целая и две десятых», `50%` → «пятьдесят процентов», `938,00` → «девятьсот тридцать восемь» |
| Fractions | `2/3` → «две третьих», `1/2` → «одна вторая», `½` → «одна вторая» |
| Context-governed case | `около 500 км` → «около пятисот километров», `с 500 рублями` → «с пятьюстами рублями» |
| Trigger nouns | `2 место` → «второе место», `5 этаж` → «пятый этаж» |
| Compound adjectives | `25-этажный` → «двадцатипятиэтажный» |
| Abbreviations | `и т.д.` → «и так далее», `ст. 158` → «статья сто пятьдесят восемь» |
| Acronyms | `СССР` → «эс эс эс эр» (vowel-less spelled out), `НАТО` kept as a word |
| Latin / mixed | `Google` → «гугл», `GPS` → «джи пи эс», `example.com` → «ексампле точка ком» |
| Symbols | `&` → «и», `²` → «в квадрате», `°C`, `№`, Greek letters |
| ё restoration | `еще` → «ещё» (unambiguous words only) |

Vocabularies are embedded in the single file. The abbreviation and unit
inventories are informed by [NVIDIA NeMo-text-processing](https://github.com/NVIDIA/NeMo-text-processing)
(Apache-2.0); only single-sense entries are kept and the spoken forms were
rewritten and checked by hand.

---

## Knowing when to defer: `flag_uncertain`

`normalize_russian` always returns its best guess. `flag_uncertain(text)` tells you
*where that guess rests on information the text doesn't contain* — so a caller can
escalate those spans (or the whole sentence) to a stronger method and trust the
rest.

```python
from rutextnorm import flag_uncertain

text = "Доктор Smith открыл том XIV на с. 42."
for start, end, original, reason in flag_uncertain(text):
    print(f"{original!r:14}{reason}")
```

```
'Smith'       foreign word (transliteration is approximate)
'XIV'         Roman numeral (case defaults to nominative)
'с.'          ambiguous abbreviation (секунда / страница / село / с (предлог))
```

It reads the **input only** (never a reference), runs in ~0.02 ms/sentence, and
detects five structural ambiguities:

| Detector | Why it's uncertain |
|---|---|
| Foreign words | transliteration is approximate; exact pronunciation needs G2P |
| Multi-sense abbreviations (`г.` `в.` `с.` `кв.` …) | several expansions; only context disambiguates |
| Roman numerals | case is context-dependent; read in the nominative by default |
| Four-digit year-or-cardinal | `1998` could be a year or a count |
| Bare numbers with no cue | grammatical case / cardinal-vs-ordinal undetermined |

Each span carries a `reason`, so a cost-sensitive caller can ignore the reason
types it doesn't care about (e.g. trust foreign-word transliteration and drop those
flags). A minimal router:

```python
def normalize_or_escalate(text, escalate):
    spans = flag_uncertain(text)
    if spans:
        return escalate(text)          # neural model / LLM
    return normalize_russian(text)     # fast path
```

---

## Metrics

Measured against `ru_2026.csv` — the Google/Kaggle Russian normalization gold
([`ru_train.csv`](https://www.kaggle.com/c/text-normalization-challenge-russian-language),
10.6M tokens) with its dataset artifacts removed (per-letter spelling markers,
`sil` tokens). Comparison is ё-insensitive (the module keeps ё, the gold drops it)
and space-folded (the gold space-separates transliterated foreign words, e.g.
`т и б е р и у с`, where the module writes the joined word).

`acc` = exact match; `rej` = fraction `flag_uncertain` escalates; `trusted` =
accuracy on the **non-escalated** part — the number a hybrid pipeline actually ships.

| Class | Share | acc | rej | trusted | Residual is… |
|---|--:|--:|--:|--:|---|
| PLAIN | 70% | 95.1% | 7% | 99.5% | foreign words (gold spells per-letter) |
| PUNCT | 21% | 100% | 0% | 100% | — |
| CARDINAL | 2.6% | 77.2% | 97% | 67.9% | oblique case of bare numbers (needs context) |
| DATE | 1.7% | 86.1% | 47% | 94.5% | year case; ambiguous day case |
| LETTERS | 1.8% | 23.6% | 28% | 32.7% | acronyms read as words, not bare letters (deliberate) |
| VERBATIM | 1.5% | 95.5% | 0% | 95.5% | symbol / Greek map |
| ORDINAL | 0.4% | 40.4% | 67% | 88.3% | bare-number ordinals (need context) |
| MEASURE | 0.4% | 59.5% | 12% | 63.4% | oblique case agreement |
| MONEY | <0.1% | 45.9% | 37% | 52.9% | case agreement; `долларов США` artifact |
| DECIMAL | <0.1% | 58.6% | 3% | 59.6% | oblique case agreement |
| FRACTION | <0.1% | 77.9% | 98% | 100% | context-dependent case |
| TIME | <0.1% | 87.6% | 5% | 90.5% | oblique case; `HH:MM:SS` kept by gold |
| **Overall** | 100% | **93.7%** | **9.1%** | **98.2%** | |

**Reading the router story:** escalating the 9.1% of tokens `flag_uncertain`
marks lifts the trusted accuracy from 93.7% to **98.2%**, catching ~75% of all
errors. Measured per *sentence* (the router's real setting, with full context)
the figures are 93.8% / **97.9%** trusted at 8.5% escalation.

The remaining error is dominated by two things rules can't fix without a token
classifier or sentence context — **grammatical case of bare numbers** and a few
**deliberate divergences** (next section) — both of which `flag_uncertain` is
designed to route away. The benchmark is a regression guard, not a target.

> The evaluation harnesses (`eval_reject.py` token-level, `eval_reject_sent.py`
> sentence-level), the regression tests (`test_russian.py`), the extension eval set
> and the dataset-cleaning script live on dev branches (`ru-2.0-alpha`); this branch
> ships only the module. To reproduce: `python3 eval_reject.py ru_2026.csv`.

---

## Design choices & gotchas

These are intentional. Where a corpus's *written* form and a synthesizer's
*spoken* needs disagree, the module picks speech.

- **Feed it whole sentences, not pre-split tokens.** The context rules (case after a
  preposition, `год` after a year, a unit after a number) only fire when the
  surrounding words are present. Normalizing isolated tokens silently disables them.
- **ё is kept in the output** (`нашёл`, `ещё`) — it carries pronunciation. If you
  diff against a corpus that writes only `е`, compare ё/е-insensitively.
- **A bare number's case defaults to nominative.** `5 километров`, not
  `пяти километрах` — the rules can't know the governing case without a cue in the
  text. `flag_uncertain` marks these; give context or route them.
- **Dates** read the day in the genitive and the year in the nominative by default
  (`13 сентября` → «тринадцатого сентября», `2008 г.` → «две тысячи восьмой год`).
  Both are the citation-form defaults; the actual case is context-dependent.
- **Foreign words are transliterated as one word** (`Google` → «гугл»), not spelled
  by English letter names. Good enough for most TTS; `flag_uncertain` flags them if
  you need exact G2P.
- **Cyrillic acronyms** use a vowel heuristic: vowel-less → letter-by-letter
  (`СССР` → «эс эс эс эр»), pronounceable → kept (`НАТО`). Exceptions like `США`
  (spelled out despite vowels) need a pronunciation lexicon and aren't bundled.
- **Multi-sense abbreviations are left untouched** (`кв.`, `г.`, `т.` standing alone)
  — they have several expansions. `flag_uncertain` marks them.
- **Phone/ISBN numbers** are read as plain cardinals (not segmented), and `HH:MM:SS`
  times are expanded.

### Known limitations (need sentence context or a classifier — out of scope)

1. Grammatical case agreement of a bare number (`500 км` → «пятисот километров`).
2. Disambiguating a bare number as cardinal vs. ordinal vs. year.
3. Telephone / ISBN segmentation and full URL G2P.
4. Context-dependent abbreviations (`г.` → год/город, `кв.` → квартира/квартал).
5. Acronyms read as letters despite vowels (`США`).

For these, the intended pattern is `flag_uncertain` → escalate to a neural
normalizer or LLM.

---

## API

```python
normalize_russian(text: str) -> str
```
Normalize a string (sentence, paragraph, or document). Idempotent on already-spoken text.

```python
flag_uncertain(text: str) -> list[tuple[int, int, str, str]]
```
Return `(start, end, original, reason)` spans where the normalization is an
unverifiable guess. Empty list = high confidence in the whole string. Offsets index
the input.

---

## Contributing

Found a case it reads wrong? PRs and issues welcome — please include the input, the
current output, and the form a Russian TTS should say. Behavioural changes should
come with a regression test (`test_russian.py` on the `ru-2.0-alpha` branch).

*If you improve the solution, please contribute the fix back here too.*

## License

MIT (see [LICENSE](LICENSE)). The embedded abbreviation/unit inventories are informed
by NVIDIA NeMo-text-processing (Apache-2.0); spoken forms were rewritten by hand.
