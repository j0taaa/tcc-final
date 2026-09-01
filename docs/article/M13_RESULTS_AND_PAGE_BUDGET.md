# M13 result selection and page budget

This record is the T1258 gate for T1301. The SBC article must remain within
the institutional 10--16 page limit, including references. The current
pre-result manuscript builds to 15 pages, so T1301 must replace placeholders
and remove obsolete planning material rather than append every generated
artifact.

## Selected result elements

The article body may contain exactly these three compact result elements:

### R1 — Correctness and finite-slot certificate table

Combine the configured Q1 oracle-agreement counts with the Q3 finite-slot
counterexamples. Report deterministic configured-family agreement as counts,
give a Wilson interval only for randomized Q1 seeds, and preserve the
`exact_on_support` and finite-slot qualifications. This replaces the current
expected-results table labelled `tab:resultados`; it does not follow it as a
new table.

### R2 — Heuristic-gap evidence table

Use one compact table to distinguish the illustrative synthetic Q2 cases from
the bounded T1254 replay of real decoder states. Do not present a population
mean gap: the synthetic rows are demonstrations, and the collected real-state
supports collapsed to singleton choices. The full row-level evidence remains
in the repository.

### R3 — Scaling and structured integration table

Use one compact table for the publication-mode Q4 CPU scaling envelope and the
structured Q5 integration facts. Keep Python and Rust timing separate, report
timeouts/censoring, call `graph_size_scale` a compound graph-size setting, and
state whether EPIC regular-cover batching actually ran. This table replaces
the final-TCC schedule table labelled `tab:cronograma`, which is no longer
scientific result content.

No fourth result table or figure is authorized by this plan. If the prose
cannot explain a result without another visual, T1301 must replace one of
R1--R3 or seek a revised page-budget decision.

## Repository and supplementary evidence

The following T1203 artifacts remain versioned, reproducible evidence but are
not inserted as separate article elements:

- `correctness-oracle-table.tex` and
  `finite-slot-counterexample-table.tex` are folded into R1;
- `heuristic-gap-table.tex` is summarized in R2, while
  `heuristic-gap-distribution.svg` stays repository/supplementary material;
- `runtime-breakdown-table.tex` is summarized in R3, while
  `runtime-scaling.svg` stays repository/supplementary material because it is
  explicitly diagnostic;
- `end-to-end-comparison-table.tex` stays repository/supplementary material and
  is superseded in the body by the structured EPIC-exercising evidence in R3.

`REPRODUCING.md` remains the index for every omitted artifact and its
verification command. The T1254 and T1255 evidence records remain the source
for the additional bounded real-state and publication-mode scaling facts.
Nothing is deleted or overwritten to meet the page limit.

## Page allocation

This is a planning budget, not a measured final page count:

| Article content | Target pages |
| --- | ---: |
| Title, Portuguese `Resumo`, and English `Abstract` | 0.75 |
| Introduction | 1.25 |
| Background and related work | 2.00 |
| formulation, algorithms, and proof correspondence | 3.25 |
| Implementation and reproduction contract | 2.00 |
| Evaluation setup and R1--R3 | 2.25 |
| Limitations and conclusion | 1.00 |
| References | 1.75 |
| **Target total** | **14.25** |
| **Contingency below the 16-page maximum** | **1.75** |

T1301 must preserve the template font, margins, required summaries, necessary
method details, limitations, and references. Space is recovered by replacing
the two named placeholder/planning tables and removing redundant prose, not by
silently shrinking required content. After results are imported, run
`make paper`, measure the produced PDF, and revise prose or replace an R element
if the measured total exceeds 16 pages. The 15-page T1258 build is only a
baseline measurement and is not a final page-count claim.

