from __future__ import annotations

import json
from dataclasses import replace
from importlib import import_module
from math import isclose

import pytest

import mwpc_exact.solver as orchestrator
from mwpc_exact import (
    CompositionalByteLevelAdapter,
    EOSMode,
    EOSPolicy,
    ExactBackend,
    Proposal,
    ProposalWeightMode,
    SolveStatus,
    SupportKind,
    SupportPolicy,
    ValidationCode,
    ValidationIssue,
    ValidationReport,
    build_per_position_support,
    build_schedule_proposals,
    solve_exact_commit,
)
from mwpc_exact.reference.grammar import (
    BinaryProduction,
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)
from mwpc_exact.rust_solver import RustBindingUnavailable
from mwpc_exact.support import PerPositionSupport

ADAPTER = CompositionalByteLevelAdapter((b"a", b"b", None, None, None))
REQUIRED = EOSPolicy(
    EOSMode.REQUIRED,
    termination_token_ids=(2, 3),
    pad_token_id=2,
)
OPTIONAL = EOSPolicy(
    EOSMode.OPTIONAL,
    termination_token_ids=(2, 3),
    pad_token_id=2,
)
ABSENT_ADAPTER = CompositionalByteLevelAdapter((b"a", b"b"))


def exact_word_grammar(word: bytes) -> CnfGrammar:
    if not word:
        return CnfGrammar(
            nonterminals=(Nonterminal(0, "S"),),
            terminals=(),
            start_nonterminal_id=0,
            accepts_empty=True,
        )
    terminals = tuple(
        Terminal(symbol_id, label) for symbol_id, label in enumerate(sorted(set(word)))
    )
    terminal_id = {terminal.label: terminal.symbol_id for terminal in terminals}
    if len(word) == 1:
        return CnfGrammar(
            nonterminals=(Nonterminal(0, "S"),),
            terminals=terminals,
            start_nonterminal_id=0,
            terminal_productions=(TerminalProduction(0, 0, terminal_id[word[0]]),),
        )
    if len(word) != 2:
        raise ValueError("test helper supports words of at most two bytes")
    return CnfGrammar(
        nonterminals=(
            Nonterminal(0, "S"),
            Nonterminal(1, "LEFT"),
            Nonterminal(2, "RIGHT"),
        ),
        terminals=terminals,
        start_nonterminal_id=0,
        terminal_productions=(
            TerminalProduction(0, 1, terminal_id[word[0]]),
            TerminalProduction(1, 2, terminal_id[word[1]]),
        ),
        binary_productions=(BinaryProduction(2, 0, 1, 2),),
    )


def explicit_support(
    *,
    canvas: tuple[int | None, ...],
    rows: tuple[tuple[int, ...], ...],
    proposals: tuple[Proposal, ...] = (),
    include_specials: bool = True,
) -> PerPositionSupport:
    return build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(
            kind=SupportKind.EXPLICIT,
            vocabulary_size=ADAPTER.vocabulary_size,
            required_special_token_ids=((2, 3) if include_specials else ()),
            pruning_description="T801 offline explicit fixture",
        ),
        explicit_support=dict(enumerate(rows)),
        proposals=proposals,
    )


def offline_saved_logits_case() -> tuple[
    CnfGrammar,
    tuple[int | None, ...],
    PerPositionSupport,
    tuple[Proposal, ...],
]:
    canvas = (None, None, None)
    saved_logits = (
        (9.0, 1.0, 0.0, 0.0, -1.0),
        (1.0, 0.0, 0.0, 9.0, -1.0),
        (1.0, 0.0, 9.0, 0.0, -1.0),
    )
    proposal_batch = build_schedule_proposals(
        predicted_token_ids=(0, 3, 2),
        confidence_values=(0.9, 0.8, 0.7),
        schedule_mask=(True, True, True),
        k_s=3,
        weight_mode=ProposalWeightMode.CONFIDENCE,
    )
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(
            kind=SupportKind.TOP_K,
            vocabulary_size=ADAPTER.vocabulary_size,
            top_k=1,
            required_special_token_ids=(2, 3),
        ),
        logits=saved_logits,
        proposals=proposal_batch.proposals,
    )
    return exact_word_grammar(b"a"), canvas, support, proposal_batch.proposals


