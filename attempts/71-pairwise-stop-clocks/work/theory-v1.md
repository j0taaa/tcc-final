# V1 — Online stopping clocks with pairwise trajectory independence

Written BEFORE code/execution. Proofs below are WRITTEN, not Lean/software/
human-reviewed. The count law, moment inequalities, copula interpolation,
inverse-hazard representation and independence closure are classical tools.
Specific priority of the online batching specialization remains OPEN.

## 1. Operation and private-path factorization

Consider K>=3 requests and finite horizon H. Request i's per-step kernel
depends only on its own prompt/history and local step. At a live state it
stops with probability p_i; otherwise it samples from the conditional
nonterminal kernel and continues. Include a forced stop at H. Conditional
stop-token identity, if needed, is private. No kernel/budget/FP result depends
on other requests. Batch-sensitive arithmetic, MoE contention or adaptive
cross-request guidance is not silently covered.

Before stopping, expose an infinite/private sequence F_i of iid conditional
nonterminal random choices, independent across requests. Ignore stopping to
define a hypothetical nonterminal path, with hazards p_i(t;F_i). Null
conditional continuations after p=1 may be arbitrary. Define

    S_i(0)=1, S_i(t)=product_{s=1..t}(1-p_i(s;F_i)),
    A_i(t)=1-S_i(t),  S_i(H)=0.

For an independent Uniform[0,1) U_i, stop at the first t with U_i<A_i(t).
This is ordinary inverse cumulative-hazard sampling. Conditional on own
survival, U_i's residual interval is uniform, giving exactly p_i at the next
step. All conditional nonterminal and stop-token draws stay private. Thus
the complete output is a deterministic function G_i(F_i,U_i) with the native
single-request law. Future hazards/paths are NOT needed online: only update
the current cumulative survival product after the actual current head.

The iid baseline has independent U_i. We replace their JOINT law while
keeping all one- and two-coordinate uniform laws. This preserves each
complete trajectory law and **every pair's complete joint law**. Consequently,
for arbitrary individual square-integrable scores f_i and deterministic a_i,

    E sum a_i f_i = same as iid,
    Var(sum a_i f_i) = sum a_i^2 Var(f_i) = same as iid.

The same statement holds for covariance matrices of individual vector scores.
It does not cover a score using other trajectories, nonlinear batch metrics,
pass@K, group-relative baselines or the full mutually independent joint law.

## 2. Classical moment law and uniform-clock lift

Fix a deterministic cut 0<q<1, a=1-q. Let

    mu=Kq, m=1+(K-1)q, r=floor(m), theta=m-r.
    w_r=mu(1-theta)/r,
    w_{r+1}=mu theta/(r+1), w_0=1-w_r-w_{r+1}.

Zero weights are omitted. Draw N from this law; choose a uniformly random
N-subset J of the K request IDs. Given J, draw U_i independently uniform
on [a,1) if i in J, otherwise on [0,a). All randomness here is independent
of the private paths F_i. Cuts may depend on fixed prompts/metadata but NOT
on realized private paths or a selected favorable output.

This support {0,r,r+1} is the CLASSICAL Dawson--Sankoff extremal count law,
not a new probability factory. Nonnegativity follows also from size bias
below, comparing to a Binomial(K,q) feasible count. Its moments are

    EN=mu, E[N(N-1)]=K(K-1)q^2.

Uniform subset selection therefore gives P(i in J)=q and
P(i,j in J)=q^2. Conditional interval uniforms then give Uniform[0,1)
single clocks and INDEPENDENT uniform clock pairs. This is ordinary
Bernoulli/checkerboard-copula lifting. K-tuples need not be independent.

## 3. Simultaneously largest avoidance probabilities in the coarse class

For any exchangeable Bernoulli vector with the same one/two moments let N
be its number of ones and N* its size-biased count:

    P(N*=n)=n P(N=n)/mu,  n=1..K,
    E N*=1+(K-1)q=m.

For a fixed j-subset let g_j(n)=C(K-n,j)/C(K,j), using zero for out-of-range
binomials. The probability that the subset has no ones is

    alpha_j=E g_j(N)=1-mu E h_j(N*),
    h_j(n)=(1-g_j(n))/n.

h_0=0; h_1 is constant; h_2 is affine. For j>=3, h_j is DISCRETELY CONVEX
on positive integer n. A direct proof follows from the telescoping identity

    h_j(n)=(j/K)(1/n) sum_{s=0..n-1} b_s,
    b_s=C(K-1-s,j-1)/C(K-1,j-1),
    Delta^2 b_s=C(K-3-s,j-3)/C(K-1,j-1)>=0.

Taking initial averages preserves discrete convexity: write a convex sequence
as an affine sequence plus nonnegative hinges (s-k-1)_+. Their initial
averages are (n-k-2)_+(n-k-1)_+/(2n), themselves discretely convex. This
proves the assertion without a continuous derivative extension.

Discrete Jensen says every integer-valued N* with mean m has E h_j(N*) at
least the interpolation (1-theta)h_j(r)+theta h_j(r+1). The declared count
law attains equality for ALL j simultaneously. Thus it maximizes alpha_j
for every subset size in this EXCHANGEABLE coarse Bernoulli class. In
particular alpha_j >= (1-q)^j from the feasible independent Binomial law.
For j=K, h_K(n)=1/n; the same comparison gives
mu[(1-theta)/r+theta/(r+1)]<=P(Binomial(K,q)>0)<=1, proving w_0>=0.

