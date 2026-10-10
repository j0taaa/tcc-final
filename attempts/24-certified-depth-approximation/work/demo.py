"""Run the same certified posterior on a public full-head packet, without a model."""

import argparse
import io
import json
from fractions import Fraction
from math import prod
from pathlib import Path
from random import Random
from time import perf_counter, process_time
from zipfile import ZipFile

from scripts.exact_commit.full_head_packet import check

from mwpc_exact.cfg_posterior import CompilationLimit
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from .posterior import Weights
from .sampler import evaluate_certified
from .table import LexerTable


def main():
    import numpy as np

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--tolerance", default="1/1000")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    started = perf_counter(), process_time()
    audit = check(args.packet)
    with ZipFile(args.packet) as archive:
        name = json.loads(archive.read("manifest.json"))["case"]
        case = json.loads(archive.read(name + ".json"))
        adapter = CompositionalByteLevelAdapter.from_token_pieces(
            json.loads(archive.read("vocabulary.json"))
        )
        probabilities = np.load(io.BytesIO(archive.read(name + ".npy")), allow_pickle=False)
    rows = [None] * len(case["canvas"])
    for p, row in zip(case["positions"], probabilities, strict=True):
        rows[p] = row
    packet_read = perf_counter() - started[0]
    try:
        begin = perf_counter()
        table = LexerTable(adapter)
        startup = perf_counter() - begin
        begin = perf_counter()
        weights = Weights(rows, case["canvas"], adapter.vocabulary_size)
        conversion = perf_counter() - begin
        begin = perf_counter()
        posterior, certificate = evaluate_certified(table, weights, args.tolerance)
        query_wall = perf_counter() - begin
        if not posterior.total:
            result = dict(status="zero_valid_mass", certificate=certificate)
        else:
            begin = perf_counter()
            word = posterior.sample(Random(args.seed))
            text = adapter.detokenize_bytes(word).decode("utf8")
            json.loads(text, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
            numerators, lower = posterior.marginals()
            upper = Fraction(certificate["upper_tail"]) * prod(weights.denominators)
            if upper.denominator != 1:
                raise RuntimeError("certificate and original marginal units differ")
            upper = upper.numerator
            result = dict(
                status="complete",
                sample=text,
                original_token_ids=list(word),
                lower_valid_mass=str(posterior.mass),
                certificate=certificate,
                sampled_token_conditional_intervals={
                    p: dict(
                        original_id=word[p],
                        low=str(Fraction(numerators[p][word[p]], lower + upper)),
                        high=str(Fraction(numerators[p][word[p]] + upper, lower + upper)),
                    )
                    for p in case["positions"]
                },
            )
            result["sample_and_marginals_wall"] = perf_counter() - begin
        result.update(
            lexer_startup_wall=startup, conversion_wall=conversion, adaptive_query_wall=query_wall
        )
    except (CompilationLimit, MemoryError, TimeoutError) as error:
        result = dict(status="resource_refusal", error=str(error))
    result.update(
        scope="One frozen full-V posterior; no new neural forward/semantic/benchmark claim",
        packet_sha256=audit["packet_sha256"],
        packet_read_and_audit_wall=packet_read,
        total_wall=perf_counter() - started[0],
        total_cpu=process_time() - started[1],
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
