"""CPU/CUDA literal generator replay with FAKE heads; not neural evidence."""

import argparse
import hashlib
import itertools
import json
import os
import pickle
import random
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import torch
from constrained_diffusion.constrain_utils import compile_lex_map
from constrained_diffusion.eval.dllm.models.llada import generate_constrained as native
from rustformlang.cfg import CFG

from .native_transition_v4 import Candidate, InitialHeadCache
from .ruin import pair


class Tokenizer:
    """Independent copy of the frozen A31/A32 fake alias/refusal fixture."""

    pieces = ("0", "1", "x", "0", "<eos>", "<mask>", "prompt")

    def __init__(self):
        self.special_tokens_map = {"eos_token": "<eos>"}

    def decode(self, token):
        return self.pieces[int(token)]

    def batch_decode(self, tokens):
        return [self.decode(token) for token in tokens]


class Head:
    def __init__(self, device, valid=False):
        self.device = torch.device(device)
        self.valid = valid

    def __call__(self, tokens):
        logits = (
            torch.tensor(
                [
                    2.2 if self.valid else 0.2,
                    0.1,
                    0.2 if self.valid else 2.2,
                    -2,
                    -1,
                    -torch.inf,
                    -torch.inf,
                ],
                device=self.device,
            )
            .expand(1, tokens.shape[1], -1)
            .clone()
        )
        if int((tokens == 5).sum()) == 1:
            logits[:, :, 4] = 2
        return SimpleNamespace(logits=logits)


def event(row):
    tokens, rejected, complete = row
    # Upstream's second component is a WALL timestamp, not a token decision.
    return tokens.cpu().tolist(), tuple(pos for pos, _elapsed in rejected), bool(complete)


def streams(device):
    gpu = torch.cuda.get_rng_state(device).cpu().numpy().tobytes() if device.type == "cuda" else b""
    return (
        torch.random.get_rng_state().numpy().tobytes(),
        gpu,
        pickle.dumps((random.getstate(), np.random.get_state())),
    )


def probe(device, seed, temperature, max_resamples, steps=2, valid=False):
    device = torch.device(device)
    grammar = CFG.from_text("S -> lexNumber", "S").to_normal_form()
    lexical = compile_lex_map({"lexNumber": "(0|1)"})

    def factory(model):
        return native.generate(
            model,
            torch.tensor([[6]], device=device),
            Tokenizer(),
            grammar,
            lexical,
            prompt_len=1,
            steps=steps,
            gen_length=2,
            block_length=2,
            mask_id=5,
            constrain=True,
            temperature=temperature,
            max_resamples=max_resamples,
        )

    torch.manual_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    expected = tuple(event(row) for row in factory(Head(device, valid)))
    previous = streams(device)
    model = InitialHeadCache(Head(device, valid))
    candidates = []
    rng = random.Random(seed + 340000)

    def draw():
        fresh = seed if not candidates else rng.randrange(2**32)
        c = Candidate(lambda: factory(model), fresh, device)
        c.advance()
        candidates.append(c)
        if streams(device) != previous:
            raise AssertionError("creating/advancing oracle leaked caller RNG")
        return c

    first, second, used = pair(
        draw,
        lambda c: c.current is not None and bool((c.current[0][0, 1:] == 1).any()),
        barrier=3,
        max_draws=12,
    )
    if first is not candidates[0]:
        raise AssertionError("first native payload replaced")
    initial = event(first.current) if first.current is not None else None
    for c in candidates:
        if c is not first and c is not second:
            c.close()
    if initial != (event(first.current) if first.current is not None else None):
        raise AssertionError("auxiliary generators mutated retained first event")
    actual = [] if first.current is None else [event(first.current)]
    while (row := first.advance()) is not None:
        actual.append(event(row))
    second.close()
    first.close()
    if tuple(actual) != expected:
        raise AssertionError("literal first full native trajectory changed")
    if streams(device) != previous:
        raise AssertionError("resume/close leaked caller RNG")
    return dict(
        device=str(device),
        seed=seed,
        temperature=temperature,
        max_resamples=max_resamples,
        steps=steps,
        valid_proposals=valid,
        first_equal=True,
        rng_isolated=True,
        native_events=len(actual),
        complete=bool(actual and actual[-1][2]),
        draws=used,
        fake_head_queries=model.queries,
        fake_forwards=model.forwards,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("refuse to overwrite evidence")
    environment = {
        "CONSTRAINED_DIFFUSION_REGULAR_COVER_BATCH": "1",
        "CONSTRAINED_DIFFUSION_REGULAR_COVER_MIN_BATCH": "2",
        "CONSTRAINED_DIFFUSION_REGULAR_COVER_EXACT": "1",
        "CONSTRAINED_DIFFUSION_DFA_FREE_CHECKER": "1",
    }
    covers = []
    original_cover = native._try_regular_cover_batch_commit_llada

    def observe_cover(*args, **kwargs):
        result = original_cover(*args, **kwargs)
        covers.append(len(result))
        return result

    # Observer delegates literally and is used on reference AND live paths.
    # These are FAKE checks, never competitive timings of this wrapper.
    with (
        patch.dict(os.environ, environment),
        patch.object(native, "_try_regular_cover_batch_commit_llada", observe_cover),
    ):
        rows = [
            probe(*x)
            for x in itertools.product(
                ("cpu", "cuda:0"), range(3), (0.0, 0.5, 1.0), (1, 8), (1, 2), (False, True)
            )
        ]
    if not covers or not any(covers):
        raise AssertionError("regular-cover SUCCESS path was not exercised")
    result = dict(
        scope="FAKE heads, actual unmodified native generator, no neural/timing claim",
        torch=torch.__version__,
        native_env=environment,
        regular_cover_calls=len(covers),
        regular_cover_successes=sum(bool(x) for x in covers),
        rows=rows,
        sources={
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in Path(__file__).parent.glob("*.py")
        },
        upstream_generate_sha256=hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            dict(
                checks=len(rows),
                first_equal=sum(r["first_equal"] for r in rows),
                fake_forwards=sum(r["fake_forwards"] for r in rows),
                regular_cover_successes=sum(bool(x) for x in covers),
            )
        )
    )


if __name__ == "__main__":
    main()
