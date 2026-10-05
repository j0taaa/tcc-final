PYTHON ?= python3.11
VENV ?= .venv
VENV_PY := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
LAKE ?= lake
PYTHON_CONSTRAINTS := requirements/constraints-py311-linux.txt
EPIC_CPU_INDEX ?= https://download.pytorch.org/whl/cpu
ARTIFACT_CONFIG ?= configs/analysis/t1201_q3_artifacts_v1.toml
STATISTICS_CONFIG ?= configs/analysis/t1202_statistics_v1.toml
FINAL_ARTIFACT_CONFIG ?= configs/analysis/t1203_final_artifacts_v1.toml
ARTICLE_RESULT_CONFIG ?= configs/analysis/m1301_article_results_v1.toml

.PHONY: bootstrap bootstrap-epic bootstrap-rust-parser verify-upstream install check check-formal check-project lint format typecheck test test-unit test-exact test-integration test-upstream check-integration test-m4-extended test-m5-differential test-m6-differential test-m7-counterexamples test-m7-differential test-rust-parser artifacts artifacts-check statistics statistics-check final-artifacts final-artifacts-check article-results article-results-check release-wheel-smoke rehearse-artifact-rebuild rehearse-source-correctness rehearse-cpu-correctness query-demo-check paper clean

bootstrap:
	git submodule update --init --recursive
	$(PYTHON) -m venv $(VENV)
	$(VENV_PIP) install --upgrade 'pip==26.2.1'
	$(VENV_PIP) install -c $(PYTHON_CONSTRAINTS) --build-constraint $(PYTHON_CONSTRAINTS) -e '.[dev]'
	./scripts/verify_upstream.sh

bootstrap-epic: bootstrap
	$(VENV_PIP) install -c $(PYTHON_CONSTRAINTS) --index-url $(EPIC_CPU_INDEX) 'torch==2.8.0+cpu'
	$(VENV_PIP) install -c $(PYTHON_CONSTRAINTS) -r requirements/epic-baseline-cpu.txt
	cd vendor/EPIC-Decoding/rustformlang_bindings && ../../../$(VENV)/bin/maturin develop --release --locked
	$(VENV_PY) scripts/install_epic_checkout.py
	PYTHONDONTWRITEBYTECODE=1 $(VENV_PY) -c "import constrained_diffusion, rustformlang; print('EPIC imports ok')"

bootstrap-rust-parser: bootstrap
	cd crates/mwpc_parser_py && ../../$(VENV)/bin/maturin develop --release --locked
	$(VENV_PY) -c "import mwpc_parser_py; print('MWPC Rust parser import ok')"

verify-upstream:
	./scripts/verify_upstream.sh

lint:
	$(VENV_PY) -m ruff check src tests

typecheck:
	$(VENV_PY) -m mypy src

format:
	$(VENV_PY) -m ruff format src tests
	$(VENV_PY) -m ruff check --fix src tests

test-unit:
	$(VENV_PY) -m pytest -q tests/unit

test-exact:
	$(VENV_PY) -m pytest -q tests/exact_commit

test-integration:
	$(VENV_PY) -m pytest -q tests/integration

test-upstream:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=vendor/EPIC-Decoding \
		$(VENV_PY) -m pytest -q vendor/EPIC-Decoding/tests

test-m4-extended:
	$(VENV_PY) scripts/exact_commit/run_m4_graph_differential.py

test-m5-differential:
	$(VENV_PY) scripts/exact_commit/run_m5_rust_differential.py

test-m6-differential:
	$(VENV_PY) scripts/exact_commit/run_m6_finite_lattice_differential.py

test-m7-counterexamples:
	$(VENV_PY) scripts/exact_commit/replay_t703_finite_slot_counterexamples.py

test-m7-differential:
	$(VENV_PY) scripts/exact_commit/run_m7_eos_finite_slot_differential.py

test-rust-parser:
	cargo fmt --manifest-path crates/mwpc_parser/Cargo.toml --all -- --check
	cargo test --manifest-path crates/mwpc_parser/Cargo.toml
	cargo clippy --manifest-path crates/mwpc_parser/Cargo.toml --all-targets -- -D warnings
	cargo fmt --manifest-path crates/mwpc_parser_py/Cargo.toml --all -- --check
	PYO3_PYTHON=$(CURDIR)/$(VENV_PY) cargo clippy --manifest-path crates/mwpc_parser_py/Cargo.toml --all-targets -- -D warnings

