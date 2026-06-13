import re

# ---- Embedded vocabularies (kept in-file so the module is a single file) -------

_ABBREVIATIONS_TSV = """\
# Russian textual abbreviations -> spoken form.
# Source: NVIDIA NeMo-text-processing, ru/data/whitelist.tsv (Apache-2.0)
#   https://github.com/NVIDIA/NeMo-text-processing
# Format: <abbreviation><TAB><expansion>   (lines starting with # are ignored).
# Matching is case-insensitive and tolerant of spaces after the dots.
#
# Only entries with a single, context-independent expansion are kept. NeMo's
# whitelist resolves the rest by context (a WFST), which a deterministic rule
# engine cannot do, so these are intentionally omitted:
#   г. (год/году/года/город), кв. (квартира/квартал), ЖК (5 senses),
#   комн./эт. (adjective agreement), экз. (count agreement).
гг.	годы
р-н	район
до н. э.	до нашей эры
н. э.	нашей эры
см. также	смотри также
с.ш.	северной широты
ю.ш.	южной широты
в.д.	восточной долготы
з.д.	западной долготы
и т. д.	и так далее
и т. п.	и тому подобное
б/у	бывший в употреблении
и др.	и другие
и пр.	и прочие
т.е.	то есть
"""

_MEASUREMENTS_TSV = """\
# Units of measurement -> spoken form, with count agreement.
# Abbreviation inventory informed by NVIDIA NeMo-text-processing
#   (ru/data/measurements.tsv, Apache-2.0). Forms here are standard Russian
#   declensions written/checked by hand, because NeMo's own forms contain
#   spelling errors (e.g. it lists "кг" as "килограм"/"килограмов", one м).
#
# Format: <abbr><TAB><one><TAB><few (2-4)><TAB><many (5+, 0, 11-14)><TAB><gender m|f>
#   one  -> "1 X"  (один/одна X)        few -> "2-4 X"  (два/две X)
#   many -> "5+ X" (пять X)             gender selects один/одна, два/две for the numeral
# Matching is case-sensitive (км != КМ, Вт != вт) and requires a number before the unit.
# Ambiguous one-letter abbreviations (г=грамм/год, т=тонна/том, с=секунда/предлог) are omitted.
#
# length
км	километр	километра	километров	m
м	метр	метра	метров	m
см	сантиметр	сантиметра	сантиметров	m
мм	миллиметр	миллиметра	миллиметров	m
дм	дециметр	дециметра	дециметров	m
# mass
кг	килограмм	килограмма	килограммов	m
мг	миллиграмм	миллиграмма	миллиграммов	m
# volume
л	литр	литра	литров	m
мл	миллилитр	миллилитра	миллилитров	m
# time
ч	час	часа	часов	m
мин	минута	минуты	минут	f
сек	секунда	секунды	секунд	f
# area / volume
га	гектар	гектара	гектаров	m
м²	квадратный метр	квадратных метра	квадратных метров	m
м2	квадратный метр	квадратных метра	квадратных метров	m
км²	квадратный километр	квадратных километра	квадратных километров	m
км2	квадратный километр	квадратных километра	квадратных километров	m
см²	квадратный сантиметр	квадратных сантиметра	квадратных сантиметров	m
м³	кубический метр	кубических метра	кубических метров	m
м3	кубический метр	кубических метра	кубических метров	m
# speed
км/ч	километр в час	километра в час	километров в час	m
м/с	метр в секунду	метра в секунду	метров в секунду	m
# frequency
Гц	герц	герца	герц	m
кГц	килогерц	килогерца	килогерц	m
МГц	мегагерц	мегагерца	мегагерц	m
ГГц	гигагерц	гигагерца	гигагерц	m
# power / electricity
Вт	ватт	ватта	ватт	m
кВт	киловатт	киловатта	киловатт	m
МВт	мегаватт	мегаватта	мегаватт	m
В	вольт	вольта	вольт	m
кВ	киловольт	киловольта	киловольт	m
А	ампер	ампера	ампер	m
мА	миллиампер	миллиампера	миллиампер	m
Ом	ом	ома	ом	m
# data
бит	бит	бита	бит	m
байт	байт	байта	байт	m
КБ	килобайт	килобайта	килобайт	m
МБ	мегабайт	мегабайта	мегабайт	m
ГБ	гигабайт	гигабайта	гигабайт	m
ТБ	терабайт	терабайта	терабайт	m
# temperature (degrees; °C / °F handled separately)
°	градус	градуса	градусов	m
# dotted unit abbreviations (Kaggle gold convention: 82 т. -> тонны, 351 с. -> секунды;
# the dot disambiguates these from the bare letters omitted above)
т.	тонна	тонны	тонн	f
с.	секунда	секунды	секунд	f
мин.	минута	минуты	минут	f
ч.	час	часа	часов	m
"""

_ENGLISH_TSV = """\
# Frequent English words / brand names -> conventional Russian rendering.
# Lookup is case-insensitive on whole Latin words; anything not listed falls
# through to letter-name spelling (acronyms) or transliteration.
# Format: <word><TAB><cyrillic>
the	зе
one	уан
two	ту
google	гугл
python	питон
ios	айос
iphone	айфон
ipad	айпад
windows	виндоус
microsoft	майкрософт
apple	эппл
facebook	фейсбук
youtube	ютуб
twitter	твиттер
instagram	инстаграм
telegram	телеграм
whatsapp	вотсап
skype	скайп
android	андроид
samsung	самсунг
intel	интел
linux	линукс
internet	интернет
online	онлайн
email	имейл
news	ньюс
ok	окей
"""

