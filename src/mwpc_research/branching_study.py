"""Paired recursive-language study using independent finite-completion oracles."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from fractions import Fraction
from itertools import pairwise, product
from math import prod
from random import Random
from time import perf_counter
from typing import Any

from mwpc_exact import (
    BenchmarkGrammar,
    BenchmarkInstance,
    ComponentProfiler,
    CompositionalByteLevelAdapter,
    EOSMode,
    EOSPolicy,
    ExactBackend,
    Proposal,
    SelectionInput,
    SupportKind,
    SupportPolicy,
    build_per_position_support,
    solve_exact_commit,
)
from mwpc_exact.evaluation.selection import select_greedy_exact_feasibility
from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_research.recursive_tasks import check_syntax, generated_witness
from mwpc_research.statistical_summaries import summarize_numeric_distribution


def build_branching_instance(
    family: str,
    seed: int,
    width: int,
    weight_mode: str,
    *,
    grammar: CnfGrammar | None = None,
) -> BenchmarkInstance:
    """Freeze a feasible synthetic state; widths share proposals and nested rows."""

    from mwpc_research.recursive_tasks import recursive_grammar

    if width not in (2, 4) or weight_mode not in ("unit", "integer_utility"):
        raise ValueError("study requires width 2/4 and unit/integer_utility weights")
    alphabet = {"brackets": b"()[]", "arithmetic": b"0123+*()", "nested_json": b"0123[],"}
    if family not in alphabet:
        raise ValueError(f"unknown recursive family: {family}")
    vocabulary = alphabet[family]
    random = Random(seed)
    witness = generated_witness(family, seed)
    target_ids = tuple(vocabulary.index(value) for value in witness)
    masked = set(random.sample(range(len(witness)), 4))
    canvas = tuple(
        None if position in masked else token for position, token in enumerate(target_ids)
    )
    rows: dict[int, tuple[int, ...]] = {}
    candidates = []
    for position, token in enumerate(target_ids):
        if position not in masked:
            rows[position] = (token,)
            continue
        alternatives = [item for item in range(len(vocabulary)) if item != token]
        random.shuffle(alternatives)
        ranking = (token, *alternatives)
        rows[position] = ranking[:width]
        primary = random.choice(ranking[:2])
        utility = random.randint(1, 9)
        candidates.append((position, primary, utility))
    candidates.sort(key=lambda item: (-item[2], item[0]))
    proposals = tuple(
        Proposal(
            index,
            position,
            token,
            1.0 if weight_mode == "unit" else float(utility),
            model_confidence=utility / 10,
        )
        for index, (position, token, utility) in enumerate(candidates)
    )
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(
            kind=SupportKind.EXPLICIT,
            vocabulary_size=len(vocabulary),
            pruning_description="synthetic witness plus seeded alternatives; no model logits",
        ),
        explicit_support=rows,
        proposals=proposals,
    )
    selected_grammar = recursive_grammar(family) if grammar is None else grammar
    return BenchmarkInstance(
        instance_id=f"{family}-{seed}-k{width}-{weight_mode}",
        grammar=BenchmarkGrammar(family, selected_grammar),
        selection_input=SelectionInput(
            selected_grammar,
            canvas,
            proposals,
            support,
            CompositionalByteLevelAdapter(tuple(bytes((value,)) for value in vocabulary)),
            EOSPolicy(EOSMode.ABSENT),
        ),
        metadata={
            "family": family,
            "seed": seed,
            "width": width,
            "weight_mode": weight_mode,
            "origin": "synthetic_feasibility_conditioned",
            "masked_positions": sorted(masked),
        },
    )


def exhaustive_completions(
    instance: BenchmarkInstance,
    *,
    maximum_paths: int = 4096,
) -> tuple[tuple[int, ...], ...]:
    """Independent language checks, without calling any CFG parser."""

    state = instance.selection_input
    path_count = prod(map(len, state.support.rows))
    if path_count > maximum_paths:
        raise ValueError(f"oracle path budget exceeded: {path_count} > {maximum_paths}")
    family = str(instance.metadata["family"])
    return tuple(
        tokens
        for tokens in product(*state.support.rows)
        if check_syntax(family, state.tokenizer_adapter.detokenize_bytes(tokens)).syntax_valid
    )


def _score(tokens: tuple[int, ...], proposals: Sequence[Proposal]) -> Fraction:
    return sum(
        (
            Fraction(proposal.weight)
            for proposal in proposals
            if tokens[proposal.position] == proposal.token_id
        ),
        Fraction(),
    )


def evaluate_branching_instance(
    instance: BenchmarkInstance,
    *,
    timeout_seconds: float = 5.0,
    maximum_paths: int = 4096,
    order_offset: int = 0,
) -> dict[str, Any]:
    """Keep input, oracle, complete statuses, independent checks and paired costs."""

    state = instance.selection_input
    started = perf_counter()
    completions = exhaustive_completions(instance, maximum_paths=maximum_paths)
    optimum = max((_score(tokens, state.proposals) for tokens in completions), default=None)
    oracle_seconds = perf_counter() - started
    methods = ("python_exact", "rust_exact", "greedy_exact_feasibility")
    offset = order_offset % len(methods)
    results: dict[str, Any] = {}
    failures = []
    for method in methods[offset:] + methods[:offset]:
        profiler = ComponentProfiler(enabled=True)
        started = perf_counter()
        try:
            if method == "greedy_exact_feasibility":
                result = select_greedy_exact_feasibility(
                    state,
                    backend=ExactBackend.RUST,
                    total_timeout_seconds=timeout_seconds,
                )
                status, score = result.status.value, result.score
                selected, witness = result.selected_proposal_ids, result.witness_token_ids
                certificate = result.to_dict()
            else:
                backend = ExactBackend.PYTHON if method == "python_exact" else ExactBackend.RUST
                exact = solve_exact_commit(
                    state.grammar,
                    canvas=state.canvas,
                    support=state.support,
                    proposals=state.proposals,
                    tokenizer_adapter=state.tokenizer_adapter,
                    eos_policy=state.eos_policy,
                    backend=backend,
                    timeout_seconds=timeout_seconds if backend is ExactBackend.RUST else None,
                    profiler=profiler,
                )
                status, score = exact.status.value, exact.objective_value
                selected, witness = exact.selected_proposal_ids, exact.witness_token_ids
                certificate = exact.to_dict()
            elapsed = perf_counter() - started
            success_status = status in {"optimal", "feasible_on_support"}
            independently_valid: bool | None = None
            if success_status:
                proposal_by_id = {proposal.proposal_id: proposal for proposal in state.proposals}
                independently_valid = (
                    len(selected) == len(set(selected))
                    and set(selected) <= proposal_by_id.keys()
                    and any(
                        all(
                            tokens[proposal_by_id[item].position] == proposal_by_id[item].token_id
                            for item in selected
                        )
                        for tokens in completions
                    )
                    and score
                    == float(
                        sum(
                            (Fraction(proposal_by_id[item].weight) for item in selected), Fraction()
                        )
                    )
                )
                if method != "greedy_exact_feasibility":
                    independently_valid = independently_valid and (
                        witness in completions
                        and _score(witness, state.proposals) == optimum
                        and set(selected)
                        == {
                            p.proposal_id
                            for p in state.proposals
                            if p.weight > 0 and witness[p.position] == p.token_id
                        }
                        and score == (None if optimum is None else float(optimum))
                    )
                if not independently_valid:
                    failures.append(f"{method}: independent oracle/certificate disagreement")
            elif status == "infeasible_on_support" and completions:
                failures.append(f"{method}: false infeasibility")
            elif status not in {"infeasible_on_support", "timeout", "unsupported"}:
                failures.append(f"{method}: {status}")
            event = profiler.snapshot() if method != "greedy_exact_feasibility" else None
            results[method] = {
                "status": status,
                "score": score,
                "runtime_seconds": elapsed,
                "independently_valid": independently_valid,
                "result": certificate,
                "profile": None if event is None else event.to_dict(),
            }
        except Exception as error:
            results[method] = {
                "status": "error",
                "score": None,
                "runtime_seconds": perf_counter() - started,
                "independently_valid": False,
                "error": f"{type(error).__name__}: {error}",
            }
            failures.append(f"{method}: {type(error).__name__}: {error}")
    greedy = results["greedy_exact_feasibility"]
    gap = (
        float(optimum) - greedy["score"]
        if optimum is not None and greedy["independently_valid"]
        else None
    )
    if gap is not None and gap < 0:
        failures.append("greedy score exceeds oracle optimum")
    return {
        "artifact_kind": "mwpc_recursive_branching_row_v1",
        **dict(instance.metadata),
        "instance_sha256": instance.fingerprint,
        "instance": instance.to_dict(),
        "total_paths": prod(map(len, state.support.rows)),
        "valid_paths": len(completions),
        "oracle_score": None if optimum is None else float(optimum),
        "oracle_runtime_seconds": oracle_seconds,
        "selectors": results,
        "absolute_gap": gap,
        "relative_gap": gap / float(optimum) if gap is not None and optimum else None,
        "failures": failures,
    }


def summarize_branching_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Stratify repeated conditions; never count them as independent states."""

    groups: dict[tuple[str, int, str], list[Mapping[str, Any]]] = defaultdict(list)
    paired: dict[tuple[str, int, str], list[Mapping[str, Any]]] = defaultdict(list)
    seen = set()
    for row in rows:
        key = (row["family"], row["seed"], row["width"], row["weight_mode"])
        if key in seen:
            raise ValueError(f"duplicate paired study row: {key}")
        seen.add(key)
        groups[row["family"], row["width"], row["weight_mode"]].append(row)
        paired[row["family"], row["seed"], row["weight_mode"]].append(row)
    summaries = []
    for (family, width, weight_mode), items in sorted(groups.items()):
        gaps = [row["absolute_gap"] for row in items if row["absolute_gap"] is not None]
        summaries.append(
            {
                "family": family,
                "width": width,
                "weight_mode": weight_mode,
                "state_count": len(items),
                "branching_valid_states": sum(row["valid_paths"] > 1 for row in items),
                "singleton_valid_states": sum(row["valid_paths"] == 1 for row in items),
                "infeasible_states": sum(row["valid_paths"] == 0 for row in items),
                "gap_pair_count": len(gaps),
                "positive_gap_count": sum(gap > 0 for gap in gaps),
                "absolute_gap": summarize_numeric_distribution(gaps).to_dict() if gaps else None,
                "selectors": {
                    method: {
                        "status_counts": dict(
                            Counter(row["selectors"][method]["status"] for row in items)
                        ),
                        "all_status_runtime_seconds": summarize_numeric_distribution(
                            [row["selectors"][method]["runtime_seconds"] for row in items]
                        ).to_dict(),
                    }
                    for method in ("python_exact", "rust_exact", "greedy_exact_feasibility")
                },
            }
        )
    improvements = violations = width_pairs = 0
    for items in paired.values():
        ordered = sorted(items, key=lambda row: row["width"])
        for narrow, wide in pairwise(ordered):
            width_pairs += 1
            if narrow["oracle_score"] is not None and wide["oracle_score"] is not None:
                improvements += wide["oracle_score"] > narrow["oracle_score"]
                violations += wide["oracle_score"] < narrow["oracle_score"]
    return {
        "artifact_kind": "mwpc_recursive_branching_summary_v2",
        "row_count": len(rows),
        "generated_state_count": len({(row["family"], row["seed"]) for row in rows}),
        "seed_cluster_count": len({row["seed"] for row in rows}),
        "correctness_failure_rows": sum(bool(row["failures"]) for row in rows),
        "width_pairs": width_pairs,
        "width_objective_improvements": improvements,
        "width_monotonicity_violations": violations,
        "groups": summaries,
        "scope": "generated feasibility-conditioned states, not real logits or end-to-end speedups",
        "interval_policy": "descriptive strata; widths/modes are not independent samples",
    }
