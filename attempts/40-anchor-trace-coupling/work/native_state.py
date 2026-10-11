"""Suspend the unmodified native generator; no successful-event filtering."""

import random
from contextlib import contextmanager
from types import SimpleNamespace

import numpy as np
import torch


class Candidate:
    """Original generator/control locals plus private, resumable RNG tapes."""

    def __init__(self, factory, seed, device):
        self.iterator = iter(factory())
        device = torch.device(device)
        self.gpu = (
            (device.index if device.index is not None else torch.cuda.current_device())
            if device.type == "cuda"
            else None
        )
        self.cpu_rng = torch.Generator().manual_seed(seed).get_state()
        self.gpu_rng = (
            torch.Generator(device=device).manual_seed(seed).get_state()
            if self.gpu is not None
            else None
        )
        self.py_rng = random.Random(seed).getstate()
        self.np_rng = np.random.RandomState(seed % 2**32).get_state()
        self.ended = False
        self.current = None
        self.first = None

    @contextmanager
    def streams(self):
        previous_py, previous_np = random.getstate(), np.random.get_state()
        with torch.random.fork_rng(devices=[] if self.gpu is None else [self.gpu]):
            torch.random.set_rng_state(self.cpu_rng)
            if self.gpu is not None:
                torch.cuda.set_rng_state(self.gpu_rng, self.gpu)
            random.setstate(self.py_rng)
            np.random.set_state(self.np_rng)
            try:
                yield
            finally:
                self.cpu_rng = torch.random.get_rng_state().clone()
                if self.gpu is not None:
                    self.gpu_rng = torch.cuda.get_rng_state(self.gpu).clone()
                self.py_rng, self.np_rng = random.getstate(), np.random.get_state()
                random.setstate(previous_py)
                np.random.set_state(previous_np)

    def advance(self):
        if self.ended:
            return None
        with self.streams():
            try:
                tokens, rejected, complete = next(self.iterator)
            except StopIteration:
                self.ended = True
                return None
            self.current = tokens.clone(), tuple(tuple(x) for x in rejected), bool(complete)
            if self.first is None:
                self.first = self.current
            return self.current

    def finish(self, on_first=None):
        """Exhaust unchanged iterator in one RNG scope; no per-yield clones."""
        if self.ended:
            return self.current
        with self.streams():
            last = None
            for tokens, rejected, complete in self.iterator:
                if self.first is None:
                    self.first = tokens.clone(), tuple(tuple(x) for x in rejected), bool(complete)
                    if on_first is not None:
                        on_first(self.first)
                last = tokens, rejected, complete
            if last is not None:
                tokens, rejected, complete = last
                self.current = tokens.clone(), tuple(tuple(x) for x in rejected), bool(complete)
            self.ended = True
            return self.current

    def close(self):
        if not self.ended:
            with self.streams():
                self.iterator.close()
        self.ended = True


class InitialHeadCache:
    """Only memoize the common initial forward; never share mutable logits."""

    def __init__(self, model):
        self.model, self.device = model, model.device
        self.input = self.head = None
        self.queries = self.forwards = 0

    def __call__(self, inputs):
        self.queries += 1
        if self.input is not None and torch.equal(inputs, self.input):
            return SimpleNamespace(logits=self.head.clone())
        result = self.model(inputs)
        self.forwards += 1
        if self.input is None:
            self.input, self.head = inputs.clone(), result.logits.detach().clone()
        return result
