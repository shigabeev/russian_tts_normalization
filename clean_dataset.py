"""De-Google-ify the gold of the Russian text-normalization set.

The Kestrel/Sproat gold uses annotation artifacts that no TTS-facing target
should contain:
  * `_trans` / `_latin` / `_letter` — per-character spelling markers
    (`э_trans л_trans` is "Elvis" spelled out); the marker is dropped, the
    letter it is attached to is kept.
  * `sil` — a silence/pause token (punctuation, and separators in phone/ISBN
    numbers); kept but rendered as an explicit, unmissable pause marker `<p>`.

This is a STRICT, deterministic transformation: it only deletes the marker
words and maps `sil` -> "<p>". It never rewrites, re-spells, or re-normalizes
anything, so it cannot introduce new mistakes. Every row is checked so that its
cleaned content (minus the inserted `<p>` markers) equals the original with the
marker words and `sil` removed; the run aborts if that ever fails.

For genuinely naturalising the ~5% of foreign-word rows (e.g. an URL spelled
letter by letter), regenerate from the `before` column with a normalizer — but
that injects the normalizer's error rate and must be reviewed, so it is NOT
done here.

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

def clean(text):
    """Remove verbatim markers and render `sil` as an explicit pause. Deterministic."""
    text = _MARKER_RE.sub('', text)
    text = _SIL_RE.sub(PAUSE, text)
    text = re.sub(r'\s{2,}', ' ', text)       # collapse runs of spaces
    return text.strip()


def _content(text):
    """Alphanumeric content only — used to prove nothing but markers changed."""
    return ''.join(c for c in text if c.isalnum())


def _content_after_removal(text):
    """Original content with exactly the marker words and `sil` removed."""
    text = _MARKER_RE.sub('', text)
    text = _SIL_RE.sub(' ', text)
    return _content(text)


def verify_row(original):
    """True iff clean() changed nothing but the artifacts: its content, minus the
    inserted pause markers, must equal the original minus markers and `sil`."""
    return _content(clean(original).replace(PAUSE, ' ')) == _content_after_removal(original)


def selftest():
    cases = [
        ('э_trans л_trans в_trans и_trans с_trans', 'э л в и с'),
        ('t h g точка р_trans у_trans', 't h g точка р у'),
        ('девятьсот семьдесят восемь sil пять sil три',
         'девятьсот семьдесят восемь <p> пять <p> три'),
        ('ноль sil восемьсот семьдесят семь', 'ноль <p> восемьсот семьдесят семь'),
        ('Москва', 'Москва'),                       # untouched
        ('тысяча восемьсот шестьдесят второй год',   # untouched
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
