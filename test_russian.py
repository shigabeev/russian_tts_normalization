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
]


def main():
    failures = []
    for before, expected in CASES:
        got = normalize_russian(before)
        if got != expected:
            failures.append((before, expected, got))
    for before, expected, got in failures:
        print(f"FAIL {before!r}: expected {expected!r}, got {got!r}")
    print(f"{len(CASES) - len(failures)}/{len(CASES)} passed")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
