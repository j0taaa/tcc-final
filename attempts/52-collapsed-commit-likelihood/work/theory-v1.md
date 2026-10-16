# V1 — A confidence-selected action as unary grammar evidence

Written 2026-10-16 BEFORE prototype. Weighted counting, conditional-score
identities and Rao–Blackwellization below are classical. The proposed scientific
distinction is their useful application to the precise observed transition,
which remains unconfirmed. This note does not prove worldwide priority.

## 1. Law, observation and cost object

Fix a current canvas, active positions M, an unambiguous bounded original-ID
language L, and nonnegative finite rational weights w[i,v]. Fixed positions
retain their original ID; special IDs/EOT/PAD belong to L, not a surrogate.
Let W(x)=product_i w[i,x_i], Z=sum_(x in L) W(x)>0 and P(x)=W(x)/Z.
Original aliases are distinct outcomes even when bytes coincide. A deterministic
layered graph or unambiguous grammar circuit computes this sum WITHOUT counting
one original word multiple times. Input lengths and circuit sizes are charged.

Each active position has a deterministic pointwise confidence c[i,v]. It can
be the original model probability, a constrained marginal computed from this
same head, or an explicitly separate frozen readout. No independence of X_i
under P is assumed. Draw X~P, choose B according to one rule below, expose X_B
and discard X_(M\B). Observe the complete action a=(B,t_B), not just t_B.
The next state, EOS handling and all future control MUST use only this action,
the previous sufficient state, and fresh independent randomness. Retaining
hidden proposals in a cache would invalidate the claimed collapse.

Tie priority is smaller physical index first. Define key(i,v)=(c[i,v],-i)
with lexicographic comparison, so different positions have a strict ordering
even at equal confidence. This matches first-index argmax. A GPU top-k kernel
with a different/unspecified tie convention needs its own contract.

## 2. Threshold with most-confident fallback

For a fixed tau, choose B={i in M:c[i,X_i]>tau} when that set is nonempty;
otherwise retain only the position maximizing key(i,X_i). Let B be nonempty.

If all observed c[i,t_i]>tau, for i in B, define filters:

    D_i={t_i}                 for i in B,
    D_j={v:c[j,v]<=tau}       for j in M\B.

If B={b} and c[b,t_b]<=tau, instead define:

    D_b={t_b},
    D_j={v:key(j,v)<key(b,t_b)} for j in M\{b}.

All other actions (including mixed high/low retained IDs) have zero mass.
Fixed positions keep their original singleton domains.

THEOREM 1. In either admissible case, T(x)=a iff x_i is in D_i at every
position. Consequently Pr(T(X)=a)=Z_D/Z, where Z_D is the ordinary partition
after replacing w[i,v] by w[i,v] times 1[v in D_i].

Proof. In the high case the retained positions and only those positions cross
the STRICT threshold. In the low singleton case all other keys rank below the
observed winner, hence all other scores are <=c[b,t_b]<=tau: the fallback is
indeed entered and has exactly that winner. Conversely either selected action
forces those inequalities. The cases are disjoint and exhaust positive-mass
actions. Summing the original product weights on this preimage proves the law.
Equality at tau belongs to the fallback/low side; equality of scores is decided
by physical index, not token alias merging.

## 3. Top-k by sampled confidence

Fix 1<=k<=|M| before seeing X. For |B|=k, all retained IDs known, define
rho=min_(i in B) key(i,t_i). Retained filters are singletons; unretained filters
are D_j={v:key(j,v)<rho}. The same equivalence and partition ratio hold: the
known weakest retained key separates the two sets. If an ordered action rather
than a canvas is consumed, verify that its retained order agrees with known
keys. A random/PL ordering is a DIFFERENT law and is not covered by this proof.

## 4. Scores: local regularity is essential

Suppose positive weights are differentiable in theta, support and graph are
fixed, and the deterministic map T_theta(x) is constant for EVERY supported
x throughout a neighborhood of theta0. This is a local stable-comparison-cell
hypothesis, not an assertion that neural confidence ranks never change. Ties
are allowed only if the actual relevant comparison outcomes remain stable.
For a positive observed action, finite differentiation gives

    d log Pr_theta(a) = E[d log W_theta(X) | T(X)=a]
                       - E[d log W_theta(X)].

For independent log-weight coordinates l[i,v]=log w[i,v], the adjoint is

    g[i,v] = Pr(X_i=v | a) - Pr(X_i=v).

