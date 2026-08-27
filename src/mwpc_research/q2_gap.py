"""Deterministic Q2 component-selector gap cases and computed artifacts."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from itertools import product
from math import fsum, isclose
from pathlib import Path
from time import perf_counter
from types import MappingProxyType
from typing import cast

from mwpc_exact import (
    AlignmentCase,
    BenchmarkGrammar,
    BenchmarkInstance,
    CompositionalByteLevelAdapter,
    EOSMode,
    EOSPolicy,
    EpicReplaySpec,
    ProposalWeightMode,
    SavedLogits,
    SelectionInput,
    SelectionResult,
    SelectionStatus,
    SelectorKind,
    SemanticAlignmentEvidence,
    SupportKind,
    SupportPolicy,
    build_per_position_support,
    build_schedule_proposals,
)
from mwpc_exact.experiments.artifacts import prepare_artifact_directories
from mwpc_exact.reference.grammar import (
    BinaryProduction,
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)
from mwpc_exact.reference.recognizer import recognizes_cnf

Q2_ARTIFACT_SCHEMA_VERSION = 1
Q2_RAW_ARTIFACT_KIND = "mwpc_q2_heuristic_gap_row"
Q2_SUMMARY_ARTIFACT_KIND = "mwpc_q2_heuristic_gap_summary"
Q2_RAW_FILENAME = "q2-gap-rows.jsonl"
Q2_SUMMARY_FILENAME = "q2-gap-summary.json"

Q2_COMPONENT_SELECTORS = (
    "greedy_exact_feasibility",
    "epic_regular_cover",
    "exact_mwpc",
)
Q2_CASE_IDS = (
    "all-compatible",
    "adversarial-one-vs-two",
    "adversarial-weight-mode-divergence",
)

_RESULT_KIND_BY_NAME = {
    "greedy_exact_feasibility": SelectorKind.GREEDY_EXACT_FEASIBILITY,
    "epic_regular_cover": SelectorKind.EPIC_REGULAR_COVER,
    "exact_mwpc": SelectorKind.EXACT_MWPC,
}
_EXPECTED_STATUS_BY_NAME = {
    "greedy_exact_feasibility": SelectionStatus.FEASIBLE_ON_SUPPORT,
    "epic_regular_cover": SelectionStatus.HEURISTIC,
    "exact_mwpc": SelectionStatus.OPTIMAL,
}
_BASELINE_NAMES = Q2_COMPONENT_SELECTORS[:2]

ReplayCallable = Callable[
    [BenchmarkInstance],
    Mapping[SelectorKind, SelectionResult],
]


@dataclass(frozen=True, slots=True)
class _Q2CaseSpec:
    common_instance_id: str
    case_kind: str
    seed: int
    grammar: CnfGrammar
    epic_cfg_text: str
    epic_start_symbol: str
    vocabulary: tuple[str, ...]
    support_rows: tuple[tuple[int, ...], ...]
    predicted_token_ids: tuple[int, ...]
    confidences: tuple[float, ...]
    accepted_alignment_cases: tuple[tuple[int, ...], ...]
    rejected_alignment_cases: tuple[tuple[int, ...], ...]


@dataclass(frozen=True, slots=True)
class Q2WeightedInstance:
    """One common synthetic state under one explicitly recorded weight mode."""

    common_instance_id: str
    case_kind: str
    seed: int
    weight_mode: ProposalWeightMode
    common_state_sha256: str
    benchmark_instance: BenchmarkInstance

    def __post_init__(self) -> None:
        if not isinstance(self.common_instance_id, str) or not self.common_instance_id:
            raise ValueError("common_instance_id must be non-empty")
        if self.case_kind not in {"canonical", "crafted_adversarial"}:
            raise ValueError("case_kind must identify canonical or crafted_adversarial input")
        if not isinstance(self.weight_mode, ProposalWeightMode):
            raise TypeError("weight_mode must be a ProposalWeightMode")
        if len(self.common_state_sha256) != 64:
            raise ValueError("common_state_sha256 must be a SHA-256 digest")
        if not isinstance(self.benchmark_instance, BenchmarkInstance):
            raise TypeError("benchmark_instance must be a BenchmarkInstance")


@dataclass(frozen=True, slots=True)
class Q2GapRecord:
    """One computed selector comparison for one state and weight mode."""

    common_instance_id: str
    evaluated_instance_id: str
    case_kind: str
    seed: int
    weight_mode: ProposalWeightMode
    common_state_sha256: str
    weighted_instance_sha256: str
    grammar_sha256: str
    support_sha256: str
    support_specification: Mapping[str, object]
    success: bool
    selector_results: Mapping[str, Mapping[str, object]]
    comparisons: Mapping[str, Mapping[str, object]]
    oracle_validation: Mapping[str, object]
    fixture_file: str | None = None
    failure_file: str | None = None
    error_type: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.weight_mode, ProposalWeightMode):
            raise TypeError("weight_mode must be a ProposalWeightMode")
        if not isinstance(self.success, bool):
            raise TypeError("success must be a boolean")
        for name in (
            "support_specification",
            "selector_results",
            "comparisons",
            "oracle_validation",
        ):
            object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))

    def to_dict(self, *, run_metadata: Mapping[str, object]) -> dict[str, object]:
        return {
            "artifact_kind": Q2_RAW_ARTIFACT_KIND,
            "schema_version": Q2_ARTIFACT_SCHEMA_VERSION,
            "common_instance_id": self.common_instance_id,
            "evaluated_instance_id": self.evaluated_instance_id,
            "case_kind": self.case_kind,
            "seed": self.seed,
            "weight_mode": self.weight_mode.value,
            "common_state_sha256": self.common_state_sha256,
            "weighted_instance_sha256": self.weighted_instance_sha256,
            "grammar_sha256": self.grammar_sha256,
            "support_sha256": self.support_sha256,
            "support_specification": dict(self.support_specification),
            "success": self.success,
            "selector_results": {
                name: dict(result) for name, result in self.selector_results.items()
            },
            "comparisons": {
                name: dict(comparison) for name, comparison in self.comparisons.items()
            },
            "oracle_validation": dict(self.oracle_validation),
            "fixture_file": self.fixture_file,
            "failure_file": self.failure_file,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "run_metadata": dict(run_metadata),
        }


@dataclass(frozen=True, slots=True)
class Q2ExperimentResult:
    """Q2 rows plus aggregates derived only from successful row payloads."""

    records: tuple[Q2GapRecord, ...]
    run_metadata: Mapping[str, object]

    def __post_init__(self) -> None:
        records = tuple(self.records)
        if not records:
            raise ValueError("Q2 experiment requires at least one record")
        keys = {(record.common_instance_id, record.weight_mode) for record in records}
        if len(keys) != len(records):
            raise ValueError("Q2 rows must have unique instance and weight-mode pairs")
        object.__setattr__(self, "records", records)
        object.__setattr__(self, "run_metadata", MappingProxyType(dict(self.run_metadata)))

    @property
    def failed_cases(self) -> int:
        return sum(not record.success for record in self.records)

    def summary_dict(self) -> dict[str, object]:
        """Compute equality rates and gap aggregates from recorded row data."""

        successful = tuple(record for record in self.records if record.success)
        modes: dict[str, object] = {}
        for mode in ProposalWeightMode:
            mode_records = tuple(record for record in successful if record.weight_mode is mode)
            selector_summaries: dict[str, object] = {}
            for selector_name in Q2_COMPONENT_SELECTORS:
                measurements = tuple(
                    record.selector_results[selector_name] for record in mode_records
                )
                selector_summary: dict[str, object] = {
                    "case_count": len(measurements),
                    "status_counts": _string_counts(
                        str(measurement["status"]) for measurement in measurements
                    ),
                    "total_score": fsum(cast(float, item["score"]) for item in measurements),
                    "total_cardinality": sum(
                        cast(int, item["cardinality"]) for item in measurements
                    ),
                    "total_runtime_seconds": fsum(
                        cast(float, item["runtime_seconds"]) for item in measurements
                    ),
                }
                if selector_name in _BASELINE_NAMES:
                    comparisons = tuple(
                        record.comparisons[selector_name] for record in mode_records
                    )
                    equality_count = sum(bool(item["score_equal"]) for item in comparisons)
                    absolute_gaps = tuple(cast(float, item["absolute_gap"]) for item in comparisons)
                    relative_gaps = tuple(cast(float, item["relative_gap"]) for item in comparisons)
                    selector_summary["equality_count"] = equality_count
                    selector_summary["equality_rate"] = (
                        equality_count / len(comparisons) if comparisons else None
                    )
                    selector_summary["mean_absolute_gap"] = _mean(absolute_gaps)
                    selector_summary["maximum_absolute_gap"] = (
                        max(absolute_gaps) if absolute_gaps else None
                    )
                    selector_summary["mean_relative_gap"] = _mean(relative_gaps)
                    selector_summary["maximum_relative_gap"] = (
                        max(relative_gaps) if relative_gaps else None
                    )
                selector_summaries[selector_name] = selector_summary
            modes[mode.value] = {
                "case_count": len(mode_records),
                "selectors": selector_summaries,
            }

        return {
            "artifact_kind": Q2_SUMMARY_ARTIFACT_KIND,
            "schema_version": Q2_ARTIFACT_SCHEMA_VERSION,
            "case_count": len(self.records),
            "passed_cases": len(successful),
            "failed_cases": self.failed_cases,
            "common_instance_count": len({record.common_instance_id for record in self.records}),
            "case_kind_counts": _string_counts(record.case_kind for record in self.records),
            "weight_modes": modes,
            "failures": [
                {
                    "common_instance_id": record.common_instance_id,
                    "weight_mode": record.weight_mode.value,
                    "error_type": record.error_type,
                    "error_message": record.error_message,
                    "fixture_file": record.fixture_file,
                    "failure_file": record.failure_file,
                }
                for record in self.records
                if not record.success
            ],
            "run_metadata": dict(self.run_metadata),
        }


def configured_q2_instances(
    *,
    seed_start: int,
    weight_modes: Iterable[ProposalWeightMode],
) -> tuple[Q2WeightedInstance, ...]:
    """Build every configured synthetic state under each requested objective."""

    if isinstance(seed_start, bool) or not isinstance(seed_start, int) or seed_start < 0:
        raise ValueError("seed_start must be a non-negative integer")
    modes = tuple(weight_modes)
    if not modes or not all(isinstance(mode, ProposalWeightMode) for mode in modes):
        raise ValueError("weight_modes must contain ProposalWeightMode values")
    if len(set(modes)) != len(modes):
        raise ValueError("weight_modes must not repeat values")
    specs = _configured_case_specs(seed_start)
    return tuple(_weighted_instance(spec, weight_mode) for spec in specs for weight_mode in modes)


def run_q2_gap_instances(
    instances: Iterable[Q2WeightedInstance],
    *,
    replay: ReplayCallable,
    run_metadata: Mapping[str, object],
    failure_directory: str | Path | None = None,
    run_timeout_seconds: float | None = None,
    clock: Callable[[], float] = perf_counter,
) -> Q2ExperimentResult:
    """Replay all component selectors, failing closed on incomparable output."""

    if not callable(replay):
        raise TypeError("replay must be callable")
    items = tuple(instances)
    if not items or not all(isinstance(item, Q2WeightedInstance) for item in items):
        raise ValueError("instances must contain at least one Q2WeightedInstance")
    if run_timeout_seconds is not None and run_timeout_seconds <= 0.0:
        raise ValueError("run_timeout_seconds must be positive or None")
    failure_path = None if failure_directory is None else Path(failure_directory)
    if failure_path is not None:
        failure_path.mkdir(parents=True, exist_ok=True)
    started = clock()
    records: list[Q2GapRecord] = []
    for item in items:
        benchmark = item.benchmark_instance
        try:
            if run_timeout_seconds is not None and clock() - started >= run_timeout_seconds:
                raise TimeoutError("Q2 total run deadline expired before this instance")
            results = replay(benchmark)
            selector_results, comparisons, oracle = _validated_gap_payload(
                benchmark,
                results,
            )
        except Exception as error:
            fixture_file, failure_file = _write_failure_fixture(
                item,
                error,
                failure_path,
            )
            records.append(
                _record(
                    item,
                    success=False,
                    selector_results={},
                    comparisons={},
                    oracle_validation={},
                    fixture_file=fixture_file,
                    failure_file=failure_file,
                    error_type=type(error).__name__,
                    error_message=str(error),
                )
            )
            continue
        records.append(
            _record(
                item,
                success=True,
                selector_results=selector_results,
                comparisons=comparisons,
                oracle_validation=oracle,
            )
        )
    return Q2ExperimentResult(records=tuple(records), run_metadata=run_metadata)


def write_q2_artifacts(
    result: Q2ExperimentResult,
    raw_directory: str | Path,
    processed_directory: str | Path,
) -> tuple[Path, Path]:
    """Write immutable JSONL separately from its computed summary."""

    if not isinstance(result, Q2ExperimentResult):
        raise TypeError("result must be a Q2ExperimentResult")
    raw_output, processed_output = prepare_artifact_directories(
        raw_directory,
        processed_directory,
    )
    raw_path = raw_output / Q2_RAW_FILENAME
    summary_path = processed_output / Q2_SUMMARY_FILENAME
    if raw_path.exists() or summary_path.exists():
        raise FileExistsError("refusing to overwrite Q2 raw or processed artifacts")
    with raw_path.open("x", encoding="utf-8") as output:
        for record in result.records:
            output.write(
                json.dumps(
                    record.to_dict(run_metadata=result.run_metadata),
                    allow_nan=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
                + "\n"
            )
    with summary_path.open("x", encoding="utf-8") as output:
        json.dump(result.summary_dict(), output, allow_nan=False, indent=2, sort_keys=True)
        output.write("\n")
    return raw_path, summary_path


def _record(
    item: Q2WeightedInstance,
    *,
    success: bool,
    selector_results: Mapping[str, Mapping[str, object]],
    comparisons: Mapping[str, Mapping[str, object]],
    oracle_validation: Mapping[str, object],
    fixture_file: str | None = None,
    failure_file: str | None = None,
    error_type: str | None = None,
    error_message: str | None = None,
) -> Q2GapRecord:
    benchmark = item.benchmark_instance
    selection_input = benchmark.selection_input
    return Q2GapRecord(
        common_instance_id=item.common_instance_id,
        evaluated_instance_id=benchmark.instance_id,
        case_kind=item.case_kind,
        seed=item.seed,
        weight_mode=item.weight_mode,
        common_state_sha256=item.common_state_sha256,
        weighted_instance_sha256=benchmark.fingerprint,
        grammar_sha256=benchmark.grammar.fingerprint,
        support_sha256=selection_input.support.fingerprint,
        support_specification=selection_input.support.exactness_scope.to_dict(),
        success=success,
        selector_results=selector_results,
        comparisons=comparisons,
        oracle_validation=oracle_validation,
        fixture_file=fixture_file,
        failure_file=failure_file,
        error_type=error_type,
        error_message=error_message,
    )


def _validated_gap_payload(
    benchmark: BenchmarkInstance,
    results: Mapping[SelectorKind, SelectionResult],
) -> tuple[
    dict[str, Mapping[str, object]],
    dict[str, Mapping[str, object]],
    dict[str, object],
]:
    required_kinds = {*_RESULT_KIND_BY_NAME.values(), SelectorKind.BRUTE_FORCE}
    if set(results) != required_kinds:
        raise ValueError("Q2 replay did not return exactly the required selectors and oracle")
    scope = benchmark.selection_input.support.exactness_scope
    for result in results.values():
        if result.exactness_scope != scope:
            raise ValueError("Q2 selectors did not retain the common support scope")
    for name, expected_status in _EXPECTED_STATUS_BY_NAME.items():
        result = results[_RESULT_KIND_BY_NAME[name]]
        if result.status is not expected_status:
            raise ValueError(
                f"{name} returned {result.status.value}; expected {expected_status.value}"
            )
        if result.score is None:
            raise ValueError(f"{name} returned no comparable score")

    exact = results[SelectorKind.EXACT_MWPC]
    oracle = results[SelectorKind.BRUTE_FORCE]
    if oracle.status is not SelectionStatus.OPTIMAL or oracle.score is None:
        raise ValueError("Q2 brute-force validation did not return OPTIMAL with a score")
    if exact.score is None or not isclose(exact.score, oracle.score, rel_tol=1e-12, abs_tol=1e-12):
        raise AssertionError("Q2 exact MWPC score disagrees with brute force")
    if not exact.token_witness_available or not oracle.token_witness_available:
        raise AssertionError("Q2 exact and brute-force validation require token witnesses")

    selector_payloads = {
        name: _selector_payload(name, results[kind]) for name, kind in _RESULT_KIND_BY_NAME.items()
    }
    comparisons: dict[str, Mapping[str, object]] = {}
    for name in _BASELINE_NAMES:
        baseline = results[_RESULT_KIND_BY_NAME[name]]
        if baseline.score is None:
            raise AssertionError("validated Q2 baseline unexpectedly lost its score")
        if not _selected_subset_is_feasible(benchmark, baseline):
            raise AssertionError(f"{name} selected proposals have no valid completion")
        selector_payloads[name] = {
            **selector_payloads[name],
            "selected_subset_feasible": True,
        }
        gap = exact.score - baseline.score
        if gap < -1e-12:
            raise AssertionError(f"{name} score exceeds the independently verified optimum")
        gap = max(0.0, gap)
        relative_gap = 0.0 if exact.score == 0.0 else gap / exact.score
        comparisons[name] = {
            "exact_selector": "exact_mwpc",
            "heuristic_selector": name,
            "exact_score": exact.score,
            "heuristic_score": baseline.score,
            "exact_cardinality": len(exact.selected_proposal_ids),
            "heuristic_cardinality": len(baseline.selected_proposal_ids),
            "absolute_gap": gap,
            "relative_gap": relative_gap,
            "score_equal": isclose(
                exact.score,
                baseline.score,
                rel_tol=1e-12,
                abs_tol=1e-12,
            ),
        }
    return (
        selector_payloads,
        comparisons,
        {
            "selector": "brute_force",
            "status": oracle.status.value,
            "score": oracle.score,
            "cardinality": len(oracle.selected_proposal_ids),
            "runtime_seconds": oracle.runtime_seconds,
            "score_equal_to_exact": True,
            "certificate_available": oracle.token_witness_available,
        },
    )


def _selector_payload(name: str, result: SelectionResult) -> Mapping[str, object]:
    payload = result.to_dict()
    legacy_selector_id = payload.pop("selector")
    payload.update(
        selector=name,
        legacy_selector_id=legacy_selector_id,
        cardinality=len(result.selected_proposal_ids),
    )
    return payload


def _selected_subset_is_feasible(
    benchmark: BenchmarkInstance,
    result: SelectionResult,
) -> bool:
    """Independently enumerate a completion matching a baseline's selected IDs."""

    selection_input = benchmark.selection_input
    if selection_input.eos_policy.mode is not EOSMode.ABSENT:
        raise ValueError("Q2 selected-subset enumeration currently requires absent EOS semantics")
    proposal_by_id = {proposal.proposal_id: proposal for proposal in selection_input.proposals}
    try:
        selected = tuple(
            proposal_by_id[proposal_id] for proposal_id in result.selected_proposal_ids
        )
    except KeyError as error:
        raise ValueError("Q2 selector returned an unknown proposal ID") from error
    for token_path in product(*selection_input.support.rows):
        if any(token_path[proposal.position] != proposal.token_id for proposal in selected):
            continue
        labels: list[int] = []
        for token_id in token_path:
            emission = selection_input.tokenizer_adapter.emissions[token_id]
            if emission is None:
                raise ValueError("Q2 direct feasibility audit requires ordinary byte tokens")
            labels.extend(emission)
        if recognizes_cnf(selection_input.grammar, tuple(labels)):
            return True
    return False


