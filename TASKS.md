# TASKS.md — Exact MWPC for CFG-Constrained dLLMs

## How to use this file

This is the authoritative checklist for current and future work. `AGENTS.md`
defines stable scientific invariants; accepted ADRs explain the maintained
design. `IMPLEMENTATION_PLAN.md` now indexes those sources and the archived
legacy Portuguese plan. Detailed completed evidence through M12 is archived in
[`docs/history/TASKS-through-M12.md`](docs/history/TASKS-through-M12.md),
which preserves links to the earlier history files.

Status convention: `[ ]` incomplete, `[x]` completed with immutable evidence,
and `BLOCKED:` a concrete gate failure. Complete required tasks in dependency
order, never substitute measurements with estimates, and do not redo a closed
milestone unless a regression invalidates its evidence.

## Current starting point

**Required project complete.** M0 through M13, including the M10.5 hardening
pass and M12.5 review-fix gate, are complete. Optional O1--O4 remain outside the required scope.

## Completed milestone summary

- **M0--M7:** pinned baseline, formal contracts, Python/Rust exact parsers,
  exhaustive gates, tokenizer-aware finite lattices, and EOS/PAD exactness.
- **M8:** proposals, adaptive support, typed validation/commit authority,
  fallbacks, profiling, and offline exact-step integration.
- **M9:** pinned LLaDA integration, baseline preservation, saved-logit loop, and
  one live correctness smoke.
- **M10:** shared frozen selector input, precise baseline adapters, guarded brute
  force, and versioned replay artifacts.
- **M10.5:** compact ranked support, pinned-EPIC integration CI, total selector
  deadlines, precise component-selector names, fair candidate-universe checks,
  executable exact/EPIC grammar alignment, and evaluation-package cleanup.
- **M11:** immutable experiment configs, Q1--Q5 drivers, and component
  timing/memory instrumentation.
- **M12:** run metadata, raw/processed/paper separation, statistical summaries,
  deterministic generated artifacts, and reproduction instructions.

See `docs/evidence/`, `docs/decisions/`, and the archived checklist for exact
commits, commands, configured-case boundaries, and result counts.

---

# M11--M12 — Completed experiment and artifact milestones

M11 and M12 are complete. Their full task definitions, acceptance criteria,
commands, and evidence are archived in
[`docs/history/TASKS-through-M12.md`](docs/history/TASKS-through-M12.md).

- **M11 / T1100--T1106:** immutable experiment configuration; executable Q1
  correctness, Q2 heuristic-gap, Q3 finite-slot, Q4 scaling, and Q5
  end-to-end drivers; and component timing/memory instrumentation.
- **M12 / T1200--T1204:** run metadata; raw/processed/paper separation;
  statistical summaries; the deterministic T1203 Q1--Q5 bundle; and
  reproduction instructions.

Stable entry points are `configs/experiments/`, `docs/evidence/t110*.json`,
`docs/artifacts/raw/t1203_final_results_v1/`,
`docs/artifacts/processed/t1203_final_results_v1/`,
`paper/generated/t1203_final_results_v1/`, and `REPRODUCING.md`. The T1201
and T1202 outputs remain internal validation fixtures. The T1203 name
`final` denotes deterministic artifact-build output, not publication-level
benchmark status.

---

# M12.5 — Review fixes before article writing

This milestone addresses the twelve findings from the post-M12 review. It must
not redesign the parser, certificate model, finite-support representation, Rust
backend, or decoder integration. Preserve serial and EPIC as baselines, keep
the existing diagnostic raw evidence immutable, regenerate derived artifacts
only through their scripts, and add no new generic experiment or artifact
framework. A publication-scope decision may restrict claims or require
additional runs, but it may never relabel existing diagnostic evidence.

## T1250 — Package and smoke-test the research modules

**Depends on:** M12 gate

**Review finding:** 1 — the release wheel omits `mwpc_research`.

- [x] Include both `src/mwpc_exact` and `src/mwpc_research` in the wheel.
- [x] Build the sdist and wheel with the locked project build toolchain.
- [x] Inspect the wheel contents so an editable checkout cannot mask omissions.
- [x] Install the wheel into a new isolated environment and import both packages.
- [x] From that wheel-installed environment, run one small experiment and one
  artifact-generation smoke without importing either package from the checkout.
- [x] Add a deterministic release-packaging regression test or CI command.

**Acceptance criteria**

- [x] A non-editable wheel install exposes `mwpc_exact` and `mwpc_research` and
  completes both smokes without `PYTHONPATH` or source-tree leakage.
- [x] The release test fails if either package is removed from the wheel.

**Evidence:** implementation commit
`2c3092ef2d34c6535c02afb8177d289f412781af`; `make
release-wheel-smoke` from that clean commit built the sdist and wheel with
`build==1.3.0` and `hatchling==1.27.0`, installed the wheel with `--no-index
--no-deps` into a new temporary environment, and found 50 `mwpc_exact` plus 17
`mwpc_research` Python files. Both imports resolved inside the temporary
site-packages directory rather than the checkout. The installed wheel then ran
the two-case Q3 experiment with zero failures and created the T1202 statistical
artifact with pinned SHA-256
`40b236f2e5988eca6ccdbe9aa2cb22b5df4cda087dfea34bade4f19f6e34a776`.
`python -m pytest -q tests/unit/test_package_boundaries.py
tests/exact_commit/test_reproduction_instructions.py` -> 5 passed; `make check`
-> upstream pin verified, Ruff and strict MyPy clean, 10 unit and 594 exact
tests passed. The same wheel rehearsal is a required `project-checks` CI step.

## T1251 — Correct the Q1 agreement presentation

**Depends on:** T1203

**Review finding:** 4 — confidence intervals are attached to fixed case sets.

- [x] Report canonical agreement as an exact numerator/denominator only.
- [x] Report the complete configured exhaustive family as an exact
  numerator/denominator only.
- [x] Keep a Wilson interval only for the randomized-seed family and describe
  the generator and seed distribution to which it applies.
- [x] Report the mixed overall configured total as an exact count with no
  confidence interval.
