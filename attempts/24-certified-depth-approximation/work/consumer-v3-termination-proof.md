# Variable EOT/PAD boundary: language and conservative certificate

2026-10-16. Written before implementing this extension. This adds the missing
serving contract to the adapter, not a new general conditioning theorem.

Let e be an original EOT ID and a an original PAD ID (possibly the same ID).
Both are forbidden as ordinary JSON content; all other unsupported special
IDs are also forbidden. On a length-n canvas the target language is

    T = { z e a^r : z is a nonempty valid UTF8 JSON token word, |z|+1+r=n }.

Each word has exactly one boundary: its first occurrence of e. If e=a,
subsequent occurrences are padding. T_d restricts actual JSON nesting depth
inside z, including peaks inside a macrotoken. The original product q and all
fixed original IDs remain unchanged. EOS/PAD probabilities are NOT omitted
from normalization. Every completed output is parsed only before its EOT.

## A finite bounded recognizer

For compilation only, map e and a to one ordinary whitespace byte each. Other
IDs retain their compositional bytes; unsupported IDs have no emission. Build
the existing bounded recognizer on this SURROGATE table and initial canvas.
For every word of T_d its surrogate is JSON followed by whitespace, so all its
descriptor prefixes have a valid completion and survive backward trimming.

Merge equal full descriptors as proved for the EOS-absent adapter. Delete e/a
from all ordinary edges. From EVERY descriptor whose lexical finish and
predictive stack recognize a complete value, add an edge labeled e to a new
finished state. Its sole positive outgoing edge is the self-loop labeled a;
only this state is accepting. Ordinary edges cannot enter the finished state.
The empty content prefix is not accepting. No e/a is allowed inside strings,
numbers or any unfinished value. Conversely, each accepting path has a unique
first e, preceded by a genuine bounded JSON value and followed only by a.
The graph thus recognizes precisely T_d under the canvas. State-minimization
is conventional; first split e/a out of whitespace's global lexer classes.

## Conservative tail without unbounded parsing

Let C_d be the original A24 CLOSED lexical-counter event on the SURROGATE
table: it is lexically complete, never negative, ends at height zero and
exceeds d somewhere. A word of T\T_d maps to exactly such a word: replacing
the termination/padding IDs by whitespace neither opens nor closes a JSON
delimiter and completes a final number correctly. The relaxed event is over
the SAME original IDs, and is deterministic; aliases/termination words are
never counted more than once. Hence

    q(T\T_d) <= U_d := q(C_d).

Compute L_d=q(T_d) from the TRUE termination graph, not from the surrogate
JSON recognizer. Surrogate shallow mass is NOT a lower bound for T_d and
must never be used in the conditioning denominator. If L_d>0,

    TV(q(.|T), q(.|T_d)) <= U_d/(L_d+U_d).

This bound may be loose because the counter does not enforce the EOT/PAD
phase. No gain is presumed. A phase-aware or first-overflow refinement is
separate future work, not retroactively used in this first version.

## Exact finite-graph arithmetic and cost

Given deterministic graph edges carrying whole refined original-token
classes, the weight of edge u->v at free slot p is the exact sum of q_p over
its IDs; at fixed slot it is the corresponding singleton indicator. Backward
DP ends with the accepting indicator. Sum over outgoing edge weight times
suffix mass. Determinism gives one path per word, so the initial inside value
is exactly L_d. Draw an edge using these products, then an original token
from that edge weighted by its original row. An outside pass yields original
token confidence. These are classical weighted-DFA operations.

With C refined classes and E edges, computing all edge weights costs
O(n E C) rational additions in the direct implementation, DP O(nE), storage
O(n(E+N)); grouping only reads present edge/class memberships. A binary64 row
is represented by scaled integers; their bit length grows with the n rows'
bit lengths, so costs include the corresponding integer additions/products.
There is no new polynomial-bit bound independent of the input weights.
Surrogate table/partition, bounded compilation, graph minimization, original
mass, tail DP, sampling/confidence, and dense GPU buffers ALL cost. Native
Mosaic floating arithmetic/draws still have their separate rounded law; only
the integer backend supplies the exact-on-T_d sampling claim.

## Version decision and eight criteria

The eight criteria in consumer-v3-contract.md continue to apply. This is the
minimal variable-length contract needed by the already identified serving
consumer. The scientific candidate remains A24's structural tail certificate;
language adapters, EOT handling, finite-DFA inference and minimization are
classical. First test small language/mass/marginals by an independent JSON
parser and rational enumeration, then a resource screen on known old heads.
Do not start an independent neural campaign without a frozen operational
protocol and a plausible benefit against both competent native GPU kernels.
No semantic gain, novelty or publication follows from this extension alone.
