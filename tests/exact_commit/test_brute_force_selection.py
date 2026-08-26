from __future__ import annotations

import json

import pytest

import mwpc_exact.evaluation.brute_force as brute_module
from mwpc_exact import (
    CompositionalByteLevelAdapter,
    EOSMode,
    EOSPolicy,
    ExactBackend,
    ExactnessScope,
    Proposal,
    SelectionInput,
    SelectionResult,
    SelectionStatus,
    SelectorKind,
    SupportKind,
    SupportPolicy,
    TerminalEdge,
    WeightedTerminalDAG,
    build_per_position_support,
    select_brute_force,
    select_brute_force_graph,
    select_exact_mwpc,
)
from mwpc_exact.reference.dag_parser import reconstruct_dag_certificate, run_dag_cky
from mwpc_exact.reference.grammar import (
    BinaryProduction,
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)
from mwpc_exact.reference.random_instances import generate_random_instance


def same_pair_grammar() -> CnfGrammar:
    return CnfGrammar(
        nonterminals=(
            Nonterminal(0, "S"),
            Nonterminal(1, "A"),
            Nonterminal(2, "B"),
        ),
        terminals=(Terminal(0, ord("a")), Terminal(1, ord("b"))),
        start_nonterminal_id=0,
        terminal_productions=(
            TerminalProduction(0, 1, 0),
            TerminalProduction(1, 2, 1),
        ),
        binary_productions=(
            BinaryProduction(2, 0, 1, 1),
            BinaryProduction(3, 0, 2, 2),
        ),
    )


def nonempty_xy_grammar() -> CnfGrammar:
    return CnfGrammar(
        nonterminals=(Nonterminal(0, "S"),),
        terminals=(Terminal(0, "x"), Terminal(1, "y")),
        start_nonterminal_id=0,
        terminal_productions=(
            TerminalProduction(0, 0, 0),
            TerminalProduction(1, 0, 1),
        ),
        binary_productions=(BinaryProduction(2, 0, 0, 0),),
    )


def common_input(
    proposals: tuple[Proposal, ...],
    *,
    rows: tuple[tuple[int, ...], ...] = ((0, 1), (0, 1)),
    adapter: CompositionalByteLevelAdapter | None = None,
) -> SelectionInput:
    tokenizer = adapter or CompositionalByteLevelAdapter((b"a", b"b"))
    canvas = (None, None)
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(
            kind=SupportKind.EXPLICIT,
            vocabulary_size=tokenizer.vocabulary_size,
            pruning_description="T1002 guarded common brute-force fixture",
        ),
        explicit_support=dict(enumerate(rows)),
        proposals=proposals,
    )
    return SelectionInput(
        grammar=same_pair_grammar(),
        canvas=canvas,
        proposals=proposals,
        support=support,
        tokenizer_adapter=tokenizer,
        eos_policy=EOSPolicy(EOSMode.ABSENT),
    )


def graph_scope() -> ExactnessScope:
    return ExactnessScope(
        kind=SupportKind.EXPLICIT,
        vocabulary_size=2,
        pruning_description="T1002 complete tiny terminal graph",
    )


def test_common_exact_and_completion_oracle_match_on_the_same_input() -> None:
    selection_input = common_input(
        (
            Proposal(0, position=0, token_id=0, weight=1.0),
            Proposal(1, position=1, token_id=1, weight=10.0),
        )
    )

    brute_force = select_brute_force(selection_input, max_completions=4)
    exact = select_exact_mwpc(selection_input, backend=ExactBackend.PYTHON)

    assert brute_force.selector is SelectorKind.BRUTE_FORCE
    assert brute_force.status is SelectionStatus.OPTIMAL
    assert brute_force.status is exact.status
    assert brute_force.score == exact.score == 10.0
    assert brute_force.selected_proposal_ids == exact.selected_proposal_ids == (1,)
    assert brute_force.witness_token_ids == (1, 1)
    assert brute_force.witness_graph_edge_ids
    assert brute_force.token_witness_available
    assert brute_force.graph_witness_available
    assert brute_force.diagnostics["certificate_independently_validated"] is True
    assert brute_force.diagnostics["enumerated_completions"] == 4
    assert brute_force.exactness_scope is selection_input.support.exactness_scope
    json.dumps(brute_force.to_dict())


