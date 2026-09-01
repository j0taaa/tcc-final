# M12.5 completion audit

- Audit date: 2026-09-01
- Audited implementation commit:
  `7b0d9aabeeaa3388b4b652b9e24d66f0da9b784d`
- Pinned EPIC commit: `5b1b31098f34ed3691d2a9f4aae14fdf5839d072`
- GitHub Actions:
  [`33468417087`](https://github.com/j0taaa/tcc-final/actions/runs/33468417087)
  (`verify`, `rust-correctness`, and `epic-integration` all passed)

This audit treats the checked boxes in `TASKS.md` as claims to verify. It
checks every T1250--T1261 acceptance criterion against the current source,
configs, pinned rows, regenerated summaries, clean-install behavior, tests,
paper build, and remote CI state. The governing scientific contract remains
the one in `AGENTS.md`: exactness is only `exact_on_support`, solver statuses
remain distinct, and every `OPTIMAL` result carries an independently
recomputable certificate.

## Requirement-by-requirement result

| Task | Direct evidence checked | Audit result |
| --- | --- | --- |
| T1250 | The release wheel contains 50 `mwpc_exact` and 19 `mwpc_research` Python files. Both imports resolve outside the checkout; installed-wheel Q3 and artifact smokes pass. Two deliberately incomplete test wheels, each omitting one package, are rejected. | Pass |
| T1251 | The regenerated Q1 table reports 5/5 canonical, 144/144 exhaustive, 100/100 randomized, and 249/249 overall agreement. Only the randomized family has a Wilson interval, and its 100 consecutive seeds are recorded. | Pass |
| T1252 | ADR 0016 and its amendments map Q1--Q5 claims to evidence. All six legacy full configs remain `publication_mode=false`; the accepted Q2 v2, Q4 v1, and Q5 v4 configs use `publication_mode=true` and `m125_publication_results_v1`. Git history proves that the policy/config decision predates every producing commit. | Pass |
| T1253 | The pinned Q5 corpus hash is `8acfb789e14779c9c33c7fec50fb713194797a2a5ae1a2ad59a56f5f5e266f44`: 240 rows, two structured tasks, three seeds, ten repetitions, and four distinct strategies. The validator recomputes the six run summaries, observes 330 EPIC regular-cover calls, a maximum batch of two in every task/seed pair, independently valid constrained outputs, and 60 validated exact optimizer certificates. Fallbacks remain explicit. | Pass |
| T1254 | The snapshot and replay hashes match their evidence records: 24 real task/seed/state snapshots and 24 common three-selector replays. A fresh current-code replay preserved every compared scientific field: snapshot/support hashes, statuses, objectives, selected IDs, witnesses, validation results, and gaps. Run metadata and only `runtime_seconds` plus the three recorded parser timing fields were excluded. It had zero failures, timeouts, or zero optima and 24 independently valid exact certificates. The summary explicitly limits interpretation because every compact support became singleton after deduplication. | Pass |
| T1255 | Re-running the publication summarizer over the pinned 540-row corpus independently rechecks objectives, selected IDs, witness token/terminal shape, pairing, censoring, and distributions. It finds 27 points, ten repetitions per backend/point, 270 Python/Rust pairs, zero mismatch, timeout, censoring, or error, and separate backend series. `graph_size_scale` remains explicitly compound. | Pass |
| T1256 | ADR 0021 freezes the existing layers and prohibits the listed generic replacements. The M12.5 diff contains task-specific configs, drivers, validators, evidence, and tests; it adds no plugin/workflow/database/charting/DI/statistics framework. T1201/T1202 do not appear in the T1203 config or manuscript as results. | Pass |
| T1257 | Both generated T1203 JSON files carry the same name clarification, and `REPRODUCING.md` plus `docs/artifacts/README.md` present it before results. All five T1203 source paths and hashes remain pinned; `make final-artifacts-check` reproduces every output. | Pass |
| T1258 | The article plan authorizes exactly R1--R3, replaces rather than appends the two existing tables, indexes all omitted artifacts, and allocates 14.25 pages plus 1.75 pages contingency. The pre-import manuscript still measures 15 pages; no final page count is claimed. | Pass |
| T1259 | The article body, theorem/algorithm names, captions, active paper README, and renamed `FIELDS_TO_FILL.md` checklist are English. The required Portuguese `Resumo` and matching English `Abstract` remain. The legacy Portuguese plan is archived verbatim at hash `fefe0b6f250e75c887455fcf3fe3459fa5d1be3fc92a385aef42dc0428c07f33`. The audit found and fixed the two previously untranslated active paper-support documents and added a regression for them. | Pass after correction in `7b0d9aa` |
| T1260 | At `7b0d9aa`, `make rehearse-artifact-rebuild` rebuilt every T1203 processed/paper output from a clean clone and non-editable wheel and byte-matched manifest hash `28a17dcd3e054d9ab4d676793caf081bbba75eafd6513d1f751fa38436c46acb`. `make rehearse-source-correctness` used independently installed main/Rust wheels and reproduced 249 agreements and 334 certificate validations; timing fields were excluded by contract. | Pass |
| T1261 | The body of `docs/history/TASKS-through-M12.md` is byte-identical to lines 43--575 of `355150d:TASKS.md`; its hash remains `b649031694f399cb3a3379129ad7211c1796a0e1abde8fb7ccbfcec9d3ce429a`. Prior history links and task evidence resolve, while active work begins at T1300. | Pass |

## Final gate commands

- `make bootstrap` -> pinned submodule and locked development environment
  verified.
- `make check` -> upstream provenance, Ruff, strict MyPy, 11 unit tests, and
  645 exact-commit tests passed.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q` -> 666 tests
  passed, including ten pinned-EPIC integration tests.
- `make test-rust-parser` -> 17 Rust unit tests and three randomized tests
  passed; formatting and Clippy passed for both Rust crates.
- The current GitHub `rust-correctness` job reran the normal M6 and M7
  campaigns (500/500 cases each), the Q1 smoke, and the Q4 smoke.
- A fresh Q2 diagnostic smoke completed all six configured illustrative cases
  with zero failures.
- Direct Q4 and Q5 summarizer reruns reproduced the checked-in evidence
  summaries; the portable Q2 source rerun reproduced all 24 semantic results.
- `make release-wheel-smoke`, `make final-artifacts-check`,
  `make rehearse-artifact-rebuild`, and `make
  rehearse-source-correctness` passed.
- `make paper` passed; `pdfinfo paper/main.pdf` reported 15 pages.

## Claim boundary after completion

M12.5 is complete, but its explicit limitations remain binding. The Q2 real
corpus is a bounded execution/alignment check, not a population gap estimate.
Q4 measures generated CPU scaling instances, not representative model
workloads. Q5 establishes real EPIC parallel execution and exact integration
on two literal structured tasks; it does not establish general output-quality
improvement. The T1203 bundle remains diagnostic despite its `final` path
name. This audit did not rerun the CUDA/model campaign; it verified the
versioned clean-run metadata, raw hashes, row-level contracts, and independent
summaries instead and does not claim a new CUDA observation.

No M12.5 requirement remains incomplete. The next required task is T1300.
