"""Small original-word enumeration oracle for the shared GPU interval frontend."""

import argparse
import hashlib
import itertools
import json
import math
import subprocess
from fractions import Fraction as F
from pathlib import Path

import numpy as np
import torch

from .interval_frontend import IntervalDAG
from .test_reference import fixture


def exact_suffixes(classes, layers, accepting, rows):
    """Enumerate complete suffix token assignments, independently of a mass DP."""
    results = []
    for p, layer in enumerate(layers):
        values = []
        for initial in range(len(layer)):
            total = F()
            for word in itertools.product(range(len(rows[0])), repeat=len(layers) - p):
                state, weight = initial, F(1)
                for q, token in enumerate(word, p):
                    edges = [
                        (target, cids)
                        for target, cids in layers[q][state]
                        if any(token in classes[c] for c in cids)
                    ]
                    if not edges:
                        break
                    if len(edges) != 1:
                        raise AssertionError("independent oracle found overlapping ID traces")
                    state = edges[0][0]
                    weight *= F(float(rows[q][token]))
                else:
                    total += weight * int(accepting[state])
            values.append(total)
        results.append(values)
    return [*results, [F(int(a)) for a in accepting]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    torch.set_flush_denormal(False)
    cases = [
        ([b"0", b"0", b"[]", b"[[]]", None, None, b" "], (None,) * 3, 4, 5),
        ([b"[", b"]", b"0", b"[]", None, b" "], (0, None, None, None), 4, 4),
        ([b'"', b"\xc3", b"\xa9", b"a", None, None], (0, None, None, None, None), 4, 5),
        ([b"1", b"e", b"0", b" ", None, None], (None, None, None, 4), 4, 5),
    ]
    examples = []
    for words, canvas, eot, pad in cases:
        for salt in (1, 2, 3):
            ref, _ = fixture(words, canvas, eot, pad, salt=salt)
            layers = tuple(
                tuple(tuple((e.target, e.tokens) for e in node) for node in layer)
                for layer in ref.layers
            )
            examples.append((tuple((t,) for t in range(len(words))), layers, (True,), ref.rows))
    small = np.nextafter(0.0, 1.0)
    for value in (small, np.finfo(np.float64).tiny, 1e-30, 0.1, np.nextafter(1.0, 0.0), 1.0, 0.0):
        # Aliases in a whole class, mixed acceptance and repeated suffix states.
        classes = ((0, 1), (2,))
        layers = ((((0, (0,)), (1, (1,))),), (((0, (0, 1)),), ((1, (0, 1)),)))
        rows = ((value, value, value), (value, value, value))
        examples.append((classes, layers, (True, False), rows))
    records, scalar_checks = [], 0
    for case, (classes, layers, accepting, rows) in enumerate(examples):
        dense = np.asarray(rows, dtype=np.float64)
        engine = IntervalDAG(classes, layers, accepting)
        result = engine.query(torch.from_numpy(dense).cuda())
        exact = exact_suffixes(classes, layers, accepting, dense)
        if not result["lower"] <= exact[0][0] <= result["upper"]:
            raise AssertionError("root mass outside certified interval")
        for p, layer in enumerate(exact):
            factor = F(1)
            for scale in result["scales"][: len(layers) - p]:
                factor *= F(scale)
            lower = result["beta_lower"][p].cpu().tolist()
            upper = result["beta_upper"][p].cpu().tolist()
            for lo, truth, hi in zip(lower, layer, upper, strict=True):
                if not F(lo) * factor <= truth <= F(hi) * factor:
                    raise AssertionError("suffix mass outside directed common-scale interval")
                scalar_checks += 1
        for p in range(len(rows)):
            for c, members in enumerate(classes):
                truth = sum((F(float(dense[p, t])) for t in members), F())
                lo, hi = result["class_lower"][p, c].item(), result["class_upper"][p, c].item()
                if not F(lo) <= truth <= F(hi):
                    raise AssertionError("original class mass not enclosed")
                scalar_checks += 1
        records.append(
            dict(
                case=case,
                exact_mass=str(exact[0][0]),
                lower=str(result["lower"]),
                upper=str(result["upper"]),
            )
        )
    # Exercise >one block, unequal class sizes and duplicate-ID/support refusal.
    rng = np.random.default_rng(51)
    for v in (257, 1025):
        classes = (tuple(range(v - 1)), (v - 1,))
        layers = ((((0, (0, 1)),),),)
        rows = rng.random((1, v), dtype=np.float64)
        engine = IntervalDAG(classes, layers, (True,))
        result = engine.query(torch.from_numpy(rows).cuda())
        truth = sum((F(float(x)) for x in rows[0]), F())
        if not result["lower"] <= truth <= result["upper"]:
            raise AssertionError("blocked class reduction did not enclose all original IDs")
        scalar_checks += 1
    refusals = 0
    bad = [
        (((0, 0),), ((((0, (0,)),),),), (True,)),
        (((0,),), ((((0, (0,)), (0, (0,))),),), (True,)),
    ]
    for classes, layers, accepting in bad:
        try:
            IntervalDAG(classes, layers, accepting)
        except ValueError:
            refusals += 1
        else:
            raise AssertionError("malformed partition/graph accepted")
    if refusals != 2 or not all(math.isfinite(s) for s in result["scales"]):
        raise AssertionError("invalid refusal or scale")
    payload = dict(
        status="PASS",
        query_cases=len(examples) + 2,
        exact_scalar_enclosures=scalar_checks,
        malformed_refusals=refusals,
        new_model_forwards=0,
        speed_claim=False,
        goal_met=False,
        torch=torch.__version__,
        cuda=torch.version.cuda,
        gpu=torch.cuda.get_device_name(),
        commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        sources={
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in Path(__file__).parent.glob("*interval*.py")
        },
        records=records,
    )
    (args.output / "summary.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in payload.items() if k != "records"}))


if __name__ == "__main__":
    main()
