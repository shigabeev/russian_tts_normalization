import re

# Updated mapping dictionary with common digraphs
cyrrilization_mapping_extended = {
    'a': 'а', 'b': 'б', 'c': 'к', 'd': 'д', 'e': 'е',
    'f': 'ф', 'g': 'г', 'h': 'х', 'i': 'и', 'j': 'й',
    'k': 'к', 'l': 'л', 'm': 'м', 'n': 'н', 'o': 'о',
    'p': 'п', 'q': 'к', 'r': 'р', 's': 'с', 't': 'т',
    'u': 'у', 'v': 'в', 'w': 'в', 'x': 'кс', 'y': 'ы',
    'z': 'з',
    # Common digraphs
    'sh': 'ш', 'ch': 'ч', 'th': 'з', 'ph': 'ф', 'oo': 'у', 'ee': 'и', 'kh': 'х',
    # common trigraphs
    'sch': 'ск'
    # Capital letters are also converted to lowercase in the cyrrilization
}


# Russian letter to its phonetic pronunciation mapping
pronunciation_map = {
    'А': 'а', 'Б': 'бэ', 'В': 'вэ', 'Г': 'гэ', 'Д': 'дэ',
    'Е': 'е', 'Ё': 'ё', 'Ж': 'жэ', 'З': 'зэ', 'И': 'и',
    'Й': 'ий', 'К': 'ка', 'Л': 'эл', 'М': 'эм', 'Н': 'эн',
    'О': 'о', 'П': 'пэ', 'Р': 'эр', 'С': 'эс', 'Т': 'тэ',
    'У': 'у', 'Ф': 'эф', 'Х': 'ха', 'Ц': 'цэ', 'Ч': 'чэ',
    'Ш': 'ша', 'Щ': 'ща', 'Ъ': 'твёрдый знак', 'Ы': 'ы', 'Ь': 'мягкий знак',
    'Э': 'э', 'Ю': 'ю', 'Я': 'я'
}

# Function to expand abbreviations in the text
def expand_abbreviations(text):
    # Regex to find sequences of uppercase Cyrillic letters
    abbreviations = re.findall(r'\b[А-ЯЁ]{2,}\b', text)

    # Expand each abbreviation using the pronunciation map
    for abbr in abbreviations:
        # Create a pronounced form of the abbreviation
        pronounced_form = ' '.join(pronunciation_map[letter] for letter in abbr if letter in pronunciation_map)
        # Replace the abbreviation with its pronounced form
        text = text.replace(abbr, pronounced_form)

    return text


def cyrrilize(text):
    """Transliterate only Latin letters to approximate Cyrillic, leaving Cyrillic
    text (and its original case) and all other characters untouched."""
    cyrrilized_text = ""
    i = 0
    while i < len(text):
        ch = text[i]
        if ch.isascii() and ch.isalpha():
            digraph = text[i:i+2].lower()
            if (i + 1 < len(text) and text[i+1].isascii() and text[i+1].isalpha()
                    and digraph in cyrrilization_mapping_extended):
                cyrrilized_text += cyrrilization_mapping_extended[digraph]
                i += 2
            else:
                cyrrilized_text += cyrrilization_mapping_extended.get(ch.lower(), ch)
                i += 1
        else:
            cyrrilized_text += ch
            i += 1
    return cyrrilized_text

