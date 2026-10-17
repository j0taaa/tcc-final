# V3 native correctness preflight, before adapter/runner execution

2026-10-17. Reassesses README1--8 without promoting the known risk identity.
Real consumer/native semantics remain those of V1. Criterion5 now requires
an unchanged native terminal transition;1/2/3/6/8 useful variance/cost/own
significance remain OPEN. No model/data/latency campaign is triggered here.

## Scope and sources

Copy/hash the necessary Mosaic36945e4b package modules and its integration
source under a NEW native_source_v3 directory, leaving V1 copies literal.
Import the pinned matching/grammar/sampling modules. Extract, without changing
their bodies, `_constrained_step`, `_offset_groups`, `_propose`, `_marginals`
from the plugin AST with its original FREE=-1 constant. This avoids importing
or starting vLLM. All tensor phases, including synthetic self-conditioning,
run with one tensor-parallel worker; no vLLM communication or actual backbone
is used. Record this boundary, not a whole serving reproduction.

Use the existing .venv-mosaic-native, Torch2.13/automata-lib9.2.0, CPU and
CUDA. Do not install/update dependencies or load a pretrained tokenizer/model.
Construct a small synthetic vocabulary with original distinct IDs, aliases,
multi-character JSON fragments, a split numeric prefix, EOT/PAD and thinking
offset tokens. Compile the ACTUAL JSONBuilder x-prob schema for labels a,b
through the native tokenizer-to-automaton code. Model logits have three extra
unrepresentable IDs, which native code must leave unavailable.

## Six fixed fixture families and all replay cases

Use deterministic positive synthetic weights depending only on fixture,
position and token, with larger weights on the three model-only IDs. No
pretrained output or selected semantic observation informs them. Six cases:

1. Full eight-position response, total budget8, no pins or accepted prefix.
2. A two-token thinking offset before the same response; total response
   budget8, ten positions including the offset, thinking IDs pinned.
3. Full response with position1 fixed to the second original-ID alias of0.1.
4. Six-position partial canvas with total budget10: both whole-completion and
   still-completable NONTERMINAL proposals must be recognized by the observer.
5. Full response pinned to a zero first and zero second value, testing the
   common uniform zero-sum fallback and a zero-variance semantic source.
6. Accepted response prefix ends INSIDE a number: prefix fragment plus0.,
   then a six-position remaining block and total response budget8.

For EVERY fixture run original seeds17/29, read_only false/true, CPU/CUDA:
48 native-step replay records in total. Force convergence by the original
maximum-step trigger with synthetic history/counters, not by claiming a model
has actually converged. Use the same original functions and precision policy
for baseline and capture paths. Helpers have budgets0/1/7 and a separately
fixed stream seeded once per readout, never reset before each helper.

## Capture and operator

Intercept only the actual temperature0 `_propose` call of the extracted
native constrained step. Clone its FINAL log-marginals, tokens, offsets, matcher
node/accepted length/budget and accepted response-prefix IDs BEFORE advancement.
Record original returned IDs and before/after RNG for literal replay. Capture
does not replace the original output or change any native control tensor.

Reconstruct a fresh matcher with the saved scalars and shared immutable
compiled language for each auxiliary. Call the same `_propose` on the saved
scores with temperature0. Do NOT run `_marginals` again or substitute raw logits.
Complete means the WHOLE accepted-prefix-plus-new-body contains EOT, only PAD
after it, and strict JSON with exactly the expected probability labels and
finite values in[0,1]. Parse decimals exactly; normalize each complete vector
BEFORE averaging. Charge incomplete helpers; never continue them via a model.
If the ORIGINAL output is incomplete/ineligible, skip helpers and keep it.

After capture, deliberately reuse/overwrite the caller's output-score buffer
and advance the live matcher. Auxiliaries must still use the cloned pre-state.
The original IDs, all other tensor/control state, compiled buffers and caller
RNG streams must be unchanged by the readout. Render with the existing exact
largest-remainder routine at8 decimals and preserve the original raw output.

## Checks and honest limits

* Baseline versus capture: literal equality of ALL original native-step
  tensors/outputs and RNG states, not only decoded text. Snapshot scores equal
  native returned log-marginals. Pins/offset IDs and padded-model exclusion pass.
* Native literal replay under the original saved RNG matches the original
  final call AND its after-state. This is a replay check, not an iid proof.
* Auxiliary calls share immutable H but advance one fresh local stream.
  Restore Python/NumPy/Torch CPU/CUDA caller RNG and global precision/thread
  policy; restarting from original-before state at each helper is disallowed.
  H in the mathematical theorem excludes UNUSED random bits. A stored RNG
  state is replay provenance, not evidence for independent ideal random draws.
* Independently enumerate all positive state paths of each small frozen final
  operator, with manual emission sums/forced-token treatment/within-edge argmax.
  Check every sampled ID sequence is in that support, every observer outcome,
  complete/incomplete classification and zero-sum handling. This REAL-ARITHMETIC
  path reference does not prove the exact torch.multinomial finite-RNG law.
  Native constrained log-marginals may differ from independent float64 path
  marginal calculation by at most5e-5 on these fixtures; report max error.
* The full response, offset, pinned alias, partial number and nonterminal
  families must all execute. Preserve any refusal/error; missing cases cannot
  be called an all-case PASS. A zero-variance fixture is retained without
  claiming a variance/quality benefit. No Monte Carlo success-rate gate.

Guards:600s total,2GiB incremental GPU allocation,500000 enumerated paths per
fixture; no favorable credit from a guard or empty language. Write raw progress
per record and complete metadata. No concurrent neural/timing campaign.

Freeze adapter/runner BEFORE any native call. If source/runtime fails, preserve
the exact draft/partial result and write a correction BEFORE a later rerun.
Passing this preflight permits only a separately frozen resource/variance
necessity protocol with real input selection and strong controls. It is not
native forecast accuracy, publication novelty, a forward-saving measurement,
or fulfillment of the full positive scientific goal.
