# Mathematical Language Cross-Section

**A Quantitative Scan of Mathematical Language Density Across Western Civilizational Slices Using Text Embeddings**

*数学语言的向量剖面：从欧几里得到欧拉的跨文明定量扫描*

Author: **Dai Rongzhen** (戴荣臻) · ORCID: [0009-0005-7165-0080](https://orcid.org/0009-0005-7165-0080)

[Paper — English (PDF)](paper/paper_en_v1.pdf) · [Paper — Chinese (PDF)](paper/数学语言的向量剖面_v1.pdf) · DOI: *pending Zenodo assignment*

---

![Evolution curves across five civilizational slices](paper/fig1_dual_curves.png)

## What This Is

This study uses **BGE-M3** multilingual text embeddings to scan all available English translations of texts from five Western civilizational slices (Greek Classical/Hellenistic, Roman Empire, Renaissance 1400–1600, Leibniz era 1684–1734, Euler era 1740–1770), totaling **3,977 works and 3.38 million paragraphs**.

For each slice, a "mathematical center vector" is built from a canonical mathematical work of that era (Euclid, Cardano, Newton's *Principia*, Newton's *Opticks*). Each paragraph of every other text is scored by its cosine similarity to this center. The **ratio of paragraphs with similarity ≥ 0.6** measures each book's "mathematical language density."

## Key Findings

- **Vertical elite curve (Top-5 mean)**: 61% (Greek) → 47% (Roman) → 42% (Renaissance) → **90% (Leibniz)** → **91% (Euler)**. The U-shaped bottom is in the Renaissance, not in Rome.
- **Horizontal popularization curve (median)**: 0% in the first three slices — a typical book contains no mathematical language at all. **Jumps to 6.84% in the Leibniz era** (first time the median exceeds zero) — mathematical language has entered common text. Falls back to 3.12% in the Euler era.
- **Three phases**: *Isolated Peaks* (antiquity through Renaissance) → *Stratified Layer* (Leibniz era, Scientific Revolution) → *Diluted Stratum* (Euler era, mass-print publication explosion).
- The **median jumping from 0 to positive** is a novel quantitative signature of the Scientific Revolution, complementary to traditional "heroic" narratives centered on Newton, Galileo, and Descartes.

![Stratified bars by slice](paper/fig2_stratified_bars.png)

## Repository Structure

```
paper/      Paper (Chinese + English, PDF/DOCX/MD) and figures
results/    Scan results for all 5 slices (JSON)
centers/    4 mathematical center vectors (.npy, BGE-M3, 1024-dim)
maps/       Author-work lookup tables (Perseus Greek & Latin)
code/       Reproducible scanning pipeline (Python + sentence-transformers)
```

### `results/`
| File | Slice | N works |
|---|---|---|
| `greek_v3.json` | Greek Classical / Hellenistic | 339 |
| `roman_v3.json` | Roman Empire | 659 |
| `renaissance_v4.json` | Renaissance 1400–1600 | 365 |
| `leibniz_v4.json` | Leibniz era 1684–1734 | 983 |
| `euler_v4.json` | Euler era 1740–1770 | 1631 |

Each record: `{slice, author, title, total_paras, max, p95, p50, ratio_above_06, ratio_above_05, ...}`

### `centers/`
| File | Built from | Used for |
|---|---|---|
| `center_euclid.npy` | Euclid, *Elements* (Heath tr.) | Greek + Roman slices |
| `center_cardano.npy` | Cardano, *Ars Magna* (Witmer tr.) | Renaissance slice |
| `center_newton.npy` | Newton, *Principia* | Leibniz era slice |
| `center_opticks.npy` | Newton, *Opticks* | Euler era slice |

## How to Reproduce

```bash
pip install -r code/requirements.txt

# 1. Extract paragraphs from source corpora
python code/extract_tei.py --root /path/to/Perseus_Greek/data --out /tmp/greek_txt
python code/extract_gutenberg.py --in /path/to/Gutenberg_books --out /tmp/leibniz_txt

# 2. Build a center vector from one canonical work
python code/build_center.py --input /path/to/euclid_elements.txt \
                            --out   centers/center_euclid.npy

# 3. Scan a corpus against that center
python code/scan_slice.py --center centers/center_newton.npy \
                          --texts  /tmp/leibniz_txt \
                          --output results/leibniz_v4.json \
                          --slice  "Leibniz Era"
```

The BGE-M3 model (~2 GB) is auto-downloaded from HuggingFace on first run. A consumer GPU (NVIDIA RTX 3060 / 12 GB) is sufficient; CPU works but is slow.

Source texts are **not** bundled. Download them from:
- **Perseus Digital Library** (Greek + Latin, CC BY-SA): <https://github.com/PerseusDL/canonical-greekLit> and `canonical-latinLit`
- **Project Gutenberg** (public domain): <https://www.gutenberg.org/>

## Human-AI Collaboration

This research was conducted by **Dai Rongzhen in collaboration with Anthropic Claude**. The scale of the work — scanning ~4,000 books across 3.38M paragraphs, iterating methodology across multiple revisions — would have been infeasible for a single independent researcher without AI assistance. Dai formulated the research questions, designed the civilizational slices, selected the mathematical centers, and adjudicated methodological decisions. Claude wrote scanning scripts, ran experiments, organized results, and drafted text.

## Limitations

1. **All texts are English translations**; translator style affects absolute values.
2. **Samples are from Perseus and Gutenberg digital libraries**, not the real historical reading ecosystem.
3. **The method identifies textual style, not mathematical substance** — e.g., Spinoza's *Ethics* scores 89% because it mimics Euclid's "definition-axiom-proposition-proof" form, despite its content being metaphysics rather than mathematics.

Conclusions should be read in **relative** terms (differences between slices, between elite and median) rather than as absolute truths.

## Citation

```
Dai Rongzhen (2026). Mathematical Language Cross-Section: A Cross-Civilizational
Quantitative Scan from Euclid to Euler. Zenodo. https://doi.org/[pending]
```

## License

MIT License. Data and code are free for any use; proper attribution appreciated.

## Contact

GitHub: [@dairongzhen3-creator](https://github.com/dairongzhen3-creator) · ORCID: [0009-0005-7165-0080](https://orcid.org/0009-0005-7165-0080)

Feedback, collaborations, and extensions to new civilizational slices (Chinese mathematical corpus, Islamic Golden Age, 19th–20th-century industrial-scientific era) are welcome.
