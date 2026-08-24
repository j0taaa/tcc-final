from __future__ import annotations

import json
from dataclasses import replace
from itertools import product

import pytest

from mwpc_exact import (
    PerPositionSupport,
    Proposal,
    SupportKind,
    SupportPolicy,
    TokenChoice,
    TokenLatticePath,
    build_per_position_support,
    build_token_lattice,
)


def explicit_support(
    *,
    canvas: tuple[int | None, ...],
    rows: tuple[tuple[int, ...], ...],
    vocabulary_size: int = 8,
    permitted_token_ids: tuple[int, ...] | None = None,
) -> PerPositionSupport:
    policy = SupportPolicy(
        kind=SupportKind.EXPLICIT,
        vocabulary_size=vocabulary_size,
        permitted_token_ids=permitted_token_ids,
    )
    return build_per_position_support(
        canvas=canvas,
        policy=policy,
        explicit_support=dict(enumerate(rows)),
    )


def test_layered_choices_preserve_positions_tokens_and_fixed_singletons() -> None:
    support = explicit_support(
        canvas=(None, 2, None),
        rows=((3, 1), (2,), (5, 0)),
    )

    lattice = build_token_lattice(support=support)

    assert lattice.boundary_ids == (0, 1, 2, 3)
    assert lattice.start_boundary == 0
    assert lattice.final_boundary == 3
    assert tuple(
        (
            choice.token_edge_id,
            choice.position,
            choice.token_id,
            choice.source_boundary,
            choice.target_boundary,
        )
        for choice in lattice.choices
    ) == (
        (0, 0, 1, 0, 1),
        (1, 0, 3, 0, 1),
        (2, 1, 2, 1, 2),
        (3, 2, 0, 2, 3),
        (4, 2, 5, 2, 3),
    )
    assert tuple(len(row) for row in lattice.choices_by_position) == (2, 1, 2)


def test_enumerated_paths_are_exactly_the_cartesian_product_and_consume_all_slots() -> None:
    support = explicit_support(
        canvas=(None, None, 4),
        rows=((0, 2), (1, 3, 5), (4,)),
    )
    lattice = build_token_lattice(support=support)

    paths = tuple(lattice.iter_paths())

    assert lattice.path_count == 6
    assert tuple(path.token_ids for path in paths) == tuple(product(*support.rows))
    for path in paths:
        lattice.validate_path(path)
        assert len(path.token_edge_ids) == lattice.slot_count == 3
        choices = tuple(lattice.choices[token_edge_id] for token_edge_id in path.token_edge_ids)
        assert tuple(choice.position for choice in choices) == (0, 1, 2)
        assert tuple(choice.source_boundary for choice in choices) == (0, 1, 2)
        assert tuple(choice.target_boundary for choice in choices) == (1, 2, 3)


def test_rewards_and_positive_proposal_ids_are_aggregated_once_per_choice() -> None:
    support = explicit_support(
        canvas=(None, 2),
        rows=((0, 1), (2,)),
        vocabulary_size=5,
    )
    proposals = (
        Proposal(9, position=0, token_id=1, weight=2),
        Proposal(4, position=0, token_id=1, weight=3),
        Proposal(12, position=0, token_id=1, weight=0),
        Proposal(7, position=0, token_id=4, weight=11),
        Proposal(8, position=1, token_id=2, weight=5),
    )

    lattice = build_token_lattice(support=support, proposals=proposals)

    choices = {(choice.position, choice.token_id): choice for choice in lattice.choices}
    assert choices[(0, 0)].weight == 0.0
    assert choices[(0, 0)].matched_proposal_ids == ()
    assert choices[(0, 1)].weight == 5.0
    assert choices[(0, 1)].matched_proposal_ids == (9, 4)
    assert choices[(1, 2)].weight == 5.0
    assert choices[(1, 2)].matched_proposal_ids == (8,)
    assert lattice.matched_positive_proposal_ids == (9, 4, 8)
    assert lattice.unrepresented_proposal_ids == (7,)
    assert lattice.unrepresented_positive_proposal_ids == (7,)
    assert lattice.zero_weight_proposal_ids == (12,)

    paths = {path.token_ids: path for path in lattice.iter_paths()}
    assert paths[(0, 2)].objective_value == 5.0
    assert paths[(0, 2)].matched_proposal_ids == (8,)
    assert paths[(1, 2)].objective_value == 10.0
    assert paths[(1, 2)].matched_proposal_ids == (9, 4, 8)


