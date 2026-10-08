# M36 — execution-conditioned Boolean rule reference

This records completed technical work, not approval of scientific novelty,
whole-code formal verification or production-decoder promotion. The stable
main manuscript and serial/EPIC/MWPC strategies are preserved.

## Producing source and immutable inputs

Clean source: `2be61a9773a016930dc407ab051d6f2d497704a0`.
Config: `configs/experiments/m36_semantic_reference_v1.json`.
Raw: `docs/artifacts/raw/m36_semantic_reference_v1/` (`config.json`,
`input.json.gz`, `rows.jsonl` and SHA256SUMS). Model/tokenizer revisions,
checkpoint/adaptation/grammar hashes, support, EOS, seed, hardware and software
are in the original result metadata. Weights, caches and full logits stay local.

Executed successfully from that clean source:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv-live/bin/python -m scripts.exact_commit.capture_semantic_reference --capture --directory docs/artifacts/raw/m36_semantic_reference_v1 --consumer .cache/jsonlogic/logic.js --full-capture .cache/semantic-reference-v1.npz
```

All 108 represented rules agree with an independent JSON executor and the
official JsonLogic library on all eight Boolean records. Both declared positive
targets produce 16 samples; the preregistered unrepresentable parity target
has zero mass. The full-vocabulary softmax and selected original-token rational
weights pass an independent NumPy audit. Captured probabilities are the real
pinned CPU MDLM output, with the documented F32/F64 adaptation, not invented
scores. The lexical support is declared, not full vocabulary coverage.

The optional consumer is Jeremy Wadhams' MIT-licensed JsonLogic source at
`c5c73601c90b11e98f6846609bac4dec203d1c18`; URL and SHA-256 are pinned in the
config. Its 14,844-byte source remains a local cache; execution used Node
`v24.19.0`. Offline checks need neither Node nor model dependencies.

## Current verification

`make check test`: lint/format/type checks and **16 focused tests passed**,
including current-solver archived recomputation. Tests independently enumerate
token paths and JSON-tree behavior, cover nested shapes, aliases, fixed slots,
zero/reduced weights, resource refusal and exact integer sampling decisions.
The historical suite remains deleted. Every semantic cell's total integer
mass is compared with its corresponding scalar syntax mass before final
normalization, so a loss cannot be hidden by renormalizing the root.
The covering-product oracle also executes the optimal recursive non-negative
control on the same vectors and checks its `3^m` product / `2(3^m−2^m)` addition
counts against the written recurrence, independently of the transform.

Offline replay exactly reproduced the capture's rational masses and statuses:

```bash
.venv/bin/python -m scripts.exact_commit.capture_semantic_reference --directory docs/artifacts/raw/m36_semantic_reference_v1
.venv/bin/python -m scripts.exact_commit.capture_semantic_reference --directory docs/artifacts/raw/m36_semantic_reference_v1 --summary > docs/research/generated/m36-semantic-summary.md
.venv-live/bin/python -m scripts.exact_commit.capture_semantic_reference --directory docs/artifacts/raw/m36_semantic_reference_v1 --consumer .cache/jsonlogic/logic.js --full-capture .cache/semantic-reference-v1.npz
```

The summary is generated from exact masses. Its geometric trial counts compare
independent rejection under the **same** syntax-conditioned product law; they
are not measured times or native EPIC performance. Original capture's optional
consumer/full-logit successes are kept distinct from ordinary offline replay.

Source commit `2be61a9` passed Rust builds, unchanged historical artifact checks,
Lean's 50 audited statements and the main 16-page PDF check. Its GitHub Actions
run [37704248806](https://github.com/j0taaa/tcc-final/actions/runs/37704248806)
passed both jobs, including all then-existing 15 tests. This follow-up adds the
sixteenth real-input recomputation; its CI result must be verified separately. The updated research supplement
builds as a four-page PDF without overflow or unresolved references; all four
rendered pages were visually inspected.

## Mathematical and scientific boundaries

The written supplement proves original-token execution conditioning and
sampling, and a tight bilinear-plan comparison for **all** dense union-profile
outputs: `3^m` products with non-negative coefficients versus `2^m` with signs.
The known covering transform attains the signed bound; it is credited to
Björklund et al. Weighted synthesis/tree automata are credited to Wang et al.
The comparator is optimal within the explicit non-negative bilinear class,
not an intentionally weak dense enumeration.

Nine added Lean statements check the finite ternary witness/rectangle argument
and the natural-coefficient lower bound with a positive common tensor scale.
Rational denominator clearing, real-coefficient reduction, signed optimality,
sampling and implementation refinement remain written/tested obligations.
The result does not lower-bound one target query, adaptive sparse algorithms,
every factor encoding or whole dLLM inference. No general speed superiority
over EPIC/FactorDLM is claimed; a classical solver using the transform shares
the advantage. The application is a fixed-template illustration, not a held-out
external benchmark or a guarantee of behavior on records not supplied.

T3607/T3608 are completed technical artifacts. T3602–T3605 retain their
scientific-priority, real human-review and publication-promotion gates.
