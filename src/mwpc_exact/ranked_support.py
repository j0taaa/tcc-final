"""Compact deterministic rankings for adaptive finite token support."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from math import isnan

from mwpc_exact.support import PerPositionSupport, SupportInputSource, SupportPolicy
from mwpc_exact.types import Proposal, SupportKind, aggregate_proposals


def _integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    return value


def _token_tuple(
    value: object,
    field_name: str,
    *,
    vocabulary_size: int,
    allow_empty: bool = False,
    canonical: bool = False,
) -> tuple[int, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise TypeError(f"{field_name} must be an iterable of token IDs")
    items = tuple(_integer(item, f"{field_name} item") for item in value)
    if not allow_empty and not items:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must not contain duplicate token IDs")
    if any(token_id < 0 or token_id >= vocabulary_size for token_id in items):
        raise ValueError(f"{field_name} contains a token outside the vocabulary")
    return tuple(sorted(items)) if canonical else items


@dataclass(frozen=True, slots=True)
class RankedSupportRows:
    """Top-ranked permitted token IDs retained without dense vocabulary logits."""

    vocabulary_size: int
    permitted_token_ids: tuple[int, ...]
    token_ids_by_position: tuple[tuple[int, ...], ...]
    max_k: int
    ranking_policy: str = "score_descending_then_token_id_ascending"
    source: str = "saved_dense_logits"

    def __post_init__(self) -> None:
        vocabulary_size = _integer(self.vocabulary_size, "vocabulary_size")
        if vocabulary_size <= 0:
            raise ValueError("vocabulary_size must be positive")
        max_k = _integer(self.max_k, "max_k")
        if max_k <= 0:
            raise ValueError("max_k must be positive")
        permitted = _token_tuple(
            self.permitted_token_ids,
            "permitted_token_ids",
            vocabulary_size=vocabulary_size,
            canonical=True,
        )
        if max_k > len(permitted):
            raise ValueError("max_k cannot exceed the permitted token count")
        if isinstance(self.token_ids_by_position, (str, bytes)) or not isinstance(
            self.token_ids_by_position, Sequence
        ):
            raise TypeError("token_ids_by_position must be a finite sequence")
        permitted_set = set(permitted)
        rows: list[tuple[int, ...]] = []
        for position, row in enumerate(self.token_ids_by_position):
            normalized = _token_tuple(
                row,
                f"ranked row {position}",
                vocabulary_size=vocabulary_size,
            )
            if len(normalized) != max_k:
                raise ValueError(f"ranked row {position} must contain exactly max_k tokens")
            if not set(normalized) <= permitted_set:
                raise ValueError(f"ranked row {position} contains a non-permitted token")
            rows.append(normalized)
        if not rows:
            raise ValueError("ranked support must contain at least one physical slot")
        if not isinstance(self.ranking_policy, str) or not self.ranking_policy:
            raise ValueError("ranking_policy must be a non-empty string")
        if not isinstance(self.source, str) or not self.source:
            raise ValueError("source must be a non-empty string")
        object.__setattr__(self, "vocabulary_size", vocabulary_size)
        object.__setattr__(self, "permitted_token_ids", permitted)
        object.__setattr__(self, "token_ids_by_position", tuple(rows))
        object.__setattr__(self, "max_k", max_k)

    @property
    def fingerprint(self) -> str:
        payload = {
            "vocabulary_size": self.vocabulary_size,
            "permitted_token_ids": list(self.permitted_token_ids),
            "token_ids_by_position": [list(row) for row in self.token_ids_by_position],
            "max_k": self.max_k,
            "ranking_policy": self.ranking_policy,
            "source": self.source,
        }
        encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return {
            "vocabulary_size": self.vocabulary_size,
            "permitted_token_count": len(self.permitted_token_ids),
            "slot_count": len(self.token_ids_by_position),
            "max_k": self.max_k,
            "ranking_policy": self.ranking_policy,
            "source": self.source,
            "ranked_rows_sha256": self.fingerprint,
        }


def rank_support_from_dense_logits(
    logits: Sequence[Sequence[float]],
    *,
    vocabulary_size: int,
    permitted_token_ids: Sequence[int],
    max_k: int,
    source: str = "saved_dense_logits",
) -> RankedSupportRows:
    """Rank only the configured prefix needed by every adaptive attempt."""

    vocabulary = _integer(vocabulary_size, "vocabulary_size")
    permitted = _token_tuple(
        permitted_token_ids,
        "permitted_token_ids",
        vocabulary_size=vocabulary,
        canonical=True,
    )
    width = _integer(max_k, "max_k")
    if width <= 0 or width > len(permitted):
        raise ValueError("max_k must be in [1, permitted token count]")
    if isinstance(logits, (str, bytes)) or not isinstance(logits, Sequence):
        raise TypeError("logits must be a finite position-by-vocabulary sequence")
    rankings: list[tuple[int, ...]] = []
    for position, raw_row in enumerate(logits):
        if isinstance(raw_row, (str, bytes)) or not isinstance(raw_row, Sequence):
            raise TypeError(f"logit row {position} must be a finite sequence")
        if len(raw_row) != vocabulary:
            raise ValueError(f"logit row {position} must contain exactly {vocabulary} scores")
        scores: list[float] = []
        for token_id, value in enumerate(raw_row):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"logit at ({position}, {token_id}) must be real")
            score = float(value)
            if isnan(score):
                raise ValueError(f"logit at ({position}, {token_id}) must not be NaN")
            scores.append(score)
        rankings.append(
            tuple(sorted(permitted, key=lambda token_id: (-scores[token_id], token_id))[:width])
        )
    return RankedSupportRows(
        vocabulary_size=vocabulary,
        permitted_token_ids=permitted,
        token_ids_by_position=tuple(rankings),
        max_k=width,
        source=source,
    )


def build_per_position_support_from_rankings(
    *,
    canvas: Sequence[int | None],
    policy: SupportPolicy,
    rankings: RankedSupportRows,
    proposals: Iterable[Proposal] = (),
) -> PerPositionSupport:
    """Build one adaptive support attempt from prefixes of a frozen ranking."""

    if not isinstance(policy, SupportPolicy):
        raise TypeError("policy must be a SupportPolicy")
    if not isinstance(rankings, RankedSupportRows):
        raise TypeError("rankings must be RankedSupportRows")
    if policy.kind not in {SupportKind.TOP_K, SupportKind.FULL}:
        raise ValueError("ranked support can construct only TOP_K or FULL policies")
    if policy.vocabulary_size != rankings.vocabulary_size:
        raise ValueError("policy and ranked support must have equal vocabularies")
    permitted = policy.permitted_token_ids
    if permitted is None or tuple(permitted) != rankings.permitted_token_ids:
        raise ValueError("policy and ranked support must use the same permitted token universe")
    if isinstance(canvas, (str, bytes)) or not isinstance(canvas, Sequence):
        raise TypeError("canvas must be a finite sequence")
    if len(canvas) != len(rankings.token_ids_by_position):
        raise ValueError("canvas and ranked support must have equal slot counts")
    canvas_items: list[int | None] = []
    for position, token_id in enumerate(canvas):
        if token_id is None:
            canvas_items.append(None)
        else:
            normalized = _integer(token_id, f"canvas token at position {position}")
            if normalized not in rankings.permitted_token_ids:
                raise ValueError(f"fixed token at position {position} is not permitted")
            canvas_items.append(normalized)
    canvas_tuple = tuple(canvas_items)

    proposal_items = tuple(proposals)
    aggregate_proposals(proposal_items)
    permitted_set = set(rankings.permitted_token_ids)
    proposal_tokens: list[set[int]] = [set() for _ in canvas_tuple]
    for proposal in proposal_items:
        if proposal.position >= len(canvas_tuple):
            raise ValueError(f"proposal {proposal.proposal_id} is outside the finite canvas")
        if proposal.token_id not in permitted_set:
            raise ValueError(f"proposal {proposal.proposal_id} uses a non-permitted token")
        fixed = canvas_tuple[proposal.position]
        if fixed is not None and fixed != proposal.token_id:
            raise ValueError(f"proposal {proposal.proposal_id} conflicts with a fixed token")
        if policy.include_proposal_tokens:
            proposal_tokens[proposal.position].add(proposal.token_id)

    top_k_rows: list[tuple[int, ...]] = []
    rows: list[tuple[int, ...]] = []
    specials = set(policy.required_special_token_ids)
    if policy.kind is SupportKind.TOP_K:
        effective_k = policy.effective_top_k
        if effective_k is None or effective_k > rankings.max_k:
            raise ValueError("the requested adaptive width exceeds the frozen ranking")
    else:
        effective_k = None
        if rankings.max_k != len(rankings.permitted_token_ids):
            raise ValueError("FULL support requires a ranking over every permitted token")

    for position, fixed in enumerate(canvas_tuple):
        if fixed is not None:
            rows.append((fixed,))
            top_k_rows.append(())
            continue
        if policy.kind is SupportKind.FULL:
            ranked: tuple[int, ...] = ()
            represented = set(rankings.permitted_token_ids)
        else:
            assert effective_k is not None
            ranked = rankings.token_ids_by_position[position][:effective_k]
            represented = set(ranked)
        represented.update(specials)
        represented.update(proposal_tokens[position])
        rows.append(tuple(sorted(represented)))
        top_k_rows.append(ranked)

    proposal_rows = tuple(
        tuple(sorted(items)) if policy.include_proposal_tokens else () for items in proposal_tokens
    )
    return PerPositionSupport(
        canvas=canvas_tuple,
        rows=tuple(rows),
        permitted_token_ids=rankings.permitted_token_ids,
        exactness_scope=policy.exactness_scope,
        input_source=SupportInputSource.LOGITS,
        top_k_token_ids_by_position=tuple(top_k_rows),
        proposal_token_ids_by_position=proposal_rows,
        proposal_token_inclusion_enabled=policy.include_proposal_tokens,
    )


__all__ = [
    "RankedSupportRows",
    "build_per_position_support_from_rankings",
    "rank_support_from_dense_logits",
]
