# V1 — A finite exact formulation before the first solve

2026-10-17. No optimum, saving or priority asserted yet. All arithmetic below
is rational. LP duality, exchangeability and Bernstein coefficients are known.

## 1. The genuine information contract

An iid oracle returns original payloads, with a fixed observable k in{0,1,2}.
These are THREE ALLOWED labels, including zero-mass labels. The algorithm
sees observed payloads and independent randomness, not probabilities or other
P-dependent information. It preserves both original marginals for EVERY P,
retains the literal first payload X1, and stops with N<=6. Its second output
is an observed original payload. Do not discard failed generations or treat
the raw randomness/masses as unavailable when a real API exposes them.

Write p_i=P(k=i). The target is simultaneous maximal reduction of every
canonical-atom diagonal under cap6. The classical padded-Bernstein bound is

    J_ii >= 5 p_i^4 - 6 p_i^5 + 2 p_i^6,
    d_i=p_i^2-J_ii <= p_i^2(1-p_i)^2[1+2p_i(1-p_i)].       (1)

Proof: condition a virtual six-tape on r occurrences of i. Universal second
marginal and nonnegative other diagonal force its joint-diagonal coefficient
to be at least max(0,2r/6-1). Summing binomial terms r=4,5,6 gives(1).
This is the known Bernoulli/Bernstein clipping principle, not a new theorem.
Uniform minimum-repeat perfect matching on the six original positions attains
it simultaneously: a majority label's unavoidable self pairs have count
2r-6; all nonmajority labels can avoid self pairs. Thus a full-six control is
available. A38/A42 already establish relevant constructions; none of their
old resource/semantic observations is an A63 measurement.

Here optimize E N at U3, the law uniform on three fixed representative
payloads. The claim sought is a fair-POINT optimum among universally valid
algorithms, not a pointwise optimum for every P. A key-only achiever would
have the same cost at any P with uniform key masses. The lower bound for
arbitrary raw algorithms is at the representative law; it does not assert
that raw metadata can never help on other within-class laws.

## 2. WLOG reduction for that comparison point

At U3, average any universal algorithm over the six label permutations,
renaming its outputs back. Universality and atom optimality remain true,
and its mean cost at U3 is unchanged. For representative payloads, anonymous
equality-pattern histories therefore suffice for a lower bound. This does
NOT symmetrize a nonuniform P without altering its pointwise cost.

No previously unobserved label can be returned: a law supported only on the
observed labels gives that same finite transcript positive probability and
the unobserved label zero marginal probability. Nor may the algorithm stop
returning the first LABEL while that label occurs only once in the observed
prefix. Pad its future tape avoiding that label; the target degree-six
diagonal coefficient for count1 is0, contradicting any positive stop mass.
When the first label has already repeated, some nonfirst index has that label.
Thus at representative laws allowing first clones gives no extra stopping
action beyond the nonfirst-observed-label action below. The achiever will
always choose an actual nonfirst index, even when raw aliases differ.

## 3. Stopping-flow variables, no model-dependent approximations

Let S be every restricted-growth equality pattern s of lengths1..6 using at
most three labels; the first symbol is0 and a new label is the next integer.
For each s and label j already appearing in a NONFIRST position, define

    x[s,j] = probability of stopping at prefix s and returning label j,

conditioned on the complete observed KEY tape being that prefix, integrating
only internal randomization. This is unconditional reach-times-action mass,
not the probability after conditioning on reaching that node. Its feasibility
constraints are

    x>=0,
    sum_(u proper-prefix of s,j) x[u,j] + sum_j x[s,j] <=1,

with equality at length6. A missing variable is zero. Conversely every such
flow gives a real sequential rule: on reaching s, use probability
x[s,j]/(1-sum_(u proper-prefix,j)x[u,j]); otherwise continue. Zero-reach
states are never visited. The rule depends only on the observed prefix,
never the unobserved future padded tape.

For a NAMED six-tape t, let out_j(t) be the sum of its prefix flow variables
whose returned anonymous label corresponds to actual named j. Its first
label is t1. For every unordered named multiset n of six keys, exchangeability
and universal degree-six coefficient uniqueness require

    average_(t in permutations(n)) out_j(t) = n_j/6,
    average_(t in permutations(n)) 1[t1=j] out_j(t)
                                     = max(0,2n_j/6-1).    (2)

It suffices to enumerate the seven integer-partition profiles with at most
three blocks, using ALL their named tape permutations and every named j.
Anonymous symmetry supplies relabeled profiles; do not use just one ordered
tape per profile. Equations(2) are conditional-multiset marginal and optimal
diagonal constraints. Off-diagonal laws need NOT equal a chosen matching
reference: imposing that extra equality would weaken the competitor class.

Why(2) is complete: pad every stopped run to six unused iid calls. Equality
of universal output polynomials on the simplex extends homogeneously and
forces all multivariate Bernstein coefficients. Conversely those coefficients
give the universal second marginal and all atom optima for every p. This is
a finite representation of every symmetrized stopping rule under the stated
representative-law comparison, not a heuristic policy search.

## 4. Objective and certificates

For s of length h with m distinct labels, its probability under U3 is

    a_s=(3)_m / 3^h.

The expected total source calls equal

    E_U3 N =6-sum_(h<6,s lengthh,j) (6-h) a_s x[s,j].       (3)

Minimize this rational linear expression over the exact constraints above.
A floating numerical optimum is NOT a theorem. Retain all rows, primal and
dual outputs. Reconstruct rationals, check every equality/inequality, dual
sign/reduced-cost inequality and ZERO primal/dual gap with an independent
verifier. If reconstruction fails, record INCONCLUSIVE. An exact dual proves
a lower bound for the full symmetrized class; a realizable primal attains it.
This would be a finite computer-assisted certificate, not Lean or human review.

The finite formulation has at most sum_(h<=6)Bell(h)patterns and at most three
actions per pattern. It is small for fixed cap6; it is exponential in growing
cap and cannot be promoted as a general polynomial factory optimizer.
Production lookup/state updates of a resulting rule would be cheap, but that
must be separately implemented/validated before any runtime statement.

## 5. Full payloads, common-score covariance and other controls

For an anonymous rule, choose uniformly a NONFIRST index of the selected key.
Conditional on the key tape, original payloads at distinct indices are iid
within their classes. This lifts the key-law marginal to the full raw law and
preserves literal first. It does not rewrite tokens/values or discard FAIL.

For three keys the symmetric pair law is fixed by its marginals and three
diagonals. For distinct i,j,k,

    J_ij+J_ji=p_i+p_j-p_k-J_ii-J_jj+J_kk.                 (4)

Consequently all feasible solutions have the SAME expectation of f(X)f(Y)
for every common square-integrable key score f. They also have the same
Boolean coverage, though their full ordered pair laws may differ. For raw
scores under the independent within-class lift, replace f by its conditional
class mean for the covariance term. A covariance-safety claim still requires
checking the known cap-six reference proof, not just assuming diagonal optima
imply safety for larger alphabets. No such larger-alphabet claim is made.

Literal same-pair-law comparison, as opposed to marginal/diagonal/covariance
comparison, would need extra constraints and may have a different optimum.
Probability-aware transport when P is actually known is a stronger PRACTICAL
control, outside the unknown-law theorem. More iid evaluations, larger pools,
binary-only factories and score-aware designs may also win complete efficiency.
A source-call optimum alone does not prove user-goal completion, useful neural
latency, semantic accuracy or academic novelty. Those obligations remain OPEN.
