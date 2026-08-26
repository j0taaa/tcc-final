"""Offline evaluation contracts, selectors, schema, alignment, and replay."""

from mwpc_exact.evaluation.alignment import (
    AlignmentCase,
    SemanticAlignmentEvidence,
    alignment_evidence_from_instance,
    validate_semantic_alignment,
)
from mwpc_exact.evaluation.brute_force import select_brute_force, select_brute_force_graph
from mwpc_exact.evaluation.epic_regular_cover import (
    EPIC_UPSTREAM_COMMIT,
    EpicSelectionContext,
    select_epic,
    select_epic_regular_cover,
)
from mwpc_exact.evaluation.instance import (
    BENCHMARK_INSTANCE_ARTIFACT_KIND,
    BENCHMARK_INSTANCE_SCHEMA_VERSION,
    BenchmarkGrammar,
    BenchmarkInstance,
    EpicReplaySpec,
    SavedLogits,
    UnsupportedBenchmarkSchemaVersion,
    migrate_benchmark_instance_data,
)
from mwpc_exact.evaluation.replay import EpicCfgFactory, replay_benchmark_instance
from mwpc_exact.evaluation.selection import (
    SelectionInput,
    SelectionResult,
    SelectionStatus,
    SelectorKind,
    recompute_witness_selection,
    select_exact,
    select_exact_mwpc,
    select_greedy_exact_feasibility,
    select_serial,
    validate_ordinary_primary_proposal_comparison,
)

__all__ = [
    "BENCHMARK_INSTANCE_ARTIFACT_KIND",
    "BENCHMARK_INSTANCE_SCHEMA_VERSION",
    "EPIC_UPSTREAM_COMMIT",
    "AlignmentCase",
    "BenchmarkGrammar",
    "BenchmarkInstance",
    "EpicCfgFactory",
    "EpicReplaySpec",
    "EpicSelectionContext",
    "SavedLogits",
    "SelectionInput",
    "SelectionResult",
    "SelectionStatus",
    "SelectorKind",
    "SemanticAlignmentEvidence",
    "UnsupportedBenchmarkSchemaVersion",
    "alignment_evidence_from_instance",
    "migrate_benchmark_instance_data",
    "recompute_witness_selection",
    "replay_benchmark_instance",
    "select_brute_force",
    "select_brute_force_graph",
    "select_epic",
    "select_epic_regular_cover",
    "select_exact",
    "select_exact_mwpc",
    "select_greedy_exact_feasibility",
    "select_serial",
    "validate_ordinary_primary_proposal_comparison",
    "validate_semantic_alignment",
]