- [x] Regenerate the Q1 processed result, table, manifest hashes, and tests from
  the pinned raw rows; do not hand-edit generated values.

**Acceptance criteria**

- [x] No canonical, exhaustive, or mixed deterministic/random row has a
  probabilistic confidence interval.
- [x] The randomized interval remains formula-tested and traceable to raw rows.

**Evidence:** implementation commit
`84ec0f4244a6db9a21d028536599bba9975f5f6f`; the unchanged 249-row Q1
input retains SHA-256
`62fb83b48c8809a3958df486b387e017ba245e97e4e74e475ca1fb55659ade8a`.
`make final-artifacts-check` from that clean commit byte-verified
`final-results.json` at
`b72d6fd08429e3eb3c18fca4e5788a4fe3617a62a1972deedd6801cd176884d0`,
the manifest at
`06e9e8d86441b4f35a0fb863654b797081a62608ea729e7bab3dc870ea2f369f`,
and the correctness table at
`119fd38aeec70ef870941fe13a528a62170bb8e20bebf5f0b0842033e2fdad7b`.
The table reports `5/5`, `144/144`, `100/100`, and `249/249`; only the
randomized row has a 95% Wilson interval and it records the generator plus 100
unique consecutive seeds 1101--1200. `python -m pytest -q
tests/exact_commit/test_q1_correctness.py
tests/exact_commit/test_final_artifacts.py
tests/exact_commit/test_t1203_evidence.py` -> 15 passed; `make check` -> 10
unit and 595 exact tests passed; full `python -m pytest -q` -> 615 passed;
`make paper` -> 15 pages.

## T1252 — Freeze the evidence tier and allowed article claims

**Depends on:** M12 gate

**Review finding:** 2 — reproducible diagnostic results are not automatically
publication-level experiments.

- [x] Record a versioned decision stating whether M13 targets a preliminary
  article with diagnostic evidence or a final article with new publication-mode
  runs.
- [x] Inventory, per Q1--Q5, what the current evidence supports and what it does
  not support.
- [x] Keep every existing `publication_mode=false` run classified as diagnostic.
- [x] If publication-mode runs are selected, define immutable configs, minimum
  metadata, stopping/resource rules, and a new artifact bundle ID before runs.
- [x] Record that the preliminary-evidence branch was not selected; broader
  claims remain blocked until the predeclared publication runs pass.

**Acceptance criteria**

- [x] Every planned M13 empirical claim maps to an evidence tier and artifact;
  unsupported claims are explicitly excluded.
- [x] No existing smoke or diagnostic is renamed or promoted to publication
  evidence.

**Evidence:** decision/config commit
`d454f922aca7b90565e44e8cb1c25562fc5924a4` records the final-article choice,
Q1--Q5 claim matrix, metadata requirements, and stopping/resource rules in
[`docs/decisions/0016-publication-evidence-tier.md`](docs/decisions/0016-publication-evidence-tier.md).
The predeclared Q2, Q4, and Q5 config hashes are respectively
`5e950bf7bd71a537a40ee50c282c30fd9d54a260933e53e2f17cce8cdc3bb5a3`,
`265f812036df651bab9c585a8c95a496f5ab27f9ab0c073e56ff35897320cfa7`,
and `ef6500bea33bf50a1b0ca112f3e1086f0f1f7c804dd49a86868705da1132b004`.
All use `publication_mode=true` and reserve `m125_publication_results_v1`;
tests also verify that the six existing full configs remain diagnostic and
that the old bundle ID is not reused. `python -m pytest -q
tests/exact_commit/test_publication_evidence_policy.py
tests/exact_commit/test_experiment_config.py` -> 18 passed; `make check` -> 10
unit and 599 exact tests passed.

## T1253 — Exercise genuine EPIC parallel commitment end to end

**Depends on:** T1105, T1106, T1252

**Review finding:** 3 — the current Q5 EPIC rows only exercise serial fallback.

- [x] Add one small structured task with at least two ordinary content tokens.
- [x] Feed exact and EPIC comparable candidate states and record their
  comparison fingerprint.
- [x] Require `regular_cover_selector_calls > 0` and at least one EPIC selected
  batch of cardinality greater than one.
- [x] Independently check the output and preserve exact-result certificate
  validation and `exact_on_support` reporting.
- [x] Keep the existing single-token task, but label its row as an EPIC-enabled
  decoder with serial fallback rather than evidence of EPIC parallel speed.
- [x] If T1252 selects publication-mode evidence, run at least two nontrivial
  structured tasks in the new Q5 campaign; otherwise classify this addition as
  integration evidence rather than a representative benchmark.
- [x] Add a regression that fails if the new EPIC task silently falls back for
  every selection.

**Acceptance criteria**

- [x] Versioned raw evidence proves that the regular-cover selector ran and made
  at least one parallel commitment on independently valid output.
- [x] Serial, EPIC, and exact remain distinct strategies with comparable inputs;
  fallback counts are reported rather than hidden.

**Evidence:** implementation commits `7bb73c3`, `9c4278f`, `3cc34e0`,
`6914b96`, and `b4a8ffd` add structured task manifests, multi-byte literal
grammars, task/seed comparison fingerprints, Rust-regex-safe EPIC literals,
repeated exact steps, independent output checks, hard EPIC execution gates,
and the old single-token fallback label. ADRs 0017--0019 preserve the rejected
v1--v3 pilots and explain the v4 choice without promoting failed runs to
evidence. The accepted immutable v4 config has file SHA-256
`0c7afd505e2dc1330d7d917f2dda0369a4033f7c43825967b3eeb04661b747a7`
and normalized SHA-256
`6318a4c2810ac7926806ceda86ad4b013146f4d27f879cbb5ab7dfb7b08a28c4`.
Six clean CUDA commands ran fenced JSON and `ADD 0 0` DSL tasks at seeds
125301--125303, ten repetitions and four strategies each, from producing
commit `b4a8ffde4cc2aabc61844a955ce98933ef03dfb9`. The resulting 240 versioned
raw rows are at
`docs/artifacts/raw/m125_publication_results_v1/q5-end-to-end-rows.jsonl`
(SHA-256 `8acfb789e14779c9c33c7fec50fb713194797a2a5ae1a2ad59a56f5f5e266f44`).
`python scripts/exact_commit/summarize_q5_publication.py` independently
rechecked all outputs and 60 stored `OPTIMAL` step certificates, observed 330
regular-cover selector calls total and a maximum EPIC batch of two in every
task/seed pair, and wrote
`docs/evidence/t1253-q5-publication-summary.json` (SHA-256
`700aa99e870c06704bbd98a4bd481bb2ee1c73c3dbff7843f3cca16a2b7f5ec1`).
That summary reports EPIC fallback counts per task/seed rather than hiding the
remaining serial selections. `python -m pytest -q
tests/exact_commit/test_t1253_evidence.py tests/exact_commit/test_q5_end_to_end.py
tests/exact_commit/test_publication_evidence_policy.py` -> 22 passed; `make
check` -> 10 unit and 608 exact tests passed; `make paper` -> 15 pages.

