from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, replace
from importlib import import_module
from math import isclose

import pytest

import mwpc_exact.finite_solver as finite_solver
from mwpc_exact import (
    CompositionalByteLevelAdapter,
    ExactBackend,
    Proposal,
    SolveStatus,
    SupportKind,
    SupportPolicy,
    build_byte_lattice,
    build_per_position_support,
    build_token_lattice,
    solve_exact_commit,
)
from mwpc_exact.reference.byte_grammars import arithmetic_expression_bytes_v1
from mwpc_exact.reference.grammar import (
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)
from mwpc_exact.reference.recognizer import recognizes_cnf
from mwpc_exact.rust_solver import RustBindingUnavailable
from mwpc_exact.support import PerPositionSupport


def _rust_binding_available() -> bool:
    try:
        import_module("mwpc_parser_py")
    except ImportError:
        return False
    return True


RUST_BINDING_AVAILABLE = _rust_binding_available()
requires_rust_binding = pytest.mark.skipif(
    not RUST_BINDING_AVAILABLE,
    reason="build the production binding with `make bootstrap-rust-parser`",
)


@dataclass(frozen=True, slots=True)
class FiniteCase:
    canvas: tuple[int | None, ...]
    rows: tuple[tuple[int, ...], ...]
    emissions: tuple[bytes | None, ...]
    proposals: tuple[Proposal, ...]

    @property
    def adapter(self) -> CompositionalByteLevelAdapter:
        return CompositionalByteLevelAdapter(self.emissions)

    @property
    def support(self) -> PerPositionSupport:
        return build_per_position_support(
            canvas=self.canvas,
            policy=SupportPolicy(
                kind=SupportKind.EXPLICIT,
                vocabulary_size=len(self.emissions),
            ),
            explicit_support=dict(enumerate(self.rows)),
            proposals=self.proposals,
        )


VARIABLE_LENGTH_CASE = FiniteCase(
    canvas=(None, None),
    rows=((0, 3), (1, 4)),
    emissions=(b"1", b"2", b"+", b"1+", b"3", b"x"),
    proposals=(
        Proposal(0, 0, 0, 5),
        Proposal(1, 0, 3, 2),
        Proposal(2, 1, 1, 1),
        Proposal(3, 1, 4, 8),
    ),
)
SAME_BYTES_CASE = FiniteCase(
    canvas=(None,),
    rows=((0, 1),),
    emissions=(b"7", b"7"),
    proposals=(
        Proposal(9, 0, 0, 1),
        Proposal(7, 0, 1, 4),
        Proposal(8, 0, 1, 6),
    ),
)
FIXED_SLOT_CASE = FiniteCase(
    canvas=(0, None, 3),
    rows=((0,), (1, 2), (3,)),
    emissions=(b"(", b"1", b"+2", b")"),
    proposals=(
        Proposal(10, 1, 1, 1),
        Proposal(11, 1, 2, 100),
    ),
)
FINITE_CASES = (VARIABLE_LENGTH_CASE, SAME_BYTES_CASE, FIXED_SLOT_CASE)
FINITE_CASE_IDS = (
    "variable-byte-lengths",
    "same-bytes-distinct-token-provenance",
    "fixed-slots-reject-higher-invalid-choice",
)


def _enumerated_optima(case: FiniteCase) -> tuple[float, set[tuple[int, ...]]]:
    grammar = arithmetic_expression_bytes_v1()
    token_lattice = build_token_lattice(support=case.support, proposals=case.proposals)
    byte_lattice = build_byte_lattice(token_lattice=token_lattice, adapter=case.adapter)
    valid_paths = tuple(
        path for path in byte_lattice.iter_paths() if recognizes_cnf(grammar, path.terminal_labels)
    )
    assert valid_paths
    best_objective = max(path.objective_value for path in valid_paths)
    return best_objective, {
        path.token_path.token_ids
        for path in valid_paths
        if isclose(path.objective_value, best_objective, rel_tol=1e-12, abs_tol=1e-12)
    }


