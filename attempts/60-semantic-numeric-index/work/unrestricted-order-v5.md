# V5 — Source-conditioned numerical ordering without a fixed positive band

2026-10-17. WRITTEN before any V5 prototype/capture/timing. V1--V4 stay literal.
This is a candidate positive construction, not confirmed academic priority or
practical performance. Cyclic shift, digit arithmetic and prefix queries are
classical. The source-conditioned representation is the possible consequence.

## Eight-criterion reassessment

1. Same real operation: numerical quantiles of a finite frozen-head source,
   now over ALL nonnegative JSON numbers, not a band bounded away from zero.
   Arbitrarily large/small scientific exponents are retained. A typed numerical
   distribution consumer can request quantiles without inventing a minimum
   positive value or enumerating magnitude values. Actual usefulness of this
   head-local law in a dLLM consumer remains unvalidated; not its iterative law.
2. Candidate distinction: polynomial source-conditioned value-key index while
   every source-INDEPENDENT one-way NFT for the same bounded normalization
   relation needs exponentially many expanded states. This strengthens V1's
   deterministic-only restriction. The generic block-reordering argument is
   classical; priority of this numerical specialization is OPEN. Maslov's
   classical cyclic-shift construction ALREADY provides the source cut, and a
   complete classical implementation is a mandatory equal-capacity control.
3. Potential advantage is complete numerical capacity with polynomial size,
   compared with a one-way normalizer compiled first and then composed. It is
   NOT a lower bound on source-aware, register, multipass, cyclic-shift or all
   numerical-inference algorithms. No measured useful gain versus all competent
   controls. A fixed-band input should still use the smaller V1 construction.
4. Theorems/construction below precede code. They include a path-weight bijection,
   polynomial arithmetic/bit costs, compact quantile output and a consequence
   for representing all source paths. No Lean or independent human review.
5. First permissible code is a tiny rational source oracle for exponent addition,
   zero, original aliases/cuts/empty bytes, mass and compact quantile boundaries.
   No performance/model campaign before equally complete classical controls and
   a substantive own useful consequence. Large exponents may exceed Decimal's
   exponent limit; independent JSON lexical parsing plus integer arithmetic
   must retain them without casting to float or constructing10^(huge exponent).
6. Charge original-token byte expansion, all candidate e/E cuts, input-epsilon
   ownership, order arithmetic, key width, suffix sums and queries. The coarse
   source-cut bound can be impractically large. Output is an exact compact
   scientific pair, NOT an exponentially expanded integer/Fraction, binary64
   value, calibrated uncertainty or a native-RNG trajectory.
7. Fatal objections: direct classical cyclic shift plus a bounded digit adder
   may already yield the useful result. Reordering source factors requires a
   commutative scalar semiring; multiplying head probabilities on revisits would
   change the law. A more compact direct comparison algorithm may win. A consumer
   may only need binary64 rounding or few approximate samples, at much lower cost.
8. Need audit of specific priority, an actual consumer, useful complete-cost
   comparison and native integration before article promotion. A correct small
   prototype or restricted architecture lower bound does not meet the user goal.

## 1. Input and compact output

A is a finite acyclic byte source with S states/E edges, original-ID traces,
nonnegative rational weights, one initial/final state (multiple ones can be
joined by explicit epsilon arcs), and known maximal emitted length L>=1.
Empty source arcs make DAG progress. Byte expansion/weight placement is part
of the input and must retain original token identity even inside tokens.

Keep valid JSON numerals with exact mathematical value>=0. Negative nonzero
values are outside this refinement; -0 and its scientific spellings denote0.
For x>0 write x=10^k*0.s*10, where s has nonzero first/last digit and no dot.
Return (s,k), the normalized significand digits and decimal ORDER. Zero has
the unique compact representation(0,0). No expansion of10^k is required.
If text length<=L then |k|<10^(L+1), since |E|<10^L and mantissa order |d|<=L.
The signed integer k has O(L)bits even if the represented number would need
exponentially many digits or denominator bits.

Set R=L+1. Define h_L(k), length R+1, by

    k>=0: '1' || zero_pad_R(decimal(k))
    k<0:  '0' || nine_complement(zero_pad_R(decimal(-k))).

Negative zero is forbidden in this order code. Define key(0)='0' and
key(x>0)='1'||h_L(k)||s. These are injective and lexically increasing:
negative orders reverse magnitude; positive orders preserve it; at equal
order canonical significands compare lexically, with a shorter proper prefix
representing a smaller value. Every key has length<=2L+3.

