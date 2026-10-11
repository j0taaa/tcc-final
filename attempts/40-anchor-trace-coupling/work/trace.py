"""Exact paid anchor trace; no helper may call a missing neural input."""

import ast
import inspect
import sys
import textwrap
from types import GeneratorType, SimpleNamespace

from .native_state import Candidate


def input_key(ids):
    return tuple(ids.shape), tuple(ids.detach().cpu().reshape(-1).tolist())


class Trace:
    def __init__(self, model, byte_budget=2 * 1024**3):
        self.model, self.device = model, model.device
        self.byte_budget, self.bytes, self.heads = byte_budget, 0, {}
        self.frozen = False
        self.helper = False
        self.queries = self.hits = self.forwards = 0

    def contains(self, ids):
        return input_key(ids) in self.heads

    def __call__(self, ids):
        self.queries += 1
        key = input_key(ids)
        if key in self.heads:
            self.hits += 1
            return SimpleNamespace(logits=self.heads[key].to(self.device, copy=True))
        if self.helper:
            raise ValueError("missing neural head requested by helper; no forward performed")
        result = self.model(ids)
        self.forwards += 1
        if not self.frozen:
            size = result.logits.numel() * result.logits.element_size()
            size += sys.getsizeof(key) + sum(sys.getsizeof(v) for v in key)
            size += sum(sys.getsizeof(v) for v in (*key[0], *key[1]))
            if self.bytes + size <= self.byte_budget:
                self.heads[key] = result.logits.detach().to("cpu", copy=True)
                self.bytes += size
        return result


def yield_sites(function, expected_count=6):
    lines, start = inspect.getsourcelines(inspect.unwrap(function))
    nodes = ast.walk(ast.parse(textwrap.dedent("".join(lines))))
    sites = sorted(start + n.lineno - 1 for n in nodes if isinstance(n, ast.Yield))
    if len(sites) != expected_count:
        raise ValueError("native yield layout changed")
    return dict(fast=sites[0], fallback=sites[-2], terminal=sites[-1], failures=tuple(sites[1:-2]))


def native_frame(iterator):
    for _ in range(4):
        frame = iterator.gi_frame
        if frame is None:
            raise ValueError("missing suspended native frame")
        if "_n_transfer_this_step" in frame.f_locals:
            return frame
        iterator = frame.f_locals.get("gen")
        if not isinstance(iterator, GeneratorType):
            raise ValueError("unknown generator wrapper")
    raise ValueError("too many generator wrappers")


class CachedCandidate(Candidate):
    def __init__(self, factory, seed, device, sites, trace):
        super().__init__(factory, seed, device)
        self.sites, self.trace = sites, trace
        self.boundary = None

    def pause(self):
        if self.first is not None or self.ended or not self.trace.frozen:
            raise ValueError("cached pause needs a fresh candidate and frozen trace")
        before, step, fallback = self.trace.forwards, None, 0
        if self.trace.helper:
            raise ValueError("overlapping helper scopes are unsupported")
        self.trace.helper = True
        try:
            self._pause(step, fallback)
        finally:
            self.trace.helper = False
        if self.trace.forwards != before:
            raise ValueError("helper crossed uncached neural boundary")
        return self.current

    def _pause(self, step, fallback):
        with self.streams():
            last = None
            for tokens, rejected, complete in self.iterator:
                if self.first is None:
                    self.first = tokens.clone(), tuple(tuple(x) for x in rejected), bool(complete)
                last = tokens, rejected, complete
                frame = native_frame(self.iterator)
                values, line = frame.f_locals, frame.f_lineno
                current_step = values["num_block"], values["i"]
                if current_step != step:
                    step, fallback = current_step, 0
                if line == self.sites["fallback"]:
                    fallback += 1
                elif line != self.sites["fast"] and line not in (
                    *self.sites["failures"],
                    self.sites["terminal"],
                ):
                    raise ValueError("unknown native yield site")
                terminal = complete or line in (*self.sites["failures"], self.sites["terminal"])
                remaining = values["_n_transfer_this_step"] - values["_regular_cover_committed"]
                if terminal or (fallback >= remaining and not self.trace.contains(tokens)):
                    self.boundary = dict(step=step, line=line, terminal=bool(terminal))
                    break
            else:
                self.ended = True
            if last is not None:
                tokens, rejected, complete = last
                self.current = tokens.clone(), tuple(tuple(x) for x in rejected), bool(complete)
