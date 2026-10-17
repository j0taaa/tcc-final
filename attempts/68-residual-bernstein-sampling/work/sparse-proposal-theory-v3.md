# V3: finite-moment proposal and classical component splitting

2026-10-17, AFTER V2, BEFORE V3 code or scientific execution. Existing
proofs/data remain frozen. This targets V2's costly proposal preparation,
not another claim that quadratic quasi-interpolation is new.

## 1. Equal-information control: separate the deterministic correction

Keep V2's SAME delta=H/d^1.5, initial degree, J and source count. For each
higher level n=4m, x=k/(4m), the identity remains

    r=1/2+[T+E_nu g(Y)]/w, w=7H/(4m^1.5),
    |T|<=tbar=H/(21m^1.5).

For ANY known envelope V(Y)>=|g(Y)| of mass B=E_nu V, with
tbar+B<=w/2, classical mixture splitting gives:

    with probability2tbar/w: Bernoulli(1/2+T/(2tbar));
    with probability2B/w: draw I~nu_i V_i/B,
                         Bernoulli(1/2+g(I/m)/(2V_i));
    otherwise: a fair coin.

The identity of output probabilities follows by summing the three terms.
No f-dependent setup is required before choosing the component. The T
component needs the m and4m stencils, six callbacks; the g component needs
the m stencils at x,Y, six callbacks. The fair component needs none. Thus
the written cap improves from9 to6 by a CLASSICAL rearrangement using the
SAME residual certificate. It is not an independent prior algorithm or a
new importance-sampling principle, and does not alone establish novelty.

## 2. A polynomial envelope with a constant-size normalizer

Let z=Y-x and u=sqrt(m)*abs(z). V2's scaled W satisfies

    m^1.5 W*(z) <=(7/15)u+u^2/2+u^3/6+4/15.

The elementary inequalities u<=u^2+1/4 and u^3<=(u^4+u^2)/2 imply
an upper bound23/60+(21/20)u^2+u^4/12. Increase the constant to9/20
to obtain a proposal with a useful shape:

    P(t)=9/20+(21/20)t^2+t^4/12,
    V_i=H/m^1.5 * P((i-mx)/sqrt(m)).                    (1)

This increase is intentional and precedes all V3 data. E t^2<=1/4. The
classical Hoeffding bound P(|t|>a)<=2exp(-2a^2), also valid without
replacement, implies E t^4<=1 by integrating8a^3 exp(-2a^2). Therefore

    B=E V<=191H/(240m^1.5),
    w/2-tbar-B>=53H/(1680m^1.5)>0.                      (2)

No complete grid is needed to compute B. For K~Hypergeom(4m,k,m), the
factorial moments are E(K)_j=(m)_j(k)_j/(4m)_j, j=0..4. Ordinary moments
use Stirling coefficients [1], [1,1], [1,3,1], [1,7,6,1]. Expanding
E(K-k/4)^2/m and E(K-k/4)^4/m^2 gives B with a fixed number of exact
rational operations on O(log m)-bit integers. This is a NORMALIZER cost,
not a constant bit-work bound for all sampling.

## 3. The tilted hypergeometric weights are log-concave

