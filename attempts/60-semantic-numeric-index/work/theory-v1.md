# Written semantic numerical index, before a normalizer prototype

2026-10-17. Candidate construction/analysis, not verified priority or useful
runtime. Classical weighted composition and prefix unranking are credited.

## 1. Source, meaning and exact target

Let A be a finite acyclic weighted byte source. Its accepting paths retain
their ORIGINAL token-ID trace; every admitted trace occurs once with weight
prod_i w_i,v_i, with nonnegative finite rational weights. Different traces
may emit the same bytes (token aliases/segmentations) and must be summed.
Fixed slots are singleton supports. Source epsilon arcs may represent empty
emissions, but must make acyclic progress. Its S states/E edges include the
actual tokenizer expansion, not an assumed free neural head.

Let L bound the emitted numeric bytes of every source path. Keep exact JSON
numerals whose mathematical decimal value lies in fixed0<a<=b<infinity,
with declared endpoint flags. Let Z be their total path weight. If Z=0,
return EMPTY; no statistic or valid replacement is fabricated. Otherwise

    P(value=x) = sum_(original traces with val(bytes)=x) weight(trace) / Z.

This is the semantic image of a declared frozen product/weighted source.
It is not a calibrated data-generating posterior or the law of the final
iterative neural decoder. Binary64-rounded semantics is a different contract.

Normalize a nonzero value uniquely as10^k*m, 1<=m<10. Let s be the finite
digit string of m with its dot removed and all trailing zeros removed. Its
first and last digits are nonzero. For the fixed order band alpha..beta,
encode k by a fixed-width monotone code h(k), then concatenate s:

    key(x) = h(k) || s.

This is injective and lexicographically increasing in x. For a common k,
the first differing significant digit decides; if one s is a proper prefix,
the longer canonical s eventually has a nonzero digit and denotes a larger
value. No trailing-zero alias remains in the key. For [1,100), h(0)=a and
h(1)=b suffice; a1 is1, a15 is1.5, b1 is10 and b9 is90.

## 2. A small functional UNAMBIGUOUS normalizer

Begin with the positive power-of-ten envelope for the fixed requested band.
Guess the normalized order k in its W possible orders and output h(k) before
reading input. The guess is verified by the exponent later, not sampled with
a new probability. Every transducer edge has weight1.

Track JSON integer/fraction syntax and mantissa order d in[-L,L]. For an
integer beginning nonzero, d starts0 and increases on subsequent integer
digits. After the dot it stays fixed. For integer0 followed by dot, d starts
-1 and decreases through fractional zeros before the first nonzero. These
leading zeros/dot emit nothing; every significant digit then emits its digit.

To remove trailing zeros without storing the whole mantissa, nondeterministically
choose its last NONZERO digit while consuming that digit. Emit the digit and
switch to a mode allowing only zero mantissa digits thereafter, emitting
nothing for them. The decimal point and syntax/order bookkeeping remain
active. A branch that chose an earlier nonzero dies on the next nonzero.
A branch that never chose a last nonzero is rejected at mantissa end.
Thus exactly ONE choice survives for any nonzero mantissa.

At mantissa end require E=k-d, with E=0 when absent. Explicit e/E uses the
actual signed decimal exponent, with mandatory minus for negative targets,
optional plus for positive targets, either/absent sign for zero and arbitrary
leading exponent zeros. E=0 still needs at least one exponent digit. Validate
these fixed targets with shared literal suffix states and separate leading-
zero loops. E validation emits nothing.

There are O(W*L) syntax/order/mode states. For fixed order metadata, the
targets k-d have O(L) distinct remaining decimal suffixes: suffixes of width
r number at most10^r, a geometric sum up to log(L+C). Together with the
per-target leading-zero/sign starts, the normalizer has O_I(L) states AND
edges. It is globally sound; rejecting counter overflow loses no input of
length<=L. It need not reject every longer valid numeral.

Every accepted input has unique k, unique last nonzero and unique exponent
spelling path, hence one output and one accepting normalization path. That
output is key(val(input)). Deterministically intersect the output with the
requested key interval to enforce non-power-of-ten endpoints; its fixed bound
digit lengths add metadata-dependent states. Do NOT silently treat huge or
variable precision bounds as constant in a uniform bit-complexity claim.

This is a functional unambiguous NFT construction, not determinization of
all numeral spellings. No claim that counters/suffix sharing/trailing-zero
transductions are new is made. The complete construction still needs checking.

## 3. Composition, aliases and epsilon ownership

Compose A with this normalizer and project onto output keys using the standard
probability semiring. If EOT/PAD/empty tokens introduce source epsilons, use
an explicit epsilon filter. In the special construction with input epsilon
only for the initial order-header guess, force that guess BEFORE any source
progress; later source epsilon arcs advance A while the normalizer stays put.
This is a canonical ownership convention, not permission to count every
epsilon interleaving. Generic filtered composition is a mandatory control.

The product has O_I(S*L) states and O_I(E*L) edges for fixed byte alphabet and
bounded transducer branching. It is acyclic: input-consuming loops advance
the finite acyclic source, and the initial header moves only forward. Splitting
multi-character output labels must count the resulting states/edges too.

For each original source path there is exactly one accepted normalization
path iff its numeral belongs to the declared domain. Therefore for every key

    weight_index(key) = sum_(original source traces mapped to key) weight(trace).

