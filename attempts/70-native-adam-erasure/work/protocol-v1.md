# A70 V1 — Frozen minimal numerical correctness protocol

Written2026-10-17 BEFORE source/build/execution. No timing competition or
neural campaign. A passing result cannot fulfill the positive user goal.

The artifact must identify the proof/protocol and actual producer commits,
all source hashes, compiler/version/flags, Python/platform, FP environment,
all cases/status, numeric bits/counters and the actual process exit code.
Build the isolated C reference only AFTER its source commit exists. Use a
temporary build directory; no third-party source/import or .venv mutation.

## 1. Native reference and independent primitive oracle

Implement theory-v1 Eq1 literally in C11 with binary32 intermediates,
FE_TONEAREST, gradual underflow, FLT_EVAL_METHOD=0, -ffp-contract=off,
-fno-fast-math, and no omitted epsilon/bias-correction scalars. Check the FP
environment. Supplied scalar tables are common inputs, generated once from
native powf/sqrtf for positive time and checked finite/positive. They are
RECORDED INPUT BITS, not a proof that libm correctly rounds pow.

An independent Python oracle rounds exact Fraction values to the nearest
binary32 grid, ties-to-even; use rational squared-midpoint comparisons to
certify sqrt_R. Check native primitives/complete step on boundary cases,
normal/subnormal operands, sign changes, and the short trajectories below.
Comparing two calls to the same native kernel alone is not an independent
primitive correctness check. Every source belongs to this attempt; no
mutable imports from prior attempts.

## 2. Every predeclared scalar case

Use beta1=R(.9), beta2=R(.999), epsilon=R(1e-8), eta=R(.001), H=512.
Zero-gradient gap lengths h in{0,1,15,128,512,4096,32768,65536}; start
steps s in{1,1024}; pre-initial-gradient weights in{-1,-.01,.01,1}; initial
nonzero gradient in{-.1,.001,.1}; next gradient in{-.2,0,.0001,.2}.
TOTAL768 cases. Initialize m=v=0 and apply the initial gradient at s;
earlier zero steps from initialization leave that state unchanged. Record
that native state, eagerly perform ALL h zero steps, record the parameter
at the next read, then apply the next actual gradient at s+h+1.

Candidate performs the guard, implicit-moment bound/admission and fallbacks
in the proof. Compare the read parameter and ALL three final state bits with
eager output on EVERY case. Retain non-erasure, absent freeze, zero/failure
cases and all source coefficients. For h<=15, independently replay the full
trajectory using exact-rational rounding/sqrt; these short cases are proof
objects, not evidence about a real model or entire software ecosystem.

Record head steps, parameter writes omitted, rounded moment steps replayed,
both erasures and guards checked. Compare operation counts with exact lazy
replay and the SAME weight-absorption guard followed by moment-only replay.
These are counts, NOT speedups or an all-algorithm lower bound. All768 cases
are constructed numerical fixtures, not external workload observations.

## 3. Independent enclosure/boundary/negative checks

- Compare the stated enclosure to actual rounded beta-decay on a fixed grid
  including smallest subnormal, neighbors of the normal boundary,1e-20,
  1e-8,.001,1,1e20 and negative first-moment counterparts; include h=0,
  1,15,128,512,4096,32768,65536. Check that(4) never excludes literal state.
- Explicitly check the nonzero rounding floor using subnormal fixed points.
- For huge binary gaps r=2^128 and2^1024, evaluate ONLY bounded-exponent
  certificates/counter handling; do not claim an eager replay was run.
- Preserve the difference between rounding each of four2^-26 decrements of1
  and rounding their real total once. Check that replacing unknown moments
  by zero WITHOUT endpoint admission changes at least one fresh update.
- Reject/admit conservatively invalid beta/epsilon/scalars, NaNs/infinities,
  negative variance, signed-zero parameter guards and zero moment outputs.
  Weight decay/EMA/other op orders are explicitly unsupported, not tested
  equivalent by this protocol. No false success from an omitted status.

## 4. Decision

Correctness screen passes only with zero identity/oracle/enclosure errors,
all768 cases and stated boundary/refusal checks preserved, and at least one
NONTRIVIAL case with nonzero initialized moments skipping native work via
both certified weight absorption and fresh-gradient moment erasure.
No fixed success fraction, practical speedup, publication or model/training
claim follows. This only decides whether the minimal proposed mechanism is
internally viable. Before any substantive implementation, priority audit,
input-only natural gap distribution, exact real consumer kernel and strong
complete-cost controls remain required. Do not add more synthetic cases or
tune the head cap after seeing results in order to fabricate a useful gate.