_YO_TSV = """\
# ё restoration: words whose е-spelling unambiguously stands for ё.
# Only unambiguous forms are listed (no звезды/все/вышел-type homographs).
# Format: <е-spelling><TAB><ё-spelling>; matching is word-bounded,
# the capitalization of the first letter is preserved.
еще	ещё
ее	её
нее	неё
елка	ёлка
елки	ёлки
елку	ёлку
елке	ёлке
елкой	ёлкой
зеленый	зелёный
зеленая	зелёная
зеленое	зелёное
зеленые	зелёные
желтый	жёлтый
желтая	жёлтая
желтое	жёлтое
желтые	жёлтые
черный	чёрный
черная	чёрная
черное	чёрное
черные	чёрные
легкий	лёгкий
легкая	лёгкая
легкое	лёгкое
легкие	лёгкие
тяжелый	тяжёлый
тяжелая	тяжёлая
тяжелое	тяжёлое
тяжелые	тяжёлые
теплый	тёплый
теплая	тёплая
теплое	тёплое
теплые	тёплые
твердый	твёрдый
серьезный	серьёзный
серьезно	серьёзно
определенно	определённо
лед	лёд
идет	идёт
придет	придёт
пойдет	пойдёт
найдет	найдёт
поймет	поймёт
начнет	начнёт
дает	даёт
остается	остаётся
шел	шёл
пошел	пошёл
пришел	пришёл
ушел	ушёл
нашел	нашёл
подошел	подошёл
произошел	произошёл
вперед	вперёд
полет	полёт
самолет	самолёт
самолета	самолёта
отчет	отчёт
счет	счёт
учет	учёт
расчет	расчёт
"""

def _read_lines(name):
    """Yield non-empty, non-comment, stripped lines from an embedded vocabulary."""
    for line in globals()[f'_{name.upper()}_TSV'].splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            yield line

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

# ---- Textual abbreviations ----------------------------------------------------
def _load_abbreviations():
    """Return (compiled_regex, {canonical_key: expansion})."""
    mapping = {}
    for line in _read_lines('abbreviations'):
        if '\t' not in line:
            continue
        key, value = line.split('\t', 1)
        mapping[re.sub(r'\s+', '', key).lower()] = value.strip()
    if not mapping:
        return None, {}
    # Build one alternation, longest key first; dots may be followed by spaces.
    def to_pattern(key):
        out = ''
        for ch in key:
            out += r'\.\s*' if ch == '.' else (r'\s*' if ch == ' ' else re.escape(ch))
        return out
    keys = sorted({line.split('\t', 1)[0] for line in _read_lines('abbreviations') if '\t' in line},
                  key=len, reverse=True)
    pattern = r'(?<![А-Яа-яёЁ])(?:' + '|'.join(to_pattern(k) for k in keys) + r')(?![А-Яа-яёЁ])'
    return re.compile(pattern, re.IGNORECASE), mapping

_abbr_re, _abbr_map = _load_abbreviations()

def normalize_abbreviations(text):
    """Expand common textual abbreviations (т.д. -> так далее, ул. -> улица)."""
    if not _abbr_re:
        return text
    def repl(m):
        canon = re.sub(r'\s+', '', m.group(0)).lower()
        return _abbr_map.get(canon, m.group(0))
    return _abbr_re.sub(repl, text)

# ---- Acronyms ----------------------------------------------------------------
# Whether an all-caps acronym is read as a word (НАТО) or spelled out (СССР) is a
# pronunciation-lexicon question, not a flat list. We use a vowel heuristic, which
# needs no unverified data: a vowel-less run is spelled letter by letter, anything
# pronounceable (incl. emphasised words like ВАЖНО) is read as a word. The known
# exceptions (e.g. США, read letter by letter despite vowels) would need a vetted
# lexicon, which is intentionally not bundled.
_RU_VOWELS = set('АЕЁИОУЫЭЮЯ')

def _spell_letters(token):
    return ' '.join(pronunciation_map[c] for c in token if c in pronunciation_map)

