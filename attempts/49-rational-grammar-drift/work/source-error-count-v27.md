# Source-grammar precision without an unverified CNF conversion

Written proof; no new implementation, model observation or successful practical
gate. This closes the precision parameter for the CLASSICAL source admission
in `polynomial-source-admission-v7.md`. It does not claim that the maintained
normalizer or a CNF conversion is formally verified. V25's failed gate remains
unchanged; V26 is development on the same heads.

## Definitions and theorem

Trim unreachable/unproductive symbols first. Apply the fixed right
binarization from V7, retaining epsilon/unit rules and the bijection of parse
trees. Let h be the longest number of edges in its acyclic SAME-SPAN dependency
graph. Let B be the sum of maximum supported, nonempty original token byte
lengths across the physical positions. Either a position has no supported
token, giving infeasibility, or B bounds every admitted word's byte length.
Empty cells are the exact zero/unit specified in V7 and cause no compression.

For any nonempty root derivation in that generalized chart, the expanded
number of nonexact compression gates satisfies

    d <= 2(h+1)(2B-1).

In particular h is smaller than the number of binarized nonterminals, which
is O(g) for source symbol size g. Hence d=O(gB), without eliminating nullable
symbols or enumerating nullable subsets.

## Proof

Consider only chart occurrences with positive byte span in one fixed root
derivation. Each selected alternative is either a terminal DAG edge, a unit
rule with one same-span positive child, an endpoint split with one empty unit
and one same-span positive child, or an interior split with two strictly
shorter positive children.

Contract maximal chains of unit/endpoint-split positive occurrences. Each
contracted chain follows SAME-SPAN dependency edges, so contains at most h+1
positive occurrences. The contracted tree is full binary: its leaves are the
ell terminal byte edges of the emitted word, and its internal nodes are the
ell-1 interior splits. It consequently has 2ell-1 nodes. There are at most
(h+1)(2ell-1) positive occurrences before contraction.

Each positive occurrence invokes at most one flat chart-cell OR compression
and at most one compression for its selected production AND. A terminal,
unit, empty product or exact passthrough may use fewer. Empty source subtrees
are implicit unique units and do not add any compression. Therefore
d<=2(h+1)(2ell-1)<=2(h+1)(2B-1). Parallel closure edges/aliases and alternatives
not selected in this derivation increase fan-in, not this count. Taking the
maximum over root derivations proves the assertion.

## Complete consequence and limitations

The admitted-event TV theorem can choose M=O(sqrt(gB/epsilon)) core rows for
the V7 generalized chart. Charge flat wide unions as in
`chart-error-count-v27.md`: with H including all wires/alternatives, its
arithmetic bound is

    O(H*((gB/epsilon)*log(gB/epsilon+2)
          +sqrt(gB/epsilon)*log(H+2))),

in addition to original input/scaling, the O(g*V^3+g*E) chart construction,
exact normalizers, grid and output work. Coordinates have the previously
proved polynomial input-bit bound; BIT time still depends on input bits.
There is no valid-mass or TV numerical floor.

This is more conservative than d<=3B-2 for an ALREADY ADMITTED unambiguous
epsilon/unit-free CNF grammar. The latter remains a separate corollary;
neither conversion nor its sharper parameter is silently asserted for every
LL(1) source. The generalized chart is a mathematical algorithm, not the
materialized-stack compiler used in V25/V26. Its implementation and
independent chart oracle remain absent. Counting parse occurrences is
classical; only the quantitative TV bound is the candidate contribution.
