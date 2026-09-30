from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from itertools import combinations, product
from random import Random

import pytest

from mwpc_exact import (
    CompositionalByteLevelAdapter,
    EOSMode,
    EOSPolicy,
    Proposal,
    SolveStatus,
    SupportKind,
    SupportPolicy,
    build_per_position_support,
)
from mwpc_exact.budgeted_commit import budgeted_commit_frontier, budgeted_progress_update
from mwpc_exact.evaluation.selection import SelectionInput
from mwpc_exact.reference.budget_certificate import check_budget_certificate
from mwpc_exact.reference.budget_types import ResourceArc, ResourceDAG, rational_reward
from mwpc_exact.reference.budgeted_parser import budgeted_frontier
from mwpc_exact.reference.byte_grammars import _SourceGrammarBuilder
from mwpc_exact.reference.grammar import CnfGrammar, Nonterminal, Terminal, TerminalProduction
from mwpc_exact.reference.normalization import normalize_to_cnf
from mwpc_exact.reference.recognizer import recognizes_cnf


def fixed_language() -> CnfGrammar:
    # One fixed regular language for the ENTIRE infinite counterexample family.
    builder = _SourceGrammarBuilder(("S", "Z", "H", "L"), start="S")
    builder.rule("S", "Z", "H", "Z")
    builder.rule("S", "Z", "L", "Z")
    builder.rule("Z", b"0", "Z")
    builder.rule("Z")
    builder.rule("H", b"h")
    builder.rule("L", b"l", "L")
    builder.rule("L", b"l")
    return normalize_to_cnf(builder.build()).grammar


@pytest.mark.parametrize("use_final", (False, True))
def test_boolean_start_or_final_is_not_a_stable_node_id(use_final):
    with pytest.raises(ValueError, match="non-negative integer"):
        ResourceDAG((0, 1), 0 if use_final else False, (False,) if use_final else (1,), ())


def state_for(grammar, emissions, rows, proposals, *, canvas=None, eos=None):
    adapter = CompositionalByteLevelAdapter(tuple(emissions))
    if canvas is None:
        canvas = (None,) * len(rows)
    if eos is None:
        eos = EOSPolicy(EOSMode.ABSENT)
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(
            kind=SupportKind.EXPLICIT,
            vocabulary_size=len(emissions),
            required_special_token_ids=eos.termination_token_ids,
        ),
        explicit_support=dict(enumerate(rows)),
        proposals=proposals,
    )
    return SelectionInput(grammar, canvas, tuple(proposals), support, adapter, eos)


def family(budget):
    proposals = tuple(
        Proposal(i, i, 1 if i < budget else 2, 7 / 8 if i < budget else 3 / 4)
        for i in range(2 * budget)
    )
    return state_for(
        fixed_language(), (b"0", b"h", b"l"), ((0, 1),) * budget + ((0, 2),) * budget, proposals
    )


def exhaustive_paths(grammar, graph, budget):
    best = None
    outgoing = {node: [a for a in graph.arcs if a.source == node] for node in graph.nodes}

    def visit(node, path):
        nonlocal best
        if node in graph.finals:
            labels = tuple(a.label for a in path if a.label is not None)
            cost = sum(a.cost for a in path)
            if cost <= budget and recognizes_cnf(grammar, labels):
                value = sum((a.reward for a in path), Fraction())
                if best is None or value > best:
                    best = value
        for arc in outgoing[node]:
            visit(arc.target, (*path, arc))

    visit(graph.start, ())
    return best


