"""Declared same-head functional replay; not a neural memory/timing benchmark."""

import argparse
import hashlib
import io
import json
import subprocess
from fractions import Fraction
from pathlib import Path
from random import Random
from zipfile import ZipFile

from scripts.exact_commit.full_head_packet import check

from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from .frozen.posterior import Weights, class_weights
from .frozen.stack_control import StackPosterior, StackPrepared
from .frozen.table import LexerTable
from .summary import ClassLedger, ClassPosterior


def integer_stream(row):
    # Every nonnegative finite binary64 weight is an integer /2^1074.
    # Using a fixed scale avoids retaining a row to discover its denominator.
    for value in row:
        n, d = float(value).as_integer_ratio()
        yield n << (1074 - (d.bit_length() - 1)) if n else 0


def main():
    import numpy as np

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    audit = check(args.packet)
    with ZipFile(args.packet) as archive:
        name = json.loads(archive.read("manifest.json"))["case"]
        case = json.loads(archive.read(name + ".json"))
        adapter = CompositionalByteLevelAdapter.from_token_pieces(
            json.loads(archive.read("vocabulary.json"))
        )
        matrix = np.load(io.BytesIO(archive.read(name + ".npy")), allow_pickle=False)
    rows = dict(zip(case["positions"], matrix, strict=True))
    table = LexerTable(adapter)
    plan = StackPrepared(
        table,
        case["canvas"],
        max_cells=200000,
        max_edges=1000000,
        max_terms=50000000,
        timeout_seconds=120,
    )
    weights = Weights(
        [rows.get(p, ()) for p in range(len(case["canvas"]))],
        case["canvas"],
        adapter.vocabulary_size,
    )
    reference_sums = class_weights(table, weights)
    full = StackPosterior(plan, weights, sums=reference_sums)
    samples, class_checks = [], 0
    for draw in range(8):
        rng = Random(2026101128 + draw)
        ledger = ClassLedger(
            (integer_stream(rows.get(p, ())) for p in range(len(case["canvas"]))),
            case["canvas"],
            table.class_of,
            len(table.classes),
            rng,
        )
        for p in range(len(case["canvas"])):
            for cid, value in enumerate(ledger.sums[p]):
                if Fraction(value, ledger.denominators[p]) != Fraction(
                    reference_sums[p][cid], weights.denominators[p]
                ):
                    raise RuntimeError("streamed original class mass changed")
                class_checks += 1
        posterior = ClassPosterior(plan, ledger)
        if posterior.mass != full.mass:
            raise RuntimeError("streamed conditional valid mass changed")
        tokens = posterior.sample(rng)
        rendered = adapter.detokenize_bytes(tokens)
        json.loads(rendered.decode("utf8"))
        if any(t is not None and tokens[p] != t for p, t in enumerate(case["canvas"])):
            raise RuntimeError("streamed sample changed fixed original IDs")
        samples.append(dict(draw=draw, tokens=tokens, output_utf8=rendered.decode("utf8")))
    result = dict(
        producer_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        packet_sha256=audit["packet_sha256"],
        case=name,
        vocabulary_size=adapter.vocabulary_size,
        grammar_classes=len(table.classes),
        free_positions=case["positions"],
        valid_mass=str(full.mass),
        exact_class_probability_checks=class_checks,
        samples=samples,
        new_neural_forwards=0,
        scope=(
            "Same archived public full-V head; input probabilities already materialized; "
            "no neural memory/timing or independent utility claim"
        ),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as file:
        json.dump(result, file, indent=2)
        file.write("\n")
    print(
        json.dumps(dict(samples=len(samples), class_checks=class_checks, valid_mass=str(full.mass)))
    )


if __name__ == "__main__":
    main()
