# Arbitrary source budget: pre-code mathematical investigation

2026-10-11. Written BEFORE the new finite oracle or neural outputs. This is
a refinement of the opaque-source direction, not a new empirical benchmark.
The four-source pivotal reduction is preserved in v3. No priority claim.

## Reassessment of the eight scientific questions

1. **Operation.** Original-source two-output coupling for a fixed CFG-valid
   dLLM candidate's noising evaluations. An implicit source produces cheap
   states and an opaque categorical proxy; only two retained states are scored
   by the real model. Raw/class-query interfaces must be kept separate.
2. **Difference.** Investigate the COMPLETE source-query budget frontier,
   rather than another proof that four-pool pivotal sampling is correct.
   Bernstein/hypergeometric interpolation, pivotal and half-rotation are OLD.
   Exact minimax characterization, its priority and significance remain open.
3. **Comparators.** Competent source derangement, same-law classical balanced
   pools, arbitrary adaptive source-aware queries and analytical masses or
   inverses when available. No universal win over arbitrary score couplings.
4. **Mathematics.** State the all-budget candidate below; check the novel step
   BEFORE implementing a training experiment. Preserve any counterexample to
   scalar/vector covariance or misleading budget improvement.
5. **Experiments.** The finite oracle is a correctness/objection search, not
   a favourable dataset. No external model measurements authorized by this
   note's conjecture; a separate frozen realistic protocol remains necessary.
6. **Costs.** A hard cap B counts original states whose BOTH labels and
   payloads are materialized (A39 interface), including both outputs. This
   cap is NOT a classifier-only bound for A41's unclassified-output interface.
   Pool construction B versus two actual neural calls, rational tickets,
   bit costs and any proxy preparation all remain charged.
7. **Objections.** Empirical atom balance can have positive covariance for a
   non-monotone score. A sharp atom frontier may still be known or too weak
   for an article. Generalizing an elementary formula alone is insufficient.
8. **Gap.** Need complete proof, closest primary precedent, practical
   consequence and minimal real-model validation. Publication is not decided
   by the number of tests, budgets or Lean statements.

## Precise candidate: universal opaque SOURCE-query cap

Uniform known source size M, 2<=B<=M, arbitrary unknown class assignment with
at least three permitted labels. First uniform source is retained literally.
Both returned sources are queried/materialized. Second ORIGINAL-source
marginal is uniform for EVERY class map. Adaptive source-address selection
and randomized cloning are permitted. No free labels/masses/inverse.

For an atom of size t define

 g_B(M,t) = sum_(r=0)^B [choose(t,r)*choose(M-t,B-r)/choose(M,B)]
                        * max(0,2r/B-1).

Candidate theorem: the worst-placement joint atom diagonal of ANY such cap-B
algorithm is at least g_B(M,t); one universal construction attains it for
ALL atoms/placements. The degree-B finite-grid uniqueness proof in the own
A39 theory appears to extend directly, but that generalization must actually
be checked, not called a new sampling principle.

Construction to audit: query a uniform distinct B-source pool; group sources
by proxy class, choose a uniform class ordering independent of scores, and
uniform ordering inside each class. Each raw source occupies a cell of length
two on a circle of2B tickets. Uniformly choose the within-cell ticket of the
literal first source; translate by B tickets and return the occupying source.
This is classical grouped half-rotation. On a uniformly oriented pool it
preserves source marginals and has conditional atom diagonal max(0,2r/B-1).
No arbitrary-f/full-gradient variance theorem is assumed for this construction.

Further questions (NOT yet theorems): odd budgets may have the same atom
frontier as the previous even budget; the exact gain between even budgets
may have a positive closed falling-factorial form. A budget of more cheap
proposals can improve coverage without more than two expensive evaluations,
but that does not itself justify the full wall-time/quality tradeoff.