@pytest.mark.parametrize("seed", range(260000, 260064))
def test_resource_dp_and_optimality_checker_equal_exhaustive_paths(seed):
    rng = Random(seed)
    builder = _SourceGrammarBuilder(("S",), start="S")
    builder.rule("S", b"a")
    builder.rule("S", b"b")
    builder.rule("S", "S", "S")
    if rng.choice((True, False)):
        builder.rule("S")
    grammar = normalize_to_cnf(builder.build()).grammar
    arcs = []
    for u in range(5):
        for v in range(u + 1, 5):
            for _ in range(rng.randrange(3)):
                arcs.append(
                    ResourceArc(
                        len(arcs),
                        u,
                        v,
                        rng.choice((None, 97, 98, 99)),
                        Fraction(rng.randrange(7), rng.randrange(1, 5)),
                        rng.randrange(3),
                    )
                )
    graph = ResourceDAG(tuple(range(5)), 0, (2, 4), tuple(arcs))
    results = budgeted_frontier(grammar, graph, 3)
    for budget, result in enumerate(results):
        expected = exhaustive_paths(grammar, graph, budget)
        assert result.objective_value == expected, seed
        assert (result.status is SolveStatus.OPTIMAL) == (expected is not None), seed
        report = check_budget_certificate(grammar, graph, result)
        assert report.accepted, (seed, report.errors)


@pytest.mark.parametrize("budget", range(2, 8))
def test_infinite_family_formula_and_joint_budget_preselection_separation(budget):
    state = family(budget)
    optimum = budgeted_commit_frontier(state, budget)[budget]
    assert optimum.objective_value == Fraction(3 * budget, 4)
    assert len(optimum.committed_positions) == budget
    assert all(i >= budget for i in optimum.committed_positions)
    preselected = replace(state, proposals=state.proposals[:budget])
    restricted = budgeted_commit_frontier(preselected, budget)[budget]
    assert restricted.objective_value == Fraction(7, 8)
    assert restricted.objective_value / optimum.objective_value == Fraction(7, 6 * budget)


@pytest.mark.integration
@pytest.mark.parametrize("budget", (2, 4, 8, 16))
@pytest.mark.parametrize("universal_cover", (False, True))
def test_pinned_epic_control_flow_selects_first_high_proposal(monkeypatch, budget, universal_cover):
    # Original upstream control flow; abstract exact oracles for the proved language.
    # This checks the algorithm specialization, not lexer/regex performance.
    from constrained_diffusion import regular_cover as upstream

    def feasible(**kwargs):
        words = kwargs["words_full"]
        highs = [i for i, x in enumerate(words) if x == "h"]
        lows = [i for i, x in enumerate(words) if x == "l"]
        return len(highs) <= 1 and not (highs and lows)

    monkeypatch.setattr(
        upstream, "cover_allows_words", (lambda **kwargs: True) if universal_cover else feasible
    )
    monkeypatch.setattr(upstream, "exact_allows_words", feasible)
    monkeypatch.setattr(upstream, "regular_cover_exact_enabled", lambda: True)
    candidates = [
        upstream.BatchCandidate(i, i, "h" if i < budget else "l", 7 / 8 if i < budget else 3 / 4)
        for i in range(2 * budget)
    ]
    selected = upstream.select_batch_with_regular_cover(
        words_full=[None] * (2 * budget),
        candidates=candidates,
        prompt_len=0,
        cfg=None,
        lex_map=None,
        terminals=[],
        prelex=None,
        single_token_lexing=None,
        inject_gap_size=0,
        max_total_injections=0,
        subtokens=None,
        supertokens=None,
        strip_chars=None,
    )
    assert len(selected) == 1 and selected[0].index == 0
    assert selected[0].score == 7 / 8


def test_duplicates_fixed_slots_multibyte_and_full_matches_are_separate():
    builder = _SourceGrammarBuilder(("S",), start="S")
    builder.rule("S", b"ab")
    grammar = normalize_to_cnf(builder.build()).grammar
    state = state_for(
        grammar,
        (b"a", b"b", b"ab", b"a"),
        ((0, 3), (1,)),
        (Proposal(1, 0, 0, 2), Proposal(2, 0, 0, 3), Proposal(3, 1, 1, 4)),
    )
    results = budgeted_commit_frontier(state, 2)
    assert [r.objective_value for r in results] == [0, 5, 9]
    assert results[1].committed_positions == (0,)
    assert results[1].committed_proposal_ids == (1, 2)
    assert results[1].matched_proposal_ids == (1, 2, 3)
    fixed = state_for(
        grammar,
        (b"a", b"b"),
        ((0,), (1,)),
        (Proposal(4, 0, 0, 100), Proposal(5, 1, 1, 2)),
        canvas=(0, None),
    )
    result = budgeted_commit_frontier(fixed, 1)[1]
    assert result.objective_value == 2 and result.committed_positions == (1,)
    assert result.matched_proposal_ids == (4, 5)


