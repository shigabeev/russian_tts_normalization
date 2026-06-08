"""De-Google-ify the gold of the Russian text-normalization set.

The Kestrel/Sproat gold uses artifacts that no TTS-facing target should contain.
This converts the gold to a plausible, fully-Cyrillic spoken form — deterministic,
no models:
  * `_trans` / `_latin` / `_letter` — per-character spelling markers
    (`э_trans л_trans` is "Elvis" spelled out); the marker is dropped, the
    letter it is attached to is kept.
  * `sil` — a silence/pause token (punctuation, and separators in phone/ISBN
    numbers); kept but rendered as an explicit, unmissable pause marker `<p>`.
  * leftover Latin letters — the gold leaves acronyms as bare Latin (`t v`,
    `i s b n`, `c`, `p`), which a Russian voice cannot read; each Latin letter is
    mapped to its Russian letter-name (`t`->`ти`, `v`->`ви`, `i`->`ай` ...).

Determinism / safety:
  * Marker/`sil` handling is content-preserving and verified per row (the run
    aborts if any Cyrillic/digit content changes).
  * Latin -> letter-name uses a fixed 26-letter table (no model); the output is
    verified to contain no Latin at all, and original Cyrillic is left untouched.

Usage:
    python3 clean_dataset.py IN.csv OUT.csv      # clean the `after` column
    python3 clean_dataset.py --selftest
"""
import csv
import re
import sys

csv.field_size_limit(10 ** 7)

# Sproat/Kestrel verbatim spelling markers (suffix on a single character/token).
_MARKER_RE = re.compile(r'_(?:trans|latin|letter)\b')
# A standalone `sil` token (never a substring of a real Russian word).
_SIL_RE = re.compile(r'(?<!\S)sil(?!\S)')


PAUSE = '<p>'  # explicit, unmissable pause marker that replaces `sil`

# Latin letter -> Russian letter-name (the standard English-alphabet reading).
# Source: NVIDIA NeMo-text-processing ru/data/latin_to_cyrillic.tsv (Apache-2.0),
# English-name variant. This is how a Russian voice reads Latin acronyms (TV ->
# "ти ви", ISBN -> "ай эс би эн").
_LATIN_NAME = {
    'a': 'эй', 'b': 'би', 'c': 'си', 'd': 'ди', 'e': 'и', 'f': 'эф', 'g': 'джи',
    'h': 'эйч', 'i': 'ай', 'j': 'джей', 'k': 'кей', 'l': 'эл', 'm': 'эм', 'n': 'эн',
    'o': 'оу', 'p': 'пи', 'q': 'кью', 'r': 'ар', 's': 'эс', 't': 'ти', 'u': 'ю',
    'v': 'ви', 'w': 'дабл-ю', 'x': 'экс', 'y': 'уай', 'z': 'зет',
}

_SENTINEL = '\x00'  # Latin-free stand-in for the pause while transliterating

