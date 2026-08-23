from __future__ import annotations

from dataclasses import replace
from functools import partial

import pytest

from mwpc_exact import ExactnessScope, Proposal, SolveStatus, SupportKind
from mwpc_exact.reference.grammar import (
    BinaryProduction,
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)
from mwpc_exact.reference.lexical import build_lexical_rewards
from mwpc_exact.reference.recognizer import recognizes_cnf
from mwpc_exact.reference.token_aligned import (
    BinaryBackpointer,
    CertificateReconstructionError,
    ChartEntry,
    CkyChart,
    CkySolve,
    TerminalBackpointer,
    build_token_aligned_support_graph,
    reconstruct_cky_certificate,
    run_cky,
    solve_token_aligned,
)
from mwpc_exact.validator import validate_exact_commit_certificate


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


PROPOSALS = (Proposal(7, 0, 100, 2), Proposal(8, 1, 200, 3))
TOKEN_IDS = {10: 100, 20: 200}
SCOPE = ExactnessScope(
    kind=SupportKind.EXPLICIT,
    vocabulary_size=256,
    pruning_description="two token IDs in the canonical fixture",
)


def solved_chart() -> CkySolve:
    lexical = build_lexical_rewards(
        grammar=pair_grammar(),
        canvas=(None, None),
        proposals=PROPOSALS,
        terminal_token_ids=TOKEN_IDS,
    )
    return run_cky(pair_grammar(), lexical)


def test_reconstruction_recovers_tokens_all_positive_ids_and_objective() -> None:
    certificate = reconstruct_cky_certificate(solved_chart(), proposals=PROPOSALS)

    assert certificate.witness_token_ids == (100, 200)
    assert certificate.witness_terminal_labels == ("x", "y")
    assert certificate.selected_proposal_ids == (7, 8)
    assert certificate.objective_value == 5.0
    assert recognizes_cnf(pair_grammar(), certificate.witness_terminal_labels)


def test_corrupted_terminal_backpointer_is_detected() -> None:
    solve = solved_chart()
    entries = dict(solve.chart.entries)
    entries[(1, 0, 1)] = ChartEntry(2, TerminalBackpointer(999, 10))
    corrupted = CkySolve(
        SolveStatus.OPTIMAL,
        CkyChart(solve.chart.grammar, solve.chart.lexical_rewards, entries),
    )

    with pytest.raises(CertificateReconstructionError, match="unknown terminal production"):
        reconstruct_cky_certificate(corrupted, proposals=PROPOSALS)


def test_corrupted_binary_backpointer_is_detected() -> None:
    solve = solved_chart()
    root = solve.chart.root_entry
    assert root is not None
    pointer = root.backpointer
    assert isinstance(pointer, BinaryBackpointer)
    entries = dict(solve.chart.entries)
    entries[solve.chart.root_key] = replace(
        root,
        backpointer=replace(pointer, split=0),
    )
    corrupted = CkySolve(
        SolveStatus.OPTIMAL,
        CkyChart(solve.chart.grammar, solve.chart.lexical_rewards, entries),
    )

    with pytest.raises(CertificateReconstructionError, match="split is outside"):
        reconstruct_cky_certificate(corrupted, proposals=PROPOSALS)


def test_corrupted_chart_score_is_detected() -> None:
    solve = solved_chart()
    root = solve.chart.root_entry
    assert root is not None
    entries = dict(solve.chart.entries)
    entries[solve.chart.root_key] = replace(root, score=root.score + 1)
    corrupted = CkySolve(
        SolveStatus.OPTIMAL,
        CkyChart(solve.chart.grammar, solve.chart.lexical_rewards, entries),
    )

    with pytest.raises(CertificateReconstructionError, match="child-score sum"):
        reconstruct_cky_certificate(corrupted, proposals=PROPOSALS)


def test_public_result_passes_independent_validator() -> None:
    grammar = pair_grammar()
    result = solve_token_aligned(
        grammar=grammar,
        canvas=(None, None),
        proposals=PROPOSALS,
        exactness_scope=SCOPE,
        terminal_token_ids=TOKEN_IDS,
    )
    lexical = build_lexical_rewards(
        grammar=grammar,
        canvas=(None, None),
        proposals=PROPOSALS,
        terminal_token_ids=TOKEN_IDS,
    )
    graph = build_token_aligned_support_graph(grammar, lexical)

    report = validate_exact_commit_certificate(
        result,
        expected_scope=SCOPE,
        canvas=(None, None),
        proposals=PROPOSALS,
        graph=graph,
        grammar_recognizer=partial(recognizes_cnf, grammar),
        tokenizer_validator=lambda token_ids, labels: (
            token_ids == (100, 200) and labels == ("x", "y")
        ),
        eos_validator=lambda token_ids: len(token_ids) == 2,
    )

    assert result.status is SolveStatus.OPTIMAL
    assert result.objective_value == 5.0
    assert result.selected_proposal_ids == (7, 8)
    assert result.to_dict()["diagnostics"]["certificate_validation"] == {  # type: ignore[index]
        "is_valid": True,
        "issues": [],
        "skipped_checks": [],
        "recomputed_objective": 5.0,
        "recomputed_selected_proposal_ids": [7, 8],
    }
    assert report.is_valid


def test_public_infeasible_result_has_no_objective_or_certificate() -> None:
    result = solve_token_aligned(
        grammar=pair_grammar(),
        canvas=(50, None),
        proposals=(),
        exactness_scope=SCOPE,
        terminal_token_ids=TOKEN_IDS,
    )

    assert result.status is SolveStatus.INFEASIBLE_ON_SUPPORT
    assert result.objective_value is None
    assert result.witness_token_ids == ()


def test_zero_slot_empty_language_is_explicitly_unsupported_by_public_contract() -> None:
    grammar = CnfGrammar(
        nonterminals=(Nonterminal(0, "S"),),
        terminals=(),
        start_nonterminal_id=0,
        accepts_empty=True,
    )
    result = solve_token_aligned(
        grammar=grammar,
        canvas=(),
        proposals=(),
        exactness_scope=SCOPE,
    )

    assert result.status is SolveStatus.UNSUPPORTED
    assert "empty path certificate" in str(result.diagnostics["reason"])
