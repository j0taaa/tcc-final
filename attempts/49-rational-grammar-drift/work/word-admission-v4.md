# Word-faithful event forests and the public numerical audit

Written2026-10-12, BEFORE implementation/observations. These are classical
weighted parsing/deterministic automaton reductions, not a new parsing theorem.

## Unambiguous CNF on a token-byte DAG

Assume an EXPLICIT unambiguous byte CNF grammar. At each original token slot,
construct a byte-prefix trie, with a separate final-byte closure edge for
each original token ID. Alias texts have different closure edges. A prefix
token closes to the next slot boundary, while the longer token continues in
the current trie. Each complete DAG path corresponds bijectively to an
original-ID assignment. Every token's probability appears on its closure
edge exactly once; structural byte edges have weight1. Empty/unsupported
emissions are invalid events; their original probability remains in the head
normalization. EOS is absent here.

In a chart cell(head,u,v), all paths consume the same consecutive physical
closure slots: vertex layers determine those closures, even if u/v are
inside a token. A binary split partitions the closure slots into disjoint
scopes. Alternatives in the same cell have the same scope. For a complete
original assignment, its byte path is unique, and its parse is unique by
the grammar hypothesis. Consequently different chart alternatives denote
disjoint ORIGINAL assignment events; products denote Cartesian products of
the disjoint closure scopes. The admitted-forest theorem therefore applies
to words, not merely derivations. Token aliases are NOT collapsed.

The DAG has O(sum_{i,t} byte_length(t)) vertices/edges before sharing. An
explicit CNF chart has polynomial size in this DAG and the grammar. Charge
its construction separately. This lemma DOES NOT prove that the existing
Python nullable/unit normalizer preserves unambiguity, bound every source
normalization, or decide general CFG unambiguity. A fixed JSON grammar can
be prepared once; an arbitrary user-source API retains its resource refusals.

## Independent deterministic JSON-stack view for one real audit

For the functional audit, use preserved classical predictive-stack/lexer
sources, not the CNF normalizer. At a physical slot and a given lexer/stack
state, a token has exactly one lexical effect and exactly one predictive
continuation or is invalid. Original IDs are partitioned by that effect in
that STATE. A leaf lists each original member separately with its paired
head weights; it DOES NOT replace the leaf by a pair of lexical sums. A
product combines that position's leaf and the next-layer suffix. A sum
unites distinct original IDs; suffix nodes can be shared without identifying
assignments. Accepting end states give the unique empty-scope unit.

Induction on remaining positions proves this is an admitted forest of
exactly the valid original JSON assignments. Dead suffix states may be
removed by structural backward reachability, independent of either head's
probabilities. Fixed slots retain their one original ID and weight1.
Explicit predictive stacks can be exponentially numerous; their preparation
is charged and subject to declared limits. They are a small-input bridge,
NOT the polynomial-grammar representation promised by the CNF-input lemma.

## Prospective real operation, all cases kept

Use the ONE existing public full-head packet originally selected before A24
independent model observations; input hash
8f8d512c1f78629a93c8bb442fff81d2fc9bca60b57f044bb7470fda4473168d.
It has four masked positions, all50,258 original IDs and a19-position canvas.
This is the sole complete head packet published offline, not a new external
confirmation dataset or a selected competitive benchmark. Copy input and
the five immutable classical helpers into this attempt with hashes.

Audit ALL three predefined numerical representations: binary32, binary16,
and bfloat16 round-to-nearest/ties-to-even. Apply rounding to the archived
PROBABILITY tables, NOT to neural parameters/logits. Normalize each rounded
full row exactly as rational numbers; retain zeros and unsupported IDs.
Evaluate BOTH epsilon=1/2 and1/10 for EVERY representation with the V3 core.
No semantic labels, original source completion or observed TV guides the
grammar, support, representation choices or case inclusion.

Compare certificate STRENGTH to two competent inexpensive controls on the
SAME conditioned distribution: exact normalized likelihood-ratio extrema
and its sharp range bound; certified Hellinger upper bound via integer
square-root intervals on the same event forest. Independently compare both
head normalizers to the frozen classical stack posterior. Complete word
counts describe the enumeration size; do not award a timeout victory over
enumeration. First validate the bridge against small original-ID enumeration.

Record every result/refusal/error, the packet/reference/producer hashes and
input/preparation/normalizer/control/core times. They are descriptive full
operation costs, NOT a latency superiority gate. The benefit under audit is
a guaranteed near-tight drift value for deciding whether a smaller numerical
table satisfies an application's declared error budget. Per-free-row nominal
storage is halved (f64->f32) or quartered (f64->16bits), before metadata and
transfer overhead; no end-to-end memory, model-speed or quality win is claimed.
No new forward, training, EPIC execution or modified source document occurs.