def solve_offline(backend: ExactBackend = ExactBackend.PYTHON, **kwargs: object):
    grammar, canvas, support, proposals = offline_saved_logits_case()
    return solve_exact_commit(
        grammar,
        canvas=canvas,
        support=support,
        proposals=proposals,
        tokenizer_adapter=ADAPTER,
        eos_policy=REQUIRED,
        backend=backend,
        **kwargs,  # type: ignore[arg-type]
    )


def rust_binding_available() -> bool:
    try:
        import_module("mwpc_parser_py")
    except ImportError:
        return False
    return True


requires_rust = pytest.mark.skipif(
    not rust_binding_available(),
    reason="build the production binding with `make bootstrap-rust-parser`",
)


def test_public_api_solves_saved_logits_offline_and_validates_full_slot_witness() -> None:
    result = solve_offline()

    assert result.status is SolveStatus.OPTIMAL
    assert result.exactness_scope.kind is SupportKind.TOP_K
    assert result.exactness_scope.top_k == 1
    assert result.objective_value == pytest.approx(2.4)
    assert result.selected_proposal_ids == (0, 1, 2)
    assert result.witness_token_ids == (0, 3, 2)
    assert result.witness_terminal_labels == (ord("a"),)
    assert result.witness_eos_position == 1
    assert result.witness_content_endpoint_slot == 1
    assert len(result.witness_token_ids) == 3
    assert result.diagnostics["exactness_name"] == "exact_on_support"
    assert result.diagnostics["certificate_source"] == "normalized_parser"
    assert result.diagnostics["represented_support_sha256"]
    assert result.diagnostics["certificate_validation"]["is_valid"] is True  # type: ignore[index]
    json.dumps(result.to_dict())


def test_explicit_support_and_fixed_position_need_no_model() -> None:
    canvas = (0, None, None)
    proposals = (
        Proposal(5, position=1, token_id=3, weight=4),
        Proposal(6, position=2, token_id=2, weight=3),
    )
    support = explicit_support(
        canvas=canvas,
        rows=((0,), (2, 3), (2, 3)),
        proposals=proposals,
    )

    result = solve_exact_commit(
        exact_word_grammar(b"a"),
        canvas=canvas,
        support=support,
        proposals=proposals,
        tokenizer_adapter=ADAPTER,
        eos_policy=REQUIRED,
        backend=ExactBackend.PYTHON,
    )

    assert result.status is SolveStatus.OPTIMAL
    assert result.witness_token_ids == (0, 3, 2)
    assert result.selected_proposal_ids == (5, 6)
    assert result.objective_value == 7.0


def test_optional_policy_can_choose_an_unterminated_full_slot_path() -> None:
    canvas = (None,)
    proposals = (
        Proposal(0, position=0, token_id=0, weight=5),
        Proposal(1, position=0, token_id=3, weight=2),
    )
    support = explicit_support(canvas=canvas, rows=((0, 3),), proposals=proposals)

    result = solve_exact_commit(
        exact_word_grammar(b"a"),
        canvas=canvas,
        support=support,
        proposals=proposals,
        tokenizer_adapter=ADAPTER,
        eos_policy=OPTIONAL,
        backend=ExactBackend.PYTHON,
    )

    assert result.status is SolveStatus.OPTIMAL
    assert result.witness_token_ids == (0,)
    assert result.witness_eos_position is None
    assert result.witness_content_endpoint_slot == 1
    assert result.objective_value == 5.0


