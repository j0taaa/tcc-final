# TCC in LaTeX — Exact MWPC for CFG-constrained dLLMs

This directory contains the SBC-format article **Certifying Parallel Commitment
and Sampling Error for CFG-Constrained Diffusion Language Models**.

The current build has **16 pages**, with definitions, complete proofs,
resource recurrences, checkable optimality, complexity and implementation
contracts, fresh prediction/admission results, historical negative findings,
limitations and the AI-use declaration. Complete historical tables remain
unchanged in their generated files and supplementary sources. Earlier algorithms and empirical detail are preserved in separate
supplementary sources.

M27 adds certified incumbent-quality/support-expansion bounds, compact token
prefixes and Lean-checked resource certificates. The precise coverage in
[`formal/README.md`](../formal/README.md) distinguishes mathematical kernel
proofs from the independent Python original-input check and unproved foreign
source refinement. No new latency, semantic-accuracy or benchmark-win claim
is introduced.

## Files

- `main.tex`: main manuscript and project entry point;
- `referencias.bib`: BibTeX database;
- `sbc-template.sty`, `sbc.bst`, and `caption2.sty`: SBC format files;
- `main.pdf`: local compiled preview;
- `FIELDS_TO_FILL.md`: checklist of implementation-dependent fields;
- `generated/`: small tables and figures produced only by scripts from
  versioned raw JSONL; and
- `Makefile`: build and cleanup commands.

## Building with Overleaf

1. Create an empty project and upload every file in this directory.
2. Set `main.tex` as the main document.
3. Select `pdfLaTeX` as the compiler.
4. Overleaf runs BibTeX automatically. If references remain unresolved, use
   **Recompile from scratch**.

## Budgeted-reward foundation

The M26 foundation centers joint budgeted commitment and independently checkable
optimality. `budgeted-math.tex` contains the exact resource-DAG construction,
complete proofs, universal same-input batch comparison and infinite-family
separations. The mathematical contribution does not depend on benchmark wins.
Original parser proofs are preserved in `supplement-foundations.tex`; full M25
empirical prose is preserved verbatim in `supplement-empirical.tex`. These separate
sources supplement the main page budget. Historical negative evidence remains
in the main text and unchanged supplementary generated tables.

The rational reference budget API is implemented. Production Rust integration
for this dimension and full source refinement remain future work; Lean already
checks the documented mathematical specifications and selected resource cases.
The earlier GPU results measure the old policies, not this new algorithm.

## Building locally

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Or:

```bash
make
```

## Remaining fields

Information that has not yet been established appears through this command:

```latex
\ph{field to fill}
```

The PDF renders these fields in bold and inside brackets. To find all of them:

```bash
rg -n '\\ph\{' main.tex
```

Replace a field only when verifiable evidence is available. Results, runtimes,
memory use, and metrics must never be estimated or fabricated. Do not edit
numbers under `generated/` manually; use the generator and manifest described
in `docs/artifacts/README.md`.

## Important notes

- The proven optimality is per-step and relative to the finite support actually
  represented by the lattice.
- With top-K support, the final text must say `exact_on_support`; it must not
  claim global exactness over the full vocabulary.
- The proofs assume that the lattice and lexical interface exactly represent
  their declared semantics. Every approximation must be documented.
- The bibliography and novelty claims must be updated before the final version
  because this is a rapidly evolving research area.
- The AI-use declaration must describe the author's actual use of the tools.

The current main article is *Certifying Parallel Commitment and Sampling Error
for CFG-Constrained Diffusion Language Models*. It separates exact reward
optimization from certified mean-field sampling/admission. `probabilistic-commitment.tex`
contains the mass, sharp conditional-error, coverage and transport statements.
Twelve fresh CPU MDLM predictions and all 192 outcomes are documented by the
[generated report](../docs/artifacts/processed/m30_probability_v1/report.md).
The [complete larger-canvas audit](../docs/artifacts/processed/m31_probability_v1/report.md)
adds 18 fresh predictions and retains all 36 cells, including one external
timeout. All 35 returned proofs pass, but admission declines at 8/16 slots and
the independent compact exact control has lower measured inference cost on
every completed pair. This explicitly limits practical-benefit claims. It is
not an execution or ranking of published competitor implementations.
Established WMC/conditioning, support filtering and AR grammar alignment are
explicit antecedents; no world-first principle or general decoder superiority
is claimed. The nine-theorem correspondence is in the
[current proof audit](../docs/evidence/submission-proof-audit.md).

The page-limited main preserves complete historical negative findings in prose;
full historical tables and longer DP/foundation/conflict proofs remain in the
supplement sources. `make article-results-check` verifies all generated products,
including M29--M31. `scripts/check_paper.py` retains the 16-page/no-overflow gate.


## Source cleanup and test reset (M32)

The user removed the old Python/Rust/upstream tests and historical campaign
framework. Their results remain attributed to the pre-cleanup source freeze
`a98ae8e09f2066157ebf6df05f8873b8600e00fb`, recoverable via Git. The reduced tree
maintains inference/certification, the current M31 campaign, immutable paper
products and unchanged Lean sources. `make article-results-check` checks frozen
hashes and M31 certificates; earlier generators run from the historical source.
Current operational checks are not a replacement correctness suite.
