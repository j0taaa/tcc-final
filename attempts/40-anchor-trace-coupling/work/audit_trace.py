"""Opt-in CPU/CUDA original-control/RNG/trace checks; no neural model."""

import random
from types import SimpleNamespace

import numpy as np
import torch

from .frontier_key import choice
from .native_state import Candidate
from .trace import CachedCandidate, Trace, yield_sites


class Head:
    def __init__(self, device):
        self.device, self.calls = torch.device(device), 0

    def __call__(self, ids):
        self.calls += 1
        return SimpleNamespace(
            logits=ids.float().unsqueeze(-1) + torch.arange(8, device=self.device)
        )


@torch.no_grad()
def generator(model):
    x = torch.full((1, 6), 126336, dtype=torch.long, device=model.device)
    num_block = 0  # noqa: F841 - observed read-only by the pinned frame adapter
    for i in range(3):
        logits = model(x).logits
        logits.add_(1)  # A native caller may mutate its own head.
        _n_transfer_this_step = 2
        _regular_cover_committed = int(torch.randint(2, ()).item())
        if _regular_cover_committed:
            x[0, 2 * i] = torch.randint(2, (), device=model.device)
            yield x, (), False
        failure = random.randrange(10000) + int(np.random.randint(10000))
        if failure == -1:
            yield x, (), False
            return
        if failure == -2:
            yield x, (), False
            return
        if failure == -3:
            yield x, (), False
            return
        for j in range(_n_transfer_this_step - _regular_cover_committed):
            j = 0  # Real upstream reuses this name for the batch row.
            index = 2 * i + _regular_cover_committed
            if x[0, index] != 126336:
                index += 1
            x[j, index] = torch.randint(2, (), device=model.device)
            yield x, (), False
    yield x, (), True


def final(candidate):
    candidate.finish()
    return candidate.current[0].clone(), candidate.current[1:]


def audit():
    sites = yield_sites(generator)
    devices = ["cpu"] + (["cuda:0"] if torch.cuda.is_available() else [])
    for device in devices:
        actual = Head(device)
        trace = Trace(actual)
        anchor = Candidate(lambda trace=trace: generator(trace), 0, device)
        anchor_ids, anchor_status = final(anchor)
        assert actual.calls == 3 and len(trace.heads) == 3
        trace.frozen = True
        before = trace.bytes, tuple(trace.heads), actual.calls
        for seed in (0, 1, 126336, 2**32 - 1):
            original = Candidate(lambda device=device: generator(Head(device)), seed, device)
            expected, status = final(original)
            replay = CachedCandidate(
                lambda trace=trace: generator(trace), seed, device, sites, trace
            )
            cpu = torch.random.get_rng_state().clone()
            cuda = torch.cuda.get_rng_state(device).clone() if device != "cpu" else None
            py, np_state = random.getstate(), np.random.get_state()
            calls = actual.calls
            replay.pause()
            assert actual.calls == calls and trace.helper is False
            assert torch.equal(cpu, torch.random.get_rng_state()) and py == random.getstate()
            np_after = np.random.get_state()
            assert np_state[0] == np_after[0] and np_state[2:] == np_after[2:]
            assert np.array_equal(np_state[1], np_after[1])
            if cuda is not None:
                assert torch.equal(cuda, torch.cuda.get_rng_state(device))
            observed, observed_status = final(replay)
            assert torch.equal(expected, observed) and status == observed_status
            if seed == 0:
                assert torch.equal(anchor_ids, observed) and observed_status == anchor_status
                assert actual.calls == calls  # Entire repeated anchor runs on exact hits.
            assert trace.bytes == before[0] and tuple(trace.heads) == before[1]
            # Modifying a delivered clone did not change an immutable stored head.
            initial = torch.full((1, 6), 126336, dtype=torch.long, device=device)
            first = trace(initial).logits
            first.zero_()
            assert trace(initial).logits.sum().item() != 0
        empty = Trace(Head(device), 0)
        empty.frozen = True
        rejected = CachedCandidate(lambda empty=empty: generator(empty), 1, device, sites, empty)
        try:
            rejected.pause()
            raise AssertionError("empty trace silently invoked a neural helper")
        except ValueError as exc:
            assert "no forward performed" in str(exc)
        assert empty.model.calls == 0 and not empty.helper
        rejected.close()
    examples = {
        '{"op":"': ("ROOT_UNKNOWN", "LEFT_UNKNOWN"),
        '{"op":"add",': ("add", "LEFT_UNKNOWN"),
        '{"op":"div","args":[2.0,': ("div", "NUMBER:2"),
        '{"op":"div","args":[2e2,': ("div", "NUMBER:200"),
        '{"op":"sub","args":[2': ("sub", "LEFT_UNKNOWN"),
        '{"op":"add","args":[{"op":"mul",': ("add", "CALL:mul"),
        '{"op":"sub","args":[01,': ("sub", "LEFT_UNKNOWN"),
        '{"op":"sub","args":[1e1025,': ("sub", "LEFT_UNKNOWN"),
    }
    assert all(choice(text) == key for text, key in examples.items())
    print(
        "PASS original CPU/CUDA multi-step IDs/statuses, private RNG, immutable heads, "
        "guarded misses and fixed frontier key"
    )


if __name__ == "__main__":
    audit()