Let v_i=nu_i P((i-k/4)/sqrt(m)). They have the contiguous HG support.
For P=b+at^2+ct^4, b=9/20,a=21/20,c=1/12,

    P''P-(P')^2
      =2ab+(12bc-2a^2)t^2-2ac t^4-4c^2 t^6<=2ab.

Since P>=b, (log P)''<=2a/b=14/3. Consequently its discrete second
log-difference on a1/sqrt(m) step is at most14/(3m). On the other hand,
for an internal support point i the EXACT HG ratio gives

    log(nu_i^2/(nu_(i-1)nu_(i+1)))
       >=1/(i+1)+1/(m-i+1)+1/(k-i+1)+1/(3m-k+i+1)
       >=4/(m+2)+4/(3m+2)>14/(3m), m>=16.

The first inequality uses log(1+1/a)>=1/(a+1). For the last, multiply
by m: both terms increase with m, and at16 their sum is1088/225>14/3.
It follows that v_i is strictly log-concave internally. At support boundaries
zero extensions cause no issue. This explicit shape certificate is the
candidate specialization; log-concave rejection sampling itself is classical.

## 4. A fully rational adaptation of classical rejection envelopes

Devroye1987 provides universal discrete log-concave rejection with known
mode/probabilities. The following level-set/geometric version is written
here as an ANALYTICAL CLASSICAL CONTROL/implementation route, not a new
general rejection sampler. It avoids real exponentials and a full table.

Find a mode M by binary search of the monotone rational ratios

    v_(i+1)/v_i=(m-i)(k-i)/[(i+1)(3m-k+i+1)] * P_(i+1)/P_i.

For each side choose the FIRST power of2 T>=1 with v_(M+-T)<=v_M/2,
using zero beyond support. This takes O(log m) weight evaluations. For
distances d<T use relative envelope1, and for d=T+j use

    (1/2) r_T^j, r_T=1-1/(2T), j>=0.

Log-concavity bounds v_(M+T+j)/v_M by
(v_(M+T)/v_M)^(1+j/T)<=2^(-1-j/T)<=(1/2)r_T^j;
the last follows from (1-1/(2T))^T>=1/2. Reflection handles the other side.
The envelope total relative mass is D=2T_left+2T_right-1. Draw uniformly
from the central integer block with weight(T_left+T_right-1)/D, or a
geometric tail with weights T_left/D,T_right/D; accept with v_i/(v_M*hat_i).

The expected number of attempts is at most8. For T>=2, the previous
power T/2 failed the cutoff and all distances1..T/2 have weight>v_M/2,
providing target mass>v_M*T/4. Together with v_M at the mode this gives
D*v_M/sum_i v_i<=8, including T=1 and singleton supports. Rejected points
never query f. A fixed rejection cap would change this law and is NOT used.

Mode/cutoff preparation is O(log m) KNOWN-weight queries and the expected
number of acceptance weight queries is at most8, independently of f.
The normalizer uses four moments. These replace V2's O(m) dense known
proposal sums; no whole-operation speed claim follows from query counts.

## 5. Bits, callbacks, source count and the actual consumer

The number of f-values per complete written output is at most6 (base J=0
still uses3); source N has EXACTLY the classical H-gap law. Equations(2)
give component probability sum<=1417/1470, so

    E f-value calls <=3+1364H/[245 n0^1.5],
    E N=n0+12H/sqrt(n0).                                (3)

All preparation, known probabilities, rejection attempts, fair bits,
geometric draws and rational arithmetic must be charged. Exact binomial
weights can have O(m) bits. With fast multiplication/product trees, each
weight/cutoff/acceptance evaluation has O(m polylog m) bit work; O(log m)
preparation and a uniformly bounded expected number of attempts preserve
that conditional asymptotic order. Exact geometric draws may use dyadic
inversion/power comparisons with expected O(m polylog m) bit work here
(T=O(m)); a loop of T Bernoulli draws is NOT constant time. Neither the
unit-cost density bound nor a Fraction proof oracle implements/proves this
entire fast-bit engine. Full memory/RNG/output/metadata costs remain required.

The ORIGINAL Koskela/Latuszynski/Spano2024 model supplies a real numerical
consumer: generate an ancestral graph before alleles, then sample each
node's colour from its number k of successful parents. Any non-adaptive
factory can replace the paper's Keane--O'Brien rule. Our and the dense
H-gap control have the SAME branching law N and node kernel r_J(k), hence
the SAME joint colours on every finite graph, by induction over its nodes.
No new duality theorem is claimed. The bounded-away-from0/1 subclass here
does NOT model absorbing fixation at both endpoints and does not reproduce
the paper's entire class/examples.

The shared finite mean mu of N also gives the usual pure-branching bounds,
for a initial lineages and per-lineage rate lambda:

    E A_t<=a exp(lambda*(mu-1)*t),
    E branching events<=a[exp(lambda*(mu-1)*t)-1]/(mu-1).

These follow by dominating with a continuous-time Galton--Watson process
and truncation/Gronwall; coalescence only reduces lineages. They imply
non-explosion and finite expected parent/colour work under this bound.
They are CLASSICAL and SHARED with the dense H-gap control, not exclusive
capabilities or a demonstrated flaw in the 2024 paper. The own proposed
benefit concerns node-colour implementation/query/preparation costs.

Global f-grid caching, closed-form/derivative-aware moment integration,
generic signed/importance estimators, retrospective quadrature and any
other valid non-adaptive factories remain competent comparators. For cheap
known splines or many repeated nodes, caching may erase a benefit. No
fabricated slow callback, speed win, new model execution, priority certificate,
human review, paper/admission success or completed user goal is claimed.
