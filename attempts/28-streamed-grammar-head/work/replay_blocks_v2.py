"""All three exact block interfaces on the same public head; no timing claim."""

import argparse
import io
import json
import subprocess
from fractions import Fraction
from pathlib import Path
from random import Random
from zipfile import ZipFile

import numpy as np
import torch
from scripts.exact_commit.full_head_packet import check

from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from .block_sampler import BlockPosterior, cuda_fetch, numpy_fetch
from .block_stats import Partition, numpy_stats
from .frozen.posterior import Weights, class_weights
from .frozen.stack_control import StackPosterior, StackPrepared
from .frozen.table import LexerTable
from .gpu_stats import DevicePartition, torch_stats, triton_stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    audit = check(args.packet)
    with ZipFile(args.packet) as archive:
        name = json.loads(archive.read("manifest.json"))["case"]
        case = json.loads(archive.read(name + ".json"))
        adapter = CompositionalByteLevelAdapter.from_token_pieces(
            json.loads(archive.read("vocabulary.json"))
        )
        matrix = np.load(io.BytesIO(archive.read(name + ".npy")), allow_pickle=False)
    table = LexerTable(adapter)
    plan = StackPrepared(
        table,
        case["canvas"],
        max_cells=200000,
        max_edges=1000000,
        max_terms=50000000,
        timeout_seconds=120,
    )
    rows = dict(zip(case["positions"], matrix, strict=True))
    weights = Weights(
        [rows.get(p, ()) for p in range(len(case["canvas"]))],
        case["canvas"],
        adapter.vocabulary_size,
    )
    original_sums = class_weights(table, weights)
    reference = StackPosterior(plan, weights, sums=original_sums)
    partition = Partition(table.class_of, len(table.classes), 512)
    mapping = DevicePartition(partition, "cuda:0")
    q = torch.tensor(matrix, dtype=torch.float64, device="cuda:0")
    result = dict(
        producer_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        packet_sha256=audit["packet_sha256"],
        case=name,
        vocabulary_size=adapter.vocabulary_size,
        classes=len(table.classes),
        blocks=len(partition.blocks),
        block_size=512,
        new_neural_forwards=0,
        scope="Same archived weights copied to GPU; no neural timing/memory or independent utility claim",
        methods=[],
        complete=False,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as log:
        try:
            for method in (numpy_stats, triton_stats, torch_stats):
                stats = method(matrix, partition) if method is numpy_stats else method(q, mapping)
                checks = 0
                for row, p in enumerate(case["positions"]):
                    for cid, mass in enumerate(stats.class_sums()[row]):
                        if Fraction(mass, sum(stats.totals[row])) != Fraction(
                            original_sums[p][cid], weights.denominators[p]
                        ):
                            raise RuntimeError("original class probability changed")
                        checks += 1
                fetch = (
                    numpy_fetch(matrix, partition)
                    if method is numpy_stats
                    else cuda_fetch(q, mapping)
                )
                samples = []
                for draw in range(8):
                    posterior = BlockPosterior(plan, stats, fetch)
                    if posterior.mass != reference.mass:
                        raise RuntimeError("original joint valid mass changed")
                    tokens = posterior.sample(Random(2026101128 + draw))
                    rendered = adapter.detokenize_bytes(tokens).decode("utf8")
                    json.loads(rendered)
                    if any(t is not None and tokens[p] != t for p, t in enumerate(case["canvas"])):
                        raise RuntimeError("fixed original ID changed")
                    samples.append(dict(draw=draw, tokens=tokens, output_utf8=rendered))
                result["methods"].append(
                    dict(
                        method=method.__name__,
                        digit_words=stats.digit_words,
                        exact_class_checks=checks,
                        valid_mass=str(reference.mass),
                        samples=samples,
                        status="complete",
                    )
                )
            result["complete"] = True
        except Exception as e:
            result["failure"] = dict(type=type(e).__name__, message=str(e))
            raise
        finally:
            json.dump(result, log, indent=2)
            log.write("\n")
    print(
        json.dumps(
            dict(
                complete=result["complete"],
                methods=len(result["methods"]),
                samples=sum(len(m["samples"]) for m in result["methods"]),
                checks=sum(m["exact_class_checks"] for m in result["methods"]),
            )
        )
    )


if __name__ == "__main__":
    main()
