# Prospective comparison with strong classical RSS

2026-10-12. Written BEFORE a comparison oracle or any new model observations.
This is a corollary of V1, not another claim to invent ranked sampling.

Let the same fixed THREE classes have population masses1/3. Allow ANY fixed
ordering of these classes in the classical two-output RSS operation, including
the best order for the target. RSS may retain the literal original anchor by
the conditional simulation already preserved in A41. Its four original
queries, two expensive target evaluations and all preprocessing are charged.
Neither a random weak ordering nor a discarded anchor is imposed.

Write mu_i for centered conditional vector means, sum mu_i=0,
S=(1/3)sum mu_i mu_i^T for between-class covariance, and V for full covariance.
For the ordered low/middle/high classes, the RSS cross covariance is

    -D D^T, D=(2/9)(mu_low-mu_high).

Cauchy--Schwarz gives D D^T <= (8/27) S for EVERY such order and ANY vectors.
V1's three-class sampler has cross covariance -delta_B S, where

    delta_B=(1-9 D_B(1/3))/2.

For B=6, D_6(1/3)=29/729 and delta_6=26/81 > 8/27=24/81.
Thus EVERY B>=6 sampler in V1 dominates EVERY fixed THREE-class RSS order
in full pair-average covariance at population balance, with strict difference
at least S/81 for B=6. This preserves within-class variation and arbitrary
gradient directions; it is not only a comparison of a fitted scalar score.
The B=6 case is also a consequence of A42V6, not a new C6 theorem.

## Complete cost, instead of equating variance and speed

For a scalar projection put beta=V_between/V_total in[0,1]. Candidate mean
variance is V_total(1-delta_B beta)/2. EVERY class-ordered RSS mean variance
is at least V_total(1-(8/27)beta)/2. If the candidate's full pair cost divided
by RSS's full pair cost is r, a SUFFICIENT cost-normalized advantage is

    r (1-delta_B beta) < 1-(8/27)beta.             (1)

For r>1 this requires beta>(r-1)/(r delta_B-8/27), with positive denominator.
For a prespecified20% cost-normalized reduction the stronger condition is

    beta >= (r-.8)/(r delta_B-.8*(8/27)),          (2)

again with positive denominator. At B=16 and r=1, this already requires about
90% of variance between the three classes. That is a demanding condition,
NOT a practical victory. Extra source/classification/fitting costs may remove
the advantage. Vector trace and each selected projection need their own beta.

If there are many targets and the amortized costs meet(1), independent pairs
give smaller estimator MSE for the same expected total budget. This is a
mathematical use condition, not physical timing measured on the actual model.

## Legitimate objections and limits

RSS with a FINER continuous proxy is not covered by the three-class bound;
neither are known-mass stratified inverses, seed derangement, control variates,
score-aware selection or more expensive target evaluations. They remain
competent application controls. Population masses need not be exactly1/3
after fitting on past data; V1's iid safety still holds but this RSS domination
does not follow automatically. The existing(.8,.1,.1) adverse C4 case stands.

This comparison refines README criteria3/6/7: it establishes a conditioned
comparative benefit without selecting benchmark outcomes, and reveals how
large the explained full-gradient fraction must be. It does NOT establish
publication novelty, semantic improvement, EPIC superiority or neural utility.
