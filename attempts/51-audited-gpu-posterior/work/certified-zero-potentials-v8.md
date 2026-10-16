# V8 — retain rigorously zero suffix potentials, before code change

2026-10-16. V7's FIRST GPU oracle attempt correctly REFUSED before any proposal.
Its source/log are preserved in evidence/ticket-v7-initial-refusal. Diagnostic:
case0/salt1, edge category at node5; original certified beta upper0 was replaced
by minimum subnormal. The artificial positive continuation produced a count
budget failure. Other two salts complete. Do not relabel this as a successful V7
run, an error in the rejection theorem, or evidence of measured latency.

Correction: when using the independently DIRECTED beta-upper frontend, KEEP
its zeros. A zero upper proves that state's true accepting suffix mass is zero.
Every positive-weight ACCEPTING word therefore visits STRICTLY positive beta
uppers at every state. V6's telescoping argument only needs positive potentials
along those positive target traces, not at states that no positive target word
can traverse. All inequalities and the SAME envelope/gamma construction remain
valid there. Words with zero target weight receive acceptance0 (including any
nonaccepting terminal mask). The full compiled graph and ALL original IDs remain;
no structural or numeric event is silently omitted from the proposal support.

For a zero-parent category, permit arbitrary positive counts only if every
constructed numerator is ALSO0; the existing `_counts` zero/zero branch does so.
Zero parent with any positive numerator remains a guard REFUSAL. State upper0
is never inferred from an ordinary approximate Torch reduction or an empirical
small value. Lower0 remains inconclusive and the admission gate remains0.99.
No cases, comparisons, budgets or performance criteria are relaxed.

This is classical exact zero propagation, not a new theorem. If future untrusted
approximate potentials replace the directed frontend, their zeros do NOT carry
this certificate and must be repaired/proved or refused independently. Leaf
potential1 for accepts and0 for nonaccepts is now retained exactly. Re-run the
SAME complete preflight and ALL count/word/packet/acceptance checks; specifically
include original aliases/fixed-zero rows and zero-target proposal traces.
