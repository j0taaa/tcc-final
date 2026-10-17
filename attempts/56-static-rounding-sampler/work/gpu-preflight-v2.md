# Minimal GPU feasibility audit before performance work

The V1 four rational oracles pass. The eight README criteria are unchanged;
this addendum justifies a SMALL opt-in GPU reference to test whether the
proposed execution scheme is even numerically available. No real-head readout,
performance timing, external dataset, model instance or new pretrained forward.
This step cannot satisfy sufficient systems novelty/usefulness on its own.

Copy the exact A51 directed frontend, CDF decision and retained-prefix sampler
from immutable d61565e4ac544334d93a81834255f29fd15c9073 into a local namespace,
recording SHA256 per copied file. These are CLASSICAL controls, not new code.
Use the SAME compiled graph/class blocks, target, CDF decisions and rational
fallback. Only the numerical frontend changes. Do not import mutable A51 work.

Implement one RNE binary32 class/inside stream with explicit PTX rounding.
Check converted inputs and every product; positive sums of already normal/zero
terms cannot become a nonzero subnormal, so a finite final sum plus valid inputs
suffices for a positive reduction. Guard finite scaled outputs as well. Any
invalid fast guard reruns the directed frontend BEFORE any sampling choice;
the original prefix tensor and RNGs stay unchanged.

Class budget: conversion1, maximum per-lane loop length ceil(maxclass/256),
and the verified256-lane binary reduction upper depth8. Edge-label reduction
uses its per-lane loop length plus depth6. A node's suffix budget adds the
next-layer budget, class budget, label sum budget, product1, conservative
maximum outdegree additions and scale-division1. Products ADD inherited
budgets. Use one worst-case budget per layer; looseness is a measured refusal/
fallback concern, never a reason to change the target support.

Generate exact outward binary32 multiplier constants from Fraction, not libm.
For this first prototype, materialize class and beta intervals for the unchanged
sampler. Explicitly charge the additional estimates/buffers and constants; do
not claim half memory or a fused consumer which has not been implemented.

Independent finite toy audit: enumerate valid original-ID JSON words with a
Python JSON parser and true EOT/PAD suffix policy, build a small disjoint trie,
and compare every root/suffix/class mass to exact Fraction enumeration. Include
byte aliases and fixed IDs. Pair every GPU output with a full rational replay
using the identical prefix and seed, including ambiguous finite prefixes and
guard-triggered subnormal/underflow fallback. Include >256-ID class reductions,
zero weights, mixed accepts and explicit invalid support refusal. Audit emitted
PTX for rounding modes/no FTZ and preserve any failed draft before repair.

The result decides only correctness/feasibility of the new numerical frontend.
After it, reassess significance and freeze a separate complete-cost protocol
with equally optimized directed and approximate controls BEFORE any real-head
study. Existing15 heads remain previously inspected development only. The
negative whole-model CPU floor is not weakened or reinterpreted as a win.
