# Universal noising covariance order — definitions and comparative corollary

2026-10-11. WRITTEN before code/measurement. The matrix lift is elementary
linear algebra, NOT a new standalone theorem claimed here. A39 source-query
frontier remains a candidate whose literature priority is unresolved.

## Original operation

Fix a CFG-valid target x (or two targets scored with common random numbers).
An original dLLM noising policy consumes a uniform known finite source s in[M],
M>=4, to obtain its time, masks and other original randomness. It need not have
a known cheap inverse for the canonical class. Let L_theta(s) be the original
finite stochastic score/loss and G_theta(s) its original gradient, if defined.
Loss, gradient and complete random tape belong to the SAME original policy;
no new corrupted token distribution or silently omitted mask outcomes.

A cheap key k_theta(s) can read noising/CFG field-role data and a detached
proxy fixed BEFORE the queried sources. It must not run the expensive current
model score/gradient. All proxy/preparation costs are charged. Model-free
corruption is queried3/4 times using the A39 C4 finite-source kernel; only
the two retained original corruption states are evaluated by the dLLM.
Unknown class probabilities are not estimated/plugged in as if exact.

q(s)=1/M is independent of theta. If an importance proposal was fitted from
PAST data, fix it during this update and include its ORIGINAL importance
weight inside L,G. If q currently depends on theta, an appropriate original
score-function/total-gradient definition is needed; do not reuse this simple
claim without it. Different loss functions/new masking eligibility are
different operations. For ideal continuous noise this finite-source theorem
is NOT automatically an exact integral theorem or a zero-discretization bound.

## Exact full-gradient geometry

Let n_i be key-class sizes, D=(M)_4, S2=sum n_i^2,
mu=E G, mu_i=E(G|class i), g_i=mu_i-mu,
Sigma_i=Cov(G|class i) and h=sum n_i^2*g_i.
The A39 class law has J_ii=(n_i)_3*(2M-n_i-3)/D. Its full-source
cross-covariance matrix for the two retained gradients is

 C = {-(M^2-S2)*sum n_i^2*g_i*g_i^T - h*h^T
        +(4M-6)*sum n_i*g_i*g_i^T}/D
       -sum_(n_i>=2) J_ii*Sigma_i/(n_i-1).                 (1)

The within-class term is WITHOUT replacement, not independent lifting.
Equation(1) follows by the original source-pair law and expanding centered
outer products. Symmetry of that law makes C symmetric. For every vector v,

 v^T*C*v = Cov(v^T G(X),v^T G(Y)) <=0                    (2)

by A39's scalar theorem. Thus C is negative semidefinite. The gradient
mean is unbiased and, with Sigma=Cov(G(s)),

 Cov((G(X)+G(Y))/2)=(Sigma+C)/2 <=_Loewner Sigma/2.       (3)

This dominates two iid evaluations of the SAME original noising operation
in EVERY linear direction, not only loss variance or one chosen norm. The
same applies to L, a likelihood-bound estimate, a paired score difference,
or any deterministic full-result statistic. No mask-to-loss monotonicity
assumption, teacher accuracy or gradient-sign condition is needed.

For a classifier depending on theta but fixed before source queries, (1)--(3)
are pointwise at that theta. Sampling/selection is STOP-GRADIENT: evaluate
the ordinary original gradients at the two retained states. Their marginal
source law is q for every theta, so the average expectation is E_q G_theta;
there is no extra derivative of the pair rule. Differentiating through hard
selection, reusing current score observations to redefine k, or theta-dependent
q without its required gradient term is a different, unsupported estimator.

## Comparative consequence for a fixed preconditioner and one quadratic update

For any deterministic matrix A chosen from the PAST (including identity or
a fixed past preconditioner), equation(3) implies A Cov(mean) A^T is no
larger than the iid2 counterpart in Loewner order. In particular expected
squared estimation error for ANY positive-semidefinite weight W is no larger,
since its difference is trace(W*(-C)/2)>=0.

For any quadratic objective F with Hessian H>=0, fixed current point theta
and step size eta, use the unbiased mean gradient estimator gbar. Exactly

 E F(theta-eta*A*gbar)
   =F(theta-eta*A*mu)+(eta^2/2)*trace(H*A*Cov(gbar)*A^T).

Therefore this ONE expected quadratic update is never worse than matching
iid2. This is a comparative mathematical benefit, not a claim that a real
neural objective is quadratic or that all AdamW trajectories improve.
A current-gradient-dependent nonlinear preconditioner is outside this result.

For general smooth neural objectives one may obtain the conventional
variance-dependent descent upper bound; a smaller upper bound is NOT proof
of better actual expected objective, faster whole training or semantic output.

## Matching comparators and complete costs

Exactly TWO current neural score/gradient evaluations are required. Corruption,
key and uniform-distinct-source arithmetic are cheap candidates to measure,
not zero-time assumptions. Include all forward/backward, grammar parsing,
proxy calls, tensor/RNG copies, class calculation and parameter output costs.
Source bit width is log2 M; drawing at most4 distinct sources and lifting
excluded ranks is polynomial in that width and original noising preparation.
Do not enumerate the source space or claim a class-count computation is needed.

Uniform source derangement uses2 evaluations and has C=-Sigma/(M-1).
It is a strong mandatory control and can beat C4 for some gradient directions.
MIRROR, timestep stratification, learned importance proposals and analytic
class samplers may also win in their regimes. The universal comparison(3) is
with iid2, NOT all those methods. A39 opaque-query lower bounds apply only
if their source/information/hard-cap hypotheses actually hold in the application.

Same-example repeated evaluations eliminate only conditional NOISE variance.
If both outputs share x, full covariance includes variation of E(G|x).
Compared to TWO independently selected examples, that positive data covariance
can exceed the negative noise covariance. Never claim(3) proves unconditional
training superiority under repeated-data batching. The matching scorer uses a
FIXED candidate; any full training study must include different-data controls.

## CFG application and closest-prior obligations

A grammar-produced JSON/DSL candidate is scored without changing its tokens
or normalizing only a favourable support. Parsed field/operator/leaf roles
may supply a cheap proxy class for mask difficulty. The guarantee holds for
EVERY admitted target and current model even if this proxy is wrong; strict
useful magnitude requires correlation with actual score/gradient geometry.
Original source masses, easy analytic class conditioning, nonuniform proposals
and ordinary timestep/mask antithetics must not be made unavailable to controls.

MIRROR/P-POTS already address masked-diffusion loss/noising variance. Ren2019
and categorical antithetics already provide probability-preserving couplings.
To qualify as a contribution, specify what the exact query frontier adds,
show nonnegligible useful covariance/cost and verify the closest reductions.
No code/model output, claimed publication priority or article promotion here.
