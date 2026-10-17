# V2 — Correct score; no justified training expansion from these properties

2026-10-17. AFTER the frozen V1 reference/oracles, before any A61 neural head,
update, dataset-row read or competitive timing. This note changes the decision,
not the V1 score/proof/software or its recorded outcomes.

## A complete numerical-distance objection

For any finite decimal epsilon in (0,1), let y=10-epsilon and

    P = (1/4) delta_y + (3/4) delta_10,   Q = delta_1.

Both are valid numerical predictive laws; a one-slot source with whole-numeral
token emissions realizes them exactly. Under V1, y has positive category0,
where P has probability1/4 and conditional mantissa point mass at y. Therefore

    L(P,y)=log4,                 L(Q,y)=(9-epsilon)/9 < 1 < log4.

The last strict inequality follows, for example, by integrating1/t over[1,2]
and[2,4], strictly above the lower rectangles of total area1. Meanwhile

    CRPS_value(P,y)=9 epsilon/16, CRPS_value(Q,y)=9-epsilon.

Thus an arbitrarily accurate, tightly concentrated forecast is ranked worse by
V1 than a very distant one. A deterministic forecast at10 even has unsupported
category/infinite V1 loss. These are analytical counterexamples to an automatic
numerical-proximity advantage, NOT a measured quality failure or contradiction
to strict propriety. Propriety is a population distributional statement, and
does not order every pair of misspecified forecasts by numerical distance.
The distinction is consequential for finite-capacity denoisers.

Decimal-only invariance is also concrete: y=9 and P=(delta_9+delta_10)/2 give
L=log2. Scaling both by2 gives y'=18 and P'=(delta_18+delta_20)/2. Both atoms
now share category1, giving L'=CRPS((delta_1.8+delta_2)/2,1.8)/9=1/180.
Hence no arbitrary-unit invariance follows. The V1 integer-decimal-shift theorem
remains intact. No alternate score has been silently substituted to remove
this objection.

## Stronger objective controls remove the proposed exclusive guarantees

For supported exact targets, complete semantic NLL is already strictly proper
on values and invariant under any bijective relabeling, including rescaling.
Its source-logit gradient is P_G(I)-P_y(I): row L1 at most2 and component at
most1, independent of output magnitude. Those are at least as favorable as
V1's bounds4/2. It requires only the valid and target-value partitions, without
the two-copy mantissa kernel. This is a classical identity, not an implemented
benchmark or a claim of universal objective dominance.

NLL is infinite on an unreachable exact target. V1 can still score a target
whose exact value is absent when its category has mass. This is a real contract
difference, but direct continuous probabilistic heads, interval/quantization
likelihoods and scientific-codec conditional proper scores also address that
situation. They cannot be excluded to create an artificial advantage.

Canonicalization already repairs V1's constructed alias example. When clamps
prevent canonicalizing a completion, semantic NLL remains a relevant control.
Generic complete weighted-automaton/kernel composition already computes V1's
same objective. An efficient implementation could be useful, but correctness
of that implementation alone would not establish a new inference principle.

GenRe2's FINAL ICML2026 method already combines whole-number reward training
with on-policy expert-token supervision, including code metrics. Its original
arXivV1 is an earlier method and must not stand in for the final comparator.
TabDLM and ICF-DLM also preclude treating continuous numerical modeling or
whole-number rewards with masked diffusion as an empty research area. Their
different contracts are recorded in primary-reading-v2.md; their reported
results are NOT results of this repository.

## Real-consumer audit, without a performance experiment

The pinned RegressLM source and public model/dataset cards provide an available
code-to-metric route. No weights, data Parquet or dataset rows were downloaded,
and no third-party code was executed. Cards include aggregate label statistics
and these HAVE been read; this is not a pristine blind evaluation. Future
protocols must disclose that exposure and define independent evaluation.

The alternative Makora card explicitly leaves measurement units, GPU and harness
unspecified and warns against cross-problem comparison. It supports a plausible
within-problem ranking consumer, not independently reproducible absolute-latency
calibration. Code-Regression provides profiled latency/memory data but its
checkpoint card declares training on that source. Dataset membership alone is
not independent generalization evidence; split/pretraining leakage needs audit.

Native IEEEFloatTokenizer's allowed mantissa digits INCLUDE leading0; its
nominal exponent is therefore not always the semantic order. Negative exponent
zero aliases and signed/all-zero mantissas also remain. A canonical new codec
would change the contract and is a legitimate comparator, not preservation of
that native distribution. The source decoder is autoregressive; no polynomial
one-head product computation has been shown to preserve its final law.

## Decision and eight-criterion reassessment

1. Consumer identified, but no A61 dLLM consumer/training integration validated.
2. The conditional-score/gradient/kernel principles are classical; a substantial
   own difference has not been established by this prototype.
3. The candidate's claimed properties do not establish an exclusive advantage;
   the explicit boundary case undermines a general proximity justification.
4. Keep the written propriety/gradient/bit results with their hypotheses. They
   are correctness/application properties, not a comparative usefulness proof.
5. Four independent V1 rational oracles and the345-test suite pass. No numerical
   quality or competitive timing hypothesis has been tested for A61.
6. Two-copy inference, full neural/optimizer costs and the native iterative law
   remain unvalidated. Bounded exact gradients do not imply floating-point
   stability of naive rare-class ratios or bounded backbone gradients.
7. Canonical completion, semantic NLL, codec scores, GenRe2 and strong continuous
   heads remain mandatory. No favorable toy may stand in for those controls.
8. Retain V1 as a bounded mathematical/reference artifact. Do NOT expand this
   simple score to a neural campaign or promote it as the article protagonist
   on the present rationale. This is a decision against expansion, not an
   empirical refutation of every conditional-score application.

The original positive scientific goal remains OPEN. Useful training benefit,
specific priority, publication significance and human review are not supplied
by passing tests or available public data. A new candidate must first identify
a surviving useful difference; changing the name, adding a mixture, or compiling
the classical kernel is not sufficient by itself.