## 2. Why a source-independent ONE-WAY NFT can be exponential

This is an explicit numerical instance of the classical block-swap obstruction.
Assume a letter-expanded one-way NFT realizes EXACTLY this relation on all
JSON inputs of length<=L. It may be nondeterministic and output epsilon; do
not assume a deterministic state or unique path. Its description size includes
states inserted by expanding multi-character labels. Initial/final output
strings can likewise be expanded. Behavior outside the budget is irrelevant.

Let L=2m+4 and let w,v range independently over{1,2}^m. Take the input

    '1.' || w || 'e1' || v.

Its mantissa order is0, exponent/order is the integer represented by'1'||v,
and its significand is'1'||w. Thus output is H(v)||'1'||w where H(v) is the
positive prefix and fixed-width order code. All these keys have equal length
and H(v) has a common length H and distinct content for each v.

Choose ONE accepting path for each(w,v), and cut immediately after the final
input digit of w, before the marker e. Call it EARLY if at least H output
characters have already been produced; otherwise call it LATE.

For a fixed w, two EARLY paths with different v CANNOT share their cut state.
Splicing the prefix of one with the suffix of the other accepts the latter's
input with the former's already complete, wrong H(v) output prefix.

For a fixed v, two LATE paths with different w CANNOT share their cut state.
Their produced outputs are prefixes of the SAME H(v). If prefix lengths differ,
splicing changes total output length, whereas all keys in this family have
equal length. If lengths agree, the prefixes agree, and splicing returns the
other w's wrong significand for the first input. Both are contradictions.

If some v has at least2^(m-1) LATE partners w, the second observation requires
that many states. Otherwise more than half of all pairs are EARLY, so some w
has at least2^(m-1) EARLY partners v, and the first observation gives the same
bound. Hence expanded NFT size is>=2^(m-1)=2^Omega(L).

This is NOT an exponential bound on all numerical inference or normalizing
one observed number in a register machine. It only rules out a compact universal
one-way relation for this input/output order before inspecting the source.
Changing the key order may remove the bound while also removing direct numeric
prefix unranking. Equivalent classical source-aware approaches remain valid.

## 3. Rotate at the ORIGINAL source's exponent-marker edge

For each ORIGINAL byte edge b=(p,e-or-E,q) with weight w_b, split a source path
as prefix P to p, that edge, and suffix Q from q to the source final state.
Process Q FIRST, then P. The scalar path weight is

    w_b * weight(Q) * weight(P) = weight(P) * w_b * weight(Q).

The source interface p/q is retained. Recombining any prefix ending at p with
any suffix starting at q reconstructs a valid original source path through b.
Every positive valid numeral with an exponent has EXACTLY one marker, so it
has one cut, not one per arbitrary cyclic rotation. Mid-token byte states must
retain the token branch; cutting bytes is not permission to combine halves
of distinct original tokens. Charge the token weight once where originally
placed. A source empty-emission arc also belongs to exactly one side.

This is the marked weighted specialization of the CLASSICAL middle-state
factorization for cyclic shift. No new closure theorem is claimed. The input
probabilities commute; an arbitrary noncommutative annotation need not.

No-exponent positive numerals use a separate branch with E=0. Zero uses the
ordinary constant-size lexical zero grammar, including signed zero and arbitrary
exponent digits; its total source weight contributes once to key'0'. These
three source languages are disjoint, so their union creates no new multiplicity.

## 4. Exponent-first: a bounded DIFFERENCE, not a huge order enumeration

For the suffix exponent text, its sign s_E is read from the source (absent=+).
Guess sign s_K of k, output the first character of h_L(k), then generate its
R absolute-magnitude digits a_j. For s_K=-, emit9-a_j; reject all-zero magnitude.
Align source exponent magnitude to width R by left padding with zeros. Guess
the padding length; verify by requiring exactly R paired digit positions and
at least one real exponent digit. Actual source text has<=L digits, so padding
exists. Leading exponent zeros are real digits, not additional padding choices.

Maintain delta_0=0 and, at each aligned position,

    delta_next = 10*delta + s_K*a_j - s_E*e_j.

At the end delta=k-E. Keep only delta in[-L-2,L+2] during the computation,
and only delta in[-L,L] at termination. For every desired |k-E|<=L this loses
no solution: with r positions remaining, delta=(d-tail_difference)/10^r;
the signed tail difference has magnitude<2*10^r, hence |delta|<L/10^r+2.
For each E/d there is exactly one signed-magnitude k and one aligned output;
padding length is fixed by the ACTUAL exponent digit count. The exponent part
is not a function of E alone: its terminal delta selects the mantissa order.

