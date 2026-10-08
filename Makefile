PYTHON ?= python3
VENV ?= .venv
VENV_PY ?= $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
LAKE ?= lake
CONSTRAINTS := requirements/constraints-py311-linux.txt

.PHONY: bootstrap bootstrap-epic bootstrap-rust-parser verify-upstream lint format typecheck check check-formal check-project build-rust article-results article-results-check paper research-note test clean

bootstrap:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PIP) install --upgrade 'pip==26.2.1'
	$(VENV_PIP) install -c $(CONSTRAINTS) --build-constraint $(CONSTRAINTS) -e '.[dev]'
	./scripts/verify_upstream.sh

bootstrap-epic: bootstrap
	$(VENV_PIP) install -c $(CONSTRAINTS) --index-url https://download.pytorch.org/whl/cpu 'torch==2.8.0+cpu'
	$(VENV_PIP) install -c $(CONSTRAINTS) -r requirements/epic-baseline-cpu.txt
	cd vendor/EPIC-Decoding/rustformlang_bindings && ../../../$(VENV)/bin/maturin develop --release --locked
	$(VENV_PY) scripts/install_epic_checkout.py

bootstrap-rust-parser: bootstrap
	cd crates/mwpc_parser_py && ../../$(VENV)/bin/maturin develop --release --locked

verify-upstream:
	./scripts/verify_upstream.sh

lint:
	$(VENV_PY) -m ruff check src scripts
	$(VENV_PY) -m ruff format --check src scripts

format:
	$(VENV_PY) -m ruff format src scripts
	$(VENV_PY) -m ruff check --fix src scripts

typecheck:
	$(VENV_PY) -m mypy

check: verify-upstream lint typecheck

build-rust:
	cargo fmt --manifest-path crates/mwpc_parser/Cargo.toml --all -- --check
	cargo clippy --manifest-path crates/mwpc_parser/Cargo.toml --all-targets --locked -- -D warnings
	cargo fmt --manifest-path crates/mwpc_parser_py/Cargo.toml --all -- --check
	PYO3_PYTHON=$(shell $(VENV_PY) -c 'import sys; print(sys.executable)') cargo clippy --manifest-path crates/mwpc_parser_py/Cargo.toml --all-targets --locked -- -D warnings

check-formal:
	$(VENV_PY) scripts/exact_commit/check_formal_project.py --lake $(LAKE)

# Focused M34/M35 checks and M36 research oracle; historical suite stays absent.
check-project: check test build-rust check-formal article-results-check

article-results:
	$(VENV_PY) -m scripts.exact_commit.build_probability_audit_results
	$(VENV_PY) -m scripts.exact_commit.build_cfg_posterior_results

article-results-check:
	$(VENV_PY) scripts/verify_artifacts.py
	$(VENV_PY) -m scripts.exact_commit.build_probability_audit_results --check
	$(VENV_PY) -m scripts.exact_commit.build_cfg_posterior_results --check
	$(VENV_PY) -m scripts.exact_commit.audit_adaptive_semantics --output docs/artifacts/raw/m36_adaptive_semantics_v1 --latex-check paper/generated/m36-adaptive-table.tex

paper: article-results-check
	$(MAKE) -C paper

research-note:
	$(MAKE) -C paper research-note

test:
	$(VENV_PY) -m unittest discover -s tests -v

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache dist build
	$(MAKE) -C paper clean
