# A37: a stronger complete-oracle control found after v2

2026-10-11. Written BEFORE implementing the control or running model heads.
V1/V2 hashes and results remain unchanged; their guarantees are still correct.
This finding blocks any claim that A37's1/13 is the best competent guarantee.

Draw four complete payloads iid. Condition on their canonical multiset, whose
empirical probabilities are KNOWN. Couple two draws with those empirical
marginals so that each canonical diagonal is its Fréchet minimum, retaining
the original first payload. This is classical empirical/quantile coupling,
not an invention of conditional resampling.

Only multiplicities2+2 and2+1+1 change the original-second policy: in2+2,
return a uniformly chosen payload from the other class; in2+1+1, pair the
repeated class with a uniformly chosen singleton, and each singleton with a
uniformly chosen payload from the repeated class. All other patterns return
the original second. Return indices other than the first, preserve aliases.

For each canonical outcome of probability p_i, its diagonal reduction is
EXACTLY p_i^2*(1-p_i)^2. Thus it obtains at least1/4 of the maximal canonical
collision reduction. It is the pointwise optimum for every atom simultaneously
among ALL oracle-only, first-retained, marginal-preserving, hard-cap4 methods.
The Bernstein lower bound is classical; a self-contained proof and the
full categorical attainment/cost contract are in the separate A38 direction.

When the second and third canonical keys agree, the fourth draw has no effect
on the returned class; the original second also has the same integrated raw
payload law. Omit that draw, charging expected full draws4-c where
c=sum_i p_i^2. A half mixture with iid2 therefore costs3-c/2<=3 and gives
at least1/8 of maximal collision reduction, stronger than A37's1/13 at the
same WORST expected full-generation budget. It has hard cap4 rather than12.

This is NOT pointwise dominance: A37's random hash and ruin can have a larger
gain on a two-key balanced law. The pool's principle is known, and the exact
categorical formula/optimality still need prior comparison and an independent
oracle. Both must be controls before any native campaign. No empirical neural
win, timing, independent human review or publication sufficiency is claimed.
