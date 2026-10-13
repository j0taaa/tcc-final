# V28 — Consolidate A49; audit decisions without moving the old gate

Written before the new decision audit. The feedback supplied by the user is
an external assessment, not an independent validation of the proofs. No new
attempt, neural campaign, model update, or replacement of A24 is authorized
by a numerical result here. V25 stays FAILED 0/36; V26 stays development.

## Three questions, kept separate

1. Correctness: reconstruct the integer compression, signed product induction,
   original-ID/derivation bijection and total cost. Identify proof obligations
   by lemma and distinguish written checks from mechanization/human review.
2. Difference: compare the complete ordered bound with the actual deterministic
   results of Feng/Fu and the classical planar approximation construction.
   Improving a published bound is not a lower bound on their techniques, and
   absence from a targeted search is not exhaustive priority certification.
3. Software: decide ACCEPT/REJECT/UNRESOLVED for a fidelity budget supplied
   externally. Test all budget regions, not a threshold inserted between two
   observed bounds. Charge controls, exact marginals and the candidate core.

## Frozen developmental operation

Use ALL 15 V25 captured heads, ALL three rounding formats and ALL 45 pairs.
Original IDs, canvas, grammar and finite support remain unchanged. Reuse the
immutable V26 certificates, with their actual producer and costs; do not
attribute those timings to a new producer. No new forward or core timing.
The primary diagnostic is ordered_planar at epsilon=1/10, selected before this
audit; preserve the other seven engine/tolerance intervals as diagnostics.
Missing/undefined/resource-limited computations remain UNRESOLVED.

Competent controls include all V26 upper bounds and V27 original-ID marginal,
Hellinger, support-loss and both chi-square lower bounds. Strengthen the
moment lower bounds with exact grammar-restricted common-support likelihood
extrema, charging that extra inside pass. This is a classical control, not
new theory. Validate it against the existing independently enumerated words
before running the full heads. Do not weaken a control to obtain an advantage.

For each control interval [l,u] and candidate [L,U], report the combined
interval [max(l,L), min(u,U)]. The EXACT extra ACCEPT budgets are
[min(u,U),u), if nonempty. The EXACT extra REJECT budgets are
[l,max(l,L)), if nonempty. This accounts for equality: acceptance uses U<=tau,
rejection uses L>tau. Return all rational endpoints, all costs and refusals.
These regions are statements conditional on a requested budget, not evidence
that a customer actually requires one of those budgets.

Also report the entire fixed illustrative grid tau=10^-j, j=1..8, for every
pair. This grid illustrates possible risk policies and is NOT a measured
deployment requirement, a new independent success gate or proof of usefulness.
A precision choice can select the smallest declared word width among formats
accepted at tau (16 bits for binary16/bfloat16, 32 for binary32, original64 as
fallback). This is only numerical-table storage, not model quantization or
memory/latency measured for a neural decoder. A choice changes no syntax rule.

Shared historical preparation refusals with no controls are retained without
repeating a known failed preparation. All other lower controls are newly
evaluated with 150-second per-stage wall and 3-GiB process address-space limits.
Record current stage wall/CPU separately from historical costs. Never subtract
controls that were actually paid or credit a refusal as a competing defeat.
The output and provenance must cover all 45 pairs even on failures.

## Stronger classical lower bound, before implementation

Let a,b be the posterior masses of the common support, and let
R=Q_c/P_c on that support. Exact forest min/max passes give l<=R<=h.
For chi(Q_c||P_c), D=max(1-l,h-1) bounds |R-1|, hence
chi=E(R-1)^2 <= 2D TV(P_c,Q_c). If v<=sqrt(chi)/2 is the existing certified
moment enclosure, 2v^2/D is a sound lower bound (zero if D=0).
Use reciprocal extrema for the reverse direction. Lift the bound to the
full laws by min(a,b)*lower_c + min(1-a,1-b), as proved in V27.
Grammar-restricted extrema cannot enlarge D relative to the original product
extrema, so these controls are at least as strong. They do not establish the
actual TV or semantic accuracy. Zero common mass yields exact TV=1.

## Decision after the audit

Preserve every loss, unresolved budget and resource refusal. Report whether
the stronger certificate permits additional decisions, and exactly what they
cost. Do not promote a numerical interval improvement into measured savings,
a faster dJev, independent confirmation, or publication sufficiency. If cheap
controls already select the same formats for the entire illustrative grid,
say so. A24 remains a separate demonstrated application; A49 remains the
single theoretical candidate pending originality and proof review.
