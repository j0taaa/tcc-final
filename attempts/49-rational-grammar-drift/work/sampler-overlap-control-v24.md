# V24 — A competent first-divergence coupling control

BEFORE implementation/observations/forwards. V23 protocol/capture are frozen,
with ZERO new heads/TV observations. V22 PDF and all previous bounds remain
valid historical comparisons against their explicitly listed controls.

## Classical exact recurrence

On an admitted unambiguous event forest let A_v,B_v be the two exact integer
inside masses at node v. For an alternative t, let a_t,b_t be its exact term
masses. Conditional samplers choose t with a_t/A_v or b_t/B_v, then sample
its disjoint-scope children independently. A leaf choice/unit is deterministic.
Maximally couple the alternative IDs. Conditioned on a common alternative,
independently couple its child samplers using the same construction. Thus

    c_v = sum_t min(a_t/A_v, b_t/B_v) * product_child c_child.

Zero inside mass in either head gives c_v=0 (unreachable jointly). Unit/choice
empty-child product is1. At the positive-mass root, c_root is the probability
that the coupled complete ORIGINAL assignment/derivation is identical.
Consequently TV<=1-c_root. The coupling principle and local overlap are
classical; ICML2024 already uses local conditional overlap in its reduction.
This is a strengthened CONTROL, not a new scientific contribution.

## Polynomial-bit scalar lower evaluation

Exact rational recurrence can accumulate large denominators. Let S=2^64.
Store integer C_v<=S*c_v. Compute the product of child lower probabilities
with division/floor by S, one child at a time, starting at S. For each term
multiply its lower product D_t by
min(a_t*B_v,b_t*A_v). Sum, divide/floor by A_v*B_v. Every operation rounds
DOWN, so C_v/S<=c_v. All values remain in[0,S]. Return the rigorous rational
upper1-C_root/S, with no unverified floating cancellation or rational LCM.
Node/term integer masses have the usual scoped O(input-bit) bound; evaluation
is scalar polynomial work/bit cost. Equal normalized laws yield exact1 at
reachable couplings, hence upper zero. Refusal is never a certificate.

Also apply the SAME control to common-support normalized P_S,Q_S, then combine
with max(lostP,lostQ)+min(P(S),Q(S))*TV(P_S,Q_S). Retain BOTH full/common
coupling bounds and EVERY previous scalar upper; take the minimum only among
valid bounds. This may erase the old18.57x practical gap and must be reported.

## Eight-question update and gate

Criteria1/2/4: same deterministic numerical-table audit and own sharper TV
theorem; this control is known, not added novelty. Criterion3/7: the cheaper
overlap may suffice or even be tighter than the endpoint interval. Criterion5:
repeat ALL75 original-ID independent enumeration cases, including zeros/scaling,
BEFORE any real data. Then repeat ALL24 development rows with both coupling
controls and full costs. No new favorable instance/success threshold.
Criterion6: compute/charge both normalizers and scalar inside overlaps, never
assume token marginals are independent after grammar conditioning. Criterion8:
new evidence updates comparisons; no publication/priority claim follows.

Only after the control gate, V23's ALL5-doc/3-mask/360-row unseen-input audit
can proceed with these controls added. All original cases, tolerance, budgets
and the2x precision predicate remain; there have been NO independent metric
observations on which to change that predicate. Preserve an old failed gate
if the strengthened comparator removes it. No speed/semantic/EPIC victory.
