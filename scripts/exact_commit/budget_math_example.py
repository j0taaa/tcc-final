"""Emit or independently verify a finite mathematical example, not a benchmark.

The verification mode imports the proof checker without importing the optimizer.
Input grammar, original resource graph and exact rational potentials are supplied
in the JSON proof. No model, tokenizer download, GPU or network is needed.
"""

from __future__ import annotations

import argparse
import json
from fractions import Fraction
from pathlib import Path

from mwpc_exact.reference.budget_certificate import check_budget_certificate
from mwpc_exact.reference.budget_types import (
    BudgetCertificate,
    BudgetPathResult,
    ResourceArc,
    ResourceDAG,
)
from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.types import SolveStatus


def fraction_json(value):
    return None if value is None else [value.numerator, value.denominator]


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
    from mwpc_exact.evaluation.selection import SelectionInput
    from mwpc_exact.reference.grammar import Nonterminal, Terminal
    from mwpc_exact.reference.normalization import (
        SourceGrammar,
        SourceProduction,
        TerminalRef,
        normalize_to_cnf,
    )

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
    graph = frontier[0].proof_graph
    proof = frontier[0].path_result.certificate
    data = {
        "kind": "mathematical_example_not_accuracy_benchmark",
        "description": "B=1 chooses abc for reward 7/8; B=2 chooses xyz for reward 1.",
        "grammar": grammar.to_dict(),
        "graph": {
            "nodes": graph.nodes,
            "start": graph.start,
            "finals": graph.finals,
            "support_description": graph.support_description,
            "arcs": [
                [a.arc_id, a.source, a.target, a.label, fraction_json(a.reward), a.cost]
                for a in graph.arcs
            ],
        },
        "certificate": {
            "max_budget": proof.max_budget,
            "epsilon_bounds": [[*r[:-1], fraction_json(r[-1])] for r in proof.epsilon_bounds],
            "grammar_bounds": [[*r[:-1], fraction_json(r[-1])] for r in proof.grammar_bounds],
        },
        "frontier": [
            {
                "budget": r.budget,
                "status": r.status.value,
                "objective_value": fraction_json(r.objective_value),
                "witness_arc_ids": r.path_result.witness_arc_ids,
                "witness_terminal_labels": r.path_result.witness_terminal_labels,
                "consumed_budget": r.path_result.consumed_budget,
                "committed_positions": r.committed_positions,
                "committed_proposal_ids": r.committed_proposal_ids,
                "matched_proposal_ids": r.matched_proposal_ids,
                "witness_token_ids": r.witness_token_ids,
            }
            for r in frontier
        ],
    }
    return data


def verify(data):
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
    return {"verification": "PASS", "scope": graph.support_description, "frontier": checked}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--output", type=Path, help="write a new JSON proof (refuses replacement)")
    group.add_argument("--verify", type=Path, help="check an existing resource-graph proof offline")
    args = parser.parse_args()
    if args.verify:
        data = json.loads(args.verify.read_text())
        print(json.dumps(verify(data), indent=2))
    else:
        data = generate()
        verify(data)
        output = json.dumps(data, indent=2) + "\n"
        if args.output:
            with args.output.open("x") as file:
                file.write(output)
            print(json.dumps(verify(data), indent=2))
        else:
            print(output, end="")


if __name__ == "__main__":
    main()