Proof. The fixed preimage has partition Z_D; differentiate log Z_D-log Z.
Conditional and base token marginals follow from classical inside/outside.
Neural softmax row normalizers cancel from the conditioned word law, but the
original confidence readout STILL needs the actual row normalizers. They are
not free or disposable. A moving comparison boundary can cause a jump; the
formula does not establish a global C1 policy or include boundary derivatives.
Changing theta across cells can make an old action impossible. Importance
sampling additionally requires absolute continuity of the relevant path laws;
an exact ratio with zero numerator is not a proof of that hypothesis.

Let S(X)=d log P_theta(X), h(a) be any square-integrable action-only multiplier
(reward, baseline-adjusted return or vector Jacobian projection), and
G_full=h(T(X))*S(X). Then

    G_coll=h(a)*d log Pr_theta(a)=E[G_full | a],
    Cov(G_full)-Cov(G_coll)=E[Cov(G_full | a)] >= 0.

These are the CLASSICAL conditional score/total covariance identities. For a
finite-horizon Markov decoder whose next inputs depend only on observed actions,
fresh later randomness is conditionally independent of discarded proposals.
Conditioning the full proposal estimator on the complete observed action path
therefore gives the sum of these collapsed scores, with the same covariance
inequality for a final-return estimator. Need local stability at EVERY reachable
state and fixed finite horizon (progress gives <=|M_initial| steps). This is an
observed-PATH likelihood, not the marginal probability of the final text summed
over different action paths. No native EPIC equivalence is inferred.

## 5. A connected family, including best scalar baseline

This is a mathematical separation against the explicit full-proposal score
estimator, NOT a benchmark, a lower bound for every analytic control, or novel
Rao–Blackwell theory. Let m>=3; X0 is binary with probability p=3/5 of 1;
X1,...,Xm are uniform on {0,1,2}. Condition on sum_i X_i ==0 mod3. A 3-state
running checksum automaton recognizes this regular language; fixed JSON array
brackets/commas embed it into consumable strings without changing calculations.
Every variable participates in the same constraint, so there is no independent
disconnected component to delete. The unconstrained valid mass at theta0 is1/3.

Tilt the log weights of X0 by theta*X0 and those of every later variable by
theta*(X_i-1). Use their row-normalized model probabilities as confidence and
tau=9/10. At theta0=0, BOTH binary probabilities (2/5,3/5) exceed every ternary
probability (1/3) and are below tau. There is an open neighborhood where the
fallback ALWAYS exposes only X0; ties among losing ternary positions do not
matter. This is genuinely the sampled-confidence rule in its regular region.

Given X0, each later variable is uniform and any pair of later variables is
independent (m>=3): after fixing at most two of them, at least one uniform
coordinate determines the checksum. Therefore, with V=2m/3,

    S(X)=(X0-p)+sum_(i=1..m)(X_i-1),
    E[S|X0]=X0-p,   Var(S|X0)=V.

For reward R=X0 the true derivative is q=p(1-p)=6/25. The collapsed estimator
with state baseline b=1-p=2/5 equals q on BOTH actions, hence variance0.
For the full estimator with ANY scalar state-only baseline b,

    Var((R-b)S) = A(1-b)^2+B*b^2-q^2,
    A=p*((1-p)^2+V), B=(1-p)*(p^2+V).

Its best baseline is b*=A/(A+B) and its minimum variance is

    A*B/(A+B)-q^2 = q*V*(V+1-3q)/(V+q) > 0,

which grows linearly in m. The collapsed estimator's baseline is allowed the
same exact moment information as that optimized control. Counting/conditional
expectation can solve the toy reward without ANY Monte Carlo, so this example
does not defeat that stronger control or predict neural speed/quality.

## 6. Charged work and decision

On a given deterministic graph/circuit of size C, the base partition and its
outside values cost O(C) arithmetic operations. Filtering original IDs costs
O(nV) densely, or the full size of an equally correct sparse interface. One
additional filtered inside/outside costs O(C), not one for every discarded
word or mask subset. Rational bit complexity grows with original precision
and length and is NOT constant-time. GPU floating arithmetic needs separate
error/law justification; exact native finite-RNG transition probabilities are
not implied by the ideal product model. The existing numerical A51 control
cannot be imported as a new numerical proof without its immutable source.

A full-proposal estimator is an admissible strong control, not an invalid
gradient. Plain retained-token probabilities generally omit both grammar and
selection evidence. Direct evidence inference can implement exactly this
reduction and MUST receive equal caches/pruning/numerical precision. Before
any large implementation: independent law/score oracles, primary novelty audit,
complete-cost external-state protocol and a plausible real variance signal.