Position, sign, nonzero flag, phase and bounded delta give O(L^2) states and
constant branching per input byte. Input/output epsilon interleavings MUST
use a proper composition filter. A convenient minimal implementation consumes
and HOLDS the first actual exponent digit before emitting all left padding;
the source is frozen during those padding emissions, then that held digit is
paired once, and normal source progress resumes. This fixes ownership even
with original empty tokens, without generating multiple epsilon interleavings.

## 5. Mantissa second: share different targets by a residual counter

After the exponent suffix terminates with delta=d, process P from the ORIGINAL
source start to p. Initialize residual c=d. For a nonzero integer first digit,
actual mantissa order starts0; decrement c on every later integer digit.
For integer0 followed by dot, increment c once (actual order=-1), then once
per fractional zero before the first nonzero. After the first significant
fractional digit, c stays fixed. At a legal mantissa end require c=0.

Emit significant digits, nondeterministically choosing the LAST nonzero to
stop output; afterwards only zeros and the dot may occur. All earlier choices
die at a later nonzero. Never-stopped branches reject. Thus normalization has
one accepting path, including trailing zeros and leading fractional zeros.
This is V1's classical trimming principle, now with a residual counter so
the guessed d need not remain as a second independent register. The counter
range[-2L-2,2L+2] is sufficient on source paths of length<=L. It gives O(L)
states shared by all initial d. Prefix source progress is DAG-acyclic.

For no-exponent numerals, choose d in[-L,L], output h_L(d), and enter this same
mantissa machine at c=d. Exactly one d survives for each valid positive source
path. Do not treat this finite choice as enumerating every possible exponent.

## 6. Weighted bijection, full costs and the useful capacity corollary

For an admitted original source path, its zero/no-exponent/exponent branch is
unique; with an exponent, its cut is unique. Syntax/sign/digit count and the
actual mantissa order determine exactly one exponent-adder path and trimming
choice. Conversely every accepting construction path reconstructs one admitted
original path with the same scalar weight and key. Distinct original traces
mapping to a common key intentionally SUM; they are not spurious derivations.
Therefore the resulting weighted output DAG has the exact numerical image law.
All zero-support cases return EMPTY; no probability is fabricated.

Let B<=E count possible marker edges. Per cut, exponent composition takes
O((S+E)L^2), mantissa composition O((S+E)L); constructing all branches has the
coarse upper bound O((B+1)(S+E)L^2), including O(L^2) fixed order-code prefixes
for no-exponent branches. It is a DAG: exponent phase first, then mantissa phase,
and within each phase source progress or output-position progress is acyclic.
Classical suffix sums cost O(M); compact quantile unranking O(L*M) arithmetic
where M is the complete output-graph size. No determinization/enumeration of
all numerical orders or distinct numerical values is required.

For rational source weights whose numerator/denominator bit lengths<=b, a common
denominator given by the product of all source-edge denominators has O(Eb)bits.
Every source path uses each DAG edge at most once and there are<=2^O(E) paths;
all nonnegative sums therefore have O(E(b+1))bits (rank inputs add their bits).
The weight-preserving bijection adds no artificial path factor. Indices require
O(log M)bits, and compact scientific outputs O(L)bits plus their digit string.
These are polynomial bit costs, not unit-cost arbitrary-precision arithmetic.

Capacity corollary: a compact source DAG (e.g. product rows independently choosing
w/v's digits in Section2) admits this polynomial numerical-statistics index even
though any universal one-way NFT for its bounded normalization relation has the
exponential lower bound. This motivates source-conditioned compilation rather
than compiling a universal normalizer first. It is NOT superiority over the
classical cyclic-shift implementation, a latency claim or semantic accuracy.

## 7. Evidence/expansion boundary

Only a small independent mass/compact-quantile reference is justified now. Compare
small values with independent JSON/Decimal/Fraction enumeration; test enormous
exponents with original JSON lexical parsing and independent integer-coefficient
arithmetic without constructing the represented real as a huge Fraction.
Count paths/weights across original-ID aliases, fixed slots, mid-token marker
cuts, empty tokens, signed zero and cumulative-boundary quantiles. No resource,
new-head or training campaign follows from passing those oracles. General
negative values and binary64 rounding need separate contracts. Specific priority,
a substantial own useful consequence beyond classical composition, and the
positive user goal remain OPEN.
