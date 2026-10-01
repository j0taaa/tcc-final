from __future__ import annotations

from fractions import Fraction
from itertools import combinations, product
from random import Random

import pytest

from mwpc_exact import (
    CompositionalByteLevelAdapter,
    EOSMode,
    EOSPolicy,
    Proposal,
    SupportKind,
    SupportPolicy,
    build_per_position_support,
)
from mwpc_exact.budget_graph import BudgetGraphLayout, compile_budget_graph
from mwpc_exact.budgeted_commit import budgeted_commit_frontier
from mwpc_exact.evaluation.selection import SelectionInput
from mwpc_exact.reference.byte_grammars import _SourceGrammarBuilder
from mwpc_exact.reference.normalization import normalize_to_cnf
from mwpc_exact.reference.recognizer import recognizes_cnf


def make_state(words, emissions, rows, proposals=(), *, eos=None, canvas=None):
    builder = _SourceGrammarBuilder(("S",), start="S")
    for word in words:
        builder.rule("S", *((word,) if word else ()))
    grammar = normalize_to_cnf(builder.build()).grammar
    eos = eos or EOSPolicy(EOSMode.ABSENT)
    canvas = canvas or (None,) * len(rows)
    specials = tuple(
        dict.fromkeys(
            (
                *eos.termination_token_ids,
                *((eos.pad_token_id,) if eos.pad_token_id is not None else ()),
            )
        )
    )
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(
            kind=SupportKind.EXPLICIT,
            vocabulary_size=len(emissions),
            required_special_token_ids=specials,
        ),
        explicit_support=dict(enumerate(rows)),
        proposals=proposals,
    )
    return SelectionInput(
        grammar,
        canvas,
        tuple(proposals),
        support,
        CompositionalByteLevelAdapter(tuple(emissions)),
        eos,
    )


def original_completion_oracle(state, budget):
    # Deliberately no resource graph, compiler, batch validator or weighted parser.
    best = None
    for tokens in product(*state.support.rows):
        visible = bytearray()
        after = False
        valid = True
        for token in tokens:
            if state.eos_policy.mode is not EOSMode.ABSENT:
                if after:
                    if token != state.eos_policy.pad_token_id:
                        valid = False
                    continue
                if token in state.eos_policy.termination_token_ids:
                    after = True
                    continue
                if token == state.eos_policy.pad_token_id:
                    valid = False
                    break
            emission = state.tokenizer_adapter.emissions[token]
            if emission is None:
                valid = False
                break
            visible.extend(emission)
        if state.eos_policy.mode is EOSMode.REQUIRED and not after:
            valid = False
        if not valid or not recognizes_cnf(state.grammar, tuple(visible)):
            continue
        free = [i for i, token in enumerate(state.canvas) if token is None]
        for size in range(min(budget, len(free)) + 1):
            for chosen in combinations(free, size):
                value = sum(
                    (
                        Fraction(p.weight)
                        for p in state.proposals
                        if p.position in chosen and tokens[p.position] == p.token_id
                    ),
                    Fraction(),
                )
                best = value if best is None else max(best, value)
    return best


