"""Build a 'mathematical center vector' from a canonical mathematical work.

The center vector represents the stylistic/semantic signature of mathematical
language for one era. It is built by:

  1. Reading a single canonical work (e.g. Euclid's *Elements*, Newton's
     *Principia*) as plain text.
  2. Splitting it into paragraphs (blank-line-separated, with over-long
     paragraphs re-split at sentence boundaries — same rule as
     ``extract_gutenberg.py``).
  3. Encoding every paragraph with BGE-M3, yielding L2-normalized vectors.
  4. Averaging those vectors and re-normalizing, producing a single unit
     vector — the "center."

Downstream, ``scan_slice.py`` measures any other text's mathematical-language
density as cosine similarity against this center.

使用方法 / Usage:
    python build_center.py --input D:/corpus/euclid_elements.txt \\
                           --out   centers/center_euclid.npy
"""

import argparse
import re
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
    # Strip Gutenberg front/back matter if present.
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


def main():
    ap = argparse.ArgumentParser(description='Build a mathematical center vector with BGE-M3.')
    ap.add_argument('--input', required=True, help='Path to a canonical text (.txt).')
    ap.add_argument('--out', required=True, help='Output .npy path for the center vector.')
    ap.add_argument('--model', default='BAAI/bge-m3', help='sentence-transformers model (default: BAAI/bge-m3).')
    ap.add_argument('--batch-size', type=int, default=8)
    args = ap.parse_args()

    from sentence_transformers import SentenceTransformer

    text = Path(args.input).read_text(encoding='utf-8', errors='replace')
    paras = split_text(text)
    if len(paras) < 5:
        raise SystemExit(f'Too few paragraphs ({len(paras)}) — need at least 5.')
    print(f'Loaded {len(paras)} paragraphs from {args.input}')

    print(f'Loading model {args.model} ...')
    model = SentenceTransformer(args.model)

    vecs = []
    for b in range(0, len(paras), 500):
        batch = paras[b:b + 500]
        v = model.encode(
            batch,
            batch_size=args.batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        vecs.append(v)
    vecs = np.vstack(vecs)

    center = vecs.mean(axis=0)
    center = center / np.linalg.norm(center)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.save(out, center.astype(np.float32))
    print(f'Saved center ({center.shape[0]}-dim) to {out}')


if __name__ == '__main__':
    main()
