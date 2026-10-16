# V3 — An auxiliary anchor, integrated from the observed action

2026-10-16. Written BEFORE V3 code/model/timings. A different law from V1/V2.
It is motivated by V2's changed word marginal and augmented normalizer, not a
retrospective change to V2 results. Forcing one Bernoulli unit, mixture sums,
weighted evidence, conditional scores and Rao–Blackwellization are CLASSICAL.
No invention of those principles or publication priority is claimed. The
specific useful grammar/selection application still requires prior/consumer
and complete-cost evidence; only a minimal rational oracle is justified.

## 1. Sampling contract

Use V1's original-ID word posterior P(x)=W(x)/Z on an unambiguous bounded
grammar L, sufficient current state and nonempty active positions M. Choose
anchor probabilities pi_i>0, sum_i pi_i=1, from the current state/model head
BEFORE the complete proposal; they cannot depend on unobserved X. Independently
draw A~pi and X~P. Force B_A=1. For i!=A draw B_i independently with probability
g[i,X_i] in(0,1). Expose the nonempty action a=(B,X_B), discard X_(M\B) AND A.
Future state/control/randomness must not remember them. Fixed IDs/EOT/PAD and
original aliases retain V1's explicit semantics.

The complete proposal X has EXACTLY P, since the subsequent conditional
anchor/mask kernel sums to1 for every X. No rejection/OR normalizer is needed.
The exposed transition, later trajectory and final-word distribution are NOT
Mosaic's and need not equal V2 or a different schedule. Progress is certain:
each action exposes at least one previously masked position; at most the
initial masked count of forwards completes a bounded canvas, assuming the
model/grammar queries succeed. Numerical/resource failures are not erased.

## 2. Collapsed likelihood with one ordinary evidence query

For observed a=(B,t_B), let Z_a be V2's ordinary filtered grammar partition:
retained rows w*g fixed to their original IDs; unretained active rows w*(1-g);
fixed inactive rows unchanged. Define the RETAINED-ONLY scalar

    S_a = sum_(j in B) pi_j/g[j,t_j].

THEOREM. The exact observed action mass is

    p(a) = (Z_a/Z)*S_a.

Proof. For a known anchor j in B, the full pair probability is

    P(x)*pi_j*product_(i!=j) g[i,x_i]^b_i*(1-g[i,x_i])^(1-b_i).

Factor the Bernoulli product over ALL i and pi_j/g[j,t_j]. Because j is
retained, that ratio depends only on observed IDs. Sum over j in B, then
over hidden X, producing S_a*Z_a/Z. All terms are nonnegative. Nonempty
compatible actions exhaust probability1. The posterior of A given a is

    rho_i = (pi_i/g[i,t_i])/S_a for i in B, otherwise0.

Conditional on a, A and the hidden original IDs are independent: their joint
weight factors into the retained scalar and the same unary-filtered grammar
posterior. This is an elementary finite-mixture identity, not new Bayes theory.

## 3. Full scores and two levels of collapse

Let mu[i,v]=Pr_P(X_i=v), nu[i,v]=Pr(X_i=v | a), and use independent log-weight
coordinates l, gate log-odds h and anchor softmax logits r. Differentiation gives

    d_l log p(a) = nu[i,v]-mu[i,v],
    d_h log p(a) = nu[i,v]*(1-rho_i)*(1[i in B]-g[i,v]),
    d_r_i log p(a) = rho_i-pi_i.

For i not retained rho_i=0; for a retained i, nu is its observed original-ID
singleton. The full (X,A,B) score has weight component1[X_i=v]-mu[i,v], gate
component1[X_i=v]*1[A!=i]*(b_i-g[i,v]), and anchor component1[A=i]-pi_i.
Taking its conditional mean given a yields exactly the displayed formula.
Keeping A but integrating hidden X is another valid, intermediate control;
integrating A as well cannot increase covariance for action-measurable returns.

