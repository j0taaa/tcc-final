"""Reproduce the final-deadline gap found in the 2026-09-28 review.

Run with the repository environment and compiled Rust binding:
    .venv/bin/python docs/reviews/repro_greedy_total_deadline.py

The clock is injected; no real two-second benchmark or sleep is involved.
Exit 1 means at least one backend returned a conclusive result after the
configured total deadline. This is review evidence, not a production change.
"""

from mwpc_exact import (
    CompositionalByteLevelAdapter,
    EOSMode,
    EOSPolicy,
    ExactBackend,
    Proposal,
    SelectionInput,
    SelectionStatus,
    SupportKind,
    SupportPolicy,
    build_per_position_support,
    select_greedy_exact_feasibility,
)
from mwpc_exact.reference.grammar import (
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)


def main() -> int:
    canvas = (None,)
    grammar = CnfGrammar(
        nonterminals=(Nonterminal(0, "S"),),
        terminals=(Terminal(0, ord("a")),),
        start_nonterminal_id=0,
        terminal_productions=(TerminalProduction(0, 0, 0),),
    )
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(kind=SupportKind.FULL, vocabulary_size=1),
        logits=((0.0,),),
    )
    state = SelectionInput(
        grammar=grammar,
        canvas=canvas,
        proposals=(Proposal(0, 0, 0, 1.0),),
        support=support,
        tokenizer_adapter=CompositionalByteLevelAdapter((b"a",)),
        eos_policy=EOSPolicy(EOSMode.ABSENT),
    )
    violations = 0
    for backend in (ExactBackend.PYTHON, ExactBackend.RUST):
        # Start, before query, after query, before reuse, final return.
        times = iter((0.0, 0.0, 0.2, 0.3, 2.0))
        result = select_greedy_exact_feasibility(
            state,
            backend=backend,
            total_timeout_seconds=1.0,
            reuse_witness=True,
            clock=lambda: next(times, 2.0),
        )
        print(
            f"backend={backend.value} status={result.status.value} "
            f"runtime_seconds={result.runtime_seconds} "
            f"score={result.score} witness={result.witness_token_ids}"
        )
        violations += result.status is not SelectionStatus.TIMEOUT
    return int(violations > 0)


if __name__ == "__main__":
    raise SystemExit(main())
