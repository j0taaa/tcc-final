from __future__ import annotations

from pathlib import Path

import pytest

from mwpc_exact import BenchmarkInstance, validate_semantic_alignment

FIXTURE = Path(__file__).parent / "fixtures" / "benchmark_instance_v1.json"


class _ExactFixtureCfg:
    def accepts(self, words: list[str]) -> bool:
        return words == ["a", "x", "b", "y"]


def test_recorded_alignment_recomputes_both_representations() -> None:
    instance = BenchmarkInstance.read_json(FIXTURE)
    report = validate_semantic_alignment(instance, _ExactFixtureCfg())
    assert report["checked_case_count"] == 5
    assert (
        report["alignment_sha256"]
        == (instance.expected_metadata["semantic_alignment"]["alignment_sha256"])
    )


def test_alignment_mismatch_blocks_comparison() -> None:
    class _WrongCfg:
        def accepts(self, words: list[str]) -> bool:
            return bool(words)

    with pytest.raises(ValueError, match="disagree"):
        validate_semantic_alignment(BenchmarkInstance.read_json(FIXTURE), _WrongCfg())
