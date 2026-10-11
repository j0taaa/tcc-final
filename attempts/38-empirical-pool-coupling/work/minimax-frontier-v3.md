# A38 v3: sharp benefit/work frontier, written before the budgeted prototype

2026-10-11. This is a NEW claim, not a relabelling of v1/v2 measurements.
Rank coupling and Bernstein/exchangeability are antecedents. The candidate
contribution is the sharp frontier below against ALL adaptive unknown-law
samplers, including those allowed to return the first payload twice. Specific
literature priority, practical magnitude and publishability remain OPEN.

## Operation and comparator class

An oracle supplies iid original payloads with arbitrary unknown law P on a
fixed countable domain. A fixed, gold-free canonical map has arbitrarily many
possible distinguishable keys. An algorithm sees the samples, their values
and independent random bits, but no probabilities, densities or other
information depending on P. Its first output is the literal first oracle
sample X. Its second output Y must have the SAME FULL law P for EVERY P.
It stops after N calls, N<=4 almost surely, and sup_P E_P N<=b, 2<=b<=4.
It may clone the first, depend on observed payload values, or adapt its call
count. This is a stronger comparator class than v2's nonfirst-index class.

Write p_i=P(key=i), c=sum p_i^2, m=max p_i, and

    D(A,P)=c-Pr[key(X)=key(Y)],
    D_opt(P)=c-max(0,2m-1).

D_opt is the classical best improvement over iid among ALL pairs with
known marginal P, obtained by a half-circle CDF rotation. Define the uniform
guaranteed fraction rho(A)=inf_(P:D_opt(P)>0) D(A,P)/D_opt(P).
No semantic verifier or model benchmark enters this definition.

### Theorem (oracle-budget minimax frontier)

    sup_A rho(A)=(b-2)/8.                                  (F)

The supremum is over the full comparator class above. At mean budget3 the
value is EXACTLY1/8, attained by an independent half mixture of iid2 and the
adaptive v2 coupling. Its mean is3-c+s3/2, not necessarily exactly3.
The hard cap and countably unbounded number of possible keys matter. This
does NOT cover cap12/unbounded factories, informed logits/CDF controls or
known binary alphabets. For a fixed finite domain use the explicit finite-M
upper bound below; do not assert its limit as a new exact finite theorem.

## Attainment

Let lambda=(b-2)/2. Independently choose the v2 rule with probability lambda
and iid2 otherwise. Both retain literal first and preserve all raw marginals.
The v2 rule has mean4-2c+s3<=4 and collision benefit

    D_4=sum p_i^2*(1-p_i)^2>=D_opt(P)/4.

Therefore E N=2+lambda*(2-2c+s3)<=b and D=lambda*D_4>=
(b-2)*D_opt/8. The v1 proof of this last inequality explicitly handles the
single heavy atom. The v2 full-score covariance formula is multiplied by
lambda, so it remains nonpositive for EVERY common square-integrable score.
This is an additional guarantee of the achiever, not a restriction imposed
on competitors in the lower bound.

## Lower bound: no universal adaptive algorithm can do better

It suffices to consider rho>=0, since (F)'s upper bound is nonnegative.
Fix M>=3 distinct representative payloads with distinct keys. Average A over
all permutations of these M representatives, applying the inverse permutation
to its output. Each permutation extends to a bijection fixing other payloads.
This symmetrized algorithm still retains first, preserves P universally,
obeys the budget and has guaranteed fraction at least rho(A). Its decisions
on these representatives are invariant under renaming keys. It may depend
on M. The argument does NOT assume all finite restrictions are one algorithm.

### 1. Universal marginals force conditional empirical marginals

Pad stopped executions with UNUSED virtual iid samples to length4. For each
finite multiset r with total count4, let z_i(r) be the probability that the
second output is representative i, averaged over all ordered tapes with that
multiset and over internal randomness. Universal marginal preservation gives

    sum_(|r|=4) (4!/prod r_j!)*prod p_j^r_j*z_i(r)
       =p_i*(sum p_j)^3.

Homogeneity extends the equality on the probability simplex to the positive
cone; uniqueness of monomial coefficients gives z_i(r)=r_i/4. This is the
classical multivariate Bernstein/coefficient principle, not our invention.
Any output not yet observed is impossible under this contract: a law supported
on the observed set gives that output probability zero but assigns positive
probability to the identical stopped transcript. Thus stopping at1 returns
first; returning first at any other time is explicitly ALLOWED.

### 2. The cost of improving the 2+1+1 pattern

