"""Isolated total-cost adaptive posterior query on captured original model rows."""

import argparse
import hashlib
import json
import resource
import signal
import subprocess
from fractions import Fraction
from pathlib import Path
from random import Random
from time import perf_counter, process_time

from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from .posterior import Weights
from .sampler import evaluate_certified
from .table import LexerTable

WORK = Path(__file__).resolve().parent


def clock():
    return perf_counter(), process_time()


def elapsed(start):
    return dict(wall=perf_counter() - start[0], cpu=process_time() - start[1])


def deadline(signum, frame):
    raise TimeoutError("whole operation deadline; not invalidity")


def main():
    import numpy as np

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--case", required=True)
    parser.add_argument("--method", required=True)
    parser.add_argument("--repeat", type=int, required=True)
    args = parser.parse_args()
    protocol = json.loads((WORK / "protocol.json").read_text())
    case = json.loads((args.capture / (args.case + ".json")).read_text())
    path = args.capture / (args.case + ".npy")
    if hashlib.sha256(path.read_bytes()).hexdigest() != case["probabilities_sha256"]:
        raise ValueError("original model probability hash differs")
    probabilities = np.load(path, allow_pickle=False)
    vocabulary = json.loads((args.capture / "vocabulary.json").read_text())
    if probabilities.shape != (len(case["positions"]), len(vocabulary)):
        raise ValueError("captured full original support shape changed")
    adapter = CompositionalByteLevelAdapter.from_token_pieces(vocabulary)
    rows = [None] * len(case["canvas"])
    for p, row in zip(case["positions"], probabilities, strict=True):
        rows[p] = row
    result = dict(
        case=case["case"],
        mask_count=case["mask_count"],
        method=args.method,
        repeat=args.repeat,
        forward=case["forward_and_softmax"],
        status="started",
        commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    )
    startup = clock()
    table = LexerTable(adapter)
    result["startup"] = elapsed(startup)
    signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, protocol["timeout_seconds"])
    operation = clock()
    try:
        begin = clock()
        weights = Weights(rows, case["canvas"], len(vocabulary))
        result["conversion"] = elapsed(begin)
        begin = clock()
        posterior, certificate = evaluate_certified(
            table,
            weights,
            protocol["tolerance"],
            method=args.method,
            depths=protocol["depths"],
            timeout_seconds=protocol["timeout_seconds"],
        )
        result["adaptive_inference"] = elapsed(begin)
        result.update(certificate=certificate, lower_valid_mass=str(posterior.mass))
        if posterior.total:
            word = posterior.sample(Random(protocol["seed"] + args.repeat))
            if any(t is not None and word[p] != t for p, t in enumerate(case["canvas"])):
                raise RuntimeError("sample changed fixed original token")
            json.loads(
                adapter.detokenize_bytes(word).decode("utf8"),
                parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)),
            )
            result["sample"] = list(word)
            result["first_sample"] = elapsed(operation)
            begin = clock()
            numerators, total = posterior.marginals()
            result["outside_and_original_marginals"] = elapsed(begin)
            result.update(original_marginal_rows=len(numerators), marginal_denominator=str(total))
            result["marginal_scope"] = (
                "exact J_d original numerators; J interval from TV certificate"
            )
            result["status"] = "complete"
        else:
            result["status"] = "zero_valid_mass"
        result["operation"] = elapsed(operation)
        if Fraction(certificate["delta"]) > Fraction(protocol["tolerance"]):
            raise RuntimeError("uncertified sample escaped adaptive query")
    except (TimeoutError, MemoryError) as error:
        result.update(status="resource_refusal", error=str(error), operation=elapsed(operation))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    for target, source in (("prepared_total", "operation"), ("sampling_total", "first_sample")):
        if source in result:
            result[target] = {u: result[source][u] + result["forward"][u] for u in ("wall", "cpu")}
    result["cold_total"] = {
        u: result["prepared_total"][u] + result["startup"][u] for u in ("wall", "cpu")
    }
    result["peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_AS, (3 * 1024**3, 3 * 1024**3))
    main()
