from __future__ import annotations

from pathlib import Path

import pytest

from mwpc_exact import (
    BenchmarkInstance,
    ExactBackend,
    SelectionStatus,
    SelectorKind,
    replay_benchmark_instance,
)

regular_cover = pytest.importorskip(
    "constrained_diffusion.regular_cover",
    reason="install the pinned EPIC CPU environment",
)
epic_profiler = pytest.importorskip(
    "constrained_diffusion.fast_enfa_profiler",
    reason="install the pinned EPIC CPU environment",
)
pytest.importorskip(
    "rustformlang.cfg",
    reason="install the pinned EPIC rustformlang binding",
)

FIXTURE_PATH = (
    Path(__file__).parents[1]
    / "exact_commit"
    / "fixtures"
    / "benchmark_instance_v1.json"
)


@pytest.mark.integration
def test_versioned_file_reconstructs_pinned_epic_cfg_and_replays_all_selectors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    allowed_words = frozenset({"a", "x", "b", "y"})

    def deterministic_cover(**kwargs: object) -> bool:
        words = kwargs["words_full"]
        assert isinstance(words, list)
        concrete_words = [word for word in words if word is not None]
        with epic_profiler.timer("regular_cover.generated_language"):
            allowed = bool(concrete_words) and all(
                word in allowed_words for word in concrete_words
            )
        with epic_profiler.timer("regular_cover.intersection"):
            return allowed

    monkeypatch.setattr(regular_cover, "cover_allows_words", deterministic_cover)
    monkeypatch.setenv("CONSTRAINED_DIFFUSION_REGULAR_COVER_EXACT", "0")
    monkeypatch.setenv("CONSTRAINED_DIFFUSION_REGULAR_COVER_MIN_BATCH", "2")

    instance = BenchmarkInstance.read_json(FIXTURE_PATH)
    results = replay_benchmark_instance(
        instance,
        backend=ExactBackend.PYTHON,
        brute_force_max_completions=1,
    )

    assert tuple(results) == (
        SelectorKind.SERIAL,
        SelectorKind.EPIC,
        SelectorKind.EXACT,
        SelectorKind.BRUTE_FORCE,
    )
    assert results[SelectorKind.SERIAL].status is SelectionStatus.FEASIBLE_ON_SUPPORT
    assert results[SelectorKind.EPIC].status is SelectionStatus.HEURISTIC
    assert results[SelectorKind.EXACT].status is SelectionStatus.OPTIMAL
    assert results[SelectorKind.BRUTE_FORCE].status is SelectionStatus.OPTIMAL
    assert results[SelectorKind.EXACT].score == results[SelectorKind.BRUTE_FORCE].score
    assert results[SelectorKind.EPIC].diagnostics["implementation"] == (
        "pinned_upstream_epic_regular_cover"
    )
