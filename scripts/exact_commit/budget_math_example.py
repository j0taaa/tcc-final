"""Emit or independently verify a finite mathematical example, not a benchmark.

The verification mode imports the proof checker without importing the optimizer.
New proofs bind the graph and token witness to their original input. Historical
M26 files remain verifiable with their explicitly narrower resource-graph scope.
No model, tokenizer download, GPU or network is needed.
"""

from __future__ import annotations

import argparse
import json
from fractions import Fraction
from pathlib import Path

from mwpc_exact.budget_proof import budget_proof_data, verify_budget_proof
from mwpc_exact.reference.budget_certificate import check_budget_certificate
from mwpc_exact.reference.budget_types import (
    BudgetCertificate,
    BudgetPathResult,
    ResourceArc,
    ResourceDAG,
)
from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.types import SolveStatus


def generate():
    # Deliberately inside generation: --verify does not load the optimizer.
    from mwpc_exact import (
        CompositionalByteLevelAdapter,
        EOSMode,
        EOSPolicy,
        Proposal,
        SupportKind,
        SupportPolicy,
        build_per_position_support,
    )
    from mwpc_exact.budgeted_commit import budgeted_commit_frontier
    from mwpc_exact.reference.grammar import Nonterminal, Terminal
    from mwpc_exact.reference.normalization import (
        SourceGrammar,
        SourceProduction,
        TerminalRef,
        normalize_to_cnf,
    )
    from mwpc_exact.state import SelectionInput

    emissions = tuple(bytes((a,)) for a in b"abcxyz")
    source = SourceGrammar(
        (Nonterminal(0, "S"),),
        tuple(Terminal(i, a[0]) for i, a in enumerate(emissions)),
        0,
        (
            SourceProduction(0, 0, tuple(TerminalRef(i) for i in (0, 1, 2))),
            SourceProduction(1, 0, tuple(TerminalRef(i) for i in (3, 4, 5))),
        ),
    )
    grammar = normalize_to_cnf(source).grammar
    proposals = (Proposal(0, 0, 0, 0.875), Proposal(1, 1, 4, 0.5), Proposal(2, 2, 5, 0.5))
    support = build_per_position_support(
        canvas=(None,) * 3,
        policy=SupportPolicy(kind=SupportKind.EXPLICIT, vocabulary_size=6),
        explicit_support={0: (0, 3), 1: (1, 4), 2: (2, 5)},
        proposals=proposals,
    )
    state = SelectionInput(
        grammar,
        (None,) * 3,
        proposals,
        support,
        CompositionalByteLevelAdapter(emissions),
        EOSPolicy(EOSMode.ABSENT),
    )
    frontier = budgeted_commit_frontier(state, 3)
    data = budget_proof_data(state, frontier)
    data["example_kind"] = "mathematical_example_not_accuracy_benchmark"
    data["description"] = "B=1 chooses abc for reward 7/8; B=2 chooses xyz for reward 1."
    return data


def verify(data):
    if "schema_version" in data:
        return verify_budget_proof(data)
    grammar = CnfGrammar.from_dict(data["grammar"])
    raw = data["graph"]
    graph = ResourceDAG(
        tuple(raw["nodes"]),
        raw["start"],
        tuple(raw["finals"]),
        tuple(ResourceArc(a, u, v, t, Fraction(*w), c) for a, u, v, t, w, c in raw["arcs"]),
        raw["support_description"],
    )
    raw_proof = data["certificate"]
    proof = BudgetCertificate(
        raw_proof["max_budget"],
        tuple((*r[:-1], Fraction(*r[-1])) for r in raw_proof["epsilon_bounds"]),
        tuple((*r[:-1], Fraction(*r[-1])) for r in raw_proof["grammar_bounds"]),
    )
    checked = []
    caps = [r["budget"] for r in data["frontier"]]
    if caps != list(range(proof.max_budget + 1)):
        raise ValueError("proof must contain the complete budget frontier")
    for row in data["frontier"]:
        value = row["objective_value"]
        result = BudgetPathResult(
            SolveStatus(row["status"]),
            row["budget"],
            None if value is None else Fraction(*value),
            None if row["witness_arc_ids"] is None else tuple(row["witness_arc_ids"]),
            None
            if row["witness_terminal_labels"] is None
            else tuple(row["witness_terminal_labels"]),
            row["consumed_budget"],
            proof,
            graph.support_description,
        )
        report = check_budget_certificate(grammar, graph, result)
        if not report.accepted:
            raise ValueError(f"Budget {result.budget}: {report.errors}")
        checked.append({"budget": result.budget, "objective": str(result.objective_value)})
    return {
        "verification": "PASS",
        "verification_scope": "historical_resource_graph_only",
        "scope": graph.support_description,
        "frontier": checked,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--output", type=Path, help="write a new JSON proof (refuses replacement)")
    group.add_argument("--verify", type=Path, help="check an existing resource-graph proof offline")
    parser.add_argument("--lean", action="store_true", help="also check v2 resource proof in Lean")
    parser.add_argument("--lake", default="lake", help="installed Lake executable")
    parser.add_argument("--lean-source", type=Path, help="export generated Lean certificate")
    args = parser.parse_args()
    if args.verify:
        data = json.loads(args.verify.read_text())
        report = verify(data)
    else:
        data = generate()
        verify(data)
        output = json.dumps(data, indent=2) + "\n"
        if args.output:
            with args.output.open("x") as file:
                file.write(output)
            report = verify(data)
        else:
            if not (args.lean or args.lean_source):
                print(output, end="")
                return
            report = verify(data)
    if args.lean_source or args.lean:
        from mwpc_exact.lean_bridge import export_lean_budget_proof, verify_with_lean

        if args.lean_source:
            args.lean_source.parent.mkdir(parents=True, exist_ok=True)
            with args.lean_source.open("x") as file:
                file.write(export_lean_budget_proof(data).source)
        if args.lean:
            report["lean"] = verify_with_lean(
                data,
                formal_directory=Path(__file__).resolve().parents[2] / "formal",
                lake=args.lake,
            )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
