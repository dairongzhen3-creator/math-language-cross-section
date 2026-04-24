"""Extract paragraphs from Perseus TEI XML files.

Perseus Digital Library distributes Greek and Latin texts as TEI-encoded XML.
English translations are in files matching ``*perseus-eng*.xml``. This script
walks a directory, reads each English-translation XML, extracts paragraphs,
and writes one plain-text file per XML.

Extraction uses three-level fallback:

1. ``<p>``  — prose (history, philosophy, oratory).
2. ``<sp>`` — drama speaker turns (tragedy, comedy).
3. ``<l>``  — verse lines, grouped into ``--lines-per-para`` lines per chunk.

HTML entities are decoded and Perseus metadata fragments (editor notes,
pointer patterns) are filtered by substring match + length cutoff. Paragraphs
shorter than ``--min-len`` characters are dropped.

使用方法 / Usage:
    python extract_tei.py --root D:/corpus/Perseus_Greek/data \\
                          --out  D:/out/greek_txt
"""

import argparse
import re
from pathlib import Path

# Perseus-specific metadata/editor junk. Short fragments that contain any of
# these substrings are discarded. Extend this list as new junk patterns appear.
JUNK_PATTERNS = [
    'pointer pattern',
    'This pointer',
    'This document',
    'perseus-eng',
    'perseus-grc',
    'Heath, Sir',
    'Dindorf',
]

ENTITY_MAP = [
    ('&mdash;', '—'), ('&ndash;', '–'), ('&nbsp;', ' '), ('&hellip;', '...'),
    ('&aelig;', 'ae'), ('&eacute;', 'é'), ('&oelig;', 'oe'),
    ('&amp;', '&'), ('&lt;', '<'), ('&gt;', '>'), ('&quot;', '"'),
]


def clean_entities(text: str) -> str:
    for ent, rep in ENTITY_MAP:
        text = text.replace(ent, rep)
    return text


def is_junk(text: str, junk_len_cutoff: int = 150) -> bool:
    low = text.lower()
    return any(p.lower() in low for p in JUNK_PATTERNS) and len(text) < junk_len_cutoff


def strip_tags(chunk: str) -> str:
    clean = re.sub(r'<[^>]+>', ' ', chunk)
    return re.sub(r'\s+', ' ', clean).strip()


def extract_from_xml(xml_path: Path, min_len: int, lines_per_para: int) -> list:
    """Return list of paragraphs from a single TEI XML file."""
    text = clean_entities(xml_path.read_text(encoding='utf-8', errors='replace'))

    # Level 1: <p> — prose
    p_chunks = re.findall(r'<p(?:\s[^>]*)?>(.*?)</p>', text, re.DOTALL)
    paras = []
    for raw in p_chunks:
        clean = strip_tags(raw)
        if clean and len(clean) >= min_len and not is_junk(clean):
            paras.append(clean)
    if paras:
        return paras

    # Level 2: <sp> — drama speaker turns
    sp_chunks = re.findall(r'<sp\b[^>]*>(.*?)</sp>', text, re.DOTALL)
    for raw in sp_chunks:
        clean = strip_tags(raw)
        if clean and len(clean) >= min_len:
            paras.append(clean)
    if paras:
        return paras

    # Level 3: <l> — verse lines, grouped
    l_chunks = re.findall(r'<l\b[^>]*>(.*?)</l>', text, re.DOTALL)
    lines = [strip_tags(raw) for raw in l_chunks]
    lines = [ln for ln in lines if ln]
    for i in range(0, len(lines), lines_per_para):
        chunk = ' '.join(lines[i:i + lines_per_para])
        if len(chunk) >= min_len:
            paras.append(chunk)
    return paras


def main():
    ap = argparse.ArgumentParser(description='Extract paragraphs from Perseus TEI XML.')
    ap.add_argument('--root', required=True, help='Perseus data root (contains tlg*/phi* dirs).')
    ap.add_argument('--out', required=True, help='Output directory for per-file .txt paragraphs.')
    ap.add_argument('--pattern', default='*perseus-eng*.xml',
                    help='Filename glob for English translations (default: *perseus-eng*.xml).')
    ap.add_argument('--min-len', type=int, default=30, help='Drop paragraphs shorter than N chars.')
    ap.add_argument('--lines-per-para', type=int, default=20,
                    help='For verse, group this many <l> lines per paragraph.')
    args = ap.parse_args()

    root = Path(args.root)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    xmls = sorted(root.rglob(args.pattern))
    print(f'Found {len(xmls)} XML files under {root}')

    total_paras = 0
    for i, xml in enumerate(xmls, 1):
        paras = extract_from_xml(xml, args.min_len, args.lines_per_para)
        if not paras:
            continue
        rel = xml.relative_to(root)
        flat_name = '_'.join(rel.parts).replace('.xml', '.txt')
        (out / flat_name).write_text('\n\n'.join(paras), encoding='utf-8')
        total_paras += len(paras)
        if i % 50 == 0 or i == len(xmls):
            print(f'[{i}/{len(xmls)}] {flat_name[:60]}  {len(paras)} paras')

    print(f'Done. Wrote {total_paras} paragraphs across {len(xmls)} files into {out}.')


if __name__ == '__main__':
    main()
