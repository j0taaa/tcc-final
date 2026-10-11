"""Literal first EPIC preservation at K=2, fake-head native recovery coverage."""

import argparse
import hashlib
import itertools
import json
import random
from pathlib import Path

import torch

from .anchored_ledger import AnchoredLedger
from .native_noise_v2 import ModelHistory, coupled_noise
from .probe_native import CFG, TinyHead, compile_lex_map, consume, native


def probe(device, seed, temperature, coordinate, max_resamples, mode):
    grammar = CFG.from_text("S -> lexNumber", "S").to_normal_form()
    lexical = compile_lex_map({"lexNumber": "(0|1)"})
    settings = {"temperature": temperature, "max_resamples": max_resamples}
    torch.manual_seed(seed)
    baseline = TinyHead(device)
    reference = consume(baseline, grammar, lexical, settings)
    book = AnchoredLedger(2, random.Random(seed + 91031))
    namespace = ("tiny-native-anchoring", tuple(settings.items()))
    outputs, counts = [], []
    for label in range(2):
        torch.manual_seed(seed + label * 101)
        proxy = ModelHistory(TinyHead(device), namespace, mode=mode)
        with coupled_noise(native, proxy, book, label, mask_id=5, coordinate=coordinate):
            outputs.append(consume(proxy, grammar, lexical, settings))
        counts.append(proxy.calls)
    if outputs[0] != reference or counts[0] != len(baseline.calls):
        raise AssertionError("first native trajectory changed")
    return dict(
        device=device,
        seed=seed,
        temperature=temperature,
        coordinate=coordinate,
        max_resamples=max_resamples,
        mode=mode,
        first_equal=True,
        reference_forwards=len(baseline.calls),
        pair_forwards=counts,
        complete=[bool(x[-1][2]) for x in outputs],
        rejections=[len(x[-1][1]) for x in outputs],
        shared_nodes=sum(len(t.tickets) > 1 for t in book.tables.values()),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = [
        probe(*x)
        for x in itertools.product(
            ("cpu", "cuda"),
            range(3),
            (0.0, 0.5, 1.0),
            ("first", "entropy"),
            (1, 8),
            ("state", "history", "root"),
        )
    ]
    files = (
        "probe_anchor.py",
        "native_noise_v2.py",
        "anchored_ledger.py",
        "probe_native.py",
        "ledger.py",
    )
    result = {
        "scope": "fake heads, first candidate literal native equality; no neural benefit/timing",
        "torch": torch.__version__,
        "rows": rows,
        "sources": {
            f: hashlib.sha256(Path(__file__).with_name(f).read_bytes()).hexdigest() for f in files
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "checks": len(rows),
                "first_equal": sum(r["first_equal"] for r in rows),
                "shared_nodes": sum(r["shared_nodes"] for r in rows),
            }
        )
    )


if __name__ == "__main__":
    main()
