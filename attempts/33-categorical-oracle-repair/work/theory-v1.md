# Categorical repair: written candidate, no implementation claim

2026-10-11. This file specifies a different operation from frozen A32/v4.
Barker/race simulation, reversibility and Dirichlet forms are antecedents.
The arguments below are written proofs, not Lean verification, human review,
timings or a claim of priority. No new neural forward is attributed to A33.

## 1. Operation

Let P be an arbitrary distribution of complete original payloads. Fix a
measurable map c to a finite or countable category set BEFORE any oracle draw.
Write p_i=P(c=i), ignoring zero-mass categories. Draw X,Y iid P and retain X
literally. If c(X)!=c(Y), return Y as the second payload. Otherwise let
i=c(X)=c(Y), draw Z iid P, and let j=c(Z).

If j=i, keep Y. If j!=i, draw iid W until c(W) belongs to {i,j}. Return Z if
c(W)=j, and the original Y if c(W)=i. The payload W is never returned.
The choice uses categories only; it does not evaluate p_i or a density.

Termination follows because p_i+p_j>0 on every visited branch. This is a
standard conditional Bernoulli race, providing Barker probability p_j/(p_i+p_j).

## 2. Complete marginal law and arbitrary scores

For i!=j, the extra flow beyond the original iid pair is

    w_ij = p_i^2 p_j * p_j/(p_i+p_j) = p_i^2 p_j^2/(p_i+p_j).

It is symmetric. Thus the class-pair law is

    J_ij = p_i p_j + w_ij                  (i!=j),
    J_ii = p_i^2 - sum_{j!=i} w_ij.

The diagonal is positive: sum_j p_j^2/(p_i+p_j)<sum_j p_j=1-p_i,
so J_ii>p_i^3 for a distribution with at least two positive categories.
Both row and column sums are p_i. Conditional on returned categories,
the two payloads remain independent with laws P_i and P_j, respectively:
all decisions used only categories; the second is either the independent
original Y or independent proposal Z. This includes aliases and original IDs.