This is a moment/convexity argument, not a claim that a classical count bound
or Jensen's inequality was discovered here. Ramachandra--Natarajan's
symmetry/moment-LP results are direct antecedents. General nonexchangeable
coarse laws, different cuts or all possible uniform copulas are NOT covered
by this class-specific maximality assertion.

## 4. Lower-orthant dominance and batch rounds

Let C_q(u)=P(U_i<u_i for all i), and Pi(u)=product_i u_i. Clock CDFs are
multiaffine on each cell cut at a=1-q. At a vertex whose coordinates are
a or1, their values are alpha_j and a^j respectively; at a zero coordinate
both vanish. Multiaffine interpolation uses nonnegative weights. Therefore

    C_q(u)>=Pi(u) for ALL u in [0,1]^K.

The simultaneous alpha_j maximality also maximizes this CDF within the fixed-
cut exchangeable conditional-uniform coarse class. It is NOT optimal among
all pairwise independent copulas, nor compared to methods given future paths.

Condition on the ENTIRE independent private paths F. The all-finished event
at t is U_i<A_i(t;F_i) for all i. Hence

    P(M<=t |F)=C_q(A_1(t),...,A_K(t))
             >= product_i A_i(t)=P(M_iid<=t |F).

Integrating F proves stochastic dominance of maximum rounds M and EM<=EM_iid,
while the complete single/pair output laws and mean/variance above are
unchanged. The algorithm is ONLINE despite conditioning on full paths in
the proof: those paths are only an analysis device, never a lookup table.

For fixed-shape model cost sum_t c_t 1{M>t}, c_t>=0 fixed, expected model
cost is no greater. More generally the same holds for

    sum_t [a_t 1{M>t} + sum_i b_it 1{L_i>t}], a_t,b_it>=0,

since active-row terms have unchanged marginals. Prefill/setup are common.
This includes ideal affine compaction with a per-round overhead, not every
GPU kernel's nonlinear cost. Sampling/precision/communication overhead is
ADDITIONAL, and must be measured. Continuous refill of a large request queue
can erase the relevant tail cost. No total-wall-time theorem is inferred.

## 5. Quantitative positive family and sharp limited case

For r an integer in[2,K-1], take q=(r-1)/(K-1). Then N is0 or r and

    P(N=r)=K(r-1)/(r(K-1)).

In the constructed process stopping at1 with probability1-q and otherwise
atH, each individual and each pair has the SAME law as iid. The batch
completion expectations are

    EM_iid=1+(H-1)[1-(1-q)^K],
    EM_q=1+(H-1)K(r-1)/(r(K-1)).

For fixed r and K,H growing, their ratio tends

    ((r-1)/r)/(1-exp(-(r-1))).

r=3 gives about.771, a constant round saving while all mean-score variances
stay identical. This is a CONSTRUCTED capacity example, not a neural timing
or a selected benchmark. Many real processes may have almost no saving.

For r=2,q=1/(K-1), and ANY heterogeneous survival probabilities S_i(t)<=q,
there are at most two alive root-tail clocks. Pairwise independence yields

    P(M>t|F)=sum_i S_i - sum_{i<j} S_i S_j.

Classical second-order Bonferroni makes this minimal among ALL pairwise
independent lifetimes with these survival marginals at this time. Do NOT
claim Bonferroni, its tightness construction or this moment bound as new.

## 6. Required adverse limits

Full iid joint laws are changed. If a use requires iid K-tuples rather than
individual/pairwise laws, it is outside the contract. Pairwise independence
does not preserve pass@K, order statistics, nonlinear reward baselines or an
entire training trajectory. Model/eval randomness may not interact across rows.

Arbitrary concave compaction cost is not dominated: K=3,q=1/2 has N=0 or2
with probabilities1/4,3/4. E[min(N,2)]=3/2, versus11/8 for iid Bernoulli
halves. The candidate can therefore LOSE against a sufficiently different
cost geometry. This must remain in the oracles and any later study.

All-one shared clocks have stronger completion coupling but lose pairwise
independence and can inflate average-score variance by K. Affine finite-field
pairwise clocks are legitimate same-contract controls and may win at some
particular thresholds even though they lack our universal iid-CDF guarantee.
Classical Dawson--Sankoff lifting is exactly our core, not an inferior control.

## 7. Bits, source and next gate

Exact rational hazards of B-bit description yield survival products of
O(HB) bits. A common fixed-precision residual clock can drift; neither that
nor native CUDA aliases are covered by the mathematical ideal. A future
implementation must declare a finite categorical kernel, preserve its law,
and account for root bits, threshold comparison/refinement/fallback and
conditional nonterminal sampling. No model forward is intrinsically needed
to coordinate an already computed head, but real overhead is not zero.

The selected next operation is ONLY the bounded exact-rational audit in
protocol-v1.md. Actual neural stopping variability, complete cost, strongest
engine controls and sufficient own priority remain OPEN.
