# V18 — Relative precision for the chi-square control

2026-10-12 BEFORE code/observations. V17's upper bounds are VALID, but an
absolute atom grid2^-64 can be loose when denominator-cleared heads have
very different scales. Do not treat that numerical weakness as an advantage.

For an atom z=x²/y with positive integers x,y, z>=1/y. At position i use
t_i=64+bit_length(max denominator-row weight), and round z*2^t_i UP.
The absolute rounding error is <=2^-t_i<=z*2^-64. Thus every nonzero atom
has relative error at most2^-64, regardless of either head's row scaling.
Multiply the scalar inside result by2^(-sum_i t_i), rather than2^(-64n).
This yields a certified chi-square upper, with polynomial integer bits:
sum_i t_i<=64n+input-bit length up to a constant. No ideal division,
floating cancellation or giant prime LCM is used. Both directions receive
this improvement. Hellinger/range/support coupling are unchanged.

Repeat ALL75 independent scalar oracles, then ALL18 unchanged public cases.
Charge the additional bit work to EVERY method. Preserve V16's setup failure,
V17's valid but looser bounds and all previous timings; do not relabel them.
Eight criteria remain V16's: this is classical control strengthening, not
own novelty. A cheap bound may now erase the claimed precision benefit.
