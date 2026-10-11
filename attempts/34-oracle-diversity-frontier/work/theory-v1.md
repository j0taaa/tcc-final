# Sharp expected-work frontier: written candidate, NOT verified priority

2026-10-11. Independent of A32/v4's live producer. No implementation or neural
measurement accompanies this note. The lower-bound technique and gambler's
ruin construction are classical; specific priority remains OPEN.

## 1. Contract

An oracle emits independent Bernoulli(p) class bits, unknown p in(0,1).
A single algorithm, independent of p, uses those bits and independent known
auxiliary randomness. It stops after N draws and emits (X,Y) in{0,1}².
Both marginal laws MUST equal Bernoulli(p) for EVERY p. Its worst expected
TOTAL cost is sup_p E_p N<=b, b>=2. For the lower bound, assume a>0 with
E_(1/2) exp(aN)<infinity. This regularity includes bounded algorithms and the
finite-barrier construction below. Do NOT silently extend the theorem to
all a.s.-finite sequential procedures without addressing regularity.

The lower bound permits arbitrary outputs, not necessarily observed bits,
and does NOT require retaining the first draw. Our construction DOES retain
the first oracle bit literally. Write q=1-p, delta=p²-Pr(X=Y=1), and

    eta(p)=delta/min(p²,q²).

This is the fraction of the MAXIMUM possible marginal-preserving increase
in pass@2 over iid for either class event. Fréchet gives eta<=1. Negative eta
is allowed for bad competitors. The optimization is

    sup_algorithms inf_(0<p<1) eta(p), subject to the above cost contract.

This is NOT a frontier for known-p sampling, arbitrary K, physical latency,
full decoding or an unknown semantic verifier's absolute improvement.

## 2. Candidate theorem

For m=floor(b), lambda=b-m and b>=2, define

    s_b=(1-lambda)/m+lambda/(m+1)
       =(2m+1-b)/(m(m+1)).

Then the minimax value is EXACTLY

    eta_b=1-2s_b.

It is attained by randomly choosing barrier m with probability1-lambda and
m+1 with probabilitylambda, then running the retained-first ruin coupling
below. Expected TOTAL cost equals b for EVERY p. Every budget parameter is
fixed BEFORE oracle bits, not estimated from successful answers.

## 3. Lower bound: stopped score and the integer refinement

Let S be the number of ones among the N observed bits, M=2S-N, and Z=X+Y-1.
At p=1/2, both marginals equal1/2, so Z in{-1,0,1}, E Z=0. Write
s=Pr(Z!=0)=Pr(X=Y). If s=0, the identity below is impossible; hence s>0.

The score of a terminated transcript is2M at1/2. Differentiate
E_p[(X+Y)/2]=p. Exponential integrability justifies differentiating the sum
over terminal prefixes: on a small neighborhood of1/2, the likelihood
ratio of an n-bit prefix is bounded by(1+2epsilon)^n, and its derivative
by a constant times n(1+2epsilon)^n. Choose epsilon so this is dominated
by the assumed exponential moment. Independent auxiliary decisions have
p-independent densities and do not alter the score. Thus

    E[Z M]=1.

Optional stopping of the simple symmetric walk gives E M=0 and E M²=E N.
For the latter use the stopped-square martingale or the L² orthogonality of
increments; finite E N follows from regularity.

For ANY integer k>=1, every integer v satisfies

    v²-(2k+1)v+k(k+1)=(v-k)(v-k-1)>=0.

On Z!=0 put v=ZM, an INTEGER with v²=M². On Z=0 retain the nonnegative
M² term. Taking expectations yields

    E N=E M² >= (2k+1)E[ZM]-k(k+1)Pr(Z!=0)
                =2k+1-k(k+1)s.

Therefore s>=(2k+1-b)/(k(k+1)). Set k=m=floor(b) to obtain s>=s_b.
At1/2, J11=s/2 and eta(1/2)=1-2s<=eta_b. Infimum over p cannot exceed
that value. This compares with ALL regular p-blind adaptive factories in
the contract, not just selected stopping trees or implemented controls.

Ordinary sequential Cramér–Rao only gives s>=1/b. The displayed bound is
strictly stronger at noninteger b: s_b-1/b=lambda(1-lambda)/(b*m*(m+1)).
The score principle is a PRIOR result, not a new method of lower bounds.

## 4. Attainment: a classical ruin process with first bit retained

