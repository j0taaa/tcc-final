# V7 — A complete direct-CDF control removes the generic capacity justification

2026-10-17. Written after V6's tiny correctness oracle, before any native/head/
timing campaign or implementation of this control. All eight V5 criteria are
reassessed here: the useful OPERATION remains, but its claimed architecture
gap must not be mistaken for a gap against all complete numerical methods.
This is classical monotone search plus bounded digit comparison, not a new
quantile principle or confirmation of A60's publication significance.

## 1. A complete power-of-ten comparison needs no universal normalizer

Let C(t) be the UNNORMALIZED source mass of nonnegative JSON numbers x<10^t,
where t is a signed integer with O(L)bits. Compute zero mass separately by the
constant-size zero grammar. For a positive numeral, its decimal order is d+E.
The mantissa lexer tracks syntax, whether a nonzero was seen, and order d in
[-L,L]. No full significand, output reordering or trailing-zero guess is needed
to test d+E<t. Integer digits increment d after the first; fractional leading
zeros decrement it before the first nonzero. This has O(L)states.

At an e/E marker, enter an ordinary exact signed-integer comparator accepting
the exponent string E iff E<T, T=t-d. Without an exponent, test0<T. Leading
exponent zeros and either zero sign are legal; lexical sign/digit requirements
are not optional. The positive/zero source languages are disjoint.

For ONE target T, compare signed magnitude by stripping leading input zeros,
then comparing canonical digit length and lexicographic digits. The DFA uses
O(1+digits(|T|))states: before a first difference, retain the target suffix;
after a first difference, retain its direction and the remaining target width.
At end, shorter/longer digit width overrides a within-width difference. Extra
input digits go to a single larger-magnitude state; exponent zero is explicit.
Negative signs reverse the signed inequality. These are standard digit-DP
states; arbitrary huge input exponents are accepted/rejected, not truncated.

There are2L+1 targets T. Even WITHOUT shared suffixes their total size is
O(L*(L+1))=O(L^2), since t and every t-d have O(L)decimal digits. Once the
mantissa ends, its order need not remain as another counter: its chosen target
comparator carries the required condition. The source product therefore gives
C(t) in O((S+E)L^2) arithmetic and space. This is a complete numeral test for
the requested strict threshold, including exponents of arbitrary magnitude
within the source byte bound. A generic register/automata library can implement
it using classical comparison states.

## 2. Localize the quantile ORDER in O(L) calls

Let Z be total nonnegative-number source mass (the ordinary lexical-number
grammar plus signed zero suffices), z0 its zero mass, and rank=pZ>0.
If rank<=z0 return0. Otherwise let K=10^(L+1), represented in O(L)bits.
All admitted positive orders lie strictly between-K and K. Binary search the
integer k for the first predicate

    C(k+1) >= rank.

It is monotone, false below the supported order range (rank>z0), and true
above it. At most O(log K)=O(L) strict-CDF calls identify the smallest such k.
This is the decimal order of the left-continuous quantile, INCLUDING exact
atom-boundary ties: C(k+1) includes every atom in order k, and no atom at the
next order's lower boundary. If an earlier order already reached the rank,
the binary search would have selected it. Empty orders create no ambiguity.
The subtraction rank-C(k) is now the positive rank within order k.

The huge INTEGER SEARCH RANGE does not mean exponentially many probes.
Only O(L)bits/decisions are needed. No actual10^k or huge real denominator
is constructed. All threshold predicates operate on t=k or k+1 directly.

## 3. Compile ONLY the selected order, using V1's classical trimming idea

Use V1's one-order relation: emit its canonical significand, count mantissa d,
and check the exact exponent target E=k-d. Last-nonzero selection is uniquely
verified; original aliases and token paths sum as before. There are2L+1 exact
exponent targets, each with O(L)digits. Even WITHOUT suffix sharing the whole
normalizer has O(L^2)states/edges. No claim of V1's fixed-metadata O_I(L)
constant is being applied uniformly to a huge variable k.

Compose with the ORIGINAL source, respecting input epsilons, to get a
significand-key weighted DAG of O((S+E)L^2)size. Classical weighted prefix
unranking with local rank rank-C(k) takes O(L)steps, hence

    O((S+E)L^3) arithmetic total for one complete global numerical quantile.

Space is O((S+E)L^2), plus rational coefficients/rank bits. Preparation for the
direct-CDF probes is sequential and discarded/reused. Bit bounds are V5's
nonnegative source-path bounds, and all original-token construction, probes,
selected-order compilation and queries are charged. Fixed output (s,k) stays
compact. Multiple ranks can share threshold results and order-specific indices;
their real tradeoff against a global index needs a fair full-cost protocol.

## 4. Consequence for the candidate and next action

This explicit complete classical control has a polynomial upper bound for
the SAME unrestricted numerical operation. Its bound even avoids V5's coarse
factor B for all possible source marker cuts. This is an UPPER-bound comparison,
not a lower bound, implemented timing, measured dominance, or published priority
claim for this exact specialization. It neither invalidates V5's exponential
ONE-WAY UNIVERSAL-NFT lower bound nor proves that V5 cannot win in some regime.

It DOES invalidate using that restricted lower bound as evidence that classical
complete numerical inference must be exponential. A source-independent normalizer
for ALL orders was an unnecessary intermediary: localize the order first.
Likewise, merely implementing a classical localized control would not create a
new general quantile algorithm or fulfill the positive user goal.

V5/V6 are retained as checked mathematical/software artifacts; their specific
normalization/statistics specialization may still merit a scoped study, but
an own substantial useful advantage has NOT been established. Do not trigger
native/full-V/training/timing work from the capacity family alone. First find
a concrete useful consequence beyond these complete controls and verify its
specific literature/consumer contract. No new forward, label or model update.
