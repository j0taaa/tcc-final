# Written bounded numeral construction, BEFORE code

2026-10-16 local date. Candidate representation theorem, not confirmed priority.
All exact values below are mathematical DECIMALS, not binary64 approximations.
The JSON numeral syntax is

    -?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?

Leading exponent zeros and arbitrary fraction length are retained. Let val(w)
be its exact rational value, and J_I the numerals with val(w) in interval I.
The byte budget L is known BEFORE compiling. A compiler is L-complete if it
accepts precisely J_I on inputs of length<=L and never accepts an invalid
numeral/value at any length. It may reject valid longer inputs. It need NOT
include a separate total-length counter: the decoder supplies that budget.

## 1. Why a fixed unbounded CFG does not express this entire interval

Take I=[1,2). Intersect J_I with the REGULAR syntax family

    R = { 1 0^n e- 1 0^k : n,k>=0 }.

Such a numeral has value10^(n-10^k). It lies in [1,2) iff n=10^k. Thus

    J_I intersect R = { 1 0^(10^k) e- 1 0^k : k>=0 }.

Map every character to a single letter a. The resulting unary language has
length set {10^k+k+4:k>=0}, whose successive gaps9*10^k+1 are unbounded.
An infinite regular unary language has bounded successive gaps (eventual
periodicity); every unary context-free language is regular by Parikh's
theorem. CFL closure under regular intersection and homomorphism therefore
proves J_[1,2) is NOT context-free. This is a standard closure/semilinearity
argument, not an asserted discovery of a new formal-language technique.

It does not prevent semantic predicates, length-dependent grammars, postfilters
or alternate encodings. It does not mean all JSON or all scientific notation
is non-context-free: the SEMANTIC interval constraint is essential.

## 2. Positive construction for fixed 0<a<=b<infinity

Fix finite DECIMAL bounds a,b and endpoint inclusion flags, with a nonempty
interval. Normalize them as

    a=10^alpha*A, b=10^beta*B, 1<=A,B<10.

The significant digit strings of A,B are finite; trailing zeros may be removed.
Let R be their maximum significant length and W=beta-alpha+1. They are fixed
metadata in this theorem. The bound is NOT uniform in encoded bounds' bit
length; see Section5.

Every nonzero positive numeral has a unique normalized value

    val(w)=10^(d+E)*m, 1<=m<10,

where E is the integer exponent (zero when absent), d is the order contributed
by the unexponentiated mantissa, and m its normalized significand.

### Mantissa graph

Use ordinary JSON integer/fraction syntax states, an order counter
d in[-L,L], a significant-digit index capped at R, and two comparison flags
in{less,equal,greater} against A and B. This is O(L*R) states/edges.

For an integer part beginning nonzero, d starts0 and increments for EACH
subsequent integer digit. After '.', d remains fixed. For integer0 followed
by '.', set d=-1; each fractional zero BEFORE the first nonzero decrements
d, and the first nonzero freezes d. Reject all-zero mantissas because a>0.
Keep JSON's prohibition of extra leading integer zeros. Reject overflow of
the declared counter interval; a word of length<=L cannot overflow it.

