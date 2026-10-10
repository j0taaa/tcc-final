"""All-frame application audit; no reinterpretation of the competitive A24 gate."""

import argparse
import gzip
import hashlib
import json
import subprocess
from fractions import Fraction
from math import prod
from pathlib import Path
from time import perf_counter, process_time

from mwpc_exact.cfg_posterior import CompilationLimit
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from .amplification import amplify
from .posterior import Weights
from .sampler import evaluate_certified
from .table import LexerTable

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[2]


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def clock():
    return perf_counter(), process_time()


def elapsed(start):
    return dict(wall=perf_counter() - start[0], cpu=process_time() - start[1])


def exact_marginal(path, position, token, vocabulary, slots):
    with gzip.open(path, "rb") as stream:
        header = json.loads(stream.readline())
        if header["rows"] != slots or int(header["total"]) <= 0:
            raise ValueError("canonical original matrix dimensions/mass differ")
        width = header["width"]
        for p in range(position + 1):
            mode = stream.read(1)
            if mode not in (b"D", b"F"):
                raise ValueError("corrupt canonical original matrix")
            if p < position:
                stream.seek(vocabulary * width if mode == b"D" else 4 + width, 1)
                continue
            if mode == b"F":
                original = int.from_bytes(stream.read(4), "little")
                value = int.from_bytes(stream.read(width), "little") if original == token else 0
            else:
                stream.seek(token * width, 1)
                raw = stream.read(width)
                if len(raw) != width:
                    raise ValueError("truncated canonical marginal")
                value = int.from_bytes(raw, "little")
            return Fraction(value, int(header["total"]))
    raise RuntimeError("missing original position")


def audit_frame(capture, case_name, table, query, application):
    import numpy as np

    case = json.loads((capture / (case_name + ".json")).read_text())
    path = capture / (case_name + ".npy")
    if hashlib.sha256(path.read_bytes()).hexdigest() != case["probabilities_sha256"]:
        raise ValueError("captured original probability hash differs")
    probabilities = np.load(path, allow_pickle=False)
    rows = [None] * len(case["canvas"])
    for p, row in zip(case["positions"], probabilities, strict=True):
        rows[p] = row
    result = dict(
        case=case_name,
        probability_sha256=case["probabilities_sha256"],
        forward=case["forward_and_softmax"],
    )
    operation = clock()
    try:
        weights = Weights(rows, case["canvas"], table.adapter.vocabulary_size)
        posterior, certificate = evaluate_certified(
            table,
            weights,
            query["tolerance"],
            method="handoff",
            depths=query["depths"],
            timeout_seconds=query["timeout_seconds"],
        )
        result["query"] = elapsed(operation)
        result["certificate"] = certificate
        if not posterior.total:
            result["status"] = "zero_valid_mass"
        else:
            begin = clock()
            numerators, lower = posterior.marginals()
            result["original_marginals"] = elapsed(begin)
            upper = Fraction(certificate["upper_tail"]) * prod(weights.denominators)
            if upper.denominator != 1:
                raise RuntimeError("tail units differ from original product")
            begin = clock()
            outcome = amplify(
                weights, numerators, lower, upper.numerator, factor=application["factor"]
            )
            result["coordinate_selection_and_copy"] = elapsed(begin)
            if outcome is None:
                result["status"] = "no_certified_signal"
            else:
                tilted, claim = outcome
                if tilted.canvas != weights.canvas:
                    raise RuntimeError("amplification changed fixed original IDs")
                result.update(status="strict_mass_increase_certified", amplification=claim)
        result["operation"] = elapsed(operation)
    except (CompilationLimit, MemoryError, TimeoutError) as error:
        result.update(status="resource_refusal", error=str(error), operation=elapsed(operation))
    result["total"] = {u: result["operation"][u] + result["forward"][u] for u in ("wall", "cpu")}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--development", type=Path, required=True)
    parser.add_argument("--independent", type=Path, required=True)
    parser.add_argument("--development-measure", type=Path, required=True)
    parser.add_argument("--independent-measure", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise ValueError("freeze audit source/protocol before executing")
    query = json.loads((WORK / "protocol.json").read_text())
    application = json.loads((WORK / "amplification-protocol.json").read_text())
    args.output.mkdir(parents=True, exist_ok=False)
    records = []
    inputs = {}
    for stage, capture, measured, count in (
        ("development", args.development, args.development_measure, 18),
        ("independent", args.independent, args.independent_measure, 15),
    ):
        metadata = json.loads((capture / "metadata.json").read_text())
        measurements = [
            json.loads(line) for line in (measured / "rows.jsonl").read_text().splitlines()
        ]
        expected = (
            count
            * len(query["methods"])
            * query["repetitions" if stage == "development" else "independent_repetitions"]
        )
        if len(measurements) != expected:
            raise ValueError("finish the original complete campaign before this application audit")
        inputs[stage] = dict(
            capture_metadata_sha256=digest(capture / "metadata.json"),
            vocabulary_sha256=digest(capture / "vocabulary.json"),
            measurement_metadata_sha256=digest(measured / "metadata.json"),
            measurement_rows_sha256=digest(measured / "rows.jsonl"),
        )
        start = clock()
        table = LexerTable(
            CompositionalByteLevelAdapter.from_token_pieces(
                json.loads((capture / "vocabulary.json").read_text())
            )
        )
        startup = elapsed(start)
        for example in metadata["selected"]:
            for masks in query["mask_counts"]:
                name = f"{example['key']}-{masks}"
                row = audit_frame(capture, name, table, query, application)
                row.update(stage=stage, shared_decoder_startup=startup)
                matrix = measured / "matrices" / (name + ".gz")
                if row["status"] == "strict_mass_increase_certified" and matrix.exists():
                    row["exact_matrix_sha256"] = digest(matrix)
                    claim = row["amplification"]
                    full = exact_marginal(
                        matrix,
                        claim["position"],
                        claim["token"],
                        table.adapter.vocabulary_size,
                        len(example["tokens"]),
                    )
                    factor, prior = claim["factor"], Fraction(claim["prior_probability"])
                    actual = (1 + (factor - 1) * full) / (1 + (factor - 1) * prior)
                    if actual < Fraction(claim["minimum_mass_ratio"]):
                        raise RuntimeError(
                            "exact original marginal violates amplification certificate"
                        )
                    row.update(exact_mass_ratio=str(actual), exact_matrix_checked=True)
                else:
                    row["exact_matrix_checked"] = False
                records.append(row)
                print(json.dumps(row), flush=True)
    (args.output / "audit.json").write_text(
        json.dumps(
            dict(
                protocol=application,
                input_provenance=inputs,
                source_sha256={p.name: digest(p) for p in WORK.glob("*.py")},
                producer_commit=subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True
                ).strip(),
                records=records,
            ),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
