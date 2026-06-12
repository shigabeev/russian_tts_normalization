# Russian text normalization for TTS
Normalize Text in Russian.


Install: `pip install russian-tts-normalization`, or just copy `russian.py`
(a single self-contained file, no dependencies) into the `text` folder of your
TTS system. It can also be used as a command-line filter:
`echo "цена 1 500 руб." | python3 russian.py`.

Note the name difference: the PyPI *package* is `russian-tts-normalization`,
but it installs a single top-level *module* named `russian` — the import name
matches the file, because the file is designed to also be vendored as
`russian.py` next to your TTS code (in which case the import becomes
`from text.russian import normalize_russian` or similar).

```
from russian import normalize_russian

complex_test_text = """У меня есть $1234 и 5678 рублей. Кроме того, я должен 90.50€ и взял в долг 4321 GBP.
В моем кошельке было 876 UAH и 543.21 RUB, а также я нашел 20 центов."""

normalized_text = normalize_russian(complex_test_text)
print(normalized_text)
```

Prints:

```
У меня есть тысяча двести тридцать четыре доллара и пять тысяч шестьсот семьдесят восемь рублей. Кроме того, я должен девяносто евро пятьдесят евроцентов и взял в долг четыре тысячи триста двадцать один фунт.
В моем кошельке было восемьсот семьдесят шесть гривен и пятьсот сорок три рубля двадцать одна копейка, а также я нашёл двадцать центов.
```

# Implemented 
1. Cyrrilization of letters such as "apple" -> "эппл". 
2. Abbreviations expansion such as "СССР" -> "эс эс эс эр". 
3. Numbers conversion of any size
4. Currency expansion
5. Phone number expansion
6. Dates: "1862 год", "12 февраля 2013", "05.08.2008" -> ordinal year/day reading
7. Ordinals with a suffix ("1-й" -> "первый") and Roman numerals ("XIX" -> "девятнадцатого")
8. Decimals: "1,2" -> "одна целая и две десятых"; percentages: "50%" -> "пятьдесят процентов"
9. Fractions: "2/3" -> "две третьих"
10. Clock times: "06:06" -> "шесть часов шесть минут"
11. Digit strings with a leading zero: "06" -> "ноль шесть"
12. Symbols / foreign letters by name: "&" -> "и", "²" -> "в квадрате", "°C", Greek
13. Space/NBSP-grouped thousands: "1 234 567" -> one number; negatives: "-5" -> "минус пять"
14. Quantity multipliers: "5 млн" -> "пять миллионов" (agrees with the number)
15. Units of measure: "5 кг" -> "пять килограммов", "90 км/ч" -> "...в час", "5 ГБ", "25°"
16. Textual abbreviations: "и т.д." -> "и так далее"
17. Acronyms: vowel-less spelled out ("СССР" -> "эс эс эс эр"), pronounceable kept as-is ("НАТО")
18. E-mail/URL spell-out: "example.com" -> "ексампле точка ком"
19. Dotted units ("82 т." -> "восемьдесят две тонны") and decimal counts ("1,5 км" -> "...километра")
20. Years with г./гг. and ranges: "2008 г." -> "две тысячи восьмой год", "1941—1945 гг.", "XIX–XX вв."
21. Context-governed case: "около 500 км" -> "около пятисот километров", "к 5" -> "к пяти",
    "с 500 рублями" -> "с пятьюстами рублями" (closed-class cardinal declension tables)
22. Ordinal trigger nouns: "2 место" -> "второе место", "5 этаж" -> "пятый этаж"
23. Compound number adjectives: "25-этажный" -> "двадцатипятиэтажный"
24. Times beyond HH:MM: "02:25:00", "2PM" -> "два часа дня"; scores: "3:1" -> "три один"
25. Versions/IP: "Python 3.11" -> "питон три точка одиннадцать", "192.168.1.1"
26. Structural refs before a number: "ст. 158" -> "статья сто пятьдесят восемь"; math: "2+2=4"
27. English word dictionary: "Google" -> "гугл"; Latin acronyms by English letter name: "GPS" -> "джи пи эс"
28. ё restoration (unambiguous words only): "еще" -> "ещё"; hashtags: "#новости" -> "хештег новости"

Notes:
- The letter ё is kept in the output (it carries pronunciation for TTS).
- Vocabularies are embedded in `russian.py` (single-file module). Abbreviations come from NVIDIA NeMo-text-processing
  (`ru/whitelist.tsv`, Apache-2.0); only single-sense entries are used.

# Validation
Tested against the Google/Kaggle Russian text-normalization set
(`ru_train.csv`, 10,574,516 tokens). Each token's input is normalized in
isolation and compared to the gold output; "accuracy" is exact string match,
compared ё/е-insensitively (the reference data writes only е, this script keeps ё).
"Original" is the script before these changes.

The evaluation harness (`eval_assess.py`, `eval_extension.csv`), regression
tests and the dataset-cleaning script live on the `ru-2.0-alpha` branch; this
branch ships only the module itself.

| Domain (class) | Tokens | Original acc. | Current acc. | Notes |
|---|--:|--:|--:|---|
| PLAIN       | 7,360,439 |  69.9% |  92.5% | residual: Latin spelled per-letter in gold |
| PUNCT       | 2,288,640 | 100.0% | 100.0% | passthrough |
| CARDINAL    |   272,442 |  51.2% |  77.0% | residual: oblique case of bare numbers (no context in token) |
| LETTERS     |   189,528 |   0.8% |   0.0% | not targeted (gold uses bare letters, worse for TTS) |
| DATE        |   185,961 |   0.0% |  86.2% | residual: bare years, ambiguous day-case |
| VERBATIM    |   157,912 |  91.1% |  95.7% | symbol / Greek map |
| ORDINAL     |    46,738 |   0.0% |  40.6% | residual: bare-number ordinals (need context) |
| MEASURE     |    40,537 |   3.1% |  50.8% | residual: oblique case agreement |
| TELEPHONE   |    10,088 |   0.3% |   1.3% | not targeted (irregular ISBN grouping) |
| DECIMAL     |     7,299 |   6.1% |  54.3% | residual: oblique case agreement |
| ELECTRONIC  |     5,832 |   2.6% |   2.8% | not targeted (English G2P + markers) |
| MONEY       |     2,690 |  14.4% |  34.0% | residual: case agreement, "долларов сэ ш а" artifact |
| FRACTION    |     2,460 |   0.0% |  66.0% | residual: context-dependent case |
| DIGIT       |     2,012 |   0.0% | 100.0% | leading-zero digit strings |
| TIME        |     1,949 |   0.0% |  85.3% | residual: oblique case, timezone suffixes |
| **Overall** | **10,574,570** | **73.0%** | **91.4%** | exact-match token accuracy (incl. eval_extension rows) |

The remaining error is dominated by things rules cannot resolve without a token
classifier or sentence context. Case agreement is now rule-handled when the
context is inside the token (`около 500 км` -> `около пятисот километров`,
preposition- and noun-ending-governed), but the gold set scores tokens in
isolation, where a bare `500 км` gives no case signal. Likewise
disambiguating a bare number as cardinal/ordinal/year, and
classes left untargeted on purpose (LETTERS, TELEPHONE, ELECTRONIC). The test set
is treated as a regression guard, not a target — some choices (keeping ё, reading
acronyms as words, nominative Roman numerals) favour TTS quality over this score.