def test_common_exact_and_brute_force_agree_on_32_recorded_tiny_seeds() -> None:
    for seed in range(32):
        instance = generate_random_instance(seed)
        grammar = CnfGrammar(
            nonterminals=instance.grammar.nonterminals,
            terminals=tuple(
                Terminal(
                    terminal.symbol_id,
                    instance.terminal_token_ids[terminal.symbol_id],
                )
                for terminal in instance.grammar.terminals
            ),
            start_nonterminal_id=instance.grammar.start_nonterminal_id,
            terminal_productions=instance.grammar.terminal_productions,
            binary_productions=instance.grammar.binary_productions,
        )
        adapter = CompositionalByteLevelAdapter(
            tuple(bytes((token_id,)) for token_id in range(instance.vocabulary_size))
        )
        rows = tuple(
            row if fixed_token is None else (fixed_token,)
            for row, fixed_token in zip(
                instance.per_position_support,
                instance.canvas,
                strict=True,
            )
        )
        proposals = tuple(
            proposal
            for proposal in instance.proposals
            if instance.canvas[proposal.position] is None
            or instance.canvas[proposal.position] == proposal.token_id
        )
        support = build_per_position_support(
            canvas=instance.canvas,
            policy=SupportPolicy(
                kind=SupportKind.EXPLICIT,
                vocabulary_size=instance.vocabulary_size,
                pruning_description=f"T1002 recorded seed {seed}",
            ),
            explicit_support=dict(enumerate(rows)),
            proposals=proposals,
        )
        selection_input = SelectionInput(
            grammar=grammar,
            canvas=instance.canvas,
            proposals=proposals,
            support=support,
            tokenizer_adapter=adapter,
            eos_policy=EOSPolicy(EOSMode.ABSENT),
        )

        brute_force = select_brute_force(selection_input, max_completions=27)
        exact = select_exact_mwpc(selection_input, backend=ExactBackend.PYTHON)

        assert brute_force.status is exact.status, f"status mismatch at seed={seed}"
        assert brute_force.score == exact.score, f"objective mismatch at seed={seed}"
        if brute_force.status is SelectionStatus.OPTIMAL:
            assert set(brute_force.selected_proposal_ids) == set(exact.selected_proposal_ids), (
                f"selected proposal mismatch at seed={seed}"
            )
            assert brute_force.diagnostics["certificate_independently_validated"] is True


def test_completion_certificate_allows_input_order_to_differ_from_graph_path_order() -> None:
    selection_input = common_input(
        (
            Proposal(0, position=0, token_id=0, weight=7.0),
            Proposal(2, position=1, token_id=0, weight=4.0),
            Proposal(3, position=0, token_id=0, weight=9.0),
        )
    )

    result = select_brute_force(selection_input)

    assert result.status is SelectionStatus.OPTIMAL
    assert result.selected_proposal_ids == (0, 2, 3)
    assert result.score == 20.0
    assert result.witness_token_ids == (0, 0)
    assert result.diagnostics["certificate_independently_validated"] is True


def test_completion_oracle_common_result_preserves_infeasible_status() -> None:
    selection_input = common_input((), rows=((0,), (1,)))

    brute_force = select_brute_force(selection_input)
    exact = select_exact_mwpc(selection_input, backend=ExactBackend.PYTHON)

    assert brute_force.status is SelectionStatus.INFEASIBLE_ON_SUPPORT
    assert brute_force.status is exact.status
    assert brute_force.score is None
    assert not brute_force.witness_available
    assert brute_force.diagnostics["grammar_valid_completions"] == 0


def test_completion_limit_is_a_status_and_prevents_enumeration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selection_input = common_input(())

    def must_not_enumerate(**_kwargs: object) -> object:
        pytest.fail("completion oracle ran beyond the preflight size guard")

    monkeypatch.setattr(brute_module, "exhaustive_completion_oracle", must_not_enumerate)
    result = select_brute_force(selection_input, max_completions=3)

    assert result.status is SelectionStatus.SIZE_LIMIT_EXCEEDED
    assert result.score is None
    assert not result.witness_available
    assert result.diagnostics["search_space_size"] == 4
    assert result.diagnostics["maximum_completions"] == 3
    assert result.diagnostics["enumeration_started"] is False


def test_completion_adapter_rejects_non_token_aligned_emissions_honestly() -> None:
    selection_input = common_input(
        (),
        adapter=CompositionalByteLevelAdapter((b"aa", b"b")),
    )

    result = select_brute_force(selection_input)

    assert result.status is SelectionStatus.UNSUPPORTED
    assert result.score is None
    assert "one unique grammar terminal" in result.diagnostics["unsupported_reason"]