@pytest.mark.parametrize("seed", range(270100, 270132))
def test_compact_private_and_original_completion_oracle_agree_for_every_budget(seed):
    rng = Random(seed)
    emissions = (b"a", b"ab", b"abc", b"ac", b"a", b"b", None, None)
    mode = (EOSMode.ABSENT, EOSMode.OPTIONAL, EOSMode.REQUIRED)[seed % 3]
    eos = EOSPolicy(mode) if mode is EOSMode.ABSENT else EOSPolicy(mode, (6,), 7)
    rows = tuple(
        tuple(sorted(rng.sample(range(8 if mode is not EOSMode.ABSENT else 6), 3)))
        for _ in range(3)
    )
    words = set()
    for tokens in product(*rows):
        words.add(b"".join(emissions[t] or b"" for t in tokens))
    words = rng.sample(sorted(words), max(1, len(words) // 2))
    proposals = tuple(
        Proposal(j, rng.randrange(3), rng.randrange(8), rng.randrange(9) / 8) for j in range(9)
    )
    state = make_state(words, emissions, rows, proposals, eos=eos)
    private = budgeted_commit_frontier(state, 3, graph_layout=BudgetGraphLayout.PRIVATE)
    compact = budgeted_commit_frontier(state, 3)
    assert len(compact[0].proof_graph.nodes) <= len(private[0].proof_graph.nodes), seed
    for cap in range(4):
        expected = original_completion_oracle(state, cap)
        assert compact[cap].objective_value == private[cap].objective_value == expected, seed
        assert compact[cap].status == private[cap].status, seed


def test_aliases_and_a_token_prefixing_another_close_with_their_own_rewards():
    state = make_state(
        (b"a", b"ab", b"ac"),
        (b"a", b"ab", b"a", b"ac"),
        ((0, 1, 2, 3),),
        (Proposal(0, 0, 0, 1), Proposal(1, 0, 1, 3), Proposal(2, 0, 2, 4)),
    )
    result = budgeted_commit_frontier(state, 1)[1]
    assert result.objective_value == 4 and result.witness_token_ids == (2,)
    assert result.committed_proposal_ids == (2,)
    compiled = result.compiled_graph
    assert compiled.node_savings == 1
    ends = [x for x in compiled.closings if x.token_id == 2]
    arcs = {a.arc_id: a for a in compiled.graph.arcs}
    assert all(arcs[x.arc_id].label is None for x in ends)


def test_two_high_tokens_cannot_splice_shared_prefix_and_foreign_suffix():
    state = make_state(
        (b"abc",),
        (b"abc", b"abd", b"abx"),
        ((0, 1, 2),),
        (Proposal(0, 0, 0, 1), Proposal(1, 0, 1, 10), Proposal(2, 0, 2, 20)),
    )
    for layout in BudgetGraphLayout:
        result = budgeted_commit_frontier(state, 1, graph_layout=layout)[1]
        assert result.objective_value == 1 and result.witness_token_ids == (0,)


def test_shared_prefix_does_not_pay_for_a_token_that_has_not_closed():
    state = make_state(
        (b"a",), (b"a", b"ab"), ((0, 1),), (Proposal(0, 0, 0, 1), Proposal(1, 0, 1, 100))
    )
    result = budgeted_commit_frontier(state, 1)[1]
    assert result.objective_value == 1 and result.committed_proposal_ids == (0,)
    for arc in result.proof_graph.arcs:
        if arc.source == 0 and arc.target not in (2, 3):
            assert arc.reward == arc.cost == 0


def test_prefix_compression_has_a_proved_strict_size_reduction_family():
    for length in (2, 8, 32):
        emissions = tuple(b"a" * length + bytes((t,)) for t in b"bcdefghi")
        state = make_state((emissions[0],), emissions, (tuple(range(8)),))
        private = compile_budget_graph(state, layout=BudgetGraphLayout.PRIVATE)
        compact = compile_budget_graph(state)
        assert len(private.graph.nodes) == 4 + 8 * length
        assert len(compact.graph.nodes) == 4 + length
        assert compact.node_savings == 7 * length


def test_split_utf8_and_fixed_positions_preserve_token_provenance():
    state = make_state(
        ("é".encode(),),
        (b"\xc3", b"\xc3\xa9", b"\xa9", None),
        ((0,), (2, 3), (3,)),
        (Proposal(0, 0, 0, 100), Proposal(1, 1, 2, 2), Proposal(2, 2, 3, 1)),
        canvas=(0, None, None),
        eos=EOSPolicy(EOSMode.REQUIRED, (3,), 3),
    )
    result = budgeted_commit_frontier(state, 2)[2]
    assert result.objective_value == 3 and result.witness_token_ids == (0, 2, 3)
    assert result.committed_positions == (1, 2)
    assert result.matched_proposal_ids == (0, 1, 2)


def test_budgeted_compiler_never_runs_ordinary_epsilon_normalization(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("ordinary MWPC normalization is unnecessary for budgeted parsing")

    monkeypatch.setattr("mwpc_exact.eos_lattice.normalize_epsilon_edges", forbidden)
    state = make_state((b"ab",), (b"ab", b"ac"), ((0, 1),), (Proposal(0, 0, 0, 1),))
    assert budgeted_commit_frontier(state, 1)[1].objective_value == 1