All shared neural parameters require their actual chain rule. In particular,
if h[i,v]=alpha_i+beta*log c[i,v] with c a row softmax of log weights, the
additional adjoint to l[i,v] is

    beta*(gate_score[i,v]-c[i,v]*sum_u gate_score[i,u]).

Anchor parameters depending on the same head add their chain term too. Merely
detaching c while updating its producer is not this gradient. For positive
smooth weights/gates/anchor logits, compatible observed-action support is
fixed and the kernel is differentiable; there are no extra hard rank/threshold
boundaries. Ordinary nonsmooth neural features retain their own limitations.

For a Markov continuation using only observed actions and fresh randomness,
the full observed-PATH score is the sum of these scores, and is the conditional
mean of the full auxiliary-path score. Classical total covariance proves no
greater covariance for terminal-return gradient estimators. This is NOT a
formula for marginal final-text likelihood, nor equality of latent/observed
clipped PPO objectives. Standard iid RLOO groups and state-only baselines are
allowed; correlations between different trajectories can invalidate the usual
RLOO independence argument and are not silently imported from earlier attempts.

## 4. Expected release count, not a full-runtime guarantee

Independence of anchor and complete word gives

    E|B|=1+sum_i (1-pi_i)*E_P[g[i,X_i]].

For fixed P/pi and g[i,v;lambda]=sigmoid(s[i,v]-lambda), this is continuous
strictly decreasing from |M| to1 when |M|>=2. Hence each target expected batch
size in(1,|M|) has a unique lambda. Once base token marginals are available,
evaluating this scalar function requires original-ID sums, not repeated grammar
partitions. A numerical calibration needs its own tolerance, cost and implicit
gradient if differentiated. This theorem does not equate a mean count to fixed
top-k, ceil(n/k) forwards, or equal whole-trajectory latency across policies.

## 5. Strong controls and eight criteria

1. Use: an explicitly new grammar-conditioned dLLM release policy whose
   observed transitions can be optimized without hidden-proposal/anchor noise.
   It preserves the CURRENT complete proposal law while guaranteeing progress.
2. Difference: the retained-only anchor normalizer makes exact marginal scores
   tractable with ordinary grammar evidence and no V2 OR normalization. Generic
   anchor-forcing/Bernoulli planning/token dependence/conditional expectation
   are antecedents. A useful own systems/consequence and sufficient originality
   remain OPEN; this direct composition may be too small for an article.
3. Choice: exact scores need no auxiliary resampling or new neural forward,
   and have no greater covariance than the same-policy full estimator. This
   says nothing yet about total cost, semantic accuracy or competent alternatives.
4. Proof: original proposal marginal, observed mass, integrated anchor score,
   chain rule, finite Markov path covariance and expected count are written.
   V1/V2 counterexamples/measurements cannot be relabeled as V3 evidence.
5. Validation: independently enumerate all triples/actions, verify original
   word marginals, intermediate/full/collapsed scores and adaptive paths. Then
   reassess prior/consumer/resource feasibility BEFORE any neural protocol.
6. Cost: original model outputs/backward, base and filtered inside/outside,
   original-V gate/anchor construction, ALL full proposals, RNG, memory, fresh
   state compilation/reweighting and output. Finite arithmetic must handle small
   gates/S_a stably. Preserving a mathematical word marginal is not a GPU-law proof.
7. Objections: ordinary mixture/evidence inference implements the same method.
   Fixed anchors or position-only Bernoulli gates may be cheaper/better; retain
   the exact position-only/fixed-anchor controls, analytic enumeration/component
   elimination, optimized state baselines and multiple conditional samples
   sharing one neural adjoint. dUltra/MD4/MAPG/Fork-dLLM are behavioral controls
   under their own contracts. No synthetic toy reward can establish real usefulness.
8. Article: primary distinction, significant complete-cost gradient benefit on
   external states, actual updates/useful neural results and independent
   confirmation remain. Only the minimal oracle is justified now; no model,
   training/timing campaign, publication or achieved goal is asserted.
