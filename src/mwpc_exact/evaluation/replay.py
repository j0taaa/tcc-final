"""Replay fair selector comparisons from one immutable benchmark instance."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import replace
from importlib import import_module
from types import MappingProxyType
from typing import cast

from mwpc_exact.backend import ExactBackend
from mwpc_exact.evaluation.alignment import EpicGrammar, validate_semantic_alignment
from mwpc_exact.evaluation.brute_force import select_brute_force
from mwpc_exact.evaluation.epic_regular_cover import (
    select_epic_regular_cover,
)
from mwpc_exact.evaluation.instance import BenchmarkInstance
from mwpc_exact.evaluation.selection import (
    SelectionInput,
    SelectionResult,
    SelectionStatus,
    SelectorKind,
    select_exact_mwpc,
    select_greedy_exact_feasibility,
    validate_ordinary_primary_proposal_comparison,
)

EpicCfgFactory = Callable[[str, str], object]


def _default_epic_cfg_factory(text: str, start_symbol: str) -> object:
    cfg_module = import_module("rustformlang.cfg")
    cfg_type = cfg_module.CFG
    return cast(object, cfg_type.from_text(text, start_symbol))


def _unsupported_epic_result(
    selection_input: SelectionInput,
    error: Exception,
) -> SelectionResult:
    return SelectionResult(
        selector=SelectorKind.EPIC_REGULAR_COVER,
        status=SelectionStatus.UNSUPPORTED,
        exactness_scope=selection_input.support.exactness_scope,
        runtime_seconds=0.0,
        diagnostics={
            "error_stage": "benchmark_epic_cfg_reconstruction",
            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )


def replay_benchmark_instance(
    instance: BenchmarkInstance,
    *,
    backend: ExactBackend = ExactBackend.PYTHON,
    selector_timeout_seconds: float | None = None,
    timeout_seconds: float | None = None,
    brute_force_max_completions: int = 100_000,
    epic_cfg_factory: EpicCfgFactory | None = None,
) -> Mapping[SelectorKind, SelectionResult]:
    """Replay every selector under one ordinary-primary-proposal comparison profile."""

    if not isinstance(instance, BenchmarkInstance):
        raise TypeError("instance must be a BenchmarkInstance")
    if timeout_seconds is not None:
        if selector_timeout_seconds is not None:
            raise ValueError("use only selector_timeout_seconds, not both timeout names")
        selector_timeout_seconds = timeout_seconds
    selection_input = instance.selection_input
    validate_ordinary_primary_proposal_comparison(selection_input)
    results: dict[SelectorKind, SelectionResult] = {}
    results[SelectorKind.GREEDY_EXACT_FEASIBILITY] = select_greedy_exact_feasibility(
        selection_input,
        backend=backend,
        total_timeout_seconds=selector_timeout_seconds,
    )
    if instance.epic_replay is not None:
        text = instance.grammar.epic_cfg_text
        start_symbol = instance.grammar.epic_start_symbol
        if text is None or start_symbol is None:
            raise AssertionError("validated EPIC replay lost its grammar representation")
        factory = epic_cfg_factory or _default_epic_cfg_factory
        try:
            cfg = factory(text, start_symbol)
            alignment_report = validate_semantic_alignment(instance, cast(EpicGrammar, cfg))
            context = instance.epic_replay.to_context(cfg)
        except (ImportError, ModuleNotFoundError, AttributeError, TypeError) as error:
            results[SelectorKind.EPIC_REGULAR_COVER] = _unsupported_epic_result(
                selection_input,
                error,
            )
        else:
            epic = select_epic_regular_cover(selection_input, context)
            results[SelectorKind.EPIC_REGULAR_COVER] = replace(
                epic,
                diagnostics={
                    **dict(epic.diagnostics),
                    "semantic_alignment": alignment_report,
                },
            )
    results[SelectorKind.EXACT_MWPC] = select_exact_mwpc(
        selection_input,
        backend=backend,
        timeout_seconds=selector_timeout_seconds,
    )
    results[SelectorKind.BRUTE_FORCE] = select_brute_force(
        selection_input,
        max_completions=brute_force_max_completions,
    )
    return MappingProxyType(results)


__all__ = ["EpicCfgFactory", "replay_benchmark_instance"]
