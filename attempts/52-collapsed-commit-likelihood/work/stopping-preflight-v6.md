# V6 — Correctness prerequisites before OLD-head diagnostic

Written6335f52 precedes stopping.py/stopping_audit.py. Two independent
rational oracles pass: six complete small original-word laws (including fixed
EOT/MASK suffix IDs and zero PAD mass), full prefix/length TV and stochastic
ordering, and a separate nearly maximal length-distortion fixture. The latter
is a proof object, not a performance benchmark or a semantic claim.

All26 focused A52 tests PASS1.745s; maintained231 tests PASS74.457s;
make check/focused Ruff pass. No model forward/sample/label/update occurs in
these oracles. V4/V5 sources, targets and evidence stay unchanged. V5 remains
negative with zero terminal rewards.

consumer-protocol-v6.json freezes source hashes and the ALL8 OLD-head audit:
first-EOT flow versus independent absorbing-DFA and old PAD-DFA partitions,
original full V, resource/error handling,1e-7 log tolerance and1e-10 survival
tolerance. Missing/zero masses are explicit, never epsilon-floored. Finite
floating checks do not verify a native RNG law. Passing the interest condition
is diagnostic only and permits considering another written consumer contract.
It is not new theory, semantic benefit, training or fulfillment of the goal.
