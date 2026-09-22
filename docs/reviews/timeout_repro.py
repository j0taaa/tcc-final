"""Read-only reproduction for the 2026-09-22 parser deadline review.

Run from the repository root with its built Rust binding:
    .venv/bin/python docs/reviews/timeout_repro.py

The observed elapsed times depend on the host. This is a diagnostic, not a
stable timing regression test or a benchmark result.
"""

import json

from mwpc_exact import TerminalEdge, WeightedTerminalDAG
from mwpc_exact.reference.grammar import (
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)
from mwpc_exact.rust_solver import solve_rust_dag


def main() -> None:
    grammar = CnfGrammar(
        nonterminals=(Nonterminal(0, "S"),),
        terminals=(Terminal(0, 98),),
        start_nonterminal_id=0,
        terminal_productions=(TerminalProduction(0, 0, 0),),
    )
    graphs = {
        "connected_chain": WeightedTerminalDAG(
            tuple(range(1001)),
            0,
            (1000,),
            tuple(TerminalEdge(i, i, i + 1, 97, 0.0) for i in range(1000)),
        ),
        "empty_chart_large_node_set": WeightedTerminalDAG(
            tuple(range(5000)), 0, (4999,), ()
        ),
    }
    for name, graph in graphs.items():
        for interval in (1024, 1):
            result = solve_rust_dag(
                grammar,
                graph,
                timeout_seconds=0.001,
                deadline_check_interval=interval,
            )
            print(
                json.dumps(
                    {
                        "case": name,
                        "timeout_seconds": 0.001,
                        "deadline_check_interval": interval,
                        "status": result.status.value,
                        "diagnostics": dict(result.diagnostics),
                    },
                    sort_keys=True,
                )
            )


if __name__ == "__main__":
    main()