artifacts:
	$(VENV_PY) scripts/exact_commit/build_publication_artifacts.py --config $(ARTIFACT_CONFIG)

artifacts-check:
	$(VENV_PY) scripts/exact_commit/build_publication_artifacts.py --config $(ARTIFACT_CONFIG) --verify-existing

statistics:
	$(VENV_PY) scripts/exact_commit/build_statistical_summary.py --config $(STATISTICS_CONFIG)

statistics-check:
	$(VENV_PY) scripts/exact_commit/build_statistical_summary.py --config $(STATISTICS_CONFIG) --verify-existing

final-artifacts:
	$(VENV_PY) scripts/exact_commit/build_final_artifacts.py --config $(FINAL_ARTIFACT_CONFIG)

final-artifacts-check:
	$(VENV_PY) scripts/exact_commit/build_final_artifacts.py --config $(FINAL_ARTIFACT_CONFIG) --verify-existing

article-results:
	$(VENV_PY) scripts/exact_commit/build_article_results.py --config $(ARTICLE_RESULT_CONFIG)
	$(VENV_PY) scripts/exact_commit/build_selection_audit.py
	$(VENV_PY) -m scripts.exact_commit.build_json_repair_results
	$(VENV_PY) scripts/exact_commit/build_policy_campaign.py
	$(VENV_PY) scripts/exact_commit/build_grounded_campaign.py
	$(VENV_PY) scripts/exact_commit/build_query_demo_results.py
	$(VENV_PY) scripts/exact_commit/build_live_article_results.py --grounded
	$(VENV_PY) -m scripts.exact_commit.build_budgeted_real_results
	$(VENV_PY) -m scripts.exact_commit.build_conflict_results
	$(VENV_PY) -m scripts.exact_commit.build_probability_results

article-results-check:
	$(VENV_PY) scripts/exact_commit/build_article_results.py --config $(ARTICLE_RESULT_CONFIG) --verify-existing
	$(VENV_PY) scripts/exact_commit/build_review_results.py --check
	$(VENV_PY) scripts/exact_commit/build_selection_audit.py --check
	$(VENV_PY) -m scripts.exact_commit.build_json_repair_results --check
	$(VENV_PY) scripts/exact_commit/build_policy_campaign.py --check
	$(VENV_PY) scripts/exact_commit/build_grounded_campaign.py --check
	$(VENV_PY) scripts/exact_commit/freeze_grounded_confirmation.py --check
	$(VENV_PY) scripts/exact_commit/build_query_demo_results.py --check
	$(VENV_PY) scripts/exact_commit/build_live_article_results.py --grounded --check
	$(VENV_PY) -m scripts.exact_commit.build_budgeted_real_results --check
	$(VENV_PY) -m scripts.exact_commit.build_conflict_results --check
	$(VENV_PY) -m scripts.exact_commit.build_probability_results --check

query-demo-check:
	$(VENV_PY) scripts/exact_commit/build_query_demo_results.py --check

release-wheel-smoke:
	$(VENV_PY) scripts/rehearse_release_wheel.py

rehearse-artifact-rebuild:
	./scripts/rehearse_cpu_correctness.sh artifact-rebuild

rehearse-source-correctness:
	./scripts/rehearse_cpu_correctness.sh source-experiment-rerun

# Backward-compatible name for the former artifact-only rehearsal.
rehearse-cpu-correctness: rehearse-artifact-rebuild

test: test-unit test-exact

check: verify-upstream lint typecheck test

check-formal:
	$(VENV_PY) scripts/exact_commit/check_formal_project.py --lake $(LAKE)

# All scientific layers: theorem kernel, implementations, baselines and paper data.
check-project: check check-formal test-rust-parser test-integration test-upstream article-results-check

check-integration: test-integration

paper: article-results-check
	$(MAKE) -C paper

clean:
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage dist build
	$(MAKE) -C paper clean || true