## T1254 — Separate illustrative Q2 cases from empirical gap evidence

**Depends on:** T1252

**Review finding:** 5 — three synthetic states are a useful unit experiment,
not an empirical heuristic-gap distribution.

- [x] Retain the existing six rows and classify them as illustrative canonical
  and adversarial cases.
- [x] Remove or prevent prose that generalizes their mean gap to model behavior.
- [x] If T1252 selects publication-mode evidence, collect a predeclared,
  versioned sample of saved real decoder states spanning multiple denoising
  steps and nontrivial tasks.
- [x] Replay greedy feasibility, EPIC regular cover, and exact MWPC over the same
  proposal/support snapshot for every sampled state.
- [x] Validate exact certificates independently and report selection failures,
  timeouts, and zero-optimum rows without dropping them silently.
- [x] Preliminary-only branch is not applicable because T1252 selected
  publication-mode evidence; the real-state campaign was run instead.

**Acceptance criteria**

- [x] Synthetic rows are never presented as a representative model-state sample.
- [x] Any empirical aggregate uses only the separately identified real-state
  sample and traces every row to a saved common snapshot.

**Evidence:** ADR 0020 amends the infeasible five-state-per-task predeclaration
to four genuine EPIC selector states for each of two Q5 v4 tasks and three
seeds. `env PYTHONDONTWRITEBYTECODE=1 .venv-live/bin/python
scripts/exact_commit/collect_q2_real_snapshots.py` captured 24 clean,
versioned snapshots from commit
`fc2ba5507589d41ffd482f532061323b9c756100`; the pinned snapshot corpus is
`docs/artifacts/raw/m125_publication_results_v1/q2-real-snapshots.jsonl`
(SHA-256
`443eda3bf4a7eb9d82c474fa9f0f3a9a11227779a07dc623e92c7f97c6f185b2`).
`env PYTHONDONTWRITEBYTECODE=1 .venv-live/bin/python
scripts/exact_commit/run_q2_real_state_gap.py` replayed all three selectors
from commit `5b6d9349adec9ac910c7bb0601d92d7e5de6f956`: 24/24 rows completed,
all exact certificates and objectives independently reproduced, with no
timeouts, failures, or zero optima. The pinned replay rows are
`docs/artifacts/raw/m125_publication_results_v1/q2-real-gap-rows.jsonl`
(SHA-256
`917aa8640ffea67305439d0526432f118801afee97932e0c120e26b7419386f7`)
and the summary is `docs/evidence/t1254-q2-real-gap-summary.json` (SHA-256
`dfa49cb7e9c7747475bebf89b28aedd64086f7368f1cda365a446e0c37745ec4`).
All 24 supports collapsed to one completion after proposal/target
deduplication, so the versioned interpretation is an execution/alignment
check with zero observed gaps, explicitly not a difficult-state or population
gap claim; no confidence interval is reported for the non-IID corpus. The old
six rows and generated table remain labeled configured synthetic illustrative
cases. `python -m pytest -q tests/exact_commit/test_t1254_evidence.py
tests/exact_commit/test_q2_real_gap.py tests/exact_commit/test_q2_gap.py
tests/exact_commit/test_publication_evidence_policy.py` -> 22 passed; `make
check` -> 10 unit and 617 exact tests passed; `make paper` -> 15 pages.

## T1255 — Separate Q4 smoke diagnostics from scaling evidence

**Depends on:** T1252

**Review finding:** 6 — the current two-repetition ranges cannot support broad
runtime or scaling claims.

- [x] Retain the current Q4 bundle as a CPU component smoke.
- [x] Label `graph_size_scale` as a compound graph-size setting because it
  changes represented width and token byte length together.
- [x] Prevent median/IQR claims for groups with insufficient repetitions.
- [x] If T1252 selects publication-mode evidence, use an immutable config with
  at least 10 repetitions per point (target 20 where the declared resource plan
  permits), broader slot and top-`K` ranges up to declared resource limits,
  explicit censoring/timeouts, and separate Python/Rust series.
- [x] Preliminary-only branch is not applicable because T1252 selected
  publication-mode evidence; the expanded run was completed instead.

**Acceptance criteria**

- [x] No timeout or censored row is summarized as a successful runtime.
- [x] The article cannot describe the compound graph-size setting as an isolated
  causal variable or the smoke curves as representative workload scaling.