def number_to_words(n):
    """
    Convert a number into its word components in Russian
    """
    if n == 0:
        return 'ноль'

    units = ['','один','два','три','четыре','пять','шесть','семь','восемь','девять']
    teens = ['десять','одиннадцать','двенадцать','тринадцать','четырнадцать','пятнадцать','шестнадцать','семнадцать','восемнадцать','девятнадцать']
    tens = ['','десять','двадцать','тридцать','сорок','пятьдесят','шестьдесят','семьдесят','восемьдесят','девяносто']
    hundreds = ['','сто','двести','триста','четыреста','пятьсот','шестьсот','семьсот','восемьсот','девятьсот']
    
    thousand_units = ['тысяча', 'тысячи', 'тысяч']
    million_units = ['миллион', 'миллиона', 'миллионов']
    billion_units = ['миллиард', 'миллиарда', 'миллиардов']

    words = []

    # Helper function to resolve the correct form of thousands, millions, and billions
    def russian_plural(number, units):
        if number % 10 == 1 and number % 100 != 11:
            return units[0]
        elif 2 <= number % 10 <= 4 and (number % 100 < 10 or number % 100 >= 20):
            return units[1]
        else:
            return units[2]

    # Helper function to handle numbers below 1000
    def under_thousand(number):
        if number == 0:
            return []
        elif number < 10:
            return [units[number]]
        elif number < 20:
            return [teens[number - 10]]
        elif number < 100:
            return [tens[number // 10], units[number % 10]]
        else:
            return [hundreds[number // 100]] + under_thousand(number % 100)

    # Break the number into the billions, millions, thousands, and the rest
    billions = n // 1_000_000_000
    millions = (n % 1_000_000_000) // 1_000_000
    thousands = (n % 1_000_000) // 1_000
    remainder = n % 1_000

    if billions:
        words += under_thousand(billions) + [russian_plural(billions, billion_units)]
    if millions:
        words += under_thousand(millions) + [russian_plural(millions, million_units)]
    if thousands:
        # Special case for 'one' and 'two' in thousands
        if thousands % 10 == 1 and thousands % 100 != 11:
            pass  # Russian drops "одна" before "тысяча" (1873 -> "тысяча восемьсот...")
        elif thousands % 10 == 2 and thousands % 100 != 12:
            words.append('две')
        else:
            words += under_thousand(thousands)
        words.append(russian_plural(thousands, thousand_units))
    words += under_thousand(remainder)

    return ' '.join(word for word in words if word)


def detect_numbers(text):
    # Regular expression pattern for matching standalone numbers
    number_pattern = re.compile(r'\b\d+\b')
    # Find all matches and return them along with their start and end indices
    matches = list(number_pattern.finditer(text))
    number_matches = [{'number': match.group(), 'start': match.start(), 'end': match.end()} for match in matches]
    
    return number_matches

def number_to_words_digit_by_digit(n):
    """
    Convert a number into its word components in Russian, digit by digit.
    """
    units = ['ноль', 'один', 'два', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять']
    return ' '.join(units[int(digit)] for digit in str(n))

# Update the normalize_text_with_numbers to handle large numbers by reading them digit by digit
def normalize_text_with_numbers(text):
    # Detect all standalone numbers in the text
    detected_numbers = detect_numbers(text)
    # Sort detected numbers by their starting index in descending order
    detected_numbers.sort(key=lambda x: x['start'], reverse=True)
    
    # Replace each number with its normalized form
    for num in detected_numbers:
        number_value = int(num['number'])
        # For large numbers that are out of the range of the 'number_to_words' function, use 'number_to_words_digit_by_digit'
        if number_value >= 1_000_000_000_000:
            normalized_number = number_to_words_digit_by_digit(number_value)
        else:
            normalized_number = number_to_words(number_value)
        # Replace the original number in the text with its normalized form
        text = text[:num['start']] + normalized_number + text[num['end']:]
    
    return text


def normalize_phone_number(phone_number):
    # Strip the phone number of all non-numeric characters
    digits = re.sub(r'\D', '', phone_number)

    # Define the segments for the Russian phone number
    segments = {
        'country_code': digits[:1],  # +7 or 8
        'area_code': digits[1:4],    # 495
        'block_1': digits[4:7],      # 123
        'block_2': digits[7:9],      # 45
        'block_3': digits[9:11],     # 67
    }

    # Normalizing the country code
    if segments['country_code'] == '8':
        segments['country_code'] = 'восемь'
    elif segments['country_code'] == '7':
        segments['country_code'] = 'плюс семь'

    # Normalize each segment using the number_to_words function
    normalized_segments = {
        key: number_to_words(int(value)) if key != 'country_code' else value
        for key, value in segments.items()
    }

    # Combine the segments into the final spoken form
    spoken_form = ' '.join(normalized_segments.values())

    return spoken_form

# Correcting the phone number normalization function to handle various formats correctly

def normalize_text_with_phone_numbers(text):
    # Detect all phone numbers in the text
    phone_pattern = re.compile(
        r"(?:\+7|8)\s*\(?\d{3}\)?\s*\d{3}[-\s]?\d{2}[-\s]?\d{2}|8\d{10}"
    )
    # We use finditer here instead of findall to get the match objects, which will include the start and end indices.
    matches = list(phone_pattern.finditer(text))
    detected_phone_numbers = [{'phone': match.group().strip(), 'start': match.start(), 'end': match.end()} for match in matches]

    # Sort detected phone numbers by their starting index in descending order
    # This ensures that when we replace them, we don't mess up the indices of the remaining phone numbers
    detected_phone_numbers.sort(key=lambda x: x['start'], reverse=True)
    
    # Replace each phone number with its normalized form
    for pn in detected_phone_numbers:
        normalized_phone = normalize_phone_number(pn['phone'])
        # Replace the original phone number in the text with its normalized form
        text = text[:pn['start']] + normalized_phone + text[pn['end']:]
    
    return text

# Full function that detects and converts currency in a text to its full Russian word representation
def currency_normalization(text):
    """
    Detects currency amounts in the text and converts them to their word representations in Russian.
    """
    # Helper function to resolve the correct form of the currency units
    def russian_plural(number, units):
        if number % 10 == 1 and number % 100 != 11:
            return units[0]
        elif 2 <= number % 10 <= 4 and (number % 100 < 10 or number % 100 >= 20):
            return units[1]
        else:
            return units[2]

    # Function to convert a currency amount into its word components in Russian
    def currency_to_words(amount, currency='rub'):
        # Define the currency units and subunits
        currencies = {
            'rub': (['рубль', 'рубля', 'рублей'], ['копейка', 'копейки', 'копеек']),
            'usd': (['доллар', 'доллара', 'долларов'], ['цент', 'цента', 'центов']),
            'eur': (['евро', 'евро', 'евро'], ['евроцент', 'евроцента', 'евроцентов']),  # Euro has invariable form
            'gbp': (['фунт', 'фунта', 'фунтов'], ['пенс', 'пенса', 'пенсов']),
            'uah': (['гривна', 'гривны', 'гривен'], ['копейка', 'копейки', 'копеек']),
        }

        # Get the correct currency units
        main_units, sub_units = currencies.get(currency, currencies['rub'])

        # Separate the amount into main and subunits
        main_amount = int(amount)
        sub_amount = int(round((amount - main_amount) * 100))

        # Convert numbers to words
        main_words = number_to_words(main_amount) + ' ' + russian_plural(main_amount, main_units)
        sub_words = ''

        # Add subunits if present
        if sub_amount > 0:
            sub_words = number_to_words(sub_amount) + ' ' + russian_plural(sub_amount, sub_units)

        # Combine main and subunit words
        full_currency_words = main_words.strip()
        if sub_words:
            full_currency_words += ' ' + sub_words.strip()

        return full_currency_words

    # Define currency patterns for detection
    currency_patterns = {
        'rub': [r'(\d+(?:\.\d\d)?)\s*(руб(л(ей|я|ь))?|₽)', r'(\d+(?:\.\d\d)?)\s*RUB'],
        'usd': [r'(\d+(?:\.\d\d)?)\s*(доллар(ов|а|ы)?|\$)', r'(\d+(?:\.\d\d)?)\s*USD', r'\$(\d+(?:\.\d\d)?)'],
        'eur': [r'(\d+(?:\.\d\d)?)\s*(евро|€)', r'(\d+(?:\.\d\d)?)\s*EUR', r'(\d+)\s*€'],
        'gbp': [r'(\d+(?:\.\d\d)?)\s*(фунт(ов|а|ы)?|£)', r'(\d+(?:\.\d\d)?)\s*GBP', r'£(\d+)'],
        'uah': [r'(\d+(?:\.\d\d)?)\s*(грив(ен|ны|на)|₴)', r'(\d+(?:\.\d\d)?)\s*UAH', r'(\d+)\s*₴'],
    }

    # Detect and convert currencies in the text
    def detect_currency(text):
        # Check each currency pattern to find matches
        for currency_code, patterns in currency_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    # Extract the amount and convert it to words
                    amount = float(match.group(1))
                    currency_words = currency_to_words(amount, currency_code)
                    # Replace the original amount with its word representation in the text
                    text = re.sub(pattern, currency_words, text, count=1)

        return text

    # Run the detection and conversion on the input text
    return detect_currency(text)

# Maps the last word of a cardinal number to its ordinal stem (nominative masculine).
_cardinal_to_ordinal_stem = {
    'один': 'первый', 'два': 'второй', 'две': 'второй', 'три': 'третий',
    'четыре': 'четвёртый', 'пять': 'пятый', 'шесть': 'шестой', 'семь': 'седьмой',
    'восемь': 'восьмой', 'девять': 'девятый', 'десять': 'десятый',
    'одиннадцать': 'одиннадцатый', 'двенадцать': 'двенадцатый', 'тринадцать': 'тринадцатый',
    'четырнадцать': 'четырнадцатый', 'пятнадцать': 'пятнадцатый', 'шестнадцать': 'шестнадцатый',
    'семнадцать': 'семнадцатый', 'восемнадцать': 'восемнадцатый', 'девятнадцать': 'девятнадцатый',
    'двадцать': 'двадцатый', 'тридцать': 'тридцатый', 'сорок': 'сороковой',
    'пятьдесят': 'пятидесятый', 'шестьдесят': 'шестидесятый', 'семьдесят': 'семидесятый',
    'восемьдесят': 'восьмидесятый', 'девяносто': 'девяностый',
    'сто': 'сотый', 'двести': 'двухсотый', 'триста': 'трёхсотый', 'четыреста': 'четырёхсотый',
    'пятьсот': 'пятисотый', 'шестьсот': 'шестисотый', 'семьсот': 'семисотый',
    'восемьсот': 'восьмисотый', 'девятьсот': 'девятисотый',
    'тысяча': 'тысячный', 'тысячи': 'тысячный', 'тысяч': 'тысячный',
}
# Genitive prefix for a count word standing before "тысячный" (e.g. две -> двух тысячный).
_count_genitive_prefix = {
    'две': 'двух', 'два': 'двух', 'три': 'трёх', 'четыре': 'четырёх', 'пять': 'пяти',
    'шесть': 'шести', 'семь': 'семи', 'восемь': 'восьми', 'девять': 'девяти',
}

def _inflect_ordinal(stem, form):
    """Inflect a nominative-masculine ordinal stem into the requested form.
    form: 'nom_m' (год), 'nom_n' (день/число), 'gen' (года), 'prep' (году)."""
    if form == 'nom_m':
        return stem
    if stem.endswith('ий'):  # третий -> третье / третьего / третьем
        base = stem[:-2]
        return base + {'nom_n': 'ье', 'gen': 'ьего', 'prep': 'ьем'}[form]
    base = stem[:-2]  # drop -ый / -ой
    return base + {'nom_n': 'ое', 'gen': 'ого', 'prep': 'ом'}[form]

def number_to_ordinal_words(n, form='nom_m'):
    """Convert an integer to its ordinal words in Russian. Only the final
    component is ordinalized; preceding components stay cardinal."""
    words = number_to_words(n).split()
    last = words[-1]
    if last in ('тысяча', 'тысячи', 'тысяч') and len(words) > 1 and words[-2] in _count_genitive_prefix:
        # round thousands: "две тысячи" -> "двух тысячный" (2000 -> двухтысячный read split)
        words[-2] = _count_genitive_prefix[words[-2]]
    words[-1] = _inflect_ordinal(_cardinal_to_ordinal_stem.get(last, last), form)
    return ' '.join(words)

_MONTHS_GEN = ('января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля',
               'августа', 'сентября', 'октября', 'ноября', 'декабря')
_MONTH_BY_NUM = {f'{i:02d}': m for i, m in enumerate(_MONTHS_GEN, start=1)}
_GOD_FORM = {'год': 'nom_m', 'года': 'gen', 'году': 'prep', 'годе': 'prep'}

_re_date_numeric = re.compile(r'\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b')
_re_date_spelled = re.compile(
    r'\b(\d{1,2})\s+(' + '|'.join(_MONTHS_GEN) + r')\s+(\d{3,4})(\s+года)?\b')
_re_date_daymonth = re.compile(r'\b(\d{1,2})\s+(' + '|'.join(_MONTHS_GEN) + r')\b')
_re_year_god = re.compile(r'\b(\d{1,4})\s+(год|года|году|годе)\b')

def normalize_dates(text):
    """Normalize the rule-tractable date shapes: DD.MM.YYYY, "D month YYYY",
    "D month", and "<year> год/года/году"."""
    def numeric(m):
        day, month, year = m.group(1), m.group(2), m.group(3)
        mn = _MONTH_BY_NUM.get(f'{int(month):02d}')
        if not mn:
            return m.group(0)
        return f"{number_to_ordinal_words(int(day), 'nom_n')} {mn} {number_to_ordinal_words(int(year), 'gen')} года"

    def spelled(m):
        day, month, year = int(m.group(1)), m.group(2), int(m.group(3))
        return f"{number_to_ordinal_words(day, 'gen')} {month} {number_to_ordinal_words(year, 'gen')} года"

    def daymonth(m):
        return f"{number_to_ordinal_words(int(m.group(1)), 'gen')} {m.group(2)}"

    def year_god(m):
        return f"{number_to_ordinal_words(int(m.group(1)), _GOD_FORM[m.group(2)])} {m.group(2)}"

    text = _re_date_numeric.sub(numeric, text)
    text = _re_date_spelled.sub(spelled, text)
    text = _re_date_daymonth.sub(daymonth, text)
    text = _re_year_god.sub(year_god, text)
    return text

def normalize_russian(text):
    text = expand_abbreviations(text)
    text = normalize_dates(text)
    text = currency_normalization(text)
    text = normalize_text_with_phone_numbers(text)
    text = normalize_text_with_numbers(text)
    text = cyrrilize(text)
    return text