# V15 — Exact self-certification and common structural passthrough

2026-10-12, BEFORE code/measurements. V13 concludes ALL18 rows, including
the strong uncapped control; its times remain descriptive. This refinement
tests another competent classical optimization, not a scientific invention.

## Exact all-direction distortion of a candidate angular core

For integer row lists G,C, the two absolute-projection norms are piecewise
linear and homogeneous. Their ratio is a fractional linear function between
successive perpendicular directions of their generators; it is monotone or
constant there. Thus its minimum and maximum occur at those breakpoints
(plus axes to cover degenerate rank cases). No angular sampling is used.

Orient each generator into the right half-plane and sort by determinant.
Store prefix sums. Orient the query w into that same half-plane. If w.y>=0,
negative dots form a prefix; otherwise positive dots form a prefix. Binary
search locates the sign transition. F_G(w) is dot(w,total-2*negative_prefix)
or dot(w,2*positive_prefix-total). Each exact norm query costs O(log(m+2))
integer operations after O(m log(m+2)) setup. A zero original norm requires
zero retained norm; skip only that undefined ratio. Rank zero is exact.

Starting with angular N'=1, double up to the existing target N. Compute its
candidate core and certify the actual minimum ratio >=1-20/N. Return the
first passing core. At N'=N the existing proof guarantees passage. Cores
therefore still have at most8N+4 rows and the SAME declared all-query loss.
This is classical adaptive approximation with an exact a posteriori check.
It may be much better than a worst-case uniform grid on this packet.

For products of <=250,000 candidate pairs materialize and self-certify.
For larger products use V13's uncapped streaming target-grid control.
This is a representation switch, NOT a resource refusal or dropped event.
Worst-case arithmetic/precision bounds do not improve over uniform angular
aggregation; extra certification/sorting is charged completely.

## Remove exact needless compressions for EVERY method

Opt-in common adapter refinement: a unary OR is exact passthrough. A product
with a singleton event on either side is an exact diagonal image, so it does
not need compression. Zero-row products are exact zero. Compute structural
event counts capped at2 bottom-up independently of head probabilities.
Count a product compression only when both children have >=2 events; count
an OR compression only for multiple alternatives. That count gives the SAME
inductive accumulation bound with the omitted exact operations contributing
no loss. Runtime may also skip products when an actual core has <=1 row;
the structural bound then remains conservative. Every method receives this
refinement; original support/IDs, scope, normalizers and law stay unchanged.
No old timings are reattributed. Unit/fixed-slot work remains charged.

## Prospective gate and all-case functional protocol

Repeat ALL V12/V13 geometry families,225 forest comparisons,3,501 products
and300 small Cartesian checks under adaptive angular, calibrated endpoints
and hybrid, using the common passthrough in forest cases. Independently
verify prefix norm queries and the computed minimum ratio against direct
integer absolute sums on existing signed/near-collinear families. Finite
checks verify correctness only. Any unexplained discrepancy blocks the run.

After passage repeat ALL18 unchanged full-V public cases, with both cheap
controls, CPU/wall and complete costs. No new model forward, favorable-case
selection, synthetic timing family or independent/statistical claim. No
wall-time cap or materialization-refusal success credit for the control.

Eight criteria: (1) same numerical dLLM/GLC distribution audit; (2--4) only
the sharper written deterministic TV bound is candidate novelty, while these
optimizations are known; (5) all prospective families/cases remain; (6) every
method gets exact passthrough and pays certification/preparation; (7) adaptive
control can remove the observed speed benefit; (8) human/exhaustive priority/
editorial judgement stay open. Preserve any unfavorable result.
