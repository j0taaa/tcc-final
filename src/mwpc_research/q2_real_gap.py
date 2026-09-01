"""Portable real-state Q2 snapshots and common-selector replay."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from itertools import product
from math import fsum, isclose, isfinite, prod
from pathlib import Path
from typing import Any, cast

from mwpc_exact import (
    AlignmentCase,
    BenchmarkGrammar,
    BenchmarkInstance,
    CompositionalByteLevelAdapter,
    EOSMode,
    EOSPolicy,
    EpicReplaySpec,
    ExactBackend,
    Proposal,
    SelectionInput,
    SelectionResult,
    SelectionStatus,
    SelectorKind,
    SemanticAlignmentEvidence,
    SupportKind,
    SupportPolicy,
    build_per_position_support,
    replay_benchmark_instance,
)
from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.reference.recognizer import recognizes_cnf
from mwpc_research.statistical_summaries import summarize_gaps

Q2_REAL_SNAPSHOT_KIND = "mwpc_q2_real_selector_snapshot"
Q2_REAL_ROW_KIND = "mwpc_q2_real_state_gap_row"
Q2_REAL_SUMMARY_KIND = "mwpc_q2_real_state_gap_summary"
Q2_REAL_SCHEMA_VERSION = 1
Q2_REAL_SELECTORS = (
    "greedy_exact_feasibility",
    "epic_regular_cover",
    "exact_mwpc",
)

_SELECTOR_KIND = {
    "greedy_exact_feasibility": SelectorKind.GREEDY_EXACT_FEASIBILITY,
    "epic_regular_cover": SelectorKind.EPIC_REGULAR_COVER,
    "exact_mwpc": SelectorKind.EXACT_MWPC,
}


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(value, allow_nan=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def build_real_snapshot_instance(
    *,
    instance_id: str,
    grammar: CnfGrammar,
    target_token_ids: Sequence[int],
    canvas_token_ids: Sequence[int | None],
    predicted_token_ids: Sequence[int],
    confidence_values: Sequence[float],
    source_adapter: CompositionalByteLevelAdapter,
    decode_actual_token: Any,
    metadata: Mapping[str, object],
) -> BenchmarkInstance:
    """Compact one live selector state without changing its represented choices."""

    target_actual = tuple(int(value) for value in target_token_ids)
    canvas_actual = tuple(None if value is None else int(value) for value in canvas_token_ids)
    predicted_actual = tuple(int(value) for value in predicted_token_ids)
    confidence = tuple(float(value) for value in confidence_values)
    if not target_actual or len(canvas_actual) != len(target_actual):
        raise ValueError("real Q2 target and canvas must have the same positive slot count")
    if len(predicted_actual) != len(canvas_actual) or len(confidence) != len(canvas_actual):
        raise ValueError("real Q2 prediction arrays must match the canvas")
    for position, fixed in enumerate(canvas_actual):
        if fixed is not None and fixed != target_actual[position]:
            raise ValueError("real Q2 fixed canvas token differs from the target witness")
        if fixed is None and (not isfinite(confidence[position]) or confidence[position] < 0.0):
            raise ValueError("real Q2 masked-position confidence must be finite and non-negative")

    proposal_actual = {
        token_id
        for position, token_id in enumerate(predicted_actual)
        if canvas_actual[position] is None
        and token_id < source_adapter.vocabulary_size
        and source_adapter.emissions[token_id] is not None
    }
    actual_vocabulary = tuple(dict.fromkeys((*target_actual, *sorted(proposal_actual))))
    local_by_actual = {actual: local for local, actual in enumerate(actual_vocabulary)}
    emissions = tuple(source_adapter.emissions[actual] for actual in actual_vocabulary)
    if any(emission is None for emission in emissions):
        raise ValueError("real Q2 compact vocabulary must contain ordinary tokens only")
    adapter = CompositionalByteLevelAdapter(tuple(cast(bytes, item) for item in emissions))
    target_local = tuple(local_by_actual[token_id] for token_id in target_actual)
    canvas_local = tuple(
        None if token_id is None else local_by_actual[token_id] for token_id in canvas_actual
    )

    candidate_positions = sorted(
        (
            position
            for position, token_id in enumerate(predicted_actual)
            if canvas_actual[position] is None and token_id in local_by_actual
        ),
        key=lambda position: (-confidence[position], position),
    )
    proposals = tuple(
        Proposal(
            proposal_id=proposal_id,
            position=position,
            token_id=local_by_actual[predicted_actual[position]],
            weight=confidence[position],
            model_confidence=confidence[position],
        )
        for proposal_id, position in enumerate(candidate_positions)
    )
    explicit_rows: dict[int, tuple[int, ...]] = {}
    for position, fixed in enumerate(canvas_local):
        if fixed is not None:
            explicit_rows[position] = (fixed,)
            continue
        choices = [target_local[position]]
        predicted = predicted_actual[position]
        if predicted in local_by_actual:
            choices.append(local_by_actual[predicted])
        explicit_rows[position] = tuple(dict.fromkeys(choices))
    support = build_per_position_support(
        canvas=canvas_local,
        policy=SupportPolicy(
            kind=SupportKind.EXPLICIT,
            vocabulary_size=len(actual_vocabulary),
            permitted_token_ids=tuple(range(len(actual_vocabulary))),
            pruning_description=(
                "saved live model primary proposal plus independently known target witness token"
            ),
        ),
        explicit_support=explicit_rows,
        proposals=proposals,
    )
    grammar_id = f"q2-real/{instance_id}"
    token_symbols = tuple(f"q2tok{local}" for local in range(len(actual_vocabulary)))
    alignment_cases: list[AlignmentCase] = []
    accepted_symbol_sequences: list[str] = []
    for token_path in product(*support.rows):
        labels = tuple(
            label for token_id in token_path for label in cast(bytes, emissions[token_id])
        )
        accepts = recognizes_cnf(grammar, labels)
        alignment_cases.append(AlignmentCase(token_ids=token_path, expected_accepts=accepts))
        if accepts:
            accepted_symbol_sequences.append(
                " ".join(token_symbols[token_id] for token_id in token_path)
            )
    if not accepted_symbol_sequences:
        raise ValueError("real Q2 support omitted every grammar-valid target tokenization")
    negative_sentinel_added = not any(
        not case.expected_accepts for case in alignment_cases
    )
    if negative_sentinel_added:
        alignment_cases.append(AlignmentCase(token_ids=(), expected_accepts=False))
    epic_cfg_text = "S -> " + " | ".join(accepted_symbol_sequences)
    benchmark_grammar = BenchmarkGrammar(
        grammar_id=grammar_id,
        cnf=grammar,
        epic_cfg_text=epic_cfg_text,
        epic_start_symbol="S",
    )
    alignment = SemanticAlignmentEvidence(
        source_grammar_id=grammar_id,
        exact_compiler_version="mwpc_exact_literal_utf8_cnf_v1",
        epic_compiler_version="rustformlang_cfg_from_text_v1",
        method="exhaustive_saved_support_plus_optional_empty_negative_v1",
        cases=tuple(alignment_cases),
    )
    decoded_tokens = tuple((local, token_symbols[local]) for local in range(len(token_symbols)))
    words_full = tuple(
        None if token_id is None else decoded_tokens[token_id][1] for token_id in canvas_local
    )
    selection_input = SelectionInput(
        grammar=grammar,
        canvas=canvas_local,
        proposals=proposals,
        support=support,
        tokenizer_adapter=adapter,
        eos_policy=EOSPolicy(EOSMode.ABSENT),
    )
    snapshot_payload = {
        "actual_canvas_token_ids": list(canvas_actual),
        "actual_predicted_token_ids": list(predicted_actual),
        "confidence_values": [
            None if fixed is not None else confidence[position]
            for position, fixed in enumerate(canvas_actual)
        ],
        "actual_to_local_token_ids": [
            {"actual_token_id": actual, "local_token_id": local}
            for local, actual in enumerate(actual_vocabulary)
        ],
        "support_rows": [list(row) for row in support.rows],
        "proposal_ids": [proposal.proposal_id for proposal in proposals],
    }
    return BenchmarkInstance(
        instance_id=instance_id,
        grammar=benchmark_grammar,
        selection_input=selection_input,
        epic_replay=EpicReplaySpec(
            words_full=words_full,
            prompt_length=0,
            decoded_tokens=decoded_tokens,
            lex_map={symbol: symbol for symbol in token_symbols},
            terminals=token_symbols,
            subtokens={},
            supertokens={},
        ),
        metadata={
            **dict(metadata),
            "artifact_kind": Q2_REAL_SNAPSHOT_KIND,
            "schema_version": Q2_REAL_SCHEMA_VERSION,
            "snapshot_payload_sha256": _canonical_sha256(snapshot_payload),
            "snapshot_payload": snapshot_payload,
            "source_kind": "live_llada_epic_denoising_selector_state",
            "contains_model_weights": False,
            "support_interpretation": "explicit_primary_proposal_plus_target_witness",
            "alignment_negative_sentinel_added": negative_sentinel_added,
            "actual_token_decodings": [
                {
                    "actual_token_id": actual,
                    "decoded": str(decode_actual_token(actual)),
                    "epic_symbol": token_symbols[local],
                }
                for local, actual in enumerate(actual_vocabulary)
            ],
        },
        expected_metadata={
            "applicable_component_selectors": list(Q2_REAL_SELECTORS),
            "exactness_scope": "exact_on_support",
            "semantic_alignment": alignment.to_dict(),
        },
    )


def _baseline_subset_feasible(instance: BenchmarkInstance, result: SelectionResult) -> bool:
    proposals = {proposal.proposal_id: proposal for proposal in instance.selection_input.proposals}
    selected = tuple(proposals[proposal_id] for proposal_id in result.selected_proposal_ids)
    for token_path in product(*instance.selection_input.support.rows):
        if any(token_path[item.position] != item.token_id for item in selected):
            continue
        labels = tuple(
            label
            for token_id in token_path
            for label in (instance.selection_input.tokenizer_adapter.emissions[token_id] or ())
        )
        if recognizes_cnf(instance.grammar.cnf, labels):
            return True
    return False


def replay_real_snapshot(
    instance: BenchmarkInstance,
    *,
    timeout_seconds: float,
    maximum_support_combinations: int,
) -> dict[str, object]:
    """Replay three selectors and independently validate exact and baseline outputs."""

    serialized_instance = instance.to_dict()
    source_metadata = serialized_instance["metadata"]
    if not isinstance(source_metadata, Mapping):
        raise TypeError("real Q2 snapshot metadata must be a mapping")
    if maximum_support_combinations <= 0:
        raise ValueError("maximum support combinations must be positive")
    support_combinations = prod(len(row) for row in instance.selection_input.support.rows)
    if support_combinations > maximum_support_combinations:
        raise ValueError("real Q2 support exceeds the configured independent-validation limit")

    results = replay_benchmark_instance(
        instance,
        backend=ExactBackend.RUST,
        selector_timeout_seconds=timeout_seconds,
        brute_force_max_completions=1,
    )
    expected_status = {
        "greedy_exact_feasibility": SelectionStatus.FEASIBLE_ON_SUPPORT,
        "epic_regular_cover": SelectionStatus.HEURISTIC,
        "exact_mwpc": SelectionStatus.OPTIMAL,
    }
    selected: dict[str, SelectionResult] = {}
    for name, selector_kind in _SELECTOR_KIND.items():
        result = results[selector_kind]
        if result.status is not expected_status[name] or result.score is None:
            raise ValueError(f"real Q2 selector {name} returned {result.status.value}")
        selected[name] = result
    exact = selected["exact_mwpc"]
    assert exact.score is not None
    exact_score = exact.score
    selection_input = instance.selection_input
    emissions = selection_input.tokenizer_adapter.detokenize_bytes(exact.witness_token_ids)
    if not recognizes_cnf(selection_input.grammar, tuple(emissions)):
        raise ValueError("real Q2 exact witness failed independent CFG recognition")
    recomputed_ids = tuple(
        proposal.proposal_id
        for proposal in selection_input.proposals
        if proposal.weight > 0.0 and exact.witness_token_ids[proposal.position] == proposal.token_id
    )
    recomputed_score = fsum(
        proposal.weight
        for proposal in selection_input.proposals
        if proposal.proposal_id in recomputed_ids
    )
    if set(recomputed_ids) != set(exact.selected_proposal_ids) or not isclose(
        recomputed_score, exact_score, rel_tol=1e-12, abs_tol=1e-12
    ):
        raise ValueError("real Q2 exact witness score did not independently reproduce")
    solver = exact.diagnostics["solver_diagnostics"]
    if not isinstance(solver, Mapping):
        raise TypeError("real Q2 exact diagnostics omit solver details")
    certificate = solver.get("certificate_validation")
    if not isinstance(certificate, Mapping) or certificate.get("is_valid") is not True:
        raise ValueError("real Q2 exact certificate was not independently valid")

    selector_payloads: dict[str, object] = {}
    comparisons: dict[str, object] = {}
    for name, result in selected.items():
        payload = result.to_dict()
        payload["cardinality"] = len(result.selected_proposal_ids)
        if name != "exact_mwpc":
            feasible = _baseline_subset_feasible(instance, result)
            if not feasible:
                raise ValueError(f"real Q2 baseline {name} selected an infeasible subset")
            payload["selected_subset_feasible"] = True
            assert result.score is not None
            gap = max(0.0, exact_score - result.score)
            comparisons[name] = {
                "exact_score": exact_score,
                "heuristic_score": result.score,
                "absolute_gap": gap,
                "relative_gap": None if exact_score == 0.0 else gap / exact_score,
                "score_equal": isclose(exact_score, result.score, rel_tol=1e-12, abs_tol=1e-12),
            }
        selector_payloads[name] = payload
    return {
        "artifact_kind": Q2_REAL_ROW_KIND,
        "schema_version": Q2_REAL_SCHEMA_VERSION,
        "snapshot_id": instance.instance_id,
        "snapshot_sha256": instance.fingerprint,
        "source": dict(source_metadata),
        "support_sha256": selection_input.support.fingerprint,
        "support_combination_count": support_combinations,
        "support_specification": selection_input.support.exactness_scope.to_dict(),
        "selector_results": selector_payloads,
        "comparisons": comparisons,
        "independent_exact_validation": {
            "certificate_valid": True,
            "grammar_witness_valid": True,
            "objective_value": exact_score,
            "recomputed_objective_value": recomputed_score,
            "selected_proposal_ids": list(exact.selected_proposal_ids),
            "recomputed_selected_proposal_ids": list(recomputed_ids),
        },
    }


def summarize_real_rows(rows: Iterable[Mapping[str, object]]) -> dict[str, object]:
    records = tuple(dict(row) for row in rows)
    if not records:
        raise ValueError("real Q2 summary requires rows")
    comparison_payloads = tuple(
        cast(Mapping[str, Mapping[str, object]], row["comparisons"]) for row in records
    )
    source_payloads = tuple(cast(Mapping[str, object], row["source"]) for row in records)
    selector_payloads = tuple(
        cast(Mapping[str, Mapping[str, object]], row["selector_results"]) for row in records
    )
    validation_payloads = tuple(
        cast(Mapping[str, object], row["independent_exact_validation"]) for row in records
    )
    support_combination_counts = Counter(
        int(cast(int, row["support_combination_count"])) for row in records
    )
    non_singleton_support_count = sum(
        count for combinations, count in support_combination_counts.items() if combinations > 1
    )
    comparison_names = ("greedy_exact_feasibility", "epic_regular_cover")
    comparisons: dict[str, object] = {}
    for name in comparison_names:
        exact_scores = tuple(
            float(cast(float, payload[name]["exact_score"]))
            for payload in comparison_payloads
        )
        heuristic_scores = tuple(
            float(cast(float, payload[name]["heuristic_score"]))
            for payload in comparison_payloads
        )
        gap_summary = summarize_gaps(exact_scores, heuristic_scores).to_dict()
        equality = cast(dict[str, object], gap_summary["equality"])
        for field in (
            "confidence_interval_lower",
            "confidence_interval_method",
            "confidence_interval_upper",
            "confidence_level",
        ):
            equality.pop(field)
        equality["inference_policy"] = (
            "no_interval_non_iid_task_seed_state_corpus"
        )
        comparisons[name] = gap_summary
    return {
        "artifact_kind": Q2_REAL_SUMMARY_KIND,
        "schema_version": Q2_REAL_SCHEMA_VERSION,
        "snapshot_count": len(records),
        "support_combination_counts": {
            str(combinations): count
            for combinations, count in sorted(support_combination_counts.items())
        },
        "non_singleton_support_count": non_singleton_support_count,
        "empirical_interpretation": (
            "bounded_real_state_gap_sample"
            if non_singleton_support_count
            else "execution_alignment_check_all_supports_singleton_after_deduplication"
        ),
        "sampling_inference": "none_non_iid_task_seed_state_corpus",
        "task_counts": dict(
            sorted(Counter(str(payload["task_id"]) for payload in source_payloads).items())
        ),
        "seed_counts": dict(
            sorted(Counter(str(payload["seed"]) for payload in source_payloads).items())
        ),
        "status_counts_by_selector": {
            name: dict(
                sorted(
                    Counter(str(payload[name]["status"]) for payload in selector_payloads).items()
                )
            )
            for name in Q2_REAL_SELECTORS
        },
        "comparisons": comparisons,
        "zero_optimum_count": sum(
            float(cast(float, payload["objective_value"])) == 0.0
            for payload in validation_payloads
        ),
        "timeout_count": sum(
            any(payload[name]["status"] == "timeout" for name in Q2_REAL_SELECTORS)
            for payload in selector_payloads
        ),
        "failure_count": 0,
        "all_snapshots_common_across_selectors": True,
        "all_exact_certificates_independently_valid": True,
    }


def load_snapshot_jsonl(path: str | Path) -> tuple[BenchmarkInstance, ...]:
    return tuple(
        BenchmarkInstance.from_dict(json.loads(line))
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line
    )


__all__ = [
    "Q2_REAL_ROW_KIND",
    "Q2_REAL_SCHEMA_VERSION",
    "Q2_REAL_SELECTORS",
    "Q2_REAL_SNAPSHOT_KIND",
    "Q2_REAL_SUMMARY_KIND",
    "build_real_snapshot_instance",
    "load_snapshot_jsonl",
    "replay_real_snapshot",
    "summarize_real_rows",
]
