"""Regression tests for normalize_russian. Run: python3 test_russian.py

Cases are drawn from the Google/Kaggle Russian text-normalization gold set,
covering the rule-tractable behaviour each change added. No external deps.
"""
from russian import normalize_russian

CASES = [
    # Cyrillic case is preserved (only Latin is transliterated).
    ("Москва", "Москва"),
    ("Tiberius", "тибериус"),
    # Cardinals: no redundant "одна" before тысяча.
    ("1873", "тысяча восемьсот семьдесят три"),
    ("2013", "две тысячи тринадцать"),
    ("123", "сто двадцать три"),
    # Dates: year with год-form drives the case.
    ("1862 год", "тысяча восемьсот шестьдесят второй год"),
    ("1811 года", "тысяча восемьсот одиннадцатого года"),
    ("12 февраля 2013", "двенадцатого февраля две тысячи тринадцатого года"),
    ("7 октября 2010 года", "седьмого октября две тысячи десятого года"),
    ("05.08.2008", "пятое августа две тысячи восьмого года"),
    ("1 марта", "первого марта"),
    # Ordinals written with an explicit suffix.
    ("1-й", "первый"),
    ("190-го", "сто девяностого"),
    ("1950-х", "тысяча девятьсот пятидесятых"),
    ("3-го", "третьего"),
    # Decimal comma.
    ("1,2", "одна целая и две десятых"),
    ("0,635", "ноль целых и шестьсот тридцать пять тысячных"),
    # Digit strings (leading zero) read digit by digit.
    ("06", "ноль шесть"),
    ("007", "ноль ноль семь"),
    # Symbols / non-Russian letters spoken by name.
    ("&", "и"),
    ("²", "в квадрате"),
    ("α", "альфа"),
    ("ї", "и"),
    # Dates/ordinals keep ё; comparison below folds ё->е (gold drops ё).
    ("4 июля 2012", "четвёртого июля две тысячи двенадцатого года"),
    # Roman numerals read as ordinals (nominative default).
    ("XIX век", "девятнадцатый век"),
    ("том III", "том третий"),
    # Clock times (HH:MM); HH:MM:SS is left for the digit reader.
    ("06:06", "шесть часов шесть минут"),
    ("07:00", "семь часов"),
    ("02:33", "два часа тридцать три минуты"),
    # Simple fractions.
    ("2/3", "две третьих"),
    ("653/26", "шестьсот пятьдесят три двадцать шестых"),

    # --- Real-world cases (beyond the test set) -------------------------------
    # Space/NBSP-grouped thousands.
    ("10 000 рублей", "десять тысяч рублей"),
    ("1 234 567", "один миллион двести тридцать четыре тысячи пятьсот шестьдесят семь"),
    # Percentages, negatives, multipliers, big numbers.
    ("50%", "пятьдесят процентов"),
    ("1%", "один процент"),
    ("-5 градусов", "минус пять градусов"),
    ("1 млн", "один миллион"),
    ("5 млн", "пять миллионов"),
    ("1000000000000000", "один квадриллион"),
    # Abbreviations (NeMo whitelist) and acronyms (vowel heuristic).
    ("и т.д.", "и так далее"),
    ("б/у", "бывший в употреблении"),
    ("НАТО", "нато"),
    ("ВАЖНО", "важно"),
    ("СССР", "эс эс эс эр"),
    # Symbols, web, Latin-abbrev guard.
    ("100°C", "сто градусов цельсия"),
    ("№5", "номер пять"),
    ("example.com", "ексампле точка ком"),
    ("CD", "кд"),
    # Units of measure with count agreement.
    ("1 кг", "один килограмм"),
    ("2 кг", "два килограмма"),
    ("5 кг", "пять килограммов"),
    ("10 км", "десять километров"),
    ("20 мин", "двадцать минут"),
    ("1 мин", "одна минута"),
    ("90 км/ч", "девяносто километров в час"),
    ("5 м²", "пять квадратных метров"),
    ("5 ГБ", "пять гигабайт"),
    ("25°", "двадцать пять градусов"),
]


def _fold(s):
    return s.replace('ё', 'е').replace('Ё', 'Е')  # ё is kept in output but compared insensitively


def main():
    failures = []
    for before, expected in CASES:
        got = normalize_russian(before)
        if _fold(got) != _fold(expected):
            failures.append((before, expected, got))
    for before, expected, got in failures:
        print(f"FAIL {before!r}: expected {expected!r}, got {got!r}")
    print(f"{len(CASES) - len(failures)}/{len(CASES)} passed")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