def _solve(case: FiniteCase, backend: ExactBackend, **kwargs: object):
    return solve_exact_commit(
        arithmetic_expression_bytes_v1(),
        canvas=case.canvas,
        support=case.support,
        proposals=case.proposals,
        tokenizer_adapter=case.adapter,
        backend=backend,
        **kwargs,  # type: ignore[arg-type]
    )


@pytest.mark.parametrize("case", FINITE_CASES, ids=FINITE_CASE_IDS)
def test_python_backend_matches_independent_token_path_enumeration(case: FiniteCase) -> None:
    expected_objective, optimal_token_paths = _enumerated_optima(case)

    result = _solve(case, ExactBackend.PYTHON)

    assert result.status is SolveStatus.OPTIMAL
    assert result.objective_value == expected_objective
    assert result.witness_token_ids in optimal_token_paths
    assert result.witness_eos_position is None
    assert result.witness_content_endpoint_slot == len(case.canvas)
    assert result.exactness_scope == case.support.exactness_scope
    validation = result.diagnostics["certificate_validation"]
    assert isinstance(validation, Mapping)
    assert validation["is_valid"] is True
    json.dumps(result.to_dict())


@requires_rust_binding
@pytest.mark.parametrize("case", FINITE_CASES, ids=FINITE_CASE_IDS)
def test_rust_and_python_backends_match_enumerated_scores(case: FiniteCase) -> None:
    expected_objective, optimal_token_paths = _enumerated_optima(case)

    python_result = _solve(case, ExactBackend.PYTHON)
    rust_result = _solve(case, ExactBackend.RUST)

    assert python_result.status is rust_result.status is SolveStatus.OPTIMAL
    assert python_result.objective_value == rust_result.objective_value == expected_objective
    assert rust_result.witness_token_ids in optimal_token_paths
    assert rust_result.diagnostics["backend"] == "rust"


@pytest.mark.parametrize("backend", [ExactBackend.PYTHON, ExactBackend.RUST])
def test_same_bytes_keep_exact_selected_token_and_all_matching_proposals(
    backend: ExactBackend,
) -> None:
    if backend is ExactBackend.RUST and not RUST_BINDING_AVAILABLE:
        pytest.skip("Rust binding is not built")
    result = _solve(SAME_BYTES_CASE, backend)

    assert result.status is SolveStatus.OPTIMAL
    assert result.witness_token_ids == (1,)
    assert result.selected_proposal_ids == (7, 8)
    assert result.objective_value == 10.0


@pytest.mark.parametrize("backend", [ExactBackend.PYTHON, ExactBackend.RUST])
def test_infeasible_on_support_is_not_reported_as_timeout(backend: ExactBackend) -> None:
    if backend is ExactBackend.RUST and not RUST_BINDING_AVAILABLE:
        pytest.skip("Rust binding is not built")
    case = FiniteCase(
        canvas=(None,),
        rows=((0,),),
        emissions=(b"x",),
        proposals=(Proposal(0, 0, 0, 9),),
    )

    result = _solve(case, backend)

    assert result.status is SolveStatus.INFEASIBLE_ON_SUPPORT
    assert result.objective_value is None
    assert result.witness_token_ids == ()
    assert result.witness_graph_edge_ids == ()


@requires_rust_binding
def test_rust_timeout_remains_distinct_and_has_no_partial_certificate() -> None:
    case = FiniteCase(
        canvas=(None,),
        rows=((0,),),
        emissions=(b"7",),
        proposals=(Proposal(0, 0, 0, 1),),
    )

    result = _solve(case, ExactBackend.RUST, deterministic_work_limit=0)

    assert result.status is SolveStatus.TIMEOUT
    assert result.objective_value is None
    assert result.selected_proposal_ids == ()
    assert result.witness_token_ids == ()
    assert result.witness_terminal_labels == ()
    assert result.witness_graph_edge_ids == ()


