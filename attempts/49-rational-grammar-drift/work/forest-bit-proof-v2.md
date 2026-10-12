# Deterministic rational TV certificate on an admitted event forest

Written proof,2026-10-12. The approximation principle and admissible-gate
composition are Fu2609.24235's antecedents. This is NOT a priority claim or
proof of the Python compiler. The theorem below concerns an EXPLICIT admitted
forest. The original-grammar compilation obligation is separated below.

## 1. Contract independent of Python

There are n finite domains S_i of ORIGINAL token IDs, two nonnegative rational
tables p_i,q_i with row sums<=1, and a common finite set F of valid assignments.
Both Z_p=sum_{y in F}prod_i p_i(y_i) and Z_q are positive. The distributions
being compared are P(y)=prod_i p_i(y_i)/Z_p and Q analogously. They are frozen
product predictions conditioned on F, not the full learned neural joint law.

An admitted event forest is an acyclic binary sum/product circuit. Each node
has a fixed scope I, a finite set of assignments of its scoped positions and
their paired product weights. A leaf either lists original choices at one
position or is an empty-scope unit/zero. At a product, scopes are disjoint and
events form a Cartesian product. At a sum, scopes agree and the event sets
are DISJOINT. Its root event set is exactly F, with each assignment appearing
ONCE. Productions have no extra learned weights. Empty-scope nodes reduce to
unit/zero. There is no assumed common v-tree: product splits may differ across
sum alternatives. This is an admission hypothesis, not a property tested by
looking only at numeric masses.

Let H count nodes and wires, and d be the maximum number of compression gates
in an expanded root derivation. Use d=1 for a singleton root requiring none.
The recurrence is max(child costs)+1 at a compressed sum and sum(child costs)+1
at a compressed binary product; exact leaves/unit/zero have cost0. With fixed
nonempty scopes, no node can occur twice in one derivation: their lowest common
ancestor would be a product whose disjoint scopes both contain that nonempty
scope. Acyclicity excludes repetition along one chain. Thus d is polynomial,
in particular bounded by the explicit nonempty gate count. Unrestricted
arithmetic DAG repeated squaring does NOT satisfy this contract.

## 2. Scaling and algorithm

For each head separately, D_i is the LCM of input denominators at position i.
Replace p_i(v) by integer a_i(v)=D_i*p_i(v) and q_i(v) by integer b_i(v) with
its own denominators. Common per-position denominators cancel in the root
normalizations. Compute EXACT positive integer normalizers A,B by ordinary
inside addition/multiplication; these are not read from compressed generators.

At a leaf keep the paired integer vectors(a_i(v),b_i(v)). At a disjoint sum
concatenate the child generator lists. At a product list every componentwise
product of a left/right generator. After each internal gate apply the planar
compression of V1 with N=ceil(16d/epsilon), epsilon rational in(0,1]. Output
generators may be SIGNED. They are norm representations, never probabilities,
token samples, or positive semantic mixtures.

At the root with compressed rows c_j return

    L = sum_j |B*c_j[0]-A*c_j[1]|/(2*A*B),
    U = min(1,(1+epsilon)*L).

## 3. Correctness for every input and arbitrarily small TV

For exact generator family G at any node, F_G(w)=sum|g dot w|.
At a sum, disjointness gives the norm SUM of the child norms. Their common
lower factor is at least the smaller child factor. At a product, fix a right
row h and query the left family with w componentwise times h. V1 holds for
EVERY real query, including signed ones. Sum over right rows, then apply the
right invariant using each retained left row as a multiplier. Thus child
lower factors MULTIPLY, while the upper factor remains1. A local compression
adds another factor1-8/N. Induction gives

    (1-8/N)^d F_exact(w) <= F_compressed(w) <= F_exact(w).

At w=(1/A,-1/B), the exact norm is2*TV(P,Q). Since8/N<=epsilon/(2d), Bernoulli's
inequality gives (1-8/N)^d>=1-epsilon/2>=1/(1+epsilon). Hence

    L <= TV(P,Q) <= U <= (1+epsilon)L.

