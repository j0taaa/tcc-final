from __future__ import annotations

import pytest

from mwpc_exact import ExactnessScope, Proposal, SolveStatus, SupportKind
from mwpc_exact.reference.grammar import (
    BinaryProduction,
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)
from mwpc_exact.reference.token_aligned import solve_token_aligned


def pair_grammar() -> CnfGrammar:
    return CnfGrammar(
        nonterminals=(Nonterminal(0, "S"), Nonterminal(1, "A"), Nonterminal(2, "B")),
        terminals=(Terminal(10, "x"), Terminal(20, "y")),
        start_nonterminal_id=0,
        terminal_productions=(
            TerminalProduction(2, 1, 10),
            TerminalProduction(3, 2, 20),
        ),
        binary_productions=(BinaryProduction(1, 0, 1, 2),),
    )


EXPLICIT_SCOPE = ExactnessScope(
    kind=SupportKind.EXPLICIT,
    vocabulary_size=256,
    pruning_description="support-scope enforcement fixture",
)


def test_full_scope_rejects_incomplete_vocabulary_mapping() -> None:
    full_scope = ExactnessScope(kind=SupportKind.FULL, vocabulary_size=256)

    with pytest.raises(ValueError, match="cover every vocabulary token"):
        solve_token_aligned(
            grammar=pair_grammar(),
            canvas=(None, None),
            proposals=(),
            exactness_scope=full_scope,
            terminal_token_ids={10: 100, 20: 200},
        )


def test_full_scope_rejects_explicitly_pruned_rows() -> None:
    full_scope = ExactnessScope(kind=SupportKind.FULL, vocabulary_size=2)

    with pytest.raises(ValueError, match="per_position_support must be omitted"):
        solve_token_aligned(
            grammar=pair_grammar(),
            canvas=(None, None),
            proposals=(),
            exactness_scope=full_scope,
            terminal_token_ids={10: 0, 20: 1},
            per_position_support=((0,), (1,)),
        )


def test_valid_full_scope_covers_the_declared_vocabulary() -> None:
    full_scope = ExactnessScope(kind=SupportKind.FULL, vocabulary_size=2)
    result = solve_token_aligned(
        grammar=pair_grammar(),
        canvas=(None, None),
        proposals=(Proposal(1, 0, 0, 1), Proposal(2, 1, 1, 1)),
        exactness_scope=full_scope,
        terminal_token_ids={10: 0, 20: 1},
    )

    assert result.status is SolveStatus.OPTIMAL
    diagnostics = result.to_dict()["diagnostics"]
    assert isinstance(diagnostics, dict)
    assert diagnostics["support_kind"] == "full"
    assert diagnostics["represented_support_token_ids"] == [[0, 1], [0, 1]]
    assert diagnostics["represented_support_row_sizes"] == [2, 2]
    assert len(str(diagnostics["represented_support_sha256"])) == 64


def test_explicit_support_must_include_fixed_canvas_tokens() -> None:
    with pytest.raises(ValueError, match="fixed canvas token.*absent"):
        solve_token_aligned(
            grammar=pair_grammar(),
            canvas=(100, None),
            proposals=(),
            exactness_scope=EXPLICIT_SCOPE,
            terminal_token_ids={10: 100, 20: 200},
            per_position_support=((200,), (200,)),
        )


def test_explicit_support_rejects_unmapped_token_ids() -> None:
    with pytest.raises(ValueError, match="without a token-aligned terminal mapping"):
        solve_token_aligned(
            grammar=pair_grammar(),
            canvas=(None, None),
            proposals=(),
            exactness_scope=EXPLICIT_SCOPE,
            terminal_token_ids={10: 100, 20: 200},
            per_position_support=((100, 123), (200,)),
        )


def test_explicit_support_is_recorded_in_machine_readable_diagnostics() -> None:
    result = solve_token_aligned(
        grammar=pair_grammar(),
        canvas=(None, None),
        proposals=(Proposal(1, 0, 100, 2), Proposal(2, 1, 200, 3)),
        exactness_scope=EXPLICIT_SCOPE,
        terminal_token_ids={10: 100, 20: 200},
        per_position_support=((100,), (200,)),
    )

    assert result.status is SolveStatus.OPTIMAL
    diagnostics = result.to_dict()["diagnostics"]
    assert isinstance(diagnostics, dict)
    assert diagnostics["support_kind"] == "explicit"
    assert diagnostics["represented_support_token_ids"] == [[100], [200]]
    assert diagnostics["represented_support_row_sizes"] == [1, 1]
    assert len(str(diagnostics["represented_support_sha256"])) == 64
