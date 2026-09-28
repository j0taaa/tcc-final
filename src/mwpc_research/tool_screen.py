"""Small exhaustive MWPC oracle for live dLLM discovery, not a CFG benchmark.

The legal tool catalog is independent of prompts. Exact and confidence-greedy
share complete legal paths, positions, probabilities and a proposal budget.
Model dependencies are confined to the executable experiment driver.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import fsum, isfinite
from random import Random


def tool_catalog(family: str = "simple") -> tuple[str, ...]:
    if family == "nested":
        base = [
            f"{op}({a},{b})" for op in ("add", "sub", "mul") for a in range(4) for b in range(4)
        ]
        base += [f"{op}({a})" for op in ("neg", "abs") for a in range(4)]
        return tuple(
            base
            + [f"{op}({call})" for op in ("neg", "abs") for call in base]
            + [
                f"{op}({call},{a})"
                for op in ("add", "sub", "mul")
                for call in base
                for a in range(4)
            ]
            + [
                f"{op}({a},{call})"
                for op in ("add", "sub", "mul")
                for call in base
                for a in range(4)
            ]
        )
    if family != "simple":
        raise ValueError("unknown tool family")
    return tuple(
        [f"{op}({a},{b})" for op in ("add", "sub", "mul") for a in range(10) for b in range(10)]
        + [f"{op}({a})" for op in ("neg", "abs") for a in range(10)]
    )


def screen_tasks(seed: int, count: int, family: str = "simple") -> tuple[dict[str, str], ...]:
    rng = Random(seed)
    tasks = []
    if family == "nested":
        for i in range(count):
            a, b, c = (rng.randrange(4) for _ in range(3))
            outer = ("add", "sub", "mul", "neg", "abs")[i % 5]
            inner = ("add", "sub", "mul")[i % 3]
            expression = f"{inner}({a},{b})"
            description = {
                "add": f"the sum of {a} and {b}",
                "sub": f"the difference of {a} minus {b}",
                "mul": f"the product of {a} and {b}",
            }[inner]
            expected = f"{outer}({expression},{c})"
            request = {
                "add": f"Add {c} to {description}.",
                "sub": f"Subtract {c} from {description}.",
                "mul": f"Multiply {description} by {c}.",
                "neg": f"Negate {description}.",
                "abs": f"Take the absolute value of {description}.",
            }[outer]
            # Explicit order removes commutative alternatives from exact-match scoring.
            if outer in ("add", "sub", "mul"):
                request += " Put the nested expression in the first argument."
            else:
                expected = f"{outer}({expression})"
            tasks.append({"id": f"nested-{seed}-{i}", "instruction": request, "expected": expected})
        return tuple(tasks)
    if family != "simple":
        raise ValueError("unknown task family")
    for i in range(count):
        op = ("add", "sub", "mul", "neg", "abs")[i % 5]
        a, b = rng.randrange(10), rng.randrange(10)
        instruction = {
            "add": f"Add {a} and {b}.",
            "sub": f"Subtract {b} from {a}.",
            "mul": f"Multiply {a} by {b}.",
            "neg": f"Negate {a}.",
            "abs": f"Take the absolute value of {a}.",
        }[op]
        expected = f"{op}({a},{b})" if op in ("add", "sub", "mul") else f"{op}({a})"
        tasks.append({"id": f"tool-{seed}-{i}", "instruction": instruction, "expected": expected})
    return tuple(tasks)


@dataclass(frozen=True)
class CatalogSelection:
    witness_index: int
    selected_positions: tuple[int, ...]
    objective: float


def select_catalog(
    paths: Sequence[Sequence[int]],
    canvas: Sequence[int | None],
    proposals: Sequence[tuple[int, int, float]],
    *,
    method: str,
) -> CatalogSelection:
    """Exact enumeration or ordered greedy feasibility on identical legal paths."""
    if method not in ("exact", "greedy"):
        raise ValueError("unknown selector")
    if any(len(path) != len(canvas) for path in paths):
        raise ValueError("path length must match canvas")
    positions = [p for p, _, _ in proposals]
    if len(set(positions)) != len(positions):
        raise ValueError("screen requires one proposal per position")
    for position, _, weight in proposals:
        if not 0 <= position < len(canvas) or canvas[position] is not None:
            raise ValueError("proposal must target a free position")
        if not isfinite(weight) or weight < 0:
            raise ValueError("invalid proposal weight")
    feasible = [
        i
        for i, path in enumerate(paths)
        if all(fixed is None or fixed == token for fixed, token in zip(canvas, path, strict=True))
    ]
    if not feasible:
        raise ValueError("infeasible canvas")
    if method == "greedy":
        for position, token, _ in proposals:
            accepting = [i for i in feasible if paths[i][position] == token]
            if accepting:
                feasible = accepting
        witness = feasible[0]
    else:
        witness = max(
            feasible,
            key=lambda i: fsum(w for p, t, w in proposals if paths[i][p] == t),
        )
    matched = tuple(p for p, t, w in proposals if w > 0 and paths[witness][p] == t)
    return CatalogSelection(
        witness, matched, fsum(w for p, t, w in proposals if paths[witness][p] == t)
    )
