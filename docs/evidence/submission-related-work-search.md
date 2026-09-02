# Submission related-work search

- Search date: 2026-09-01
- Coverage cutoff: primary records discoverable through 2026-08-31
- Audited manuscript base: `aedbf900a1cb1ac64ea6c3736b70987ebaae3b02`
- Scope: constrained decoding for masked/discrete diffusion language models,
  parallel token commitment, CFG/automata inference, non-autoregressive
  constrained decoding, and tokenizer-aware structured generation.

This is a targeted update for the institutional submission, not a claim of a
systematic review or proof of novelty. The search was restricted to English
primary paper records in arXiv, OpenReview/ICLR, NeurIPS proceedings, the ACL
Anthology, PMLR, and MLSys proceedings. Secondary discovery pages were not used
as evidence for manuscript claims or bibliographic metadata.

## Search strings

The following query families were run with spelling and site variants:

1. `diffusion language model constrained decoding grammar CFG parallel inference`
2. `masked diffusion language model parallel decoding constraints structured output`
3. `parallel commitment diffusion language model`
4. `constrained diffusion language models decoding 2026`
5. `grammar masked diffusion decoding 2026`
6. `non-autoregressive DAG constrained decoding weighted finite state automata`
7. `context-free grammar constrained generation tokenizer XGrammar`
8. `arXiv 2608 diffusion language constrained decoding parallel decoding`

Backward/forward inspection of the direct DINGO, Mündler et al., EPIC, and
finite-automata papers was used to identify adjacent terminology. Searches
were stopped after the focused variants repeatedly returned the same direct
line and the same representative parallel-decoding families.

## Review and citation decisions

| Source | Citation decision | Boundary used in the review |
| --- | --- | --- |
| [Zhang et al., *Generation Order and Parallel Decoding in Masked Diffusion Models*](https://arxiv.org/abs/2602.00286) (arXiv:2602.00286) | Reviewed but not cited separately: it is adjacent theory rather than a formal-constraint method, and one added entry exceeded the 16-page limit. | It studies distributional error, not exact CFG-compatible proposal selection. |
| [Zoabi et al., *Mean-Field Parallel Decoding for Discrete Diffusion Language Models*](https://arxiv.org/abs/2606.15805) (arXiv:2606.15805) | Reviewed but not cited separately: representative model-proxy method already covered by the cited theory/method boundary. | It optimizes pairwise predictive interactions and empirical quality/latency, not a grammar certificate. |
| [Qi et al., *Cluster-Level Attention-Guided Parallel Decoding for Masked Diffusion Language Models*](https://arxiv.org/abs/2605.29607) (arXiv:2605.29607) | Reviewed but not cited separately under the 16-page limit. | Its attention-derived cluster conflicts are proxies rather than exact CFG completion constraints. |
| [Dong et al., *XGrammar*](https://proceedings.mlsys.org/paper_files/paper/2025/hash/5c20ca4b0b20b0bd2f1d839dc605e70f-Abstract-Conference.html) (MLSys 2025) | Reviewed but not cited separately under the 16-page limit. | It performs left-to-right next-token masking, not arbitrary-hole dLLM completion or MWPC. |
| [Chen et al., *Control-DAG*](https://aclanthology.org/2024.naacl-short.42/) (NAACL 2024) | Reviewed but not cited separately under the 16-page limit. | It uses weighted finite-state constraints for a particular NAR DAG model, not CFG feasibility over current dLLM proposals. |

The article already cited the direct formal-constraint line: DINGO for regular
constraints, Mündler et al. for arbitrary-hole CFG completion feasibility,
EPIC for verified heuristic parallel CFG commitment, and Dang--Ermon for exact
finite-automata inference. The search also established publication records for
DINGO (NeurIPS 2025) and Mündler et al. (ICLR 2026), replacing their older arXiv
metadata in the bibliography. Because no retrieved adjacent source changed that
positioning and even one additional reference pushed the paper to 17 pages, the
search record preserves the broader review without expanding the 16-page body.
The metadata updates use the official
[NeurIPS DINGO record](https://proceedings.neurips.cc/paper_files/paper/2025/hash/eb17a2030d1bd4a1bd29531bcd626705-Abstract-Conference.html)
and the authors' [ICLR publication record](https://www.sri.inf.ethz.ch/publications/muendler2025constraineddiffusion).

## Representative exclusions

| Retrieved family | Decision |
| --- | --- |
| LocalLeap, AXON, PVF, DAWN/DEMASK, DOS, and related fast samplers | Relevant to reveal scheduling or dependency proxies, but redundant after the recorded coordinated-commit review and not formal-language certificate methods. |
| Dynamic Infilling Anchors | Format/length anchoring rather than grammar-language constrained inference. |
| Diffinity/continuous-diffusion syntax guidance | Continuous latent guidance with empirical regular-expression satisfaction, outside the masked discrete exactness setting. |
| Geng et al., Grammar-Aligned Decoding, CFGzip, and XGrammar 2 | Useful autoregressive structured-generation context, but XGrammar suffices as the compact representative under the 16-page limit. |
| JSONSchemaBench and evaluations of constrained-output quality | Evaluation context rather than a competing algorithm for the MWPC objective. |

## Search conclusion

No retrieved primary source formulated and solved the same problem as this
work: selecting the maximum-weight subset of current dLLM proposals that is
jointly compatible with one finite-slot CFG-valid completion, with a
reconstructible witness and an independently recomputable objective. This is a
bounded result of the recorded search, not evidence that no such work exists.

The recorded review distinguishes:

- exact regular-language posterior inference from CFG completion;
- model-derived dependency proxies from grammar-certified compatibility;
- left-to-right grammar token masking from arbitrary-hole completion; and
- weighted finite-state decoding of one NAR DAG from finite-slot CFG MWPC.

No implementation claim, theorem, experiment, or benchmark value changed.

## Verification

- `python -m pytest -q
  tests/exact_commit/test_submission_related_work_search.py` -> 3 passed.
- `make check` -> the EPIC pin, Ruff, and strict MyPy passed; 11 unit tests and
  672 exact-commit tests passed.
- `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q` -> 693 passed with the Rust
  binding loaded.
- `make paper` -> BibTeX emitted no missing-entry warning, the final LaTeX pass
  had no undefined citation or overfull box, and `pdfinfo` reported 16 A4 pages.
- All 16 rendered pages were visually inspected; the bibliography is legible,
  unclipped, and ends on page 16 with usable bottom margin.