**Evidence:** Commit `a4ea377570d730a32000cf376f29ff500da84a3b`
enabled only the predeclared publication fields in the existing Q4 driver and
changed the T1203 two-repetition smoke artifact to withhold all 42 per-point
median/IQR distributions. Its replacement SVG says that the raw rows remain
diagnostic and that `graph_size_scale` jointly changes support width and token
byte length. `env PYTHONDONTWRITEBYTECODE=1 .venv/bin/python
scripts/exact_commit/run_q4_scaling.py --config
configs/experiments/q4_scaling_publication_v1.toml` ran 27 generated settings,
10 repetitions and both backends in isolated 2 GiB workers: 540/540 `OPTIMAL`,
zero censored/timeouts/errors, and zero mismatches across 270 Python/Rust
pairs. Slots and top-`K` reached 16; grammar productions reached 32; compound
graph size and token byte length reached 8; proposal count reached 16.
`python scripts/exact_commit/summarize_q4_publication.py --raw-input
results/raw/q4_scaling_publication_v1/q4_scaling_publication_v1-20260901T030111Z/q4-scaling-rows.jsonl`
independently recomputed all witness objectives and selected IDs before
pinning `docs/artifacts/raw/m125_publication_results_v1/q4-scaling-rows.jsonl`
(SHA-256
`63abf6a974bdd74f20b34f7f80e9c3d646a30f9385f359a76a4747c86f8eef51`)
and `docs/evidence/t1255-q4-publication-summary.json` (SHA-256
`8570ee64c462a8139302867be56a8abc3c7f116cbb589f363a4c29807b5505f1`).
Every one of the 54 backend/point distributions contains 10 successful,
uncensored runtimes and reports median/IQR separately by backend. `python -m
pytest -q tests/exact_commit/test_t1255_evidence.py
tests/exact_commit/test_q4_scaling.py tests/exact_commit/test_final_artifacts.py
tests/exact_commit/test_t1203_evidence.py
tests/exact_commit/test_publication_evidence_policy.py` -> 20 passed; `make
final-artifacts-check` passed; `make check` -> 10 unit and 621 exact tests
passed; `make paper` -> 15 pages.

## T1256 — Freeze the experiment and artifact architecture

**Depends on:** M12 gate

**Review finding:** 7 — the infrastructure has reached the overengineering
boundary.

- [x] Record that M13 may reuse the existing config, metadata, raw/processed,
  statistics, and final-artifact paths but must not add another generic layer.
- [x] Treat T1201's two-row inventory and T1202's synthetic formula artifact as
  internal validation fixtures, not scientific findings.
- [x] Treat the T1203 Q1--Q5 bundle as the only current scientific-result bundle.
- [x] Prohibit a plugin system, workflow engine, artifact schema, charting
  framework, database, dependency-injection layer, second statistical library,
  or second raw/processed convention during M12.5/M13.
- [x] Split a large module only when a required modification makes the split
  necessary; do not refactor solely for file size or aesthetics.

**Acceptance criteria**

- [x] M12.5 and M13 add no generic infrastructure unrelated to a concrete task.
- [x] Internal pipeline fixtures are not imported or cited as research results.

**Evidence:** ADR 0021 freezes the existing configuration, metadata,
raw/processed, statistics, and final-artifact layers for M12.5/M13; lists the
prohibited generic infrastructure; limits future splitting to required
functional changes; and classifies T1201/T1202 as internal fixtures. It keeps
T1203 as the only currently assembled Q1--Q5 scientific-result bundle while
classifying `m125_publication_results_v1` as staged evidence consumed through
the same paths. `git diff --name-status
4deb73c7094004aedb5de8b2c3db20d57e353e89..HEAD` was reviewed: the M12.5
changes are task-specific configs, drivers, validators, evidence, tests, and
corrections to existing layers; no generic replacement layer was added.
`python -m pytest -q tests/exact_commit/test_t1256_architecture_freeze.py
tests/exact_commit/test_publication_evidence_policy.py` -> 7 passed.

## T1257 — Clarify the meaning of the existing final-results name

**Depends on:** T1203, T1252

**Review finding:** 8 — `final-results` can be mistaken for final empirical
evidence even though parts of the bundle are diagnostic.

- [x] Keep the T1203 bundle ID and pinned raw input paths/hashes stable; update
  derived hashes only through the existing generator when presentation changes.
- [x] Add a prominent generated-manifest, reproduction, and M13-source note that
  "final" means deterministic output of that artifact build, not publication-
  level benchmark status.
- [x] Require any later publication-mode evidence to use a new bundle ID and
  never overwrite `t1203_final_results_v1`.
- [x] Add a regression that keeps the clarification synchronized across the
  processed bundle and documentation.

**Acceptance criteria**

- [x] A reader following the T1203 manifest or reproduction guide encounters
  the diagnostic-status clarification before interpreting its results.
- [x] Existing artifact provenance remains verifiable after the clarification.

**Evidence:** `FINAL_NAME_CLARIFICATION` is emitted into both
`docs/artifacts/processed/t1203_final_results_v1/final-results.json` and
`artifact-manifest.json`, and the same rule appears before results in
`REPRODUCING.md` and the `docs/artifacts/README.md` M13 source note: `final`
means deterministic build output, not publication-level benchmark status;
later publication evidence uses a new bundle ID and never overwrites T1203.
All five config-pinned T1203 raw paths and hashes remain unchanged. The existing
generator produced only new derived hashes: manifest
`28a17dcd3e054d9ab4d676793caf081bbba75eafd6513d1f751fa38436c46acb`
and results
`1dd39f7f115c5363ab6340faaee178e1ca4d48aa665f7c85d135cfb2fb03827f`;
all table/figure hashes stayed stable. `python -m pytest -q
tests/exact_commit/test_t1257_final_name.py
tests/exact_commit/test_final_artifacts.py
tests/exact_commit/test_t1203_evidence.py` -> 9 passed; `make
final-artifacts-check` passed; `make check` -> 10 unit and 626 exact tests
passed.

## T1258 — Set the article result and page budget

**Depends on:** T1252, T1257

**Review finding:** 9 — inserting all seven artifacts would exceed the
institutional 16-page limit.

- [x] Select at most three compact result elements for the article body.
- [x] Prefer replacing expected-results placeholders over appending new tables
  and figures.
- [x] Record which remaining artifacts stay in the repository or approved
  supplementary material.
- [x] Define a page-budget allocation including references and the required
  summaries before T1301 imports results.
- [x] Keep every omitted artifact traceable from the reproduction guide.

**Acceptance criteria**

- [x] The versioned article plan stays within the 10--16 page regulation without
  silently shrinking required content or claiming an unmeasured final page count.
- [x] T1301 depends on this selection and does not append all generated artifacts.