Output ambiguity from DIFFERENT original traces is intended aggregation,
including lexical spellings and original token aliases. It is not an
extra grammar-derivation multiplicity. Z is unchanged by composition.
This identity is a standard composition consequence once the specific
normalizer is sound/unambiguous; it is not a new posterior law.

## 4. Exact CDF and quantiles without listing the support

Let B be the resulting weighted output DAG, with M edges. Precompute suffix
mass beta(q)=final(q)+sum_(q--c/w-->r) w*beta(r), including epsilon edges,
in reverse topological order. This is O(M) arithmetic operations.

Given a key prefix, retain the forward mass vector alpha immediately after
its last nonempty output character. Compute output-epsilon closure BEFORE
the next character/termination only. For each next character c its block
mass is the sum of alpha(q)*w*beta(r) over matching first nonempty c edges
after that closure. Terminating mass is the closure's final-state mass.
Each path then has exactly one next event: terminate or one next character.
This partitions the prefix mass without counting epsilon placement twice.

For probability p in(0,1], keep an exact rank p*Z. Visit terminating mass
FIRST, then character blocks in lexical order, subtracting preceding blocks.
Choose the first block whose inclusive cumulative mass reaches the rank.
Update alpha for the chosen character and continue. Termination returns the
smallest numerical value x with F(x)>=p, including exact atom-boundary ties.
Canonical keys have length O_I(L), so this uses O(R*M) arithmetic operations
for a returned R-character key. A CDF query similarly accumulates lesser
blocks along its threshold key. Z=0 is handled before any rank operation.

Weighted prefix enumeration/inverse CDF is classical. Determinizing B can
be exponential and is NOT required. Nor is a table of all distinct numerical
values. Actual sparse closure/cache costs and memory must be measured.

## 5. Comparative bounds, and the stronger control that can remove them

A complete fresh numeric comparison DP with a threshold of R significant
digits can have O_I(L*R) comparison/order states. Composing and evaluating
it anew for each digit of a quantile gives the elementary upper bound
O_I(E*L*R^2), while the proposed index gives O_I(E*L*R) after preparation.
This is a comparison of THESE implementations, NOT a lower bound on every
complete CDF/quantile algorithm. Direct queries may be preferable for few
queries or when the product index is large.

A complete register implementation with semantic-prefix frontier caching,
or generic lazy WFST output projection, can achieve the SAME reuse as the
index. It must be supplied as a competent comparator. If it matches all
useful costs, a generic own speed claim is unsupported. The remaining
candidate would be only the specific normalizer/operator/application; its
originality and significance require a separate substantive assessment.
No experimental campaign is triggered by the quadratic-vs-linear upper bound.

## 6. A restricted state separation, not a general inference lower bound

For [1,100) consider inputs1.w e0 and1.w e1, where w has m digits from{1,2}
and m+4<=L. Their keys start with DIFFERENT first characters a and b.
A deterministic single-pass subsequential transducer producing these canonical
keys cannot emit anything before reading the distinguishing exponent digit.
After each prefix1.w e it must therefore retain w in its state. If two
different w shared a state, appending0 would require different final outputs
from the same state with identical previous output, a contradiction. Thus
it needs at least2^m states, whereas the unambiguous construction is O(L).

This is the classical delayed-last-symbol separation applied to this key
encoding. It does NOT prove new generic transducer theory, a lower bound on
all numeric inference, or an exponential bit-memory benefit for normalizing
ONE number. A streaming string-register program can store that number in
O(L) bits; multipass and source-aware algorithms remain legitimate controls.
The potential benefit concerns a weighted representation of ALL source paths.

## 7. Bits and a decision corollary

If original slot weights are dyadic with denominators at most2^b, n slots
and V IDs per slot, path sums have O(n*(b+log V)) bits under a common dyadic
denominator. Epsilon filtering/unambiguous normalization adds no artificial
path factor. Rank probabilities add their own bit lengths. A graph entry
still needs O(log(S*L)) index bits. Exact real values need O_I(L) digit bits.
These are finite rational costs, not constant-time exact arithmetic or a
floating-point/native RNG equality assertion.

A median minimizes EXPECTED absolute numerical error under P; this is the
classical Bayes decision, not a new proper-scoring theorem or ground-truth
accuracy guarantee. A constructed one-slot source illustrates alias effects:

    P("90")=.4, P("1")=.3, P("1.0")=.2, P("1e0")=.1.

Word MAP predicts90. The induced numerical law has mass.6 at1 and.4 at90;
its median is1. Its subjective expected absolute error is35.6 instead of53.4.
These are mathematical example values, NOT model/benchmark measurements.
Uncalibrated P may still be a bad predictor; the index does not fix that.

## 8. Scope and missing evidence

Fixed positive finite bands have finitely many decimal orders. An interval
including0 admits arbitrarily tiny nonzero values with very large negative
orders even in short scientific strings; it does not inherit this simple
finite-order guess. Negative/cross-zero bands, arbitrary recursive JSON-field
extraction, EOT/PAD/native bindings, numerical rounding and a source-graph
resource protocol are still separate obligations. No masked model/global
decoder/statistical calibration claim follows from the written construction.

Before extensive implementation, require an actual useful difference beyond
generic cached WFST machinery and read the outstanding exact-quantile
antecedents. First permissible code is a MINIMAL independent relation/mass/
quantile oracle, not a production decoder, head kernel or model campaign.