Fix integer r>=2. Draw X from the oracle. Set level i=1 if X=1 and i=r-1
if X=0. Draw further iid bits; a1 raises the level by1 and a0 lowers it by1.
Stop at0 or r and return the FINAL draw as Y. No class probability is used.
The construction has an exponentially bounded tail: any block of r-1 bits
all equal absorbs from any live level, with probability
p^(r-1)+q^(r-1)>=2^(2-r). N counts X and EVERY later draw.

Let f_i be the probability of absorption at r from level i. Classical ruin
gives f_i=[1-(q/p)^i]/[1-(q/p)^r] for p!=1/2, f_i=i/r at1/2. Its symmetry
identity p f_1+q f_(r-1)=p proves the second marginal. The joint law is

    J11=(p-q)p^r/(p^r-q^r),
    J00=(p-q)q^r/(p^r-q^r),
    J01=J10=p-J11,

with the continuous fair limit J11=J00=1/(2r). Boundary p=0/1 also yields
the correct degenerate pair; it is not needed for the lower bound.

For expected further walk time t_i, the classical stopped-drift equation is
t_i=(i-r f_i)/(q-p), with fair t_i=i(r-i). Weighting the first-bit cases,

    E further draws=[p+q(r-1)-r(p f_1+q f_(r-1))]/(q-p)=r-1.

Hence E TOTAL N=r for EVERY p, including1/2 by its fair expression.

To prove the uniform normalized advantage take p<=q and a=p/q<=1. Then

    J11/p² = (1+a)a^(r-2)/(1+a+...+a^(r-1))
            <=(1+a)/(r-1+a)<=2/r.

The first inequality uses a^k>=a^(r-2) for k<=r-2; the second is equivalent
to(r-2)(1-a)>=0. By swapping0/1 the same statement holds for p>=q, now
using J00/q². Thus eta_r(p)>=1-2/r for EVERY p, equality at1/2. Mixture of
r=m/m+1 gives eta(p)>=1-2s_b and E N=b, proving attainment and the theorem.
For r=2 the pair is iid. For r>2 interior p, its class covariance is strictly
negative. This is a comparison with unknown-p iid, not with known-p optimal
antithetic sampling, which attains eta=1 without estimating p.

## 5. Full token/transition payloads and a limited application corollary

Let the oracle actually emit full payloads U~P with a fixed binary class c.
Keep the first payload literally, and use the LAST drawn payload for the
second output. r>=2 ensures it is a distinct draw. Decisions and stopping
depend ONLY on class bits, so conditionally on the two output classes the
payloads have independent laws P(.|c). Both complete marginals equal P,
including original token IDs, aliases and every failure/recovery status
present in that oracle. No grammar-valid output is substituted for a failure.

For any square-integrable score f, put mu_j=E[f(U)|c=j]. Then

    Cov(f(U1),f(U2))=-delta(p)(mu_1-mu_0)²<=0.

The comparison to the maximally antithetic class coupling obtains at least
eta_b of its variance reduction for EVERY f, without knowing its mu_j.
For terminal event A use f=1_A; pass@2 is no lower than iid, strictly larger
iff the class means differ and b>2. If the two classes have equal conditional
success rates, the gain is ZERO. Complete events can have arbitrary values
inside a class: the theorem does not assume semantic monotonicity.

Apply P to a native structured dLLM transition on one head, retaining the
original transfer/rejection/recovery policy. The GLC is part of the oracle;
the coordination itself never changes its marginal. A frozen head may serve
auxiliary draws with no further forward, but constructing each FULL native
transition is still charged. Use full histories and independent continuation
after divergence for the old backward-induction nonpositive-covariance
consequence. The eta_b fraction does NOT automatically survive the whole
trajectory: different local couplings change meeting probabilities. A32
already preserves an adverse example against such monotonicity.

## 6. Publication/implementation obligations still open

This is a written candidate proof, not a formal proof or originality claim.
Need primary comparisons with DeGroot1959/Ghosh1987, discrete Cramér–Rao,
Bernoulli factories and optimal coupling literature; the exact frontier might
already be implicit or explicit there. Need independent tiny exact oracles,
and a useful cheap native oracle/classification. Rare event maximum absolute
pass@2 gain is p², and iid with more terminal outputs can win. No speed or
semantic improvement has been measured for A34. A32/v4 is a DIFFERENT method
and its ongoing records are not experimental evidence for this theorem.