def test_epsilon_only_optimum_reconstructs_eos_and_every_pad_slot() -> None:
    canvas = (None, None, None)
    proposals = (
        Proposal(10, position=0, token_id=3, weight=7),
        Proposal(11, position=1, token_id=2, weight=5),
        Proposal(12, position=2, token_id=2, weight=3),
    )
    support = explicit_support(
        canvas=canvas,
        rows=((2, 3), (2,), (2,)),
        proposals=proposals,
    )

    result = solve_exact_commit(
        exact_word_grammar(b""),
        canvas=canvas,
        support=support,
        proposals=proposals,
        tokenizer_adapter=ADAPTER,
        eos_policy=REQUIRED,
        backend=ExactBackend.PYTHON,
    )

    assert result.status is SolveStatus.OPTIMAL
    assert result.witness_token_ids == (3, 2, 2)
    assert result.witness_terminal_labels == ()
    assert result.witness_eos_position == result.witness_content_endpoint_slot == 0
    assert result.selected_proposal_ids == (10, 11, 12)
    assert result.objective_value == 15.0
    assert result.diagnostics["certificate_source"] == "epsilon_only"


def test_infeasible_on_support_remains_distinct() -> None:
    canvas = (None, None)
    support = explicit_support(canvas=canvas, rows=((0,), (2,)))

    result = solve_exact_commit(
        exact_word_grammar(b"b"),
        canvas=canvas,
        support=support,
        proposals=(),
        tokenizer_adapter=ADAPTER,
        eos_policy=REQUIRED,
        backend=ExactBackend.PYTHON,
    )

    assert result.status is SolveStatus.INFEASIBLE_ON_SUPPORT
    assert result.objective_value is None
    assert result.witness_token_ids == ()


def test_explicit_absent_policy_preserves_ordinary_byte_semantics() -> None:
    canvas = (None,)
    proposals = (Proposal(0, 0, 0, 1),)
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(
            kind=SupportKind.EXPLICIT,
            vocabulary_size=ABSENT_ADAPTER.vocabulary_size,
        ),
        explicit_support={0: (0, 1)},
        proposals=proposals,
    )

    result = solve_exact_commit(
        exact_word_grammar(b"a"),
        canvas=canvas,
        support=support,
        proposals=proposals,
        tokenizer_adapter=ABSENT_ADAPTER,
        eos_policy=EOSPolicy(EOSMode.ABSENT),
        backend=ExactBackend.PYTHON,
    )

    assert result.status is SolveStatus.OPTIMAL
    assert result.witness_token_ids == (0,)
    assert result.witness_eos_position is None
    assert result.witness_content_endpoint_slot == 1


def test_input_consistency_rejects_canvas_scope_and_adapter_mismatches() -> None:
    grammar, canvas, support, proposals = offline_saved_logits_case()
    with pytest.raises(ValueError, match="canvas must exactly match"):
        solve_exact_commit(
            grammar,
            canvas=(None,),
            support=support,
            proposals=proposals,
            tokenizer_adapter=ADAPTER,
            eos_policy=REQUIRED,
            backend=ExactBackend.PYTHON,
        )

    support_without_special_metadata = explicit_support(
        canvas=(None,),
        rows=((0, 2, 3),),
        include_specials=False,
    )
    with pytest.raises(ValueError, match="exactness-scope special tokens"):
        solve_exact_commit(
            exact_word_grammar(b"a"),
            canvas=(None,),
            support=support_without_special_metadata,
            proposals=(),
            tokenizer_adapter=ADAPTER,
            eos_policy=REQUIRED,
            backend=ExactBackend.PYTHON,
        )

    wrong_adapter = CompositionalByteLevelAdapter((b"a", b"b"))
    with pytest.raises(ValueError, match="equal vocabularies"):
        solve_exact_commit(
            grammar,
            canvas=canvas,
            support=support,
            proposals=proposals,
            tokenizer_adapter=wrong_adapter,
            eos_policy=REQUIRED,
            backend=ExactBackend.PYTHON,
        )


