# After V3: a direct proof cross-check and an essential practical objection

2026-10-17, AFTER the V3 finite audit. These are additional WRITTEN deductions
and exact relevance arithmetic, not results of that earlier producer or a
new sampling/timing campaign. No independent human review is asserted.

## Direct check of the infinite batch obstruction

V3's quantitative argument provides a second route to V1's infinite lower
bound, without relying on its non-C2 proof. For each fixed n, uniform
convergence f_R->f implies D_n f_R->D_n f, so D_n f>=1/16. Any preselected
batch for f still obeys sum_(n=4)^K |D_n f|<=128 E N, since its kernel proof
is target-independent. Therefore E N>=(K-3)/2048 for EVERY K, forcing
infinite expectation. V1's adaptive algorithm has the improved expected
input bound<2 fromV3 and retains its pointwise finite bit-work proof.
This independently derives the SAME lower conclusion analytically; it is
not a new external review or mechanical verification of the infinite proof.

## Approximation can erase the whole growing gap

The exact constructed family has very small fine-scale features. For R>=s,

    sup_p |f_R(p)-f_s(p)|
      <=(1/4)sum_(n>s)4^(-n^2-4)
      <=4^(-((s+1)^2+5))/(1-4^(-(2s+3)))=:delta_s.

This uses the ratio of successive weights, at most4^(-(2s+3)). The simple
classical batch for f_s has mean s/4. At s=2, delta_s<10^-8 and the mean
is1/2, UNIFORMLY for all R. At s=4, delta_s<2^-59. That is below the
spacing2^-54 of binary64 numbers in[1/4,1/2); proximity alone does NOT imply
literal equality after rounding, since a value can lie near a midpoint.

Thus the exact growing lower bound does not make this a useful method for
ordinary approximate probability gates or establish a neural quality/cost
win. For Bernoulli outputs, total variation equals the absolute probability
error. Standard coupling gives at most K delta_s for K independent outputs,
or for a finite K-step common adaptive policy with the same uniform kernel
bound. These are CLASSICAL consequences, not a new approximation theorem.

Exact arithmetic for the stated bounds is separately preserved in
docs/evidence/a69-v3-tolerance-audit.json. No old measurement or success
criterion is changed; there was no practical success gate for this proof.

## Decision before expansion

The quantitative exact resource separation remains a positive mathematical
candidate, with sharp linear source-cost order and a scoped pointwise full-
work gap. The fixed-tolerance comparison is a mandatory strong control for
any proposed application. A natural consumer must independently REQUIRE
the exact conditional law/precision or justify a tolerance small enough to
make the distinction consequential; do not impose exactness solely to
favour the candidate. No application/neural/performance campaign is selected
from this constructed response. Priorities now are specific literature
precedence and a real useful consequence; otherwise pursue another operation.