An iid infinite-source analogue uses binomial rather than hypergeometric
counts. Do not transfer finite-source exclusions or without-replacement
corrections to iid sources silently. Source sizes/finite RNG tapes are part
of the declared operation, not an exact continuous ELBO integral.

## First adversarial result: atom optimality is not universal score safety

An exact pre-model search checked65 integer pool partitions for B=2--8 and
EVERY Boolean union of their classes. It found B=8 with sizes(1,1,3,3),
where the event is the union of the two singleton classes. Under uniform
class ordering and half-rotation, joint event probability is1/12, versus
the independent probability(1/4)^2=1/16. Covariance is therefore+1/48.
For two-score means the variance is5/48, versus iid2's3/32, an11.11% increase.
Every individual atom still attains its conditional Frechet diagonal.

The written atom-frontier candidate does NOT imply the v2/v3 guarantee for
all terminal verifiers, vector gradients or arbitrary scores. Do not promote
this full-pool construction as a universally safe gradient replacement.
This is a mathematical counterexample, not an empirical dLLM result. A
different construction might avoid it; that requires a different proof.

## Written all-budget atom proof and exact even-budget consequence

Let L be the finite number of PERMITTED labels. After randomizing the source
addresses and padding unrequested queries to B, the observation counts r have
the multivariate hypergeometric law. A universal algorithm's conditional
second class marginal z_i(r) can depend on M and observed identities, but
not on the unknown global counts. Source symmetrization averages identities.
For every feasible global count vector n the marginal requirement is

 sum_(|r|=B) [B!/prod r_j!]*prod(n_j)_(r_j)/(M)_B*z_i(r) = n_i/M.

The same equation holds for z_i(r)=r_i/B. The coefficient matrix is invertible:
evaluate at nodes n_j=u_j for j<L with sum u_j<=B, and n_L=M-sum u_j.
Order by sum outside L. If r_j>u_j for any j<L the entry is zero; at equal
degree only the identical outside-L vector is nonzero. Diagonal is
prod_(j<L)u_j! * (M-sum u_j)_(B-sum u_j)>0 since M>=B. Thus z_i(r)=r_i/B.
The original uniform retained anchor has the same conditional marginal.
Conditional Frechet forces joint diagonal>=max(0,2r_i/B-1). Average and use
worst placement>=symmetrized placement average. The grouped half-rotation
construction attains that bound for all atoms, proving the candidate atom
theorem. This argument extends the own A39 proof; interpolation and
coefficient positivity are known tools, not a claimed new principle.

Let C_r=choose(2r,r)/(r+1), the Catalan number. For 2r+1<=M,

 g_(2r+1)(M,t)=g_(2r)(M,t).

For 2r+2<=M,

 g_(2r)(M,t)-g_(2r+2)(M,t)
   = C_r * (t)_(r+1)*(M-t)_(r+1)/(M)_(2r+2).

Proof independent of code: delete a uniform element from a pool. In an odd
pool n=2r+1 with j atom members, the expectation of
max(0,2(j-removed)/(n-1)-1) equals max(0,2j/n-1): both expressions are zero
for j<=r, and the linear identity holds for j>=r+1. Hypergeometric
projectivity gives the odd identity. In an even pool n=2r+2, the comparison
with the preceding odd pool is zero except at j=r+1. At that central count
the smaller-pool expected bound exceeds the even-pool bound by
1/[2(2r+1)]. Its hypergeometric probability is
choose(2r+2,r+1)*(t)_(r+1)*(M-t)_(r+1)/(M)_(2r+2).
Simplifying the coefficient gives C_r. This also proves monotonicity and
strict improvement iff r+1<=t<=M-r-1. Endpoints and zero factorials are
explicit. Cap2/cap3 coincide with source derangement's atom diagonal.

This characterizes a COMPLETE comparative atom frontier, not physical speed,
all-verifier success or arbitrary-gradient dominance. Its closest-precedent
priority/significance and practical CFG/dLLM consequence remain unresolved.
