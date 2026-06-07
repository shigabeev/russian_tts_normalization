# Russian text normalization for TTS
Normalize Text in Russian.


Usage:
Add `russian.py` (and the `data/` folder next to it) into the `text` folder of
your TTS system and import it from there. It can also be used as a command-line
filter: `echo "цена 1 500 руб." | python3 russian.py`.

```
from text.russian import normalize_russian

complex_test_text = """У меня есть $1234 и 5678 рублей. Кроме того, я должен 90.50€ и взял в долг 4321 GBP.
В моем кошельке было 876 UAH и 543.21 RUB, а также я нашел 20 центов."""
​
normalized_text = normalize_russian(complex_test_text)
print(normalized_text)
```

​Prints:

```
У меня есть тысяча двести тридцать четыре доллара и пять тысяч шестьсот семьдесят восемь рублей. Кроме того, я должен девяносто евро пятьдесят евроцентов и взял в долг четыре тысячи триста двадцать один фунт.\nВ моем кошельке было восемьсот семьдесят шесть гривен и пятьсот сорок три рубля двадцать один копейка, а также я нашел двадцать центов.
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
16. Textual abbreviations (data/abbreviations.txt): "и т.д." -> "и так далее"
17. Acronyms: vowel-less spelled out ("СССР" -> "эс эс эс эр"), pronounceable read as words ("НАТО" -> "нато")
18. E-mail/URL spell-out: "example.com" -> "ексампле точка ком"

Notes:
- The letter ё is kept in the output (it carries pronunciation for TTS).
- Vocabulary lives in `data/`. Abbreviations come from NVIDIA NeMo-text-processing
  (`ru/whitelist.tsv`, Apache-2.0); only single-sense entries are used.

# Validation
Tested against the Google/Kaggle Russian text-normalization set
(`ru_train.csv`, 10,574,516 tokens). Each token's input is normalized in
isolation and compared to the gold output; "accuracy" is exact string match,
compared ё/е-insensitively (the reference data writes only е, this script keeps ё).
"Original" is the script before these changes.

| Domain (class) | Tokens | Original acc. | Current acc. | Notes |
|---|--:|--:|--:|---|
| PLAIN       | 7,360,439 |  69.9% |  92.2% | residual: Latin spelled per-letter in gold |
| PUNCT       | 2,288,640 | 100.0% | 100.0% | passthrough |
| CARDINAL    |   272,442 |  51.2% |  77.0% | residual: oblique case agreement |
| LETTERS     |   189,528 |   0.8% |   0.0% | not targeted (gold uses bare letters, worse for TTS) |
| DATE        |   185,959 |   0.0% |  84.2% | residual: bare years, ambiguous day-case |
| VERBATIM    |   157,912 |  91.1% |  95.7% | symbol / Greek map |
| ORDINAL     |    46,738 |   0.0% |  40.7% | residual: bare-number ordinals (need context) |
| MEASURE     |    40,534 |   3.1% |  19.9% | residual: oblique case agreement |
| TELEPHONE   |    10,088 |   0.3% |   1.4% | not targeted (irregular ISBN grouping) |
| DECIMAL     |     7,297 |   6.1% |  49.8% | residual: oblique case agreement |
| ELECTRONIC  |     5,832 |   2.6% |   2.6% | not targeted (English G2P + markers) |
| MONEY       |     2,690 |  14.4% |  30.3% | residual: case agreement |
| FRACTION    |     2,460 |   0.0% |  66.0% | residual: context-dependent case |
| DIGIT       |     2,012 |   0.0% | 100.0% | leading-zero digit strings |
| TIME        |     1,945 |   0.0% |  84.9% | residual: HH:MM:SS, oblique case |
| **Overall** | **10,574,516** | **73.0%** | **91.1%** | exact-match token accuracy |

The remaining error is dominated by things rules cannot resolve without a token
classifier or sentence context: grammatical case agreement (`500 км` ->
`пятисот километров`), disambiguating a bare number as cardinal/ordinal/year, and
classes left untargeted on purpose (LETTERS, TELEPHONE, ELECTRONIC). The test set
is treated as a regression guard, not a target — some choices (keeping ё, reading
acronyms as words, nominative Roman numerals) favour TTS quality over this score.

Run `python3 test_russian.py` for the regression cases.

# Not implemented (needs sentence context or a token classifier, not pure rules)
1. HH:MM:SS times
2. Grammatical case agreement (e.g. "500 км" -> "пятисот километров"; oblique decimals)
3. Disambiguating a bare number as cardinal vs. ordinal vs. year; date day-case; Roman case
4. Telephone/ISBN segment reading and full URL G2P (irregular / English pronunciation)
5. Context-dependent abbreviations ("г." -> год/город, "кв." -> квартира/квартал)
6. Acronyms read as letters despite vowels ("США"); needs a pronunciation lexicon

# Acknowledgements
I want to thank OpenAI's ChatGPT for writing this code. I would've never been able to write it myself since I'm too lazy for that.

# Call for collaboration
Feel free to use this code. You can share it, copy it, modify as you wish. However, pretty please, *if you improved the solution somehow, add your modifications here too.*

