"""Task-specific M13 result selection and deterministic LaTeX rendering."""

from __future__ import annotations

import hashlib
import json
import statistics
import tomllib
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

ARTICLE_RESULT_SCHEMA_VERSION = 1
ARTICLE_RESULTS_FILENAME = "article-results.json"
ARTICLE_VALUES_FILENAME = "article-result-values.tex"
R1_FILENAME = "r1-correctness-finite-slots.tex"
R2_FILENAME = "r2-heuristic-gap.tex"
R3_FILENAME = "r3-scaling-integration.tex"

_EXPECTED_ROLES = {
    "t1203_results",
    "q1_rows",
    "q2_real_summary",
    "q4_publication_summary",
    "q4_publication_rows",
    "q5_publication_summary",
    "q5_publication_rows",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise TypeError(f"{field} must be a string-keyed mapping")
    return cast(Mapping[str, object], value)


def _sequence(value: object, field: str) -> Sequence[object]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{field} must be a sequence")
    return cast(Sequence[object], value)


def _integer(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field} must be an integer")
    return value


def _number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field} must be numeric")
    return float(value)


def _string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise TypeError(f"{field} must be a non-empty string")
    return value


def _boolean(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{field} must be boolean")
    return value


def _load_json(path: Path) -> Mapping[str, object]:
    return _mapping(json.loads(path.read_text(encoding="utf-8")), path.as_posix())


def _load_jsonl(path: Path) -> tuple[Mapping[str, object], ...]:
    return tuple(
        _mapping(json.loads(line), f"{path}:{line_number}")
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if line
    )


def _within(root: Path, relative: Path, field: str) -> Path:
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"{field} must be repository-relative")
    result = (root / relative).resolve()
    if not result.is_relative_to(root):
        raise ValueError(f"{field} resolves outside the repository")
    return result


def _load_config(path: Path, root: Path) -> tuple[str, Path, Path, dict[str, Path], list[object]]:
    raw = _mapping(tomllib.loads(path.read_text(encoding="utf-8")), "article config")
    if _integer(raw.get("schema_version"), "schema_version") != ARTICLE_RESULT_SCHEMA_VERSION:
        raise ValueError("unsupported article-result schema version")
    artifact_id = _string(raw.get("artifact_id"), "artifact_id")
    processed = _within(
        root, Path(_string(raw.get("processed_directory"), "processed_directory")), "processed"
    )
    paper = _within(root, Path(_string(raw.get("paper_directory"), "paper_directory")), "paper")
    inputs: dict[str, Path] = {}
    source_records: list[object] = []
    for index, item_value in enumerate(_sequence(raw.get("inputs"), "inputs")):
        item = _mapping(item_value, f"inputs[{index}]")
        role = _string(item.get("role"), f"inputs[{index}].role")
        if role in inputs:
            raise ValueError(f"duplicate article input role: {role}")
        relative = Path(_string(item.get("path"), f"inputs[{index}].path"))
        expected = _string(item.get("expected_sha256"), f"inputs[{index}].expected_sha256")
        resolved = _within(root, relative, f"inputs[{index}].path")
        observed = _sha256(resolved)
        if observed != expected:
            raise ValueError(f"article input hash mismatch for {role}: {observed} != {expected}")
        inputs[role] = resolved
        source_records.append({"role": role, "path": relative.as_posix(), "sha256": observed})
    if set(inputs) != _EXPECTED_ROLES:
        raise ValueError("article inputs must contain every required evidence role exactly once")
    return artifact_id, processed, paper, inputs, source_records


