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

## Follow-up verification: 2026-09-28

The historical inventory above covers all 19 BibTeX records at that date. Four
additional cited records were checked against their primary publication pages
for this revision (23 records total). Historical verification is unchanged.

| Key | Status | Primary metadata source and relevance |
|---|---|---|
| `nederhof2003intersection` | Cited | https://aclanthology.org/W03-3016/ — Nederhof/Satta, 2003, IWPT, 137–148; weighted parsing as intersection. |
| `hanneforth2011intersection` | Cited | https://aclanthology.org/W11-4408/ — Thomas Hanneforth, 2011, FSMNLP, 57–64; practical weighted intersection. |
| `pasti2023intersection` | Cited | https://aclanthology.org/2023.eacl-main.52/ — Pasti, Opedal, Pimentel, Vieira, Eisner, Cotterell, 2023, EACL, 737–749; epsilon arcs and structural correspondence. |
| `qi2026clad` | Cited | https://arxiv.org/abs/2605.29607 — Heqiang Qi, Wei Huang, Mingyuan Bai, Xiangming Meng, 2026; preprint, attention-cluster matching conflicts, not CFG feasibility. |

No general weighted-intersection or exact-parallel-selection novelty is claimed.

## M21 repair references: 2026-09-28

Two further records (25 total), checked against primary sources. Scored parsing
and language edit distance are prior work, not claimed inventions. The cited
2024 arXiv revision corrects the earlier conference upper bound; no such running
bound is used in the repair implementation.

| Key | Status | Primary metadata source and relevance |
|---|---|---|
| `kociumaka2024edit` | Cited | https://arxiv.org/abs/1411.7315v4 — Tomasz Kociumaka and Barna Saha, revised 24 October 2024; scored parsing and edit distance background. |
| `baccianella2025jsonrepair` | Cited | https://github.com/mangiucugna/json_repair — Stefano Baccianella, software citation year 2025; measured version 0.63.5, including schema standard/salvage. |

## M25 primary-source extension, 2026-09-29

The original verification date and earlier inventories above are historical.
The manuscript now has 27 bibliography records, including two additional primary
sources for the public external data and the read-only application. Their URLs
were opened on 2026-09-29; they support the exact dataset revision and API
interface, rather than a claim of research novelty.

| Key | Current use | Verification |
|---|---|---|
| `bfcldataset` | Cited | Pinned Gorilla data directory at commit `6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`; original README declares Apache-2.0. Individual source hashes and eligible IDs are in `docs/evidence/m25-grounding-coverage.json`. |
| `openmeteogeocoding` | Cited | Official `https://open-meteo.com/en/docs/geocoding-api`, GET `/v1/search` with `name`, `count`, `language` and JSON output; GeoNames attribution. No model performance claim is attributed to this API. |

## Closest-method extension, 2026-09-30

The complete inventory now contains 32 records. These five primary sources
clarify that the present contribution is an integration/evaluation and not
invention of weighted CFG optimization, confidence decoding or commitment gating.

| Key | Current use | Verification |
|---|---|---|
| `katsirelos2008weighted` | Cited | Author-hosted PDF, CPAIOR 2008, LNCS 5015, 323–327; UNSW publication record verifies DOI `10.1007/978-3-540-68155-7_31`. Browser fetch failed but direct download and text extraction succeeded; weighted grammar optimization and soft Hamming/edit constraints are explicit antecedents. |
| `weiss2010cascades` | Cited | Official PMLR 9:916–923 (2010), David Weiss and Benjamin Taskar; max-marginal filtering explicitly stated in the abstract. |
| `wang2026tacg` | Cited | arXiv `2607.03236v1`, 3 July 2026; authors and identity/timing distinction checked in primary HTML. No TACG baseline or sampling theorem is claimed as implemented here. |
| `cai2026confidence` | Cited | arXiv `2603.22248v1`, 23 March 2026; Changxiao Cai and Gen Li. Its entropy-sum sampling result is distinct from this project's fixed probability threshold. |
| `su2026factor` | Cited | Primary arXiv HTML `2609.32900v1`, 26 September 2026, Jianchang Su and Wei Zhang; direct download succeeded after a browser-tool fetch error. FactorDLM uses finite-domain factor graphs, exact variable elimination and mean-field logits; it is not an implemented baseline here. No general exact-dLLM-inference novelty is claimed. |

## M26 mathematical extension, 2026-09-30

