from __future__ import annotations

import json
from math import inf, nan

import pytest

from mwpc_exact import (
    Proposal,
    SupportInputSource,
    SupportKind,
    SupportPolicy,
    build_per_position_support,
    canonical_support_rows_json,
    support_rows_sha256,
)


def test_top_k_is_deterministic_on_score_ties_and_canonicalizes_rows() -> None:
    policy = SupportPolicy(kind=SupportKind.TOP_K, vocabulary_size=5, top_k=2)
    logits = (
        (0.5, 0.5, 0.5, 0.0, -1.0),
        (100.0, 90.0, 80.0, 70.0, -100.0),
        (0.0, 2.0, 1.0, 2.0, -1.0),
    )

    support = build_per_position_support(
        canvas=(None, 4, None),
        policy=policy,
        logits=logits,
    )

    assert support.rows == ((0, 1), (4,), (1, 3))
    assert support.top_k_token_ids_by_position == ((0, 1), (), (1, 3))
    assert support.input_source is SupportInputSource.LOGITS
    assert support.exactness_scope.kind is SupportKind.TOP_K
    assert support.exactness_scope.top_k == 2
    assert support.diagnostics["tie_break"] == "score_descending_then_token_id_ascending"


def test_top_k_adds_required_specials_and_configured_proposal_tokens() -> None:
    policy = SupportPolicy(
        kind=SupportKind.TOP_K,
        vocabulary_size=6,
        top_k=2,
        required_special_token_ids=(5,),
        include_proposal_tokens=True,
    )

    support = build_per_position_support(
        canvas=(None,),
        policy=policy,
        logits=((9.0, 8.0, 7.0, 6.0, 5.0, 4.0),),
        proposals=(Proposal(10, position=0, token_id=4, weight=1),),
    )

    assert support.rows == ((0, 1, 4, 5),)
    assert support.top_k_token_ids_by_position == ((0, 1),)
    assert support.proposal_token_ids_by_position == ((4,),)
    assert support.exactness_scope.included_special_tokens == (5,)
    assert support.diagnostics["proposal_token_inclusion_enabled"] is True


def test_proposal_tokens_are_not_silently_added_when_policy_disables_it() -> None:
    policy = SupportPolicy(kind=SupportKind.TOP_K, vocabulary_size=6, top_k=2)

    support = build_per_position_support(
        canvas=(None,),
        policy=policy,
        logits=((9.0, 8.0, 7.0, 6.0, 5.0, 4.0),),
        proposals=(Proposal(10, position=0, token_id=4, weight=1),),
    )

    assert support.rows == ((0, 1),)
    assert support.proposal_token_ids_by_position == ((),)
    assert support.diagnostics["proposal_token_inclusion_enabled"] is False


def test_adaptive_expansion_uses_last_recorded_width() -> None:
    policy = SupportPolicy(
        kind=SupportKind.TOP_K,
        vocabulary_size=6,
        top_k=1,
        adaptive_expansions=(2, 4),
    )

    support = build_per_position_support(
        canvas=(None,),
        policy=policy,
        logits=((0.0, 5.0, 4.0, 3.0, 2.0, 1.0),),
    )

    assert support.effective_top_k == 4
    assert support.top_k_token_ids_by_position == ((1, 2, 3, 4),)
    assert support.rows == ((1, 2, 3, 4),)
    assert support.exactness_scope.adaptive_expansions == (2, 4)


def test_fixed_position_remains_singleton_with_logits_specials_and_proposal() -> None:
    policy = SupportPolicy(
        kind=SupportKind.TOP_K,
        vocabulary_size=6,
        top_k=2,
        required_special_token_ids=(5,),
        include_proposal_tokens=True,
    )

    support = build_per_position_support(
        canvas=(3,),
        policy=policy,
        logits=((100.0, 90.0, 80.0, -100.0, 70.0, 60.0),),
        proposals=(Proposal(10, position=0, token_id=3, weight=1),),
    )

    assert support.rows == ((3,),)
    assert support.top_k_token_ids_by_position == ((),)
    assert support.proposal_token_ids_by_position == ((3,),)


def test_proposal_conflicting_with_fixed_position_is_rejected() -> None:
    policy = SupportPolicy(kind=SupportKind.TOP_K, vocabulary_size=4, top_k=2)

    with pytest.raises(ValueError, match="conflicts with fixed canvas token"):
        build_per_position_support(
            canvas=(3,),
            policy=policy,
            logits=((4.0, 3.0, 2.0, 1.0),),
            proposals=(Proposal(10, position=0, token_id=2, weight=1),),
        )


