"""Explicit fixed-bit consumer helpers; no model, labels or parameter updates."""

import numpy as np

from .two_stage import json_text


def extent(width, fixed, eos):
    if any(type(i) is not int or not 0 <= i < width for i in fixed):
        raise ValueError("fixed positions outside the original canvas")
    stops = [i for i, v in fixed.items() if v == eos]
    if len(stops) > 1 or (stops and max(fixed) > stops[0]):
        raise ValueError("a fixed original ID would be truncated by EOT")
    return stops[0] + 1 if stops else width


def terminal(language, width, fixed):
    end = extent(width, fixed, language.eos)
    if fixed.get(end - 1) == language.eos and all(i in fixed for i in range(end)):
        word = tuple(fixed[i] for i in range(end))
        json_text(language, word)
        return word
    return None


def assemble(probabilities, positions, fixed, length, vocabulary_size):
    positions = tuple(positions)
    if positions != tuple(i for i in range(length) if i not in fixed):
        raise ValueError("queried positions must exactly match explicit active bits")
    if probabilities.shape != (len(positions), vocabulary_size):
        raise ValueError("full original-V probabilities required at every queried slot")
    rows = np.zeros((length, vocabulary_size), dtype=np.float64)
    for i, v in fixed.items():
        if not 0 <= i < length or type(v) is not int or not 0 <= v < vocabulary_size:
            raise ValueError("fixed original ID outside the active prefix extent")
        rows[i, v] = 1
    rows[list(positions)] = probabilities
    return rows


def release(plan, planner, rng):
    word = plan.sample_prefix(planner.weights, rng, minimum=max(planner.fixed, default=-1))
    eligible = [i for i in range(len(word)) if planner.active[i]]
    if not eligible:
        raise AssertionError("nonterminal prefix has no eligible anchor")
    anchor = int(rng.choice(eligible))
    uniforms = rng.random(len(eligible))
    action = tuple(
        (i, word[i])
        for i, coin in zip(eligible, uniforms, strict=True)
        if i == anchor or coin < planner.gates[i, word[i]]
    )
    following = {**planner.fixed, **dict(action)}
    if (
        not action
        or len(following) <= len(planner.fixed)
        or any(i >= len(word) or word[i] != v for i, v in following.items())
    ):
        raise AssertionError("prefix release changed or truncated an original fixed ID")
    return word, anchor, action, following
