PYTHON ?= python3
VENV ?= .venv
VENV_PY ?= $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
LAKE ?= lake
CONSTRAINTS := requirements/constraints-py311-linux.txt

.PHONY: help setup setup-epic setup-rust check test format rust formal evidence paper demo clean

help:
	@echo 'make setup     Instala o ambiente Python de desenvolvimento'
	@echo 'make check     Verifica baseline, lint, tipos e testes offline'
	@echo 'make test      Executa somente os testes'
	@echo 'make demo      Executa o exemplo publico sem carregar modelo'
	@echo 'make evidence  Confere dados e derivados cientificos preservados'
	@echo 'make paper     Confere evidencias e compila o artigo'
	@echo 'make rust      Verifica parser e bindings Rust'
	@echo 'make formal    Verifica as especificacoes Lean'
	@echo 'make format    Aplica formatacao e correcoes de lint'
	@echo 'make clean     Remove caches de ferramentas e produtos de build'
	@echo 'Opcionais: make setup-rust / make setup-epic'

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PIP) install --upgrade 'pip==26.2.1'
	$(VENV_PIP) install -c $(CONSTRAINTS) --build-constraint $(CONSTRAINTS) -e '.[dev]'
	./scripts/verify_upstream.sh

setup-epic: setup
	$(VENV_PIP) install -c $(CONSTRAINTS) --index-url https://download.pytorch.org/whl/cpu 'torch==2.8.0+cpu'
	$(VENV_PIP) install -c $(CONSTRAINTS) -r requirements/epic-baseline-cpu.txt
	cd vendor/EPIC-Decoding/rustformlang_bindings && ../../../$(VENV)/bin/maturin develop --release --locked
	$(VENV_PY) scripts/install_epic_checkout.py

setup-rust: setup
	cd crates/mwpc_parser_py && ../../$(VENV)/bin/maturin develop --release --locked

check:
	./scripts/verify_upstream.sh
	$(VENV_PY) -m ruff check src scripts
	$(VENV_PY) -m ruff format --check src scripts
	$(VENV_PY) -m mypy
	$(MAKE) test

test:
	$(VENV_PY) -m unittest discover -s tests -v

format:
	$(VENV_PY) -m ruff format src scripts
	$(VENV_PY) -m ruff check --fix src scripts

rust:
	cargo fmt --manifest-path crates/mwpc_parser/Cargo.toml --all -- --check
	cargo clippy --manifest-path crates/mwpc_parser/Cargo.toml --all-targets --locked -- -D warnings
	cargo fmt --manifest-path crates/mwpc_parser_py/Cargo.toml --all -- --check
	PYO3_PYTHON=$(shell $(VENV_PY) -c 'import sys; print(sys.executable)') cargo clippy --manifest-path crates/mwpc_parser_py/Cargo.toml --all-targets --locked -- -D warnings

formal:
	$(VENV_PY) scripts/exact_commit/check_formal_project.py --lake $(LAKE)

evidence:
	$(VENV_PY) scripts/verify_artifacts.py
	$(VENV_PY) -m scripts.exact_commit.build_probability_audit_results --check
	$(VENV_PY) -m scripts.exact_commit.build_cfg_posterior_results --check
	$(VENV_PY) -m scripts.exact_commit.build_depth_certificate_results --check
	$(VENV_PY) -m scripts.exact_commit.audit_adaptive_semantics --output docs/artifacts/raw/m36_adaptive_semantics_v1 --latex-check paper/generated/m36-adaptive-table.tex

paper: evidence
	$(MAKE) -C paper

demo:
	$(VENV_PY) -m attempts.24-certified-depth-approximation.work.demo \
		--packet attempts/24-certified-depth-approximation/work/evidence/first-full-head-v2/packet.zip \
		--tolerance 1/1000 --seed 42

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache dist build
	$(MAKE) -C paper clean