def test_zero_weight_unrepresented_proposal_is_recorded_but_never_matched() -> None:
    support = explicit_support(canvas=(None,), rows=((0,),), vocabulary_size=3)

    lattice = build_token_lattice(
        support=support,
        proposals=(Proposal(5, position=0, token_id=2, weight=0),),
    )

    assert lattice.unrepresented_proposal_ids == (5,)
    assert lattice.unrepresented_positive_proposal_ids == ()
    assert lattice.zero_weight_proposal_ids == (5,)
    assert tuple(lattice.iter_paths()) == (
        TokenLatticePath(
            token_edge_ids=(0,),
            token_ids=(0,),
            objective_value=0,
            matched_proposal_ids=(),
        ),
    )


def test_empty_canvas_has_one_empty_complete_path() -> None:
    support = explicit_support(canvas=(), rows=(), vocabulary_size=2)

    lattice = build_token_lattice(support=support)

    assert lattice.boundary_ids == (0,)
    assert lattice.choices == ()
    assert lattice.slot_count == 0
    assert lattice.path_count == 1
    (path,) = tuple(lattice.iter_paths())
    assert path == TokenLatticePath((), (), 0, ())
    lattice.validate_path(path)


def test_path_validation_rejects_skips_duplicates_and_inconsistent_metadata() -> None:
    support = explicit_support(canvas=(None, None), rows=((0, 1), (2, 3)))
    lattice = build_token_lattice(support=support)

    with pytest.raises(ValueError, match="exactly 2 slots"):
        lattice.validate_path(TokenLatticePath((0,), (0,), 0, ()))
    with pytest.raises(ValueError, match="exactly one edge per slot"):
        lattice.validate_path(TokenLatticePath((0, 1), (0, 1), 0, ()))
    with pytest.raises(ValueError, match="metadata does not match"):
        lattice.validate_path(TokenLatticePath((0, 2), (1, 2), 0, ()))


def test_lattice_validation_rejects_non_layered_or_incomplete_choices() -> None:
    support = explicit_support(canvas=(None, None), rows=((0,), (1,)))
    lattice = build_token_lattice(support=support)
    first = lattice.choices[0]

    with pytest.raises(ValueError, match="consume exactly one"):
        replace(
            lattice,
            choices=(replace(first, target_boundary=2), lattice.choices[1]),
        )
    with pytest.raises(ValueError, match="match every support row exactly"):
        replace(lattice, choices=(first,))


@pytest.mark.parametrize(
    ("proposal", "message"),
    [
        (Proposal(1, position=2, token_id=0, weight=1), "outside the finite canvas"),
        (Proposal(1, position=0, token_id=8, weight=1), "outside.*vocabulary"),
        (Proposal(1, position=0, token_id=6, weight=1), "non-permitted token"),
        (Proposal(1, position=1, token_id=0, weight=1), "conflicts with fixed"),
    ],
)
def test_lattice_rejects_proposals_inconsistent_with_support(
    proposal: Proposal, message: str
) -> None:
    support = explicit_support(
        canvas=(None, 2),
        rows=((0, 1), (2,)),
        vocabulary_size=8,
        permitted_token_ids=(0, 1, 2, 3),
    )

    with pytest.raises(ValueError, match=message):
        build_token_lattice(support=support, proposals=(proposal,))


def test_lattice_rejects_duplicate_proposal_ids() -> None:
    support = explicit_support(canvas=(None,), rows=((0, 1),))

    with pytest.raises(ValueError, match="duplicate proposal_id: 3"):
        build_token_lattice(
            support=support,
            proposals=(
                Proposal(3, position=0, token_id=0, weight=1),
                Proposal(3, position=0, token_id=1, weight=1),
            ),
        )


def test_serialization_records_scope_support_choices_and_proposal_diagnostics() -> None:
    support = explicit_support(canvas=(None,), rows=((0, 2),), vocabulary_size=4)
    lattice = build_token_lattice(
        support=support,
        proposals=(Proposal(6, position=0, token_id=2, weight=4),),
    )

    serialized = json.loads(json.dumps(lattice.to_dict()))

    assert serialized["boundary_ids"] == [0, 1]
    assert serialized["support"]["exactness_scope"]["kind"] == "explicit"
    assert serialized["token_choices"][1]["token_id"] == 2
    assert serialized["token_choices"][1]["matched_proposal_ids"] == [6]
    assert serialized["diagnostics"]["matched_positive_proposal_ids"] == [6]
    assert len(serialized["diagnostics"]["represented_support_sha256"]) == 64


def test_token_choice_rejects_reward_without_positive_provenance() -> None:
    with pytest.raises(ValueError, match="positive weight exactly"):
        TokenChoice(
            token_edge_id=0,
            position=0,
            token_id=1,
            source_boundary=0,
            target_boundary=1,
            weight=1,
        )