def test_eos_pad_empty_emissions_preserve_exact_slots_and_zero_budget():
    grammar = CnfGrammar(
        (Nonterminal(0, "S"),), (Terminal(0, 97),), 0, (TerminalProduction(0, 0, 0),)
    )
    state = state_for(
        grammar,
        (b"a", None),
        ((0,), (1,), (1,)),
        (Proposal(0, 0, 0, 1), Proposal(1, 1, 1, 3), Proposal(2, 2, 1, 2)),
        eos=EOSPolicy(EOSMode.REQUIRED, (1,), 1),
    )
    results = budgeted_commit_frontier(state, 3)
    assert [r.objective_value for r in results] == [0, 3, 5, 6]
    assert all(r.witness_token_ids == (0, 1, 1) for r in results)
    assert results[1].committed_positions == (1,)
    assert results[1].witness_terminal_labels == (97,)
    with pytest.raises(ValueError, match="zero budget"):
        budgeted_progress_update(state, results[0])


def test_zero_rewards_progress_is_unscored_and_fills_budget():
    state = family(2)
    state = replace(state, proposals=())
    result = budgeted_commit_frontier(state, 2)[2]
    updated, fallback = budgeted_progress_update(state, result)
    assert result.objective_value == 0 and result.committed_proposal_ids == ()
    assert len(fallback) == 2 and sum(t is not None for t in updated) == 2
    for i in fallback:
        assert updated[i] == result.witness_token_ids[i]


def test_multibyte_split_utf8_changes_the_best_witness_with_budget():
    builder = _SourceGrammarBuilder(("S",), start="S")
    builder.rule("S", "é".encode())
    grammar = normalize_to_cnf(builder.build()).grammar
    state = state_for(
        grammar,
        (b"\xc3", b"\xa9", "é".encode(), None),
        ((0, 2), (1, 3), (3,)),
        (Proposal(0, 0, 2, 3), Proposal(1, 0, 0, 2), Proposal(2, 1, 1, 2)),
        eos=EOSPolicy(EOSMode.REQUIRED, (3,), 3),
    )
    frontier = budgeted_commit_frontier(state, 2)
    assert frontier[1].objective_value == 3
    assert frontier[1].witness_token_ids == (2, 3, 3)
    assert frontier[2].objective_value == 4
    assert frontier[2].witness_token_ids == (0, 1, 3)
    assert frontier[1].witness_terminal_labels == frontier[2].witness_terminal_labels == (195, 169)


@pytest.mark.parametrize("weak_count", (2, 4, 8))
def test_optimize_all_then_filter_also_has_unbounded_loss_at_budget_one(weak_count):
    from mwpc_exact import ExactBackend, select_exact_mwpc

    proposals = (
        Proposal(0, 0, 1, 7 / 8),
        *(Proposal(i, i, 2, 7 / (4 * weak_count)) for i in range(1, weak_count + 1)),
    )
    state = state_for(
        fixed_language(), (b"0", b"h", b"l"), ((0, 1),) + ((0, 2),) * weak_count, proposals
    )
    joint = budgeted_commit_frontier(state, 1)[1]
    ordinary = select_exact_mwpc(state, backend=ExactBackend.PYTHON)
    postfiltered = max(
        Fraction(p.weight) for p in proposals if p.proposal_id in ordinary.selected_proposal_ids
    )
    assert ordinary.score == 7 / 4
    assert joint.objective_value == Fraction(7, 8)
    assert postfiltered / joint.objective_value == Fraction(2, weak_count)