For f in L2(P), set mu_i=E[f|c=i]. Subtracting the iid joint law gives

    Cov(f(X),f(Y')) = -sum_{i<j} w_ij (mu_i-mu_j)^2 <=0.

For countably many categories, nonnegative energy sums converge by the finite
L2 bound and the established joint law. Equality holds precisely when mu_i
is constant on positive-mass categories. For any event A, write a=P(A),
a_i=P(A|c=i). Then

    pass@2 = 2a-a^2 + sum_{i<j} w_ij (a_i-a_j)^2.

There is no gain in pass@1. For an injective c this gain is strictly positive
for EVERY event with 0<a<1. A coarse token class does NOT imply injectivity
on future decoder states or on final semantic outcomes.

## 3. Exact expected oracle work

Let N count all P draws, including X,Y. The proposal Z is drawn with
probability C=sum_i p_i^2. The race is reached with probability p_i^2 p_j
for each i!=j and costs mean1/(p_i+p_j) draws. Tonelli gives

    E N = 2 + C + sum_{i!=j} p_i^2 p_j/(p_i+p_j)
        = 2 + C + sum_{i<j} p_i p_j
        = 5/2 + C/2 <=3.

This is a bound on iid oracle draws, not parser steps, wall time or forwards.
The second moment need not have a distribution-independent bound: for m
equal categories, collisions have probability1/m but the conditional race
has success2/m and second moment of order m^2. Unconditional second moments
grow with m. Small expected work must not hide a latency tail.

## 4. Sharp minimax work FOR THIS TARGET LAW

Among all probability-blind adaptive factories retaining the first draw,
preserving both marginals and realizing the displayed J for EVERY Bernoulli
p in(0,1), permit arbitrary auxiliary randomness and arbitrary a.s.-finite
stopping. Then sup_p E_p N>=3. The construction attains3, as a supremum.
This is not an optimum among all possible antithetic target laws.

Proof: in the binary case p_1=p, p_0=q, the target J11 is

    p^2-p^2 q^2 = 2p^3-p^4 = O(p^3).

Any positive-measure auxiliary choices stopping on k<3 all-ones observations
and outputting second bit1 would contribute alpha*p^k to J11, a contradiction
as p approaches0. No all-ones finite leaf outputting0 is possible either:
its alpha*p^k contribution to J10 violates J10<=q as p approaches1.
Therefore P_p(N>=3)>=p^2 and E_p N>=3p^2. Let p approach1. The previous upper
bound proves the minimax identity. No continuity of expected work, endpoint
termination or hard stopping budget was assumed. Positive-prefix arguments
are classical Bernoulli-factory tools; priority of this target-specific
identity is still unconfirmed.

## 5. Safe deterministic truncation, with a DIFFERENT explicit law

After at most R>=1 race draws, keep original Y if no category i or j appeared.
No new FAIL is introduced. Symmetry is preserved, with

    w_ij^(R) = p_i^2 p_j^2 [1-(1-p_i-p_j)^R]/(p_i+p_j).

The total draws satisfy N<=3+R, and E N<=5/2+C/2. All preceding marginal,
nonpositive-covariance and nondegenerate-class-effect statements remain true,
but the target is J^(R), NOT J. R=1 is a coin-thinned instance of A29's general
stationary-collision transform, and in the BINARY case coincides with A32/v1.
It is NOT the one-proposal probability-aware MH implementation of A29.

## 6. Whole decoder paths: strictness needs complete transition classes

Consider a finite-horizon native structured decoder. Make terminal states
absorbing, include every item affecting future behavior in its history, and
assume per-label kernels do not depend on other trajectories. At equal full
histories, use the preceding coupling for the next transition. At different
histories, continue independently. Only the first trajectory's native draws
are retained literally. Extra oracle work never changes a per-label logical
budget or silently drops a recovery alternative.

For a terminal score f, let h_s(next)=E[f|history s,next]. The usual backward
induction over the product process gives

    Cov(f(output1),f(output2))
      = -sum_s P(pair visits equal history s)
          sum_{i<j} w_ij(s) (E[h_s|c=i]-E[h_s|c=j])^2.

This is the classical local Dirichlet-energy/coupling argument, now using the
specified sample-only kernel. If c identifies the COMPLETE next history,
every nonconstant terminal f has a positive energy at some reachable equal
history: otherwise all conditional expectations remain constant from the
root to terminal leaves. Both histories can reach that node together because
every positive-mass diagonal is positive. Thus covariance is strictly negative
for every nonconstant finite terminal score, and pass@2 is strictly larger
than iid for every nondegenerate terminal event. The magnitude can be tiny.

For incomplete categories only weak dominance is proved. For sufficient-state
coalescence after divergence, K>2 batches, adaptive global budgets or labels
that share mutable decoder behavior, this written statement does not apply.

## 7. Honest cost and comparator boundaries

Complete transition classification may require substantial grammar work.
There is currently NO A33 realization proving it cheaper than a full model
run. A frozen-head implementation must replay the exact native ranking,
transfer schedule, regular-cover path, rejection count, EOS and recovery.
Classifying only raw argmax is a weaker operation, explicitly so.

Knowing the class probabilities allows stronger conventional couplers, e.g.
the Metropolized Gibbs sampler; approximate ideal-PL probabilities may also
be a practically better control. Replacing the native finite law with them
changes the exactness claim but must not exclude them from cost/quality tests.
Even a perfect marginal-preserving pair increases rare-event coverage by at
most a^2 when a<=1/2. Real utility, priority and publication significance remain
OPEN. A32's running timings do not measure this algorithm.
## 8. Reduction gate, before implementation

A29 Section1 already supplies the general stationary collision transform.
For identical category laws its collision target is R_i proportional to p_i^2.
An independent proposal from p followed by ordinary Barker acceptance has
ratio (p_j^2*p_i)/(p_i^2*p_j)=p_j/p_i. Hence its acceptance is exactly
p_j/(p_i+p_j). A33 is precisely that existing transform with the known Barker
coin-race implementation. The diagonal/Dirichlet and full-path statements are
consequences of the old transform; the expected-work calculation is a useful
specialization but does NOT presently justify a new protagonist.

Decision: do not expand this into a native implementation or neural campaign
unless a genuinely distinct useful result appears. Preserve it as a written
reduction and a competent possible control. No novelty or utility goal is
declared fulfilled by these notes.
