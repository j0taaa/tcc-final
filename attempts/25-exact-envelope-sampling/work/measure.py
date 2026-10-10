"""First exact sample and batch32; all methods pay the same necessary operation."""

import argparse
import hashlib
import json
import resource
import signal
import subprocess
from bisect import bisect_right
from itertools import accumulate
from math import prod
from pathlib import Path
from random import Random
from time import monotonic, perf_counter, process_time

from mwpc_exact.cfg_posterior import CompilationLimit
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from .adaptive import prepare_certified
from .cars import Cars
from .envelope import prepare_envelope
from .frozen_control import module
from .posterior import Weights
from .table import LexerTable

WORK = Path(__file__).resolve().parent


def clock():
    return perf_counter(), process_time()


def elapsed(start):
    return dict(wall=perf_counter() - start[0], cpu=process_time() - start[1])


def deadline(signum, frame):
    raise TimeoutError("whole sampling operation deadline; not invalidity")


def valid(adapter, word, canvas):
    if len(word) != len(canvas) or any(
        t is not None and word[p] != t for p, t in enumerate(canvas)
    ):
        raise RuntimeError("sample changed original fixed frame")
    if any(adapter.emissions[t] is None for t in word):
        return False
    try:
        json.loads(
            adapter.detokenize_bytes(word).decode("utf8"),
            parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)),
        )
        return True
    except RecursionError as error:
        raise CompilationLimit("independent JSON recognizer resources") from error
    except (ValueError, UnicodeDecodeError):
        return False


class Rejection:
    """Cached inverse CDF; no lexer cost and no full-V scan per proposal."""

    def __init__(self, weights, adapter):
        self.weights, self.adapter = weights, adapter
        self.cdfs = {
            p: tuple(accumulate(row))
            for p, row in enumerate(weights.rows)
            if weights.canvas[p] is None
        }

    def sample(self, rng, *, max_trials):
        for trial in range(1, max_trials + 1):
            word = tuple(
                t if t is not None else bisect_right(self.cdfs[p], rng.randrange(self.cdfs[p][-1]))
                for p, t in enumerate(self.weights.canvas)
            )
            if valid(self.adapter, word, self.weights.canvas):
                return word, trial
        raise CompilationLimit("raw rejection proposal budget; validity unresolved")


def prepare_exact(method, table, weights, canvas, grammar, seconds):
    factory = (
        module("stack_control").StackPrepared
        if method == "exact_stack"
        else module("epsilon").EpsilonPrepared
        if method == "exact_eps_local"
        else module("forest").Prepared
    )
    arguments = (
        (table, canvas)
        if method == "exact_stack"
        else (table, canvas, grammar, method.removeprefix("exact_").removeprefix("eps_"))
    )
    prepared = factory(
        *arguments,
        max_edges=10_000_000,
        max_cells=10_000_000,
        max_terms=50_000_000,
        timeout_seconds=seconds,
    )
    posterior = (
        module("stack_control").StackPosterior
        if method == "exact_stack"
        else module("posterior").Posterior
    )(prepared, weights)
    return posterior


