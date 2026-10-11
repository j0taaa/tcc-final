# A34 antecedents and outstanding reductions

2026-10-11. The following is a bounded reading record, NOT confirmation that
no prior paper has the proposed frontier. Direct sources unavailable here
must not be replaced by an invented assertion that they exclude it.

- Nacu–Peres2005, [primary PDF](https://arxiv.org/pdf/math/0309222), Section6/
  Proposition24 ACTUALLY READ for A32: exact bounded reflection construction
  and Bernstein envelope. Their algorithm is not invented here. Section5
  positive-prefix/tail techniques also read.
- Mendo2019, [primary PDF](https://arxiv.org/pdf/1612.08923), Section3/Theorem3
  ACTUALLY READ: fast sequential Bernoulli factories satisfy a score-based
  Cramér–Rao work bound. A34 reuses that principle; its proposed difference
  is the lattice restriction and SHARP full-budget minimax coupling frontier.
- DeGroot1959, DOI10.1214/aoms/1177706361, "Unbiased Sequential Estimation for
  Binomial Populations", Annals30(1),80–101. Publisher URL is blocked by an
  access challenge in this environment. Abstract indexed: jointly optimizing
  unbiased variance and expected sample size at a chosen p0 is ALREADY the
  problem studied there. Full Sections2/4/8 must be read before excluding an
  exact reduction. Do NOT cite this abstract as a proof of novelty.
- Ghosh1987, DOI10.1080/07474948708836131, "On the attainment of the Cramér–Rao
  bound in the sequential case", Sequential Analysis6,267–288. Publisher
  abstract accessed in earlier research; full text still unavailable. Covers
  Bernoulli exceptional attainability among exponential families. A34's fair
  integer-budget equality is not itself a novel claim unless a distinct
  output-restricted theorem survives this comparison.
- Koike1997, [primary PDF](https://www.jstage.jst.go.jp/article/jjss1995/27/1/27_1_65/_pdf),
  "The Bhattacharyya type bound for the variance of sequential estimation
  procedures". Introduction ACTUALLY READ; exact higher-order bounds and
  binomial examples exist. Remaining theorems/examples need direct comparison.
- Simons, sequential-estimator counterexamples: regularity of Cramér–Rao
  cannot simply be dropped. A34 explicitly assumes an exponential moment at
  the fair point; weaker assumptions are NOT currently claimed.
- Gambler's ruin: absorption probabilities, expected durations and stopped
  score/square martingales are CLASSICAL. The barrier sampler alone is not
  presented as an invention. Bernoulli races already give r=3/4 special laws.
- A29/A31/A32: full payload covariance and full-history induction are already
  written there, and standard Dirichlet/coupling arguments. A34 cannot own
  those principles. Its sole proposed new mathematical statement must be the
  explicit sharp frontier with all its assumptions, plus a useful consequence.

Mandatory objections: known-p maximum coupling; full-budget more-output iid;
weak semantic signal; classification/recovery cost; priority of lattice
information inequalities; expected versus hard stopping bounds; complete
trajectory meeting probabilities. None may be discarded to manufacture a win.

## Additional direct reading,2026-10-11

Koike1997 full Sections2/3 ACTUALLY READ, including Theorem2.1, Theorem3.1,
Examples3.1--3.3 and Remark3.2. Mathematical equations on printed69/73/74
were visually inspected in the original PDF (localSHA to be recorded). The
Bhattacharyya bound uses a2x2 covariance matrix of stopped first/second scores
and stopping-time moments; its binomial examples optimize g(p) under a given
sampling plan. No exact A34 output-restricted budget frontier was identified
in those sections. This is NOT an exclusion of DeGroot/Ghosh's full results.

Niazadeh/Paes Leme/Schneider, [Combinatorial Bernoulli Factories](https://arxiv.org/pdf/2011.03865),
v2(2024), Sections1/2/4 and AppendixE.1/E.10 ACTUALLY READ. Polytope factories,
Bernstein races, interior-zero impossibility and differentiation under fast
tails are PRIOR results. Their existence theorem/fast-factory obstruction is
not a cost-optimality theorem for the A34 paired-output contract in those
sections. Do not describe their existence/differentiability principles as
inventions; no exclusion of all variants or implicit consequences is proved.

DeGroot1959 original22-page scanned PDF was located in a mirror:
https://scispace.com/pdf/unbiased-sequential-estimation-for-binomial-populations-3exutqf436.pdf.
The web reader returns only cover OCR and screenshot references without usable
image data; direct local download returns403. Therefore the ORIGINAL SECTIONS
HAVE NOT YET BEEN READ. A located file is not a completed literature check.

Wasan1964, [publisher abstract](https://www.tandfonline.com/doi/abs/10.1080/00401706.1964.10490183),
"Sequential Optimum Procedures for Unbiased Estimation of a Binomial
Parameter", Technometrics6(3),259--271, DOI10.1080/00401706.1964.10490183:
the ORIGINAL ABSTRACT was read. It explicitly addresses unbiased variance
under expected observation budgets, uniform/minimax criteria, and a
noninteger-budget construction. This is a VERY CLOSE predecessor, added
before claiming novelty. Its full13 pages have NOT been retrieved; the
publisher PDF fails and JSTOR1266043 exposes no readable full text here.
The unrestricted estimator contract differs from A34's paired-output
restriction, but that alone does NOT prove a sufficiently new theorem.

Huber/Maric2014, [primary PDF](https://alea.impa.br/articles/v11/11-20.pdf),
"Minimum correlation for any bivariate Geometric distribution": Introduction,
Lemma1.1 and Section2 ACTUALLY READ. The coupling is the classical known-CDF
countermonotonic construction; probability evaluation and geometric output
contract differ from A34. The Frechet optimality principle is a predecessor,
not a result discovered here. No claim about all unexamined coupling papers.

## DeGroot original retrieved, after the unsuccessful mirror attempts

The complete ORIGINAL volume OCR is public at
https://archive.org/download/sim_annals-of-mathematical-statistics_1959-03_30_1/sim_annals-of-mathematical-statistics_1959-03_30_1_djvu.txt
(SHA256 `f0efcb7113268b4b8de36a031f97b3d383a7999853d15564f60941c42548a223`).
DeGroot's ORIGINAL Sections1--8 were read, including Lemmas2.5--2.7,
Theorem3.2, Theorem4.1, Theorem5.1, SchemesI/II and Theorems7.1--7.4/
8.1--8.8. OCR damages some equations; visual verification of the key formulas
is COMPLETE on printed84/91 in the public original PDF, AFTER A32 timings.
PDF SHA256:`421f0c9d368dbe5e2f7458256cf59e9fe7b972ae61d3f8d88fa3e3f3e88a4472`.
The equations in Lemmas2.5--2.7 and Theorem5.1 agree with the interpretation
above. The original volume is53MB and is not copied into source snapshots.
Its public PDF URL is the same volume path with `_djvu.txt` replaced by `.pdf`.

The score identity, stopped-square identity and variance/work principle used
in A34 are EXPLICIT predecessors: Lemmas2.5--2.7. Theorem5.1 links pointwise
efficient unbiased estimation of p to constant expected work. Integer fair-
point efficiency therefore follows the classical information inequality and
must NOT be claimed as an invented lower-bound principle. Section6 gives
constant-work unbounded procedures (including unbounded estimators), and
Section7 compares plans with the SAME expected-work function. Theorem7.4
classifies constant expected cost2 among its nonrandomized count-based plans.
Section8 characterizes completeness of bounded plans, not coupling optimality.

No paired-output, output-lattice restricted, normalized Frechet minimax
frontier was identified in the read sections. This narrows the possible
difference; it is NOT proof of exclusion from subsequent literature or of
sufficient scientific significance. Wasan1964/Ghosh1987 remain outstanding.
The Internet Archive metadata for Wasan's original issue
`sim_technometrics_1964-08_6_3` marks its OCR PRIVATE; it was not downloaded.

Bibbona/Rubba2011, [primary PDF](https://arxiv.org/pdf/1101.4038), Sections1/2
ACTUALLY READ: Theorem2.1 credits Koike1993 for boundary path-count ratios as
unbiased multinomial estimators, and the introduction credits Girshick et al.
1946 for the binomial case. The first-bit Rao--Blackwell interpretation of the
ruin pair's mean is a CLASSICAL construction, not a second new contribution.

Koike1997 original PDF SHA256:
`0e8fefa970ff868245178ae94e5199e2ae64428a4e124a8b217ec3fc6d79f9a0`.
