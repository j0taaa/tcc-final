"""Pure predeclared gates; incomplete controls can reject but never award wins."""

from statistics import median


def metrics(rows, n, method):
    chosen = [
        r for r in rows if r.get("N") == n and r.get("method") == method and r.get("kind") == "warm"
    ]
    if (
        len(chosen) != 3
        or {r.get("rep") for r in chosen} != {0, 1, 2}
        or any(r.get("status") != "COMPLETE" for r in chosen)
    ):
        return None
    chosen.sort(key=lambda r: r["rep"])
    walls = [r["wall_ns"] for r in chosen]
    peaks = [r["workspace_bytes"] for r in chosen]
    if min(walls) <= 0 or min(peaks) <= 0:
        return None
    return {"median": median(walls), "wall": walls, "peak": max(peaks)}


def cell(rows, n, candidate, controls):
    c = metrics(rows, n, candidate)
    known = [metrics(rows, n, m) for m in controls]
    available = [v for v in known if v is not None]
    if c is None:
        failed = any(
            r.get("N") == n
            and r.get("method") == candidate
            and r.get("status") in ("ERROR", "REFUSED")
            for r in rows
        )
        return {"win": False, "possible": not failed, "complete": False}
    speed = all(
        c["median"] <= 0.8 * x["median"]
        and all(a < b for a, b in zip(c["wall"], x["wall"], strict=True))
        and c["peak"] <= 1.10 * x["peak"]
        for x in available
    )
    memory = all(
        c["peak"] <= 0.75 * x["peak"] and c["median"] <= 1.10 * x["median"] for x in available
    )
    complete = bool(controls) and len(available) == len(controls)
    return {
        "win": complete and (speed or memory),
        "possible": speed or memory,
        "complete": complete,
        "speed": complete and speed,
        "memory": complete and memory,
    }


def analyze(rows, ns, candidates, controls):
    cells = {c: {str(n): cell(rows, n, c, controls) for n in ns} for c in candidates}
    wins = {c: sum(r["win"] for r in states.values()) for c, states in cells.items()}
    possible = {c: sum(r["possible"] for r in states.values()) for c, states in cells.items()}
    return {
        "cells": cells,
        "wins": wins,
        "possible": possible,
        "gate": any(v >= 3 for v in wins.values()),
        "negative_shortcut": all(v < 3 for v in possible.values()),
    }