def worker(args, protocol):
    import numpy as np

    case = json.loads((args.capture / (args.case + ".json")).read_text())
    path = args.capture / (args.case + ".npy")
    if hashlib.sha256(path.read_bytes()).hexdigest() != case["probabilities_sha256"]:
        raise ValueError("captured original probability hash changed")
    probabilities = np.load(path, allow_pickle=False)
    vocabulary = json.loads((args.capture / "vocabulary.json").read_text())
    if probabilities.shape != (len(case["positions"]), len(vocabulary)):
        raise ValueError("captured full original support shape changed")
    adapter = CompositionalByteLevelAdapter.from_token_pieces(vocabulary)
    raw = [None] * len(case["canvas"])
    for p, row in zip(case["positions"], probabilities, strict=True):
        raw[p] = row
    method = args.method
    exact = method in protocol["frozen_exact_methods"]
    # Kernel import/integrity IO is outside decoder timings for every method.
    # The measured operation starts at rational conversion, and includes all
    # real grammar normalization/table preparation in the cold figures.
    if exact:
        for name in ("table", "lexer", "forest", "epsilon", "stack_control", "posterior"):
            module(name)
    result = dict(
        case=case["case"],
        mask_count=case["mask_count"],
        method=method,
        repeat=args.repeat,
        forward=case["forward_and_softmax"],
        first_status="started",
        status="started",
        samples=[],
        proposal_counts=[],
    )
    startup = clock()
    table = (
        None
        if method == "rejection"
        else (module("table").LexerTable if exact else LexerTable)(adapter)
    )
    grammar = (
        module("lexer").lexical_grammar(marked=method != "exact_eps_local")
        if exact and method != "exact_stack"
        else None
    )
    result["startup"] = elapsed(startup)
    signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, protocol["timeout_seconds"])
    operation, end = clock(), monotonic() + protocol["timeout_seconds"]
    try:
        try:
            begin = clock()
            weights = Weights(raw, case["canvas"], len(vocabulary))
            result["conversion"] = elapsed(begin)
            result["product_denominator"] = str(prod(weights.denominators))
            begin = clock()
            if exact:
                sampler = prepare_exact(
                    method, table, weights, case["canvas"], grammar, end - monotonic()
                )
                result["valid_mass"] = str(sampler.mass)
                result["exact_total"] = str(sampler.total)
            elif method in ("handoff", "closed", "grammar_hit"):
                sampler, certificate = prepare_certified(
                    table,
                    weights,
                    protocol["tolerance"],
                    method=method,
                    depths=protocol["depths"],
                    timeout_seconds=end - monotonic(),
                )
                result.update(
                    certificate=certificate,
                    lower=str(sampler.lower),
                    upper_tail=str(sampler.upper_tail),
                    envelope_total=str(sampler.total),
                )
            elif method == "counter_only":
                sampler = prepare_envelope(
                    table, weights, None, method=method, timeout_seconds=end - monotonic()
                )
                result["envelope_total"] = str(sampler.total)
            elif "cars" in method:
                sampler = Cars(
                    table,
                    weights,
                    perfect=method.endswith("perfect"),
                    counter=method.startswith("counter_"),
                    timeout_seconds=end - monotonic(),
                )
                result["initial_allowed_total"] = str(sampler.root.total)
            else:
                sampler = Rejection(weights, adapter)
            result["preparation"] = elapsed(begin)
            total = sampler.root.total if "cars" in method else getattr(sampler, "total", None)
            if total == 0:
                result.update(status="zero_valid_mass", first_status="zero_valid_mass")
            else:
                rng = Random(protocol["seed"] + args.repeat)
                max_trials = protocol[
                    "candidate_max_proposals"
                    if method in protocol["candidates"]
                    else "control_max_proposals"
                ]
                for index in range(protocol["batch_size"]):
                    word, trials = (
                        (sampler.sample(rng), 1)
                        if exact
                        else sampler.sample(rng, max_trials=max_trials)
                    )
                    if not valid(adapter, word, case["canvas"]):
                        raise RuntimeError("returned original token sequence is invalid JSON")
                    result["samples"].append(list(word))
                    result["proposal_counts"].append(trials)
                    if index == 0:
                        result.update(first_status="complete", first_sample=elapsed(operation))
                result.update(status="complete", batch=elapsed(operation))
            result["operation"] = elapsed(operation)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
    except (CompilationLimit, TimeoutError, MemoryError) as error:
        # Cancel before recording a refusal; the one-shot alarm may arrive
        # during cancellation itself, which is also inside this boundary.
        signal.setitimer(signal.ITIMER_REAL, 0)
        result.update(status="resource_refusal", error=str(error), operation=elapsed(operation))
        if result["first_status"] == "started":
            result["first_status"] = "resource_refusal"
    for target, source in (("first_total", "first_sample"), ("batch_total", "batch")):
        if source in result:
            result[target] = {u: result[source][u] + result["forward"][u] for u in ("wall", "cpu")}
            result["cold_" + target] = {
                u: result[target][u] + result["startup"][u] for u in ("wall", "cpu")
            }
    result["peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result["commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--case", required=True)
    parser.add_argument("--method", required=True)
    parser.add_argument("--repeat", type=int, required=True)
    args = parser.parse_args()
    protocol = json.loads((WORK / "protocol.json").read_text())
    if args.method not in protocol["methods"]:
        raise ValueError("method absent from frozen protocol")
    resource.setrlimit(resource.RLIMIT_AS, (protocol["virtual_memory_gib"] * 1024**3,) * 2)
    print(json.dumps(worker(args, protocol)), flush=True)


if __name__ == "__main__":
    main()
