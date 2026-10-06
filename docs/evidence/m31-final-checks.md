# M31 verification and relevance verdict — 5 October 2026

Implementation/evidence freeze: `d137a36acf2dca4a7837686ebaaff415f9de1333`.
Final verification: **PASS**. Scientific verdict: the certification capability is validated within its declared scope; general practical superiority and substantial novelty remain unestablished.

The falsification audit supports the specified mathematical certificate/admission construction. It does not establish general practical superiority, substantial novelty or semantic accuracy. No finite test campaign supports 100% certainty of those claims.

All 18 fresh official CPU MDLM predictions and all 36 partition jobs remain recorded. There are 35 independently checked returned proofs, 27 incomplete outcomes, 8 admitted outcomes and one external timeout (not infeasibility). At the 64-query cap and TV tolerance 1/20, admissions with 4/8/16 free slots are 5/6, 1/6 and 0/6. The independent compact exact control handles every canvas, as many as 14,082,354,344 positive token paths, with zero conditional approximation error. Its coverage/compilation/median-query core costs 11.714–81.180 ms and is lower in all 35 returned pairs. Different numeric/certificate interfaces make this a diagnostic cost comparison, not a deployment or published-competitor ranking.

| Command/check | Actual result |
| --- | --- |
| `.venv/bin/python -m pytest -q tests/exact_commit/test_probability_relevance_audit.py tests/exact_commit/test_mass_certificates.py tests/exact_commit/test_probability_provenance.py` | 95 passed in 1.71s |
| `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q` | 1523 passed in 134.72s |
| `.venv/bin/ruff check src tests scripts/exact_commit/capture_mdlm_probability.py scripts/exact_commit/probability_audit_controls.py scripts/exact_commit/run_probability_audit.py scripts/exact_commit/build_probability_audit_results.py` | PASS |
| `.venv/bin/ruff format --check <four audit scripts and new regression file>` | PASS |
| `.venv/bin/mypy` | PASS: 108 source files |
| `make test-rust-parser` | 24 passed; parser/binding fmt and clippy PASS |
| `.venv/bin/python -m pytest -q vendor/EPIC-Decoding/tests/test_constrain_utils.py vendor/EPIC-Decoding/tests/test_bindings.py` | 19 passed, 4 existing upstream skips |
| `./scripts/verify_upstream.sh` | PASS: unchanged 5b1b31098f34ed3691d2a9f4aae14fdf5839d072 |
| `.venv/bin/python scripts/exact_commit/check_formal_project.py --lake <installed-pinned-lake> --output results/processed/m31-formal-checks.json` | PASS: 35 universal declarations, 16 concrete claims, forged-bound rejection |
| `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.exact_commit.build_probability_audit_results --capture results/raw/m31_probability_v1/capture` | PASS: full local source checks and 35 proofs; final regeneration with offline reference repeats only the check, not model measurements |
| `make article-results-check` | PASS: all historical/current derivatives, complete inventories, 2,664 M29, 192 M30 and 35 M31 proofs |
| `PYTHONDONTWRITEBYTECODE=1 make release-wheel-smoke` | PASS: isolated installed-wheel proof/experiment/artifact/Lean-export; no editable-source leakage; sdist 48868031 bytes under unchanged 50MB gate |
| `make -C paper; pdftoppm -r 100 -png paper/main.pdf <local-render-prefix>` | PASS: 16 pages, no overflow/unresolved references, all 16 rendered pages visually inspected |
| `git diff --check` | PASS |

Correctness controls check 19,680 byte strings against independent JSON/schema parsing, 6,272 original-token products at seeds 310000–310031, and 128 partial/exhaustive rational partitions. Aliases, omitted mass, partial/refused admission, zero feasible mass, reweighting, categorical tickets, forged input/bounds, fabricated softmax and changed tokenizer bytes are covered. The full suite preserves prior ambiguity, fixed-slot, EOS/PAD, infeasibility, timeout and upstream regressions.

Lean checks 35 audited universal specifications and 16 concrete resource claims across five fixtures, and rejects a forged bound. Original-input correspondence uses the independent Python checker. The prior 75-node real replay export timed out at 180 seconds and remains unfinished; blanket acceptance of large proofs, the full trajectory coupling library and Python/Rust/model source refinement are not claimed.

Original primary numeric-reference timings lacked a separately recorded coverage phase. They are retained unchanged, excluded from final cost comparisons, and complemented by a separately committed fresh-worker follow-up over the same 18 inputs. No prediction, partition outcome or case selection changed.

Full large-logit/softmax traces stay in ignored local capture storage. The source verifier checked those logits, full-row normalization and tokenizer bytes. Git stores complete original retained rational probabilities, tokenizer semantics, source hashes, all proofs/statuses and derivative products, reproducing mathematics/tables offline. Users without that capture cannot independently recover the unavailable source matrices merely from hashes. A new opt-in model run is a reproduction, not bitwise GPU equivalence.

The installed non-editable wheel was exercised from a clean freeze, outside the checkout, without source-tree leakage. The source archive remains under the unchanged 50 MB guard; bulk campaign data stays in the Git evidence checkout. All 16 final PDF pages were rendered and visually inspected, with the unchanged overflow/reference gate. No remote push/publication, slides or presentation script was performed.

Complete frozen protocol: `docs/research/m31-relevance-audit.md`. Every cell and claim verdict: `docs/artifacts/processed/m31_probability_v1/report.md`. The JSON companion records producer commits, immutable manifests, source/PDF hashes and exact command outcomes. Detailed logs remain ignored locally.
