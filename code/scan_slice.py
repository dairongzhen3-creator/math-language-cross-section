"""Scan a corpus against a mathematical center vector.

For every ``.txt`` file in ``--texts``:

  1. Split into paragraphs (blank-line split + long-paragraph re-split at
     sentence boundaries, matching ``build_center.py``).
  2. Encode each paragraph with BGE-M3, L2-normalized.
  3. Compute cosine similarity vs. the center vector (dot product, since both
     sides are unit vectors).
  4. Record per-book statistics: total paragraph count, max / p95 / p50
     similarity, and the *ratio* of paragraphs with similarity >= 0.6 (and
     >= 0.5).

The ``ratio_above_06`` is the primary signal used in the paper — it measures
what fraction of a book reads as "mathematical language," rather than just
whether any mathematical passage exists.

Results are checkpointed after every book, so the scan resumes cleanly if
interrupted.

使用方法 / Usage:
    python scan_slice.py --center centers/center_newton.npy \\
                         --texts  D:/corpus/leibniz_era/txt \\
                         --output results/leibniz_v4.json \\
                         --slice  "Leibniz Era"
"""

import argparse
import json
import re
import time
from pathlib import Path

import numpy as np


MIN_LEN = 30
MAX_LEN = 1000


def split_long(para: str) -> list:
    if len(para) <= MAX_LEN:
        return [para]
    sentences = re.split(r'(?<=[.!?])\s+', para)
    out, cur = [], ''
    for s in sentences:
        if len(cur) + len(s) + 1 <= MAX_LEN:
            cur = (cur + ' ' + s).strip() if cur else s
        else:
            if cur:
                out.append(cur)
            cur = s
    if cur:
        out.append(cur)
    return [p for p in out if len(p) >= MIN_LEN]


def split_text(text: str) -> list:
    start = text.find('*** START')
    end = text.find('*** END')
    if start > 0:
        body_start = text.find('\n', start) + 1
        text = text[body_start:end] if end > 0 else text[body_start:]
    raw_paras = re.split(r'\n\s*\n', text)
    out = []
    for p in raw_paras:
        p = p.strip()
        if not p or len(p) < MIN_LEN:
            continue
        out.extend(split_long(p))
    return out


def scan_book(path: Path, center: np.ndarray, model, batch_size: int) -> tuple:
    paras = split_text(path.read_text(encoding='utf-8', errors='replace'))
    if len(paras) < 5:
        return None, 0

    sims = []
    for b in range(0, len(paras), 500):
        batch = paras[b:b + 500]
        vecs = model.encode(
            batch,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        sims.extend((vecs @ center).tolist())
    return np.array(sims), len(paras)


def main():
    ap = argparse.ArgumentParser(description='Scan a corpus against a math center vector.')
    ap.add_argument('--center', required=True, help='Path to center .npy (from build_center.py).')
    ap.add_argument('--texts', required=True, help='Directory of .txt files to scan.')
    ap.add_argument('--output', required=True, help='Output results .json path (resumable).')
    ap.add_argument('--slice', default='unnamed', help='Slice label stored in each record.')
    ap.add_argument('--model', default='BAAI/bge-m3')
    ap.add_argument('--batch-size', type=int, default=8)
    args = ap.parse_args()

    from sentence_transformers import SentenceTransformer

    center = np.load(args.center)
    print(f'Loaded center from {args.center}, dim={center.shape[0]}')

    print(f'Loading model {args.model} ...')
    t0 = time.time()
    model = SentenceTransformer(args.model)
    print(f'Model loaded in {time.time() - t0:.1f}s')

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    results = []
    done_names = set()
    if out_path.exists():
        results = json.loads(out_path.read_text(encoding='utf-8'))
        done_names = {r['name'] for r in results}
        print(f'Resuming: {len(results)} books already scanned.')

    files = sorted(Path(args.texts).glob('*.txt'))
    print(f'Found {len(files)} .txt files under {args.texts}')

    t_start = time.time()
    processed = 0
    for i, f in enumerate(files, 1):
        name = f.stem[:80]
        if name in done_names:
            continue
        try:
            sims, n_paras = scan_book(f, center, model, args.batch_size)
            if sims is None:
                continue
            stat = {
                'slice': args.slice,
                'name': name,
                'total_paras': n_paras,
                'max': float(sims.max()),
                'p95': float(np.percentile(sims, 95)),
                'p50': float(np.percentile(sims, 50)),
                'ratio_above_06': float((sims >= 0.6).mean()),
                'ratio_above_05': float((sims >= 0.5).mean()),
            }
            results.append(stat)
            processed += 1
            out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')

            if processed % 5 == 0 or i == len(files):
                elapsed = time.time() - t_start
                remaining = len(files) - len(results)
                eta = elapsed / processed * remaining if processed else 0
                print(f'[{i}/{len(files)}] {name[:50]:<52} '
                      f'{n_paras:>5} paras  >=0.6={stat["ratio_above_06"] * 100:>5.1f}%  '
                      f'(elapsed {elapsed:.0f}s, ETA {eta:.0f}s)')
        except Exception as e:
            print(f'  [fail] {f.name[:50]}: {str(e)[:80]}')
            continue

    print(f'\nDone. {len(results)} books in {(time.time() - t_start) / 60:.1f} min.')


if __name__ == '__main__':
    main()