The inventory now has 34 records; the preceding 32-record audit remains
historical. Primary publication metadata was opened and checked, including
all authors, version/year, title, volume/pages and stable identifiers.

| Key | Current use | Verification |
|---|---|---|
| `demirovic2024certifying` | Cited | Official Dagstuhl page/BibTeX, DOI `10.4230/LIPIcs.CP.2024.9`, CP 2024, LIPIcs 307, 9:1–9:21; Emir Demirović, Ciaran McCreesh, Matthew J. McIlree, Jakob Nordström, Andy Oertel, Konstantin Sidorov. Certifying DP/proof logging is prior art, not claimed invention. |
| `ayoub2026axon` | Cited | Primary arXiv `2606.04236v1`, submitted 2 June 2026, Supportive Token Revealing for Fast Diffusion Language Model Decoding; Giries Abu Ayoub, Mario Barbara, Lluís Pastor-Pérez, Tanja Bien, Aneesh Barthakur, Alaa Maalouf, Loay Mualem. Supportive reveal selection is an antecedent; AXON is not a reproduced baseline here. |

M26 additionally rechecked EPIC `2606.00722v1`, FactorDLM `2609.32900v1`,
Goodman J99-4004 and the weighted-GRAMMAR journal DOI
`10.1007/s10479-010-0697-y`. No first-ever parsing, exact dLLM inference,
resource DP or certifying-algorithm novelty is claimed. The mathematical
contribution is incremental and its validity does not establish global priority.

## M27 additions, 1 October 2026

The current inventory contains 37 records. Three new primary sources acknowledge
established quality bounds, prefix sharing and the actual proof toolchain.

| Key | Status | Primary source | Verification |
| --- | --- | --- | --- |
| `likhachev2003ara` | Cited | [NeurIPS 2003 official record](https://papers.nips.cc/paper_files/paper/2003/hash/ee8fe9093fbbb687bef15a38facc44d2-Abstract.html) | Title, Likhachev/Gordon/Thrun and volume 16 verified. ARA* improves bounds with time; M27 only implements an incumbent certifier, not that search. |
| `xu2026trie` | Cited | [arXiv 2608.12574v1](https://arxiv.org/abs/2608.12574v1) | Xu/Bouyarmane, title and 12 August 2026 submission verified. Shared prefixes are prior art; no speedup from that paper is attributed to this project. |
| `lean2026reference` | Cited | [Official versioned reference](https://lean-lang.org/doc/reference/4.34.0/) | The manual explicitly covers Lean 4.34.0 and kernel checking. No claim that Lean automatically verifies foreign Python/Rust programs. |

## M29/M30 additions, 5 October 2026

The inventory now contains 43 records. Prior invention/priority claims remain
excluded. The new universal guarantees specialize established exact solving,
WMC, conditioning and token-support principles, rather than being firsts for
those principles.

| Key | Current use | Primary verification |
| --- | --- | --- |
| `davies2011maxhs` | Cited | Fahiem Bacchus/MaxHS primary paper, CP 2011, Davies and Bacchus; implicit hitting-set separation is explicitly attributed. DOI `10.1007/978-3-642-23786-7_19`. |
| `saikko2016lmhs` | Cited | Primary LMHS paper, Saikko, Berg and Järvisalo, SAT 2016; DOI `10.1007/978-3-319-40970-2_45`. The project does not invent hitting-set reuse. |
| `dubray2024anytime` | Cited | Official Dagstuhl metadata/full paper: Dubray, Schaus, Nijssen; CP 2024, LIPIcs 307, 10:1–10:16; DOI `10.4230/LIPIcs.CP.2024.10`. Deterministic anytime lower/upper WMC guarantees are established. |
| `renkens2014wmc` | Cited | Official AAAI record: Renkens, Kimmig, Van den Broeck, De Raedt; 2014, volume 28(1); DOI `10.1609/aaai.v28i1.9067`. Explanation-based bounded approximate counting is an antecedent. |
| `park2024gad` | Cited | Primary arXiv `2405.21047`, accepted NeurIPS 2024; Park, Wang, Berg-Kirkpatrick, Polikarpova, D'Antoni. ASAp's grammar-aligned AR sampling is not a new project discovery or reproduced baseline. |
| `parys2025cars` | Cited | Primary arXiv `2510.01902v2`, original 2 October 2025/revised 2 June 2026; Parys, Vaidya, Berg-Kirkpatrick, D'Antoni. Exact constrained AR sampling is acknowledged; project mean-field bounds do not claim its full-joint guarantee. |
