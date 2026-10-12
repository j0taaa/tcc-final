# V27 candidate application: two-sided fidelity decisions, not a relabeled V25 win

Written AFTER V25's complete0/36 failure and while the frozen V26 development
replay runs. No measured program is changed. This is a proposed application of
the quantitative theorem, not a new theorem of coupling or a successful gate.

## Operation and mathematical contract

A library developer auditing original-token grammar-conditioned sampling has
two stored probability tables from the same dLLM step and a fidelity budget
tau. The question is whether the resulting laws differ by at most tau, not
whether either produces syntactically valid JSON. Validity alone is unchanged.
The two normalizers must be positive; support/canvas/grammar are shared.

Return ACCEPT if U<=tau, REJECT if L>tau, otherwise UNRESOLVED. For the
deterministic near-relative interval L<=TV<=U<=(1+epsilon)L, both decisions
are sound for EVERY admitted input. Moreover:

- TV<=tau/(1+epsilon) necessarily leads to ACCEPT;
- TV>(1+epsilon)*tau necessarily leads to REJECT.

Proof: U<=(1+epsilon)L<=(1+epsilon)TV for the first implication, and
L>=TV/(1+epsilon) for the second. The asymmetric strictness respects the
budget's <= convention. TV=0 is accepted for tau=0; positive TV is rejected
for tau=0. Undefined distributions/resource refusals stay UNRESOLVED.

Choosing ACCEPT is a valid ingredient of the already written common-policy
trajectory budget. Choosing REJECT prevents claiming a table substitution
meets its budget when it demonstrably does not. The decision rule and coupling
application are classical; the candidate scientific advance remains the
lower precision exponent of the deterministic quantitative algorithm.

## Eight questions before any implementation or new observations

1. **Use:** deterministic fidelity auditing for a CFG-constrained dLLM
   sampler; the software consumes ACCEPT/REJECT/UNRESOLVED. This does not
   avoid the two forwards or prove the neural model is accurately quantized.
2. **Significance:** the decision corollary itself is elementary, NOT a new
   contribution. The potential article centers the quantitative integer
   TV algorithm and its complete cost theorem, compared with Feng/Fu. A new
   application cannot rescue an equivalent-to-prior algorithm.
3. **Choice:** a near-relative guarantee bounds both overconservative admission
   and false claims of fidelity. Existing cheap bounds may already decide the
   requested budget faster. Include their strongest available LOWER bounds,
   not only the eight upper controls that were measured in V25. Exact small
   enumeration and competent randomized relative inference remain alternatives.
4. **Proof:** the decision implication above holds without experiments for
   all tau and all admitted inputs. It is not a comparative runtime theorem.
   The product quantitative bound remains O(nq sqrt(n/epsilon) log(q+2)),
   plus complete input/scaling/normalizer and integer bit costs. CFG source
   admission must retain its stated hypotheses and preparation cost.
5. **Honest validation:** do NOT choose a budget between a candidate and a
   competing bound after seeing them. A future audit must report complete
   competing intervals and their decided/undecided budget regions for ALL
   inputs, so no favorable threshold is needed. Existing heads are DEVELOPMENT.
   There is currently no new independent confirmation or utility gate.
6. **Costs:** lower-control preparation, both normalizers, any inside/outside
   marginal computation, core evaluation and bit arithmetic must be paid.
   The value of a stricter decision is distinct from cheaper full generation.
7. **Objection:** strong marginal/moment/coarsening lower bounds or an exact
   shortcut might already decide everything of practical interest; a relative
   guarantee may be too expensive. Constant-factor product-TV proxies are
   relevant for an application that tolerates their gap. No universal speed,
   sole capability or publication sufficiency follows from this corollary.
8. **Article:** need competent two-sided controls and an actual software need
   for the claimed decision precision. Preserve V25's failed2x-upper gate and
   V26's development status. Human proof review, exhaustive priority and
   acceptance remain absent; this note is not evidence of them.

## Current disposition

The mathematical cost distinction deserves continued proof/prior review.
The decision application is only a candidate. Do not start another extensive
model campaign or call it a confirmed conquest on this note. First specify
and validate minimal classical two-sided controls, or reject this application
if those show the expensive near-relative computation is unnecessary.

## Minimal classical lower-control proof before code

Use the already computed original-ID posterior marginals: by data processing,
each marginal TV is at most joint TV. Retain their maximum, not a selected
position. Retain the exact support-loss lower bound too.

For integer atoms x,y, S=2^64 and delta=1/S, a nonzero floor(S sqrt(xy))
is at least (1-delta)S sqrt(xy). Positive inside evaluation therefore gives
an affinity squared upper from its downward approximation divided by
(1-delta)^(2n). A rational ceiling square root yields an affinity upper;
max(0,1-affinity_upper) is a sound Hellinger-based lower bound on TV.

For each common-support chi direction use the already proved ideal-control
lower enclosure v<=sqrt(chi)/2. Bound the normalized likelihood ratio R
using the product of ALL per-position minima/maxima, including choices that
the grammar might disallow. These looser extrema still enclose every valid
R and avoid pretending a new parser call is free. If D>=max|R-1|, then
chi=E(R-1)^2<=D*E|R-1|=2D*TV, so 2v^2/D is a conditional TV lower bound.
The reverse direction uses the reciprocal extrema. Handle D=0 as identical
conditional laws, rather than division by zero.

Let a,b be the two common-support masses and Lc a conditional lower bound.
On the common set, the triangle inequality gives
TV(P,Q)>=min(a,b)*Lc+min(1-a,1-b). Take this with the exact support-loss lower
and the other lower controls. The existing mass-aware/overlap upper controls
remain. Undefined mass refuses; no approximation changes the model's support.

These are known inequalities and can strengthen the comparison, not new
scientific claims. Before any application, repeat ALL105 original word cases
including zeros/aliases, using independent enumeration to check each interval.
Do not run a timing comparison until every lower bound is sound. Existing
full heads remain development and V25's0/36 result remains frozen.
