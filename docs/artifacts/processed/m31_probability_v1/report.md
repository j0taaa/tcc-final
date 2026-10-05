# Scientific relevance audit: complete larger-canvas results

Original-input certificates, independent exact controls, complete grid and provenance: **PASS**.

18 fresh official CPU MDLM predictions; 36 partition jobs;
35 returned certificates independently accepted.

## Verdict

Mathematical validity and the checked admission/refusal interface survive this
audit. A general practical advantage does **not** follow. The compact exact
control resolves every canvas with zero conditional approximation error and
lower observed inference cost than every returned partition job. This rejects
a superiority claim on these two schemas; it does not prove that every CFG
has such a compact representation.

The contribution is an incremental finite-slot/token-provenance certification
specialization. Conditioning, WMC, deterministic anytime bounds and alphabet
filters are established. Novelty priority, semantic accuracy, production benefit
and universal runtime superiority remain unestablished. No percentage of
scientific certainty is assigned.

## Complete scaling outcomes at 64 calls

| Free token slots | Canvases | Admitted at TV <= 0.05 |
|---:|---:|---:|
| 4 | 6 | 5 |
| 8 | 6 | 1 |
| 16 | 6 | 0 |

All-job statuses: `{"certified_tolerance": 8, "external_timeout": 1, "incomplete": 27}`.

The exact control sums as many as 14,082,354,344 positive original-token paths
without enumerating them. Its measured coverage + compilation + median
forward/backward/sample cost ranges from 11.714 to 81.180 ms. It is faster
in 35/35 returned-job comparisons. External timeouts are retained and
excluded from paired numeric timing ratios.

## Every method job

| Canvas | Cap | Status | TV bound | True TV | Solve/check (s) | Check (s) | Reference (ms) |
|---|---:|---|---:|---:|---:|---:|---:|
| recursive_one_child_arrays_depth1-4 | 8 | incomplete | 0.873428 | 0.000368455 | 0.575060 | 0.313017 | 11.761 |
| recursive_one_child_arrays_depth1-4 | 64 | certified_tolerance | 0.0332598 | 5.83074e-08 | 0.708582 | 0.467341 | 11.761 |
| recursive_one_child_arrays_depth1-8 | 8 | incomplete | 0.999731 | 0.757772 | 0.392846 | 0.190892 | 14.975 |
| recursive_one_child_arrays_depth1-8 | 64 | incomplete | 0.827113 | 0.0119885 | 2.838716 | 1.624234 | 14.975 |
| recursive_one_child_arrays_depth1-16 | 8 | incomplete | 1 | 0.932212 | 0.629646 | 0.246861 | 24.864 |
| recursive_one_child_arrays_depth1-16 | 64 | incomplete | 0.999985 | 0.721009 | 4.274046 | 1.986745 | 24.864 |
| recursive_one_child_arrays_depth3-4 | 8 | incomplete | 0.920158 | 0.094554 | 0.274315 | 0.132708 | 11.714 |
| recursive_one_child_arrays_depth3-4 | 64 | certified_tolerance | 0.0112235 | 0 | 1.026759 | 0.666607 | 11.714 |
| recursive_one_child_arrays_depth3-8 | 8 | incomplete | 0.999803 | 0.880585 | 0.400945 | 0.196465 | 14.821 |
| recursive_one_child_arrays_depth3-8 | 64 | incomplete | 0.993209 | 0.558532 | 2.543897 | 1.292670 | 14.821 |
| recursive_one_child_arrays_depth3-16 | 8 | incomplete | 1 | 0.937891 | 0.771651 | 0.269912 | 25.014 |
| recursive_one_child_arrays_depth3-16 | 64 | incomplete | 0.999999 | 0.804099 | 5.890827 | 2.075346 | 25.014 |
| recursive_one_child_arrays_depth8-4 | 8 | certified_tolerance | 0 | 0 | 0.365924 | 0.290589 | 12.085 |
| recursive_one_child_arrays_depth8-4 | 64 | certified_tolerance | 0 | 0 | 0.375291 | 0.327088 | 12.085 |
| recursive_one_child_arrays_depth8-8 | 8 | incomplete | 0.999818 | 4.92506e-06 | 0.702313 | 0.282913 | 15.596 |
| recursive_one_child_arrays_depth8-8 | 64 | certified_tolerance | 0.030704 | 9.27277e-07 | 5.671447 | 1.875928 | 15.596 |
| recursive_one_child_arrays_depth8-16 | 8 | incomplete | 0.999999 | 7.15992e-05 | 1.085585 | 0.296827 | 27.042 |
| recursive_one_child_arrays_depth8-16 | 64 | incomplete | 0.999891 | 6.79934e-05 | 8.581420 | 2.956900 | 27.042 |
| recursive_arrays_depth1-4 | 8 | incomplete | 0.981377 | 0.402721 | 0.374062 | 0.180900 | 12.658 |
| recursive_arrays_depth1-4 | 64 | certified_tolerance | 0.0446197 | 2.90946e-07 | 1.324830 | 0.739247 | 12.658 |
| recursive_arrays_depth1-8 | 8 | incomplete | 0.999954 | 0.766928 | 0.883980 | 0.127050 | 18.346 |
| recursive_arrays_depth1-8 | 64 | incomplete | 0.995202 | 0.194669 | 4.656678 | 1.469354 | 18.346 |
| recursive_arrays_depth1-16 | 8 | incomplete | 1 | 0.963147 | 3.224370 | 0.335180 | 59.787 |
| recursive_arrays_depth1-16 | 64 | incomplete | 1 | 0.941134 | 19.671467 | 1.860010 | 59.787 |
| recursive_arrays_depth3-4 | 8 | incomplete | 0.99247 | 0.507897 | 0.273948 | 0.088838 | 13.187 |
| recursive_arrays_depth3-4 | 64 | incomplete | 0.0666319 | 0.000230285 | 3.020602 | 1.611143 | 13.187 |
| recursive_arrays_depth3-8 | 8 | incomplete | 0.999998 | 0.967639 | 0.602610 | 0.120937 | 20.235 |
| recursive_arrays_depth3-8 | 64 | incomplete | 0.999889 | 0.889867 | 4.559951 | 0.910102 | 20.235 |
| recursive_arrays_depth3-16 | 8 | incomplete | 1 | 0.993583 | 3.241063 | 0.249965 | 65.631 |
| recursive_arrays_depth3-16 | 64 | external_timeout | -- | -- | -- | -- | 65.631 |
| recursive_arrays_depth8-4 | 8 | certified_tolerance | 0 | 0 | 0.548814 | 0.248350 | 13.973 |
| recursive_arrays_depth8-4 | 64 | certified_tolerance | 0 | 0 | 0.546711 | 0.247186 | 13.973 |
| recursive_arrays_depth8-8 | 8 | incomplete | 0.999911 | 6.88431e-06 | 0.663615 | 0.120250 | 24.208 |
| recursive_arrays_depth8-8 | 64 | incomplete | 0.944032 | 4.94233e-06 | 6.900487 | 1.161444 | 24.208 |
| recursive_arrays_depth8-16 | 8 | incomplete | 1 | 0.000178862 | 1.375131 | 0.120668 | 81.180 |
| recursive_arrays_depth8-16 | 64 | incomplete | 0.999999 | 0.000167362 | 25.525557 | 1.900949 | 81.180 |

