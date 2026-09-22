"""Portable nonliteral live-state contracts and descriptive analysis."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
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
from mwpc_research.recursive_tasks import recursive_grammar


def snapshot_instance(
    snapshot: Mapping[str, Any], width: int, proposal_budget: int | None = None
) -> BenchmarkInstance:
    """Compact only saved model choices, never a task's known answer.

    The local-to-model-ID map is retained. Proposal IDs/weights are frozen
    across widths; EOS/PAD and proposal additions are declared explicitly.
    """
    rankings = snapshot["rankings"]
    if width < 1 or any(len(row) < width for row in rankings):
        raise ValueError("requested width exceeds the captured ranking")
    proposals = tuple(Proposal(**item) for item in snapshot["proposals"])
    if proposal_budget is not None:
        if isinstance(proposal_budget, bool) or not isinstance(proposal_budget, int):
            raise TypeError("proposal_budget must be an integer")
        if proposal_budget < 1:
            raise ValueError("proposal_budget must be positive")
        # Saved full-vocabulary probabilities, not a softmax over the top-K.
        candidates = sorted(
            (position for position, token in enumerate(snapshot["canvas"]) if token is None),
            key=lambda position: (-snapshot["ranked_probabilities"][position][0], position),
        )[:proposal_budget]
        proposals = tuple(
            Proposal(
                position,
                position,
                rankings[position][0],
                snapshot["ranked_probabilities"][position][0],
                model_confidence=snapshot["ranked_probabilities"][position][0],
            )
            for position in candidates
        )
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
        instance_id=f"{snapshot['snapshot_id']}-k{width}"
        + (f"-b{proposal_budget}" if proposal_budget is not None else ""),
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
            "proposal_budget": proposal_budget,
            "proposal_policy": "saved_original"
            if proposal_budget is None
            else "top_permitted_token_by_saved_full_vocabulary_probability",
            "model_token_ids": model_ids,
            "source_strategy": "unconstrained",
            "target_injected": False,
            "source_seed": snapshot["seed"],
            "source_task_id": snapshot["task_id"],
            "source_forward_index": snapshot["forward_index"],
            "model_revision": snapshot["model_revision"],
            "tokenizer_revision": snapshot["tokenizer_revision"],
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
