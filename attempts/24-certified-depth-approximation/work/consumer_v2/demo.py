"""Use the queried-confidence consumer on A24's licensed public head packet."""

import argparse
import io
import json
from fractions import Fraction
from pathlib import Path
from random import Random
from time import monotonic, perf_counter
from zipfile import ZipFile

import numpy as np
from scripts.exact_commit.full_head_packet import check

from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from ..table import LexerTable
from .block_stats import Partition
from .query import BoundaryWeights, confidence, evaluate, sample


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--tolerance", default="1/1000")
    args = parser.parse_args()
    audit = check(args.packet)
    start = perf_counter()
    with ZipFile(args.packet) as archive:
        name = json.loads(archive.read("manifest.json"))["case"]
        case = json.loads(archive.read(name + ".json"))
        vocabulary = json.loads(archive.read("vocabulary.json"))
        head = np.load(io.BytesIO(archive.read(name + ".npy")), allow_pickle=False)
    table = LexerTable(CompositionalByteLevelAdapter.from_token_pieces(vocabulary))
    partition = Partition(tuple(table.class_of), len(table.classes), 1024)
    weights = BoundaryWeights(table, head, case["canvas"], partition)
    end = monotonic() + 120
    post, certificate = evaluate(table, weights, args.tolerance, timeout_seconds=end - monotonic())
    word = sample(post, weights, Random(args.seed))
    sampled_certificate = certificate
    refinements = []
    for tolerance in (None, Fraction(1, 10**6), Fraction(1, 10**9), "full"):
        if tolerance is not None:
            post, certificate = evaluate(
                table,
                weights,
                args.tolerance if tolerance == "full" else tolerance,
                method="exact_stack" if tolerance == "full" else "handoff",
                timeout_seconds=end - monotonic(),
            )
            refinements.append(str(tolerance))
        result = confidence(post, certificate, word)
        if not result["ambiguous"]:
            break
    if result["ambiguous"]:
        raise RuntimeError("full confidence fallback did not resolve")
    text = table.adapter.detokenize_bytes(word).decode("utf8")
    json.loads(text, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    print(
        json.dumps(
            dict(
                status="complete",
                sample=text,
                original_token_ids=word,
                committed_positions=result["committed"],
                queried_confidences=result["decisions"],
                sample_certificate=sampled_certificate,
                refinements=refinements,
                exact_lower_valid_mass=sampled_certificate["attempts"][-1]["lower_mass"],
                packet_sha256=audit["packet_sha256"],
                wall=perf_counter() - start,
                scope=(
                    "One frozen public head; no new backbone run, "
                    "semantic correctness or speed gate"
                ),
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
