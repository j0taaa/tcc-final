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
from mwpc_exact.budget_bounds import (
    certify_budget_batch,
    unconstrained_budget_bound,
    validate_budget_batch,
)
from mwpc_exact.budgeted_commit import budgeted_commit_frontier
from mwpc_exact.evaluation.selection import SelectionInput
from mwpc_exact.reference.byte_grammars import _SourceGrammarBuilder
from mwpc_exact.reference.normalization import normalize_to_cnf
from mwpc_exact.reference.recognizer import recognizes_cnf


def state_for(words, emissions, rows, proposals, *, canvas=None, eos=None):
    builder = _SourceGrammarBuilder(("S",), start="S")
    for word in words:
        builder.rule("S", word)
    grammar = normalize_to_cnf(builder.build()).grammar
    canvas = tuple(canvas) if canvas is not None else (None,) * len(rows)
    eos = eos or EOSPolicy(EOSMode.ABSENT)
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


@pytest.mark.parametrize("seed", range(270000, 270032))
def test_relaxation_and_certified_ratios_bound_every_original_batch(seed):
    rng = Random(seed)
    all_words = [bytes(t) for t in product(b"ab", repeat=3)]
    words = rng.sample(all_words, rng.randrange(1, len(all_words) + 1))
    # A third alias token is deliberately absent from support in half the trials.
    rows = ((0, 1, 2),) * 3 if seed % 2 else ((0, 1),) * 3
    proposals = tuple(
        Proposal(j, rng.randrange(3), rng.randrange(3), rng.randrange(7) / 8) for j in range(12)
    )
    state = state_for(words, (b"a", b"b", b"a"), rows, proposals)
    for budget in range(4):
        optimum = budgeted_commit_frontier(state, budget)[budget].objective_value
        assert optimum is not None, seed
        upper = unconstrained_budget_bound(state, budget)
        for tokens in product(*rows):
            labels = tuple(state.tokenizer_adapter.emissions[t][0] for t in tokens)
            if not recognizes_cnf(state.grammar, labels):
                continue
            for size in range(budget + 1):
                for chosen in combinations(range(3), size):
                    expected = sum(
                        (
                            Fraction(p.weight)
                            for p in proposals
                            if p.position in chosen and tokens[p.position] == p.token_id
                        ),
                        Fraction(),
                    )
                    proof = certify_budget_batch(
                        state, budget=budget, witness_token_ids=tokens, committed_positions=chosen
                    )
                    assert proof.lower_bound == expected, seed
                    assert expected <= optimum <= upper, seed
                    assert optimum - expected <= proof.additive_gap_bound, seed
                    if optimum:
                        assert proof.approximation_ratio <= expected / optimum, seed


def test_out_of_support_proposals_are_included_in_expansion_bound():
    proposals = (Proposal(0, 0, 0, 1), Proposal(1, 0, 2, 10))
    state = state_for((b"a",), (b"a", b"b", b"a"), ((0,),), proposals)
    proof = certify_budget_batch(state, budget=1, witness_token_ids=(0,))
    assert proof.lower_bound == 1 and proof.upper_bound == 10
    assert proof.approximation_ratio == Fraction(1, 10)
    assert not proof.optimal_under_support_expansion
    expanded = state_for((b"a",), (b"a", b"b", b"a"), ((0, 2),), proposals)
    optimum = budgeted_commit_frontier(expanded, 1)[1]
    assert optimum.objective_value == proof.upper_bound
    tight = certify_budget_batch(expanded, budget=1, witness_token_ids=(2,))
    assert tight.optimal_under_support_expansion
    assert tight.exactness_scope == expanded.support.exactness_scope


def test_zero_bound_is_optimal_only_after_validating_a_real_completion():
    state = state_for((b"a",), (b"a", b"b"), ((0, 1),), ())
    proof = certify_budget_batch(state, budget=0, witness_token_ids=(0,))
    assert proof.lower_bound == proof.upper_bound == 0
    assert proof.approximation_ratio == 1 and proof.optimal_under_support_expansion
    with pytest.raises(ValueError, match="grammar"):
        certify_budget_batch(state, budget=0, witness_token_ids=(1,))


def test_upper_bound_can_be_arbitrarily_loose():
    state = state_for((b"a",), (b"a", b"b"), ((0, 1),), (Proposal(0, 0, 1, 1000),))
    proof = certify_budget_batch(state, budget=1, witness_token_ids=(0,))
    assert proof.lower_bound == 0 and proof.upper_bound == 1000
    assert proof.approximation_ratio == 0 and not proof.optimal_under_support_expansion


def test_fixed_positions_duplicates_and_exact_binary_weights():
    tiny = 2.0**-54
    proposals = (Proposal(0, 0, 0, 100), Proposal(1, 1, 1, 1), Proposal(2, 1, 1, tiny))
    state = state_for((b"ab",), (b"a", b"b"), ((0,), (1,)), proposals, canvas=(0, None))
    proof = certify_budget_batch(state, budget=1, witness_token_ids=(0, 1))
    assert proof.lower_bound == proof.upper_bound == 1 + Fraction(tiny)
    assert proof.batch.committed_positions == (1,)
    assert proof.batch.committed_proposal_ids == (1, 2)
    assert proof.batch.matched_proposal_ids == (0, 1, 2)


@pytest.mark.parametrize("tokens", ((1, 0, 2), (0, 2, 1), (0, 0, 0)))
def test_invalid_eos_pad_trajectories_cannot_supply_lower_bounds(tokens):
    state = state_for(
        (b"a",), (b"a", None, None), ((0, 1, 2),) * 3, (), eos=EOSPolicy(EOSMode.REQUIRED, (1,), 2)
    )
    with pytest.raises(ValueError):
        certify_budget_batch(state, budget=1, witness_token_ids=tokens)


def test_eos_and_pad_are_distinct_physical_slots_even_with_same_token_id():
    state = state_for(
        (b"a",),
        (b"a", None),
        ((0,), (1,), (1,)),
        (Proposal(0, 1, 1, 3), Proposal(1, 2, 1, 2)),
        eos=EOSPolicy(EOSMode.REQUIRED, (1,), 1),
    )
    proof = certify_budget_batch(state, budget=1, witness_token_ids=(0, 1, 1))
    assert proof.batch.emitted_bytes == b"a" and proof.lower_bound == 3
    assert proof.batch.committed_positions == (1,) and proof.upper_bound == 3


@pytest.mark.parametrize(
    "tokens,positions,budget",
    (
        ((0,), (), 1),
        ((0, 1), (1, 1), 2),
        ((0, 1), (0, 1), 1),
        ((False, 1), (), 1),
        ((0, 1), (False,), 1),
        ((0, 1), (2,), 1),
        ((0, 1), (), True),
        ((0, 1), (), -1),
    ),
)
def test_malformed_batches_are_rejected(tokens, positions, budget):
    state = state_for((b"ab",), (b"a", b"b"), ((0,), (1,)), ())
    with pytest.raises(ValueError):
        validate_budget_batch(
            state, budget=budget, witness_token_ids=tokens, committed_positions=positions
        )
