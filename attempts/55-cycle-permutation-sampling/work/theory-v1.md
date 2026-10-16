# A55 written derivation — before prototype

Date 2026-10-16. Positive algorithm/cost candidate under explicit conditions;
not a claim of new loop-soup theory or superiority over every known sampler.

## 1. Target and detection

For a nonnegative rational n×n matrix W with positive permanent, the target is

    P(pi) = product_i W[i,pi(i)] / per(W).

Choose a positive base matching b and relabel its columns as the diagonal.
Divide row i by W[i,b(i)], obtaining I+R with R[i,i]=0 and R>=0.
Both transformations preserve the normalized assignment law. First require

    r = max_i sum_j R[i,j] < 1.

If such a base satisfies this condition, its entry in EVERY row is the unique
row maximum. Thus this implementation can detect it by row argmax plus a
distinct-columns check, O(n²) rational comparisons/additions; no Hungarian
call is needed for this restricted condition. A failure is a refusal, not a
proof that no other exact sampler applies. A more general spectral-radius
variant is NOT implemented or included in the stated work bound.

Diagonal row/column scalings preserving the target act on R by diagonal
similarity (after ratio normalization). They preserve rho(R), but can change
the maximum row sum. No claim that arbitrary matrices become eligible by
scaling. Fixed original identifiers are returned via the inverse relabeling.

## 2. Classical soup and conditioning

A rooted closed walk x0,...,xk=x0, k>=1, has mass

    (1/k) product_{j=0}^{k-1} R[xj,x(j+1)].

There is one atom per rooted vertex SEQUENCE, not per abstract rotation.
Projecting to unrooted loops gives product R / repetition multiplicity.
Independent Poisson counts of these rooted atoms project to the standard
oriented Markov loop soup of intensity one. Total intensity is

    L = sum_{k>=1} tr(R^k)/k = -log det(I-R) < infinity.

Let E mean that each vertex occurs at most once in the union of all loop
visits (exclude the repeated closing endpoint). Then all present loops are
simple and mutually vertex-disjoint. A permutation is uniquely its nontrivial
cycles plus fixed points. Since R has zero diagonal, for each permutation pi,

    P(soup represents pi AND E) = det(I-R) product_{i:pi(i)!=i} R[i,pi(i)].

Proof: a simple length-k cycle has k distinct rooted rotations, each with
intensity weight/k; their Poisson sum has intensity weight. Exactly one
copy contributes weight, no copy exp(-weight), and the independent absence
of EVERY other loop supplies exp(-L). Distinct simple cycles yield independent
factors. This includes the identity via the empty soup. Consequently

    A := P(E) = det(I-R) per(I+R),
    law(pi | E) = P(pi).

Unlimited independent soup retries therefore give the exact target and
terminate almost surely because A>=det(I-R)>0. This is a DIRECT consequence
of the classical occupation/permanental law (Li–Zheng2022 Theorem1.2), not a
new identity. Independent simple-cycle Poisson conditioning is explicitly
present in Armendáriz–Ferrari–Frevenza2019 §3. Non-simple loops here are a
proposal device, never accepted output cycles.

## 3. Finite rational draws, no enumerated cycles or transcendental oracle

For r=0 output the base assignment. Otherwise generate a dominating soup:

1. Draw M as the sum of n independent geometric-on-{0,1,...} variables
   with continuation probability r. Thus

       P(M=m) = C(n+m-1,m) (1-r)^n r^m.

2. Conditional on M=m, generate an Ewens permutation on m AUXILIARY labels
   with parameter n. For j from 1 to m draw an integer uniformly in
   {0,...,n+j-2}. One of the first n outcomes starts a new cycle; each
   remaining outcome inserts j after its designated existing label.
3. For every auxiliary cycle of length k choose a start vertex uniformly
   among n. Follow k transitions of the substochastic matrix R/r, with a
   cemetery category for each row deficit. A killed walk is discarded.
   Keep only walks which close at their starting vertex.
4. If the kept walks visit any vertex twice, reject this WHOLE soup. Otherwise
   output the permutation specified by those cycles and the base fixed points.

Geometric continuation and categorical draws use rational probabilities;
uniform integers can be sampled by unbiased random bits and rejection.
There are no Poisson/logarithm/real-number primitives in this realization.
The Ewens insertion sampler is standard. Its n here is the number of original
vertices, not a count of new neural samples.

Proof of domination. Write C_k for the number of auxiliary cycles of size k.
Multiplying the negative-binomial mass and Ewens cycle-count mass yields

    P((C_k)) = (1-r)^n product_k [(n r^k/k)^C_k / C_k!].

These are independent Poisson counts with means n r^k/k, since
sum_k n r^k/k=-n log(1-r). Start/transition/closure thinning sends a specific
rooted closed walk to rate

    (n r^k/k) (1/n) product_j (R[xj,x(j+1)]/r)
      = product_j R[xj,x(j+1)]/k.

Poisson marking/thinning gives exactly the soup of §2. Rotation and repeated
walk multiplicities are already accounted for by rooted sequences. There
must NOT be an extra factor k in the thinning or the accepted probability.

## 4. Explicit rejection certificate

Let G=(I-R)^(-1) and u_i=G[i,i]-1>=0. The pgf of the loop occupation L_i is

    E[z^L_i] = 1 / (1 + u_i (1-z)).

