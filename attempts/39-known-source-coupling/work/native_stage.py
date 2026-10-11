"""Read-only pinned generator boundary; do not alter native locals or tokens."""

import ast
import inspect
import textwrap
from types import GeneratorType

from .native_state import Candidate


def yield_sites(function, expected_count):
    lines, start = inspect.getsourcelines(inspect.unwrap(function))
    nodes = ast.walk(ast.parse(textwrap.dedent("".join(lines))))
    locations = sorted(start + node.lineno - 1 for node in nodes if isinstance(node, ast.Yield))
    if len(locations) != expected_count:
        raise ValueError("native yield layout changed")
    return dict(
        fast=locations[0],
        fallback=locations[-2],
        terminal=locations[-1],
        failures=tuple(locations[1:-2]),
    )


def step_done(iterator, complete, fallback_count, sites):
    for _ in range(4):
        frame = iterator.gi_frame
        if frame is None:
            raise ValueError("missing suspended native frame")
        values = frame.f_locals
        if "_n_transfer_this_step" in values:
            if values["i"] != 0 or values["num_block"] != 0:
                raise ValueError("crossed first native neural step")
            committed = values["_regular_cover_committed"]
            remaining = values["_n_transfer_this_step"] - committed
            line = frame.f_lineno
            if line == sites["fallback"]:
                fallback_count += 1
            elif line != sites["fast"] and line not in (*sites["failures"], sites["terminal"]):
                raise ValueError("unknown native yield site")
            done = complete or line in (*sites["failures"], sites["terminal"])
            return done or fallback_count >= remaining, fallback_count
        nested = values.get("gen")
        if not isinstance(nested, GeneratorType):
            raise ValueError("unknown native generator wrapper")
        iterator = nested
    raise ValueError("too many generator wrappers")


class StageCandidate(Candidate):
    def __init__(self, factory, seed, device, sites):
        super().__init__(factory, seed, device)
        self.sites = sites

    def pause(self):
        """One RNG scope, snapshots at first/boundary only; no second forward."""
        if self.first is not None or self.ended:
            raise ValueError("first-step pause requires a fresh candidate")
        with self.streams():
            last = None
            fallback_count = 0
            for tokens, rejected, complete in self.iterator:
                if self.first is None:
                    self.first = tokens.clone(), tuple(tuple(x) for x in rejected), bool(complete)
                last = tokens, rejected, complete
                done, fallback_count = step_done(
                    self.iterator, bool(complete), fallback_count, self.sites
                )
                if done:
                    break
            else:
                self.ended = True
            if last is not None:
                tokens, rejected, complete = last
                self.current = tokens.clone(), tuple(tuple(x) for x in rejected), bool(complete)
            return self.current


def body_key(snapshot, input_length):
    if snapshot is None:
        return ("NO_YIELD",)
    ids = snapshot[0][0, input_length:].tolist()
    return next(
        ((i, t) for i, t in enumerate(ids) if t not in (126336, 126081, 126348)), ("NO_BODY",)
    )
