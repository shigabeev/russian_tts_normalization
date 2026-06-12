"""Assessment: per-class accuracy + top miss patterns + latency on the Kaggle gold."""
import csv, sys, time, random
from collections import Counter, defaultdict
from russian import normalize_russian

PATH = sys.argv[1] if len(sys.argv) > 1 else 'text-normalization-challenge-russian-language/ru_train.csv'
SAMPLE_EVERY = int(sys.argv[2]) if len(sys.argv) > 2 else 10  # 1/10 of 10.5M tokens

def yo(s):
    return s.replace('ё', 'е').replace('Ё', 'Е')

cache = {}
total = defaultdict(int)
hit = defaultdict(int)
misses = defaultdict(Counter)

t0 = time.time()
n = 0
with open(PATH, encoding='utf-8') as f:
    for i, row in enumerate(csv.DictReader(f)):
        if i % SAMPLE_EVERY:
            continue
        before, after, cls = row['before'], row['after'], row['class']
        got = cache.get(before)
        if got is None:
            got = cache[before] = normalize_russian(before)
        total[cls] += 1
        n += 1
        # YO rows test ё restoration itself, so they compare ё-sensitively.
        if (got == after) if cls == 'YO' else (yo(got) == yo(after)):
            hit[cls] += 1
        else:
            misses[cls][(before, got, after)] += 1
print(f"scored {n} tokens in {time.time()-t0:.1f}s (sample 1/{SAMPLE_EVERY})\n")

print(f"{'class':<12}{'tokens':>9}{'acc':>8}")
grand = grandhit = 0
for cls in sorted(total, key=total.get, reverse=True):
    grand += total[cls]; grandhit += hit[cls]
    print(f"{cls:<12}{total[cls]:>9}{hit[cls]/total[cls]:>8.1%}")
print(f"{'OVERALL':<12}{grand:>9}{grandhit/grand:>8.1%}\n")

for cls in sorted(total, key=lambda c: total[c]-hit[c], reverse=True):
    wrong = total[cls] - hit[cls]
    if not wrong:
        continue
    print(f"== {cls}: {wrong} misses ==")
    for (b, g, a), c in misses[cls].most_common(12):
        print(f"  x{c:<5} {b!r} -> got {g!r} | gold {a!r}")
    print()

# Latency: whole-sentence normalization on reconstructed sentences.
random.seed(0)
sents = defaultdict(list)
with open(PATH, encoding='utf-8') as f:
    for row in csv.DictReader(f):
        sid = int(row['sentence_id'])
        if sid > 5000:
            break
        sents[sid].append(row['before'])
texts = [' '.join(v) for v in sents.values()]
if not texts:
    sys.exit(0)
chars = sum(map(len, texts))
for _ in range(2):  # warm + measured
    t0 = time.time()
    for t in texts:
        normalize_russian(t)
    dt = time.time() - t0
print(f"LATENCY: {len(texts)} sentences, {chars} chars: {dt:.2f}s "
      f"=> {dt/len(texts)*1000:.2f} ms/sentence, {chars/dt/1000:.0f}k chars/s")