def _write_failure_fixture(
    item: Q2WeightedInstance,
    error: Exception,
    failure_directory: Path | None,
) -> tuple[str | None, str | None]:
    if failure_directory is None:
        return None, None
    stem = f"{item.common_instance_id}-{item.weight_mode.value}"
    fixture_name = f"{stem}.json"
    failure_name = f"{stem}.failure.json"
    item.benchmark_instance.write_json(failure_directory / fixture_name)
    (failure_directory / failure_name).write_text(
        json.dumps(
            {
                "schema_version": Q2_ARTIFACT_SCHEMA_VERSION,
                "common_instance_id": item.common_instance_id,
                "weight_mode": item.weight_mode.value,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "fixture_file": fixture_name,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return fixture_name, failure_name


def _weighted_instance(
    spec: _Q2CaseSpec,
    weight_mode: ProposalWeightMode,
) -> Q2WeightedInstance:
    canvas = (None,) * len(spec.predicted_token_ids)
    proposal_batch = build_schedule_proposals(
        predicted_token_ids=spec.predicted_token_ids,
        confidence_values=spec.confidences,
        schedule_mask=(True,) * len(canvas),
        k_s=len(canvas),
        weight_mode=weight_mode,
    )
    adapter = CompositionalByteLevelAdapter(
        tuple(token.encode("ascii") for token in spec.vocabulary)
    )
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(
            kind=SupportKind.EXPLICIT,
            vocabulary_size=len(spec.vocabulary),
            permitted_token_ids=tuple(range(len(spec.vocabulary))),
            pruning_description="Q2 configured explicit per-position synthetic support",
        ),
        explicit_support={position: row for position, row in enumerate(spec.support_rows)},
        proposals=proposal_batch.proposals,
    )
    grammar_id = f"q2/{spec.common_instance_id}-v1"
    grammar = BenchmarkGrammar(
        grammar_id=grammar_id,
        cnf=spec.grammar,
        epic_cfg_text=spec.epic_cfg_text,
        epic_start_symbol=spec.epic_start_symbol,
    )
    alignment = SemanticAlignmentEvidence(
        source_grammar_id=grammar_id,
        exact_compiler_version="mwpc_exact_handwritten_cnf_v1",
        epic_compiler_version="rustformlang_cfg_from_text_v1",
        method="configured_bounded_token_sequences_v1",
        cases=tuple(
            AlignmentCase(token_ids=token_ids, expected_accepts=True)
            for token_ids in spec.accepted_alignment_cases
        )
        + tuple(
            AlignmentCase(token_ids=token_ids, expected_accepts=False)
            for token_ids in spec.rejected_alignment_cases
        ),
    )
    selection_input = SelectionInput(
        grammar=spec.grammar,
        canvas=canvas,
        proposals=proposal_batch.proposals,
        support=support,
        tokenizer_adapter=adapter,
        eos_policy=EOSPolicy(EOSMode.ABSENT),
    )
    logits = tuple(
        tuple(
            confidence if token_id == proposed_token_id else 0.0
            for token_id in range(len(spec.vocabulary))
        )
        for proposed_token_id, confidence in zip(
            spec.predicted_token_ids,
            spec.confidences,
            strict=True,
        )
    )
    benchmark = BenchmarkInstance(
        instance_id=f"q2-{spec.common_instance_id}-{weight_mode.value}-v1",
        grammar=grammar,
        selection_input=selection_input,
        saved_logits=SavedLogits(
            values=logits,
            dtype="float64",
            source="configured_synthetic_confidence_matrix",
            metadata={"contains_model_weights": False, "seed": spec.seed},
        ),
        epic_replay=EpicReplaySpec(
            words_full=canvas,
            prompt_length=0,
            decoded_tokens=tuple(enumerate(spec.vocabulary)),
            lex_map={token: token for token in spec.vocabulary},
            terminals=spec.vocabulary,
            subtokens={},
            supertokens={},
        ),
        metadata={
            "source_kind": "configured_synthetic_q2_state",
            "seed": spec.seed,
            "case_kind": spec.case_kind,
            "weight_mode": weight_mode.value,
            "proposal_policy": proposal_batch.diagnostics,
            "model_id": "not_applicable",
            "model_revision": "synthetic_q2_generator_v1",
            "tokenizer_id": "generated_raw_byte_vocabulary",
            "tokenizer_revision": "q2_generator_v1",
        },
        expected_metadata={
            "applicable_component_selectors": list(Q2_COMPONENT_SELECTORS),
            "exactness_scope": "exact_on_support",
            "semantic_alignment": alignment.to_dict(),
        },
    )
    common_state_payload = {
        "common_instance_id": spec.common_instance_id,
        "grammar_sha256": grammar.fingerprint,
        "canvas": list(canvas),
        "support_sha256": support.fingerprint,
        "proposal_positions": [proposal.position for proposal in proposal_batch.proposals],
        "proposal_token_ids": [proposal.token_id for proposal in proposal_batch.proposals],
        "model_confidences": [proposal.model_confidence for proposal in proposal_batch.proposals],
    }
    common_state_sha256 = hashlib.sha256(
        json.dumps(common_state_payload, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()
    return Q2WeightedInstance(
        common_instance_id=spec.common_instance_id,
        case_kind=spec.case_kind,
        seed=spec.seed,
        weight_mode=weight_mode,
        common_state_sha256=common_state_sha256,
        benchmark_instance=benchmark,
    )


def _configured_case_specs(seed_start: int) -> tuple[_Q2CaseSpec, ...]:
    return (
        _Q2CaseSpec(
            common_instance_id="all-compatible",
            case_kind="canonical",
            seed=seed_start,
            grammar=_abc_grammar(),
            epic_cfg_text=("S -> A TAIL\nTAIL -> B C\nA -> a\nB -> b\nC -> c"),
            epic_start_symbol="S",
            vocabulary=("a", "b", "c"),
            support_rows=((0,), (1,), (2,)),
            predicted_token_ids=(0, 1, 2),
            confidences=(0.9, 0.8, 0.7),
            accepted_alignment_cases=((0, 1, 2),),
            rejected_alignment_cases=((0, 1), (0, 2, 1)),
        ),
        _Q2CaseSpec(
            common_instance_id="adversarial-one-vs-two",
            case_kind="crafted_adversarial",
            seed=seed_start + 1,
            grammar=_one_vs_two_grammar(),
            epic_cfg_text=(
                "S -> A AXTAIL | X XBCTAIL\n"
                "AXTAIL -> X X\nXBCTAIL -> B C\n"
                "A -> a\nX -> x\nB -> b\nC -> c"
            ),
            epic_start_symbol="S",
            vocabulary=("a", "x", "b", "c"),
            support_rows=((0, 1), (1, 2), (1, 3)),
            predicted_token_ids=(0, 2, 3),
            confidences=(0.9, 0.6, 0.5),
            accepted_alignment_cases=((0, 1, 1), (1, 2, 3)),
            rejected_alignment_cases=((0, 2, 3), (1, 1, 1)),
        ),
        _Q2CaseSpec(
            common_instance_id="adversarial-weight-mode-divergence",
            case_kind="crafted_adversarial",
            seed=seed_start + 2,
            grammar=_one_vs_two_grammar(),
            epic_cfg_text=(
                "S -> A AXTAIL | X XBCTAIL\n"
                "AXTAIL -> X X\nXBCTAIL -> B C\n"
                "A -> a\nX -> x\nB -> b\nC -> c"
            ),
            epic_start_symbol="S",
            vocabulary=("a", "x", "b", "c"),
            support_rows=((0, 1), (1, 2), (1, 3)),
            predicted_token_ids=(0, 2, 3),
            confidences=(0.9, 0.4, 0.3),
            accepted_alignment_cases=((0, 1, 1), (1, 2, 3)),
            rejected_alignment_cases=((0, 2, 3), (1, 1, 1)),
        ),
    )


def _abc_grammar() -> CnfGrammar:
    return CnfGrammar(
        nonterminals=tuple(
            Nonterminal(index, name) for index, name in enumerate(("S", "A", "B", "C", "TAIL"))
        ),
        terminals=tuple(Terminal(index, ord(label)) for index, label in enumerate("abc")),
        start_nonterminal_id=0,
        terminal_productions=tuple(
            TerminalProduction(index, index + 1, index) for index in range(3)
        ),
        binary_productions=(
            BinaryProduction(3, 0, 1, 4),
            BinaryProduction(4, 4, 2, 3),
        ),
    )


def _one_vs_two_grammar() -> CnfGrammar:
    return CnfGrammar(
        nonterminals=tuple(
            Nonterminal(index, name)
            for index, name in enumerate(("S", "A", "X", "B", "C", "AXTAIL", "XBCTAIL"))
        ),
        terminals=tuple(Terminal(index, ord(label)) for index, label in enumerate("axbc")),
        start_nonterminal_id=0,
        terminal_productions=tuple(
            TerminalProduction(index, index + 1, index) for index in range(4)
        ),
        binary_productions=(
            BinaryProduction(4, 0, 1, 5),
            BinaryProduction(5, 0, 2, 6),
            BinaryProduction(6, 5, 2, 2),
            BinaryProduction(7, 6, 3, 4),
        ),
    )


def _string_counts(values: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _mean(values: Sequence[float]) -> float | None:
    return fsum(values) / len(values) if values else None


__all__ = [
    "Q2_ARTIFACT_SCHEMA_VERSION",
    "Q2_CASE_IDS",
    "Q2_COMPONENT_SELECTORS",
    "Q2_RAW_ARTIFACT_KIND",
    "Q2_RAW_FILENAME",
    "Q2_SUMMARY_ARTIFACT_KIND",
    "Q2_SUMMARY_FILENAME",
    "Q2ExperimentResult",
    "Q2GapRecord",
    "Q2WeightedInstance",
    "configured_q2_instances",
    "run_q2_gap_instances",
    "write_q2_artifacts",
]
