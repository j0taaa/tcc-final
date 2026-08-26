from __future__ import annotations

from mwpc_exact import (
    Proposal,
    RankedSupportRows,
    SupportKind,
    SupportPolicy,
    build_per_position_support,
    build_per_position_support_from_rankings,
    rank_support_from_dense_logits,
)


def test_compact_rankings_reproduce_dense_support_for_every_adaptive_prefix() -> None:
    logits = (
        (2.0, 4.0, 4.0, -1.0, 0.0),
        (5.0, 1.0, 3.0, 3.0, 2.0),
    )
    rankings = rank_support_from_dense_logits(
        logits,
        vocabulary_size=5,
        permitted_token_ids=(0, 1, 2, 3, 4),
        max_k=4,
    )
    assert rankings.token_ids_by_position == ((1, 2, 0, 4), (0, 2, 3, 4))
    proposals = (Proposal(7, position=0, token_id=3, weight=1.0),)
    for width in (1, 2, 4):
        policy = SupportPolicy(
            kind=SupportKind.TOP_K,
            vocabulary_size=5,
            top_k=1,
            adaptive_expansions=(() if width == 1 else (width,)),
            required_special_token_ids=(4,),
            include_proposal_tokens=True,
        )
        dense = build_per_position_support(
            canvas=(None, None),
            policy=policy,
            logits=logits,
            proposals=proposals,
        )
        compact = build_per_position_support_from_rankings(
            canvas=(None, None),
            policy=policy,
            rankings=rankings,
            proposals=proposals,
        )
        assert compact == dense


def test_ranked_support_is_bounded_by_max_k_not_vocabulary_size() -> None:
    rankings = RankedSupportRows(
        vocabulary_size=100_000,
        permitted_token_ids=tuple(range(10)),
        token_ids_by_position=((3, 2, 1, 0), (4, 5, 6, 7)),
        max_k=4,
        source="unit_test",
    )
    assert sum(len(row) for row in rankings.token_ids_by_position) == 8
    assert rankings.to_dict()["permitted_token_count"] == 10