def test_full_logits_support_covers_all_permitted_tokens_only_at_masked_slots() -> None:
    policy = SupportPolicy(
        kind=SupportKind.FULL,
        vocabulary_size=6,
        permitted_token_ids=(4, 0, 2),
        required_special_token_ids=(4,),
    )

    support = build_per_position_support(
        canvas=(None, 2),
        policy=policy,
        logits=((5, 4, 3, 2, 1, 0), (0, 1, 2, 3, 4, 5)),
    )

    assert support.permitted_token_ids == (0, 2, 4)
    assert support.rows == ((0, 2, 4), (2,))
    assert support.exactness_scope.kind is SupportKind.FULL
    assert support.exactness_scope.top_k is None


def test_full_explicit_support_requires_complete_masked_rows() -> None:
    policy = SupportPolicy(
        kind=SupportKind.FULL,
        vocabulary_size=4,
        permitted_token_ids=(0, 2, 3),
    )

    valid = build_per_position_support(
        canvas=(None, 2),
        policy=policy,
        explicit_support={1: (2,), 0: (3, 0, 2)},
    )

    assert valid.rows == ((0, 2, 3), (2,))
    assert valid.input_source is SupportInputSource.EXPLICIT
    with pytest.raises(ValueError, match="FULL support row 0"):
        build_per_position_support(
            canvas=(None, 2),
            policy=policy,
            explicit_support={0: (0, 2), 1: (2,)},
        )


def test_explicit_support_adds_configured_tokens_and_preserves_scope() -> None:
    policy = SupportPolicy(
        kind=SupportKind.EXPLICIT,
        vocabulary_size=7,
        required_special_token_ids=(6,),
        include_proposal_tokens=True,
        pruning_description="saved replay rows",
    )

    support = build_per_position_support(
        canvas=(None, None),
        policy=policy,
        explicit_support={1: (5, 2), 0: (3, 1)},
        proposals=(Proposal(10, position=0, token_id=4, weight=1),),
    )

    assert support.rows == ((1, 3, 4, 6), (2, 5, 6))
    assert support.exactness_scope.kind is SupportKind.EXPLICIT
    assert support.exactness_scope.pruning_description == "saved replay rows"
    assert support.proposal_token_ids_by_position == ((4,), ())


def test_explicit_input_order_does_not_change_canonical_fingerprint() -> None:
    policy = SupportPolicy(kind=SupportKind.EXPLICIT, vocabulary_size=5)
    first = build_per_position_support(
        canvas=(None, None),
        policy=policy,
        explicit_support={0: (3, 1), 1: (4, 2)},
    )
    second = build_per_position_support(
        canvas=(None, None),
        policy=policy,
        explicit_support={1: (2, 4), 0: (1, 3)},
    )

    assert first.rows == second.rows == ((1, 3), (2, 4))
    assert first.canonical_rows_json == second.canonical_rows_json == "[[1,3],[2,4]]"
    assert first.fingerprint == second.fingerprint == support_rows_sha256(first.rows)
    assert first.fingerprint == "b8071183795a2d11bef66cd2c5b27c2f8fb12f6152b34e4ddfd0c87c895fdbb5"


@pytest.mark.parametrize("fixed_row", [(), (1,), (2, 3), (1, 2, 3)])
def test_explicit_support_cannot_omit_or_widen_fixed_token(
    fixed_row: tuple[int, ...],
) -> None:
    policy = SupportPolicy(kind=SupportKind.EXPLICIT, vocabulary_size=4)

    with pytest.raises(ValueError, match="fixed position 0 explicit support"):
        build_per_position_support(
            canvas=(2,),
            policy=policy,
            explicit_support={0: fixed_row},
        )


@pytest.mark.parametrize(
    ("support_map", "message"),
    [
        ({0: (1,)}, r"missing=\[1\]"),
        ({0: (1,), 1: (2,), 2: (3,)}, r"extra=\[2\]"),
        ({0: (1, 1), 1: (2,)}, "duplicate token IDs"),
        ({0: (), 1: (2,)}, "masked support row 0 must not be empty"),
    ],
)
def test_explicit_support_rejects_malformed_maps(
    support_map: dict[int, tuple[int, ...]], message: str
) -> None:
    policy = SupportPolicy(kind=SupportKind.EXPLICIT, vocabulary_size=4)

    with pytest.raises(ValueError, match=message):
        build_per_position_support(
            canvas=(None, None),
            policy=policy,
            explicit_support=support_map,
        )


def test_input_source_must_match_scope_and_be_unambiguous() -> None:
    top_k_policy = SupportPolicy(kind=SupportKind.TOP_K, vocabulary_size=4, top_k=2)
    explicit_policy = SupportPolicy(kind=SupportKind.EXPLICIT, vocabulary_size=4)

    with pytest.raises(ValueError, match="exactly one"):
        build_per_position_support(canvas=(None,), policy=top_k_policy)
    with pytest.raises(ValueError, match="exactly one"):
        build_per_position_support(
            canvas=(None,),
            policy=top_k_policy,
            logits=((1, 2, 3, 4),),
            explicit_support={0: (1,)},
        )
    with pytest.raises(ValueError, match="TOP_K support must be constructed from logits"):
        build_per_position_support(
            canvas=(None,), policy=top_k_policy, explicit_support={0: (1,)}
        )
    with pytest.raises(ValueError, match="EXPLICIT support must be constructed"):
        build_per_position_support(
            canvas=(None,), policy=explicit_policy, logits=((1, 2, 3, 4),)
        )


