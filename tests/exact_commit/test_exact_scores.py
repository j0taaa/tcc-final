"""Non-associative floating-point counterexamples must not change the optimum."""

import random
from fractions import Fraction
from math import fsum

import pytest

from mwpc_exact import (
    CompositionalByteLevelAdapter,
    EOSMode,
    EOSPolicy,
    ExactBackend,
    Proposal,
    SolveStatus,
    SupportKind,
    SupportPolicy,
    build_per_position_support,
    solve_exact_commit,
    solve_ordinary_support_reference,
)
from mwpc_exact.reference.grammar import (
    BinaryProduction,
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)
from mwpc_exact.reference.token_aligned import solve_token_aligned

GRAMMAR = CnfGrammar(
    nonterminals=tuple(Nonterminal(i, label) for i, label in enumerate(("S", "X", "A", "Y", "B"))),
    terminals=(Terminal(0, 97), Terminal(1, 98)),
    start_nonterminal_id=0,
    terminal_productions=(TerminalProduction(0, 2, 0), TerminalProduction(1, 4, 1)),
    binary_productions=(
        BinaryProduction(2, 1, 2, 2),
        BinaryProduction(3, 0, 1, 2),
        BinaryProduction(4, 3, 4, 4),
        BinaryProduction(5, 0, 3, 4),
    ),
)


@pytest.mark.parametrize(
    "backend",
    [ExactBackend.PYTHON, ExactBackend.RUST, "token_aligned", "ordinary_python", "ordinary_rust"],
)
@pytest.mark.parametrize("large,small", [(1e16, 1.0), (1.0, 5e-324), (1e300, 1e-300)])
@pytest.mark.parametrize("duplicates", [False, True])
def test_score_order_is_independent_of_tree_shape_and_duplicate_aggregation(
    backend: ExactBackend | str, large: float, small: float, duplicates: bool
) -> None:
    proposals = (
        Proposal(0, 0, 0, large),
        Proposal(1, 0, 1, large),
        Proposal(2, 0 if duplicates else 1, 1, small),
        Proposal(3, 2, 1, small),
    )
    support = build_per_position_support(
        canvas=(None,) * 3,
        policy=SupportPolicy(kind=SupportKind.FULL, vocabulary_size=2),
        logits=((1.0, 0.0),) * 3,
    )
    if backend == "token_aligned":
        result = solve_token_aligned(
            grammar=GRAMMAR,
            canvas=support.canvas,
            proposals=proposals,
            exactness_scope=support.exactness_scope,
            terminal_token_ids={0: 0, 1: 1},
        )
    elif backend in ("ordinary_python", "ordinary_rust"):
        ordinary_backend = ExactBackend.RUST if backend == "ordinary_rust" else ExactBackend.PYTHON
        if ordinary_backend is ExactBackend.RUST:
            pytest.importorskip("mwpc_parser_py")
        result = solve_ordinary_support_reference(
            GRAMMAR,
            canvas=support.canvas,
            support=support,
            proposals=proposals,
            tokenizer_adapter=CompositionalByteLevelAdapter((b"a", b"b")),
            backend=ordinary_backend,
        )
    else:
        if backend is ExactBackend.RUST:
            pytest.importorskip("mwpc_parser_py")
        result = solve_exact_commit(
            GRAMMAR,
            canvas=support.canvas,
            support=support,
            proposals=proposals,
            tokenizer_adapter=CompositionalByteLevelAdapter((b"a", b"b")),
            eos_policy=EOSPolicy(EOSMode.ABSENT),
            backend=backend,
        )
    assert result.status is SolveStatus.OPTIMAL, result.diagnostics
    assert result.witness_token_ids == (1, 1, 1)
    assert set(result.selected_proposal_ids or ()) == {1, 2, 3}
    assert result.objective_value == fsum((large, small, small))
    assert Fraction(large) + 2 * Fraction(small) > Fraction(large)


