# Terminal forecast aggregation: written native-kernel contract and risk proof

2026-10-17. BEFORE code/execution. All eight README criteria apply. This is a
known conditional-averaging argument specialized to an audited real consumer;
it is not a claim of new MBR/Jensen/probability theory or a measured own benefit.

## 1. The source to average, not an assumed head posterior

Run the ORIGINAL decoder to completion. At a converged commit let H contain
the entire fixed task/history/control, accepted prefix, pins, offsets, matcher
node/budget, actual sampler inputs and log_probs. The last native commit is a
random draw Z0 from its real terminal-transition kernel R_H. This may be a
finite floating/RNG law; the theorem only assumes repeatable iid draws of the
SAME kernel. It does not require knowing any event probability or token mass.

Let C_H(z) mean that committing that candidate completes the whole forecast
with the required labels and finite nonnegative values. Define its semantic
point F_H(z) by dividing the values by their sum. At zero sum, use one fixed
uniform fallback in BOTH baseline and readout, explicitly a changed normalized
baseline policy. Original malformed/resource-failure outcomes without this
typed contract are left unchanged, not silently discarded or called valid.

Only when the original run reaches a completing typed transition C_H(Z0)=1
do we change its numerical readout. Earlier states, other outputs/failures,
original raw text and all backbone calls stay literal. Native converged canvases
which do not finish the response still take their original continuation. A
proposal's apparent last-token location is not enough to decide completion.

Afterwards draw N independent auxiliaries Z1..ZN from the SAME R_H, without
advancing/rewriting H or performing a backbone call. Let I={i:C_H(Zi)=1},
M=|I|, and emit

    A_N = [F_H(Z0)+sum_(i in I)F_H(Zi)]/(1+M).          (1)

All N helpers, including rejected/nonterminal ones, count. If M=0 the point
is the original normalized forecast exactly. No auxiliary continuation or
unbounded rejection is hidden. This is a readout, not an original-word sampler.

## 2. Exact finite-budget conditional risk identity

For a reached H and its original completing event let

    alpha=P_RH(C_H=1)>0,
    mu=E[F_H(Z)|C_H(Z)=1],
    Sigma=Cov(F_H(Z)|C_H(Z)=1), V=trace(Sigma).

The success indicators of iid auxiliaries are independent Bernoulli(alpha).
Conditional on the indicators, all retained points are independent draws
of the same conditional law, including original Z0: auxiliary randomness is
independent of that original draw given H. Hence

    E[A_N|H,C0]=mu,
    Cov(A_N|H,C0)=Sigma * r_N(alpha),
    r_N(alpha)=E[1/(1+M)]
      =[1-(1-alpha)^(N+1)]/[(N+1)*alpha].              (2)

To check the closed form, expand the binomial law and use
binom(N,m)/(m+1)=binom(N+1,m+1)/(N+1). There is no alpha=0 division on a
positive-probability completing event. In the irrelevant limit alpha->0,
r_N tends to1. For alpha=1, r_N=1/(N+1).

For EVERY fixed gold vector g in the simplex, regardless of model calibration,

    E||F_H(Z0)-g||²-E||A_N-g||²
        = V * [1-r_N(alpha)] >=0.                    (3)

This follows by decomposing both risks into ||mu-g||² plus covariance trace.
It is strict for N>0,alpha>0,V>0. A bad model mean is NOT corrected: only
within-this-terminal-state variance is removed. Between-history variance and
reasoning errors remain. No pass@1/top-choice accuracy/ECE bound follows.

For any convex loss ell(a,g), Jensen conditional on all retained points gives
E ell(A_N,g)<=E ell(F_H(Z0),g): all points have the same conditional marginal.
In particular this covers numerical TV distance to any gold probability
vector. It does not prove improvement for a nonconvex aggregate metric.

## 3. Whole original trajectory and finite failures

The original trajectory is executed first, unchanged, and only its eligible
absorbing numerical output is replaced. Decompose by the last pre-absorption
history H and the completing event. Equation(3) holds in EVERY stratum; all
ineligible/failure strata keep the old output and loss. Averaging proves the
same non-deterioration relative to the specified NORMALIZED native baseline
for the complete bounded decoder. Expected squared-risk reduction is the
original occupation-weighted expectation of V(H)[1-r_N(alpha(H))].

This argument would be invalid if auxiliaries were drawn from a new forward,
another history or unconditional raw mean-field logits substituted for the
audited marginal-reprojection kernel. Ordinary finite-RNG pseudorandom code
needs its own replay audit; independence is a theorem hypothesis, not inferred
from a tensor's shape or a code comment. Floating ideal-weight integration
requires an explicit error comparison to the native kernel if used instead.

## 4. Cost and semantic rendering

No additional original backbone forward is required by(1). Extra work is N
frozen sampler calls, capture/copies/storage, prefix reconstruction, complete
parsing, normalization and output arithmetic. Holding dense source tensors
can be costly. Full-trace ensembles average other histories too and remain
strong controls. Cached exact sum-state moment DP may be cheaper here because
all native numbers are multiples of1/100; its weighted source/annotation must
still match the native edge-argmax path law and terminal conditioning.

The arithmetic mean is in the simplex but can require more than two decimals.
The REAL JevBench consumer accepts ordinary JSON numbers; the internal native
x-prob spelling restriction is not an immutable output contract for this new
readout. Preserve the raw native response separately; never claim original
ID/word/support preservation for the reserialized numerical vector.

For explicit finite output choose Q=10^d, round down Q*A_i and distribute the
remaining integer units to largest fractional remainders, deterministic ties.
The output B is nonnegative, sums EXACTLY to1 in decimal, and |B_i-A_i|<1/Q.
Thus ||B-A||1<=K/Q and for g in the simplex

    | ||B-g||²-||A-g||² |<=2K/Q,
    | TV(B,g)-TV(A,g) |<=K/(2Q).                     (4)

These are classical rounding/error bounds. The guarantee is reduced by these
terms, not declared exact after finite rendering. Binary64 parsing/summation
adds its own arithmetic error; no native bitwise equality is asserted.

## 5. Why no large campaign follows from this proof

All identities are classical and compatible with NEGLIGIBLE V(H). The actual
terminal variance may be tiny after convergence, helper costs may exceed any
gain, and a direct classical moment control may solve the entire operation.
The initial validation must check conditioning and this actual source boundary,
not just show that means have smaller variance in a favorable toy. Need a
separate prospective native/resource/necessity protocol before any new model
head, semantic observation or timing, including zero-variance/unfavorable cases.
Own priority, useful magnitude, whole-consumer validation and publication
sufficiency remain OPEN. This is not a guarantee of a successful experiment.
