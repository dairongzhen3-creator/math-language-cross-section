"""Extract paragraphs from Project Gutenberg plain-text books.

Gutenberg texts wrap the actual book body between ``*** START OF ...`` and
``*** END OF ...`` markers, which this script strips. Paragraphs are split on
blank lines. Any paragraph longer than ``--max-len`` characters is
re-segmented at sentence boundaries — this prevents single mega-paragraphs
(common in older typography) from dominating the embedding average or
exceeding the model's context window.

使用方法 / Usage:
    python extract_gutenberg.py --in  D:/corpus/Gutenberg/txt \\
                                --out D:/out/gutenberg_paragraphs
"""

import argparse
import re
from pathlib import Path


def split_long(para: str, min_len: int, max_len: int) -> list:
    """Break a too-long paragraph into <= max_len chunks at sentence boundaries."""
    if len(para) <= max_len:
        return [para]
    sentences = re.split(r'(?<=[.!?])\s+', para)
    out, cur = [], ''
    for s in sentences:
        if len(cur) + len(s) + 1 <= max_len:
            cur = (cur + ' ' + s).strip() if cur else s
        else:
            if cur:
                out.append(cur)
            cur = s
    if cur:
        out.append(cur)
    return [p for p in out if len(p) >= min_len]


def strip_gutenberg_boundaries(text: str) -> str:
    """Remove Project Gutenberg front-matter and back-matter."""
    start = text.find('*** START')
    end = text.find('*** END')
    if start > 0:
        body_start = text.find('\n', start) + 1
        text = text[body_start:end] if end > 0 else text[body_start:]
    return text


def extract_paragraphs(text: str, min_len: int, max_len: int) -> list:
    text = strip_gutenberg_boundaries(text)
    raw_paras = re.split(r'\n\s*\n', text)
    out = []
    for p in raw_paras:
        p = p.strip()
        if not p or len(p) < min_len:
            continue
        out.extend(split_long(p, min_len, max_len))
    return out


def main():
    ap = argparse.ArgumentParser(description='Extract paragraphs from Gutenberg .txt files.')
    ap.add_argument('--in', dest='in_dir', required=True, help='Input dir of .txt books.')
    ap.add_argument('--out', required=True, help='Output dir for per-book paragraph files.')
    ap.add_argument('--min-len', type=int, default=30, help='Drop paragraphs shorter than N chars.')
    ap.add_argument('--max-len', type=int, default=1000,
                    help='Re-split paragraphs longer than N chars at sentence boundaries.')
    args = ap.parse_args()

    in_dir = Path(args.in_dir)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    txts = sorted(in_dir.glob('*.txt'))
    print(f'Found {len(txts)} txt files under {in_dir}')

    for i, txt in enumerate(txts, 1):
        text = txt.read_text(encoding='utf-8', errors='replace')
        paras = extract_paragraphs(text, args.min_len, args.max_len)
        if not paras:
            continue
        (out / txt.name).write_text('\n\n'.join(paras), encoding='utf-8')
        if i % 50 == 0 or i == len(txts):
            print(f'[{i}/{len(txts)}] {txt.name[:60]}  {len(paras)} paras')

    print(f'Done. Output in {out}.')


if __name__ == '__main__':
    main()