@pytest.mark.parametrize("backend", [ExactBackend.PYTHON, ExactBackend.RUST])
def test_eos_closure_preserves_small_rewards_and_individual_duplicate_terms(
    backend: ExactBackend,
) -> None:
    if backend is ExactBackend.RUST:
        pytest.importorskip("mwpc_parser_py")
    grammar = CnfGrammar(
        nonterminals=(Nonterminal(0, "S"),),
        terminals=(Terminal(0, 97),),
        start_nonterminal_id=0,
        terminal_productions=(TerminalProduction(0, 0, 0),),
    )
    # All branches emit 'a'; only the second EOS alternative carries the tiny
    # duplicate reward. An earlier-rounded epsilon closure chooses incorrectly.
    proposals = (
        Proposal(0, 0, 0, 1e16),
        Proposal(1, 1, 2, 1.0),
        Proposal(2, 1, 2, 1.0),
        Proposal(3, 2, 1, 1.0),
    )
    policy = EOSPolicy(EOSMode.REQUIRED, termination_token_ids=(1, 2), pad_token_id=1)
    support = build_per_position_support(
        canvas=(None,) * 3,
        policy=SupportPolicy(
            kind=SupportKind.FULL, vocabulary_size=3, required_special_token_ids=(1, 2)
        ),
        logits=((0.0, 0.0, 0.0),) * 3,
    )
    result = solve_exact_commit(
        grammar,
        canvas=support.canvas,
        support=support,
        proposals=proposals,
        tokenizer_adapter=CompositionalByteLevelAdapter((b"a", None, None)),
        eos_policy=policy,
        backend=backend,
    )
    assert result.status is SolveStatus.OPTIMAL, result.diagnostics
    assert result.witness_token_ids == (0, 2, 1)
    assert result.objective_value == fsum(proposal.weight for proposal in proposals)


def test_epsilon_free_normalization_preserves_the_original_graph_and_ids() -> None:
    from mwpc_exact import TerminalEdge, WeightedTerminalDAG
    from mwpc_exact.reference.epsilon import normalize_epsilon_edges

    graph = WeightedTerminalDAG((0, 1), 0, (1,), (TerminalEdge(99, 0, 1, 97, 1.0),))
    normalized = normalize_epsilon_edges(graph)
    assert normalized.normalized_graph is graph
    assert normalized.original_edge_ids_by_normalized_edge_id == {99: (99,)}


@pytest.mark.parametrize("backend", [ExactBackend.PYTHON, ExactBackend.RUST])
def test_seeded_extreme_weights_match_exhaustive_homogeneous_completions(
    backend: ExactBackend,
) -> None:
    if backend is ExactBackend.RUST:
        pytest.importorskip("mwpc_parser_py")
    support = build_per_position_support(
        canvas=(None,) * 3,
        policy=SupportPolicy(kind=SupportKind.FULL, vocabulary_size=2),
        logits=((0.0, 0.0),) * 3,
    )
    for seed in range(100):
        rng = random.Random(seed)
        proposals = tuple(
            Proposal(i, i // 2, i % 2, rng.choice((0.0, 5e-324, 1e-300, 0.1, 1.0, 1e16, 1e300)))
            for i in range(6)
        )
        scores = {
            (token,) * 3: sum(
                (Fraction(p.weight) for p in proposals if p.token_id == token), Fraction()
            )
            for token in (0, 1)
        }
        result = solve_exact_commit(
            GRAMMAR,
            canvas=support.canvas,
            support=support,
            proposals=proposals,
            tokenizer_adapter=CompositionalByteLevelAdapter((b"a", b"b")),
            eos_policy=EOSPolicy(EOSMode.ABSENT),
            backend=backend,
        )
        assert result.status is SolveStatus.OPTIMAL, (seed, result.diagnostics)
        assert scores[result.witness_token_ids] == max(scores.values()), seed
        assert result.objective_value == float(max(scores.values())), seed
