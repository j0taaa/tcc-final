# Submission bibliography verification

- Verification date: 2026-09-01
- Bibliography: `paper/referencias.bib`
- Manuscript: `paper/main.tex`
- Scope: all 19 BibTeX records, including the 17 cited records emitted by
  BibTeX and the two currently uncited records.

## Method

Each record was compared with a primary or official publication record. The
audit checked author order, title, publication type, venue or institution,
year, volume/issue, pages, and DOI or stable URL when available. For every
cited record, the surrounding sentence in `paper/main.tex` was also checked
against the source's stated contribution. A successful LaTeX build alone was
not treated as bibliographic verification.

Official proceedings and publisher records take precedence over arXiv records
when the same work has been formally published. Stable citation keys were kept
even when their embedded year predates the final venue year.

## Per-record audit

| BibTeX key | Citation status | Verification source | Result |
| --- | --- | --- | --- |
| `austin2021d3pm` | Cited | [NeurIPS 2021 proceedings](https://proceedings.neurips.cc/paper/2021/hash/958c530554f78bcd8e97125b70e6973d-Abstract.html) | Verified; normalized from `article` to `inproceedings` and recorded the official URL. |
| `sahoo2024mdlm` | Cited | [NeurIPS 2024 proceedings](https://proceedings.neurips.cc/paper_files/paper/2024/hash/eb0b13cc515724ab8015bc978fdde0ad-Abstract-Conference.html) | Verified; added volume 37, pages 130136--130184, DOI, and official URL. |
| `nie2025llada` | Cited | [NeurIPS 2025 proceedings](https://proceedings.neurips.cc/paper_files/paper/2025/hash/48b383b24230e0e6e649d9c98dae4d8c-Abstract-Conference.html) | Corrected stale preprint metadata to the final NeurIPS 2025 record: volume 38, pages 50608--50646, and DOI 10.52202/085713-1689. |
| `suresh2025dingo` | Cited | [NeurIPS 2025 proceedings](https://proceedings.neurips.cc/paper_files/paper/2025/hash/eb17a2030d1bd4a1bd29531bcd626705-Abstract-Conference.html) | Verified; added pages 160518--160551 and the official URL. |
| `mundler2025cfg` | Cited | [ETH SRI publication record](https://www.sri.inf.ethz.ch/publications/muendler2025constraineddiffusion) and [OpenReview](https://openreview.net/forum?id=7Sph4KyeYO) | Verified as ICLR 2026. The stable citation key is intentionally unchanged. |
| `jin2026epic` | Cited | [arXiv:2606.00722](https://arxiv.org/abs/2606.00722) | Verified as a 2026 arXiv preprint; added its arXiv-issued DOI and stable URL. |
| `dang2026automata` | Cited | [arXiv:2607.07026](https://arxiv.org/abs/2607.07026) | Verified as a 2026 arXiv preprint; added its arXiv-issued DOI and stable URL. |
| `amarilli2026probabilistic` | Cited | [DROPS STACS 2026 record](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.STACS.2026.5) | Verified; normalized the official LIPIcs series name and added the stable URL. |
| `goodman1999semiring` | Cited | [ACL Anthology J99-4004](https://aclanthology.org/J99-4004/) | Verified; added the stable Anthology URL. |
| `earley1970` | Cited | [ACM DOI 10.1145/362007.362035](https://doi.org/10.1145/362007.362035) | Verified; added the DOI resolver URL. |
| `stolcke1995` | Uncited | [ACL Anthology J95-2002](https://aclanthology.org/J95-2002/) | Verified; added the stable Anthology URL. It remains a valid internal bibliography record but is not emitted in the current paper. |
| `barhillel1961` | Cited | [publisher DOI record](https://doi.org/10.1524/stuf.1961.14.14.143) and [Hebrew University record](https://cris.huji.ac.il/en/publications/on-formal-properties-of-simple-phrase-structure-grammars/) | Verified; added the DOI resolver URL. |
| `mohri2002` | Cited | [Google Research publication record](https://research.google/pubs/semiring-frameworks-and-algorithms-for-shortest-distance-problems/) and [journal DOI](https://doi.org/10.25596/JALC-2002-321) | Verified; added DOI 10.25596/JALC-2002-321 and the author-hosted publication URL. |
| `hopcroft2006` | Cited | [Pearson third-edition record](https://www.pearson.com/en-us/subject-catalog/p/introduction-to-automata-theory-languages-and-computation/P200000003517/9780321455369) | Verified; added ISBN 978-0-321-45536-9 and the publisher URL. |
| `aho2006` | Cited | [Pearson second-edition record](https://www.pearson.com/en-us/subject-catalog/p/compilers-principles-techniques-and-tools/P200000003472/9780321486813) | Verified; added ISBN 978-0-321-48681-3 and the publisher URL. |
| `sennrich2016bpe` | Cited | [ACL Anthology P16-1162](https://aclanthology.org/P16-1162/) | Verified; retained the concise proceedings title and added the stable Anthology URL. |
| `kudo2018sentencepiece` | Cited | [ACL Anthology D18-2012](https://aclanthology.org/D18-2012/) | Verified; added the stable Anthology URL. |
| `kasami1965` | Cited | [University of Illinois repository handle](https://hdl.handle.net/2142/74304) | Verified as report AFCRL-65-758; added Bedford, MA, and the repository URL. |
| `younger1967` | Uncited | [Elsevier article record](https://doi.org/10.1016/S0019-9958(67)80007-X) | Verified; added DOI 10.1016/S0019-9958(67)80007-X and its resolver URL. It is not emitted in the current paper. |

## Claim-to-source audit

The 17 cited records support the claims attached to them in the manuscript:

- Austin, Sahoo, and Nie support the progression from discrete diffusion to
  masked diffusion language models and LLaDA-scale models.
- Suresh, Mündler, Jin, and Dang--Ermon support the distinctions among regular
  constrained inference, CFG completion feasibility, EPIC's verified heuristic
  parallel selection, and exact finite-automaton inference.
- Goodman and Mohri support semiring parsing and weighted shortest-distance
  principles; Amarilli et al. support the contrasting sum-product complexity
  statement.
- Kasami, Earley, Bar-Hillel et al., and Hopcroft et al. support the parsing and
  formal-language closure statements.
- Sennrich et al., Kudo--Richardson, and Aho et al. support the tokenization and
  lexical-analysis background.

No citation was used as evidence for this repository's implementation,
experimental measurements, or a broader exactness guarantee. Those claims
remain tied to versioned code and artifacts, and the algorithm remains only
per-step `exact_on_support` for the represented finite support.

## Corrections and non-corrections

The material correction is the LLaDA venue update from an arXiv-only record to
NeurIPS 2025. The remaining edits improve completeness or normalize publication
types and official identifiers without changing the manuscript's scientific
positioning. The two unused entries were retained because their metadata is
valid; their unused status is explicit and tested rather than silently confused
with the 17 references printed in the paper. Publisher and location fields that
would only expand the SBC bibliography were omitted where the DOI or official
URL already identifies the exact proceedings record; this keeps the verified
bibliography within the institutional 16-page limit without dropping sources.

## Verification commands

After the metadata changes, completion requires:

```bash
source .venv/bin/activate
python -m pytest -q tests/exact_commit/test_submission_bibliography_verification.py
make check
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q
make paper
pdfinfo paper/main.pdf
```

The final build log must contain no missing BibTeX entry, undefined citation,
unresolved reference, overfull box, or fatal LaTeX error. All rendered pages
must be inspected after the final build.

## Results

- Focused bibliography regression: 4 passed.
- `make check`: upstream provenance, Ruff, and strict MyPy passed; 11 unit and
  676 exact-commit tests passed.
- Full `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q`: 697 passed.
- `make paper`: passed; `pdfinfo` reported 16 A4 pages and 357,549 bytes.
- The final LaTeX/BibTeX logs contained no missing entry, undefined citation,
  unresolved reference, overfull box, fatal error, or emergency stop.
- Poppler renders of all 16 pages were inspected, with pages 13--16 checked at
  original detail. No clipping, overlap, broken glyph, unreadable reference, or
  page-boundary defect was found.
