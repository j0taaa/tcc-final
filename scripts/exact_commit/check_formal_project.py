"""Mandatory offline Lean gates, concrete certificate cases and rejection checks.

Install formal/lean-toolchain explicitly before running this command. Normal
Python tests do not download Lean; this formal gate fails if Lean is unavailable.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

from budget_math_example import generate

from mwpc_exact import (
    CompositionalByteLevelAdapter,
    EOSMode,
    EOSPolicy,
    Proposal,
    SupportKind,
    SupportPolicy,
    build_per_position_support,
)
from mwpc_exact.budget_proof import budget_proof_data
from mwpc_exact.budgeted_commit import budgeted_commit_frontier
from mwpc_exact.evaluation.selection import SelectionInput
from mwpc_exact.lean_bridge import audit_lean_axioms, export_lean_budget_proof, verify_with_lean
from mwpc_exact.reference.byte_grammars import _SourceGrammarBuilder
from mwpc_exact.reference.normalization import normalize_to_cnf


def fixture(words, emissions, rows, proposals=(), *, eos=None, canvas=None):
    builder = _SourceGrammarBuilder(("S",), start="S")
    for word in words:
        builder.rule("S", *((word,) if word else ()))
    grammar = normalize_to_cnf(builder.build()).grammar
    policy = eos or EOSPolicy(EOSMode.ABSENT)
    canvas = canvas or (None,) * len(rows)
    specials = tuple(
        dict.fromkeys(
            (
                *policy.termination_token_ids,
                *((policy.pad_token_id,) if policy.pad_token_id is not None else ()),
            )
        )
    )
    support = build_per_position_support(
        canvas=canvas,
        proposals=proposals,
        policy=SupportPolicy(
            kind=SupportKind.EXPLICIT,
            vocabulary_size=len(emissions),
            required_special_token_ids=specials,
        ),
        explicit_support=dict(enumerate(rows)),
    )
    state = SelectionInput(
        grammar,
        canvas,
        tuple(proposals),
        support,
        CompositionalByteLevelAdapter(tuple(emissions)),
        policy,
    )
    return budget_proof_data(state, budgeted_commit_frontier(state, len(rows)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default="lake")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    formal = root / "formal"
    cases = {
        "budget_frontier": generate(),
        "shared_prefix_alias": fixture(
            (b"a", b"ab", b"ac"),
            (b"a", b"ab", b"ac", b"a"),
            ((0, 1, 2, 3),),
            (Proposal(0, 0, 1, 0.1), Proposal(1, 0, 3, 0.5)),
        ),
        "fixed_utf8_eos_pad": fixture(
            (b"\xc3\xa9",),
            (b"\xc3", b"\xa9", None),
            ((0,), (1,), (2,), (2,)),
            (Proposal(0, 0, 0, 99), Proposal(1, 1, 1, 0.5), Proposal(2, 2, 2, 1)),
            canvas=(0, None, None, None),
            eos=EOSPolicy(EOSMode.REQUIRED, (2,), 2),
        ),
        "empty_epsilon": fixture(
            (b"",),
            (None,),
            ((0,), (0,)),
            (Proposal(0, 0, 0, 0.5),),
            eos=EOSPolicy(EOSMode.REQUIRED, (0,), 0),
        ),
        "infeasible": fixture((b"b",), (b"a",), ((0,),)),
    }
    reports = {
        name: verify_with_lean(data, formal_directory=formal, lake=args.lake)
        for name, data in cases.items()
    }
    for source in [formal / "MWPC.lean", *(formal / "MWPC").glob("*.lean")]:
        if re.search(
            r"\b(sorry|admit|native_decide)\b|^\s*axiom\b", source.read_text(), re.MULTILINE
        ):
            raise ValueError(f"Unapproved admission or axiom in {source.name}")
    audit = subprocess.run(
        [args.lake, "env", "lean", "Audit.lean"],
        cwd=formal,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if audit.returncode:
        raise RuntimeError(f"Universal proof audit failed: {audit.stdout}{audit.stderr}")
    expected = tuple(re.findall(r"#print axioms (\S+)", (formal / "Audit.lean").read_text()))
    universal = audit_lean_axioms(audit.stdout, expected)
    # Check the versioned example against its original JSON, then prove that
    # changing a formal root bound is rejected by the kernel itself.
    canonical = export_lean_budget_proof(cases["budget_frontier"]).source
    if (formal / "examples/BudgetExample.lean").read_text() != canonical:
        raise ValueError("versioned Lean example differs from its original input proof")
    with tempfile.TemporaryDirectory(prefix="mwpc-lean-reject-") as temporary:
        source = Path(temporary) / "Forged.lean"
        forged = canonical.replace(
            "RootUpper grammar graph potentials 1 7", "RootUpper grammar graph potentials 1 0", 1
        )
        if forged == canonical:
            raise ValueError("rejection fixture did not alter the bound")
        source.write_text(forged)
        rejected = subprocess.run(
            [args.lake, "env", "lean", str(source)],
            cwd=formal,
            capture_output=True,
            text=True,
            timeout=180,
        )
        if rejected.returncode == 0:
            raise AssertionError("Lean accepted a forged optimum bound")
    report = {
        "verification": "PASS",
        "universal_axiom_dependencies": universal,
        "cases": reports,
        "kernel_rejects_forged_bound": True,
        "original_input_correspondence": "independent_python_checker",
        "excluded": [
            "source-level Python/Rust refinement",
            "model inference",
            "external tokenizer implementation",
            "runtime and semantic accuracy",
        ],
    }
    output = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        with args.output.open("x") as file:
            file.write(output)
    print(output, end="")


if __name__ == "__main__":
    main()
