# V2 — Proper first-EOS-length-conditioned action control, BEFORE prototype

2026-10-16. Six small V1 rational oracles pass. No A54 real score statistic,
new auxiliary, head or timing. README's eight criteria remain; this refinement
strengthens the control before considering an OLD-data opportunity diagnostic.

A52's methods named length_integrated/combined_partial are useful unbiased
coordinate controls, but their mixed conditioning is NOT automatically the
score of a joint probability law usable in a maximal-coupling ratio. Add a
proper control that shares the proposal's first-EOS length T, whose marginal
is policy-independent. Couple actions maximally conditional on that T.

For fixed old state s and action B with retained original IDs, use the SAME
q_B word factors as A52 and define Q_T by restricting the EOS arc to T-1,
retaining1/H_T on it. No early EOS or truncation of fixed/retained IDs. Then

    K_theta(T,B|s)=S_ret(theta)*Q_T(theta)/Z_s,
    S_ret=sum_{i in B} u_i/g_i(x_i).

At u_i=1 the score has retained alpha_i=(1-rho_i)(1-g_i(x_i)),
unretained alpha_i=-E[g_i(X_i)|s,B,T], beta the analogous log-confidence
weighted sum, and anchor_i=rho_i-pi_i(T). Fixed/post-EOS positions contribute
zero. This is an ordinary conditioned weighted-DAG query, not new theory.
Marginalizing T gives the observed score and mass. Whenever EOS is already
fixed, this control has EXACTLY the same ideal score as the candidate.

The first task is only a small independent rational enumeration of K(T,B)
and its score, plus a counterexample to identifying the older mixed-coordinate
control with this joint density. An isolated FP64 implementation must pass
that oracle before any real old head/query. Its numerical approximation is
NOT a native finite-RNG or exact-acceptance certificate.

A later OLD-data screen must include this proper length control together
with joint full/anchor-integrated/class/known-anchor controls. All scores
use the SAME original actor9 at theta0. Merely beating independent noise or
word-conditioned coupling is insufficient. The generic observed-action
query/coupling itself is classical and gives the same candidate rule.

Any infinitesimal screen is only about local split/shared-work loss, not
20% total latency or rank-estimation accuracy. A positive screen cannot
trigger neural work without a correct exact numerical law, finite-policy
sampler, full strong-control cost design and originality reassessment.