For the virtual multiset2A+1B+1C let alpha be its conditional joint diagonal
Pr[first=A,second=A]. It is independent of label names. Put v=1-6alpha.
Empirical first/second marginals are both1/2 on A. Conditional on first being
either singleton, second=A therefore has probability1-2alpha=(2+v)/3.

Condition further on first=B. The remaining three equally likely tapes are

    B,A,A,C; B,A,C,A; B,C,A,A.

Write R1,R2,R3 for their probabilities of returning A. Symmetry and the
conditional marginal above give R1+R2+R3=2+v. Always R1<=1.
Let gamma=Pr[N=4 | the first three keys are distinct]. The decision to request
draw4 is made BEFORE seeing it. In the last two tapes, before requesting
draw4 the probabilities of choosing positions2/3 together are at most
1-gamma: label symmetry makes this the same stopped decision law. After
requesting draw4 each tape can return A with probability at most gamma.
Consequently R2+R3<=1+gamma and

    gamma>=v.                                               (6)

This inequality includes cloning first and all adaptive early stopping.
Let t=Pr[N>=3 | first two keys are distinct]. Stopping-time measurability and
label symmetry imply t>=gamma. No fourth-key information is used for t.

### 3. A diffuse law exposes the work budget

Under the uniform law U_M let q1=Pr[N=1]. It is the same for every first key.
Those stops are collisions, hence nonnegative guaranteed benefit implies
q1<=Pr[collision]<=c=1/M. Occupation probabilities give

    E_U N >=2-q1 +(1-1/M)*t
                    +(1-1/M)*(1-2/M)*gamma
           >=2-q1 +2*(1-1/M)^2*v.

Together with E_U N<=b this yields

    v <= (b-2+1/M)/(2*(1-1/M)^2).                           (7)

This remains valid if v is negative; t and gamma are nonnegative and >=v.
Also v<=1 by alpha>=0. Uniform U_M is a proof distribution, NOT a model
benchmark chosen to improve the candidate's reported performance.

### 4. A heavy/diffuse law exposes the benefit

Now use H_M with mass1/2 on A and mass1/[2(M-1)] on each other key. The
same symmetrized decision law and therefore the same alpha/v apply.
Conditional on3A+1B the empirical marginals are3/4, so the diagonal is at
least1/2 by the ordinary Frechet bound. Conditional on4A it is1. Conditional
on2A plus two distinct singleton keys it is alpha=(1-v)/6. These patterns
have probabilities1/4,1/16 and(3/8)*(1-1/(M-1)), respectively. Dropping only
NONNEGATIVE other heavy-diagonal terms gives

    J_AA >=1/8+1/16 +(1-v)*(1-1/(M-1))/16,
    D_A <=v/16+(1-v)/[16(M-1)].

Other-key gains sum to at most their iid collisions1/[4(M-1)], without
assuming they are nonnegative. Here D_opt=c=1/4+1/[4(M-1)], so

    D/D_opt <=[v*(M-2)+5]/(4M)
       <= ((M-2)/(4M))*((b-2+1/M)/(2*(1-1/M)^2))+5/(4M).   (8)

The second inequality has a nonnegative multiplier for M>=3. Let M tend to
infinity. Every symmetrized restriction retained A's original guarantee,
so rho(A)<=(b-2)/8. Together with attainment this proves (F).

## Scientific interpretation and objections still open

The lower bound compares ALL adaptive algorithms in the stated information
and resource model; it is not a victory over an intentionally slow pool.
It proves optimal guaranteed canonical diversity per unknown-law oracle
budget with cap4. It does not prove optimal benefit for EACH distribution,
wall time, semantic correctness, pass@1, arbitrary cap, or informed sampling.
Its finite-M correction cannot be silently removed for one fixed-length
finite-vocabulary dLLM. Original samplers with arbitrary valid JSON lengths
can have an unbounded outcome domain; actual finite implementations do not.

For a CFG-constrained dLLM the payload oracle can be the full original
decoder, including failure, or a full accepted native transition whose
remaining state/RNG is retained. Unknown accepted-state probabilities are
not equal to the input logits. The v2 continuation corollary gives preserved
original final-answer marginals and pass@2 never inferior to iid2 for every
verifier, with strictness depending on informative canonical classes.
Every auxiliary call, parser retry, continuation, copy and canonicalization
must be charged. More iid outputs, informed/raw-ticket coupling and known
rank algorithms remain legitimate PRACTICAL controls outside (F)'s model.

Most importantly, an oracle lower bound plus a small kernel is not by itself
publication-worthy application evidence. Check whether (F) is already known,
and whether a real decoder/consumer obtains a useful benefit after full cost.
No native adapter, new model forward, timing, human review or publication
confirmation was performed in writing this proof.
