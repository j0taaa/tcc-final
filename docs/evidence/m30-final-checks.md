# M29/M30 final verification — 5 October 2026

Implementation/evidence freeze: `b4a4746d28e56171d57e1a82163d8a6b0f4eb43f`. Final verification: **PASS**.

Fresh MDLM observations are twelve small structured-output canvases, not external user requests or 192 independent samples. The mathematical contribution is finite-token certifying optimization and probability/error-controlled admission, specializing established methods. The complete proof boundary remains explicit.

| Command/check | Actual result |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q` | 1482 passed in 140.20s |
| `.venv/bin/ruff check src tests scripts/exact_commit/build_probability_results.py scripts/exact_commit/build_conflict_results.py` | PASS |
| `.venv/bin/mypy` | PASS: 108 source files |
| `make test-rust-parser` | 24 passed; fmt/clippy parser and bindings PASS |
| `.venv/bin/python -m pytest -q vendor/EPIC-Decoding/tests/test_constrain_utils.py vendor/EPIC-Decoding/tests/test_bindings.py` | 19 passed, 4 existing skips |
| `./scripts/verify_upstream.sh` | PASS: unchanged 5b1b31098f34ed3691d2a9f4aae14fdf5839d072 |
| `.venv/bin/python scripts/exact_commit/check_formal_project.py --lake <installed-pinned-lake> --output docs/evidence/m30-formal-checks.json` | 35 audited universal theorems, 16 concrete claims across 5 fixtures, forged-bound rejection PASS |
| `make article-results-check` | PASS: all current/historical derivatives, complete archives, 2664 M29 and 192 M30 proofs |
| `make release-wheel-smoke` | PASS: independent budget proof, experiment/artifact generator, installed Lean export and sdist guard; fixture run before final clean commit emitted dirty-worktree warning, not published measurements |
| `.venv/bin/python -m build --no-isolation --outdir results/processed/m30-dist` | sdist and wheel built from clean source commit |
| `isolated venv, local wheel pip install --no-deps, python -I -m mwpc_exact.mass_cli --verify <each real proof> --sample --max-tv 1/20` | PASS: two admitted samples, one refusal; isolated imports, no model/optimizer/network dependencies |
| `make -C paper; pdftoppm -r 100 -png paper/main.pdf <render-prefix>` | 16 pages, no overflow/unresolved references; all 16 final pages visually inspected |
| `verify each interruption-audit/inventory.json content reference against its original SHA-256` | 5527 exact original-file entries across 5 attempts; only additional diagnostic logs have explicit path sanitization |

Current data: 3,312 M29 jobs/2,664 proofs; twelve fresh M30 canvases/192 proofs (51 admitted, 93 incomplete, 48 zero mass). Complete archives and every unfavorable outcome remain versioned. GPU generation was unavailable; actual new official MDLM predictions used CPU F32 kernels and recorded F64/rational normalization.

At 64 calls, full-support coverage evidence authorizes 9/12 updates at TV tolerance 0.05; the generic tail bound authorizes none. This compares certificate strength on identical predictions, not semantic accuracy or a population win rate. A two-slot license prediction implies approximately 1.55×10^11 independent rejection draws in expectation; no such trial or wall-time speedup is fabricated.

Lean: 35 audited universal statements and 16 concrete resource claims, plus one constructed small conflict. The separate 75-node replay export timed out at 180 seconds. Every replay/probability certificate passes the independent Python checker; source refinement, the full coupling library and blanket large-certificate Lean acceptance are not claimed. Formal timeouts now terminate actual descendants.

Local wheel and source distribution were built from the clean freeze. An isolated dependency-free wheel outside the checkout reverified two real model proofs, produced their admitted JSON/recursive samples and refused a third uncertified tolerance. Bulk M29/M30 evidence is excluded from the install archives, preserved in Git for full reproduction. No weights or caches are distributed.

All 16 final PDF pages were rendered and visually inspected. The page/overflow/reference gate is unchanged. Historical tables and longer proofs were moved to preserved supplements, without changing historical results or weakening tests. The bibliography inventory has 43 primary-source-verified records.

`m30-final-checks.json` records command results, implementation/producer commits, original manifests, proof scope, isolated-wheel outputs and source/PDF SHA-256 values. Detailed full command logs remain in ignored `results/processed/`; the recorded outcomes and scientific archives are versioned. No remote publication, push, slide deck or presentation script was created.