**Evidence:** `docs/article/M13_RESULTS_AND_PAGE_BUDGET.md` selects exactly
three compact body elements: R1 combines Q1 correctness and Q3 finite-slot
evidence, R2 separates illustrative Q2 cases from the bounded T1254 real-state
replay, and R3 combines selected T1255 Q4 scaling facts with the structured Q5
integration result. It requires replacement of `tab:resultados` and removal of
the obsolete `tab:cronograma`, lists all seven T1203 artifacts retained in the
repository/supplement, and keeps them indexed by `REPRODUCING.md`. The planning
allocation is 14.25 pages including summaries and references, with 1.75 pages
of contingency under the 16-page maximum; it explicitly preserves template
font/margins and calls the final count unmeasured until T1301 rebuilds the PDF.
`python -m pytest -q tests/exact_commit/test_t1258_article_budget.py` ->
5 passed. `make paper` passed and `pdfinfo paper/main.pdf` reported the current
pre-import baseline as 15 pages; this is not a final page-count claim.

## T1259 — Decide and normalize repository/article language

**Depends on:** T1258

**Review finding:** 10 — repository and article terminology are mixed between
English and Portuguese.

- [x] Record the article-language decision before editing result prose; use an
  English body unless an institutional or advisor constraint is documented.
- [x] Apply English consistently to the article body, section titles,
  theorem/algorithm names, captions, code, and repository terminology.
- [x] Preserve the institutionally required Portuguese `Resumo` and provide a
  matching English `Abstract`.
- [x] Translate `IMPLEMENTATION_PLAN.md` or archive it with a clear supersession
  notice if `TASKS.md` and ADRs have replaced it.
- [x] Add a terminology review for `exact_on_support`, statuses, finite slots,
  proposals, witness, fallback, and baseline names.

**Acceptance criteria**

- [x] Mixed-language prose remains only where institutionally required or where
  a cited title/quotation must retain its original language.
- [x] Language normalization does not alter scientific claims or generated data.

**Evidence:** ADR 0022 selects an English title/body, English theorem and
algorithm names and captions, an institutionally required Portuguese `Resumo`,
and a matching English `Abstract`; it also fixes the meanings of
`exact_on_support`, all five solver statuses, finite slots, proposal, witness,
progress fallback, and the `serial | epic | exact` strategies. The 1,030-line
Portuguese implementation plan is preserved verbatim at
`docs/history/IMPLEMENTATION_PLAN-legacy-pt.md` (SHA-256
`fefe0b6f250e75c887455fcf3fe3459fa5d1be3fc92a385aef42dc0428c07f33`),
while its root path now indexes maintained English sources. A structural
pre/post translation check found identical sets/counts for 20 citations, 23
labels, 13 references, 20 equation environments, one align environment, three
algorithms, four theorems, three definitions, two propositions, and 34
placeholders. `python -m pytest -q
tests/exact_commit/test_t1259_language_and_terminology.py` -> 3 passed;
`make check` -> 10 unit and 634 exact tests passed; `make paper` passed and the
normalized article remained 15 pages. No generated artifact or measured result
changed. A final requirement-by-requirement audit then found two active
Portuguese paper-support documents that the original regression did not cover.
`paper/README.md` is now English and the translated checklist is
`paper/FIELDS_TO_FILL.md`; the former Portuguese checklist path was removed.
The added regression scans both active documents and rejects the old filename
and Portuguese headings. `python -m pytest -q
tests/exact_commit/test_t1259_language_and_terminology.py` -> 4 passed; `make
check` -> 11 unit and 645 exact tests passed; `make paper` still produced 15
pages. This documentation-only correction changed no generated artifact or
measured result.

## T1260 — Add artifact-rebuild and source-rerun rehearsals

**Depends on:** T1250, T1251, T1252, T1253, T1254, T1255

**Review finding:** 11 — the current clean-clone rehearsal rebuilds artifacts
from pinned rows but does not rerun the source experiment.

- [x] Name and document two distinct rehearsal levels:
  `artifact-rebuild` (pinned raw rows to generated output) and
  `source-experiment-rerun` (code plus config to new raw rows and output).
- [x] Keep byte-for-byte comparison for deterministic artifact rebuilds.
- [x] For the CPU correctness source rerun, compare case IDs, statuses,
  objectives, agreement counts, and certificate validity while excluding timing
  fields from byte-identity requirements.
- [x] Run the release-oriented rehearsal from a clean checkout and non-editable
  wheel install so packaging and source availability are tested together.
- [x] Document which GPU/model experiments remain external or optional and do
  not claim they were rerun when they were not.

**Acceptance criteria**

- [x] Both rehearsal levels have distinct commands, expected artifacts, and
  failure conditions.
- [x] A deterministic test proves that a semantic correctness mismatch fails the
  source-rerun rehearsal even when timing fields differ legitimately.

**Evidence:** `REPRODUCING.md` defines `make rehearse-artifact-rebuild` and
`make rehearse-source-correctness` with separate inputs, temporary outputs,
comparison rules, and failure conditions; it explicitly excludes Q2/Q4 and all
CUDA/model Q5 runs from the T1260 claim. Both commands clone the clean commit,
build `mwpc-exact` from that clone, install its wheel non-editably outside the
source tree, and reject source-tree imports. On commit
`8bd5ff5c69f896e1b799f2703eafe4dc6b71d869`, `make
rehearse-artifact-rebuild` passed a recursive byte comparison of every
processed/paper output and reproduced manifest SHA-256
`28a17dcd3e054d9ab4d676793caf081bbba75eafd6513d1f751fa38436c46acb`.
`make rehearse-source-correctness` additionally built and non-editably
installed the independent Rust binding, reran all 249 configured Q1 cases, and
reported `comparison=PASS`, 249 agreements, 334 independent certificate
validations, semantic-summary SHA-256
`8658c44a1d442e7dd63cc434ab65386daf66605d4baa18ba49015a1cf55fe682`,
and table SHA-256
`ea89d63ff989a629a0d60b05335d306b8f2de0401b591b9f5bd314d0cda17f9a`;
timing fields were not compared. The first source run exposed that infeasible
rows correctly omit optimal-certificate checks; the comparator now maps that
absence to zero only for non-`optimal` rows, with a deterministic regression.
`python -m pytest -q tests/exact_commit/test_t1260_correctness_rehearsal.py
tests/exact_commit/test_reproduction_instructions.py` -> 9 passed; `make
check` -> 10 unit and 640 exact tests passed.