def test_budget_round_bound_with_witness_preserving_support_updates():
    initial = family(3)
    initial = replace(initial, proposals=())
    state = initial
    rounds = 0
    while any(t is None for t in state.canvas):
        result = budgeted_commit_frontier(state, 2)[2]
        updated, _ = budgeted_progress_update(state, result)
        rows = tuple(
            (token,) if token is not None else row
            for token, row in zip(updated, state.support.rows, strict=True)
        )
        state = state_for(
            state.grammar, state.tokenizer_adapter.emissions, rows, (), canvas=updated
        )
        rounds += 1
    assert rounds == 3
    labels = tuple(b for t in state.canvas for b in state.tokenizer_adapter.emissions[t])
    assert recognizes_cnf(state.grammar, labels)


def test_progress_rejects_a_result_from_other_proposals():
    state = family(2)
    result = budgeted_commit_frontier(state, 2)[2]
    with pytest.raises(ValueError, match="different frozen input"):
        budgeted_progress_update(replace(state, proposals=()), result)


def test_exact_binary_float_values_and_parallel_epsilon_paths():
    grammar = CnfGrammar(
        (Nonterminal(0, "S"),), (Terminal(0, "a"),), 0, (TerminalProduction(0, 0, 0),)
    )
    graph = ResourceDAG(
        (0, 1, 2),
        0,
        (2,),
        (
            ResourceArc(0, 0, 1, "a", Fraction(1)),
            ResourceArc(1, 1, 2, None, Fraction(1, 2**54)),
            ResourceArc(2, 0, 2, "a", Fraction(1)),
        ),
    )
    result = budgeted_frontier(grammar, graph, 0)[0]
    assert result.objective_value == 1 + Fraction(1, 2**54)
    assert result.witness_arc_ids == (0, 1)
    assert check_budget_certificate(grammar, graph, result).accepted


def test_checker_rejects_forged_upper_bound_witness_and_infeasibility():
    state = family(2)
    result = budgeted_commit_frontier(state, 2)[2].path_result
    graph = budgeted_commit_frontier(state, 2)[2].proof_graph
    proof = result.certificate
    modified = replace(
        proof, grammar_bounds=tuple((*row[:4], row[4] + 1) for row in proof.grammar_bounds)
    )
    for forged in (
        replace(result, certificate=modified),
        replace(result, certificate=replace(proof, epsilon_bounds=proof.epsilon_bounds[1:])),
        replace(result, witness_arc_ids=(999999,)),
        replace(result, consumed_budget=0),
        replace(result, status=SolveStatus.INFEASIBLE_ON_SUPPORT),
        replace(result, exactness_scope="full vocabulary"),
    ):
        assert not check_budget_certificate(state.grammar, graph, forged).accepted


def test_feasibility_alone_cannot_certify_a_suboptimal_batch():
    state = family(2)
    frontier = budgeted_commit_frontier(state, 2)
    smaller = frontier[1].path_result
    forged = replace(smaller, budget=2)
    report = check_budget_certificate(state.grammar, frontier[1].proof_graph, forged)
    assert report.errors == ("witness does not attain independently checked upper bound",)


@pytest.mark.parametrize("bad", (-1, float("nan"), float("inf"), True))
def test_reject_invalid_weights(bad):
    with pytest.raises((ValueError, TypeError)):
        rational_reward(bad)


def test_budget_cannot_be_negative_or_boolean_and_graph_must_be_acyclic():
    for budget in (-1, True):
        with pytest.raises(ValueError):
            budgeted_commit_frontier(family(2), budget)
    with pytest.raises(ValueError, match="topological"):
        ResourceDAG((0, 1), 0, (1,), (ResourceArc(0, 1, 0, "x", Fraction()),))


def test_tiny_token_completion_and_subset_oracle_independent_of_resource_graph():
    state = family(2)
    frontier = budgeted_commit_frontier(state, 4)
    for budget in range(5):
        best = Fraction()
        for tokens in product(*state.support.rows):
            labels = tuple(b for token in tokens for b in state.tokenizer_adapter.emissions[token])
            if not recognizes_cnf(state.grammar, labels):
                continue
            for size in range(budget + 1):
                for chosen in combinations(range(4), size):
                    score = sum(
                        (
                            Fraction(p.weight)
                            for p in state.proposals
                            if p.position in chosen and tokens[p.position] == p.token_id
                        ),
                        Fraction(),
                    )
                    best = max(best, score)
        assert frontier[budget].objective_value == best
