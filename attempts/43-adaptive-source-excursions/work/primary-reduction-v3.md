# The sequential statistic is classical; retained payload novelty remains open

2026-10-12. This adverse reduction does not alter V1/V2 sources or results.

The correct Wolfowitz1947 DOI, verified through Crossref title metadata, is
10.1214/aoms/1177730439, not the previously attempted1177730433. The publisher
full/PDF addresses still returned an unavailable iframe in this environment.
Original text has NOT been read. The same remains true for the Akahira/Koike
and Simons reports; metadata or cached snippets are not full-text review.

Actually read Bibbona/Rubba, *Boundary crossing Random Walks, clinical trials
and multinomial sequential estimation*, arXiv:1101.4038v2, sections1/2,
Theorems2.1/2.2 and the examples in3.1/3.2:
<https://arxiv.org/pdf/1101.4038>. Their Theorem2.1 explicitly credits Koike1993;
the binary antecedents include Girshick/Mosteller/Savage1946 and Blackwell1947.
For a stopped count boundary, the ratio of admissible paths beginning with a
given label to all paths is an unbiased class-mass estimator. It is the
conditional expectation of the first indicator given the stopped counts.

A43's terminal class statistic T=(c(X)+c(Y))/2 equals

    T=(1+S_N/M)/2.

On a return to zero, path reversal pairs the two first-label choices and the
conditional expectation of c(Z1) is1/2. On a hit of+M it is1, and on-M it is0:
every admissible excursion hitting that signed barrier began on that side.
Thus T is exactly the classical conditional-first-indicator/path-count
estimator for this stopping region. Its unbiasedness is not a new sequential
estimation principle. Wald's equation and stopped information are also old.

The remaining question is the DIFFERENT expensive-operation contract:
materialize two ORIGINAL independent-position within-class payloads, retain
the literal first, evaluate arbitrary unknown downstream vectors only twice,
and preserve each full source marginal. The V1 sharp bound is phrased for
this pair contract; the scalar statistic reduction alone neither proves its
priority nor supplies a practical use. It prevents presenting the familiar
unbiased scalar estimator as the discovery.

Wasan1964, *Sequential Optimum Procedures for Unbiased Estimation of a
Binomial Parameter*, DOI10.1080/00401706.1964.10490183, publisher ABSTRACT read
only. It explicitly optimizes variance versus expected sample size and costs:
<https://www.tandfonline.com/doi/abs/10.1080/00401706.1964.10490183>.
Bhat/Kulkarni1966, *On Efficient Multinomial Estimation*,
DOI10.1111/j.2517-6161.1966.tb00617.x, publisher ABSTRACT read only:
<https://academic.oup.com/jrsssb/article/28/1/45/7027025>.
These reinforce that the general resource tradeoff is an antecedent.

Also read Jia/Shen/Wang2026, *Couple to Control: Joint Initial Noise Design
in Diffusion Models*, arXiv:2605.11311, sections1--3, Proposition3.1/3.2 and
the displayed matrix parameterization in Theorem3.3:
<https://arxiv.org/pdf/2605.11311>. Marginal-preserving noise batches and
Gaussian worst-pair correlation are already explicit diffusion contributions.
A43 cannot claim that idea. This paper's stated correlation optimum concerns
Gaussian raw noise; it is not an every-nonlinear-target unknown-class-mass
two-expensive-evaluation theorem. Neither distinction establishes priority.

Decision: preserve A43 as a mathematical candidate with a scoped unresolved
retained-payload question. Do not launch a large neural campaign or promote
it as publication-ready based on the scalar frontier alone. Investigate a
more specific all-vector sampling guarantee if it has an independently
provable advantage and a cheap dLLM/CFG operation.