## T1261 — Archive completed M11/M12 task detail

**Depends on:** T1250, T1251, T1252, T1253, T1254, T1255, T1256, T1257,
T1258, T1259, T1260

**Review finding:** 12 — the active task file is large and its next work is hard
to locate.

- [x] Archive the complete M11/M12 task text and evidence under
  `docs/history/TASKS-through-M12.md` without losing prior history links.
- [x] Replace completed M11/M12 detail in this file with a concise summary and
  stable links to evidence and the archive.
- [x] Keep M12.5 and M13 in full detail until their gates close.
- [x] Verify that task IDs, dependencies, evidence links, and current starting
  point remain unambiguous after the move.

**Acceptance criteria**

- [x] A new agent can identify the first incomplete task and its dependencies
  without reading completed command logs.
- [x] No completed evidence or blocking scientific contract is lost.

**Evidence:** `docs/history/TASKS-through-M12.md` preserves the prior M11/M12
range byte-for-byte after its 16-line archive header and links the earlier
M0--M10 archives; its SHA-256 is
`b649031694f399cb3a3379129ad7211c1796a0e1abde8fb7ccbfcec9d3ce429a`.
The active file fell from 1,297 to 787 lines, retains M12.5 and M13 in full,
states that the M12.5 gate audit is current and T1300 is the first remaining
task after that gate, and replaces only M11/M12 command logs with task-ID and
artifact entry points. `python -m pytest -q
tests/exact_commit/test_t1261_task_archive.py` -> 4 passed. A direct `diff` of
the archived body against lines 43--575 of the pre-archive
`355150d:TASKS.md` produced no differences; all versioned links checked by the
regression resolve.

**M12.5 review-fix gate — complete**

- [x] The installed wheel contains and exercises both Python packages.
- [x] Q1 statistical presentation distinguishes fixed and random case families.
- [x] Evidence tier, genuine EPIC execution, and any selected Q2/Q4 expansion
  are versioned without promoting diagnostics.
- [x] Artifact naming, architecture freeze, page budget, and language are settled.
- [x] Both reproduction levels pass and completed M11/M12 detail is archived.
- [x] No correctness gate regresses and no unsupported article claim remains.

