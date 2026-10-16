# V12 — ALL-old-state proxy functionality, BEFORE prototype/replay

2026-10-16, after V11 correctness, not a cost/variance/training campaign.

## Eight criteria and operation

1. Apply the V11 policy-only projected control to ALL70 recorded V10
   transitions (62 distinct head contexts; eight roots each used twice).
   No new pretrained forward, sampled trajectory, parameter update or label.
   All eight questions/golds are already KNOWN development data. Do not call
   this independent confirmation. V5/V8 remain closed.
2. Reuse classic deterministic lexical projection, grouped weighted automata,
   conditional expectation and autodiff. These mechanisms are NOT novelty.
   PAPL/baseline correction remain direct antecedents. This only tests whether
   a computable nontrivial proxy is available in the actual resource contract.
3. Possible later benefit is a useful proposal-conditioned training control
   without another model call. It has extra verifier/compilation/query costs.
   No favorable variance, speed or training claim follows from functionality.
4. Prove the regular subset and same-original-weights formula below. Preserve
   EOS=PAD126081, all126464 original IDs including115 empty aliases, explicit
   fixed bits and absorbing unused suffix. Never use a gold-restricted sampler.
5. Before replay: minimal independent regex/Decimal/byte-language and rational
   projection oracles, zero-support detection, NumPy and independent Torch CPU
   autodiff. Freeze exact runner/runtime/input hashes BEFORE reading heads for
   these new computed quantities. Input files are inspected for schema first.
6. Preserve every transition/error/refusal/structural-zero/underflow. Diagnostic
   times and memory describe this correctness replay only; they do not compare
   deployment implementations. Prepare one lexical plan per distinct target,
   charging it in any later cost study. Ordinary WMC computes the same result.
7. Objections: proxy can be zero after an incorrect commit or miss alternative
   correct exponents; raw semantic proposal correctness is a stronger full/
   anchor baseline. State/horizon/RLOO/combined-class controls remain required.
   Neither a proxy-positive state nor an extra query implies useful variance.
8. Gaps: strong-control full-cost variance, actual policy updates, application
   benefit, adequate originality and independent confirmation all remain open.

## Regular-subset proof and exact query

For the KNOWN positive canonical decimal integer d (no leading zeros), accept
suffix bytes matching, with JSON whitespace W=[space,tab,CR,LF],

    W* d (\.0+)? ([eE][+-]?0+)? W* } W*

and then FIRST true EOS. Every accepted byte string, after the existing fixed
`{"answer":` prefix, is a syntactically valid JSON with Decimal value int(d).
This is a strict subset: e.g.270 and270.00e-0 are included but27e1 is not.
No claim that all correct spellings are regular by this construction. The DFA
uses one state per matched digit plus six scalar phases, complete20/tail21;
require at most12 digits to fit. Current eight targets have at most three.
Unreachable states reject; empty original emissions keep the current state.
EOS is a control ID, not its printable emission. After it the unused suffix
has weight1 and never changes a recorded fixed ID.

All native confidences/gates/anchor weights are IDENTICAL to the base query.
Let K be its observed-action probability and Z its proposal mass; let K_D,Z_D
be those of the same policy conditioned on the proxy, when Z_D>0. Then

    J_D = (Z_D/Z) K_D,
    z = J_D/K,
    C = z * grad_phi log K_D.

Because Z_D and Z are policy-independent here, this is V11's grad J_D/K.
Autodiff may instead differentiate exp(logQ_D-logQ) while retaining its
derivative; z*S alone is not used. Structural-zero detection must use positive
reachability in the weighted DFA BEFORE any floating logarithm. A positive
event whose probability underflows is a RESOURCE_REFUSAL, not structural zero.
CPU scaled arithmetic can also underflow; report it, do not fabricate C=0.

## Replay contract to freeze after preflight

Input is a52_llada_stopped_resource_v10_initial plus its known-label analysis,
producer e6ef83b and archived evidence53bd428. Inspect all70 in original order;
roots are repeated deliberately to check preservation. Reconstruct every
original BF16 row with the existing binary64 normalization and exact fixed
singletons, original prefix extent/root feature/action. No resampling.

For each transition output base score, proxy prior mass, proxy action posterior
z, projected alpha/beta/anchor vector, structural-support status and independent
Torch comparison. Keep zero cases and verify original traces. NumPy versus
independent log-space Torch: absolute error1e-7 AND relative error1e-7 where
defined; report log-probability error as absolute1e-7. A strict zero event
must be zero in both symbolic CPU reachability and Torch log partition.
If a recorded proposal lies in D, J_D cannot be structurally zero. Check the
proposal proxy with an independent byte regex AND Decimal; never condition
subsequent model calls on it. Preserve all semantic-correct proxy-missed words.

Before replay, the relative-error convention is fixed as
abs(actual-reference)/max(1,abs(reference)); this avoids declaring roundoff in
structurally-zero score coordinates a large relative error. Both this scaled
relative error and the absolute error must be<=1e-7. Existing stricter base
score comparisons remain unchanged. Positive native filtered factors must be
checked BEFORE aggregating classes; factor underflow is a refusal, not zero.

Caps: no pretrained loading/forward; one replay of70 states;1200s whole,
60s per numeric operation;2GiB explicitly tracked sampler payload. Observer
latches foreign GPU PID/query errors during the WHOLE replay, as in V10.
Use existing .venv-live/pinned Torch2.8.0+cu128/NumPy2.4.6 unchanged.
Strict functionality decision requires all70 records with no numeric/trace
error or resource refusal; zero proxy events are legitimate successful cases.
Failure does not trigger more data. Success only permits reconsidering a
separate full-cost variance protocol; no new sampling/training branch yet.