def _families(final_results: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    correctness = _mapping(final_results["correctness"], "correctness")
    return {
        _string(row["family"], "family"): row
        for value in _sequence(correctness["families"], "correctness.families")
        for row in (_mapping(value, "correctness family"),)
    }


def _synthetic_gaps(final_results: Mapping[str, object]) -> list[dict[str, object]]:
    heuristic = _mapping(final_results["heuristic_gap"], "heuristic_gap")
    result: list[dict[str, object]] = []
    for value in _sequence(heuristic["gap_rows"], "heuristic_gap.gap_rows"):
        row = _mapping(value, "synthetic gap row")
        stats = _mapping(row["statistics"], "synthetic gap statistics")
        equality = _mapping(stats["equality"], "synthetic equality")
        absolute = _mapping(stats["absolute_gap"], "synthetic absolute gap")
        relative = _mapping(stats["relative_gap"], "synthetic relative gap")
        result.append(
            {
                "weight_mode": _string(row["weight_mode"], "weight_mode"),
                "selector": _string(row["selector"], "selector"),
                "comparisons": _integer(stats["comparison_count"], "comparison_count"),
                "equal": _integer(equality["event_count"], "event_count"),
                "median_absolute_gap": _number(absolute["median"], "absolute median"),
                "median_relative_gap": _number(relative["median"], "relative median"),
            }
        )
    return result


def _q4_summary(
    summary: Mapping[str, object], rows: Sequence[Mapping[str, object]]
) -> dict[str, object]:
    if not _boolean(summary["all_optimal_certificates_independently_rechecked"], "q4 certs"):
        raise ValueError("Q4 certificates were not independently rechecked")
    if _integer(summary["backend_mismatch_count"], "q4 mismatches") != 0:
        raise ValueError("Q4 backend mismatch blocks article generation")

    graph_rows: dict[tuple[str, int], Mapping[str, object]] = {}
    for value in _sequence(summary["scaling_series"], "q4 scaling series"):
        point = _mapping(value, "q4 scaling point")
        if point["axis"] == "graph_size_scale":
            graph_rows[
                (_string(point["backend"], "q4 backend"), _integer(point["axis_value"], "axis"))
            ] = point

    backend_rows: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        if row["status"] != "optimal" or _boolean(row["censored"], "q4 censored"):
            continue
        backend_rows[_string(row["backend"], "q4 backend")].append(row)

    backends: dict[str, object] = {}
    for backend in ("python", "rust"):
        selected = backend_rows[backend]
        component_values: dict[str, list[float]] = defaultdict(list)
        max_rss = 0
        for row in selected:
            memory = _mapping(row["memory"], "q4 memory")
            max_rss = max(max_rss, _integer(memory["peak_worker_rss_bytes"], "q4 RSS"))
            profile = _mapping(row["observed_profile"], "q4 profile")
            timings = _mapping(profile["timings_seconds"], "q4 timings")
            for name, value in _mapping(timings["components"], "q4 components").items():
                component_values[name].append(_number(value, f"q4 component {name}"))
            component_values["unattributed_measurement_overhead"].append(
                _number(timings["unattributed_measurement_overhead"], "q4 unattributed")
            )
        medians = {name: statistics.median(values) for name, values in component_values.items()}
        named = {
            name: value for name, value in medians.items() if not name.startswith("unattributed")
        }
        dominant_named = max(named, key=named.__getitem__)
        dominant_all = max(medians, key=medians.__getitem__)
        endpoints: dict[str, object] = {}
        for axis_value in (1, 8):
            point = graph_rows[(backend, axis_value)]
            runtime = _mapping(point["runtime_seconds"], "q4 runtime")
            endpoints[str(axis_value)] = {
                "median_ms": _number(runtime["median"], "q4 median") * 1000.0,
                "iqr_ms": _number(runtime["iqr"], "q4 IQR") * 1000.0,
            }
        backends[backend] = {
            "successful_rows": len(selected),
            "compound_graph_size_endpoints": endpoints,
            "maximum_peak_worker_rss_mib": max_rss / (1024.0**2),
            "dominant_recorded_component": dominant_all,
            "dominant_recorded_component_median_ms": medians[dominant_all] * 1000.0,
            "dominant_named_component": dominant_named,
            "dominant_named_component_median_ms": medians[dominant_named] * 1000.0,
        }

    counters = [
        _mapping(_mapping(row["sizes"], "q4 sizes")["counters"], "q4 counters") for row in rows
    ]
    return {
        "measurement_count": _integer(summary["measurement_count"], "q4 measurements"),
        "point_count": _integer(summary["point_count"], "q4 points"),
        "repetitions_per_backend_point": _integer(
            summary["configured_repetitions_per_backend_point"], "q4 repetitions"
        ),
        "backend_comparison_count": _integer(summary["backend_comparison_count"], "q4 comparisons"),
        "backend_mismatch_count": _integer(summary["backend_mismatch_count"], "q4 mismatch"),
        "timeout_count": _integer(summary["timeout_count"], "q4 timeout"),
        "censored_count": _integer(summary["censored_count"], "q4 censored"),
        "error_count": _integer(summary["error_count"], "q4 errors"),
        "graph_size_scale_interpretation": _string(
            summary["graph_size_scale_interpretation"], "q4 graph interpretation"
        ),
        "maximum_terminal_graph_nodes": max(
            _integer(row["terminal_graph_node_count"], "graph nodes") for row in counters
        ),
        "maximum_terminal_graph_edges": max(
            _integer(row["terminal_graph_edge_count"], "graph edges") for row in counters
        ),
        "maximum_chart_entries": max(
            _integer(row["chart_entries"], "chart entries") for row in counters
        ),
        "backends": backends,
    }


def _q5_summary(
    summary: Mapping[str, object], rows: Sequence[Mapping[str, object]]
) -> dict[str, object]:
    if not _boolean(summary["all_constrained_outputs_independently_valid"], "q5 validity"):
        raise ValueError("Q5 constrained outputs were not independently valid")
    if not _boolean(
        summary["all_exact_optimizer_certificates_independently_valid"], "q5 certificates"
    ):
        raise ValueError("Q5 exact certificates were not independently valid")
    if not _boolean(
        summary["epic_parallel_commit_observed_in_every_task_seed"], "q5 EPIC batching"
    ):
        raise ValueError("Q5 did not exercise EPIC batching in every task/seed")

    tasks: dict[str, object] = {}
    for task_id in ("json_x_zero", "fenced_add_dsl"):
        task_rows = [
            row
            for row in rows
            if _mapping(row["run_metadata"], "q5 metadata")["selected_task_id"] == task_id
        ]
        strategies: dict[str, object] = {}
        for strategy in ("unconstrained", "serial", "epic", "exact"):
            selected = [row for row in task_rows if row["strategy"] == strategy]
            elapsed = [
                _number(_mapping(row["resources"], "q5 resources")["elapsed_seconds"], "elapsed")
                for row in selected
            ]
            strategies[strategy] = {
                "generation_count": len(selected),
                "valid_count": sum(
                    _boolean(row["syntactic_valid"], "syntactic_valid")
                    and _boolean(row["functional_success"], "functional_success")
                    for row in selected
                ),
                "median_runtime_ms": statistics.median(elapsed) * 1000.0,
                "fallback_event_count": sum(
                    _integer(
                        _mapping(row["generation"], "generation")["fallback_count"],
                        "fallback",
                    )
                    for row in selected
                ),
                "maximum_cuda_allocated_gib": max(
                    _integer(
                        _mapping(row["resources"], "q5 resources")["cuda_peak_allocated_bytes"],
                        "cuda bytes",
                    )
                    for row in selected
                )
                / (1024.0**3),
            }
        epic_rows = [row for row in task_rows if row["strategy"] == "epic"]
        exact_rows = [row for row in task_rows if row["strategy"] == "exact"]
        epic_calls = sum(
            _integer(
                _mapping(row["diagnostics"], "q5 diagnostics")["regular_cover_selector_calls"],
                "EPIC calls",
            )
            for row in epic_rows
        )
        epic_batches = [
            _integer(value, "EPIC batch")
            for row in epic_rows
            for value in _sequence(
                _mapping(row["diagnostics"], "q5 diagnostics")["regular_cover_batch_sizes"],
                "EPIC batches",
            )
        ]
        exact_certificates = sum(
            _mapping(row["exact_solver"], "exact solver")["certificate_valid"] is True
            for row in exact_rows
        )
        serial_runtime = _number(
            _mapping(strategies["serial"], "serial strategy")["median_runtime_ms"], "serial runtime"
        )
        exact_runtime = _number(
            _mapping(strategies["exact"], "exact strategy")["median_runtime_ms"], "exact runtime"
        )
        tasks[task_id] = {
            "strategies": strategies,
            "constrained_valid_count": sum(
                _integer(_mapping(strategies[name], name)["valid_count"], "valid count")
                for name in ("serial", "epic", "exact")
            ),
            "constrained_generation_count": sum(
                _integer(_mapping(strategies[name], name)["generation_count"], "generation count")
                for name in ("serial", "epic", "exact")
            ),
            "epic_regular_cover_selector_calls": epic_calls,
            "epic_maximum_batch_size": max(epic_batches),
            "exact_certificate_count": exact_certificates,
            "exact_to_serial_median_runtime_ratio": exact_runtime / serial_runtime,
        }
    return {
        "measured_row_count": _integer(summary["measured_row_count"], "q5 rows"),
        "task_count": len(_sequence(summary["tasks"], "q5 tasks")),
        "seed_count": len(_sequence(summary["seeds"], "q5 seeds")),
        "strategy_count": len({_string(row["strategy"], "q5 strategy") for row in rows}),
        "exact_optimizer_step_count": _integer(
            summary["exact_optimizer_step_count"], "q5 exact steps"
        ),
        "contract_failure_count": _integer(summary["contract_failure_count"], "q5 failures"),
        "tasks": tasks,
    }


def _build_summary(
    artifact_id: str,
    config_relative: str,
    config_sha256: str,
    sources: list[object],
    inputs: Mapping[str, Path],
) -> dict[str, object]:
    final_results = _load_json(inputs["t1203_results"])
    q1_rows = _load_jsonl(inputs["q1_rows"])
    q2_real = _load_json(inputs["q2_real_summary"])
    q4_publication = _load_json(inputs["q4_publication_summary"])
    q4_rows = _load_jsonl(inputs["q4_publication_rows"])
    q5_publication = _load_json(inputs["q5_publication_summary"])
    q5_rows = _load_jsonl(inputs["q5_publication_rows"])

    families = _families(final_results)
    correctness = _mapping(final_results["correctness"], "correctness")
    if _integer(correctness["failed_case_count"], "failed cases") != 0:
        raise ValueError("Q1 disagreement blocks article generation")
    certificate_validations = sum(
        _integer(
            _mapping(row["property_checks"], "property checks").get("certificate_validation", 0),
            "certificate validations",
        )
        for row in q1_rows
    )
    q3 = _mapping(final_results["finite_slots"], "finite slots")
    q2_comparisons = _mapping(q2_real["comparisons"], "real Q2 comparisons")
    return {
        "artifact_kind": "mwpc_m1301_article_results",
        "schema_version": ARTICLE_RESULT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "configuration": {"path": config_relative, "sha256": config_sha256},
        "sources": sources,
        "r1": {
            "families": list(families.values()),
            "failed_case_count": _integer(correctness["failed_case_count"], "failed cases"),
            "slot_count_minimum": min(
                _integer(_mapping(row["sizes"], "q1 sizes")["slot_count"], "slots")
                for row in q1_rows
            ),
            "slot_count_maximum": max(
                _integer(_mapping(row["sizes"], "q1 sizes")["slot_count"], "slots")
                for row in q1_rows
            ),
            "enumerated_paths_maximum": max(
                _integer(_mapping(row["sizes"], "q1 sizes")["enumerated_token_paths"], "paths")
                for row in q1_rows
            ),
            "independent_certificate_validation_count": certificate_validations,
            "finite_slot_cases": q3["cases"],
        },
        "r2": {
            "synthetic_interpretation": _mapping(final_results["heuristic_gap"], "heuristic gap")[
                "interpretation"
            ],
            "synthetic_rows": _synthetic_gaps(final_results),
            "real_snapshot_count": _integer(q2_real["snapshot_count"], "real snapshots"),
            "real_non_singleton_support_count": _integer(
                q2_real["non_singleton_support_count"], "non-singleton supports"
            ),
            "real_timeout_count": _integer(q2_real["timeout_count"], "real timeouts"),
            "real_failure_count": _integer(q2_real["failure_count"], "real failures"),
            "real_comparisons": q2_comparisons,
            "real_interpretation": q2_real["empirical_interpretation"],
        },
        "r3": {
            "q4": _q4_summary(q4_publication, q4_rows),
            "q5": _q5_summary(q5_publication, q5_rows),
        },
    }


def _macro(name: str, value: object) -> str:
    return f"\\newcommand{{\\{name}}}{{{value}}}"


def _render_values(summary: Mapping[str, object]) -> bytes:
    r1 = _mapping(summary["r1"], "r1")
    r2 = _mapping(summary["r2"], "r2")
    r3 = _mapping(summary["r3"], "r3")
    q4 = _mapping(r3["q4"], "q4")
    q5 = _mapping(r3["q5"], "q5")
    q4_backends = _mapping(q4["backends"], "q4 backends")
    q5_tasks = _mapping(q5["tasks"], "q5 tasks")
    py = _mapping(q4_backends["python"], "python")
    rust = _mapping(q4_backends["rust"], "rust")
    json_task = _mapping(q5_tasks["json_x_zero"], "json task")
    dsl_task = _mapping(q5_tasks["fenced_add_dsl"], "dsl task")
    q1_case_count = sum(
        _integer(_mapping(value, "family")["case_count"], "cases")
        for value in _sequence(r1["families"], "families")
        if _mapping(value, "family")["family"] != "overall"
    )
    python_named_ms = _number(py["dominant_named_component_median_ms"], "python component")
    rust_named_ms = _number(rust["dominant_named_component_median_ms"], "rust component")
    rust_overhead_ms = _number(rust["dominant_recorded_component_median_ms"], "rust overhead")
    json_ratio = _number(json_task["exact_to_serial_median_runtime_ratio"], "json ratio")
    dsl_ratio = _number(dsl_task["exact_to_serial_median_runtime_ratio"], "dsl ratio")
    families = {
        _string(row["family"], "family"): row
        for value in _sequence(r1["families"], "families")
        for row in (_mapping(value, "family"),)
    }
    overall_statuses = _mapping(families["overall"]["oracle_status_counts"], "overall statuses")
    finite_cases = [
        _mapping(value, "finite case")
        for value in _sequence(r1["finite_slot_cases"], "finite cases")
    ]
    synthetic = {
        (_string(row["weight_mode"], "weight mode"), _string(row["selector"], "selector")): row
        for value in _sequence(r2["synthetic_rows"], "synthetic rows")
        for row in (_mapping(value, "synthetic row"),)
    }
    unit_serial_gap = _number(
        synthetic[("unit", "greedy_exact_feasibility")]["median_absolute_gap"],
        "unit serial gap",
    )
    unit_epic_gap = _number(
        synthetic[("unit", "epic_regular_cover")]["median_absolute_gap"],
        "unit EPIC gap",
    )
    confidence_epic_gap = _number(
        synthetic[("confidence", "epic_regular_cover")]["median_absolute_gap"],
        "confidence EPIC gap",
    )
    lines = [
        "% Generated by scripts/exact_commit/build_article_results.py; do not edit.",
        _macro("MThirteenQOneCases", q1_case_count),
        _macro("MThirteenQOneFailures", r1["failed_case_count"]),
        _macro("MThirteenQOneMinSlots", r1["slot_count_minimum"]),
        _macro("MThirteenQOneMaxSlots", r1["slot_count_maximum"]),
        _macro("MThirteenQOneMaxPaths", r1["enumerated_paths_maximum"]),
        _macro("MThirteenQOneCertificateChecks", r1["independent_certificate_validation_count"]),
        _macro("MThirteenQOneOptimalCases", overall_statuses["optimal"]),
        _macro(
            "MThirteenQThreeAvailableSlots",
            finite_cases[0]["available_physical_slots"],
        ),
        _macro(
            "MThirteenQThreeRequiredTokens",
            finite_cases[0]["minimum_required_physical_tokens"],
        ),
        _macro(
            "MThirteenQTwoUnitSerialGap",
            f"{unit_serial_gap:.1f}",
        ),
        _macro(
            "MThirteenQTwoUnitEpicGap",
            f"{unit_epic_gap:.1f}",
        ),
        _macro(
            "MThirteenQTwoConfidenceEpicGap",
            f"{confidence_epic_gap:.1f}",
        ),
        _macro("MThirteenQTwoRealSnapshots", r2["real_snapshot_count"]),
        _macro("MThirteenQTwoNonSingleton", r2["real_non_singleton_support_count"]),
        _macro("MThirteenQFourMeasurements", q4["measurement_count"]),
        _macro("MThirteenQFourPoints", q4["point_count"]),
        _macro("MThirteenQFourRepetitions", q4["repetitions_per_backend_point"]),
        _macro("MThirteenQFourComparisons", q4["backend_comparison_count"]),
        _macro("MThirteenQFourTimeouts", q4["timeout_count"]),
        _macro("MThirteenQFourCensored", q4["censored_count"]),
        _macro("MThirteenQFourMismatches", q4["backend_mismatch_count"]),
        _macro("MThirteenQFourMaxNodes", q4["maximum_terminal_graph_nodes"]),
        _macro("MThirteenQFourMaxEdges", q4["maximum_terminal_graph_edges"]),
        _macro("MThirteenQFourMaxChart", q4["maximum_chart_entries"]),
        _macro("MThirteenQFourPythonNamedMs", f"{python_named_ms:.3f}"),
        _macro("MThirteenQFourRustNamedMs", f"{rust_named_ms:.3f}"),
        _macro("MThirteenQFourRustOverheadMs", f"{rust_overhead_ms:.3f}"),
        _macro("MThirteenQFiveRows", q5["measured_row_count"]),
        _macro("MThirteenQFiveTasks", q5["task_count"]),
        _macro("MThirteenQFiveSeeds", q5["seed_count"]),
        _macro("MThirteenQFiveStrategies", q5["strategy_count"]),
        _macro("MThirteenQFiveExactCertificates", q5["exact_optimizer_step_count"]),
        _macro(
            "MThirteenQFiveEpicMaxBatch",
            max(
                _integer(_mapping(value, "q5 task")["epic_maximum_batch_size"], "EPIC batch")
                for value in q5_tasks.values()
            ),
        ),
        _macro("MThirteenQFiveJsonRatio", f"{json_ratio:.3f}"),
        _macro("MThirteenQFiveDslRatio", f"{dsl_ratio:.3f}"),
    ]
    return ("\n".join(lines) + "\n").encode()


def _family_row(families: Mapping[str, Mapping[str, object]], family: str, label: str) -> str:
    row = families[family]
    agreement = _mapping(row["agreement"], f"{family} agreement")
    count = _integer(row["case_count"], f"{family} cases")
    interval = "--"
    if family == "randomized":
        lower = _number(agreement["confidence_interval_lower"], "Wilson lower") * 100.0
        upper = _number(agreement["confidence_interval_upper"], "Wilson upper") * 100.0
        interval = f"[{lower:.1f}, {upper:.1f}]"
    statuses = _mapping(row["oracle_status_counts"], f"{family} statuses")
    return (
        f"{label} & {count} & {_integer(agreement['event_count'], 'agreements')}/{count} & "
        f"{interval} & {_integer(statuses['optimal'], 'optimal')}/"
        f"{_integer(statuses['infeasible_on_support'], 'infeasible')} \\\\"
    )


def _render_r1(summary: Mapping[str, object]) -> bytes:
    r1 = _mapping(summary["r1"], "r1")
    families = {
        _string(row["family"], "family"): row
        for value in _sequence(r1["families"], "r1 families")
        for row in (_mapping(value, "r1 family"),)
    }
    cases = [
        _mapping(value, "finite-slot case")
        for value in _sequence(r1["finite_slot_cases"], "finite cases")
    ]
    lines = [
        "% Generated by scripts/exact_commit/build_article_results.py; do not edit.",
        r"\begin{table}[t]",
        r"\centering",
        (
            r"\caption{R1: exhaustive-oracle agreement and finite-slot "
            r"counterexamples. All decisions are per-step "
            r"\texttt{exact\_on\_support}.}"
        ),
        r"\label{tab:r1-correctness-finite-slots}",
        r"\scriptsize",
        r"\begin{tabular}{p{4.0cm}rrrr}",
        r"\toprule",
        r"Q1 family & Cases & Agreement & 95\% CI & OPT/INF \\ \midrule",
        _family_row(families, "canonical", "Canonical configured set"),
        _family_row(families, "exhaustive", "Exhaustive configured family"),
        _family_row(families, "randomized", "Randomized seeds"),
        _family_row(families, "overall", "Overall configured cases"),
        r"\midrule",
        r"Q3 counterexample & Slots & Abstract & Finite & Objective \\ \midrule",
    ]
    first, second = cases
    lines.extend(
        (
            f"Required EOS cannot fit & {_integer(first['available_physical_slots'], 'slots')} & "
            f"accepted & INF & -- \\\\ ",
            "Slots force EOS-only witness & "
            f"{_integer(second['available_physical_slots'], 'slots')} & "
            f"accepted & OPT & {_number(second['finite_objective_value'], 'objective'):.1f} \\\\ ",
            r"\bottomrule",
            r"\end{tabular}",
            (
                r"\par\footnotesize Wilson CI applies only to randomized seeds; fixed and "
                r"mixed rows are complete configured counts. OPT/INF denotes "
                r"\texttt{OPTIMAL}/\texttt{INFEASIBLE\_ON\_SUPPORT}. The 167 optima produced "
                r"334 independent certificate validations; neither Q3 row timed out."
            ),
            r"\end{table}",
        )
    )
    return ("\n".join(lines) + "\n").encode()


def _selector_label(value: str) -> str:
    return "Serial greedy" if value == "greedy_exact_feasibility" else "EPIC regular cover"


def _render_r2(summary: Mapping[str, object]) -> bytes:
    r2 = _mapping(summary["r2"], "r2")
    lines = [
        "% Generated by scripts/exact_commit/build_article_results.py; do not edit.",
        r"\begin{table}[t]",
        r"\centering",
        (
            r"\caption{R2: paired heuristic gaps on illustrative synthetic states "
            r"and saved real decoder states.}"
        ),
        r"\label{tab:r2-heuristic-gap}",
        r"\scriptsize",
        r"\begin{tabular}{llrrrr}",
        r"\toprule",
        (
            r"Evidence/weights & Selector & Pairs & Equal & Median $\Delta$ & "
            r"Median $\delta$ \\ \midrule"
        ),
    ]
    for value in _sequence(r2["synthetic_rows"], "synthetic rows"):
        row = _mapping(value, "synthetic row")
        lines.append(
            f"Synthetic/{_string(row['weight_mode'], 'weight mode')} & "
            f"{_selector_label(_string(row['selector'], 'selector'))} & "
            f"{_integer(row['comparisons'], 'pairs')} & {_integer(row['equal'], 'equal')}/"
            f"{_integer(row['comparisons'], 'pairs')} & "
            f"{_number(row['median_absolute_gap'], 'absolute gap'):.1f} & "
            f"{_number(row['median_relative_gap'], 'relative gap'):.1f} \\\\"
        )
    real_comparisons = _mapping(r2["real_comparisons"], "real comparisons")
    for selector in ("greedy_exact_feasibility", "epic_regular_cover"):
        stats = _mapping(real_comparisons[selector], f"real {selector}")
        equality = _mapping(stats["equality"], "real equality")
        absolute = _mapping(stats["absolute_gap"], "real absolute")
        relative = _mapping(stats["relative_gap"], "real relative")
        lines.append(
            f"Saved states/confidence & {_selector_label(selector)} & "
            f"{_integer(stats['comparison_count'], 'real pairs')} & "
            f"{_integer(equality['event_count'], 'real equal')}/"
            f"{_integer(stats['comparison_count'], 'real pairs')} & "
            f"{_number(absolute['median'], 'real absolute median'):.1f} & "
            f"{_number(relative['median'], 'real relative median'):.1f} \\\\"
        )
    lines.extend(
        (
            r"\bottomrule",
            r"\end{tabular}",
            (
                r"\par\footnotesize $\Delta=W(J^*)-W(J_H)$ and "
                r"$\delta=\Delta/W(J^*)$. Synthetic rows are illustrative. All 24 non-IID "
                r"saved supports were singleton after deduplication, so their zero gaps are an "
                r"alignment check, not a population estimate; no failed row was omitted."
            ),
            r"\end{table}",
        )
    )
    return ("\n".join(lines) + "\n").encode()


def _runtime_cell(backend: Mapping[str, object]) -> str:
    endpoints = _mapping(backend["compound_graph_size_endpoints"], "graph endpoints")
    low = _mapping(endpoints["1"], "graph low")
    high = _mapping(endpoints["8"], "graph high")
    return (
        f"{_number(low['median_ms'], 'low median'):.3f} "
        f"[{_number(low['iqr_ms'], 'low IQR'):.3f}] $\\rightarrow$ "
        f"{_number(high['median_ms'], 'high median'):.3f} "
        f"[{_number(high['iqr_ms'], 'high IQR'):.3f}]"
    )


def _q5_task_row(task_label: str, task: Mapping[str, object]) -> str:
    strategies = _mapping(task["strategies"], "q5 strategies")
    serial = _mapping(strategies["serial"], "serial")
    epic = _mapping(strategies["epic"], "epic")
    exact = _mapping(strategies["exact"], "exact")
    max_cuda = max(
        _number(_mapping(strategies[name], name)["maximum_cuda_allocated_gib"], "CUDA GiB")
        for name in ("unconstrained", "serial", "epic", "exact")
    )
    return (
        f"Q5 {task_label} & {_number(serial['median_runtime_ms'], 'serial ms'):.1f}/"
        f"{_number(epic['median_runtime_ms'], 'epic ms'):.1f}/"
        f"{_number(exact['median_runtime_ms'], 'exact ms'):.1f} & "
        f"{max_cuda:.2f} GiB CUDA & "
        f"{_integer(task['constrained_valid_count'], 'valid')}/"
        f"{_integer(task['constrained_generation_count'], 'generations')} valid; "
        f"exact/serial={_number(task['exact_to_serial_median_runtime_ratio'], 'ratio'):.3f} & "
        f"EPIC {_integer(task['epic_regular_cover_selector_calls'], 'EPIC calls')} calls, "
        f"max batch {_integer(task['epic_maximum_batch_size'], 'EPIC batch')}; "
        f"fallback {_integer(epic['fallback_event_count'], 'fallback')} \\\\"
    )


def _render_r3(summary: Mapping[str, object]) -> bytes:
    r3 = _mapping(summary["r3"], "r3")
    q4 = _mapping(r3["q4"], "q4")
    q5 = _mapping(r3["q5"], "q5")
    q4_backends = _mapping(q4["backends"], "q4 backends")
    py = _mapping(q4_backends["python"], "python")
    rust = _mapping(q4_backends["rust"], "rust")
    tasks = _mapping(q5["tasks"], "q5 tasks")
    lines = [
        "% Generated by scripts/exact_commit/build_article_results.py; do not edit.",
        r"\begin{table}[t]",
        r"\centering",
        (
            r"\caption{R3: publication-mode generated-instance CPU scaling and "
            r"structured LLaDA integration.}"
        ),
        r"\label{tab:r3-scaling-integration}",
        r"\scriptsize",
        r"\begin{tabular}{p{1.45cm}p{3.15cm}p{1.7cm}p{2.35cm}p{3.05cm}}",
        r"\toprule",
        (
            r"Evidence & Median runtime ms [IQR] & Peak memory & Validity/status & "
            r"Parallel/fallback evidence \\ \midrule"
        ),
        f"Q4 Python & {_runtime_cell(py)} & "
        f"{_number(py['maximum_peak_worker_rss_mib'], 'Python RSS'):.2f} MiB RSS & "
        f"40/40 OPT; 0 T/C & compound graph scale $1\\rightarrow8$ \\\\ ",
        f"Q4 Rust & {_runtime_cell(rust)} & "
        f"{_number(rust['maximum_peak_worker_rss_mib'], 'Rust RSS'):.2f} MiB RSS & "
        f"40/40 OPT; 0 T/C & compound graph scale $1\\rightarrow8$ \\\\ ",
        _q5_task_row("JSON", _mapping(tasks["json_x_zero"], "JSON task")),
        _q5_task_row("DSL", _mapping(tasks["fenced_add_dsl"], "DSL task")),
        r"\bottomrule",
        r"\end{tabular}",
        (
            r"\par\footnotesize Q4 separates backends on a compound support-width/token-byte "
            r"scale; T/C is timeout/censored. Q5 order is serial/EPIC/exact; fallback counts "
            r"serial events despite EPIC batching, while exact had 60 valid certificates and "
            r"no fallback."
        ),
        r"\end{table}",
    ]
    return ("\n".join(lines) + "\n").encode()


def build_article_results(
    config_path: str | Path,
    *,
    repository_root: str | Path,
    verify_existing: bool = False,
) -> dict[str, object]:
    """Build or verify the selected R1--R3 article artifacts."""

    root = Path(repository_root).resolve()
    config = Path(config_path).resolve()
    if not config.is_relative_to(root):
        raise ValueError("article-result config must be inside the repository")
    artifact_id, processed, paper, inputs, source_records = _load_config(config, root)
    summary = _build_summary(
        artifact_id,
        config.relative_to(root).as_posix(),
        _sha256(config),
        source_records,
        inputs,
    )
    summary_bytes = (json.dumps(summary, indent=2, sort_keys=True) + "\n").encode()
    outputs = {
        processed / ARTICLE_RESULTS_FILENAME: summary_bytes,
        paper / ARTICLE_VALUES_FILENAME: _render_values(summary),
        paper / R1_FILENAME: _render_r1(summary),
        paper / R2_FILENAME: _render_r2(summary),
        paper / R3_FILENAME: _render_r3(summary),
    }
    for path, payload in outputs.items():
        if verify_existing:
            if not path.is_file() or path.read_bytes() != payload:
                raise ValueError(f"generated article result differs from pinned evidence: {path}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
    return {
        "artifact_id": artifact_id,
        "outputs": {
            path.relative_to(root).as_posix(): hashlib.sha256(payload).hexdigest()
            for path, payload in outputs.items()
        },
        "verified_existing": verify_existing,
    }