Ignore the decimal point while feeding significant digits to the two finite
lexicographic comparisons. Missing bound digits are0. If comparison is still
equal when the mantissa ends, pad its missing digits with0 against the bound's
remaining finite suffix. A remaining nonzero bound digit makes m smaller;
otherwise equality remains. Once the capped index reaches R, later nonzero
digits can still change equal to greater (the bound's remaining digits are0).
The index cap does NOT truncate the allowed mantissa precision.

At each completed mantissa state the final comparisons C_a,C_b are known.
The EXACT allowable exponent interval is

    lo=alpha-d + 1{C_a<0 or (C_a=0 and lower endpoint excluded)},
    hi=beta-d  - 1{C_b>0 or (C_b=0 and upper endpoint excluded)}.

Discard it if lo>hi. With no written exponent, accept iff lo<=0<=hi. With
'e' or 'E', permit precisely the INTEGER values E in[lo,hi]. There are at
most W+1 such integers, a fixed constant. This follows by comparing orders
first, then significands only when the order equals the relevant bound order.

### Shared exponent graph

All required E satisfy |E|<=K=L+max(|alpha|,|beta|)+1. For each required E
create a start with the appropriate optional plus/required minus sign and
arbitrary leading exponent zeros, then the canonical nonzero decimal digits
of |E|. E=0 instead accepts0+, with absent/plus/minus sign. No exponent is
permitted to be empty. Use separate leading-zero states and finite literal
tail states: an internal zero is NOT a new leading-zero loop.

Intern equal remaining digit suffixes across the canonical integer strings.
There are O(K) distinct suffix strings: for each width r there are at most
10^r, and sum_(r<=floor(log10 K))10^r=O(K). There are O(K) exponent starts.
The graph thus has O(K) states/edges. Connect every completed mantissa state
after consuming e/E to its admitted exponent starts by epsilon edges, with
O(W+1) alternatives per state. End-of-number is a unique accepting sink.

TOTAL states AND edges are O(L*R*(W+1)+K)=O_I(L) for a FIXED interval. Counts
do not enumerate all strings/values or constrain fraction/exponent spelling
to a canonical form. Sharing suffix states does not rewrite any input byte.

### Soundness, bounded completeness and unambiguity

Mantissa syntax/order/comparison states are deterministic. Every completed
mantissa has its actual d,m comparisons. The displayed lo/hi equivalence is
exact, and the exponent graph accepts precisely those integer values with
all legal sign/leading-zero spellings. Every accepted word is therefore in
J_I, at ANY length. A word in J_I of length<=L cannot overflow d, has an
admitted E, and follows an accepting path. This proves L-completeness.

For each fixed word, its mantissa boundary and d/comparisons are unique. Its
written exponent determines exactly ONE chosen E. Leading zeros before a
nonzero canonical exponent are uniquely separated;0+ has a single path.
Each canonical tail has one literal path, despite suffix sharing. Absence
and presence of an exponent consume different strings. Hence every accepted
word has EXACTLY ONE accepting path. This is an UNAMBIGUOUS epsilon-NFA;
no determinization or dense epsilon-elimination bound is asserted.

## 3. Matching lower bound, including arbitrary nondeterministic automata

Again I=[1,2). For integer k=1,...,floor(L/2), let

    u_k=1 0^k, v_k=e- dec(k).

For all sufficiently large L, every u_i v_j in this set has length<=L.
Its value10^(i-j) belongs to I iff i=j. This is a fooling set: on an
accepting path for each u_k v_k choose a state immediately after the prefix
u_k (epsilon transitions may be assigned consistently at that cut). If two
cuts shared a state, prefix/suffix splicing would accept u_i v_j for i!=j,
contradicting soundness on the bounded domain. Therefore ANY epsilon-NFA
with the required bounded agreement needs Omega(L) states. The construction
above attains O(L), including O(L) edges, for this fixed interval.

The fooling-set technique is classical. The specific numeral application and
matching bound are written claims to audit, NOT verified academic priority.

## 4. Link to structured dLLM infilling, preserving original IDs

Let original ID v emit bytes s(v), including aliases; n token slots have
known nonnegative weights w_iv. Fixed slots are singleton supports. Let
L be at least the maximum emitted byte length of every supported n-slot
word, including fixed context. Lift the UNAMBIGUOUS byte automaton to token
edges and compose fixed JSON delimiters as needed. A consistent epsilon
ownership convention is required, e.g. closure BEFORE each consumed byte
and final closure ONCE. Do not count epsilon closure both before AND after
every token boundary; that can multiply accepting paths incorrectly.

The weight of accepted token sequence v_1...v_n is exactly prod_i w_i,v_i,
because its byte word has exactly one accepting path. Thus conventional
weighted-automata sum-product gives its mass, original-ID marginals and
conditional sampling whenever total mass is positive. Aliases remain
different token sequences with their own weights; no numeric/text
canonicalization is applied to payloads. Empty conditional support must be
reported, never replaced with an arbitrary valid number.

This conditioning/inference principle is already present in ODD/FactorDLM;
it is NOT our theorem of a new posterior law. Original EOT/PAD and variable
length must be composed explicitly before any native decoder claim.

An infill such as fixed1.5e- with a single-digit hole admits2 in
[0.01,0.02). A frontend that excludes exponent forms declares this fixed
prefix incompatible. The bounded complete compiler retains it and preserves
any other positive-weight valid completion. This is a capability corollary,
not a speed/quality result or a claim against ALL semantic engines.

## 5. Costs and unresolved comparisons

The O_I(L) theorem fixes interval metadata. If bounds are inputs with huge
encoded orders or many significant digits, those constants cannot be free.
A straightforward alternative builds a signed integer-interval automaton for
each mantissa state's lo/hi in O(D) states, where
D=O(log(L+|alpha|+|beta|+2)) decimal digits. Standard length/lexicographic
integer comparison handles that finite interval in O(D); sign/leading-zero
branches are disjoint. This gives O(L*R*D) graph size plus bound normalization,
instead of enumerating W potentially exponentially many integer values.
Its uniform bit-cost implementation and exact constants are not yet audited.

Even the linear byte graph may have large constants. Token lifting can create
dense transitions; epsilon elimination may create quadratically many edges.
Sparse epsilon-DAG scanning, generic digit/register DP, shared regex/DFA
construction, symbolic constraints and existing numeric parsers are competent
comparators. There is NO written claim that they cannot obtain the same
bound. A direct known compact construction would remove a generic algorithmic
novelty claim. A resource/quality campaign is not triggered by this note alone.

The next allowed prototype is a minimal independently checked [1,2) compiler
and rational oracle. No trained model, fresh forward, experimental win,
verified priority, sufficient publishability or achieved goal is asserted.
