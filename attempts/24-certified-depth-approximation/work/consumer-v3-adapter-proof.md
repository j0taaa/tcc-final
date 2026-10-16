# Bounded original-token JSON language supplied to Mosaic's unchanged kernels

Written before implementation. This is a classical representation adapter,
not a new automata or parsing theorem. First-stage scope: EOS absent, a fixed
physical canvas, compositional bytes, a fixed finite depth, nonnegative weights.

Let P be A24's trimmed deterministic layered recognizer on the initial canvas.
Each node descriptor s=(lexer state, predictive stack) has its true JSON
meaning. Each arc s --g--> r consumes one original token from the deterministic
lexical-effect group g, and respects the depth bound even inside a macrotoken.
Backward trimming removes only prefixes with no accepting completion in that
canvas. A word has one path; aliases remain different original IDs.

Construct a finite token automaton A by merging occurrences of the SAME full
descriptor s across layers. For each observed arc, admit ALL original IDs in
its lexical-effect group. Union equal source/target edge memberships. The
full descriptor contains every lexer/parser fact needed for the next
transition; a token can never lead from s to two different descriptors.
Mark s accepting exactly when lexical finish is defined and its emitted
terminals consume the remaining predictive stack completely. Keep the original
initial descriptor. A zero-mask self-loop may represent a node with no outgoing
edge for the tensor constructor; it introduces no word or positive path.

**Language under the canvas.** Every word in J_d respecting the canvas has
an accepting path in P: every prefix has that word as a completion, so trimming
cannot remove it. Mapping each descriptor into A retains that path. Conversely,
every path in A follows genuine deterministic lexer/parser transitions and
obeys the depth bound. Ending in an accepting descriptor gives a valid JSON.
Fixing the original canvas tokens therefore yields precisely the same J_d.
Merging can admit paths absent from a particular trimmed layer, but those paths
are still genuine bounded JSON; if they respect the canvas their accepting
word itself shows that P admitted them. No unproved state minimization is used.

Both samplers receive the same original weights at free positions and singleton
indicators at fixed positions. Since the automaton is deterministic, the
sum over accepting paths is the sum over ORIGINAL token words, with no parse
or NFA multiplicity. Thus inside masses, original-token marginals and the
real-arithmetic sampling law agree with the layered reference. Conventional
DFA minimization may additionally be supplied to both competitors, but must
be separately validated before measuring it.

The adapter scans stored arcs/group memberships and materializes dense E×V
edge masks for the native constructor. State merging does not promise a small
automaton: storage and work, including every dense temporary, are paid. No
universal speed or memory advantage follows from this representation proof.

Mosaic's finite-precision matmuls and final categorical draws remain its native
implementation, including its dtype conversions and warnings. The proof above
does not certify their rounded law. Small numerical oracle checks establish
only their disclosed observed accuracy. Native model-loop, EOS/EOT/PAD and
tokenizer-byte contracts are further obligations before an application claim.

## Classical minimization, before its measurements

Global lexer classes have the same transition out of every descriptor. Replace
each such class by one alphabet symbol, minimize the resulting partial DFA
with Hopcroft's algorithm, then restore ALL original token IDs to each edge.
Every original word maps to one class word and has unchanged acceptance.
No probabilities are averaged or normalized in this operation. Each restored
edge must contain a whole global class; the implementation checks that fact.
The unchanged native kernels still receive E×V masks, not class logits.
Minimization is a mandatory competent control optimization, not our invention.
For the full-V screen, construct that symbolic class graph DIRECTLY from
stored lexical groups, minimize it, and only then expand original IDs. This
has the identical language argument and avoids materializing a needlessly
large pre-minimization E×V membership list. It is supplied to the control
before any resource/cost measurements, not presented as a new contribution.