For TV=0, L=U=0 exactly. No minimum positive TV, nonzero probability floor,
conditioning-mass floor, numerical cancellation assumption or sampling failure
probability is used. If either normalizer is zero, TV is UNDEFINED and the
operation must refuse; it must not replace that case by a zero certificate.

## 4. Complete integer bit cost on this admitted representation

Let ell be the total input bit length of both rational tables, domains, forest
and epsilon. Each log D_i is at most the sum of input denominator bit lengths.
At an exact scoped node, its mass under either integer head is at most
prod_{i in I}D_i: its events are a subset of distinct scoped assignments and
sum_v a_i(v)<=D_i. Thus the mass has O(ell) bits. The SAME bound applies to
the absolute coordinate sums of compressed rows: evaluate the all-query norm
invariant at either coordinate axis. Product/union intermediates obey this
bound too before their local compression.

Compression outputs are sums of SIGNED INPUT integers. Polygon vertices have
O(ell+log m) bits for m input rows; determinants/cofactors and the integer
bucket divisions have O(ell+log m+log N) bits. No output coordinates are
rounded, no square root/inverse-square-root oracle is used, and no rational
denominators accumulate inside compression. The final numerator/denominator
and rational upper bound have polynomial bit length as well.

Each compressed list has at most M=2(N+1)=O(d/epsilon) rows. Exact leaves may
have V original rows, so put K=max(V,M). A binary product has at most K^2
candidates; a sum with f children has at most fK candidates.
The current simple compression costs O(m^2) integer determinants plus sorting
and O(m) divisions. A conservative total
bound is O(H*J^2*poly(ell+log J+log N)) bit operations and polynomial storage,
where J=HK+K^2. This includes leaf-domain costs even when V is large.
The LCMs, exact normalizers and reading the representation are included.
This is a polynomial BIT bound, not a strongly polynomial bit algorithm or
a claim of low latency. The coarse runtime can be substantially worse than
a specialized product/Markov algorithm or an exact small enumeration.

## 5. Word-faithfulness and grammar preparation: separate obligation

For a nonambiguous grammar and a deterministic original-token lattice, a
complete accepted token assignment determines ONE lattice path and ONE parse.
Token aliases remain distinct closing edges, even if their bytes agree; a
token prefix of another keeps its own closure. In a byte-span chart, scopes
are the positions whose closing edges occur between its endpoints. Product
scopes partition these positions. Local sum alternatives must be disjoint
under the original closing-ID assignment, not merely under a parse-tree tag.

The standard unambiguous CFG/lattice chart can therefore supply the required
forest WHEN these properties and acyclicity are established. A fixed-tree
WTA is not enough, and the current normalizer is not mechanically verified.
The maintained compiler's admission/normalization costs must be measured or
bounded separately; its original-source correspondence normalization still
has an explicit work budget, not a claimed unconditional polynomial bound.
V2 therefore proves the certificate for the admitted forest and does NOT
quietly claim an end-to-end polynomial bound for all source-grammar APIs.

Next obligations: check scopes/multiplicities independently on real compiled
tiny forests including macro/alias tokens; formalize a source-to-forest
construction or retain the forest-input theorem honestly. Audit whether this
is a useful scientific difference from rational forms of standard geometry.

## 6. Application and comparative limits

If U<=tau, replacing P by Q at this step changes the expectation of any
verifier f in[0,1] by at most tau. A common continuation kernel cannot increase
TV. Along a finite iterative decoder with conditional per-state bounds tau_t,
the usual coupling/union argument bounds trajectory TV by sum_t tau_t. These
are classical consequences, not a semantic or speed improvement theorem.

EPIC solves a different proposal/acceptance law; this certificate is not its
probability evaluator. Exact posterior, ordinary PC inference and exact
Hellinger/KL bounds remain competent alternatives. The new candidate is a
rational certified operation, not a declaration of superior generation.