def test_non_byte_grammar_is_rejected_before_lattice_construction() -> None:
    grammar = CnfGrammar(
        nonterminals=(Nonterminal(0, "S"),),
        terminals=(Terminal(0, "a"),),
        start_nonterminal_id=0,
        terminal_productions=(TerminalProduction(0, 0, 0),),
    )
    _, canvas, support, proposals = offline_saved_logits_case()

    with pytest.raises(ValueError, match="integer byte grammar terminals"):
        solve_exact_commit(
            grammar,
            canvas=canvas,
            support=support,
            proposals=proposals,
            tokenizer_adapter=ADAPTER,
            eos_policy=REQUIRED,
            backend=ExactBackend.PYTHON,
        )


def test_corrupted_normalized_backend_certificate_becomes_error(monkeypatch) -> None:
    original = orchestrator._run_python_backend

    def corrupted(grammar: CnfGrammar, lattice):
        outcome = original(grammar, lattice)
        assert outcome.certificate is not None
        certificate = replace(
            outcome.certificate,
            witness_graph_edge_ids=outcome.certificate.witness_graph_edge_ids[:-1],
        )
        return replace(outcome, certificate=certificate)

    monkeypatch.setattr(orchestrator, "_run_python_backend", corrupted)

    result = solve_offline()

    assert result.status is SolveStatus.ERROR
    assert result.objective_value is None
    assert result.witness_token_ids == ()
    assert result.diagnostics["error_stage"] == "certificate_validation"


def test_independent_validator_rejection_becomes_error(monkeypatch) -> None:
    def rejected(*_args: object, **_kwargs: object) -> ValidationReport:
        return ValidationReport(
            issues=(
                ValidationIssue(
                    ValidationCode.SUPPORT_REJECTED,
                    "injected deterministic validator rejection",
                ),
            ),
            skipped_checks=(),
            recomputed_objective=0.0,
            recomputed_selected_proposal_ids=(),
        )

    monkeypatch.setattr(orchestrator, "validate_exact_commit_certificate", rejected)

    result = solve_offline()

    assert result.status is SolveStatus.ERROR
    assert result.objective_value is None
    assert result.selected_proposal_ids == ()
    assert result.diagnostics["error_stage"] == "certificate_validation"
    assert result.diagnostics["certificate_validation"]["is_valid"] is False  # type: ignore[index]


def test_backend_exception_becomes_payload_free_error(monkeypatch) -> None:
    def failed(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError("injected backend failure")

    monkeypatch.setattr(orchestrator, "_run_python_backend", failed)

    result = solve_offline()

    assert result.status is SolveStatus.ERROR
    assert result.objective_value is None
    assert result.witness_graph_edge_ids == ()
    assert result.diagnostics["error_stage"] == "backend_solve"


def test_missing_rust_binding_remains_unsupported(monkeypatch) -> None:
    def unavailable(*_args: object, **_kwargs: object) -> object:
        raise RustBindingUnavailable("injected unavailable binding")

    monkeypatch.setattr(orchestrator, "solve_rust_dag", unavailable)

    result = solve_offline(ExactBackend.RUST)

    assert result.status is SolveStatus.UNSUPPORTED
    assert result.objective_value is None
    assert result.diagnostics["error_stage"] == "backend_availability"


@requires_rust
def test_rust_and_python_orchestration_agree_on_eos_objective_and_certificate() -> None:
    python_result = solve_offline(ExactBackend.PYTHON)
    rust_result = solve_offline(ExactBackend.RUST)

    assert python_result.status is rust_result.status is SolveStatus.OPTIMAL
    assert isclose(
        python_result.objective_value or -1.0,
        rust_result.objective_value or -2.0,
        rel_tol=1e-12,
        abs_tol=1e-12,
    )
    assert rust_result.witness_token_ids == (0, 3, 2)
    assert rust_result.diagnostics["certificate_validation"]["is_valid"] is True  # type: ignore[index]


@requires_rust
def test_rust_timeout_is_not_converted_to_epsilon_optimal_or_infeasible() -> None:
    result = solve_offline(ExactBackend.RUST, deterministic_work_limit=0)

    assert result.status is SolveStatus.TIMEOUT
    assert result.objective_value is None
    assert result.witness_token_ids == ()
    assert result.witness_graph_edge_ids == ()