def _clean_markers(text):
    """Remove verbatim markers and render `sil` as an explicit pause. Content-preserving."""
    text = _MARKER_RE.sub('', text)
    text = _SIL_RE.sub(PAUSE, text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()

def _translit_latin(text):
    """Replace each Latin letter with its Russian letter-name."""
    if not re.search(r'[A-Za-z]', text):
        return text
    text = re.sub(r'[A-Za-z]', lambda m: ' ' + _LATIN_NAME[m.group(0).lower()] + ' ', text)
    text = re.sub(r'\s+([,.;:!?])', r'\1', text)   # drop space before punctuation
    return re.sub(r'\s{2,}', ' ', text).strip()

def clean(text):
    """Full deterministic conversion to a plausible, fully-Cyrillic spoken form.
    `sil` goes to a Latin-free sentinel during transliteration so the `<p>` marker
    (which itself contains a Latin 'p') is not mangled."""
    text = _MARKER_RE.sub('', text)
    text = _SIL_RE.sub(_SENTINEL, text)
    text = _translit_latin(text)
    text = text.replace(_SENTINEL, PAUSE)
    return re.sub(r'\s{2,}', ' ', text).strip()


def _content(text):
    """Alphanumeric content only — used to prove nothing but markers changed."""
    return ''.join(c for c in text if c.isalnum())


def _content_after_removal(text):
    """Original content with exactly the marker words and `sil` removed."""
    text = _MARKER_RE.sub('', text)
    text = _SIL_RE.sub(' ', text)
    return _content(text)


def verify_row(original):
    """Two guarantees: (1) the marker/sil pass preserves all Cyrillic/digit content
    (its content, minus inserted pauses, equals the original minus markers and sil);
    (2) the final output contains no Latin (the letter-name pass only touches Latin,
    never original Cyrillic)."""
    marker_ok = _content(_clean_markers(original).replace(PAUSE, ' ')) == _content_after_removal(original)
    no_latin = not re.search(r'[A-Za-z]', clean(original).replace(PAUSE, ' '))  # <p> marker exempt
    return marker_ok and no_latin


def selftest():
    cases = [
        ('э_trans л_trans в_trans и_trans с_trans', 'э л в и с'),   # _trans -> Cyrillic kept
        ('t h g точка р_trans у_trans', 'ти эйч джи точка р у'),     # bare Latin -> letter-names
        ('девятьсот семьдесят восемь sil пять sil три',
         'девятьсот семьдесят восемь <p> пять <p> три'),
        ('ноль sil восемьсот семьдесят семь', 'ноль <p> восемьсот семьдесят семь'),
        ('t v', 'ти ви'),                            # leftover Latin acronym
        ('i s b n', 'ай эс би эн'),
        ('c l', 'си эл'),
        ('p', 'пи'), ('i', 'ай'), ('H', 'эйч'),      # the short single-letter failures
        ('tvРоссия', 'ти ви Россия'),                # glued source token
        ('Москва', 'Москва'),                        # untouched
        ('тысяча восемьсот шестьдесят второй год',    # untouched
         'тысяча восемьсот шестьдесят второй год'),
    ]
    ok = True
    for src, want in cases:
        got = clean(src)
        flag = 'OK ' if got == want else 'XX '
        if got != want:
            ok = False
        print(f"{flag}{src!r} -> {got!r}" + ('' if got == want else f"  WANT {want!r}"))
        assert verify_row(src), f"verify failed on {src!r}"
    print('selftest passed' if ok else 'selftest FAILED')
    sys.exit(0 if ok else 1)


def main():
    if '--selftest' in sys.argv:
        selftest()
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    if len(args) != 2:
        sys.exit(__doc__)
    src_path, out_path = args

    # Quote exactly like the source (strings quoted, bare integers left alone) so
    # the output diffs against the original on the cleaned `after` field ONLY.
    def quote(field):
        if re.fullmatch(r'-?\d+', field):
            return field
        return '"' + field.replace('"', '""') + '"'

    n = changed = unsafe = 0
    examples = []
    with open(src_path, encoding='utf-8', newline='') as fin, \
            open(out_path, 'w', encoding='utf-8', newline='') as fout:
        reader = csv.reader(fin)
        header = next(reader)
        fout.write(','.join(quote(c) for c in header) + '\n')
        try:
            col = header.index('after')
        except ValueError:
            sys.exit(f"no 'after' column in header: {header}")
        for row in reader:
            n += 1
            original = row[col]
            cleaned = clean(original)
            if not verify_row(original):          # must never happen
                unsafe += 1
            if cleaned != original:
                changed += 1
                if len(examples) < 12 and ('_' in original or 'sil' in original.split()):
                    examples.append((original, cleaned))
            row[col] = cleaned
            fout.write(','.join(quote(c) for c in row) + '\n')

    print(f"rows: {n:,}   changed: {changed:,} ({100*changed/max(n,1):.2f}%)   "
          f"unsafe (content altered): {unsafe}")
    if unsafe:
        sys.exit("ABORT: cleaning altered content on some rows — do not use output")
    print("\nexamples:")
    for src, dst in examples:
        print(f"  {src!r}\n   -> {dst!r}")
    print(f"\nwrote {out_path}")


if __name__ == '__main__':
    main()
