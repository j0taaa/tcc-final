# V10 — Preserve the coarse-grid refusal and clear an unavailable channel

2026-10-13. V9 source68e1d04's adaptive run passes ALL1,780 word cases,
90 channel/18 accepted laws and432 samples, with12 undefined-posterior refusals.
Fixed grids4/256 also pass the exact law but have six precision-gate losses
each and237/185 explicit one-attempt FAILs. These are preserved negative
precision/cap results, not performance evidence.

Fixed grid2 stopped during the channel-law oracle. A node can have positive
unrounded common mass U but floor(S*c_raw)=0. The reference correctly sets
its actual submeasure C to zero and beta to zero, yet stores a positive
conditional COMMON CDF from the pre-rounding U values. That zero-mass channel
is unreachable from the implemented residual sampler: parents multiply its
declared common mass0. Nevertheless it violates the stored-channel contract
that the exhaustive oracle checks. Do not relabel the failed run as passed.

Clear the common CDF weights when Cint=0. This changes no reachable sample
law, head, tolerance or expected-work theorem. Preserve the original failure,
then repeat the SAME oracle and all previously fixed grids in new output
directories. The defect was exposed by an unfavorable coarse control; the
adaptive pass alone would not have exposed it on these small fixtures.
