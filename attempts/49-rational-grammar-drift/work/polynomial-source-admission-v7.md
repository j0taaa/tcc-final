# Polynomial source admission without nullable-subset expansion

Written2026-10-12. This is a CLASSICAL generalized-CYK construction and a
word-faithfulness lemma for the TV theorem, not a claim to invent parsing.
It is a mathematical algorithm separate from the current main compiler's
canonical-normalization checks. The public audit uses the separately admitted
predictive-stack bridge, not this construction. No software guarantee is
silently enlarged.

## Source and token hypotheses

The finite source grammar is LL(1), has neutral production weights, and passes
the usual nullable/FIRST/FOLLOW and nullable-prefix left-recursion checks.
It is therefore unambiguous, including its empty derivations. Original finite
token domains, byte emissions, fixed slots and absent EOS are as in V4.
Unsupported/empty emissions have no valid path and retain their input mass.
Let g be total source symbol occurrences, V/E the explicit token-byte DAG
sizes, and ell the total rational/input description bits.

## Binarize without eliminating epsilon or units

Replace terminal occurrences in longer bodies by byte preterminals and split
each longer body into a fixed right-associated chain of fresh auxiliaries.
KEEP epsilon and unit rules. This costs O(g), has O(g) rules/nonterminals and
preserves derivations bijectively by expanding/collapsing the fresh chains.
In particular it does not enumerate2^k subsets of k nullable body symbols.

Compute nullability. For each binary rule A->BC, add a SAME-SPAN dependency
A->B if C is nullable, and A->C if B is nullable; for A->B add A->B. This
dependency graph is acyclic. Each edge is in the nullable-prefix left-corner
graph of the binarized grammar (A->B is always a left corner; A->C requires
B nullable). A cycle through auxiliaries would, upon collapsing their fixed
chains, be a nullable-prefix left-recursion cycle in the source. A cycle only
through auxiliaries cannot occur because each auxiliary chain goes forward.
Both kinds are excluded by the source admission check. Byte preterminals
have no nonterminal dependencies.

## Generalized chart and explicit algorithm

Number byte-DAG vertices topologically. Define cell(A,u,v). If u=v, the
event is the singleton empty path iff A is nullable; store unit or zero.
The source's unique empty derivation is implicit, with weight1.

For u<v, process cells by increasing v-u and, within one span, process heads
with their SAME-SPAN dependencies first. Add these alternatives:

1. A->byte: every matching labeled edge u->v, preserving its own original-ID
   closure choice and weight, or neutral structural byte weight.
2. A->B: the nonzero child cell(B,u,v).
3. A->BC: each split vertex w with u<=w<=v and two nonzero children
   cell(B,u,w), cell(C,w,v).

Interior splits have strictly shorter spans. Endpoint splits use a nullable
unit and a same-span child already available in the dependency order. Thus
the construction is acyclic and well-defined. A unary alternative can be
represented as a product with the common empty unit.

Induction over the span/dependency order gives exactly all grammar parses of
all DAG paths, with their original-edge choices, without extra tree schedules.
Empty source subtrees have one implicit derivation and neutral weight; their
replacement does not identify distinct original assignments. Grammar
unambiguity and V4's path/ID bijection show each original assignment occurs
once. Closure scopes determined by endpoints make sum scopes equal and product
scopes disjoint. Empty-scope cells have at most the single relevant trie path
and unambiguous parse, so reduce to unit/zero as required by V2.

The chart has O(g*V^2) cells and O(g*V^3+g*E) alternatives. Binarization,
nullability and dependency preparation are polynomial; the DAG is linear in
total declared token-byte occurrences before prefix sharing. Full input
preparation and this forest construction are charged. Sparse implementations
can refuse resource budgets without declaring infeasibility or a certificate.

## Complete source-input TV corollary

For two rational frozen product heads over the same original support/canvas,
conditioned by any admitted LL(1) source grammar with both valid masses
positive, the construction above followed by the V3 integer-core algorithm
computes rational L,U with

    L <= TV(P_valid,Q_valid) <= U <= (1+epsilon)*L.

Its FULL cost is polynomial in g,V,E,ell and1/epsilon. Core coordinates have
polynomial bits by V2's unique-assignment mass argument; compressed size is
O(sqrt(d/epsilon)) and d is bounded by the explicit nonempty gate count.
There is no numerical valid-mass or TV floor, common parse tree, or ideal-real
primitive. Preparation is no longer hidden behind the provided-forest theorem.

This corollary is an algorithm/proof, NOT verification of the existing
Python/Rust normalizer, nor a benchmark about explicit predictive stacks.
The NEW candidate contribution remains the quantitative/integer TV core
refinement and its full-cost original-word application. Generalized parsing,
LL(1) unambiguity and the gate principle are antecedents.
