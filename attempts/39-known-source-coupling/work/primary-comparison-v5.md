# Further original categorical-sampling comparison

2026-10-11. CARMS, Dimitriev/Zhou, NeurIPS2021, original
[PDF](https://proceedings.neurips.cc/paper/2021/file/6e16656a6ee1de7232164767ccfa7920-Paper.pdf),
SHA256 `6b0d1ed4eae5444777abe36c57764732908abdad01461e494ad6686b43fd3170`.
Actually read introduction/related work and Sections2--3.2 including
Theorems1--3, Algorithms1--2, equations7--11. Not its full experimental
campaign or all appendix proofs.

Known probability-preserving categorical antithetics, shuffled CDF
orderings, copula Gumbels and REINFORCE correction are antecedents. CARTS
Theorem2 assumes every off-diagonal probability is at least its iid product
for its strict gradient-variance conclusion. A38/A39 do not automatically
satisfy that off-diagonal condition; their unweighted terminal-score
covariance cannot be relabelled as the CARMS gradient guarantee. CARMS uses
known category probabilities/bivariate masses (or estimated masses for
Gumbels), unlike an opaque first grammar-recovery lookup whose class law
is not supplied. That distinction does not prove computational hardness
of the actual EPIC map or superiority over an informed implementation.

The construction is NOT new because it uses categorical/empirical
antithetics in a dLLM. Remaining candidate assertions are the precise
known-source opaque-label cap/query minima and paid native integration.
Countercontrols with known analytical probabilities remain legitimate
where they solve the same native operation. No gradient training claim,
general learned-coupling defeat or publication confirmation follows.

The authors' official Makur/Luo pages were also rechecked: the2026
49-page multivariate preprint is listed, but no accessible PDF is linked;
the2025 original `AntitheticVariates.pdf` still returns404. A38 read its
2025 slides, NOT either complete manuscript. This unresolved original
scope cannot be counted as a completed exhaustive novelty check.
