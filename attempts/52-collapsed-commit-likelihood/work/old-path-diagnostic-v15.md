# V15 — Existing16-path variance DIAGNOSTIC, before code/calculations

2026-10-16, after V13 functionality and V14's fixed nine-parameter actor.
This is exploratory development on already KNOWN data, not a preregistered
independent confirmation or a competitive complete-cost/training experiment.
No favorable gate is defined, and no new pretrained forward/sample/label/update
is authorized by this diagnostic. Do not close a general hypothesis from two
trajectories per question or call their ranking statistically established.

## Eight criteria

1. Operation: compare finite-path REINFORCE gradient estimates at the SAME
   frozen V10 actor, in V14's9 fixed coordinates, on ALL16 recorded paths from
   ALL8 questions/70 transitions. Original V10 generation/rewards stay intact.
2. Method is classical score projection/control variates. No new RB, baseline,
   policy-gradient or weighted-inference principle is claimed. Own sufficient
   scientific difference/usefulness are still open.
3. Purpose: assess whether another, costly fresh-data variance study is
   plausible against stronger controls; no semantic/latency benefit follows.
4. Correctness: state baselines are current/pre-action functions; sampled
   semantic full/anchor controls and exact regular control have zero mean by
   V11/V14. Same fixed linear actor map for every term. All coefficients below
   are fixed BEFORE viewing these gradient variances, never fit on this data.
5. Minimal chain-rule/gradient and serialization checks precede replay. Freeze
   actual source/runtime/old-input hashes before reading original heads for
   the new state features and computing ANY trajectory gradient variances.
6. Every cost/status retained, but CPU diagnostics under shared load are NOT
   deployment cost measurements. Reuse existing heads ONLY to derive original
   full-V max-confidence state features; no proposal/head is sampled or trained.
7. Objections: two trajectories give a very uncertain variance estimate;
   pilot-fitted state/horizon critics, arbitrary-sign coefficients, RLOO,
   cheap score mixtures and other actor parameterizations can change rankings.
   They remain required in a later real protocol. No per-question dropping,
   baseline/coordinate tuning or selected winner becomes a confirmed result.
8. Gaps: independently fitted strong controls, fresh complete paths, full cost,
   learning/application, novelty and independent evidence. The scientific goal
   remains open whatever these16-path estimates show.

## Fixed diagnostic configurations and estimand

All seven V10 score readouts: full_triple,anchor_integrated,class_integrated,
length_integrated,combined_partial,known_anchor,collapsed. Project to V14 actor
coordinates; confidences are unchanged ORIGINAL full-V rows, with fixed bits.
At each pre-action state let p_s=exp(log prior proxy mass) from V13, or0 for
structural-zero prior. Every method gets four fixed state baselines:

    0, 1/2, p_s, p_root(question).

And EVERY method gets all27 triples (a,b,c) in {0,1/2,1}^3 of control
coefficients for exact regular C, raw semantic-proposal full score W_F and
raw semantic-proposal anchor-integrated score W_A. Compute

    G = sum_t [(R-v(s_t))*score_t - a*C_t - b*W_F,t - c*W_A,t].

All756 configurations and ALL16 gradients remain. No evaluated coefficient
fit or choice is presented as an unbiased fitted method. Current proposal's
semantic reward comes from V13's official-tokenizer/Decimal audit. It is
never naively multiplied into a class/visible score. State baseline p_s is
held fixed when differentiating, even though its inputs include a known label.

For each question q with its two independent declared draws, the FIXED method
estimate .5*||G_q0-G_q1||^2 is an unbiased single-path trace-variance estimator
under the ideal iid interpretation. Report each question and sum_q/64 for
the equal-weight eight-question MEAN gradient. Do not treat questions with
different means as interchangeable iid trajectories. Report the5 gate,3
anchor and1 confidence blocks separately. Tiny or zero observed estimates
are not zero population variance or strict improvement. No significance gate.

RLOO with only two draws has ONE independent group per question. Its group
gradient can be reported, but its variance is NOT estimable by treating the
two dependent individual contributions as iid. Return variance=null for RLOO;
do not compare a fictitious RLOO variance to the756 fixed estimators.

Report the full table and optional development-only minima WITH the label
"selected on the same16 paths; optimistic diagnostic, not an unbiased
performance estimate of a selected method". No new training/quality campaign
is automatically triggered by any such minimum.