**Gate evidence:** commits `2c3092e` through `6a8f747` implement and document
T1250--T1261. Follow-up commit `f47ee05` keeps optional EPIC/Rust imports out of
the generic test environment while explicitly exercising the affected Q2/Q5
tests in the pinned EPIC job. GitHub Actions run
[`33467321623`](https://github.com/j0taaa/tcc-final/actions/runs/33467321623)
passed all three jobs at `f47ee05837dcd8a66bbf353391fc49a3548bea98`:
lightweight verification and release-wheel rehearsal, production Rust/full
correctness campaigns, and pinned EPIC integration. The final local audit
passed `make check` (11 unit and 644 exact tests), `make test-rust-parser` (20
Rust tests plus formatting and Clippy), `make release-wheel-smoke`, `make
final-artifacts-check`, `make paper` (15 pages), the 500-case M6 and 500-case
M7 oracle campaigns, the ten pinned-EPIC integration tests, and the six-case
Q2 smoke. T1260 separately records passing clean-clone artifact-rebuild and
source-experiment-rerun rehearsals. ADR 0016, the T1257 artifact clarification,
and the T1258 result budget prevent diagnostic evidence from being promoted to
publication claims; no CUDA/model experiment is claimed as rerun by this gate.
The final requirement-by-requirement audit is versioned at
[`docs/evidence/m125-completion-audit.md`](docs/evidence/m125-completion-audit.md).
It found and corrected the remaining T1259 paper-documentation language gap in
commit `7b0d9aabeeaa3388b4b652b9e24d66f0da9b784d`; GitHub Actions run
[`33468417087`](https://github.com/j0taaa/tcc-final/actions/runs/33468417087)
then passed all three jobs, including both 500-case oracle campaigns, release
wheel rehearsal, pinned EPIC integration, and focused combined Q2/Q5 tests.

---

# M13 — Synchronize implementation with the TCC

## T1300 — Fill implementation-method fields in LaTeX

**Depends on:** M12.5 gate

- [x] Insert exact repository and upstream commits.
- [x] Insert module/backend architecture.
- [x] Insert grammar normalization and epsilon handling.
- [x] Insert tokenizer byte semantics.
- [x] Insert support/top-`K` policy and exactness wording.
- [x] Insert candidate/weight policy.
- [x] Insert EOS/PAD, timeout, tie, and fallback behavior.
- [x] Insert model, tokenizer, hardware, and software versions.

**Acceptance criteria**

- [x] No implementation field is filled from memory when an artifact can provide it.
- [x] Paper claims match the actual code path.

**Evidence:** commit `02aabd239a3d76ef4d9176c6d8257651c27af5ac`
fills the method fields in `paper/main.tex` and keeps the parent license status
explicitly pending rather than inventing one. Repository/upstream provenance
comes from `docs/evidence/m125-completion-audit.md` and `UPSTREAM.md`; grammar,
epsilon, tokenizer, support, proposal, EOS/PAD, timeout, tie, and fallback
semantics come from ADRs 0001--0013 and their referenced implementation paths.
The exact model/tokenizer revision and vocabulary audit come from
`docs/evidence/t600-llada-tokenizer-audit.json`; Q5 schedules, support, weights,
specials, and protocol come from
`configs/experiments/q5_structured_publication_v4.toml` and
`configs/experiments/q5_structured_tasks_v4.toml`; hardware/software values
come from the pinned Q4 summary and Q5 raw JSONL metadata under
`docs/artifacts/raw/m125_publication_results_v1/`. The paper now states that
the live path uses a raw-byte CFG without a production lexical transducer,
reports only per-step `exact_on_support`, retries wider support only after
`INFEASIBLE_ON_SUPPORT`, and preserves non-optimal statuses and baseline
separation. `python -m pytest -q
tests/exact_commit/test_t1300_paper_method.py` -> 6 passed; `make check` ->
11 unit and 651 exact-commit tests passed; full `python -m pytest -q` -> 672
passed. `make paper` passed and `pdfinfo paper/main.pdf` reported 16 pages.
Poppler renders of pages 1--2 and 11--16 were visually checked with no
clipping, overlap, unreadable table text, or broken identifiers. Advancing the
active pointer exposed a stale T1261 test that hard-coded T1300 as the next
task; `tests/exact_commit/test_t1261_task_archive.py` now deterministically
expects T1301 while continuing to protect the archived M0--M12 content.

## T1301 — Fill and analyze results

**Depends on:** M12.5 gate, T1258

T1301 must follow `docs/article/M13_RESULTS_AND_PAGE_BUDGET.md`: replace the
two named placeholder/planning tables with R1--R3 and does not append all
generated artifacts.

- [x] Import generated tables/figures.
- [x] Report correctness campaign size and agreement.
- [x] Analyze heuristic gaps.
- [x] Analyze finite-slot findings.
- [x] Analyze runtime/memory and the dominant component.
- [x] Analyze end-to-end validity, fallbacks, and limitations.
- [x] Report negative or null findings honestly.

**Acceptance criteria**

- [x] Every number is generated by a script and traceable.
- [x] No smoke-test result is presented as a benchmark conclusion.

**Evidence:** commit `844dc68c34d49e31253aff799fdd9e6f89471108`
adds the task-specific `m1301_article_results_v1` builder and immutable config,
which pin seven T1203/M12.5 inputs by SHA-256 and generate one processed value
map, LaTeX macros, and exactly the three R1--R3 tables selected by T1258. The
paper replaces `tab:resultados` and `tab:cronograma`; it reports configured Q1
agreement and certificate checks, illustrative versus singleton-support Q2
evidence, both Q3 finite-slot outcomes, separate Python/Rust Q4 timing and
memory with the compound-axis qualification, and Q5 validity, real EPIC
batching, serial fallback events, exact certificates, and bounded-task runtime
ratios. It explicitly withholds population, realistic-workload, full-vocabulary,
and broad output-quality conclusions. `make article-results-check` reproduced
processed SHA-256
`f2ebbe091d5b00a6324d1c13c8b6058bcec6ed3c10e9511ed6e6eaca3a42ddb0`
and table hashes `fa7f50a8`, `621b589d`, and `354d77b4`; `make
final-artifacts-check` preserved the T1203 manifest hash `28a17dcd`. Focused
generator, budget, method, reproduction, and architecture tests -> 21 passed;
`make check` -> 11 unit and 655 exact-commit tests passed; full `python -m
pytest -q` -> 676 passed. `make paper` passed with no overfull box or unresolved
reference, and `pdfinfo paper/main.pdf` reported 16 A4 pages. Poppler renders
of all 16 pages were visually inspected; the three result tables are legible
with no clipping or overlap.

## T1302 — Update limitations and theorem-to-code correspondence

**Depends on:** T1300, T1301

- [x] State exact-on-support limitations.
- [x] State tokenizer and byte-level language limitations.
- [x] State the CFG syntax-versus-semantics limitation.
- [x] State per-step versus trajectory optimality.
- [x] State timeout and resource limits.
- [x] Add a table mapping theorem assumptions to code/config enforcement.

**Acceptance criteria**

- [x] No theorem assumption is silently violated by the reported experiment.

**Evidence:** commit `4cabaef8b98c1f7e973e0205ef2d9214da426e0e`
expands Section~10 of `paper/main.tex` and adds Table~5, which maps Theorems
1--4 and the decoder propositions to executable weight, CNF/parser,
support/EOS, tokenizer-byte, validation, and monotone-commit boundaries. The
paper now states top-K and per-step scope, raw-byte/no-lexer semantics,
syntax-versus-semantics, timeout-versus-infeasibility, and time/memory limits.
The audit also resolves two presentation ambiguities: the upstream
`low_confidence` label ranks still-masked baseline candidates but exact Q5
never remasks, and the lexicographic tie/cardinality-chart variants are named
unimplemented rather than implied as active. The Q5 config-to-execution
regression in `tests/exact_commit/test_t1302_paper_limitations.py` protects
these claims. `make article-results-check` reproduced the pinned processed and
R1--R3 hashes; the focused T1261/T1302 regressions passed 9 tests; `make check`
passed 11 unit and 660 exact-commit tests; full `python -m pytest -q` passed
681 tests. `make paper` passed without overfull boxes or unresolved references, and
`pdfinfo paper/main.pdf` reported 16 A4 pages. Poppler renders of all 16 pages
were visually inspected with no clipping, overlap, broken glyphs, or
unreadable tables.

## T1303 — Fill AI-use declaration

**Depends on:** T1300

- [x] Name tools, providers, and versions used.
- [x] State purposes: planning, drafting, review, coding assistance, and related uses.
- [x] Identify affected sections/components.
- [x] State that the author reviewed proofs, code, references, and results.
- [x] Ensure no fabricated data or unattributed text is included.

**Acceptance criteria**

- [x] Declaration satisfies the institutional regulation.

**Evidence:** commit `cca3f889342a0711b36ab9124f9c4ea3f32f7f39` replaces the placeholders with `paper/main.tex`'s `AI-Use Declaration` and closes the paper checklist. It names OpenAI Codex/OpenAI, Codex CLI 0.151.0, the GPT-5 basis, and the unexposed immutable hosted-build ID; purposes and affected manuscript/Python/Rust components; author review/responsibility; and excluded AI-proposed measurements, fabricated data, AI-generated figures, and unattributed text. Focused regression -> 3 passed; `make check` -> 11 unit + 663 exact tests; full pytest -> 684 passed; `make paper` -> 16 A4 pages; all-page Poppler inspection (pages 15--16 full-size) found no clipping, overlap, broken glyphs, or crowded references.

## T1304 — Create final reproducibility release

**Depends on:** T1301, T1302, T1303

- [x] Run full Python tests.
- [x] Run Rust tests and formatting.
- [x] Rebuild bindings.
- [x] Re-run publication configs or verify immutable artifacts.
- [x] Build the final LaTeX PDF.
- [x] Create a release tag.
- [x] Archive configs, small raw evidence, processed data, figures, tables, and reproduction instructions.
- [x] Record known limitations and any non-reproducible external dependency.

**Acceptance criteria**

- [x] Repository and paper point to the same release commit.
- [x] Worktree is clean or intentional untracked artifacts are documented.

**Evidence:** release payload commit `08f59455620630c3b5b0e29f69171af69f515662` is the dereferenced annotated tag [`v0.1.0`](https://github.com/j0taaa/tcc-final/releases/tag/v0.1.0) named by the repository and paper. The published release archives 132 config/raw/processed/evidence/table/figure/source/reproduction entries in `mwpc-exact-v0.1.0-evidence.tar.gz` (SHA-256 `e1ae69b6c9e2dbfd1cf69de6c2de2e9d47665a9573e6f9d911ca92f5bfbbf8d5`) plus the 16-page PDF (SHA-256 `5ba5858c549b063ffab0f965407009f3f29339077aee4187fe12cd4dd01716ab`); local and GitHub asset digests agree. `docs/releases/v0.1.0.md` records the exact archive command, scientific boundaries, external EPIC/model/toolchain dependencies, private-release/licensing constraint, and the three author-only identification fields. Gates: full pytest 688 passed; `make check` 11 unit + 667 exact tests; rebuilt PyO3 binding; Rust formatting/Clippy plus 17 unit and 3 randomized tests passed; M4 2000/2000, M5 500/500 + 2000/2000, M6 500/500 + 2000/2000, and M7 500/500 + 2000/2000 differential cases had zero failures; immutable artifact checks reproduced T1203 manifest `28a17dcd3e054d9ab4d676793caf081bbba75eafd6513d1f751fa38436c46acb`; clean-clone artifact rebuild matched byte-for-byte and source rerun reproduced 249/249 agreements with 334 certificate validations; release-wheel installation/import/experiment/artifact smoke passed; `make paper` and all-page Poppler inspection passed at 16 A4 pages. GitHub Actions run [`33554812631`](https://github.com/j0taaa/tcc-final/actions/runs/33554812631) passed verify, Rust correctness, and pinned EPIC integration. The tagged and final bookkeeping worktrees were clean; ignored local copies in `dist/release-v0.1.0/` correspond to the published checksummed assets.

**Required project completion gate**

- [x] M0–M13 complete.
- [x] All scientific-contract rules in `AGENTS.md` hold.
- [x] Correctness evidence is 100% on configured oracle campaigns.
- [x] Exact end-to-end mode and baselines are reproducible.
- [x] TCC contains no fabricated or unsupported implementation/result fields.

---

# OPTIONAL O1 — Exact cardinality budget

## O100 — Extend objective with `|B| <= k`

**Depends on:** Required project stable

- [ ] Add a budget dimension or formally equivalent semiring/state construction.
- [ ] Prove recurrence and complexity.
- [ ] Compare with candidate-set truncation semantics.
- [ ] Add brute-force tests.

**Acceptance criteria**

- [ ] Exact budgeted solver agrees with exhaustive subsets.

---

# OPTIONAL O2 — Deterministic lexer transducer

## O200 — Replace byte grammar with token-lattice × lexer composition

**Depends on:** Required byte-level path stable

- [ ] Define lexer state, maximal munch, priority, whitespace, comments, and keyword rules.
- [ ] Compose without losing token provenance or slot count.
- [ ] Validate against an independent lexer on complete strings.
- [ ] Reuse lexeme-level EPIC CFGs only when semantics match exactly.

**Acceptance criteria**

- [ ] Every accepted witness produces the same lexeme sequence as the declared lexer.

---

# OPTIONAL O3 — Incremental parsing across denoising steps

## O300 — Reuse chart/lattice state safely

**Depends on:** Required solver correct and profiled

- [ ] Identify unchanged graph regions between steps.
- [ ] Define invalidation rules.
- [ ] Preserve exactness under updates.
- [ ] Compare incremental and full-recomputation certificates.

**Acceptance criteria**

- [ ] Scores and certificates match full recomputation on all tests.

---

# OPTIONAL O4 — Lazy/full-vocabulary support

## O400 — Add trie/lazy token expansion

**Depends on:** Required top-`K` solver stable

- [ ] Share token byte prefixes without merging token provenance.
- [ ] Generate arcs lazily from parser demand or admissible-prefix analysis.
- [ ] Prove pruning safety.
- [ ] Compare with explicit full support on small vocabularies.

**Acceptance criteria**

- [ ] Lazy and explicit support return equal optimum and valid provenance.

---

# Final evidence index

Fill this section only with real artifacts.

- Baseline commit: `b9f2179caadf8640fe026f7a73833cbda9755876`
- Upstream EPIC commit: `5b1b31098f34ed3691d2a9f4aae14fdf5839d072`
- Token-aligned correctness artifact: `docs/evidence/m3-differential-summary.json`
- Rust/Python differential artifact:
  `docs/evidence/m5-rust-differential-normal-summary.json`
- Finite-slot counterexample artifact:
  `docs/evidence/t703-finite-slot-counterexamples.json`
- Heuristic-gap experiment artifact:
  `docs/evidence/t1102-q2-heuristic-gap-summary.json`
- Scaling experiment artifact: `docs/evidence/t1255-q4-publication-summary.json`
- End-to-end experiment artifact: `docs/evidence/t1253-q5-publication-summary.json`
- Parent release license: MIT; scope and release evidence in
  `docs/evidence/submission-license-release.md`
- Reproduction release/tag: [`v0.1.1`](https://github.com/j0taaa/tcc-final/releases/tag/v0.1.1), commit `3db85bb0ec7e4416352b74832e8a6750af8bcaf2`
- Final TCC PDF/source commit: [`mwpc-exact-v0.1.1-paper.pdf`](https://github.com/j0taaa/tcc-final/releases/download/v0.1.1/mwpc-exact-v0.1.1-paper.pdf), source tag `v0.1.1`