def test_graph_path_oracle_returns_a_common_graph_witness_and_matches_parser() -> None:
    grammar = nonempty_xy_grammar()
    graph = WeightedTerminalDAG(
        node_ids=(0, 1, 2),
        start_node_id=0,
        final_node_ids=(2,),
        edges=(
            TerminalEdge(0, 0, 1, "x", 4.0, matched_proposal_ids=(10,)),
            TerminalEdge(1, 1, 2, "y", 7.0, matched_proposal_ids=(11,)),
            TerminalEdge(2, 0, 2, "x", 8.0, matched_proposal_ids=(12,)),
        ),
    )

    brute_force = select_brute_force_graph(
        grammar,
        graph,
        exactness_scope=graph_scope(),
        max_paths=2,
    )
    parser_certificate = reconstruct_dag_certificate(run_dag_cky(grammar, graph))

    assert brute_force.status is SelectionStatus.OPTIMAL
    assert brute_force.score == parser_certificate.objective_value == 11.0
    assert brute_force.selected_proposal_ids == (10, 11)
    assert brute_force.witness_graph_edge_ids == (0, 1)
    assert brute_force.witness_terminal_labels == ("x", "y")
    assert brute_force.witness_available
    assert not brute_force.token_witness_available
    assert brute_force.graph_witness_available
    assert brute_force.diagnostics["completed_path_count"] == 2
    assert brute_force.diagnostics["certificate_independently_validated"] is True
    serialized = brute_force.to_dict()
    assert serialized["token_witness_available"] is False
    assert serialized["graph_witness_available"] is True


def test_graph_path_limit_prevents_oracle_enumeration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph = WeightedTerminalDAG(
        node_ids=(0, 1, 2),
        start_node_id=0,
        final_node_ids=(2,),
        edges=tuple(
            [TerminalEdge(edge_id, 0, 1, "x") for edge_id in range(4)]
            + [TerminalEdge(edge_id, 1, 2, "y") for edge_id in range(4, 8)]
        ),
    )

    def must_not_enumerate(*_args: object, **_kwargs: object) -> object:
        pytest.fail("graph oracle ran beyond the preflight size guard")

    monkeypatch.setattr(brute_module, "enumerate_best_cfg_path", must_not_enumerate)
    result = select_brute_force_graph(
        nonempty_xy_grammar(),
        graph,
        exactness_scope=graph_scope(),
        max_paths=15,
    )

    assert result.status is SelectionStatus.SIZE_LIMIT_EXCEEDED
    assert result.diagnostics["completed_path_count"] == 16
    assert result.diagnostics["maximum_paths"] == 15
    assert result.diagnostics["enumeration_started"] is False


def test_graph_path_oracle_preserves_infeasible_status() -> None:
    graph = WeightedTerminalDAG(
        node_ids=(0, 1),
        start_node_id=0,
        final_node_ids=(1,),
        edges=(TerminalEdge(0, 0, 1, "z", 9.0),),
    )

    result = select_brute_force_graph(
        nonempty_xy_grammar(),
        graph,
        exactness_scope=graph_scope(),
    )

    assert result.status is SelectionStatus.INFEASIBLE_ON_SUPPORT
    assert result.score is None
    assert not result.witness_available
    assert result.diagnostics["enumerated_paths"] == 1


def test_graph_only_optimum_cannot_weaken_the_exact_selector_contract() -> None:
    with pytest.raises(ValueError, match=r"non-oracle OPTIMAL.*token sequence"):
        SelectionResult(
            selector=SelectorKind.EXACT,
            status=SelectionStatus.OPTIMAL,
            exactness_scope=graph_scope(),
            runtime_seconds=0.0,
            score=1.0,
            witness_terminal_labels=("x",),
            witness_graph_edge_ids=(0,),
        )


@pytest.mark.parametrize(("field", "value"), [("max_completions", 0), ("max_paths", True)])
def test_brute_force_guards_require_positive_integer_limits(field: str, value: object) -> None:
    if field == "max_completions":
        with pytest.raises(ValueError, match="max_completions must be positive"):
            select_brute_force(common_input(()), max_completions=value)  # type: ignore[arg-type]
    else:
        graph = WeightedTerminalDAG(
            node_ids=(0, 1),
            start_node_id=0,
            final_node_ids=(1,),
            edges=(TerminalEdge(0, 0, 1, "x"),),
        )
        with pytest.raises(TypeError, match="max_paths must be an integer"):
            select_brute_force_graph(
                nonempty_xy_grammar(),
                graph,
                exactness_scope=graph_scope(),
                max_paths=value,  # type: ignore[arg-type]
            )
