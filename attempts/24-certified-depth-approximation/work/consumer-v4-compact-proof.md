# A competent compact CFG control for JSON EOT PAD*

Written BEFORE its adapter/measurements. The eight criteria and objections
of consumer-v3-contract.md remain in force. This is a classical stronger
baseline, not another proposed contribution. A CPU solver should not pay
DFA minimization or a separate complete parse for every possible EOS position.

## Deterministic lexical interface

Retain the original A24 byte lexer states and introduce one DONE state.
Ordinary original IDs have their unchanged byte transitions before DONE.
EOT and PAD IDs are removed from every ordinary group. EOT is enabled only
when the old lexer has a defined finish: append its finish terminals (possibly
NUMBER), emit a new terminal E, and enter DONE. In DONE only PAD is enabled;
it emits E and stays in DONE. All other original special IDs remain forbidden.
The initial lexical state is OUT; only DONE is allowed to finish the canvas.
EOT=PAD is supported: the first occurrence changes phase, subsequent ones pad.

Reuse the SURROGATE table's already refined global classes/row sums: ordinary
class members had identical effects in all original states; in DONE all are
forbidden. EOT/PAD were split out as individual original-ID classes, so each
new lexical group is still a union of whole classes. Global class numbering
and row denominators are unchanged; original termination probabilities count.

## CFG and unique original-word paths

Use the original unbounded JSON value productions, with start production

    S -> Value E Pads END
    Pads -> epsilon | E Pads.

END is the existing physical end-of-canvas sentinel, distinct from E. E is a
new terminal13; JSON uses the old syntax terminals0..10 and MARK/END11/12.
For the marked compiler, the same canonical Skip-before-each-terminal lifting
is used. The scanner emits one MARK per ORIGINAL token, including EOT/PAD.
For epsilon removal, use the same unmarked syntax grammar and the original
provenance scanner. Padding has one right-recursive derivation; Skip blocks
are attached to the next actual syntax terminal as in the existing grammar.

Each original word has one deterministic lexical path. Acceptance requires
its unique first EOT to follow a complete JSON value, enter DONE and leave
only PAD IDs. Conversely any word of JSON EOT PAD* follows this path and its
unique JSON/Pad productions. Thus the forest sums words, not EOS locations
or multiple parses of the same original word. Original aliases stay distinct.

## Frozen compiler boundary

Load A23's immutable compiler/posterior sources in a SEPARATE module namespace
from the EOS-absent controls. Supply the new lexer table and normalized grammar.
The compiler's imported `finish` callback is set in this isolated namespace
to return epsilon on DONE and undefined otherwise. This is the only lexical
end predicate change; it is used both by ordinary finalization and lexical
coaccessibility. No parser, CNF normalizer, trimming, scanner, numerical inside/
outside or sampling source is edited or given a candidate-specific shortcut.
The old namespace/controls must remain unaffected. Record the archive hash
and this explicit adapter hook; it is not an unmodified original JSON input.

Give this adapter to local, bidirectional-local and epsilon-local controls,
with the same exact NumPy row summaries, original-ID block recovery and sparse
sampled-token confidence already supplied in V2. Compile once for an initial
canvas, then reweight compatible extra fixed positions with fresh numerics.
The same language-only trimming/reuse proof applies. Validate masses, ALL
original marginals, the finite-ticket joint law, aliases and changing fixed
positions against independent strict JSON+EOT/PAD enumeration before timing.

Setup costs O(QV) table work plus ordinary CFG normalization/forest work, all
paid. Standard chart sharing may avoid the explicit-stack explosion. No lower
bound or speed promise is made for either representation. The full-cost A24
comparison must survive these controls; their resource guards/costs remain
visible, without promoting a refusal to general impossibility.
