# IID proposals: pure covariance proof and sharp directional query frontier

This is a written mathematical theorem. Its proof does NOT require v4's
finite rational certificates, a numerical experiment, or Lean. It does
require the explicitly specified sampling/information model below. Classical
matching, RSS, pivotal sampling, Bernstein polynomials and variance identities
are antecedents. Priority and publication sufficiency remain to be audited.

## Six-proposal operation

Let P be ANY probability law, c a fixed map to finitely many classes, and G
any finite-vector square-integrable function. Zero-mass classes are omitted.
Draw Z1,...,Z6 IID from P, **with replacement**. Uniformly choose one of the15
perfect matchings of the six POSITIONS that minimizes equal-class edges.
Return X=Z1 and its matching partner Y. Do not deduplicate identical original
states or aliases. Selection uses only the six class labels and independent
integer randomness, never the current G values. The first state is retained
literally; it may already have been evaluated.

**Safety theorem.** Both marginals are P and, in Loewner order,

    Cov(G(X),G(Y)) <= 0,
    Cov((G(X)+G(Y))/2) <= Cov(G(Z1))/2.

For any linear projection the inequality is strict iff its conditional class
means are not all equal. Thus a bad proxy never increases any projected
variance; a useless proxy gives equality. This is an MSE/covariance statement,
not a claim of lower total training loss or higher generation accuracy.

## Direct class-count description

Conditional on the unordered labeled pool, the first POSITION is uniform.
Every matching permutes positions and is invariant in law under permutation,
giving both original marginals. If r_i are its class counts, the conditional
atom diagonal is max(0,r_i/3-1). The complete six-position profiles are:

| Profile | Conditional class joint law |
|---|---|
| Any count>=3 | Star at h: J_hj=r_j/6, J_hh=r_h/3-1; all other entries zero |
| (2,2,2) | Zero diagonal, every off-diagonal1/6 |
| (2,2,1,1) | Big/big1/5; big/small1/15; small/small1/30; zero diagonal |
| (2,1,1,1,1) | Big/small1/12; small/small1/36; zero diagonal |
| (1,1,1,1,1,1) | Every off-diagonal1/30; zero diagonal |

The star includes ties at3. These cases exhaust the eleven integer partitions
of6. The non-star completion counts are respectively8,10,12,15, derived by
inclusion-exclusion of the forbidden equal-class edges among the15 matchings.
For example(2,2,1,1) has15-3-3+1=10 matchings; fixing a big/big edge leaves3
completions, and fixing a small/small edge leaves2. Counting the possible
oriented endpoints yields the table. All displayed probabilities refer to
class pairs, retaining the multiplicity of ORIGINAL positions.

Let p_i=P(c=i) and let J now denote the unconditional class joint matrix.
The counts have law6! product_i(p_i^r_i/r_i!). Averaging the table gives

    J_ii = g6(p_i) = 5p_i^4-6p_i^5+2p_i^6.
    J_ij = p_i p_j U(p_i,p_j), i!=j,

where S_k=sum_i p_i^k and

    U(x,y)=1+x+y-S2+2(x^2+y^2)-S2(x+y)-2S3
            -(x^3+y^3)-2xy(x+y)+S2^2+S2xy+S4+xy(x^2+y^2).

This is also the leading homogeneous part of v3's finite-source polynomial
W, since multinomial counts are the limit of hypergeometric counts with
n_i/M tending to p_i. The counting formula/table, not an empirical check,
justifies the polynomial identity for any number of classes.

## Sum-of-squares proof for all class probabilities

With at least two positive classes put

    A=1-S2>0, T=sum_i p_i^2(1-p_i)^2, B=A^2+T>0.

Center scalar class means f so sum_i p_i f_i=0. Set

    a_i=p_i f_i, h=sum_i p_i a_i, t_i=p_i(2-p_i),
    b_i=a_i+(h/A)p_i, K=B+A.

Expanding the joint polynomial gives

    f^T(J-pp^T)f = -sum_i (B+A t_i)b_i^2
                   +K (sum_i p_i b_i)^2.                (1)

To check the algebra without code: g6(x)-x^2 U(x,x) equals
-x^2(B+A x(2-x)); the mixed surviving terms on sum_i a_i=0 are
S2 h^2-2h sum_i p_i t_i a_i. Finally sum_i p_i b_i=h/A,
and A+S2=1. Completing the square gives(1). Equivalently take the analytic
B0>=0 square identity of v4 to its multinomial limit; B is strictly positive,
so the computer-assisted small-M boundary plays no role in this argument.

Weighted Cauchy gives (sum_i p_i b_i)^2<=sum_i p_i b_i^2. Moreover

    B+A t_i-K p_i = (1-p_i)(B+A p_i)>0.

Consequently

    f^T(J-pp^T)f <= -sum_i (1-p_i)(B+A p_i)b_i^2 <=0.

If f is nonzero after centering, b cannot be zero: b=0 would imply all f_i
equal -h/A, contradicting centering. Thus the class form is strictly negative
on every nonconstant class-mean direction. A one-class map gives J=pp^T.

