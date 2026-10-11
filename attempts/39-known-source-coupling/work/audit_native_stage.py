"""Opt-in CPU/CUDA actual wrapper boundary tests; no model inference."""

import random

import numpy as np
import torch

from .native_stage import StageCandidate, body_key, yield_sites
from .native_state import Candidate


def main():
    for device in ("cpu", "cuda:0"):
        for fast, failure in ((2, False), (1, False), (0, False), (0, True)):
            calls = []

            @torch.no_grad()
            def factory(device=device, fast=fast, failure=failure, calls=calls):
                tokens = torch.zeros((1, 4), dtype=torch.long, device=device)
                num_block = 0
                _n_transfer_this_step = 2
                for i in range(2):
                    calls.append((i, num_block))
                    _regular_cover_committed = fast
                    if fast:
                        tokens[0] = torch.randint(0, 1000, (4,), device=device)
                        yield tokens, [], False
                    if _regular_cover_committed < _n_transfer_this_step:
                        for j in range(_n_transfer_this_step - _regular_cover_committed):
                            j = 0  # Actual EPIC resets its transfer-loop local to the batch row.
                            tokens[0] = torch.tensor(
                                [
                                    torch.randint(0, 1000, ()).item(),
                                    torch.randint(0, 1000, (), device=device).item(),
                                    random.randrange(1000),
                                    int(np.random.randint(1000)),
                                ],
                                device=device,
                            )
                            if failure:
                                yield tokens, [(j, ["original"])], False
                                return
                            yield tokens, [(j, ["original"])], False
                yield tokens, [], True

            cpu, gpu = torch.random.get_rng_state().clone(), torch.cuda.get_rng_state().clone()
            py, np_state = random.getstate(), np.random.get_state()
            for seed in (0, 126336, 2**32 - 1):
                before = len(calls)
                stage = StageCandidate(factory, seed, device, yield_sites(factory, 4))
                stage.pause()
                assert len(calls) - before == 1
                assert not stage.current[0].requires_grad
                first = stage.first[0].clone()
                stage.finish()
                ordinary = Candidate(factory, seed, device)
                ordinary.finish()
                assert torch.equal(stage.first[0], first)
                assert torch.equal(stage.first[0], ordinary.first[0])
                assert torch.equal(stage.current[0], ordinary.current[0])
                assert stage.current[1:] == ordinary.current[1:]
                try:
                    stage.pause()
                except ValueError:
                    pass
                else:
                    raise AssertionError("second pause accepted")
                stage.close()
                ordinary.close()
            assert torch.equal(cpu, torch.random.get_rng_state())
            assert torch.equal(gpu, torch.cuda.get_rng_state())
            assert py == random.getstate()
            assert all(
                np.array_equal(x, y) for x, y in zip(np_state, np.random.get_state(), strict=True)
            )
        snapshot = torch.tensor([[7, 126081, 126336, 126348, 41, 42]], device=device), (), False
        assert body_key(snapshot, 1) == (3, 41)
        assert body_key((snapshot[0][:, :4], (), False), 1) == ("NO_BODY",)
    print(
        "PASS fast/fallback/terminal-failure first-step boundaries, "
        "private tapes and original IDs; no model"
    )


if __name__ == "__main__":
    main()
