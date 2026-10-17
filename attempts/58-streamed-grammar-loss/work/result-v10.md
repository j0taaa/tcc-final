# V10 — Full-head resource gate is NEGATIVE; no native training triggered

2026-10-16 local date. This is a result AFTER the frozen V7 protocol and V8/V9
addenda. The original V1 archive and every previous producer remain literal.
The eight scientific criteria in README/V5/V6 still apply; the measured
systems advantage in criteria3/5 FAILS. Criteria2/8 (own distinction and
publication significance) remain unestablished. This is not the user's goal.

## Before timings: stronger controls, metadata and arithmetic

V5 physical-layout control note70157a7 precedes implementation88ce301. It
permutes classifier/tied-input/optimizer coordinates once, batches small
classes and assembles disjoint class gradients. Both maintained CPU oracles
pass. All96 old-fixture/backend/threshold cases pass at88ce301. Hoisted fixed
support at5d68227 also passes96/96, with1,142,256 comparisons in each packet.

V6 note76275ee precedes four launch configurations785efa6. All32 tile/fixture
cases pass380752 comparisons. Metadata builderf52b751 reads ONLY the existing
packet's vocabulary.json, not numerical model weights or heads. All50258 IDs
map to194 lexer classes, SHAe7b5575b519dadb1b0f2402ba708c13549bbe75f6f27f50d47b047dca4ee8a1f.
The pinned public MDLM config supplies D768; all H/W/b values are synthetic.

Resource protocolf177be0 precedes runnere93c8ee and ALL competitive timings.
V8 note2618e03 precedes bucketed merge82f61b9:32/32 old fixtures pass380752
comparisons. Both old and bucketed configurations remain in the timed family.
V9 note321a56d precedes output-buffer host adapterd5131bd: unmodified pinned
CCE kernels write directly into final gradients. Its source/license are
credited. Native autotuning resets output buffers, so the adapter explicitly
refuses it; measurements use the native default heuristic, filtering OFF.
This additional guard/source pin is inbb6ced4, before ANY timing.

The first V9 CLI pointed to a nonexistent input directory and exited before
fixture evaluation. Its config/trace are preserved in
evidence/strong-v9-out-launch-failure. Replayd5131bd on the actual frozen V4
inputs passes128/128 configurations,1,523,008 output/gradient comparisons.
This is not attributed retroactively to older96-record packets. Adding the
heuristic-mode refusal does not alter that replay's math or relabel its source.
The actual timed source checks correctness again at every new geometry.

Primary MonoidReduce indexed excerpts already expose general arbitrary-
adjoint recomputation. Direct original PDF retrieval still returns browser
verification; the complete proof/listing/source has NOT been obtained.
Generic monoidal streaming, CCE, permutation and the known semantic loss are
not claimed as ours. No priority claim follows from this experiment.

## Executed resource screen

Producer **bb6ced4209a2f27ad2518308cdb4955417ed4fca**, runtime Torch2.13.0+cu130,
Triton3.7.1, RTX3080Ti, FP32 IEEE. All8 N values16--2048, all8 candidates and
the4 first-stage controls were executed. Those controls are dense segmented
GEMM, CCE128, checkpoint128/panel8192 and CCE_out128. Physical parameters
remain sorted between calls; there is no per-step full-weight reorder or
unnecessary original GPU copy. Full H/W/bias gradients count toward workspace.

**680/680 records:**8 common validations,96 FP64 validation PASS,288 complete
preparation/first calls,288 complete warm measurements; ZERO errors/refusals.
Every warm record averages5 complete head forward+scalar+backward calls;
there are3 paired repetitions per method/N. Full output/gradient checks total
3,757,395,168 scalar comparisons; maximum scaled error0.058185 at the frozen
5e-5+5e-5|reference| tolerance. These are floating checks, not exact proofs.
No test suite/other GPU job ran concurrently. RNG restoration passes.

**ALL EIGHT candidates have0/8 wins and0/8 possible wins against the completed
four-control subset.** The predeclared negative-only shortcut therefore
rejects the full gate without timing its other10 controls. They are listed
in summary.json and have NO fabricated measurements. Adding further required
controls cannot undo a failed necessary comparison with a completed control.
This is a complete first stage and a necessary negative decision, not a full
22-method benchmark or independent statistical confirmation.

The following minima are AFTER-data diagnostics across all8 candidates,
not selection of a new candidate or a revised gate. Times are median ms/call.

| N | Fastest candidate | ms | Fastest measured control | ms |
|---:|---|---:|---|---:|
|16|bucket16x32|2.528|dense|3.161|
|32|bucket32x64|3.910|dense|4.421|
|64|tile32x64|6.752|checkpoint128p8192|5.098|
|128|tile64x128|12.792|checkpoint128p8192|5.379|
|256|bucket32x64|24.675|checkpoint128p8192|7.895|
|512|bucket32x64|48.407|checkpoint128p8192|14.356|
|1024|bucket32x64|103.527|checkpoint128p8192|25.618|
|2048|bucket64x128|209.509|checkpoint128p8192|49.042|

Even the favorable N16 median cannot earn a win: bucket16x32's first paired
repetition2.898ms exceeds dense2.798ms, violating the unchanged all-repetition
sign condition. At N2048, candidate workspace around159MiB is lower than
CCE_out's215MiB, but candidate latency exceeds the fastest control by over4x.
The memory alternative requires latency<=1.10x the fastest control too.
Dense-only memory savings do not meet the gate against competent controls.
All CPU times, repeated peaks, cold observations and source/input hashes are
retained. First calls reuse shared compiler caches; no clean cold win is claimed.

## Decision, scope and reproduction

Do NOT trigger native training, extra seeds or an independent model campaign
for this simple kernel/layout family. No own useful systems contribution is
confirmed. This does not refute every future architecture or grammar objective.
Any expansion needs a substantive new distinction and separate justification,
not relaxed thresholds, favorable N selection or renamed old measurements.
The frozen loss/gradient algebra remains a reference/control only.

The A58 control/resource runs contain ZERO model parameter reads, fresh neural
heads/forwards, semantic labels or optimizer/model updates. Grammar inference, backbone and optimizer
were not timed. Whole-training quality/speed, a trained dJev and publication
are NOT established. The positive scientific goal remains OPEN.

Raw evidence: evidence/resource-v7-initial/{config,records,summary,
phase-I-decision}.json[l], input-N*.json and completed stdout.log. The AFTER-
data independent arithmetic audit in audit_resource_v10.py recalculates
medians/peaks and supplies both speed and memory rejection witnesses for all
64 candidate/state pairs, without importing the gate implementation. Its
output is evidence/resource-audit-v10.json, not an independent new dataset.

Reproduce from the measured producer, using a fresh output directory:

```sh
OPENBLAS_NUM_THREADS=4 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 \
.venv-mosaic-native/bin/python \
  -m attempts.58-streamed-grammar-loss.work.benchmark_resource_v7 \
  --output <fresh-directory> \
  --cce-source /home/jota/.cache/tcc-final/a58/ml-cross-entropy
```

The source verifies the pinned CCE revision3de376c and its file hashes. Input
recipes/runtime and exact byte hashes are in the frozen protocol/config.
Later archive/check receipts are preservation evidence and must not be
attributed to the earlier measured producer.

Later maintained validation (after timings, not attributed to their producer):
full326 tests PASS93.764s; focused Ruff check/format PASS32 files. The complete
logs are evidence/full-tests-v10.log and evidence/ruff-v10.log. Existing legacy
fixtures remain part of that suite; these checks are not new A58 neural data.
