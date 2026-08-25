#!/usr/bin/env python3
"""Update generated imports after moving policy, backend, and research modules."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REPLACEMENTS = {
    "from mwpc_exact.eos_lattice import EOSMode, EOSPolicy, TokenRole": (
        "from mwpc_exact.eos_policy import EOSMode, EOSPolicy, TokenRole"
    ),
    "from mwpc_exact.eos_lattice import EOSMode, EOSPolicy": (
        "from mwpc_exact.eos_policy import EOSMode, EOSPolicy"
    ),
    "from mwpc_exact.eos_lattice import EOSPolicy": "from mwpc_exact.eos_policy import EOSPolicy",
    (
        "from mwpc_exact.eos_lattice import "
        "EOSLattice, EOSLatticePath, EOSMode, EOSPolicy, build_eos_lattice"
    ): (
        "from mwpc_exact.eos_lattice import EOSLattice, EOSLatticePath, build_eos_lattice\n"
        "from mwpc_exact.eos_policy import EOSMode, EOSPolicy"
    ),
    (
        "from mwpc_exact.eos_lattice import (\n"
        "    EOSLattice,\n"
        "    EOSLatticePath,\n"
        "    EOSMode,\n"
        "    EOSPolicy,\n"
        "    TokenRole,\n"
        "    build_eos_lattice,\n"
        ")"
    ): (
        "from mwpc_exact.eos_lattice import (\n"
        "    EOSLattice,\n"
        "    EOSLatticePath,\n"
        "    build_eos_lattice,\n"
        ")\n"
        "from mwpc_exact.eos_policy import EOSMode, EOSPolicy, TokenRole"
    ),
    (
        "from mwpc_exact.eos_lattice import "
        "EOSLatticePath, EOSMode, EOSPolicy, build_eos_lattice"
    ): (
        "from mwpc_exact.eos_lattice import EOSLatticePath, build_eos_lattice\n"
        "from mwpc_exact.eos_policy import EOSMode, EOSPolicy"
    ),
    "from mwpc_exact.finite_solver import ExactBackend, solve_exact_commit": (
        "from mwpc_exact.backend import ExactBackend\n"
        "from mwpc_exact.finite_solver import solve_exact_commit"
    ),
    "from mwpc_exact.finite_solver import ExactBackend": "from mwpc_exact.backend import ExactBackend",
}

for directory in (ROOT / "src", ROOT / "tests", ROOT / "scripts"):
    for path in directory.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        updated = text
        for old, new in REPLACEMENTS.items():
            updated = updated.replace(old, new)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
