"""CPU-only first-sample/confidence service, independent of the neural process."""

import argparse
import hashlib
import importlib
import json
import resource
import signal
import sys
import types
from fractions import Fraction
from math import prod
from pathlib import Path
from random import Random
from time import monotonic, perf_counter, process_time

from mwpc_exact.cfg_posterior import CompilationLimit
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from .frozen_control import materialize
from .posterior import Weights
from .sampler import evaluate_certified
from .stack_control import StackPosterior, StackPrepared
from .table import LexerTable

WORK = Path(__file__).resolve().parent


def clock():
    return perf_counter(), process_time()


def elapsed(start):
    return dict(wall=perf_counter() - start[0], cpu=process_time() - start[1])


def classify(word, canvas, numerators, lower, upper, threshold):
    """Prove each selected-original-ID threshold decision, or mark unresolved."""
    result, ambiguous = {}, []
    for p, fixed in enumerate(canvas):
        if fixed is not None:
            continue
        numerator = numerators[p][word[p]]
        low, high = Fraction(numerator, lower + upper), Fraction(numerator + upper, lower + upper)
        decision = True if low >= threshold else False if high < threshold else None
        result[p] = dict(low=str(low), high=str(high), accepted=decision)
        if decision is None:
            ambiguous.append(p)
    return result, ambiguous


def full_query(table, weights, seconds, *, frozen=None):
    factory = StackPrepared if frozen is None else frozen.StackPrepared
    inference = StackPosterior if frozen is None else frozen.StackPosterior
    prepared = factory(
        table,
        weights.canvas,
        max_edges=10_000_000,
        max_cells=10_000_000,
        max_terms=50_000_000,
        timeout_seconds=seconds,
    )
    return inference(prepared, weights)


def query(request, protocol, table, frozen=None):
    import numpy as np

    operation, end = clock(), monotonic() + 120
    result = dict(status="started", refinements=[])
    try:
        path = Path(request["probabilities"])
        if hashlib.sha256(path.read_bytes()).hexdigest() != request["probabilities_sha256"]:
            raise ValueError("new full-V model head hash changed")
        probabilities = np.load(path, allow_pickle=False)
        if probabilities.shape != (len(request["positions"]), table.adapter.vocabulary_size):
            raise ValueError("new model full support differs")
        rows = [None] * len(request["canvas"])
        for p, row in zip(request["positions"], probabilities, strict=True):
            rows[p] = row
        weights = Weights(rows, request["canvas"], table.adapter.vocabulary_size)
        tolerance = Fraction(protocol["trajectory_total_tv"]) / request["initial_masks"]
        if frozen is None:
            posterior, certificate = evaluate_certified(
                table,
                weights,
                tolerance,
                method="handoff",
                depths=(1, 2, 3, 4, 6, 8, 12),
                timeout_seconds=end - monotonic(),
            )
        else:
            posterior = full_query(table, weights, end - monotonic(), frozen=frozen)
            certificate = dict(delta="0", depth=None, upper_tail="0")
        result["sample_certificate"] = certificate
        if not posterior.total:
            return dict(result, status="zero_valid_mass", operation=elapsed(operation))
        word = posterior.sample(Random(request["seed"]))
        table.adapter.detokenize_bytes(word).decode("utf8")
        json.loads(
            table.adapter.detokenize_bytes(word).decode("utf8"),
            parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)),
        )
        if any(t is not None and word[p] != t for p, t in enumerate(weights.canvas)):
            raise RuntimeError("sample changed previously fixed original IDs")
        # Confidence refinement evaluates the same frozen product and the SAME
        # sampled word; sampling TV belongs to the initial query only.
        tolerances = iter((Fraction(1, 10**6), Fraction(1, 10**9), None))
        while True:
            numerators, lower = posterior.marginals()
            upper = Fraction(certificate["upper_tail"]) * prod(weights.denominators)
            if upper.denominator != 1:
                raise RuntimeError("confidence tail units differ")
            decisions, ambiguous = classify(
                word,
                weights.canvas,
                numerators,
                lower,
                upper.numerator,
                Fraction(protocol["confidence_threshold"]),
            )
            if not ambiguous:
                break
            refined = next(tolerances)
            begin = clock()
            if refined is None:
                posterior = full_query(table, weights, end - monotonic())
                certificate = dict(delta="0", depth=None, upper_tail="0")
            else:
                posterior, certificate = evaluate_certified(
                    table,
                    weights,
                    refined,
                    method="handoff",
                    depths=(1, 2, 3, 4, 6, 8, 12),
                    timeout_seconds=end - monotonic(),
                )
            result["refinements"].append(
                dict(
                    tolerance=None if refined is None else str(refined),
                    certificate=certificate,
                    cost=elapsed(begin),
                )
            )
        accepted = [p for p, d in decisions.items() if d["accepted"]]
        committed = accepted[: protocol["commit_budget"]] or [min(decisions)]
        result.update(
            status="complete",
            sample=list(word),
            decisions=decisions,
            committed=committed,
            confidence_certificate=certificate,
            operation=elapsed(operation),
        )
    except (CompilationLimit, MemoryError, TimeoutError, RecursionError) as error:
        result.update(status="resource_refusal", error=str(error), operation=elapsed(operation))
    result["peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return result


def deadline(signum, frame):
    raise TimeoutError("whole sample/confidence operation deadline")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", choices=("handoff", "exact_stack"), required=True)
    parser.add_argument("--vocabulary", type=Path, required=True)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (3 * 1024**3,) * 2)
    protocol = json.loads((WORK / "generation-protocol.json").read_text())
    adapter = CompositionalByteLevelAdapter.from_token_pieces(
        json.loads(args.vocabulary.read_text())
    )
    frozen, table_factory = None, LexerTable
    if args.method == "exact_stack":
        target, _, _ = materialize()
        package = types.ModuleType("_a24_generation_exact")
        package.__path__ = [str(target / "attempts/23-canonical-epsilon-posterior/work")]
        sys.modules[package.__name__] = package
        frozen = importlib.import_module(package.__name__ + ".stack_control")
        table_factory = importlib.import_module(package.__name__ + ".table").LexerTable
    start = clock()
    table = table_factory(adapter)
    print(json.dumps(dict(status="ready", decoder_startup=elapsed(start))), flush=True)
    signal.signal(signal.SIGALRM, deadline)
    for line in sys.stdin:
        signal.setitimer(signal.ITIMER_REAL, 120)
        try:
            result = query(json.loads(line), protocol, table, frozen)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