def test_missing_rust_binding_returns_unsupported_without_partial_data(monkeypatch) -> None:
    def unavailable(*_args: object, **_kwargs: object) -> object:
        raise RustBindingUnavailable("injected missing binding")

    monkeypatch.setattr(finite_solver, "solve_rust_dag", unavailable)

    result = _solve(VARIABLE_LENGTH_CASE, ExactBackend.RUST)

    assert result.status is SolveStatus.UNSUPPORTED
    assert result.objective_value is None
    assert result.witness_token_ids == ()
    assert result.diagnostics["error_stage"] == "backend_availability"


def test_corrupted_backend_certificate_becomes_error_not_optimal(monkeypatch) -> None:
    original_backend = finite_solver._run_python_backend

    def corrupted(grammar: CnfGrammar, byte_lattice):
        outcome = original_backend(grammar, byte_lattice)
        assert outcome.certificate is not None
        certificate = replace(
            outcome.certificate,
            witness_graph_edge_ids=outcome.certificate.witness_graph_edge_ids[:-1],
            witness_terminal_labels=outcome.certificate.witness_terminal_labels[:-1],
        )
        return replace(outcome, certificate=certificate)

    monkeypatch.setattr(finite_solver, "_run_python_backend", corrupted)

    result = _solve(VARIABLE_LENGTH_CASE, ExactBackend.PYTHON)

    assert result.status is SolveStatus.ERROR
    assert result.objective_value is None
    assert result.witness_token_ids == ()
    assert result.diagnostics["error_stage"] == "certificate_validation"


def test_solver_rejects_canvas_support_mismatch_and_non_byte_grammar() -> None:
    with pytest.raises(ValueError, match="exactly match"):
        solve_exact_commit(
            arithmetic_expression_bytes_v1(),
            canvas=(None,),
            support=VARIABLE_LENGTH_CASE.support,
            proposals=VARIABLE_LENGTH_CASE.proposals,
            tokenizer_adapter=VARIABLE_LENGTH_CASE.adapter,
            backend=ExactBackend.PYTHON,
        )

    string_grammar = CnfGrammar(
        nonterminals=(Nonterminal(0, "S"),),
        terminals=(Terminal(1, "x"),),
        start_nonterminal_id=0,
        terminal_productions=(TerminalProduction(2, 0, 1),),
    )
    with pytest.raises(ValueError, match="integer byte grammar terminals"):
        solve_exact_commit(
            string_grammar,
            canvas=VARIABLE_LENGTH_CASE.canvas,
            support=VARIABLE_LENGTH_CASE.support,
            proposals=VARIABLE_LENGTH_CASE.proposals,
            tokenizer_adapter=VARIABLE_LENGTH_CASE.adapter,
            backend=ExactBackend.PYTHON,
        )


def test_python_backend_rejects_rust_only_timeout_controls() -> None:
    with pytest.raises(ValueError, match="unsupported by the Python backend"):
        _solve(VARIABLE_LENGTH_CASE, ExactBackend.PYTHON, deterministic_work_limit=0)


def test_top_k_result_preserves_pruned_exactness_scope() -> None:
    proposals = (
        Proposal(0, 0, 0, 1),
        Proposal(1, 0, 1, 100),
    )
    support = build_per_position_support(
        canvas=(None,),
        policy=SupportPolicy(
            kind=SupportKind.TOP_K,
            vocabulary_size=2,
            top_k=1,
        ),
        logits=((10.0, 0.0),),
        proposals=proposals,
    )

    result = solve_exact_commit(
        arithmetic_expression_bytes_v1(),
        canvas=(None,),
        support=support,
        proposals=proposals,
        tokenizer_adapter=CompositionalByteLevelAdapter((b"7", b"8")),
        backend=ExactBackend.PYTHON,
    )

    assert result.status is SolveStatus.OPTIMAL
    assert result.exactness_scope.kind is SupportKind.TOP_K
    assert result.exactness_scope.top_k == 1
    assert result.objective_value == 1.0
    assert result.selected_proposal_ids == (0,)
    assert result.witness_token_ids == (0,)
