"""Executable adversarial family, separate from prevalence measurements."""

from __future__ import annotations

import pytest

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
)
from mwpc_exact.evaluation.selection import select_exact_mwpc, select_greedy_exact_feasibility
from mwpc_exact.reference.grammar import Nonterminal, Terminal
from mwpc_exact.reference.normalization import (
    NonterminalRef as N,
)
from mwpc_exact.reference.normalization import (
    SourceGrammar,
    normalize_to_cnf,
)
from mwpc_exact.reference.normalization import (
    SourceProduction as P,
)
from mwpc_exact.reference.normalization import (
    TerminalRef as T,
)


@pytest.mark.integration
@pytest.mark.parametrize("length", (3, 4, 8, 16, 32))
@pytest.mark.parametrize("backend", (ExactBackend.PYTHON, ExactBackend.RUST))
def test_confidence_ordered_unit_greedy_has_no_constant_approximation(
    length: int,
    backend: ExactBackend,
) -> None:
    if backend is ExactBackend.RUST:
        pytest.importorskip("mwpc_parser_py")
    # Constant-size grammar: a b* | b a*. At length n there are exactly two words.
    grammar = normalize_to_cnf(
        SourceGrammar(
            (Nonterminal(0, "S"), Nonterminal(1, "A"), Nonterminal(2, "B")),
            (Terminal(0, ord("a")), Terminal(1, ord("b"))),
            0,
            (
                P(0, 0, (T(0), N(2))),
                P(1, 0, (T(1), N(1))),
                P(2, 1, (T(0), N(1))),
                P(3, 1, ()),
                P(4, 2, (T(1), N(2))),
                P(5, 2, ()),
            ),
        )
    ).grammar
    proposals = tuple(
        Proposal(i, i, 0, 1.0, model_confidence=0.75 if i == 0 else 0.5) for i in range(length)
    )
    support = build_per_position_support(
        canvas=(None,) * length,
        policy=SupportPolicy(kind=SupportKind.FULL, vocabulary_size=2),
        explicit_support={i: (0, 1) for i in range(length)},
        proposals=proposals,
    )
    state = SelectionInput(
        grammar,
        support.canvas,
        proposals,
        support,
        CompositionalByteLevelAdapter((b"a", b"b")),
        EOSPolicy(EOSMode.ABSENT),
    )
    greedy = select_greedy_exact_feasibility(state, backend=backend)
    exact = select_exact_mwpc(state, backend=backend)
    assert greedy.status is SelectionStatus.FEASIBLE_ON_SUPPORT
    assert exact.status is SelectionStatus.OPTIMAL
    assert greedy.score == 1.0
    assert greedy.selected_proposal_ids == (0,)
    assert exact.score == length - 1
    assert exact.witness_token_ids == (1,) + (0,) * (length - 1)
    assert exact.selected_proposal_ids == tuple(range(1, length))
