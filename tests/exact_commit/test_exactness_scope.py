from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest

from mwpc_exact import ExactnessScope, SolveStatus, SupportKind


def test_solver_statuses_are_distinct_and_complete() -> None:
    assert {status.value for status in SolveStatus} == {
        "optimal",
        "infeasible_on_support",
        "timeout",
        "unsupported",
        "error",
    }
    assert SolveStatus.TIMEOUT is not SolveStatus.INFEASIBLE_ON_SUPPORT


def test_top_k_requires_an_explicit_width() -> None:
    with pytest.raises(ValueError, match="requires top_k"):
        ExactnessScope(kind=SupportKind.TOP_K, vocabulary_size=32)


@pytest.mark.parametrize(
    "scope",
    [
        ExactnessScope(
            kind=SupportKind.FULL,
            vocabulary_size=32,
            included_special_tokens=(0, 31),
        ),
        ExactnessScope(
            kind=SupportKind.TOP_K,
            vocabulary_size=32,
            included_special_tokens=(0, 31),
            top_k=4,
            adaptive_expansions=(8, 16),
            pruning_description="per-slot model top-K plus required special tokens",
        ),
        ExactnessScope(
            kind=SupportKind.EXPLICIT,
            vocabulary_size=32,
            included_special_tokens=(0,),
            pruning_description="token IDs recorded with each lattice slot",
        ),
    ],
)
def test_scope_json_round_trip(scope: ExactnessScope) -> None:
    json_data = json.loads(json.dumps(scope.to_dict()))

    assert ExactnessScope.from_dict(json_data) == scope


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"kind": SupportKind.FULL, "vocabulary_size": 0}, "vocabulary_size"),
        (
            {
                "kind": SupportKind.TOP_K,
                "vocabulary_size": 32,
                "top_k": 33,
            },
            "top_k",
        ),
        (
            {
                "kind": SupportKind.FULL,
                "vocabulary_size": 32,
                "top_k": 4,
            },
            "cannot define top_k",
        ),
        (
            {
                "kind": SupportKind.EXPLICIT,
                "vocabulary_size": 32,
                "adaptive_expansions": (8,),
            },
            "cannot define adaptive_expansions",
        ),
        (
            {
                "kind": SupportKind.TOP_K,
                "vocabulary_size": 32,
                "top_k": 4,
                "adaptive_expansions": (16, 8),
            },
            "strictly increasing",
        ),
        (
            {
                "kind": SupportKind.FULL,
                "vocabulary_size": 32,
                "included_special_tokens": (32,),
            },
            "within the vocabulary",
        ),
        (
            {
                "kind": SupportKind.FULL,
                "vocabulary_size": 32,
                "included_special_tokens": (0, 0),
            },
            "must not contain duplicates",
        ),
    ],
)
def test_scope_rejects_invalid_metadata(kwargs: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        ExactnessScope(**kwargs)  # type: ignore[arg-type]


def test_scope_is_deeply_immutable() -> None:
    source_special_tokens = [0, 31]
    scope = ExactnessScope(
        kind=SupportKind.TOP_K,
        vocabulary_size=32,
        included_special_tokens=source_special_tokens,  # type: ignore[arg-type]
        top_k=4,
        adaptive_expansions=[8],  # type: ignore[arg-type]
    )
    source_special_tokens.append(1)

    assert scope.included_special_tokens == (0, 31)
    assert scope.adaptive_expansions == (8,)
    with pytest.raises(FrozenInstanceError):
        scope.top_k = 16  # type: ignore[misc]


def test_from_dict_rejects_unknown_fields() -> None:
    with pytest.raises(ValueError, match="unknown exactness scope fields"):
        ExactnessScope.from_dict(
            {"kind": "full", "vocabulary_size": 32, "unrecorded_pruning": True}
        )
