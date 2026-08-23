# Environment baseline

Measured on 2026-08-23 during T001. These values describe the CPU baseline
environment; they are not model-inference or benchmark results.

- OS: Ubuntu 24.04.4 LTS (noble), Linux 7.0.0-28-generic, x86_64
- CPU: Intel Core i7-11700K, 1 socket, 8 cores, 16 threads
- RAM: 15 GiB; swap: 4 GiB
- Detected GPU / VRAM: NVIDIA GeForce RTX 3080 Ti, 12,288 MiB; driver 595.84
- Python: CPython 3.11.16
- pip: 26.2.1
- Rust: rustc 1.98.0 (`88d9e12ae`, LLVM 22.1.8)
- Cargo: 1.98.0 (`797e8a9bc`)
- C compiler: GCC 13.3.0
- Maturin: 1.14.1
- PyTorch: 2.8.0+cpu; `torch.cuda.is_available() == False`; CUDA runtime absent
- TeX: pdfTeX 1.40.29 / TeX Live 2026; BibTeX 0.99e
- EPIC commit: `5b1b31098f34ed3691d2a9f4aae14fdf5839d072`

## Installation and import provenance

The root package is installed editable in `.venv`. The PyO3 extension was
built in release mode from
`vendor/EPIC-Decoding/rustformlang_bindings` using the same Python 3.11
environment.

The pinned EPIC `pyproject.toml` is not accepted by current setuptools because
`project.authors` uses a string instead of a PEP 621 author table. The
submodule remains read-only: `make bootstrap-epic` installs the pinned CPU
dependencies from `requirements/epic-baseline-cpu.txt` and generates an
environment-local `.pth` file with `scripts/install_epic_checkout.py`.

Verified imports resolve to the current checkout:

```text
constrained_diffusion -> vendor/EPIC-Decoding/constrained_diffusion/__init__.py
rustformlang -> vendor/EPIC-Decoding/rustformlang_bindings/rustformlang/__init__.py
```

`python -m pip check` reported `No broken requirements found.`

The `uv`, rustup, and TinyTeX installers place user tools outside the virtual
environment. Their commands are exposed through `~/.local/bin`, so activating
`.venv` does not hide `cargo`, `rustc`, `pdflatex`, or `bibtex`.

## Paper toolchain verification

`make paper` completed with pdfLaTeX, BibTeX, and two final pdfLaTeX passes.
The generated, gitignored `paper/main.pdf` is 15 pages (340,147 bytes). The
log contains only ordinary underfull-box typography warnings; no citation,
reference, package, or build error remains. No scientific placeholder was
replaced during this setup verification.