## Comparison and availability boundaries

These are controlled schema/scaling probes, not an external semantic benchmark,
production requests, or a new full denoising trajectory. They cover one-child
arrays and recursively nested arrays with multiple children. All prefixes and
4/8/16-slot combinations were frozen before predictions. The 36 cells reuse
18 predictions; repetitions are not new requests.

The control independently implements standard finite-state/counter transfer.
It is not an execution of Dang--Ermon, FactorDLM or CARS. It shares original
probabilities, token IDs, fixed slots and ABSENT EOS. Full vocabulary scope
requires every alphabet-compatible original token to be retained. Count tokens
once per original-token path, including aliases. Never renormalize retained rows.

Reference time includes coverage validation, transition compilation and a median
of three query repetitions after one warmup. Each query includes forward,
backward and sampled-output JSON/schema validation. Parser time includes proof
construction and internal validation; external portable checking is separate.
Call caps count primary selection queries; proof construction can issue further
parsing queries and is included in measured solver time.
Input/logit reconstruction and model forward are separate/shared in raw rows.
Process startup and serialization are outside reference/solver core; external
wall times are retained. A certifying engine and an exact numeric control expose
different interfaces: these are diagnostic inference-cost comparisons, not
full-deployment runtime rankings.

Fresh reference and parser worker RSS include imported libraries. Original
controller-reference timings lacked a separately recorded coverage scan. They
are preserved unchanged but excluded from the final cost comparison. A separately
committed follow-up repeats only exact reference queries on the same inputs,
including coverage time and a fresh-worker memory boundary. No model or
partition outcome is repeated or replaced.

Full logits/probability matrices remain in the ignored local capture; large
traces are not committed. Git contains complete tokenizer semantics, retained
exact rational inputs, normalization/array hashes, every returned proof, all
statuses and generated evidence. The default verifier reproduces mathematics
and tables offline. `--capture` additionally checks every retained probability
and normalization against the full local logits/softmax and tokenizer bytes.
Full-logit availability is limited accordingly. A fresh opt-in checkpoint run
is a reproduction, not a claim of bitwise GPU equivalence.

Producing commit: `7780d94763d146799de564b38a328f3dd4686756`.
Reference timing follow-up: `bb93550c6d5754ff193a612f05d9364dfc9514ca`.
Immutable primary manifest: `3c677037d41fa7dda5f14f22e134e0226811227ebcc94b8692e8e5237affa486`.
Immutable reference manifest: `c900665d75685ed9c0c44dc529146e5955f89cc82d3812bc62729f0952770b24`.

Prior-art scope and pre-measurement falsification criteria:
`docs/research/m31-relevance-audit.md` and
`docs/research/m30-probability-certificates.md`.
