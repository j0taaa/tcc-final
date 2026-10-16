"""Original-word/retained-prefix control replay and a finite full-word law oracle."""

import argparse
import hashlib
import itertools
import json
import subprocess
from collections import Counter
from fractions import Fraction as F
from pathlib import Path
from random import Random

import numpy as np
import torch

from .exact_control import ExactDAG
from .interval_sampler import IntervalSampler
from .test_reference import fixture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    torch.set_flush_denormal(False)
    generator = np.random.default_rng(2026101651)
    cases = [
        ([b"0", b"0", b"[]", b"[[]]", None, None, b" "], (None,) * 3, 4, 5),
        ([b"[", b"]", b"0", b"[]", None, b" "], (0, None, None, None), 4, 4),
        ([b'"', b"\xc3", b"\xa9", b"a", None, None], (0, None, None, None, None), 4, 5),
        ([b"1", b"e", b"0", b" ", None, None], (None, None, None, 4), 4, 5),
    ]
    literal, fallbacks, certified, records = 0, 0, 0, []
    for case, (words, canvas, eot, pad) in enumerate(cases):
        for salt in (1, 3):
            ref, law = fixture(words, canvas, eot, pad, salt=salt)
            layers = tuple(
                tuple(tuple((e.target, e.tokens) for e in node) for node in layer)
                for layer in ref.layers
            )
            control = IntervalSampler(
                tuple((t,) for t in range(len(words))), layers, (True,), block_size=2
            )
            rows = np.array(ref.rows, dtype=np.float64)
            weights = torch.from_numpy(rows).cuda()
            exact = ExactDAG(
                control.engine.classes, control.engine.layers, control.engine.accepting, rows
            )
            for bits in (2, 8, 32):
                count = 32
                source = generator.integers(0, 1 << bits, (count, len(canvas), 3), dtype=np.int64)
                seeds = [Random(case * 10000 + salt * 1000 + i) for i in range(count)]
                result = control.sample(weights, torch.from_numpy(source).cuda(), seeds, bits=bits)
                found = result["tokens"].cpu().tolist()
                for i, word in enumerate(found):
                    expected = exact.sample(
                        source[i].tolist(), bits, Random(case * 10000 + salt * 1000 + i)
                    )
                    if tuple(word) != expected or law[tuple(word)] <= 0:
                        raise AssertionError(
                            "GPU/fallback control changed the true retained-uniform word"
                        )
                    if any(t is not None and word[p] != t for p, t in enumerate(canvas)):
                        raise AssertionError("fixed original ID changed")
                    stop = word.index(eot)
                    if any(t != pad for t in word[stop + 1 :]):
                        raise AssertionError("true EOT/PAD language changed")
                    text = b"".join(words[t] for t in word[:stop]).decode("utf8")
                    json.loads(text, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
                    literal += 1
                fallbacks += result["fallback_count"]
                certified += result["gpu_certified"]
                records.append(
                    dict(
                        case=case,
                        salt=salt,
                        bits=bits,
                        samples=count,
                        gpu_certified=result["gpu_certified"],
                        fallback=result["fallback_count"],
                    )
                )
    # Exact enumeration of ALL4^6 fair-bit prefixes, dyadic full-word law.
    classes = ((0, 1), (2, 3))
    layers = ((((0, (0,)), (0, (1,))),), (((0, (0, 1)),),))
    control = IntervalSampler(classes, layers, (True,), block_size=2)
    source = np.asarray(list(itertools.product(range(4), repeat=6)), dtype=np.int64).reshape(
        -1, 2, 3
    )
    result = control.sample(
        torch.full((2, 4), 0.5, dtype=torch.float64, device="cuda"),
        torch.from_numpy(source).cuda(),
        [Random(i) for i in range(len(source))],
        bits=2,
    )
    words = [tuple(w) for w in result["tokens"].cpu().tolist()]
    observed = Counter(words)
    if (
        result["fallback_count"]
        or len(observed) != 16
        or any(F(count, len(source)) != F(1, 16) for count in observed.values())
    ):
        raise AssertionError("executed full-word fair-bit law differs from exact product target")
    payload = dict(
        status="PASS",
        original_json_replays=literal,
        gpu_certified=certified,
        exact_retained_fallbacks=fallbacks,
        complete_word_prefixes=len(source),
        full_word_events=len(observed),
        new_model_forwards=0,
        speed_claim=False,
        goal_met=False,
        torch=torch.__version__,
        gpu=torch.cuda.get_device_name(),
        commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        sources={
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in Path(__file__).parent.glob("*.py")
        },
        records=records,
    )
    (args.output / "summary.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in payload.items() if k not in ("records", "sources")}))


if __name__ == "__main__":
    main()
