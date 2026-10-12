# All-budget covariance refinement: written construction and proof

This is an analytic argument, not a novelty or practical-use certificate.
The base C4 law is classical; V7's exact C6-versus-C4 obstruction stands.

Let Z_1,...,Z_B be IID from any law P, B>=4, and c map to a FIXED declared
set of L>=2 labels. Keep X=Z_1. Target G can be any square-integrable vector,
and c cannot be fitted using the current target evaluations. Given unordered
label counts r_i, put D=(B)_4 and S2r=sum r_i^2. The joint label matrix of
C4 on a uniformly selected four-subpool is

    J0_ii = d_i = r_i(r_i-1)(r_i-2)(2B-r_i-3)/D,
    J0_ij = r_i r_j [B^2+B(r_i+r_j)-6B-S2r-r_i r_j+7]/D.

It has row sums r_i/B. To derive the off-diagonal numerator, fix labels i,j
and enumerate the two other slots: counts(3,1) contribute
(r_i-1)(r_i-2)+(r_j-1)(r_j-2); counts(2,2) contribute
3(r_i-1)(r_j-1); counts(2,1,1) contribute
3(r_i+r_j-2)(B-r_i-r_j); four distinct labels contribute
(B-r_i-r_j)^2-(S2r-r_i^2-r_j^2). Their sum is the displayed polynomial.
The diagonal is the hypergeometric average of the four-pool diagonals
1/2 at count3 and1 at count4. Thus these are exact count identities.

Set w_ij=min(d_i,d_j)/(L-1) and

    J_B = J0 - sum_{i<j} w_ij (e_i-e_j)(e_i-e_j)^T.          (1)

Every off-diagonal increases. Its diagonal stays nonnegative because
sum_{j!=i} w_ij<=d_i. Row sums are unchanged. Given the retained first
class i, choose partner class j with probability J_B,ij/(r_i/B), then choose
uniformly among original positions of class j, excluding position1 if j=i.
A singleton has d_i=0, so no impossible same-class singleton draw occurs.
Both ORIGINAL marginals are P. Repeat states/aliases are not deduplicated.

## Universal comparison, not a conditionally averaged variance claim

Let mu_i=E[G(Z)|c(Z)=i]. Conditional on the label tape, different IID
positions have independent within-class residuals. Neither policy chooses
the same position twice. Their unconditional cross-covariance difference is

    Cov_C4(G(X),G(Y))-Cov_B(G(X),G(Y))
      = sum_{i<j} E[w_ij] (mu_i-mu_j)(mu_i-mu_j)^T >=0.     (2)

This explicitly compares two unconditional laws with the SAME P marginals;
there is no missing pilot-mean variance term. The covariance difference of
their pair averages is one half of(2). C4 itself has nonpositive cross
covariance for all scores, so the new pair remains no worse than iid2.
For B>=6 and any two positive-mass classes, E[w_ij]>0: the event of at least
three samples of each has positive probability. Thus every projected
variance decreases strictly exactly when its conditional class means differ.
For B=4/5, two positive diagonal capacities cannot occur, so J_B is C4.

For a terminal binary verifier V, write mu_i=P(V=1|c=i). Since both
marginals are unchanged, pass@2 improves by exactly

    sum_{i<j} E[w_ij] (mu_i-mu_j)^2.                       (3)

This allows a native dLLM/CFG source to include its private continuation RNG
tape. Fixed native control and independent future draws are essential;
first-token canvases alone do not necessarily specify the transition state.
The statement says nothing about pass@1, physical speed or semantic meaning.

## Monotone budget theorem

For B'>B, draw a uniform B-subpool of a B'-pool. The diagonal d_i of C4
is a fourth-order U-statistic: average the C4 diagonal over every four-subset.
Consequently E[d_i(r_B)|r_B']=d_i(r_B'). Concavity of min on two coordinates
gives

    E[min(d_i(r_B),d_j(r_B)) | r_B']
       <= min(d_i(r_B'),d_j(r_B')).

Averaging shows E[w_ij] is nondecreasing in B. Equations(2)/(3) prove that
EVERY score projection and EVERY terminal verifier is monotonically improved
as the cheap-source budget grows. This theorem requires L fixed; replacing
L by the number of observed labels would invalidate this proof.

## Balanced frontier and its honest limitation

With positive balanced masses p_i=1/L, symmetry makes all E[w_ij] equal.
Let d=g4(1/L)=2/L^3-1/L^4 and a_B=E[min(d_1(r),d_2(r))]. The class-mean
variance reduction versus iid2 is

    delta_B = (1/L)(1-1/L) + L^2*a_B/(L-1).              (4)

The law of large numbers and boundedness imply a_B->d, hence
delta_B->1/(L-1). This limit is optimal among ALL exchangeable two-output
couplings with balanced marginals in the worst class-contrast direction:
nonnegative atom diagonals give trace(J-pp^T)>=-1/L; averaging its L-1
contrast eigenvalues gives delta<=1/(L-1). This limiting bound permits
known masses and does not establish finite-budget optimality of(1).

For B>=6, a_B>0, so (4) strictly beats the balanced worst direction of
EVERY universally marginal-correct score-oblivious cap4/cap5 original-source
coupling under V6's Bernstein contract. More cheap source calls are charged.
Classical pivotal/minimum-repeat methods can reach the finite atom frontier
more quickly; no domination of them or of score-specific RSS/CV is claimed.

A crude explicit rate follows without model data. Changing one label changes
the kernel d_i-d_j on any four-subset by at most1/2, and affects fraction4/B
of those subsets. Its coordinate sensitivity is therefore2/B. Tensorized
conditional variance gives Var(d_i-d_j)<=1/B. Its balanced mean is zero,
so a_B=d-E|d_i-d_j|/2>=d-1/(2 sqrt(B)). In particular

    0<=1/(L-1)-delta_B<=L^2/[2(L-1)sqrt(B)].             (5)

The rate is deliberately coarse; it is not an exponential query-frontier
claim. At L=4 even the limiting improvement over C4 is only7/39 (~17.95%)
of the pair's CLASS-MEAN variance, before within-class noise and overhead.
This alone cannot meet a20% full-cost practical gate against C4.

## Implementation and full costs

Only the retained first row is needed: multiply(1) by D(L-1) to obtain
nonnegative integer weights. Counts/S2r/diagonals and its row take O(B+L)
operations; integers have O(log L+log B) bits. Charge exact categorical
selection, all B materializations/classifications, proxy preparation,
two expensive original evaluations and vector output. For any target, let
rho be the actual variance reduction relative to C4 and epsilon the relative
complete-cost overhead. Variance-times-cost improves only when
(1-rho)(1+epsilon)<1. No practical gain is assumed from the theorem.

Generic Laplacian/Dirichlet improvements and conditional Jensen are old.
Whether this exact unknown-mass, retained-source budget construction adds
enough scientific difference is OPEN; no production or article promotion.