Proof: marking departures from i replaces R by D(z)R. Apply the determinant
lemma to I-D(z)R=(I-R)+(1-z)e_i e_i^T R. Since RG=G-I, its determinant is
det(I-R)[1+(1-z)u_i]. The determinant-ratio pgf follows from the soup's
Poisson generating functional. Therefore L_i is geometric with mean u_i and

    P(L_i>=2) = (u_i/(1+u_i))².

The union bound yields the computable certificate

    A >= 1 - B,   B = sum_i (1 - 1/G[i,i])².

No independence between vertex occupations is asserted. Inverting R gives
this certificate but is NOT needed by the sampler. If every off-diagonal
entry is at most a/n, then for k>=2,

    (R^k)[i,i] <= (a/n) r^(k-1),
    u_i <= a r / [n(1-r)],
    B <= a² r² / [n(1-r)²].

The first inequality uses the last edge into i and the row sum of R^(k-1).
This cheap certificate requires only r and the maximum entry. A negative
lower bound is inconclusive, not a failed correctness claim. These estimates
are classical determinant/occupation/union-bound calculations; sufficient
originality of the operational consequence remains to be assessed.

## 5. Work and a comparison with a fully specified control

Precompute rational categorical rows for R/r including cemetery, after reading
ALL matrix entries. Linear CDF tables use O(n²) storage/preparation arithmetic
and O(log n) comparisons per transition; exact alias tables can improve this
but are not assumed. The n geometric draws require expected n/(1-r) Bernoulli
trials, M has mean nr/(1-r), Ewens insertion uses O(M) integer draws and pointer
work, and total proposed walk lengths are M. Closed killed walks can stop
early. Including output the expected draw/comparison work per soup is

    O(n/(1-r) + nr log(n)/(1-r)).

Independent retries with possibly correlated cost and acceptance have
expected total work E[cost per soup]/A: expand the sum of trial costs, using
independence of a new trial from the PREVIOUS failures. No assumption that
within-trial cost is independent of acceptance is needed.

For fixed r<1,a=O(1), sufficiently large n makes A>=1/2. Thus reading/preparing
the dense matrix costs O(n²), and expected subsequent work is O(n log n)
with those constants. An optional exact G computation costs O(n³) arithmetic
and is billed separately. No bit complexity is hidden by the word
"rational": if entries have B bits, normalized ratios/row sums/CDFs can have
O(nB) bits under elementary common-denominator preparation. All integer
comparisons/additions/multiplications and rejection for randbelow are charged
at their actual operand lengths. The theorem is an arithmetic/draw bound,
NOT a unit-cost claim for arbitrary precision or a GPU/latency measurement.

For the connected dense family R[i,j]=r/(n-1), i!=j, fixed 0<r<1,
the soup intensity obeys

    L <= sum_{k>=2} [n/(n-1)] r^k/k = O_r(1).

Indeed tr(R^k)<=n max(R[i,j]) r^(k-1). Hence per(I+R)<=exp(L)=O_r(1)
by §2 (A<=1). Independent row draws from normalized I+R are a competent
EXACT rejection control if invalid assignments are discarded. Their
acceptance is per(I+R)/(1+r)^n = exp(-Theta_r(n)). This proves a separation
from THAT control, including early invalidity checking in its number of
trials. It proves neither a lower bound for all exact samplers nor superiority
over symmetry-aware sampling of this particular matrix. Perturbations keeping
entry bounds and row sums bounded away from zero retain the comparison:
per(I+R)=O(1), while product of row sums of I+R grows exponentially. They need
not have the family's exchangeable symmetry. Still, known polymer samplers
are mandatory, not bypassed by perturbing an example.

## 6. Essential unfavorable cases and finite budgets

Take n/2 disjoint two-cycles with ratio r on both directions. Then

    A = [(1-r²)(1+r²)]^(n/2) = (1-r^4)^(n/2).

Global rejection is exponentially bad. Actual SCC decomposition reduces this
example to independent 2×2 blocks with elementary exact samplers, so it is
not a useful advertised hard case. Dense tiny connections can prevent exact
SCC splitting while preserving a similarly poor global acceptance: no
universal efficiency claim even for row-dominant matrices.

Any time/draw/memory cap returns FAIL. Conditioning successful outputs on a
cap can bias the normalized law, since cost and output may be correlated.
A same-randomness coupling bounds the variation of the subprobability
implementation by its cap-hit probability; it does not establish exact
conditional output after a cap or arbitrary fallback. Unlimited termination
is the exact target claimed above. No posterior matrix is claimed equal to
native DiffuRank/EPIC output, and no semantic ranking/tracking improvement is
implied by a correct assignment sampler alone.

## 7. Prior obligations before promotion

MacMahon's theorem and Le Jan's occupation law give the target identity.
Poisson simple-cycle exclusion/loss networks and Boltzmann weighted-cycle
sampling give immediate competing constructions. The candidate detail is
the efficient rational closed-walk implementation plus an input-checkable
cost regime. Whether this already follows from a published sampler in the
same regime is unresolved. Read original sources and include their feasible
oracles/costs, not only arbitrary-row rejection. New neural matrices,
tracking data or expensive benchmarks require a separate frozen protocol.
