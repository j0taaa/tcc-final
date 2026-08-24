PYTHON ?= python3.11
VENV ?= .venv
VENV_PY := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
EPIC_CPU_INDEX ?= https://download.pytorch.org/whl/cpu

.PHONY: bootstrap bootstrap-epic verify-upstream install check lint format typecheck test test-unit test-exact test-upstream test-m4-extended paper clean

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

test-upstream:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=vendor/EPIC-Decoding \
		$(VENV_PY) -m pytest -q vendor/EPIC-Decoding/tests

test-m4-extended:
	$(VENV_PY) scripts/exact_commit/run_m4_graph_differential.py

test: test-unit test-exact

check: verify-upstream lint typecheck test

paper:
	$(MAKE) -C paper

clean:
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage dist build
	$(MAKE) -C paper clean || true
