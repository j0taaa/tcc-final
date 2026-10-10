"""Exact proportional strata; only identical histories coordinate future draws."""

from collections import defaultdict
from dataclasses import dataclass
from random import Random


@dataclass(frozen=True)
class Kernel:
    total: int
    unrank: object


def draw_batch(kernel, size, rng, *, stratified=True):
    """Uniform marginal for every label, even when size does not divide total.

    unrank must be deterministic. This is not systematic sampling with one
    shared phase, nor coordinate-wise Latin hypercube sampling.
    """
    if type(size) is not int or size < 1:
        raise ValueError("batch size must be a positive integer")
    if type(kernel.total) is not int or kernel.total < 1:
        raise ValueError("kernel must have positive integer mass")
    if not isinstance(rng, Random):
        raise TypeError("an explicit Random instance is required")
    if not callable(kernel.unrank):
        raise TypeError("unrank must be a deterministic callable")
    if stratified:
        tickets = [(j * kernel.total + rng.randrange(kernel.total)) // size for j in range(size)]
        rng.shuffle(tickets)
    else:
        tickets = [rng.randrange(kernel.total) for _ in range(size)]
    return tuple(kernel.unrank(ticket) for ticket in tickets)


def decode_batch(kernel_for, is_terminal, size, max_steps, rng, *, stratified=True):
    """Return full action histories and explicit terminal flags.

    kernel_for(history) is a pure original decoder kernel, never a function of
    other candidates or the verifier. Complete histories remain distinct even
    if canvases reconverge. IID uses identical preparation-sharing rules.
    """
    if type(size) is not int or size < 1 or type(max_steps) is not int or max_steps < 0:
        raise ValueError("invalid size or finite horizon")
    histories = [()] * size
    for _ in range(max_steps):
        groups = defaultdict(list)
        for i, history in enumerate(histories):
            if not is_terminal(history):
                groups[history].append(i)
        if not groups:
            break
        for history, labels in groups.items():
            actions = draw_batch(kernel_for(history), len(labels), rng, stratified=stratified)
            for label, action in zip(labels, actions, strict=True):
                histories[label] = (*history, action)
    return tuple(histories), tuple(bool(is_terminal(h)) for h in histories)
