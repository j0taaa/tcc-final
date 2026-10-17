"""Opt-in toy GPU proof audit; no neural data or performance measurement."""

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

from .frozen_control.exact_control import ExactDAG
from .frozen_control.interval_sampler import IntervalSampler
from .static_frontend import StaticDAG


def json_trie(tokens, eot, pad, length):
    classes, names = [], []
    for token, value in enumerate(tokens):
        if value in names:
            classes[names.index(value)].append(token)
        else:
            names.append(value)
            classes.append([token])
    valid, class_words = set(), set()
    for word in itertools.product(range(len(tokens)), repeat=length):
        if eot not in word:
            continue
        stop = word.index(eot)
        if any(t != pad for t in word[stop + 1 :]) or any(t in (eot, pad) for t in word[:stop]):
            continue
        try:
            raw = b"".join(tokens[t] for t in word[:stop]).decode("utf8")
            json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        except (UnicodeDecodeError, ValueError):
            continue
        valid.add(word)
        class_words.add(tuple(names.index(tokens[t]) for t in word))
    assert valid
    prefixes = [sorted({word[:p] for word in class_words}) for p in range(length)]
    layers = []
    for p, row in enumerate(prefixes):
        layer = []
        for prefix in row:
            edges = []
            for c in range(len(classes)):
                nxt = (*prefix, c)
                if any(word[: p + 1] == nxt for word in class_words):
                    target = 0 if p + 1 == length else prefixes[p + 1].index(nxt)
                    edges.append((target, (c,)))
            layer.append(tuple(edges))
        layers.append(tuple(layer))
    return tuple(map(tuple, classes)), tuple(layers), (True,), valid


def independent_suffixes(classes, layers, accepting, rows):
    result = []
    for p, layer in enumerate(layers):
        row = []
        for initial in range(len(layer)):
            total = F(0)
            for word in itertools.product(range(len(rows[0])), repeat=len(layers) - p):
                state, mass = initial, F(1)
                for slot, token in enumerate(word, p):
                    choices = [
                        dst
                        for dst, cids in layers[slot][state]
                        if any(token in classes[c] for c in cids)
                    ]
                    assert len(choices) <= 1
                    if not choices:
                        break
                    state = choices[0]
                    mass *= F(float(rows[slot][token]))
                else:
                    total += mass * accepting[state]
            row.append(total)
        result.append(row)
    return [*result, [F(int(x)) for x in accepting]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    torch.set_flush_denormal(False)
    rng = np.random.default_rng(2026101756)
    fixtures = []
    for tokens, eot, pad, length in (
        ((b"0", b"0", b"[]", b"[[]]", "EOT", "PAD", b" "), 4, 5, 3),
        ((b'"', b"\xc3", b"\xa9", b"a", "EOT", "PAD"), 4, 5, 5),
    ):
        classes, layers, accepts, valid = json_trie(tokens, eot, pad, length)
        for salt in (1, 2):
            rows = 0.1 + 0.8 * rng.random((length, len(tokens)))
            if salt == 2 and length == 3:
                rows[0] = 0
                rows[0, 1] = 1
            fixtures.append((classes, layers, accepts, rows, valid))
    for small in (1e-40, np.nextafter(0.0, 1.0)):
        classes, layers, accepts, valid = json_trie((b"0", b"0", "EOT", "PAD"), 2, 3, 3)
        fixtures.append((classes, layers, accepts, np.full((3, 4), small), valid))
    classes = (tuple(range(1024)), (1024,))
    layers = ((((0, (0,)), (1, (1,))),),)
    fixtures.append((classes, layers, (True, False), rng.random((1, 1025)), None))
    records, mass_checks, replays, ptx = [], 0, 0, {}
    for case, (classes, layers, accepts, rows, valid) in enumerate(fixtures):
        sampler = IntervalSampler(classes, layers, accepts)
        engine = StaticDAG(sampler.engine.classes, sampler.engine.layers, accepts)
        engine.capture_ptx = True
        sampler.engine = engine
        weights = torch.from_numpy(rows).cuda()
        result = engine.query(weights)
        fast_status = engine.last_fast_status
        truth = independent_suffixes(engine.classes, engine.layers, accepts, rows)
        assert result["lower"] <= truth[0][0] <= result["upper"]
        for p, true_row in enumerate(truth):
            factor = F(1)
            for s in result["scales"][: len(layers) - p]:
                factor *= F(s)
            lo = result["beta_lower"][p].cpu().tolist()
            hi = result["beta_upper"][p].cpu().tolist()
            for lower, exact, upper in zip(lo, true_row, hi, strict=True):
                assert F(lower) * factor <= exact <= F(upper) * factor
                mass_checks += 1
        for p, row in enumerate(rows):
            for c, members in enumerate(engine.classes):
                exact_mass = sum((F(float(row[t])) for t in members), F())
                assert F(result["class_lower"][p, c].item()) <= exact_mass
                assert exact_mass <= F(result["class_upper"][p, c].item())
                mass_checks += 1
        exact = ExactDAG(engine.classes, engine.layers, accepts, rows)
        for bits in (2, 8, 32):
            source = rng.integers(0, 1 << bits, size=(16, len(layers), 3), dtype=np.int64)
            seeds = [case * 1000 + bits * 20 + i for i in range(16)]
            sample = sampler.sample(
                weights, torch.from_numpy(source).cuda(), [Random(s) for s in seeds], bits=bits
            )
            for i, word in enumerate(sample["tokens"].cpu().tolist()):
                assert tuple(word) == exact.sample(source[i].tolist(), bits, Random(seeds[i]))
                if valid is not None:
                    assert tuple(word) in valid
                if case == 1:
                    assert word[0] == 1
                replays += 1
            records.append(
                dict(
                    case=case,
                    bits=bits,
                    status=fast_status,
                    certified=sample["gpu_certified"],
                    fallback=sample["fallback_count"],
                )
            )
        ptx.update(engine.ptx)
    classes = ((0, 1), (2, 3))
    layers = ((((0, (0,)), (0, (1,))),), (((0, (0, 1)),),))
    sampler = IntervalSampler(classes, layers, (True,))
    sampler.engine = StaticDAG(sampler.engine.classes, sampler.engine.layers, (True,))
    source = np.asarray(list(itertools.product(range(4), repeat=6)), dtype=np.int64).reshape(
        -1, 2, 3
    )
    sample = sampler.sample(
        torch.full((2, 4), 0.5, dtype=torch.float64, device="cuda"),
        torch.from_numpy(source).cuda(),
        [Random(i) for i in range(4096)],
        bits=2,
    )
    law = Counter(tuple(w) for w in sample["tokens"].cpu().tolist())
    assert len(law) == 16 and all(F(n, 4096) == F(1, 16) for n in law.values())
    ptx_dir = args.output / "ptx"
    ptx_dir.mkdir()
    for digest, content in ptx.items():
        assert ".ftz" not in content
        (ptx_dir / (digest + ".ptx")).write_text(content)
    payload = dict(
        status="PASS",
        records=records,
        mass_checks=mass_checks,
        literal_replays=replays,
        finite_word_prefixes=4096,
        finite_word_events=len(law),
        ptx_modules=len(ptx),
        new_model_forwards=0,
        speed_claim=False,
        goal_met=False,
        torch=torch.__version__,
        gpu=torch.cuda.get_device_name(),
        commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        sources={
            str(p.relative_to(Path(__file__).parent)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in Path(__file__).parent.rglob("*.py")
        },
    )
    (args.output / "summary.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
