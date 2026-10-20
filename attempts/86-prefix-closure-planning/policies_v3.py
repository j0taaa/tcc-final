"""Prospective A86 CPU calibration and whole-trajectory replay (no neural calls).

The Spiffy objectives are adaptations to the common top-1 candidate pool, not
reproductions of its attention backend or underspecified online pruning. Closure
and fractional optimization are classical; ``planner`` implements that reduction.
All reported inference costs below are profile-based estimates, not decoder times.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import random
import sys
import time
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

from planner import choose_plan

HERE = Path(__file__).resolve().parent
K, BLOCK, TOTAL, GENERATION = 8, 32, 256, 128
MASK, TERMINALS = 126336, {126081, 126348}
D_GRID = (1, 2, 3, 4, 6, 8, 10, 12)
N_GRID = tuple(range(1, 9))
MILP_SECONDS = 30.0


class Inconclusive(RuntimeError):
    """Missing/unsupported data or resources cannot establish a gain."""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bucket(count: int) -> int:
    return 0 if count <= 1 else 1 if count <= 3 else 2


@dataclass(frozen=True)
class Root:
    k: int
    context: int
    path: tuple[int, ...]
    confidence: tuple[float, ...] = ()


@dataclass(frozen=True)
class Case:
    id: str
    split: str
    family: str
    roots: tuple[Root, ...]
    stop_reason: str
    capture_head_ns: int
    capture_wall_ns: int


@dataclass(frozen=True)
class Costs:
    c1: int
    c8: int

    def __post_init__(self):
        if not 0 < self.c1 < self.c8 < 8 * self.c1:
            raise Inconclusive("profile must have 0 < c1 < c8 < 8*c1")
        if self.b <= 0 or self.a <= 0:
            raise Inconclusive("profile has no supported positive affine lower envelope")

    def __call__(self, size: int) -> int:
        if size == 0:
            return 0
        if not 1 <= size <= 128:
            raise ValueError("query count must be in 1..128")
        waves, remainder = divmod(size, 8)
        return waves * self.c8 + min(remainder * self.c1, self.c8)

    @property
    def b(self) -> int:
        return (self.c8 - self.c1) // 7

    @property
    def a(self) -> int:
        return min(self(size) - self.b * size for size in range(1, 129))

    @property
    def kappa(self) -> Fraction:
        return max(Fraction(self(size), self.a + self.b * size) for size in range(1, 129))


def read_costs(path: Path) -> Costs:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    values = {
        row["batch"]: round(row["median_seconds"] * 1_000_000_000)
        for row in rows
        if row.get("type") == "profile" and row.get("length") == TOTAL
    }
    if set(values) != {1, 2, 4, 8}:
        raise Inconclusive("frozen profile lacks the complete n256 batch grid")
    return Costs(values[1], values[8])


def read_capture(path: Path) -> tuple[list[Case], dict]:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if any(row.get("type") in {"error", "refusal"} for row in rows):
        raise Inconclusive("capture contains a refusal or error")
    producers = [row for row in rows if row.get("type") == "producer"]
    results = [row for row in rows if row.get("type") == "result"]
    if len(producers) != 1 or len(results) != 1 or results[0].get("status") != "COMPLETE":
        raise Inconclusive("require one complete capture, not a partial stream")
    producer = producers[0]
    if any(
        producer.get(key) != value
        for key, value in {
            "total": TOTAL,
            "generation": GENERATION,
            "block": BLOCK,
            "batch": 1,
            "use_cache": False,
        }.items()
    ):
        raise Inconclusive("unsupported capture contract")
    for name in ("policies_v3.py", "planner.py", "profile-v1.jsonl"):
        if producer.get("hashes", {}).get(name) != digest(HERE / name):
            raise Inconclusive(f"capture/source hash mismatch: {name}")
    grouped: dict[str, dict] = {}
    for row in rows:
        if row.get("type") in {"input", "serial_step", "serial_final", "case_cost"}:
            data = grouped.setdefault(row["id"], {"steps": []})
            if row["type"] == "serial_step":
                data["steps"].append(row)
            else:
                if row["type"] in data:
                    raise ValueError(f"duplicate {row['type']} for {row['id']}")
                data[row["type"]] = row
    cases = []
    for case_id, data in grouped.items():
        inp, final, cost = (data[name] for name in ("input", "serial_final", "case_cost"))
        steps = data["steps"]
        if not steps or len(steps) != final["events"] or len(steps) != cost["events"]:
            raise ValueError(f"incomplete case {case_id}")
        offset = inp["offset"]
        if len(inp["prompt_ids"]) != offset or offset + GENERATION > TOTAL:
            raise ValueError("invalid prompt/canvas dimensions")
        canvas = inp["prompt_ids"] + [MASK] * (TOTAL - offset)
        root_ranks = []
        for t, step in enumerate(steps):
            if step["step"] != t or step["split"] != inp["split"]:
                raise ValueError("steps must be consecutive and have the declared split")
            remaining = [i for i in range(offset, offset + GENERATION) if canvas[i] == MASK]
            if not remaining:
                raise ValueError("head recorded after generation completed")
            start = offset + ((remaining[0] - offset) // BLOCK) * BLOCK
            if step["block_start"] != start:
                raise ValueError("incorrect active block")
            ids, conf, order = step["top1_ids"], step["confidence"], step["order"]
            if len(ids) != BLOCK or len(conf) != BLOCK or sorted(order) != list(range(BLOCK)):
                raise ValueError("head must contain all 32 positions")
            if any(not math.isfinite(p) or not 0 <= p <= 1 for p in conf):
                raise ValueError("invalid head confidence")
            expected_order = sorted(
                range(BLOCK),
                key=lambda i: (
                    -conf[i] if canvas[start + i] == MASK else math.inf,
                    i,
                ),
            )
            if order != expected_order:
                raise ValueError("recorded confidence order violates stable native ties")
            active = [i for i in order if canvas[start + i] == MASK]
            chosen = active[:K]
            root_ranks.append(
                (
                    [(start + i, ids[i]) for i in chosen],
                    bucket(sum(conf[i] >= 0.95 for i in chosen)),
                    tuple(conf[i] for i in chosen),
                )
            )
            position, token = step["action"]
            if [position, token] != [start + active[0], ids[active[0]]] or token == MASK:
                raise ValueError("recorded action is not the native top-1 confidence action")
            canvas[position] = token
            terminal = None
            for pos in range(offset, offset + GENERATION):
                if canvas[pos] in TERMINALS and MASK not in canvas[offset:pos]:
                    terminal = [pos, canvas[pos]]
                    break
            complete = MASK not in canvas[offset : offset + GENERATION]
            reason = (
                "safe_terminal"
                if terminal
                else "generation_complete"
                if complete
                else ("event_limit" if t + 1 == inp["event_limit"] else "continue")
            )
            if step["terminal"] != terminal or step["stop_reason"] != reason:
                raise ValueError("capture stop semantics do not match its canvas")
            if reason != "continue" and t != len(steps) - 1:
                raise ValueError("capture continues beyond its declared endpoint")
        if canvas != final["canvas_ids"] or final["stop_reason"] != steps[-1]["stop_reason"]:
            raise ValueError("final canvas does not reconstruct from original action IDs")
        roots = []
        for t, (ranked, context, confidence) in enumerate(root_ranks):
            ranks = {position: (rank, token) for rank, (position, token) in enumerate(ranked)}
            path, mask = [], 0
            # The final event needs no future head. A block change does not
            # invalidate the head at t+d; its projection is the next active block.
            for d in range(1, min(K, len(steps) - 1 - t) + 1):
                position, token = steps[t + d - 1]["action"]
                if position not in ranks or ranks[position][1] != token:
                    break
                bit = 1 << ranks[position][0]
                if mask & bit:
                    raise ValueError("native path reveals a fixed position twice")
                mask |= bit
                path.append(mask)
            if t + 1 < len(steps) and (not path or path[0] != 1):
                raise ValueError("known first event must match mandatory mask 1")
            roots.append(Root(len(ranked), context, tuple(path), confidence))
        cases.append(
            Case(
                case_id,
                inp["split"],
                inp["family"],
                tuple(roots),
                final["stop_reason"],
                round(sum(s["seconds"] for s in steps) * 1_000_000_000),
                round(cost["capture_wall_seconds"] * 1_000_000_000),
            )
        )
    expected = {"train": 4, "validation": 4, "test": 8}
    if Counter(case.split for case in cases) != Counter(expected):
        raise Inconclusive("capture must have the frozen 4/4/8 split")
    if results[0].get("completed_cases") != 16 or results[0].get("total_events") != sum(
        len(case.roots) for case in cases
    ):
        raise ValueError("capture completion counters disagree")
    return cases, producer


def universe(k: int) -> tuple[int, ...]:
    return tuple(range(1, 1 << k, 2))


def parents(mask: int) -> tuple[int, ...]:
    return tuple(mask ^ (1 << bit) for bit in range(1, mask.bit_length()) if mask & (1 << bit))


def progress(path: tuple[int, ...], selected: frozenset[int]) -> int:
    accepted = 0
    for mask in path:
        if mask not in selected:
            break
        accepted += 1
    return accepted


def score(selected: frozenset[int], counts: Counter, degree: int) -> int:
    value = sum(counts[node] for node in selected)
    if degree:
        value += sum(
            counts[parent] for node in selected for parent in parents(node) if parent in selected
        )
    return value


def fit_spiffy(paths: list[tuple[int, ...]], size: int, degree: int) -> tuple[frozenset[int], dict]:
    """Exact integer MILP formulation; numerical optimality is reported by HiGHS."""
    counts = Counter(node for path in paths for node in path)
    counts.setdefault(1, 0)
    nodes = sorted(counts, key=lambda node: (node.bit_count(), node))
    target = min(size, len(nodes))
    if target == 1 or target == len(nodes):
        selected = frozenset({1} if target == 1 else nodes)
        return selected, {
            "status": "OPTIMAL",
            "solver": "direct",
            "objective": score(selected, counts, degree),
            "observed_nodes": len(nodes),
            "effective_D": target,
        }
    try:
        import numpy as np
        from scipy.optimize import Bounds, LinearConstraint, milp
        from scipy.sparse import coo_array
    except ImportError as exc:
        raise Inconclusive("SciPy/HiGHS is required for competent Spiffy controls") from exc
    index = {node: i for i, node in enumerate(nodes)}
    edges = [(p, q) for q in nodes for p in parents(q) if p in index] if degree else []
    nvars = len(nodes) + len(edges)
    objective = [-counts[node] for node in nodes] + [-counts[p] for p, _ in edges]
    entries, lower, upper = [], [], []

    def constraint(terms, lo=-math.inf, hi=0):
        row = len(lower)
        entries.extend((row, col, val) for col, val in terms)
        lower.append(lo)
        upper.append(hi)

    constraint([(i, 1) for i in range(len(nodes))], target, target)
    constraint([(index[1], 1)], 1, 1)
    for q in nodes:
        if q != 1:
            constraint([(index[q], 1)] + [(index[p], -1) for p in parents(q) if p in index])
    for j, (p, q) in enumerate(edges, len(nodes)):
        constraint([(j, 1), (index[p], -1)])
        constraint([(j, 1), (index[q], -1)])
        constraint([(index[p], 1), (index[q], 1), (j, -1)], hi=1)
    rr, cc, vv = zip(*entries, strict=True)
    matrix = coo_array(
        (
            np.array(vv, dtype=float),
            (
                np.array(rr, dtype=np.int32),
                np.array(cc, dtype=np.int32),
            ),
        ),
        shape=(len(lower), nvars),
    ).tocsc()
    result = milp(
        np.array(objective, dtype=float),
        integrality=np.ones(nvars),
        bounds=Bounds(np.zeros(nvars), np.ones(nvars)),
        constraints=LinearConstraint(matrix, lower, upper),
        options={"time_limit": MILP_SECONDS, "mip_rel_gap": 0.0, "presolve": True},
    )

    def finite_number(name, *, integer=False):
        value = getattr(result, name, None)
        if value is None or not math.isfinite(value):
            return None
        return int(value) if integer else float(value)

    metadata = {
        "status": "OPTIMAL"
        if result.status == 0
        else ("TIMEOUT" if result.status == 1 else "INFEASIBLE" if result.status == 2 else "ERROR"),
        "solver": "scipy.optimize.milp/HiGHS",
        "solver_message": result.message,
        "observed_nodes": len(nodes),
        "effective_D": target,
        "mip_gap": finite_number("mip_gap"),
        "mip_node_count": finite_number("mip_node_count", integer=True),
        "mip_dual_bound": finite_number("mip_dual_bound"),
    }
    if result.status != 0:
        return frozenset(), metadata
    if result.x is None or max(abs(x - round(x)) for x in result.x) > 1e-6:
        raise ArithmeticError("HiGHS returned a nonintegral optimal assignment")
    selected = frozenset(node for node, i in index.items() if round(result.x[i]))
    if (
        len(selected) != target
        or 1 not in selected
        or any(node != 1 and not set(parents(node)).intersection(selected) for node in selected)
    ):
        raise ArithmeticError("independent MILP feasibility validation failed")
    value = score(selected, counts, degree)
    if abs(result.fun + value) > 1e-5:
        raise ArithmeticError("independent integer MILP objective validation failed")
    metadata["objective"] = value
    return selected, metadata


@dataclass(frozen=True)
class Config:
    family: str
    mode: str = "global"
    sizes: tuple[int, ...] = ()

    @property
    def id(self):
        return f"{self.family}:{self.mode}:" + ",".join(map(str, self.sizes))


class Tables:
    def __init__(self, cases: list[Case], costs: Costs, record):
        self.plans: dict[tuple[str, int, int, int], frozenset[int] | None] = {}
        self.failures = []
        self.costs = costs
        self.fit_wall_ns = self.fit_cpu_ns = 0
        self.fit_by_family: dict[str, Counter] = {}
        groups: dict[tuple[int, int], list[tuple[int, ...]]] = {}
        for case in cases:
            if case.split != "train":
                continue
            for root in case.roots[:-K]:
                groups.setdefault((root.k, -1), []).append(root.path)
                groups.setdefault((root.k, root.context), []).append(root.path)
        self.observed = frozenset(groups)
        for k in range(1, K + 1):
            for context in (-1, 0, 1, 2):
                paths = groups.get((k, context), [])
                for family, sizes in (("flow", (0,)), ("spiffy_j0", D_GRID), ("spiffy_j1", D_GRID)):
                    for size in sizes:
                        key = family, k, context, size
                        began, cpu_began = time.perf_counter_ns(), time.process_time_ns()
                        if not paths:
                            fallback = (family, k, -1, size)
                            chosen = self.plans[fallback] if context != -1 else frozenset({1})
                            details = {
                                "status": "FALLBACK_GLOBAL" if context != -1 else "FALLBACK_SERIAL",
                                "origins": 0,
                            }
                        elif family == "flow":
                            plan = choose_plan(
                                [(1, path) for path in paths],
                                universe(k),
                                costs.a,
                                costs.b,
                                mandatory={1},
                            )
                            chosen = frozenset(plan.selected)
                            details = {
                                "status": "OPTIMAL",
                                "origins": len(paths),
                                "cut_count": plan.cut_count,
                                "progress": plan.progress,
                                "ratio": str(plan.ratio),
                                "residual": str(plan.residual),
                            }
                        else:
                            chosen, details = fit_spiffy(paths, size, int(family == "spiffy_j1"))
                            details["origins"] = len(paths)
                            if details["status"] != "OPTIMAL":
                                self.failures.append({"key": list(key), **details})
                                chosen = None
                        elapsed, cpu_elapsed = (
                            time.perf_counter_ns() - began,
                            (time.process_time_ns() - cpu_began),
                        )
                        self.fit_wall_ns += elapsed
                        self.fit_cpu_ns += cpu_elapsed
                        totals = self.fit_by_family.setdefault(family, Counter())
                        totals.update(wall_ns=elapsed, cpu_ns=cpu_elapsed)
                        self.plans[key] = chosen
                        record(
                            {
                                "type": "fit",
                                "family": family,
                                "k": k,
                                "context": context,
                                "D": size,
                                "selected": sorted(chosen) if chosen else None,
                                "wall_ns": elapsed,
                                "cpu_ns": cpu_elapsed,
                                **details,
                            }
                        )

    def select(self, config: Config, root: Root) -> frozenset[int]:
        if config.family == "serial":
            return frozenset({1})
        context = root.context if config.mode == "context" else -1
        size = config.sizes[root.context if config.mode == "context" else 0] if config.sizes else 0
        if config.family.startswith("ssd_"):
            if (root.k, context) not in self.observed and (root.k, -1) not in self.observed:
                return frozenset({1})
            length = min(size, root.k)
            selected = {(1 << d) - 1 for d in range(1, length + 1)}
            if config.family == "ssd_mix":
                # B_0={rank2} is impossible with the known first native action.
                selected.update(((1 << d) - 1) | (1 << (d + 1)) for d in range(1, length - 1))
            return frozenset(selected)
        if config.family.endswith("_gm"):
            base = self.plans[config.family.removesuffix("_gm"), root.k, context, 12]
            if base is None:
                raise Inconclusive("GM base graph MILP did not establish optimality")
            if len(root.confidence) != root.k:
                raise ValueError("online pruning requires root top-k confidences")
            logs = [math.log(p) if p > 0 else -math.inf for p in root.confidence]
            local = {
                node: math.exp(
                    sum(logs[i] for i in range(root.k) if node & (1 << i)) / node.bit_count()
                )
                for node in base
            }
            scores = {}
            for node in base:
                children = [child for child in base if node in parents(child)]
                summary = (
                    math.exp(
                        sum(
                            math.log(local[child]) if local[child] > 0 else -math.inf
                            for child in children
                        )
                        / len(children)
                    )
                    if children
                    else local[node]
                )
                scores[node] = math.sqrt(local[node] * summary)
            ranked = sorted(base - {1}, key=lambda node: (-scores[node], node))
            return frozenset({1, *ranked[: max(0, min(size, len(base)) - 1)]})
        selected = self.plans[config.family, root.k, context, size]
        if selected is None:
            raise Inconclusive("required comparator MILP did not establish optimality")
        return selected


def replay(case: Case, config: Config, tables: Tables, *, detailed: bool = False) -> dict:
    t, queries, macros, inference_ns = 0, 0, [], tables.costs.c1
    selection_ns = 0
    while t < len(case.roots) - 1:
        root = case.roots[t]
        selection_start = time.perf_counter_ns()
        selected = tables.select(config, root)
        elapsed = time.perf_counter_ns() - selection_start
        selection_ns += elapsed
        if 1 not in selected or not selected.issubset(universe(root.k)):
            raise AssertionError("policy violates the common pool/mandatory contract")
        accepted = progress(root.path, selected)
        if accepted < 1:
            raise AssertionError("cached-head macro must advance to at least mask 1")
        cost = tables.costs(len(selected))
        queries += len(selected)
        inference_ns += cost
        if detailed:
            macros.append(
                {
                    "origin": t,
                    "k": root.k,
                    "context": root.context,
                    "advance": accepted,
                    "queries": len(selected),
                    "cost_ns": cost,
                    "selection_ns": elapsed,
                    "selected": sorted(selected),
                }
            )
        t += accepted
    if t != len(case.roots) - 1:
        raise AssertionError("macro ends at a queried existing head, never a phantom bonus")
    # Apply the final event directly from its cached head, including capped traces.
    result = {
        "id": case.id,
        "split": case.split,
        "family": case.family,
        "events": len(case.roots),
        "stop_reason": case.stop_reason,
        "estimated_inference_ns": inference_ns,
        "policy_selection_ns": selection_ns,
        "estimated_total_ns": inference_ns + selection_ns,
        "query_count": queries + 1,
        "initial_query_ns": tables.costs.c1,
        "final_event_extra_query_ns": 0,
    }
    if detailed:
        result["macros"] = macros
    return result


def configurations(family: str):
    if family in {"flow", "serial"}:
        yield Config(family)
        if family == "flow":
            yield Config(family, "context")
        return
    grid = N_GRID if family.startswith("ssd_") else D_GRID
    for size in grid:
        yield Config(family, sizes=(size,))
    for sizes in itertools.product(grid, repeat=3):
        yield Config(family, "context", sizes)


def select_validation(cases: list[Case], tables: Tables, record) -> tuple[dict, dict]:
    chosen, timing = {}, {}
    validation_cost = {}
    validation = [case for case in cases if case.split == "validation"]
    for family in (
        "serial",
        "ssd_chain",
        "ssd_mix",
        "spiffy_j0",
        "spiffy_j1",
        "spiffy_j0_gm",
        "spiffy_j1_gm",
        "flow",
    ):
        began, cpu_began = time.perf_counter_ns(), time.process_time_ns()
        ranked = []
        for config in configurations(family):
            try:
                outcomes = [replay(case, config, tables) for case in validation]
                total = sum(row["estimated_total_ns"] for row in outcomes)
                queries = sum(row["query_count"] for row in outcomes)
                rank = total, queries, config.mode == "context", config.sizes
                ranked.append((rank, config))
                record(
                    {
                        "type": "policy_candidate",
                        "policy": config.id,
                        "family": family,
                        "mode": config.mode,
                        "sizes": list(config.sizes),
                        "status": "COMPLETE",
                        "validation_estimated_total_ns": total,
                        "validation_queries": queries,
                        "validation_cases": [
                            {"id": row["id"], "cost_ns": row["estimated_total_ns"]}
                            for row in outcomes
                        ],
                    }
                )
            except Inconclusive as exc:
                record(
                    {
                        "type": "policy_candidate",
                        "policy": config.id,
                        "family": family,
                        "status": "INCONCLUSIVE",
                        "reason": str(exc),
                    }
                )
        elapsed, cpu_elapsed = time.perf_counter_ns() - began, time.process_time_ns() - cpu_began
        timing[family] = {"wall_ns": elapsed, "cpu_ns": cpu_elapsed}
        if not ranked:
            record(
                {
                    "type": "selection",
                    "family": family,
                    "status": "INCONCLUSIVE",
                    "search_wall_ns": elapsed,
                    "search_cpu_ns": cpu_elapsed,
                }
            )
            continue
        rank, config = min(ranked, key=lambda item: item[0])
        chosen[family] = config
        validation_cost[family] = rank[0]
        record(
            {
                "type": "selection",
                "family": family,
                "policy": config.id,
                "status": "SELECTED",
                "validation_estimated_total_ns": rank[0],
                "search_wall_ns": elapsed,
                "search_cpu_ns": cpu_elapsed,
            }
        )
    if "flow" not in chosen or "serial" not in chosen:
        raise Inconclusive("required policy selection unavailable")
    # Baseline identity is fixed by validation, never by test comparisons.
    competitors = [config for family, config in chosen.items() if family != "flow"]
    chosen["best_baseline"] = min(
        competitors,
        key=lambda config: (
            validation_cost[config.family],
            config.id,
        ),
    )
    record(
        {
            "type": "selection",
            "family": "best_baseline",
            "policy": chosen["best_baseline"].id,
            "status": "SELECTED_ON_VALIDATION",
        }
    )
    return chosen, timing


def zeta_oracle(
    paths: list[tuple[int, ...]],
    nodes: tuple[int, ...],
    costs: Costs,
) -> tuple[Fraction, int]:
    """Independent exhaustive true-cost optimum, restricted to N <= 16."""
    if len(nodes) > 16 or 1 not in nodes:
        raise ValueError("zeta correctness control requires mandatory 1 and N <= 16")
    index = {node: i for i, node in enumerate(nodes)}
    rewards = [0] * (1 << len(nodes))
    for path in paths:
        prefix = 0
        for node in path:
            if node not in index:
                break
            prefix |= 1 << index[node]
            rewards[prefix] += 1
    values = rewards[:]
    for bit in range(len(nodes)):
        for mask in range(1 << len(nodes)):
            if mask & (1 << bit):
                values[mask] += values[mask ^ (1 << bit)]
    best = Fraction(-1)
    checked = 0
    for mask, value in enumerate(values):
        if not mask & (1 << index[1]):
            continue
        chosen = frozenset(node for node, i in index.items() if mask & (1 << i))
        direct = sum(progress(path, chosen) for path in paths)
        if direct != value:
            raise AssertionError("zeta and independent first-missing replay disagree")
        best = max(best, Fraction(value, costs(len(chosen))))
        checked += 1
    return best, checked


def audit() -> dict:
    rng, costs, subsets = random.Random(86003), Costs(100, 510), 0
    for k in range(1, 6):
        nodes = universe(k)
        paths = []
        for _ in range(12):
            order = list(range(1, k))
            rng.shuffle(order)
            mask, path = 1, [1]
            for bit in order:
                mask |= 1 << bit
                path.append(mask)
            paths.append(tuple(path[: rng.randint(1, k)]))
        best, checked = zeta_oracle(paths, nodes, costs)
        subsets += checked
        plan = choose_plan([(1, p) for p in paths], nodes, costs.a, costs.b, mandatory={1})
        if Fraction(sum(progress(p, plan.selected) for p in paths), costs(len(plan.selected))) < (
            best / costs.kappa
        ):
            raise AssertionError("affine envelope transfer bound failed")
    paths = [(1, 3, 7), (1, 5, 7), (1, 5, 13)]
    counts = Counter(node for path in paths for node in path)
    nodes = sorted(counts)
    for degree in (0, 1):
        for size in range(1, len(nodes) + 1):
            selected, result = fit_spiffy(paths, size, degree)
            if result["status"] != "OPTIMAL":
                raise AssertionError("small MILP did not finish")
            exact = max(
                score(frozenset(choice), counts, degree)
                for choice in itertools.combinations(nodes, size)
                if 1 in choice
                and all(node == 1 or set(parents(node)).intersection(choice) for node in choice)
            )
            if score(selected, counts, degree) != exact:
                raise AssertionError("MILP differs from independent exhaustive connected optimum")
    dummy = object.__new__(Tables)
    dummy.costs = costs
    dummy.observed = frozenset({(3, -1)})
    case = Case(
        "audit",
        "test",
        "synthetic",
        (
            Root(3, 0, (1, 5, 7)),
            Root(2, 0, (1, 3)),
            Root(1, 0, (1,)),
            Root(1, 0, ()),
        ),
        "event_limit",
        0,
        0,
    )
    if replay(case, Config("serial"), dummy)["estimated_inference_ns"] != 4 * costs.c1:
        raise AssertionError("serial cached-head/endpoint accounting failed")
    if dummy.select(Config("ssd_mix", sizes=(3,)), case.roots[0]) != frozenset({1, 3, 5, 7}):
        raise AssertionError("SSD mix common-pool formula failed")
    dummy.plans = {("spiffy_j0", 3, -1, 12): frozenset({1, 3, 5, 7})}
    gm_root = Root(3, 0, (1, 5, 7), (0.99, 0.95, 0.8))
    if dummy.select(Config("spiffy_j0_gm", sizes=(2,)), gm_root) != frozenset({1, 3}):
        raise AssertionError("root-only geometric pruning formula/ties failed")
    crossing = Case(
        "cross-block",
        "test",
        "synthetic",
        (
            Root(1, 0, (1,)),
            Root(3, 0, (1, 3)),
            Root(2, 0, (1,)),
            Root(1, 0, ()),
        ),
        "generation_complete",
        0,
        0,
    )
    if replay(crossing, Config("serial"), dummy)["estimated_inference_ns"] != 4 * costs.c1:
        raise AssertionError("successor head across a block boundary was dropped")
    if progress((1, 5, 7), frozenset({1, 3, 7})) != 1:
        raise AssertionError("replay incorrectly skipped a missing predecessor")
    return {
        "status": "PASS",
        "seed": 86003,
        "zeta_subsets": subsets,
        "milp_exhaustive_cases": 2 * len(nodes),
        "scope": "CPU correctness only",
    }


def run(input_path: Path, record):
    import importlib.metadata

    began, cpu_began = time.perf_counter_ns(), time.process_time_ns()
    profile = HERE / "profile-v1.jsonl"
    record(
        {
            "type": "producer",
            "source_sha256": digest(Path(__file__)),
            "planner_sha256": digest(HERE / "planner.py"),
            "input_sha256": digest(input_path),
            "profile_sha256": digest(profile),
            "python": sys.version,
            "packages": {
                name: importlib.metadata.version(name) for name in ("scipy", "numpy", "networkx")
            },
            "K": K,
            "D_grid": list(D_GRID),
            "N_grid": list(N_GRID),
            "context_threshold": 0.95,
            "context_bins": [[0, 1], [2, 3], [4, 8]],
            "milp_time_limit_seconds": MILP_SECONDS,
            "milp_relative_gap": 0.0,
            "gm_pruning": {
                "base_D": 12,
                "leaf_summary": "local_score",
                "mandatory": [1],
                "tie_break": "integer mask ascending",
                "connectivity_repair": False,
                "scope": "explicit online-score adaptation, not full Spiffy",
            },
            "scope": "native serial capture plus profile-based CPU replay; no decoder timing",
        }
    )
    costs = read_costs(profile)
    record(
        {
            "type": "cost_model",
            "c1_ns": costs.c1,
            "c8_ns": costs.c8,
            "a_ns": costs.a,
            "b_ns": costs.b,
            "kappa": str(costs.kappa),
            "cost_ns": [costs(m) for m in range(1, 129)],
        }
    )
    cases, _ = read_capture(input_path)
    capture_ns = sum(
        case.capture_head_ns for case in cases if case.split in {"train", "validation"}
    )
    capture_wall_ns = sum(
        case.capture_wall_ns for case in cases if case.split in {"train", "validation"}
    )
    tables = Tables(cases, costs, record)
    selected, search_timing = select_validation(cases, tables, record)
    preparation_ns = time.perf_counter_ns() - began
    preparation_cpu_ns = time.process_time_ns() - cpu_began
    # Subtract measured baseline-specific fit/search intervals; shared parsing,
    # ranks, bookkeeping, and all flow fit/search remain charged to the candidate.
    baseline_fit_ns = sum(
        value["wall_ns"] for family, value in tables.fit_by_family.items() if family != "flow"
    )
    baseline_search_ns = sum(
        value["wall_ns"] for family, value in search_timing.items() if family != "flow"
    )
    flow_shared_ns = preparation_ns - baseline_fit_ns - baseline_search_ns
    if flow_shared_ns < 0:
        raise AssertionError("preparation intervals overlap")
    setup_ns = capture_wall_ns + flow_shared_ns
    record(
        {
            "type": "preparation",
            "train_validation_capture_head_ns": capture_ns,
            "train_validation_capture_wall_ns": capture_wall_ns,
            "offline_wall_ns": preparation_ns,
            "offline_cpu_ns": preparation_cpu_ns,
            "fit_wall_ns": tables.fit_wall_ns,
            "fit_cpu_ns": tables.fit_cpu_ns,
            "fit_by_family": {key: dict(value) for key, value in tables.fit_by_family.items()},
            "validation_search": search_timing,
            "candidate_setup_ns": setup_ns,
            "candidate_flow_shared_offline_ns": flow_shared_ns,
            "accounting": "integral capture plus flow/shared CPU; baseline inference only in gate",
        }
    )
    totals = Counter()
    inference_totals = Counter()
    by_task_family: dict[str, Counter] = {}
    test = [case for case in cases if case.split == "test"]
    for family, config in selected.items():
        for case in test:
            replay_began, replay_cpu_began = time.perf_counter_ns(), time.process_time_ns()
            row = replay(case, config, tables, detailed=True)
            row["replay_wall_ns"] = time.perf_counter_ns() - replay_began
            row["replay_cpu_ns"] = time.process_time_ns() - replay_cpu_began
            totals[family] += row["estimated_total_ns"]
            inference_totals[family] += row["estimated_inference_ns"]
            by_task_family.setdefault(case.family, Counter())[family] += row["estimated_total_ns"]
            record({"type": "replay", "selected_family": family, "policy": config.id, **row})
    comparison = "INCONCLUSIVE" if tables.failures else "COMPLETE"
    gates = []
    for task_family, values in sorted(by_task_family.items()):
        count = sum(case.family == task_family for case in test)
        own = Fraction(values["flow"]) + Fraction(count * setup_ns, 1000)
        competitors = {
            family: value
            for family, value in values.items()
            if family not in {"flow", "best_baseline"}
        }
        passes = all(own <= Fraction(9 * value, 10) for value in competitors.values())
        differences = {
            family: Fraction(value - values["flow"], count) for family, value in competitors.items()
        }
        gates.append(
            {
                "task_family": task_family,
                "cases": count,
                "flow_plus_amortized_setup_ns": str(own),
                "selected_baseline_inference_plus_selection_ns": competitors,
                "pass": passes,
                "break_even_requests_vs_baseline": {
                    family: str(Fraction(setup_ns, 1) / saving) if saving > 0 else None
                    for family, saving in differences.items()
                },
                "criterion": "flow+setup/1000 <= 90% of EVERY validation-selected family",
            }
        )
    record(
        {
            "type": "result",
            "status": comparison,
            "test_cases": len(test),
            "milp_failures": tables.failures,
            "test_estimated_inference_ns": dict(inference_totals),
            "test_estimated_inference_plus_selection_ns": dict(totals),
            "candidate_setup_ns": setup_ns,
            "amortization_requests": 1000,
            "flow_mean_plus_setup_per1000_ns": str(
                Fraction(totals["flow"], len(test)) + Fraction(setup_ns, 1000)
            ),
            "baseline_mean_inference_ns": str(Fraction(totals["best_baseline"], len(test))),
            "family_gates": gates,
            "potential_gate": "INCONCLUSIVE"
            if tables.failures
            else ("PASS" if all(gate["pass"] for gate in gates) else "FAIL"),
            "scope": "prospective CPU replay estimate; no accelerated decoder or measured gain",
        }
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    if args.audit:
        if args.input or args.output:
            parser.error("--audit does not read captures or write replay results")
        print(json.dumps(audit(), sort_keys=True, allow_nan=False))
        return
    if not args.input or not args.output:
        parser.error("require --input and --output, or --audit")
    with args.output.open("x", encoding="utf-8") as output:

        def record(value):
            output.write(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")
            output.flush()

        try:
            run(args.input, record)
        except Inconclusive as exc:
            record({"type": "result", "status": "INCONCLUSIVE", "reason": str(exc)})
        except BaseException as exc:
            record({"type": "error", "status": "FAIL", "reason": repr(exc)})
            raise


if __name__ == "__main__":
    main()