def expand_abbreviations(text):
    """Read all-caps Cyrillic acronyms: vowel-less runs (СССР) are spelled out,
    pronounceable ones (НАТО) and emphasised words (ВАЖНО) are kept as-is
    (case carries no spoken information, and the gold set preserves it)."""
    def repl(m):
        token = m.group(0)
        if not (set(token.upper()) & _RU_VOWELS):
            return _spell_letters(token.upper())
        return token
    return re.sub(r'\b[А-ЯЁ]{2,}\b', repl, text)


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
    
    # (scale value, plural forms, feminine?) from largest to smallest.
    scales = [
        (10**15, ['квадриллион', 'квадриллиона', 'квадриллионов'], False),
        (10**12, ['триллион', 'триллиона', 'триллионов'], False),
        (10**9,  ['миллиард', 'миллиарда', 'миллиардов'], False),
        (10**6,  ['миллион', 'миллиона', 'миллионов'], False),
        (10**3,  ['тысяча', 'тысячи', 'тысяч'], True),
    ]

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

    # Handle very large numbers (>= 10^18) digit by digit rather than failing.
    if n >= 10**18:
        return number_to_words_digit_by_digit(n)

    for value, forms, feminine in scales:
        count = (n // value) % 1000
        if not count:
            continue
        chunk = under_thousand(count)
        if feminine:
            if chunk[-1] == 'один':
                chunk[-1] = 'одна'
            elif chunk[-1] == 'два':
                chunk[-1] = 'две'
            if count == 1:
                chunk = chunk[:-1]  # solitary thousand: "тысяча", not "одна тысяча"
        words += chunk + [russian_plural(count, forms)]
    words += under_thousand(n % 1000)

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
    digit_words = ['ноль', 'один', 'два', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять']
    for num in detected_numbers:
        digits = num['number']
        number_value = int(digits)
        # A leading zero (e.g. "06", "007") signals a digit string, not a quantity: read it out digit by digit.
        if len(digits) > 1 and digits[0] == '0':
            normalized_number = ' '.join(digit_words[int(d)] for d in digits)
        else:
            normalized_number = number_to_words(number_value)  # self-handles >= 10^18
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
        # (forms, feminine): копейка and гривна count in the feminine (одна копейка).
        currencies = {
            'rub': ((['рубль', 'рубля', 'рублей'], False), (['копейка', 'копейки', 'копеек'], True)),
            'usd': ((['доллар', 'доллара', 'долларов'], False), (['цент', 'цента', 'центов'], False)),
            'eur': ((['евро', 'евро', 'евро'], False), (['евроцент', 'евроцента', 'евроцентов'], False)),  # Euro has invariable form
            'gbp': ((['фунт', 'фунта', 'фунтов'], False), (['пенс', 'пенса', 'пенсов'], False)),
            'uah': ((['гривна', 'гривны', 'гривен'], True), (['копейка', 'копейки', 'копеек'], True)),
        }

        # Get the correct currency units
        (main_units, main_fem), (sub_units, sub_fem) = currencies.get(currency, currencies['rub'])

        # Separate the amount into main and subunits
        main_amount = int(amount)
        sub_amount = int(round((amount - main_amount) * 100))

        # Convert numbers to words
        def count_words(n, feminine):
            words = number_to_words(n).split()
            if feminine:
                _feminine_last(words)
            return ' '.join(words)

        main_words = count_words(main_amount, main_fem) + ' ' + russian_plural(main_amount, main_units)
        sub_words = ''

        # Add subunits if present
        if sub_amount > 0:
            sub_words = count_words(sub_amount, sub_fem) + ' ' + russian_plural(sub_amount, sub_units)

        # Combine main and subunit words
        full_currency_words = main_words.strip()
        if sub_words:
            full_currency_words += ' ' + sub_words.strip()

        return full_currency_words

    # Define currency patterns for detection
    # (?![а-яё]) keeps word forms from matching inside longer words
    # (e.g. "рубля" inside "рублями", which the instrumental rule handles).
    currency_patterns = {
        'rub': [r'(\d+(?:\.\d\d)?)\s*(руб(л(ей|я|ь))?(?![а-яё])|₽)', r'(\d+(?:\.\d\d)?)\s*RUB'],
        'usd': [r'(\d+(?:\.\d\d)?)\s*(доллар(ов|а|ы)?(?![а-яё])|\$)', r'(\d+(?:\.\d\d)?)\s*USD', r'\$(\d+(?:\.\d\d)?)'],
        'eur': [r'(\d+(?:\.\d\d)?)\s*(евро(?![а-яё])|€)', r'(\d+(?:\.\d\d)?)\s*EUR', r'(\d+)\s*€'],
        'gbp': [r'(\d+(?:\.\d\d)?)\s*(фунт(ов|а|ы)?(?![а-яё])|£)', r'(\d+(?:\.\d\d)?)\s*GBP', r'£(\d+)'],
        'uah': [r'(\d+(?:\.\d\d)?)\s*(грив(ен|ны|на)(?![а-яё])|₴)', r'(\d+(?:\.\d\d)?)\s*UAH', r'(\d+)\s*₴'],
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

# Endings for an ordinal, keyed by grammatical form, for hard (-ый/-ой) and soft (-ий) stems.
_ordinal_endings = {
    'nom_n': ('ое', 'ье'), 'nom_f': ('ая', 'ья'), 'nom_pl': ('ые', 'ьи'),
    'gen': ('ого', 'ьего'), 'dat': ('ому', 'ьему'), 'prep': ('ом', 'ьем'),
    'pl': ('ых', 'ьих'), 'acc_f': ('ую', 'ью'),
}

def _inflect_ordinal(stem, form):
    """Inflect a nominative-masculine ordinal stem into the requested form
    (nom_m keeps the stem; other forms drop the -ый/-ой/-ий ending)."""
    if form == 'nom_m':
        return stem
    soft = stem.endswith('ий')  # третий
    return stem[:-2] + _ordinal_endings[form][1 if soft else 0]

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
    r'\b(\d{1,2})\s+(' + '|'.join(_MONTHS_GEN) + r')\s+(\d{3,4})(?:\s+года\b|\s*г\.(?![а-яё]))?')
_re_date_daymonth = re.compile(r'\b(\d{1,2})\s+(' + '|'.join(_MONTHS_GEN) + r')\b')
_re_year_god = re.compile(r'\b(\d{1,4})\s+(год|года|году|годе)\b')
# "2008 г." -> ordinal year + год (nominative default; "г." = город never follows digits)
_re_year_g = re.compile(r'\b(\d{3,4})\s*г\.(?![а-яё])')

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

    def year_g(m):
        y = int(m.group(1))
        if not 900 <= y <= 2199:
            return m.group(0)
        return f"{number_to_ordinal_words(y, 'nom_m')} год"

    text = _re_date_numeric.sub(numeric, text)
    text = _re_date_spelled.sub(spelled, text)
    text = _re_date_daymonth.sub(daymonth, text)
    text = _re_year_god.sub(year_god, text)
    text = _re_year_g.sub(year_g, text)
    return text

# Standalone symbols and non-Russian letters spoken by name.
# Multi-character keys come first so they are replaced before their substrings.
_symbol_map = {
    '°C': 'градусов цельсия', '°С': 'градусов цельсия', '°F': 'градусов фаренгейта',
    '±': 'плюс минус', '≈': 'приблизительно равно', '≠': 'не равно',
    '≤': 'меньше или равно', '≥': 'больше или равно', '×': 'умножить на',
    '÷': 'разделить на', '=': 'равно', '<': 'меньше', '>': 'больше',
    '‰': 'промилле', '§': 'параграф', '₿': 'биткоин', '•': ' ', '·': ' ',
    '~': 'тильда',
    '&': 'и', '#': 'решетка', '_': 'нижнее подчеркивание',
    '²': 'в квадрате', '³': 'в кубе', '№': 'номер',
    # Cyrillic letters outside the Russian alphabet
    'ї': 'и', 'і': 'и', 'ў': 'у', 'є': 'е', 'ґ': 'г',
    # Greek alphabet (lower and upper case spoken with the same name)
    'α': 'альфа', 'β': 'бета', 'γ': 'гамма', 'δ': 'дельта', 'ε': 'эпсилон',
    'ζ': 'дзета', 'η': 'эта', 'θ': 'тета', 'ι': 'йота', 'κ': 'каппа',
    'λ': 'лямбда', 'μ': 'мю', 'ν': 'ню', 'ξ': 'кси', 'ο': 'омикрон',
    'π': 'пи', 'ρ': 'ро', 'σ': 'сигма', 'ς': 'сигма', 'τ': 'тау',
    'υ': 'ипсилон', 'φ': 'фи', 'χ': 'хи', 'ψ': 'пси', 'ω': 'омега',
}
_symbol_map.update({k.upper(): v for k, v in list(_symbol_map.items()) if k.upper() != k})

def normalize_symbols(text):
    """Replace standalone symbols / foreign letters with their spoken names."""
    for sym, word in _symbol_map.items():
        if sym in text:
            text = text.replace(sym, ' ' + word + ' ')
    return re.sub(r' {2,}', ' ', text).strip() if text else text

# Place value (genitive plural) for the fractional part of a decimal, by digit count.
_decimal_places = {1: 'десятых', 2: 'сотых', 3: 'тысячных', 4: 'десятитысячных',
                   5: 'стотысячных', 6: 'миллионных'}

def _feminine_last(words):
    """Russian fractions count in the feminine: один->одна, два->две (last word only)."""
    if words and words[-1] == 'один':
        words[-1] = 'одна'
    elif words and words[-1] == 'два':
        words[-1] = 'две'
    return words

def _decimal_to_words(int_part, frac_part):
    """'7', '54' -> 'семь целых и пятьдесят четыре сотых' (None if unsupported length)."""
    place = _decimal_places.get(len(frac_part))
    if place is None:
        return None
    int_words = _feminine_last(number_to_words(int(int_part)).split())
    whole = 'целая' if (int(int_part) % 10 == 1 and int(int_part) % 100 != 11) else 'целых'
    frac_words = _feminine_last(number_to_words(int(frac_part)).split())
    return f"{' '.join(int_words)} {whole} и {' '.join(frac_words)} {place}"

def normalize_decimals(text):
    """Read decimal-comma numbers: 1,2 -> 'одна целая и две десятых'."""
    def repl(m):
        return _decimal_to_words(m.group(1), m.group(2)) or m.group(0)
    return re.sub(r'\b(\d+),(\d+)\b', repl, text)

# Russian ordinal suffix (after a hyphen) -> grammatical form, e.g. "1-й" / "190-го" / "1950-х".
_ordinal_suffix_form = {
    'й': 'nom_m', 'го': 'gen', 'му': 'dat', 'м': 'prep',
    'я': 'nom_f', 'ю': 'acc_f', 'е': 'nom_pl', 'х': 'pl',
}
_re_ordinal_suffix = re.compile(r'(\d+)[-–—](' + '|'.join(_ordinal_suffix_form) + r')\b')

# Roman numerals (>=2 chars) in Russian text are almost always ordinals; their case
# is context-dependent, so we read them in the nominative (the natural default for
# "XIX век", "Людовик XIV", "том III").
_roman_values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
_re_roman = re.compile(r'\b[MDCLXVI]{2,}\b')
_re_roman_valid = re.compile(r'^M{0,4}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})$')

def _roman_to_int(s):
    total = prev = 0
    for ch in reversed(s):
        v = _roman_values[ch]
        total += -v if v < prev else v
        prev = v
    return total

# Latin abbreviations that are also valid Roman numerals — do NOT read as ordinals.
_roman_stoplist = {'CD', 'DVD', 'MD', 'DC', 'MC', 'MI', 'MM', 'DI', 'DIV', 'MIX', 'CIV', 'LCD'}

def normalize_ordinals(text):
    """Expand ordinals written with a grammatical suffix (1-й, 190-го) and
    Roman numerals (XIX -> 'девятнадцатого')."""
    text = _re_ordinal_suffix.sub(
        lambda m: number_to_ordinal_words(int(m.group(1)), _ordinal_suffix_form[m.group(2)]), text)
    def roman(m):
        tok = m.group(0)
        if tok in _roman_stoplist or not _re_roman_valid.match(tok):
            return tok
        return number_to_ordinal_words(_roman_to_int(tok), 'nom_m')
    return _re_roman.sub(roman, text)

def _plural(n, forms):
    """Pick the Russian plural form: (one, few, many)."""
    if n % 10 == 1 and n % 100 != 11:
        return forms[0]
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return forms[1]
    return forms[2]

# Clock times: HH:MM, HH:MM:SS and English 2PM / 8pm forms.
_re_time = re.compile(r'(?<![\d:])(\d{1,2}):([0-5]\d)(?![\d:])')
_re_time_hms = re.compile(r'(?<![\d:])(\d{1,2}):([0-5]\d):([0-5]\d)(?![\d:])')
_re_time_ampm = re.compile(r'\b(\d{1,2})\s*([APap])\.?\s*[Mm]\.?(?![A-Za-zа-яё])')

def _hours_words(h):
    return f"{number_to_words(h)} {_plural(h, ('час', 'часа', 'часов'))}"

def _minutes_words(mn, forms=('минута', 'минуты', 'минут')):
    return f"{' '.join(_feminine_last(number_to_words(mn).split()))} {_plural(mn, forms)}"

def normalize_time(text):
    """Read clock times: 06:06 -> 'шесть часов шесть минут', 07:00 -> 'семь часов',
    02:25:00 -> '... ноль секунд', 2PM -> 'два часа дня'."""
    def hms(m):
        h, mn, s = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return (f"{_hours_words(h)} {_minutes_words(mn)} "
                f"{_minutes_words(s, ('секунда', 'секунды', 'секунд'))}")

    def ampm(m):
        h = int(m.group(1))
        if not 1 <= h <= 12:
            return m.group(0)
        if m.group(2).lower() == 'p':
            part = 'дня' if h < 6 or h == 12 else 'вечера'
        else:
            part = 'ночи' if h < 5 or h == 12 else 'утра'
        return f"{_hours_words(h)} {part}"

    def repl(m):
        h, mn = int(m.group(1)), int(m.group(2))
        out = _hours_words(h)
        if mn:
            out += ' ' + _minutes_words(mn)
        return out

    text = _re_time_hms.sub(hms, text)
    text = _re_time_ampm.sub(ampm, text)
    return _re_time.sub(repl, text)

# Simple fractions a/b -> numerator (feminine) + denominator as a genitive-plural ordinal.
_re_fraction = re.compile(r'\b(\d+)/(\d+)\b')

def normalize_fractions(text):
    """Read 'a/b' as 'two thirds': 2/3 -> 'две третьих', 653/26 -> '... двадцать шестых'."""
    def repl(m):
        num, den = int(m.group(1)), int(m.group(2))
        if den >= 10**12:
            return m.group(0)
        numer = ' '.join(_feminine_last(number_to_words(num).split()))
        return f"{numer} {number_to_ordinal_words(den, 'pl')}"
    return _re_fraction.sub(repl, text)

# ---- Modern / web text cleanup -----------------------------------------------
def normalize_typography(text):
    """Normalise Unicode spaces and strip markdown emphasis markers. Quotes and
    other punctuation are left intact (a TTS engine ignores them, and removing
    them would only diverge from the reference data)."""
    text = re.sub(r"[\u00a0\u2009\u202f\u2060]", " ", text)  # NBSP family -> space
    text = re.sub(r"\*\*|__|`", "", text)                      # markdown bold / code
    return text

# Email / URL: spell symbols out and let cyrrilize transliterate the latin parts.
_re_email = re.compile(r'\b[\w.+-]+@[\w-]+\.[A-Za-zА-Яа-я]{2,}\b')
_re_url = re.compile(r'\b(?:https?://|www\.)\S+|\b[\w-]+\.(?:com|ru|org|net|info|io|edu|gov|рф)\b', re.I)
_web_symbols = {'@': ' собака ', '.': ' точка ', '/': ' слэш ', ':': ' двоеточие ',
                '-': ' дефис ', '_': ' подчёркивание '}

def normalize_web(text):
    """Spell out e-mail addresses and URLs (example.com -> 'ексампле точка ком')."""
    def spell(m):
        s = m.group(0).rstrip('.,!?')
        for sym, word in _web_symbols.items():
            s = s.replace(sym, word)
        return re.sub(r' {2,}', ' ', s).strip()
    text = _re_email.sub(spell, text)
    text = _re_url.sub(spell, text)
    return re.sub(r'#([A-Za-zА-Яа-яёЁ0-9_]+)', r'хештег \1', text)

# ---- Number pre-processing ----------------------------------------------------
def normalize_number_groups(text):
    """Join space-separated digit groups into one number: '1 234 567' -> '1234567'."""
    return re.sub(r'\b\d{1,3}(?: \d{3})+\b', lambda m: m.group(0).replace(' ', ''), text)

def normalize_negatives(text):
    """Read a leading minus before a number: '-5' -> 'минус 5'."""
    return re.sub(r'(?:(?<=^)|(?<=[\s(\[]))[-−](\d)', r'минус \1', text)

# Quantity multipliers with grammatical agreement (handled here, not in the flat
# abbreviation list, so the number agrees: 1 млн -> один миллион, 5 млн -> пять миллионов).
_multipliers = {
    'тыс': (['тысяча', 'тысячи', 'тысяч'], True),
    'млн': (['миллион', 'миллиона', 'миллионов'], False),
    'млрд': (['миллиард', 'миллиарда', 'миллиардов'], False),
    'трлн': (['триллион', 'триллиона', 'триллионов'], False),
}
_re_multiplier = re.compile(r'\b(\d+(?:,\d+)?)\s*(тыс|млн|млрд|трлн)\.?(?![а-яё])', re.I)

def normalize_multipliers(text):
    def repl(m):
        forms, feminine = _multipliers[m.group(2).lower()]
        if ',' in m.group(1):
            # decimal count takes the genitive singular: 2,7 млрд -> ... миллиарда
            ip, fp = m.group(1).split(',', 1)
            words = _decimal_to_words(ip, fp)
            if words is None:
                return m.group(0)
            return words + ' ' + forms[1]
        n = int(m.group(1))
        words = number_to_words(n).split()
        if feminine:
            _feminine_last(words)
        return ' '.join(words) + ' ' + _plural(n, forms)
    return _re_multiplier.sub(repl, text)

def normalize_percent(text):
    """Read percentages: 50% -> 'пятьдесят процентов', 3,5% -> '... процента'."""
    forms = ('процент', 'процента', 'процентов')
    def repl(m):
        num = m.group(1)
        if ',' in num or '.' in num:
            ip, fp = re.split(r'[.,]', num, 1)
            words = _decimal_to_words(ip, fp)
            return (words + ' процента') if words else m.group(0)
        n = int(num)
        return f"{number_to_words(n)} {_plural(n, forms)}"
    return re.sub(r'(\d+(?:[.,]\d+)?)\s*%', repl, text)

# ---- Units of measurement -----------------------------------------------------
def _load_measurements():
    units = {}
    for line in _read_lines('measurements'):
        parts = line.split('\t')
        if len(parts) == 5:
            ab, one, few, many, gender = parts
            units[ab] = (one, few, many, gender)
    return units

_measurements = _load_measurements()
_UNIT_ALT = '|'.join(re.escape(u) for u in sorted(_measurements, key=len, reverse=True))
# Case-sensitive, longest unit first, number required before the unit, and no
# letter immediately after (so "м" does not fire inside "метр", "°" not in "°C").
_re_measure = re.compile(
    r'(?<![\d.,])(\d+(?:,\d+)?)\s*(' + _UNIT_ALT +
    r')(?![A-Za-zА-Яа-яёЁ])') if _measurements else None

def normalize_measurements(text):
    """Read a number followed by a unit, agreeing in count: 5 кг -> 'пять
    килограммов', 2 кг -> 'два килограмма', 1,5 км -> '... километра'."""
    if not _re_measure:
        return text
    def repl(m):
        one, few, many, gender = _measurements[m.group(2)]
        if ',' in m.group(1):
            # decimal count takes the genitive singular: 1,5 км -> ... километра
            ip, fp = m.group(1).split(',', 1)
            words = _decimal_to_words(ip, fp)
            if words is None:
                return m.group(0)
            return words + ' ' + few
        n = int(m.group(1))
        words = number_to_words(n).split()
        if gender == 'f':
            _feminine_last(words)
        return ' '.join(words) + ' ' + _plural(n, (one, few, many))
    return _re_measure.sub(repl, text)

# ---- Cardinal declension (closed-class morphology, table-driven) --------------
_CASES = ('gen', 'dat', 'instr', 'prep')
_CASE_FORMS = {
    'ноль': ('нуля', 'нулю', 'нулём', 'нуле'),
    'один': ('одного', 'одному', 'одним', 'одном'),
    'одна': ('одной', 'одной', 'одной', 'одной'),
    'два': ('двух', 'двум', 'двумя', 'двух'),
    'две': ('двух', 'двум', 'двумя', 'двух'),
    'три': ('трёх', 'трём', 'тремя', 'трёх'),
    'четыре': ('четырёх', 'четырём', 'четырьмя', 'четырёх'),
    'восемь': ('восьми', 'восьми', 'восьмью', 'восьми'),
    'сорок': ('сорока',) * 4,
    'девяносто': ('девяноста',) * 4,
    'сто': ('ста',) * 4,
    'пятьдесят': ('пятидесяти', 'пятидесяти', 'пятьюдесятью', 'пятидесяти'),
    'шестьдесят': ('шестидесяти', 'шестидесяти', 'шестьюдесятью', 'шестидесяти'),
    'семьдесят': ('семидесяти', 'семидесяти', 'семьюдесятью', 'семидесяти'),
    'восемьдесят': ('восьмидесяти', 'восьмидесяти', 'восьмьюдесятью', 'восьмидесяти'),
    'двести': ('двухсот', 'двумстам', 'двумястами', 'двухстах'),
    'триста': ('трёхсот', 'трёмстам', 'тремястами', 'трёхстах'),
    'четыреста': ('четырёхсот', 'четырёмстам', 'четырьмястами', 'четырёхстах'),
    'пятьсот': ('пятисот', 'пятистам', 'пятьюстами', 'пятистах'),
    'шестьсот': ('шестисот', 'шестистам', 'шестьюстами', 'шестистах'),
    'семьсот': ('семисот', 'семистам', 'семьюстами', 'семистах'),
    'восемьсот': ('восьмисот', 'восьмистам', 'восьмьюстами', 'восьмистах'),
    'девятьсот': ('девятисот', 'девятистам', 'девятьюстами', 'девятистах'),
    'тысяча': ('тысячи', 'тысяче', 'тысячей', 'тысяче'),
    'тысячи': ('тысяч', 'тысячам', 'тысячами', 'тысячах'),
    'тысяч': ('тысяч', 'тысячам', 'тысячами', 'тысячах'),
}
# Soft-sign numerals decline regularly: пять -> пяти / пятью (восемь is above).
for _w in ('пять', 'шесть', 'семь', 'девять', 'десять', 'одиннадцать', 'двенадцать',
           'тринадцать', 'четырнадцать', 'пятнадцать', 'шестнадцать', 'семнадцать',
           'восемнадцать', 'девятнадцать', 'двадцать', 'тридцать'):
    _CASE_FORMS[_w] = (_w[:-1] + 'и', _w[:-1] + 'и', _w[:-1] + 'ью', _w[:-1] + 'и')
for _s in ('миллион', 'миллиард', 'триллион', 'квадриллион'):
    _CASE_FORMS[_s] = (_s + 'а', _s + 'у', _s + 'ом', _s + 'е')
    _CASE_FORMS[_s + 'а'] = _CASE_FORMS[_s + 'ов'] = (_s + 'ов', _s + 'ам', _s + 'ами', _s + 'ах')

def number_to_words_case(n, case):
    """Cardinal in an oblique case: 500/'gen' -> 'пятисот'."""
    idx = _CASES.index(case)
    return ' '.join(_CASE_FORMS.get(w, (w,) * 4)[idx] for w in number_to_words(n).split())

# ---- Context-governed case (preposition / oblique noun ending) ----------------
_prep_case = {
    'около': 'gen', 'более': 'gen', 'менее': 'gen', 'свыше': 'gen', 'от': 'gen',
    'до': 'gen', 'из': 'gen', 'без': 'gen', 'после': 'gen',
    'к': 'dat', 'о': 'prep', 'об': 'prep',
}
# Longest alternative first; the trailing guard refuses decimals, times, ranges
# and percentages, which keep their own rules.
_re_prep_num = re.compile(
    r'(?<![А-Яа-яёЁ-])(около|после|более|менее|свыше|без|от|до|из|об|к|о)'
    r'\s+(\d+)(?:\s*(' + _UNIT_ALT + r'))?(?![\d.,:%–—-])(?![A-Za-zА-Яа-яёЁ])', re.I)
# "с 500 рублями": instrumental signalled by the noun ending.
_re_instr_num = re.compile(r'(?<![А-Яа-яёЁ])([Сс]о?)\s+(\d+)\s+([а-яё]{3,}(?:ами|ями))\b')
# A number directly before an obliquely-inflected noun agrees with it.
_re_num_oblique_noun = re.compile(r'\b(\d+)\s+([а-яё]{3,}(?:ами|ями|ах|ях))\b')
_oblique_suffix_case = {'ами': 'instr', 'ями': 'instr', 'ах': 'prep', 'ях': 'prep'}

def normalize_case_context(text):
    """Inflect a number to the case its context dictates: 'около 500 км' ->
    'около пятисот километров', 'к 5' -> 'к пяти', 'с 500 рублями' -> 'с пятьюстами рублями'."""
    def prep(m):
        case = _prep_case[m.group(1).lower()]
        out = m.group(1) + ' ' + number_to_words_case(int(m.group(2)), case)
        if m.group(3):
            if case != 'gen':
                return m.group(0)  # unit in dat/prep needs noun declension; leave it
            out += ' ' + _measurements[m.group(3)][2]  # genitive plural == many form
        return out

    def instr(m):
        return f"{m.group(1)} {number_to_words_case(int(m.group(2)), 'instr')} {m.group(3)}"

    def oblique(m):
        suffix = next(s for s in ('ами', 'ями', 'ах', 'ях') if m.group(2).endswith(s))
        return f"{number_to_words_case(int(m.group(1)), _oblique_suffix_case[suffix])} {m.group(2)}"

    text = _re_instr_num.sub(instr, text)
    text = _re_prep_num.sub(prep, text)
    return _re_num_oblique_noun.sub(oblique, text)

# ---- Bare-number ordinals from a trigger noun ----------------------------------
# A singular trigger noun right after a number signals an ordinal reading
# ("2 место" is второе место; the cardinal would demand "места"/"мест").
_ordinal_trigger = {
    'место': 'nom_n', 'этаж': 'nom_m', 'класс': 'nom_m', 'век': 'nom_m',
    'том': 'nom_m', 'курс': 'nom_m', 'раунд': 'nom_m', 'сезон': 'nom_m',
    'этап': 'nom_m', 'тур': 'nom_m', 'разряд': 'nom_m', 'подъезд': 'nom_m',
}
_re_ordinal_trigger = re.compile(
    r'\b(\d{1,4})\s+(' + '|'.join(_ordinal_trigger) + r')\b(?![а-яё])')

def normalize_ordinal_triggers(text):
    def repl(m):
        return f"{number_to_ordinal_words(int(m.group(1)), _ordinal_trigger[m.group(2)])} {m.group(2)}"
    return _re_ordinal_trigger.sub(repl, text)

# ---- Compound number adjectives: 5-летний -> пятилетний ------------------------
# The numeral joins the adjective as a genitive prefix (sole exceptions below).
_compound_prefix_override = {'один': 'одно', 'одна': 'одно', 'девяносто': 'девяносто',
                             'сто': 'сто', 'тысяча': 'тысяче'}
_re_compound = re.compile(
    r'\b(\d+)-([а-яё]{2,}(?:ий|ый|ой|ая|яя|ое|ее|ые|ие|ого|его|ому|ему|ым|им|ом|ем|ую|юю|ых|их|ыми|ими))\b')

def normalize_compounds(text):
    def repl(m):
        words = number_to_words(int(m.group(1))).split()
        prefix = ''.join(_compound_prefix_override.get(w, _CASE_FORMS.get(w, (w,))[0])
                         for w in words)
        return prefix + m.group(2)
    return _re_compound.sub(repl, text)

# ---- Numeric ranges ------------------------------------------------------------
_re_year_range = re.compile(r'\b(\d{3,4})\s*[-–—]\s*(\d{3,4})\s*(?:гг\.?|годы)(?![а-яё])')
_re_century_range = re.compile(r'\b([MDCLXVI]{1,6})\s*[-–—]\s*([MDCLXVI]{1,6})\s*вв\.?(?![а-яё])')
_re_num_range = re.compile(r'(?<=\d)\s*[–—]\s*(?=\d)')  # en/em dash only: hyphen is phones/ISBN

def normalize_ranges(text):
    """Read ranges: '1941—1945 гг.' -> '... первый ... пятый годы', '5–10' -> '5 10'."""
    def years(m):
        return (f"{number_to_ordinal_words(int(m.group(1)), 'nom_m')} "
                f"{number_to_ordinal_words(int(m.group(2)), 'nom_m')} годы")

    def centuries(m):
        if not (_re_roman_valid.match(m.group(1)) and _re_roman_valid.match(m.group(2))):
            return m.group(0)
        return (f"{number_to_ordinal_words(_roman_to_int(m.group(1)), 'nom_m')} "
                f"{number_to_ordinal_words(_roman_to_int(m.group(2)), 'nom_m')} века")

    text = _re_year_range.sub(years, text)
    text = _re_century_range.sub(centuries, text)
    return _re_num_range.sub(' ', text)

# ---- Scores (after clock times have been consumed): 3:1 -> 'три один' -----------
_re_score = re.compile(r'\b(\d{1,2}):(\d{1,2})\b')

def normalize_scores(text):
    return _re_score.sub(
        lambda m: f"{number_to_words(int(m.group(1)))} {number_to_words(int(m.group(2)))}", text)

# ---- Arithmetic: '+' between numbers (=, ×, ÷ live in the symbol map) ----------
def normalize_math(text):
    return re.sub(r'(?<=\d)\s*\+\s*(?=\d)', ' плюс ', text)

# ---- Structural references before a number: ст. 158 -> статья 158 ---------------
_section_abbr = {'ст': 'статья', 'пп': 'подпункт', 'п': 'пункт',
                 'рис': 'рисунок', 'табл': 'таблица', 'гл': 'глава'}
_re_section = re.compile(r'(?<![А-Яа-яёЁ])(ст|пп|табл|рис|гл|п)\.\s*(?=\d)', re.I)

def normalize_sections(text):
    return _re_section.sub(lambda m: _section_abbr[m.group(1).lower()] + ' ', text)

# ---- Versions / IP addresses: dot-separated numbers read with 'точка' ----------
_re_ip = re.compile(r'\b\d+(?:\.\d+){2,}\b')
# A single dot reads as a version only after a Latin product name (Python 3.11);
# bare N.N stays untouched (could be an English-style decimal).
_re_version = re.compile(r'\b([A-Za-z][\w-]*\s+)(\d+(?:\.\d+)+)\b')

def _read_dotted(num):
    digit_words = ['ноль', 'один', 'два', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять']
    def part(p):
        if len(p) > 1 and p[0] == '0':
            return ' '.join(digit_words[int(d)] for d in p)
        return number_to_words(int(p))
    return ' точка '.join(part(p) for p in num.split('.'))

def normalize_versions(text):
    text = _re_version.sub(lambda m: m.group(1) + _read_dotted(m.group(2)), text)
    return _re_ip.sub(lambda m: _read_dotted(m.group(0)), text)

# ---- English words and Latin acronyms ------------------------------------------
def _load_english():
    mapping = {}
    for line in _read_lines('english'):
        if '\t' in line:
            key, value = line.split('\t', 1)
            mapping[key.strip().lower()] = value.strip()
    return mapping

_english_words = _load_english()
_re_latin_word = re.compile(r"\b[A-Za-z][A-Za-z'’-]*\b")

# English letter names for spelled-out Latin acronyms (GPS -> джи пи эс).
_latin_letter_names = {
    'a': 'эй', 'b': 'би', 'c': 'си', 'd': 'ди', 'e': 'и', 'f': 'эф', 'g': 'джи',
    'h': 'эйч', 'i': 'ай', 'j': 'джей', 'k': 'кей', 'l': 'эл', 'm': 'эм', 'n': 'эн',
    'o': 'оу', 'p': 'пи', 'q': 'кью', 'r': 'ар', 's': 'эс', 't': 'ти', 'u': 'ю',
    'v': 'ви', 'w': 'дабл ю', 'x': 'экс', 'y': 'уай', 'z': 'зед',
}
_re_latin_acronym = re.compile(r'\b[A-Z]{2,6}\b')

def normalize_english(text):
    """Dictionary words get their conventional rendering (Google -> гугл); all-caps
    acronyms that are not pronounceable as a word (a vowel-less stretch of two or
    more consonants) are spelled with English letter names (GPS -> джи пи эс).
    Everything else falls through to transliteration."""
    def word(m):
        return _english_words.get(m.group(0).lower(), m.group(0))

    def acronym(m):
        low = m.group(0).lower()
        if low in _english_words:
            return m.group(0)  # dictionary handled / will handle it
        if not set(low) & set('aeiou') or re.search(r'[^aeiou]{2}', low):
            return ' '.join(_latin_letter_names[c] for c in low)
        return m.group(0)

    text = _re_latin_word.sub(word, text)
    return _re_latin_acronym.sub(acronym, text)

# ---- ё restoration (unambiguous е-spellings only) -------------------------------
def _load_yo():
    mapping = {}
    for line in _read_lines('yo'):
        if '\t' in line:
            key, value = line.split('\t', 1)
            mapping[key.strip().lower()] = value.strip()
    return mapping

_yo_map = _load_yo()
_re_yo = re.compile(r'\b(' + '|'.join(sorted(_yo_map, key=len, reverse=True)) + r')\b',
                    re.I) if _yo_map else None

def restore_yo(text):
    """Restore ё in words where the е-spelling is unambiguous: еще -> ещё."""
    if not _re_yo:
        return text
    def repl(m):
        rep = _yo_map.get(m.group(0).lower())
        if rep is None:
            return m.group(0)
        if m.group(0)[0].isupper():
            rep = rep[0].upper() + rep[1:]
        return rep
    return _re_yo.sub(repl, text)

# ---- Uncertainty detection (router / abstention) ------------------------------
# normalize_russian() always returns its best guess. flag_uncertain() returns the
# spans where that guess rests on information the rules cannot recover — so a
# caller can route just those spans (or the sentences holding them) to a stronger
# method (LLM / neural normaliser) and trust the rest. Detectors read the INPUT
# only; they never consult the gold. Each is a structural ambiguity: a reading
# that needs a cue which is absent from the text.

# Abbreviations with several common expansions that context (not rules) must pick.
_MULTISENSE_ABBR = {
    'г': 'год / город / грамм / господин', 'в': 'век / восток / в (предлог)',
    'кв': 'квартира / квартал / квадратный', 'т': 'том / тонна / так',
    'с': 'секунда / страница / село / с (предлог)', 'д': 'дом / деревня / дочь',
    'к': 'комната / корпус / к (предлог)', 'об': 'оборот / область / об (предлог)',
}
_re_uncertain_abbr = re.compile(
    r'(?<![А-Яа-яёЁ])(' + '|'.join(sorted(_MULTISENSE_ABBR, key=len, reverse=True)) +
    r')\.(?![а-яё])', re.I)
_re_uncertain_latin = re.compile(r"\b[A-Za-z][A-Za-z'’-]*\b")
_re_uncertain_roman = re.compile(r'\b[MDCLXVI]{2,}\b')
_re_uncertain_year = re.compile(r'(?<![\d.,])(\d{4})(?![\d.,])')
# A bare integer with no surrounding cue (preposition, unit, ordinal suffix,
# year/trigger noun) — its grammatical case and cardinal/ordinal status are
# genuinely undetermined; the rules default to a nominative cardinal.
_GOVERNORS = set(_prep_case) | {'в', 'на', 'за', 'по', 'с', 'со', 'у', 'из'}
_re_uncertain_int = re.compile(r'(?<![\d.,:%-])(\d{1,4})(?![\d.,:%/-])')
_CARDINAL_CUE_AFTER = re.compile(r'^\s*(?:' + _UNIT_ALT + r'|%|руб|коп|год|тыс|млн|млрд|'
                                 r'человек|раз|[-–—])', re.I)

def flag_uncertain(text):
    """Return a list of (start, end, original, reason) spans where the
    normalisation is a guess the rules cannot verify. Empty list == high
    confidence in the whole string. Offsets index the input `text`."""
    spans = []
    seen = set()
    def add(s, e, why):
        if (s, e) not in seen:
            seen.add((s, e))
            spans.append((s, e, text[s:e], why))

    for m in _re_uncertain_abbr.finditer(text):
        add(m.start(), m.end(), 'ambiguous abbreviation (' +
            _MULTISENSE_ABBR[m.group(1).lower()] + ')')
    for m in _re_uncertain_latin.finditer(text):
        w = m.group(0)
        if re.fullmatch(r'[A-Z]{2,6}', w) or w.lower() in _english_words:
            continue  # handled: letter-name acronym or dictionary word
        add(m.start(), m.end(), 'foreign word (transliteration is approximate)')
    for m in _re_uncertain_roman.finditer(text):
        w = m.group(0)
        if w not in _roman_stoplist and _re_roman_valid.match(w):
            add(m.start(), m.end(), 'Roman numeral (case defaults to nominative)')
    for m in _re_uncertain_year.finditer(text):
        if not 1000 <= int(m.group(1)) <= 2099:
            continue
        after = text[m.end():m.end() + 8]
        if re.match(r'\s*(?:год|года|году|годе|г\.|гг\.|г\b|вв?\.)', after):
            continue  # год-context resolves year reading
        add(m.start(), m.end(), 'four-digit number (year or cardinal?)')

    # Bare integers with no resolving cue on either side.
    words_before_end = {m.end(): m.group(0).lower()
                        for m in re.finditer(r'[А-Яа-яёЁA-Za-z]+', text)}
    for m in _re_uncertain_int.finditer(text):
        s, e = m.start(), m.end()
        if (s, e) in seen:
            continue  # already flagged as a year
        if len(m.group(1)) > 1 and m.group(1)[0] == '0':
            continue  # leading zero -> confident digit string
        left = text[:s].rstrip()
        prev = re.search(r'[А-Яа-яёЁ]+$', left)
        if prev and prev.group(0).lower() in _GOVERNORS:
            continue  # governed by a preposition -> case resolved
        if _CARDINAL_CUE_AFTER.match(text[e:]):
            continue  # unit / currency / year / range follows -> handled
        add(s, e, 'bare number (case / cardinal-vs-ordinal undetermined)')

    spans.sort()
    return spans

def normalize_russian(text):
    text = normalize_typography(text)
    text = normalize_web(text)
    text = normalize_abbreviations(text)
    text = normalize_sections(text)
    text = normalize_number_groups(text)
    text = normalize_ranges(text)
    text = normalize_dates(text)
    text = normalize_case_context(text)
    text = normalize_ordinal_triggers(text)
    text = normalize_compounds(text)
    text = normalize_ordinals(text)
    text = normalize_time(text)
    text = normalize_scores(text)         # leftover N:M after clock times
    text = normalize_fractions(text)
    text = normalize_percent(text)
    text = normalize_multipliers(text)
    text = normalize_measurements(text)   # before acronym speller (ГБ/МБ are units, not letters)
    text = expand_abbreviations(text)
    text = normalize_symbols(text)
    text = normalize_math(text)
    text = normalize_decimals(text)
    text = currency_normalization(text)
    text = normalize_text_with_phone_numbers(text)
    text = normalize_versions(text)       # after dates and currency claim their dots
    text = normalize_negatives(text)
    text = normalize_text_with_numbers(text)
    text = normalize_english(text)
    text = cyrrilize(text)
    text = restore_yo(text)
    text = re.sub(r' {2,}', ' ', text).strip()
    # ё is kept intentionally (it carries pronunciation for TTS); the reference
    # data drops it, so evaluation should compare ё/е-insensitively.
    return text

def _cli():
    """Read text from stdin, write normalized text to stdout."""
    import sys
    data = sys.stdin.read()
    sys.stdout.write(normalize_russian(data) + ('\n' if data.endswith('\n') else ''))

if __name__ == '__main__':
    _cli()