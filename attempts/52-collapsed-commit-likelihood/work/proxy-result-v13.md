# V13 — ALL70 real OLD states pass CPU functionality, not variance/cost

2026-10-16, producer0381620, after written d3c69b7 contract and FAKE-driver
preflight. Exactly70/70 original V10 transitions PASS,0ERROR/0REFUSAL/0NOT_RUN.
No new pretrained forward, sampled word/trajectory, label or parameter update.
All inputs/golds were already known development data; this is not confirmation
on independent questions. V12's GPU startup refusal remains preserved separately
with70NOT_RUN and is NOT relabeled as this CPU pass.

Support outcomes:33 positive proxy action posteriors,10 structural-zero actions
with a positive prior,27 structural-zero priors. All37 zero controls remain
in the data. Positive posterior range2.7391292010592244e-8--1.0. Independent
NumPy versus Torch CPU scaled/log-space autodiff errors are at most
1.042568809062061e-14. These are floating consistency checks, not a global
exact-native-RNG/arithmetic certificate. Rational laws were checked separately.

All126464 IDs,115 empty aliases, physical first-EOS positions, fixed original
IDs, frozen native confidences and V10 root features are retained. The proxy
never constrains generation and is only a training-baseline query. An AFTER-data
auditor checks all70 proposals using the official tokenizer/json/Decimal plus
independent regex, all manifests, statuses and correction vectors. It finds24
semantically correct proposals, all included in the restricted regular proxy;
zero misses in THESE proposals is not completeness of the proxy language.

CPU-only peak entire process RSS1,692,696,576bytes is under2GiB; no CUDA context
or GPU operation is used. Setup7.235s/replay115.480s are DIAGNOSTIC under shared
host load, not optimized latency, a GPU comparison or a full-cost result.
The70-record FAKE-driver regression and initial parse-error draft are preserved
separately in evidence/proxy-cpu-v13-{before-replay,initial-draft}.

Raw complete output/protocol/source pins/statuses/scores/proxy vectors and
post-capture audit: docs/artifacts/raw/a52_proxy_cpu_functionality_v13_initial.
The runner's original manifest is immutable; a separate packaging manifest
covers late audit/log additions. Audit source was written AFTER these outputs
and is not attributed to producer0381620.

The pass establishes that the projected proxy is computable at the actual
recorded consumer states. It does not establish useful variance, cost-adjusted
sample efficiency, learning, semantic superiority, originality or publication.
V14 strengthens comparisons with raw semantic-proposal controls for EVERY
estimator, and writes one common nine-parameter actor before variance analysis.
Only a separately frozen strong-control necessity/cost protocol is next.
