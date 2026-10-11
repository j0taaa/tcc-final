"""Opt-in real CPU/CUDA randomness audit; no neural model or benchmark."""

import random
from types import SimpleNamespace

import numpy as np
import torch

from .native_pilot import first_key
from .native_state import Candidate, InitialHeadCache


def main():
    for device in ("cpu", "cuda:0"):
        cpu = torch.random.get_rng_state().clone()
        gpu = torch.cuda.get_rng_state().clone()
        py, np_state = random.getstate(), np.random.get_state()

        def factory(device=device):
            tensor = torch.zeros((1, 4), device=device, dtype=torch.long)
            for i in range(4):
                tensor[0] = torch.tensor(
                    [
                        torch.randint(0, 1000, ()).item(),
                        torch.randint(0, 1000, (), device=device).item(),
                        random.randrange(1000),
                        int(np.random.randint(1000)),
                    ],
                    device=device,
                )
                yield tensor, [(i, ["original"])], i == 3

        for seed in (0, 1, 126336, 2**32 - 1):
            a, b = (Candidate(factory, seed, device) for _ in range(2))
            a.advance()
            original_first = a.first[0].clone()
            other = Candidate(factory, seed ^ 42, device)
            other.advance()
            other.close()
            a.finish()
            b.finish()
            assert torch.equal(a.current[0], b.current[0])
            assert torch.equal(a.first[0], b.first[0])
            assert torch.equal(original_first, a.first[0])
            assert a.current[1:] == b.current[1:]
            assert a.current[2] and a.ended and b.ended
            assert a.advance() is None and a.finish() is a.current
            a.close()
            b.close()
        calls = []

        def model(inputs, calls=calls, device=device):
            calls.append(inputs.clone())
            return SimpleNamespace(logits=torch.ones((1, 4), device=device))

        model.device = torch.device(device)
        cached = InitialHeadCache(model)
        inputs = torch.zeros((1, 4), device=device, dtype=torch.long)
        cached(inputs).logits.fill_(10)
        assert torch.equal(cached(inputs).logits, torch.ones((1, 4), device=device))
        cached(inputs + 1)
        cached(inputs + 1)
        assert cached.queries == 4 and cached.forwards == len(calls) == 3
        snapshot = torch.tensor([[9, 8, 126336, 41, 42]], device=device), (), False
        assert first_key(snapshot, 2) == (1, 41)
        assert first_key((snapshot[0][:, :3], (), False), 2) == ("NO_PROGRESS",)
        assert first_key(None, 2) == ("NO_YIELD",)
        assert torch.equal(cpu, torch.random.get_rng_state())
        assert torch.equal(gpu, torch.cuda.get_rng_state())
        assert py == random.getstate()
        assert all(
            np.array_equal(a, b) for a, b in zip(np_state, np.random.get_state(), strict=True)
        )
    print("PASS original first/final IDs and private CPU/CUDA/Python/NumPy tapes; no model")


if __name__ == "__main__":
    main()
