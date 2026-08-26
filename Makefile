PYTHON ?= python3.11
VENV ?= .venv
VENV_PY := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
EPIC_CPU_INDEX ?= https://download.pytorch.org/whl/cpu

.PHONY: bootstrap bootstrap-epic bootstrap-rust-parser verify-upstream install check lint format typecheck test test-unit test-exact test-integration test-upstream check-integration test-m4-extended test-m5-differential test-m6-differential test-m7-counterexamples test-m7-differential test-rust-parser paper clean

bootstrap:
	git submodule update --init --recursive
	$(PYTHON) -m venv $(VENV)
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -e '.[dev]'
	./scripts/verify_upstream.sh

bootstrap-epic: bootstrap
	$(VENV_PIP) install --index-url $(EPIC_CPU_INDEX) 'torch==2.8.0+cpu'
	$(VENV_PIP) install -r requirements/epic-baseline-cpu.txt
	cd vendor/EPIC-Decoding/rustformlang_bindings && ../../../$(VENV)/bin/maturin develop --release
	$(VENV_PY) scripts/install_epic_checkout.py
	PYTHONDONTWRITEBYTECODE=1 $(VENV_PY) -c "import constrained_diffusion, rustformlang; print('EPIC imports ok')"

bootstrap-rust-parser: bootstrap
	cd crates/mwpc_parser_py && ../../$(VENV)/bin/maturin develop --release
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

test: test-unit test-exact

check: verify-upstream lint typecheck test

check-integration: test-integration

paper:
	$(MAKE) -C paper

clean:
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage dist build
	$(MAKE) -C paper clean || true
