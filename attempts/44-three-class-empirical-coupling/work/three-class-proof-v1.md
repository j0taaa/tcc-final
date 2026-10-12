# Three unknown-mass classes: candidate analytic theorem

2026-10-12. Written BEFORE code. Empirical transports, Fréchet coupling,
Bernstein uniqueness, ranked sets and the binomial concentration bound are
antecedents. This proof does not certify scientific priority or practical speed.

## Exact original-source operation

Let Z1,...,ZB be IID ORIGINAL draws from ANY P, B>=2, c a fixed map into
{0,1,2}, and G any square-integrable finite vector. Include independent
continuation RNG in Z when it will be consumed later. Distinct IID positions
can have the same value/bytes; never deduplicate them. Retain X=Z1 literally.
Write r_i for label counts, q_i=r_i/B and d_i=(2q_i-1)_+.

Define a symmetric empirical joint label matrix by

    J_ii=d_i,
    J_ij=(q_i+q_j-q_k-d_i-d_j+d_k)/2, {i,j,k}={0,1,2}.   (1)

If no q_i exceeds1/2, all diagonals vanish and off-diagonals are nonnegative.
If q_i>1/2, its diagonal is2q_i-1, its two off-diagonals are q_j/q_k,
and the other off-diagonal vanishes. Hence J>=0 entrywise with row sums q.
Given the retained first label i, choose partner label j with probability
J_ij/q_i, then a uniform ORIGINAL position of that label excluding position1.
Whenever J_ii>0, r_i>B/2 and r_i>=2, so that exclusion is possible.

Conditional on counts, the first label has distribution q by exchangeability.
Both unconditional original source marginals are P. Selected different IID
positions have independent within-class residuals conditional on the label
tape. Reservoir sampling of nonfirst positions stores only one representative
per label, plus the first. All B draws/classifications and RNG are charged;
only the final two original payloads require downstream G evaluations.

## Exact unconditional diagonals

For each class probability p_i, put

    D_B(p)=E[(2R/B-1)_+], R~Binomial(B,p).

Then the unconditional label matrix has diagonal D_B(p_i), rows p_i, and
off-diagonals uniquely determined by(1) with q replaced by p and d by D.
For B=2/3, D_B(p)=p^2 and the full output pair is iid2.
For B=4/5, D_B(p)=p^3(2-p), the classical C4 atom law.
Odd B gives the same D as its preceding even budget, by the binomial
degree-elevation identity; retaining the last redundant draw is unnecessary.

Set W_B(p)=p^2-D_B(p). Convexity of x->(2x-1)_+ and deletion of one
uniform slot show D_(B+1)<=D_B, so D_B<=D_2=p^2 and W_B>=0.
Also D_B(p)-D_B(1-p)=2p-1, hence W_B(p)=W_B(1-p).

## The delicate step: square-root concavity

Let B=2m>=4. Twice differentiating the Bernstein polynomial, whose coefficient
second differences vanish except at the midpoint, gives

    D_B''(p)=2(B-1)*binom(B-2,m-1)*[p(1-p)]^(m-1).

Consequently W_B'''(p)<0 for0<p<1/2. For

    A(p)=[W_B'(p)]^2-2W_B(p)W_B''(p),

we have A(0)=0 and A'(p)=-2W_B(p)W_B'''(p)>=0 on[0,1/2].
Since W_B>0 in(0,1),

    (sqrt(W_B))''=-A/(4 W_B^(3/2))<=0.

Symmetry extends concavity to[0,1]; the derivative is zero at1/2, so no
hidden upward derivative jump occurs. Endpoints follow by continuity.
Odd budgets inherit the previous even polynomial. B=2/3 is identically zero.

Write f(p)=sqrt(W_B(p)). Concavity and f(0)=0 imply
f(a)+f(b)>=f(a+b). With p0+p1+p2=1 and symmetry,

    f(p_i)<=f(p_j)+f(p_k) for every i.                (2)

