"""Predeclared bound diagnostic on the public head; no timing or new forwards."""

import argparse
import hashlib
import io
import json
import subprocess
from pathlib import Path
from zipfile import ZipFile

from scripts.exact_commit.full_head_packet import check

from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from .finite_closure import FiniteClosure
from .frozen.posterior import Weights, class_weights
from .frozen.stack_control import StackPosterior, StackPrepared
from .frozen.table import LexerTable


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
    model_rows = dict(zip(case["positions"], matrix, strict=True))
    weights = Weights(
        [model_rows.get(p, ()) for p in range(len(case["canvas"]))],
        case["canvas"],
        adapter.vocabulary_size,
    )
    table = LexerTable(adapter)
    sums = class_weights(table, weights)
    options = dict(max_edges=1000000, max_cells=200000, max_terms=50000000, timeout_seconds=120)
    full = StackPosterior(StackPrepared(table, weights.canvas, **options), weights, sums=sums)
    records = []
    for depth in (0, 1, 2, 4):
        plan = StackPrepared(table, weights.canvas, max_depth=depth, track_overflow=True, **options)
        shallow = StackPosterior(plan, weights, sums=sums)
        finite = FiniteClosure(plan, weights, sums=sums)
        tail = full.mass - shallow.mass
        for modulus in (2, 3, 4, 8, 16):
            upper, cells = finite.residue(modulus)
            if not tail <= upper <= 1:
                raise RuntimeError("actual deep mass exceeds residue bound")
            records.append(
                dict(
                    depth=depth,
                    method="residue",
                    parameter=modulus,
                    actual_tail=str(tail),
                    upper=str(upper),
                    suffix_cells=cells,
                    lower=str(shallow.mass),
                )
            )
        for exponents in ((0,), (1,), (2,), (4,), (0, 1, 2, 4)):
            upper, cells = finite.potential(exponents)
            if not tail <= upper <= 1:
                raise RuntimeError("actual deep mass exceeds potential bound")
            records.append(
                dict(
                    depth=depth,
                    method="potential",
                    parameter=exponents,
                    actual_tail=str(tail),
                    upper=str(upper),
                    suffix_cells=cells,
                    lower=str(shallow.mass),
                )
            )
    result = dict(
        source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        packet_sha256=audit["packet_sha256"],
        source_case=name,
        new_neural_forwards=0,
        scope="Archived full-original-ID head, bounds only; no independent speed/utility evidence",
        vocabulary_size=adapter.vocabulary_size,
        full_mass=str(full.mass),
        records=records,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as file:
        json.dump(result, file, indent=2)
        file.write("\n")
    print(json.dumps(dict(records=len(records), all_bounds_sound=True, new_neural_forwards=0)))


if __name__ == "__main__":
    main()
