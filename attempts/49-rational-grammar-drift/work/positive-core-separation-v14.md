# V14 — An explicit positive-weight storage separation, not a benchmark

2026-10-12, written BEFORE finite checks. This theorem compares the specified
uniform angular CORE representation with the endpoint CORE under the same
all-query tolerance. It is NOT a lower bound for every TV algorithm, a new
convex approximation rate, or a synthetic generation/performance experiment.

## Positive original probability family

Let M>=8 be divisible by8, j=-M/2,...,M/2, and define one shared domain with
M+1 distinct original IDs. Set

    p(j)=1/(M+1), q(j)=(M+j)/(M*(M+1)).

Both rows are strictly positive and sum to one. Their minimal denominator
clearings give paired integer generators a_j=(1,M+j), because the consecutive
q numerators have common gcd1. This is a legal input row, not an artificial
signed vector family. Its exact TV is S/[2*M*(M+1)], where
S=sum_j |j|=M*(M+2)/4.

## Lower bound for the specified streamed uniform control

Take angular grid N=M. Its positive-coordinate support points both equal
u=(M+1,M*(M+1)). As det(u,a_j)=(M+1)j, its second support point is
v=(1,M+S), using the fixed +1 tie at j=0. Cofactor coordinates of a_j are

    X_j=S-j, Y_j=(M+1)j.

For |j|<=M/8, X_j>0 and

    |Y_j/X_j| <= (M+1)/(2M+3) < 1/2.

Thus these M/4+1 generators lie on the same positive-x square side. The
bucket coordinate is floor(M*r_j), where r_j=(M+1)j/(S-j). Consecutive ratios
satisfy

    r_(j+1)-r_j = (M+1)*S / ((S-j-1)*(S-j)) > 1/M.

For the last inequality, (S+M/8)^2 < M*(M+1)*S: substitute
S=M(M+2)/4 and cancel M², reducing to
(2M+5)^2 < 16(M+1)(M+2), true for M>=8.
Hence the central generators occupy DIFFERENT integer buckets. No bucket
sum vanishes, since every original first coordinate is positive. Therefore
the streamed angular control outputs at least M/4+1 integer pairs. This
lower bound does not rely on V12's exact-input shortcut or a resource cap.

## Matched endpoint upper bound

For M>=40 put epsilon=20/(M-20) and d=1. V12's angular budget is EXACTLY
N=ceil(20*d*(1+epsilon)/epsilon)=M. Its calibrated endpoint budget is
k=ceil(sqrt(M/320)), with at most64k retained pairs. Both preserve every
real query by at least1/(1+epsilon). As M tends to infinity, this explicit
positive family therefore has angular Omega(1/epsilon) stored pairs versus
endpoint O(1/sqrt(epsilon)). The ratio is unbounded.

This is a strict mathematical storage benefit for interchangeable all-query
cores composed inside a product/grammar forest. It is independent of physical
timings. It does NOT imply that computing this ONE-POSITION TV is harder:
an ordinary exact scalar sum solves it in O(M) time and O(1) auxiliary space.
That competent control must be acknowledged. A root-only query need not build
either core. The benefit concerns a reusable intermediate representation for
all downstream admissible compositions, not universal fastest scalar TV.

Classical planar support approximation already gives this order; the own
candidate is its sharper explicit deterministic TV propagation bound and
integer realization. No new geometric lower bound or exclusive feasibility
is claimed. Finite checks, if run, verify the formulas/implementation only.

## Prospective checks and eight-question update

Use ALL M in {64,256,1024,4096,16384}. Check the two exact row sums, minimal
integer weights, analytic norm/TV, streamed bucket lower bound and endpoint
64k cardinality. Compute each resulting scalar TV interval against the exact
closed form. Record no runtime rankings or model result. Stop on unexplained
failure and preserve it. All earlier real functional cases remain unchanged.

Criteria1/6 retain the numerical dLLM/GLC audit and full costs. Criteria2--4
gain a strict, explicit storage comparison against the strengthened specified
core, not all TV algorithms. Criterion5 uses a proof family as correctness,
not benchmark. Criterion7 includes the faster exact one-position scalar
method and known geometric rate. Criterion8 still requires precise priority
and independent human judgement; the lemma does not guarantee publication.