## Every target vector is safe, without knowing class masses

Let C=J_unconditional-pp^T. It has row sums zero and diagonal -W_B(p_i).
The symmetric matrix -C is positive semidefinite iff its three nonnegative
square-root diagonal lengths satisfy the triangle inequalities. To verify
this directly, its off-diagonal entries are

    (-C)_ij=(W_k-W_i-W_j)/2.

A principal2x2 determinant is

    W_i W_j-[(W_k-W_i-W_j)/2]^2,

nonnegative exactly when |sqrt(W_i)-sqrt(W_j)|<=sqrt(W_k)
<=sqrt(W_i)+sqrt(W_j). The determinant is zero because row sums vanish.
All principal minors are thus nonnegative by(2).

With mu_i=E[G|c=i], independent selected residuals give

    Cov(G(X),G(Y))=sum_ij C_ij mu_i mu_j^T <=0.      (3)

Therefore covariance of the two-score average never exceeds iid2 for ANY G.
For three positive masses and B>=4 it is strict in every projection whose
class conditional means differ. A terminal Boolean verifier has pass@2 at
least iid2; best-score tails follow by applying(3) to threshold indicators.
This is not a guarantee of better pass@1 or of physical runtime.

## Unknown-mass cap-B frontier and balanced minimax consequence

Consider ANY coupling using at most B original IID sources, retaining the
first, valid for EVERY UNKNOWN three-class probability vector. Virtual
padding to B does not change its outputs. Conditional on total counts r,
universal marginal correctness plus uniqueness of degree-B multinomial
Bernstein coefficients forces each output label marginal to be r_i/B.
Fréchet then forces its conditional diagonal at least(2r_i/B-1)_+.
This yields the simultaneous bound J_ii>=D_B(p_i), attained by(1).
This is a bound for this unknown-mass materialized-pair operation, not for
free known-mass inverses, score-aware estimators or additional information.

At p_i=1/3 put d=D_B(1/3). Our normalized class operator has both contrast
eigenvalues (9d-1)/2. Every competing universal cap-B coupling has contrast
trace at least9d-1, so its worst contrast eigenvalue is at least(9d-1)/2.
Thus our rule is minimax optimal for balanced class-constant target variance
against ALL admitted universal cap-B couplings, not merely a poor baseline.

At balance the full pair covariance is

    [V_within + ((1+9d)/2)*V_between]/2.              (4)

Binomial concentration bounds d<=exp(-B/18); for any class masses separated
below1/2 by gamma, each diagonal is at most exp(-2B gamma^2).
This is an exponential approach to the ideal no-repeat class law with a
FINITE source cap, rather than the binary balanced central-binomial rate.
At balance C4's between factor is7/9; the limit is1/2, an improvement of
5/14 (~35.7%) in the between component, not in arbitrary full gradients.

Increasing B need NOT dominate C4 for every nonuniform contrast. Preserve
the explicit p=(.8,.1,.1), f=(0,1,-1) obstruction instead of hiding it.
Known mass, continuous ranked sets, CV and source derangement are competent
practical comparators and can win. Total preparation/fitting/draw/evaluation
costs and the fraction of variance explained by classes determine usefulness.

## dLLM/CFG scope

For an actual CFG-valid JSON/DSL target, P can be original timed corruption
with the proper weighting in G, or original count-uniform noising when its
time-independent-model assumptions hold. Classes are fixed structural or
past-fitted proxies of noisy original inputs. Average the two ORIGINAL full
gradients before any parameter update. The objective remains unbiased and
(3) holds conditionally on the prior fitting history. No grammatical token
or mask event is removed. Two expensive evaluations, B cheap preparations
and constant retained-payload storage are explicit.

That application still needs a meaningful full-gradient advantage and an
actual primary-literature distinction. Correctness of this analytic argument
alone does not establish publication novelty or a useful neural improvement.
