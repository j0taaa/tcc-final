from __future__ import annotations

import copy
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import cast

import pytest

import mwpc_exact.evaluation.epic_regular_cover as epic_module
from mwpc_exact import (
    BENCHMARK_INSTANCE_SCHEMA_VERSION,
    BenchmarkInstance,
    ExactBackend,
    ExactnessScope,
    SavedLogits,
    SelectionStatus,
    SelectorKind,
    SupportInputSource,
    SupportKind,
    UnsupportedBenchmarkSchemaVersion,
    migrate_benchmark_instance_data,
    replay_benchmark_instance,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "benchmark_instance_v1.json"


@dataclass(frozen=True)
class _FakeCandidate:
    index: int
    token_id: int
    word: object
    score: float = 0.0


def _load_raw_fixture() -> dict[str, object]:
    value = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return cast(dict[str, object], value)


def _install_select_all_epic(monkeypatch: pytest.MonkeyPatch) -> None:
    def select_all(**kwargs: object) -> object:
        return kwargs["candidates"]

    runtime = epic_module._EpicRuntime(
        candidate_factory=cast(epic_module._CandidateFactory, _FakeCandidate),
        select_batch=cast(epic_module._BatchSelector, select_all),
        minimum_batch_size=lambda: 2,
        exact_shrink_enabled=lambda: False,
        profiler_enabled=lambda: False,
        profiler_snapshot=lambda: {},
    )
    monkeypatch.setattr(epic_module, "_load_pinned_epic_runtime", lambda: runtime)


def test_versioned_fixture_round_trips_every_frozen_input_field(tmp_path: Path) -> None:
    instance = BenchmarkInstance.read_json(FIXTURE_PATH)

    assert BENCHMARK_INSTANCE_SCHEMA_VERSION == 1
    assert instance.instance_id == "t1003-axby-saved-logits-v1"
    assert instance.fingerprint == _load_raw_fixture()["instance_sha256"]
    assert instance.grammar.fingerprint == (
        "588f1b4a098114854703741df880add036d4f0fb521b5b85e09ee0804906ca8f"
    )
    assert instance.selection_input.canvas == (None, None, None, None)
    assert [proposal.weight for proposal in instance.selection_input.proposals] == [
        4.0,
        30.0,
        2.0,
        20.0,
    ]
    assert instance.selection_input.support.rows == ((10,), (11,), (12,), (13,))
    assert instance.saved_logits is not None
    assert instance.saved_logits.shape == (4, 14)
    assert instance.saved_logits.metadata["contains_model_weights"] is False
    assert "model_weights" not in instance.to_dict()

    destination = tmp_path / "round-trip.json"
    instance.write_json(destination)
    reloaded = BenchmarkInstance.read_json(destination)
    assert reloaded == instance
    assert reloaded.to_dict() == instance.to_dict()
    with pytest.raises(FileExistsError, match="already exists"):
        instance.write_json(destination)


def test_one_file_replays_serial_epic_exact_and_guarded_brute_force(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    instance = BenchmarkInstance.read_json(FIXTURE_PATH)
    _install_select_all_epic(monkeypatch)
    seen_cfg: list[tuple[str, str]] = []

    class _AlignedCfg:
        def accepts(self, words: list[str]) -> bool:
            return words == ["a", "x", "b", "y"]

    def cfg_factory(text: str, start_symbol: str) -> object:
        seen_cfg.append((text, start_symbol))
        return _AlignedCfg()

    results = replay_benchmark_instance(
        instance,
        backend=ExactBackend.PYTHON,
        brute_force_max_completions=1,
        epic_cfg_factory=cfg_factory,
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
    assert {result.score for result in results.values()} == {56.0}
    assert results[SelectorKind.EXACT].selected_proposal_ids == (0, 1, 2, 3)
    assert results[SelectorKind.BRUTE_FORCE].selected_proposal_ids == (0, 1, 2, 3)
    assert results[SelectorKind.EXACT].witness_token_ids == (10, 11, 12, 13)
    assert results[SelectorKind.BRUTE_FORCE].witness_token_ids == (10, 11, 12, 13)
    assert seen_cfg == [
        (
            "S -> A TAIL1\nTAIL1 -> X TAIL2\nTAIL2 -> B Y\nA -> a\nX -> x\nB -> b\nY -> y",
            "S",
        )
    ]


def test_schema_rejects_unknown_versions_fields_and_tampered_hashes() -> None:
    raw = _load_raw_fixture()

    newer = copy.deepcopy(raw)
    newer["schema_version"] = 2
    with pytest.raises(UnsupportedBenchmarkSchemaVersion, match="no deterministic migration"):
        migrate_benchmark_instance_data(newer)

    older = copy.deepcopy(raw)
    older["schema_version"] = 0
    with pytest.raises(UnsupportedBenchmarkSchemaVersion, match="no deterministic migration"):
        BenchmarkInstance.from_dict(older)

    unknown = copy.deepcopy(raw)
    unknown["model_weights"] = ["forbidden"]
    with pytest.raises(ValueError, match="unknown benchmark instance fields: model_weights"):
        BenchmarkInstance.from_dict(unknown)

    grammar_tamper = copy.deepcopy(raw)
    grammar = cast(dict[str, object], grammar_tamper["grammar"])
    cnf = cast(dict[str, object], grammar["cnf"])
    terminals = cast(list[dict[str, object]], cnf["terminals"])
    terminals[0]["label"] = 122
    with pytest.raises(ValueError, match="grammar_sha256 does not match"):
        BenchmarkInstance.from_dict(grammar_tamper)

    support_tamper = copy.deepcopy(raw)
    selection = cast(dict[str, object], support_tamper["selection_input"])
    support = cast(dict[str, object], selection["support"])
    support["rows"] = [[10, 11], [11], [12], [13]]
    with pytest.raises(ValueError, match="represented_support_sha256 does not match"):
        BenchmarkInstance.from_dict(support_tamper)


def test_saved_logits_have_portable_infinity_encoding_and_reject_nan() -> None:
    logits = SavedLogits(
        values=((float("-inf"), 0.0, float("inf")),),
        dtype="float32",
        source="unit_test",
    )

    encoded = logits.to_dict()
    assert encoded["values"] == [["-Infinity", 0.0, "Infinity"]]
    assert SavedLogits.from_dict(encoded) == logits
    with pytest.raises(ValueError, match="must be finite"):
        SavedLogits(values=((float("nan"),),), dtype="float32", source="unit_test")


def test_saved_logits_must_reproduce_serialized_top_k_ranking() -> None:
    instance = BenchmarkInstance.read_json(FIXTURE_PATH)
    support = replace(
        instance.selection_input.support,
        exactness_scope=ExactnessScope(
            kind=SupportKind.TOP_K,
            vocabulary_size=14,
            top_k=1,
            pruning_description="saved top-1 plus configured additions",
        ),
        input_source=SupportInputSource.LOGITS,
        top_k_token_ids_by_position=((10,), (11,), (12,), (13,)),
    )
    selection_input = replace(instance.selection_input, support=support)
    assert instance.saved_logits is not None
    consistent = replace(instance, selection_input=selection_input)
    assert consistent.saved_logits is instance.saved_logits

    changed_rows = [list(row) for row in instance.saved_logits.values]
    changed_rows[0][10] = -20.0
    changed_rows[0][11] = 20.0
    inconsistent_logits = replace(
        instance.saved_logits,
        values=tuple(tuple(row) for row in changed_rows),
    )
    with pytest.raises(ValueError, match="do not reproduce ranked top-K"):
        replace(
            instance,
            selection_input=selection_input,
            saved_logits=inconsistent_logits,
        )


def test_strict_json_loader_rejects_nonstandard_numeric_constants(tmp_path: Path) -> None:
    path = tmp_path / "nan.json"
    path.write_text('{"schema_version": NaN}', encoding="utf-8")

    with pytest.raises(ValueError, match="non-standard JSON numeric constant"):
        BenchmarkInstance.read_json(path)
