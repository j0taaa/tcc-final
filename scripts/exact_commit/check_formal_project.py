"""Check the pinned Lean library and canonical proof, without a regression suite."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from mwpc_exact.lean_bridge import _run_lean, audit_lean_axioms


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default="lake")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    formal = Path(__file__).resolve().parents[2] / "formal"
    for source in [formal / "MWPC.lean", *(formal / "MWPC").glob("*.lean")]:
        if re.search(
            r"\b(sorry|admit|native_decide)\b|^\s*axiom\b", source.read_text(), re.MULTILINE
        ):
            raise ValueError(f"Unapproved admission or axiom: {source.name}")
    build = _run_lean(
        [
            args.lake,
            "build",
            "MWPC",
            "MWPC.CfgSampling",
            "MWPC.SemanticProfiles",
            "MWPC.AdaptiveSemantics",
        ],
        cwd=formal,
        timeout=180,
    )
    if build.returncode:
        raise RuntimeError(build.stdout + build.stderr)
    axioms = {}
    for source in ("Audit.lean", "AuditCfgSampling.lean"):
        audited = _run_lean([args.lake, "env", "lean", source], cwd=formal, timeout=180)
        if audited.returncode:
            raise RuntimeError(audited.stdout + audited.stderr)
        expected = tuple(re.findall(r"#print axioms (\S+)", (formal / source).read_text()))
        axioms.update(audit_lean_axioms(audited.stdout, expected))
    example = _run_lean(
        [args.lake, "env", "lean", "examples/BudgetExample.lean"], cwd=formal, timeout=180
    )
    if example.returncode:
        raise RuntimeError(example.stdout + example.stderr)
    report = {
        "verification": "PASS",
        "universal_axiom_dependencies": axioms,
        "canonical_lean_example": "PASS",
        "regression_suite": "historical suite removed; focused M34 tests run separately",
        "scope": "Lean specifications/canonical proof; not Python/Rust source refinement",
    }
    raw = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        with args.output.open("x") as output:
            output.write(raw)
    print(raw, end="")


if __name__ == "__main__":
    main()
