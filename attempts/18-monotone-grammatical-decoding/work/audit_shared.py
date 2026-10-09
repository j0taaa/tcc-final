"""Opt-in independent full-sort and native/SAT trajectory correctness audit."""

import argparse
import hashlib
import json
import random
from pathlib import Path

import torch
from native_queries import NativeCountWarm, NativeLex, NativePrefix
from native_sat import SatPrefix
from shared_fastpath import complete_point, keep_engine, stable_topk
from test_correctness import oracle, setup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    seed = 2026100920
    torch.set_flush_denormal(False)
    rng = random.Random(seed)
    gen = torch.Generator().manual_seed(seed)
    for i in range(200):
        width = (16, 29, 100, 50258)[i % 4]
        row = torch.randint(0, 5, (width,), generator=gen).double()
        if i % 3 == 0:
            row = torch.rand(width, generator=gen, dtype=torch.float64)
        if i % 7 == 0:
            row.zero_()
        expected = tuple(row.argsort(descending=True, stable=True)[:16].tolist())
        assert stable_topk(row, 16) == expected
    plan, valid = setup(
        (b"[", b"[]", b"]", b"0", b"00", b"0]", b" ", b"0"),
        ((0, 1), (0, 1, 2, 3, 4, 7), (1, 2, 3, 5, 6, 7)),
    )
    for _ in range(40):
        engines = [
            NativeLex(plan.state, compressed=True),
            NativePrefix(plan.state, compressed=True),
            NativeCountWarm(plan.state, compressed=True),
            SatPrefix(plan),
        ]
        canvas = [None] * 3
        while None in canvas:
            proposals = [
                (p, rng.choice(row), rng.choice((0.1, 0.8, 0.9)))
                for p, row in enumerate(plan.state.support.rows)
                if canvas[p] is None
            ]
            proposals.sort(key=lambda p: (-p[2], p[0], p[1]))
            threshold, cap = rng.choice((0.0, 0.8, 1.0)), rng.randrange(1, 4)
            expected = oracle(valid, canvas, proposals, threshold, cap)
            point = complete_point(
                canvas,
                plan.state.support.rows,
                plan.state.tokenizer_adapter,
                proposals,
                threshold=threshold,
                cap=cap,
            )
            for engine in engines:
                if point is None:
                    actual = engine.transition(proposals, threshold=threshold, cap=cap)
                else:
                    actual, word = point
                    keep_engine(engine, actual, word)
                assert actual == expected, (type(engine).__name__, actual, expected)
            for p, t in expected:
                canvas[p] = t
    tiny, _ = setup((b"[", b"0", b"1", b"]"), ((0,), (1, 2), (3,)))
    native = NativeLex(tiny.state, compressed=True)
    for common in (0, 300, 1073):
        proposals = [(0, 0, 0.9)] * common + [(1, 2, 0.8), (1, 1, 0.8)]
        assert native.solve([None] * 3, proposals) == (0, 2, 3)
    names = (
        "audit_shared.py",
        "native_queries.py",
        "trie_lattice.py",
        "shared_fastpath.py",
        "grammar_selectors.py",
        "native_sat.py",
        "test_correctness.py",
    )
    evidence = dict(
        kind="correctness only, no model or performance experiment",
        seed=seed,
        partial_topk_independent_fullsort_comparisons=200,
        native_rust_and_sat_independent_json_trajectories=40,
        dyadic_primary_priority_widths=[2, 302, 1075],
        source_sha256={
            name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in names
        },
    )
    args.output.write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({k: v for k, v in evidence.items() if k != "source_sha256"}))


if __name__ == "__main__":
    main()
