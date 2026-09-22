"""Portable nonliteral live-state contracts and descriptive analysis."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from statistics import median
from typing import Any

from mwpc_exact import (
    BenchmarkGrammar,
    BenchmarkInstance,
    CompositionalByteLevelAdapter,
    EOSMode,
    EOSPolicy,
    Proposal,
    SelectionInput,
    SupportKind,
    SupportPolicy,
    build_per_position_support,
)
from mwpc_research.matched_schedule import transfer_schedule
from mwpc_research.recursive_tasks import RecursiveTask, pilot_tasks, recursive_grammar


def study_tasks(split: str) -> tuple[RecursiveTask, ...]:
    if split == "pilot":
        return pilot_tasks()
    if split != "confirmation":
        raise ValueError("split must be pilot or confirmation")
    tasks: list[RecursiveTask] = []
    for index in range(4):
        tasks.extend(
            (
                RecursiveTask(
                    f"confirm-brackets-{index}",
                    "brackets",
                    f"Write a balanced sequence with {index + 1} pairs of round brackets and "
                    "three pairs of square brackets. The maximum nesting depth must be at least "
                    "three. Return brackets only, with no spaces or code fence.",
                    (index + 1, 3),
                    3,
                ),
                RecursiveTask(
                    f"confirm-arithmetic-{index}",
                    "arithmetic",
                    f"Make an expression equal to {index + 12}, using each of the digits "
                    f"{index + 4}, 3, 5 once. Only + and * are allowed; enclose every binary "
                    "operation in parentheses. Return the expression without a code fence.",
                    (index + 4, 3, 5),
                    2,
                    index + 12,
                ),
                RecursiveTask(
                    f"confirm-nested_json-{index}",
                    "nested_json",
                    f"Return a JSON array whose leaves, read from left to right, are "
                    f"{index + 4}, 3, 5. Nest arrays at least three levels deep. "
                    "Use no other values and no Markdown formatting.",
                    (index + 4, 3, 5),
                    3,
                ),
            )
        )
    return tuple(tasks)


def live_jobs(split: str, seeds: Sequence[int], repetitions: int) -> tuple[dict[str, Any], ...]:
    if not seeds or repetitions < 1:
        raise ValueError("seeds and positive repetitions are required")
    jobs = []
    strategies = ("unconstrained", "serial", "epic", "exact")
    for task_index, task in enumerate(study_tasks(split)):
        for seed in seeds:
            for repetition in range(repetitions):
                offset = (task_index + repetition) % len(strategies)
                for strategy in strategies[offset:] + strategies[:offset]:
                    jobs.append(
                        {
                            "job_id": f"{task.task_id}-{seed}-{repetition}-{strategy}",
                            "task": asdict(task),
                            "seed": seed,
                            "repetition": repetition,
                            "strategy": strategy,
                        }
                    )
            jobs.append(
                {
                    "job_id": f"{task.task_id}-{seed}-capture",
                    "task": asdict(task),
                    "seed": seed,
                    "repetition": 0,
                    "strategy": "capture",
                }
            )
    return tuple(jobs)


def snapshot_instance(snapshot: Mapping[str, Any], width: int) -> BenchmarkInstance:
    """Compact only saved model choices, never a task's known answer.

    The local-to-model-ID map is retained. Proposal IDs/weights are frozen
    across widths; EOS/PAD and proposal additions are declared explicitly.
    """
    rankings = snapshot["rankings"]
    if width < 1 or any(len(row) < width for row in rankings):
        raise ValueError("requested width exceeds the captured ranking")
    proposals = tuple(Proposal(**item) for item in snapshot["proposals"])
    specials = tuple(snapshot["termination_token_ids"])
    pad = snapshot["pad_token_id"]
    model_rows = []
    for position, fixed in enumerate(snapshot["canvas"]):
        row = (
            (fixed,)
            if fixed is not None
            else tuple(
                dict.fromkeys(
                    (
                        *rankings[position][:width],
                        *specials,
                        pad,
                        *(p.token_id for p in proposals if p.position == position),
                    )
                )
            )
        )
        model_rows.append(row)
    model_ids = tuple(sorted({pad, *specials, *(t for row in model_rows for t in row)}))
    local = {token: i for i, token in enumerate(model_ids)}
    adapter = CompositionalByteLevelAdapter(
        tuple(
            None
            if snapshot["emissions"][str(token)] is None
            else bytes.fromhex(snapshot["emissions"][str(token)])
            for token in model_ids
        )
    )
    canvas = tuple(None if token is None else local[token] for token in snapshot["canvas"])
    mapped_proposals = tuple(
        Proposal(
            p.proposal_id,
            p.position,
            local[p.token_id],
            p.weight,
            model_confidence=p.model_confidence,
        )
        for p in proposals
    )
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(
            kind=SupportKind.EXPLICIT,
            vocabulary_size=len(model_ids),
            required_special_token_ids=tuple(local[token] for token in specials),
            pruning_description=f"saved model top-{width} plus frozen proposals and EOS/PAD",
        ),
        explicit_support={
            i: tuple(local[token] for token in row) for i, row in enumerate(model_rows)
        },
        proposals=mapped_proposals,
    )
    grammar = recursive_grammar(snapshot["family"])
    return BenchmarkInstance(
        instance_id=f"{snapshot['snapshot_id']}-k{width}",
        grammar=BenchmarkGrammar(snapshot["family"], grammar),
        selection_input=SelectionInput(
            grammar,
            canvas,
            mapped_proposals,
            support,
            adapter,
            EOSPolicy(
                EOSMode.REQUIRED,
                termination_token_ids=tuple(local[token] for token in specials),
                pad_token_id=local[pad],
            ),
        ),
        metadata={
            "origin": "real_model_precommit",
            "snapshot_id": snapshot["snapshot_id"],
            "width": width,
            "model_token_ids": model_ids,
            "source_strategy": "unconstrained",
            "target_injected": False,
        },
    )


def summarize_live_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Keep all statuses; successful-runtime medians never hide failure counts."""
    groups: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["strategy"] != "capture":
            groups[row["task"]["family"], row["strategy"]].append(row)
    summaries = []
    for (family, strategy), items in sorted(groups.items()):
        complete_times = [
            item["runtime_seconds"] for item in items if item["execution_status"] == "complete"
        ]
        summaries.append(
            {
                "family": family,
                "strategy": strategy,
                "attempts": len(items),
                "unique_tasks": len({item["task"]["task_id"] for item in items}),
                "statuses": dict(Counter(item["execution_status"] for item in items)),
                "solver_statuses": dict(Counter(str(item.get("solver_status")) for item in items)),
                "syntax_valid": sum(item.get("syntactic_valid") is True for item in items),
                "functional_success": sum(item.get("functional_success") is True for item in items),
                "complete_runtime_median_seconds": median(complete_times)
                if complete_times
                else None,
                "complete_runtime_sample_count": len(complete_times),
                "forward_counts": [item.get("model_forward_count") for item in items],
            }
        )
    return {
        "groups": summaries,
        "analysis_unit": "task; repetitions are repeated measures",
        "runtime_censoring": "timeouts excluded from complete-runtime medians, counted in statuses",
    }


def checked_generation(
    task: RecursiveTask,
    tokens: Sequence[int],
    adapter: CompositionalByteLevelAdapter,
    termination_ids: Sequence[int],
    mask_id: int,
) -> dict[str, Any]:
    endpoint = next((i for i, token in enumerate(tokens) if token in termination_ids), len(tokens))
    content = tuple(tokens[:endpoint])
    if mask_id in content:
        return {"complete": False, "syntactic_valid": False, "functional_success": False}
    try:
        decoded = adapter.detokenize_bytes(content)
    except ValueError:
        return {"complete": True, "syntactic_valid": False, "functional_success": False}
    checked, success = task.check(decoded)
    return {
        "complete": True,
        "syntactic_valid": checked.syntax_valid,
        "functional_success": success,
        "content_hex": decoded.hex(),
        "checker": asdict(checked),
    }


def declared_schedule(slots: int, steps: int) -> dict[str, Any]:
    return {
        "initial_slots": slots,
        "steps": steps,
        "block_length": slots,
        "proposal_budgets": transfer_schedule(slots, steps),
        "stop": "first complete prefix through EOS or full canvas; at most configured steps",
        "special_updates": "EOS suffix canonicalization may update additional physical slots",
    }
