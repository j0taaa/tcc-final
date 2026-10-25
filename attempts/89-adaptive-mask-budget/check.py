"""Independent finite enumeration, exact-gap tests and cross-device checks."""
import argparse
import itertools
import json
import time
from pathlib import Path

import numpy as np
import torch
from transformers import AutoTokenizer

from verifier import Verifier, compile_library, compile_tables, grammar_step, insert_masks

HERE = Path(__file__).resolve().parent
MODEL = Path.home() / ".cache/huggingface/hub/models--GSAI-ML--LLaDA-8B-Instruct/snapshots/08b83a6feb34df1a6011b80c3c00c7563e963b07"


def accepted(table, seq):
    q = 0
    for cls in seq:
        q = table[cls, q]
        if q < 0:
            return False
    return q == table.shape[1] - 1


def brute(table, canvas):
    free = [i for i, c in enumerate(canvas) if c < 0]
    for values in itertools.product(range(len(table)), repeat=len(free)):
        seq = list(canvas)
        for p, c in zip(free, values):
            seq[p] = c
        if accepted(table, seq):
            return True
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refusing overwrite")
    start = time.perf_counter()
    lib, build = compile_library(HERE / "../../.cache/a89")
    # Language ab (cc)* d EOS PAD*: non-contiguous lengths before fixed d.
    table = np.array([[1,-1,-1,-1,-1,-1],[-1,2,-1,-1,-1,-1],
                      [-1,-1,3,2,-1,-1],[-1,-1,4,-1,-1,-1],
                      [-1,-1,-1,-1,5,5]], dtype=np.int32)
    cpu, gpu = Verifier(table, lib), Verifier(table, lib, "cuda")
    finite_checks = 0
    for n in range(1, 5):
        for canvas in itertools.product(range(-1, len(table)), repeat=n):
            expected = brute(table, canvas)
            assert cpu.prepare(canvas) == expected
            if finite_checks % 13 == 0:
                assert gpu.prepare(canvas) == expected
            finite_checks += 1
    assert cpu.prepare([0, 1, 3, 4])
    assert not cpu.prepare([0, 1, -1, 3, 4])
    assert cpu.prepare([0, 1, -1, -1, 3, 4])
    assert not cpu.prepare([0, -1, 0, 3, 4])
    rng = np.random.default_rng(89001)
    allocation_checks = 0
    for _ in range(48):
        canvas = rng.integers(-1, 4, size=int(rng.integers(1, 7))).tolist()
        a, da = cpu.allocate(canvas, 4, True)
        b, db = gpu.allocate(canvas, 4, True)
        assert np.array_equal(da, db), (canvas, da, db)
        assert a == b
        if a is not None:
            expanded, _ = insert_masks(canvas, a)
            assert brute(table, expanded)
            assert sum(a) == da[0, 0]
            # Exhaust all strictly cheaper allocations in this tiny language.
            for count in range(sum(a)):
                for gaps in itertools.combinations_with_replacement(range(len(canvas)+1), count):
                    allocation = [gaps.count(i) for i in range(len(canvas)+1)]
                    trial, _ = insert_masks(canvas, allocation)
                    assert not brute(table, trial)
        allocation_checks += 1
    # Test generic recursion and macros independently of model proposals.
    tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True, trust_remote_code=True)
    tables = compile_tables(tokenizer)
    cpu = Verifier(tables["table"], lib)
    gpu = Verifier(tables["table"], lib, "cuda")
    grammar_checks = 0
    for n in range(7):
        for chars in itertools.product('[a",]', repeat=n):
            text = "".join(chars)
            def shape(x):
                return isinstance(x, list) and all(
                    shape(v) if isinstance(v, list) else isinstance(v,str) and
                    all(c.isascii() and c.isalpha() for c in v) for v in x)
            try:
                valid = shape(json.loads(text))
            except (ValueError, TypeError):
                valid = False
            q = grammar_step(0, text, tables["depth"])
            actual = q == tables["table"].shape[1] - 2
            assert actual == valid, text
            grammar_checks += 1
    full_checks, timings = 0, []
    for text in ['[]', '["a"]', '[["a"],["b","c"]]', '[[[]]]', '[""]']:
        tokens = tokenizer.encode(text, add_special_tokens=False) + [126081]
        classes = tables["groups"][tokens].tolist()
        assert min(classes) >= 0
        for _ in range(3):
            canvas = [c if rng.random() < .5 else -1 for c in classes]
            assert cpu.prepare(canvas) == gpu.prepare(canvas)
            for pos, c in enumerate(classes):
                assert cpu.allows(pos, c) == gpu.allows(pos, c)
            t = time.perf_counter()
            a, da = cpu.allocate(canvas, 4, True)
            cpu_time = time.perf_counter() - t
            torch.cuda.synchronize()
            t = time.perf_counter()
            b, db = gpu.allocate(canvas, 4, True)
            torch.cuda.synchronize()
            gpu_time = time.perf_counter() - t
            assert np.array_equal(da, db)
            assert a == b
            timings.append({"tokens":len(canvas),"cpu_allocation_s":cpu_time,
                            "gpu_allocation_s":gpu_time})
            full_checks += 1
    result = dict(status="PASS", finite_checks=finite_checks,
                  tiny_allocation_checks=allocation_checks, grammar_checks=grammar_checks,
                  full_table_checks=full_checks, states=cpu.s,
                  classes=len(tables["table"]), admitted_ids=len(tables["admitted"]),
                  depth_bound=tables["depth"], max_opens=tables["max_open_per_token"],
                  compile=build, table_prepare_seconds=tables["seconds"], timings=timings,
                  total_seconds=time.perf_counter()-start)
    args.output.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
