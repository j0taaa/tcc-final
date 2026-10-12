# V16 — Strengthen inexpensive bounds before claiming a precision advantage

2026-10-12. BEFORE implementation/observations. V15's adaptive control wins
one core timing; this is preserved. This refinement targets another possible
weak-comparator problem: Hellinger applied before isolating underflow mass can
be unnecessarily loose. Classical support decomposition/chi-square/range
bounds are controls, NOT new contributions.

## Common-support coupling

Let S be the valid assignments with positive probability under BOTH heads.
Two weighted inside passes give a=P(S), b=Q(S). If either is zero, the laws
are disjoint and TV=1. Otherwise let P_S,Q_S denote conditioning on S.
All outside-support events of P have zero Q mass, and conversely. Coupling
the common min(a,b) mass and allowing the rest to disagree gives

    max(1-a,1-b) <= TV(P,Q)
       <= max(1-a,1-b) + min(a,b)*TV(P_S,Q_S).

This is useful even without the old range control's Q-support-subset-P
hypothesis. Same original IDs remain; S is a temporary analytic restriction,
not silent truncation of either law.

Use certified Hellinger, BOTH directional chi-square bounds and the sharp
likelihood-range upper bound on P_S,Q_S. Take the minimum of these valid
common-law bounds, then compose it with the above support-loss bound.
Report each separate bound, lost masses and complete costs. Do not omit a
control if it erases the current certificate-strength advantage.

## Exact integers for scalar controls

Use the separate denominator-cleared integer weights p_i,q_i and original
normalizers A,B. Common-support weights retain only atoms with p_i,q_i>0;
their exact inside masses are R,T, so a=R/A,b=T/B. With t=64:

* Floor sqrt(p_i*q_i)*2^t by integer square root. Inside H gives a lower
  affinity square H^2/(R*T*2^(2tn)); round sqrt(1-affinity²) UP rationally.
* For chi-square(Q_S||P_S), round each (q_i²/p_i)*2^t UP to an integer.
  Its inside sum U yields upper chi-square R*U/(T²*2^(tn))-1. Round
  half its square root UP and clip at1. Reverse P,Q for the other direction.
  Direct sums of rational q_i²/p_i can create prohibitively large LCMs;
  certified dyadic bounds avoid that hidden bit cost.
* Ratio extrema are min/max-product passes ignoring atoms outside S. Scale
  their root range by R/T and apply the existing sharp range formula.

All bounds use polynomial input bits, scalar inside passes, no generator
cores and no stochastic concentration assumption. They need not be tight.

## Prospective gate and unchanged real cases

Check ALL75 original-ID forest fixture/mode/tolerance cases against independent
enumeration, including unequal supports, exact equality and undefined masses.
Check each declared upper individually, the common-support lower and combined
minimum. A discrepancy blocks the public run and remains archived.

Then repeat ALL18 V15 public cases, original50,258 IDs and every format/
tolerance/method. Add these inexpensive controls for EVERY method and charge
their complete CPU/wall costs. Same packet is developmental, not independent
confirmation. No new forward, constructed timing family or chosen error-budget
success threshold. The old67.98-times-vs-Hellinger figure remains a factual
V9 comparison, not the ranking against these strengthened controls.

Eight answers: same real audit/use; sharpened quantitative TV bound only as
candidate novelty; compare the best competent scalar bound; original written
core proof unchanged; all cases prospectively fixed; bit/preparation costs
charged; support decomposition may erase useful precision gain; independent
priority/human/editorial judgement still open.
