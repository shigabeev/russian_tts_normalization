"""OPTIONAL, review-only: naturalise foreign-word rows with RUNorm, side by side.

The deterministic cleaner (clean_dataset.py) leaves foreign words spelled out
letter by letter, because turning "Tiberius" into "тибериус" needs a model and a
model can err. This script runs RUNorm (a neural normalizer,
https://github.com/Den4ikAI/runorm) over the `before` column of the rows whose
input contains Latin letters, and writes a SIDE-BY-SIDE review file:

    sentence_id, token_id, class, before, after_gold_clean, after_runorm, differs

It NEVER overwrites the verified gold — the output is a separate file for a human
to review and selectively accept. Treat `after_runorm` as a suggestion, not truth.

Requires (in a venv, not the system Python):  pip install runorm
Usage:
    python3 runorm_pass.py IN.csv REVIEW.csv [--limit N] [--model small|medium|big] [--device cpu|cuda]
"""
import csv
import re
import sys

from clean_dataset import clean

csv.field_size_limit(10 ** 7)


def _patch_runorm_token_type_ids():
    """RUNorm's anglicism path crashes on transformers>=5 (token_type_ids is gone
    from the tokenizer output). Reinstall the method with a safe pop so the fix
    travels with this script instead of editing site-packages."""
    from runorm.runorm import RUNorm

    def predict_anglicizms(self, prompt):
        data = self.angl_tokenizer("<pad><pad><pad>" + prompt, return_tensors="pt")
        data.pop("token_type_ids", None)
        data = {k: v.to(self.angl_model.device) for k, v in data.items()}
        output_ids = self.angl_model.generate(
            **data, do_sample=False, max_new_tokens=128, repetition_penalty=1.0)[0]
        out = self.angl_tokenizer.decode(output_ids.tolist())
        out = out.replace("<s>", "").replace("</s>", "").replace("<pad>", "").strip()
        return self.kirillizator(out)

    RUNorm.predict_anglicizms = predict_anglicizms


_HAS_LATIN = re.compile(r'[A-Za-z]')


def main():
    flags = {a.split('=')[0]: a.split('=')[1] for a in sys.argv[1:] if a.startswith('--') and '=' in a}
    bare = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(bare) != 2:
        sys.exit(__doc__)
    src_path, out_path = bare
    limit = int(flags.get('--limit', 500))
    model_size = flags.get('--model', 'small')
    device = flags.get('--device', 'cpu')

    _patch_runorm_token_type_ids()
    from runorm import RUNorm
    norm = RUNorm()
    norm.load(model_size=model_size, device=device)

    n = done = differs = 0
    with open(src_path, encoding='utf-8', newline='') as fin, \
            open(out_path, 'w', encoding='utf-8', newline='') as fout:
        reader = csv.reader(fin)
        writer = csv.writer(fout)
        header = next(reader)
        idx = {name: header.index(name) for name in ('before', 'after') if name in header}
        has_ids = 'sentence_id' in header and 'token_id' in header
        cls_i = header.index('class') if 'class' in header else None
        writer.writerow(['sentence_id', 'token_id', 'class', 'before',
                         'after_gold_clean', 'after_runorm', 'differs'])
        for row in reader:
            n += 1
            before = row[idx['before']]
            if not _HAS_LATIN.search(before):
                continue
            gold_clean = clean(row[idx['after']])
            try:
                runorm_out = norm.norm(before)
            except Exception as e:
                runorm_out = f'<<ERR:{type(e).__name__}>>'
            d = int(runorm_out != gold_clean)
            differs += d
            writer.writerow([
                row[header.index('sentence_id')] if has_ids else '',
                row[header.index('token_id')] if has_ids else '',
                row[cls_i] if cls_i is not None else '',
                before, gold_clean, runorm_out, d])
            done += 1
            if done % 50 == 0:
                print(f"  processed {done} foreign-word rows...", file=sys.stderr)
            if done >= limit:
                break

    print(f"scanned {n:,} rows, wrote {done} foreign-word rows to {out_path} "
          f"({differs} differ from the cleaned gold)")


if __name__ == '__main__':
    main()