Conditional on the label tape, different IID POSITIONS carry independent
original values from their class-conditional laws. Matching selects two
different positions using only their labels. Thus within-class residuals
have zero cross covariance, even if two realized raw states coincide. The
cross covariance of G is precisely that of its conditional class means.
Applying the scalar form to every linear projection proves the vector result.
There is no monotonicity/isotonicity assumption on a neural gradient.

## Information model and sharp worst-direction advantage

Consider universal algorithms which query at most b IID proposals from an
opaque source, retain their literally first one, and return two queried
original states. Cloning/randomization/adaptive stopping are permitted. No
free class masses, inverses, unsampled labels or expensive score evaluations
are supplied. Original marginal correctness must hold for EVERY class-mass
vector p, not only when the true masses happen to be balanced. This model
does NOT bound all mask-specific, mass-aware or non-IID algorithms.

Pad queries to b. Given counts r, the second class marginal z_i(r) is
independent of the unknown p. Universal correctness says its multinomial
average equals p_i. It also equals that average for z_i(r)=r_i/b. The
degree-b homogeneous Bernstein monomials are independent on the simplex:
a homogeneous polynomial zero there is zero on the whole positive cone and
therefore identically zero. Thus z_i(r)=r_i/b for every r. The retained first
has this conditional marginal too. Conditional Frechet forces joint atom
diagonal at least max(0,2r_i/b-1). Averaging gives the sharp bound

    g_b(p)=sum_{r=0}^b choose(b,r)p^r(1-p)^(b-r) max(0,2r/b-1).

At balanced masses p_i=1/L, let C be the SYMMETRIC class cross-covariance of
any admitted algorithm. It has C1=0 and
trace C >= L*g_b(1/L)-1/L. Its largest eigenvalue on the L-1 contrast
directions is at least that trace divided by L-1. Hence some nonconstant
class-constant score has pair-mean variance at least1-delta_b times iid2,

    delta_b = (1-L^2 g_b(1/L))/(L-1).

Matching6 is label-permutation invariant and attains the atom bound on
every class. At balanced masses J has constant diagonal/off-diagonal, so
EVERY class contrast attains the bound. It is therefore exactly minimax
for worst-direction variance under this universal six-IID-query contract.
Class-first pivotal6 shares this BALANCED frontier; no exclusivity is claimed.

For p=1/L,

    delta4=delta5=p(1-p),
    delta6=p+p^2-4p^3+2p^4.

With four balanced classes these are3/16 and33/128. Thus matching6 improves
the optimal worst-direction pair-mean variance of ANY admitted cap4/cap5
algorithm by at least9/104 (about8.65%), and reduces it by33/128 (about25.78%)
relative to iid2. Both use TWO expensive evaluations; the extra proposals
are cheap. These are analytic resource statements, not measured runtime.
Classical paired RSS has cross covariance -dd^T and rank at most1, leaving
L-2 directions unchanged when L>=3; it can still beat matching6 on a chosen
scalar direction, as all six old score banks demonstrate.

## dLLM/CFG corollary, complete costs and practical limit

Hold a CFG-valid JSON/DSL training candidate, parameters, and a finite cheap
structural classifier fixed. P can be the native known count-uniform noising
law (K uniform1..n, uniform K-subset) for a time-independent dLLM, or its
native timed corruption/dropout law with the appropriate original loss
weights included in G. No LCM lifting is required, although callers using
lifted original tickets keep their aliases. Evaluate the same loss/gradient
at the retained corruption and selected partner; update parameters only
after averaging the pair. Conditional on the past this is unbiased and
covariance-safe for the original objective. Fitting the classifier from
CURRENT selected scores would invalidate the declared independence.

At balanced class masses, if V_between is the covariance of conditional
class means and V_within is the remaining covariance, the pair has covariance

    (V_within+(1-delta6)V_between)/2,

versus (V_within+V_between)/2 for iid2. This exhibits the practical limit:
if class means explain little gradient variance, the reduction is small.
A41's weak output-bias proxy and stronger retained RSS/analytical controls
are preserved; no whole-model training superiority follows from this theorem.

The exact matching uses15 constant-size candidates and bounded integer
randomness. Charge six original noising/materialization/classification costs,
any proxy fit/update/storage and two forward/backward evaluations plus O(d)
gradient output. For native count masks, exact subset generation can use
standard integer sampling without constructing a gigantic uniform ticket
LCM. If the setup is amortized and overhead relative to iid2 is epsilon,
the variance-times-cost is improved only if

    (1-delta6*R^2)(1+epsilon)<1,

where R^2=trace(V_between)/trace(V_total). This is a sufficient condition,
not a measured gain or assumption that setup is free. Output-bias target
histogram controls, known count/time stratification, analytical/CV methods,
retained RSS and competent pivotal designs must remain in practical controls.
This does not establish semantic quality, a new trained dJev, whole-training
dominance, decoding latency, or superiority over EPIC.