@pytest.mark.parametrize(
    ("logits", "error", "message"),
    [
        (((1.0, 2.0, 3.0),), ValueError, "exactly 4 scores"),
        (((1.0, 2.0, 3.0, nan),), ValueError, "must not be NaN"),
        (((1.0, 2.0, 3.0, True),), TypeError, "must be real"),
    ],
)
def test_logits_are_validated_before_ranking(
    logits: tuple[tuple[object, ...], ...], error: type[Exception], message: str
) -> None:
    policy = SupportPolicy(kind=SupportKind.TOP_K, vocabulary_size=4, top_k=2)

    with pytest.raises(error, match=message):
        build_per_position_support(
            canvas=(None,),
            policy=policy,
            logits=logits,  # type: ignore[arg-type]
        )


def test_infinite_logits_have_deterministic_ranking_semantics() -> None:
    policy = SupportPolicy(kind=SupportKind.TOP_K, vocabulary_size=4, top_k=2)

    support = build_per_position_support(
        canvas=(None,),
        policy=policy,
        logits=((inf, 0.0, -inf, 1.0),),
    )

    assert support.top_k_token_ids_by_position == ((0, 3),)
    assert support.rows == ((0, 3),)


def test_top_k_ranks_only_semantically_permitted_tokens() -> None:
    policy = SupportPolicy(
        kind=SupportKind.TOP_K,
        vocabulary_size=5,
        top_k=1,
        permitted_token_ids=(1, 3, 4),
    )

    support = build_per_position_support(
        canvas=(None,),
        policy=policy,
        logits=((100.0, 1.0, 90.0, 5.0, 4.0),),
    )

    assert support.rows == ((3,),)
    assert support.top_k_token_ids_by_position == ((3,),)


def test_top_k_covering_permitted_vocabulary_must_be_labeled_full() -> None:
    with pytest.raises(ValueError, match="use FULL"):
        SupportPolicy(
            kind=SupportKind.TOP_K,
            vocabulary_size=5,
            top_k=3,
            permitted_token_ids=(0, 2, 4),
        )


def test_non_permitted_special_fixed_and_proposal_tokens_are_rejected() -> None:
    with pytest.raises(ValueError, match="special tokens are not permitted"):
        SupportPolicy(
            kind=SupportKind.EXPLICIT,
            vocabulary_size=5,
            permitted_token_ids=(0, 1, 2),
            required_special_token_ids=(4,),
        )

    policy = SupportPolicy(
        kind=SupportKind.EXPLICIT,
        vocabulary_size=5,
        permitted_token_ids=(0, 1, 2),
    )
    with pytest.raises(ValueError, match=r"fixed canvas token.*not permitted"):
        build_per_position_support(
            canvas=(4,), policy=policy, explicit_support={0: (4,)}
        )
    with pytest.raises(ValueError, match="non-permitted token ID"):
        build_per_position_support(
            canvas=(None,),
            policy=policy,
            explicit_support={0: (1,)},
            proposals=(Proposal(10, position=0, token_id=4, weight=1),),
        )
    with pytest.raises(ValueError, match="non-permitted token IDs"):
        build_per_position_support(
            canvas=(None,), policy=policy, explicit_support={0: (1, 4)}
        )


def test_support_serialization_contains_scope_rows_and_replay_diagnostics() -> None:
    policy = SupportPolicy(kind=SupportKind.EXPLICIT, vocabulary_size=4)
    support = build_per_position_support(
        canvas=(None, 2),
        policy=policy,
        explicit_support={0: (3, 1), 1: (2,)},
    )

    serialized = json.loads(json.dumps(support.to_dict()))

    assert serialized["per_position_support"] == [[1, 3], [2]]
    assert serialized["permitted_token_ids"] == [0, 1, 2, 3]
    assert serialized["exactness_scope"]["kind"] == "explicit"
    assert serialized["diagnostics"]["represented_support_canonical_json"] == "[[1,3],[2]]"
    assert len(serialized["diagnostics"]["represented_support_sha256"]) == 64
    assert len(serialized["diagnostics"]["permitted_token_ids_sha256"]) == 64


def test_canonical_support_helpers_reject_duplicates() -> None:
    assert canonical_support_rows_json(((3, 1), (), (2,))) == "[[1,3],[],[2]]"
    with pytest.raises(ValueError, match="duplicate token IDs"):
        canonical_support_rows_json(((1, 1),))
