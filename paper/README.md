# TCC in LaTeX: exact finite-token inference for constrained dLLMs

The current SBC-format article is **Exact Finite-Token Inference for
CFG-Constrained Diffusion Language Models**. The compiled manuscript has
16 pages and retains the existing 10--16-page/no-overflow gate.

The primary new contribution is a checked recursive-grammar posterior backend:
exact original-token valid mass, marginals and sampling, with finite slots,
explicit support loss and reusable inference after new commitments. Its
mathematical utility is a scoped polynomial-versus-exponential representation
separation and avoidance of rare-acceptance rejection. Weighted CFG sampling
is explicitly credited to its classical antecedents; no world priority,
semantic-quality or universal decoder-speed claim is made.

## Sources and evidence

- `main.tex`: manuscript, abstract/resumo, methodology, complete negative
  historical findings, limitations and AI-use declaration.
- `cfg-posterior.tex`: exact posterior theorem/proof, tokenization/arithmetic/reuse,
  typed nesting and direct JSON utility, bit-cost scope, competitor distinctions
  and all nine fresh model outcomes.
- `commitment-summary.tex`: complementary budgeted MWPC/certificate summary.
  Complete prior resource/conflict/separation proofs remain unchanged in
  `budgeted-math.tex`, `conflict-commitment.tex` and `supplement-resource-dp.tex`.
- `probabilistic-commitment.tex`: ambiguity-safe mass/error/coverage/transport.
- `generated/`: tables/numbers regenerated from recorded source artifacts.
- `referencias.bib`: primary references, including established Markov/CFG
  sampling and current dLLM methods.

The [complete M34 report](../docs/artifacts/processed/m34_cfg_posterior_v1/report.md)
includes every comparison, failure and losing case. All 52 previously successful
exact outputs are unchanged after refinement; eight of nine fresh JSON cases
resolve. One-type counters and small-case rejection remain cheaper. Every source
config/commit, full-token probability input and hash is archived; full logits
remain local. Mathematical specifications, implementation tests and empirical
application evidence are distinct. See [Lean scope](../formal/README.md).

## Build

```bash
make article-results-check
make paper
```

From this directory, `make` compiles with pdfLaTeX/BibTeX and validates the final
PDF. Overleaf: upload this directory, select `main.tex` and pdfLaTeX, then rebuild
from scratch if references remain unresolved.

Never edit generated numbers manually or fill unknown fields with guesses.
Reproduce the M34 products with `build_cfg_posterior_results`; earlier frozen
artifacts and negative M31 evidence retain their original producing commits.
The old test suite remains removed; the latest user request authorizes eight
focused independent posterior tests. This does not constitute Lean verification
of all Python/Rust/model source or a general decoder superiority result.
