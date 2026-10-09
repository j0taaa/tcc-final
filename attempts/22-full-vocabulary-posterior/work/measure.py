"""Isolated, bounded exact operations on the SAME captured full model prediction."""

import argparse
import gzip
import hashlib
import json
import resource
import signal
import subprocess
from bisect import bisect_right
from pathlib import Path
from random import Random
from time import perf_counter, process_time

from mwpc_exact.cfg_posterior import CompilationLimit
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from .forest import Prepared
from .lexer import lexical_grammar
from .posterior import Posterior, Weights
from .table import LexerTable

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[2]


def deadline(signum, frame):
    raise TimeoutError("whole operation deadline; feasibility unresolved")


def clock():
    return perf_counter(), process_time()


def elapsed(start):
    return dict(wall=perf_counter() - start[0], cpu=process_time() - start[1])


def valid(adapter, word, canvas):
    if any(t is not None and word[p] != t for p, t in enumerate(canvas)):
        raise RuntimeError("sample changed fixed original frame")
    try:
        json.loads(
            adapter.detokenize_bytes(word).decode("utf8"),
            parse_constant=lambda t: (_ for _ in ()).throw(ValueError(t)),
        )
        return True
    except (ValueError, UnicodeDecodeError):
        return False


def audit_matrix(destination, numerators, total):
    """Compare byte-for-byte exact integers. Diagnostic IO outside ALL timings."""
    width = max(1, (total.bit_length() + 7) // 8)
    header = json.dumps(dict(total=str(total), width=width, rows=len(numerators))).encode() + b"\n"
    digest = hashlib.sha256()
    exists = destination.exists()
    with gzip.open(destination, "rb" if exists else "wb", compresslevel=1) as stream:
        chunks = [header]
        for row in numerators:
            # Dense free rows; fixed delta rows have a unique sparse encoding.
            if isinstance(row, dict):
                token, value = next(iter(row.items()))
                chunk = b"F" + token.to_bytes(4, "little") + value.to_bytes(width, "little")
            else:
                chunk = b"D" + b"".join(v.to_bytes(width, "little") for v in row)
            chunks.append(chunk)
        for chunk in chunks:
            digest.update(chunk)
            if exists:
                if stream.read(len(chunk)) != chunk:
                    raise RuntimeError("exact full marginal matrix differs from first control")
            else:
                stream.write(chunk)
        if exists and stream.read(1):
            raise RuntimeError("canonical matrix has trailing data")
    return digest.hexdigest()


def rejection(weights, adapter, rng, max_attempts):
    cdfs = {}
    for p, row in enumerate(weights.rows):
        if isinstance(row, dict):
            continue
        cumulative, total = [], 0
        for w in row:
            total += w
            cumulative.append(total)
        cdfs[p] = cumulative
    for trial in range(1, max_attempts + 1):
        word = tuple(
            fixed
            if fixed is not None
            else bisect_right(cdfs[p], rng.randrange(weights.denominators[p]))
            for p, fixed in enumerate(weights.canvas)
        )
        if valid(adapter, word, weights.canvas):
            return word, trial
    raise CompilationLimit("rejection attempt budget; valid mass unresolved")


def worker(args, protocol):
    import numpy as np

    case = json.loads((args.capture / (args.case + ".json")).read_text())
    probabilities = np.load(args.capture / (args.case + ".npy"), allow_pickle=False)
    if (
        hashlib.sha256((args.capture / (args.case + ".npy")).read_bytes()).hexdigest()
        != case["probabilities_sha256"]
    ):
        raise RuntimeError("captured probability hash changed")
    vocabulary = json.loads((args.capture / "vocabulary.json").read_text())
    adapter = CompositionalByteLevelAdapter.from_token_pieces(vocabulary)
    if probabilities.shape != (len(case["positions"]), len(vocabulary)):
        raise ValueError("captured original support shape changed")
    raw_rows = [None] * len(case["canvas"])
    for p, row in zip(case["positions"], probabilities, strict=True):
        raw_rows[p] = row
    limits = protocol["limits"]
    result = dict(
        case=case["case"],
        mask_count=case["mask_count"],
        method=args.method,
        repeat=args.repeat,
        forward=case["forward_and_softmax"],
        status="started",
    )
    startup = clock()
    # Same service-wide lexer/global refinement/normalizer for all exact controls.
    # Rejection does not need a grammar table, and is not charged one.
    table = LexerTable(adapter) if args.method != "rejection" else None
    grammar = lexical_grammar() if table else None
    result["startup"] = elapsed(startup)
    if table:
        result["classes"] = len(table.classes)
        result["local_groups"] = len(table.groups)
    signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, limits["timeout_seconds"])
    operation = clock()
    posterior, numerators = None, None
    try:
        begin = clock()
        weights = Weights(raw_rows, case["canvas"], len(vocabulary))
        result["conversion"] = elapsed(begin)
        rng = Random(protocol["seed"] + args.repeat)
        begin = clock()
        if args.method == "rejection":
            word, trials = rejection(weights, adapter, rng, limits["rejection_attempts"])
            result.update(trials=trials, sample=list(word))
            result["first_sample"] = elapsed(operation)
        else:
            prepared = Prepared(
                table,
                case["canvas"],
                grammar,
                args.method,
                max_edges=limits["max_edges"],
                max_cells=limits["max_cells"],
                max_terms=limits["max_terms"],
                timeout_seconds=limits["timeout_seconds"],
            )
            result["compilation"] = elapsed(begin)
            result.update(
                graph_nodes=prepared.graph_nodes,
                graph_edges=prepared.graph_edges,
                cells=len(prepared.plan.terms),
                alternatives=sum(map(len, prepared.plan.terms)),
            )
            begin = clock()
            posterior = Posterior(prepared, weights)
            result["inside"] = elapsed(begin)
            result.update(valid_mass=str(posterior.mass), integer_bits=posterior.total.bit_length())
            if posterior.total:
                begin = clock()
                word = posterior.sample(rng)
                if not valid(adapter, word, case["canvas"]):
                    raise RuntimeError("grammar sample is not independently valid JSON")
                result.update(sample=list(word), sampling=elapsed(begin))
                result["first_sample"] = elapsed(operation)
                begin = clock()
                numerators, total = posterior.marginals()
                result["outside_and_original_marginals"] = elapsed(begin)
            else:
                result["status"] = "zero_valid_mass"
        result["operation"] = elapsed(operation)
        if result["status"] == "started":
            result["status"] = "complete"
    except (CompilationLimit, TimeoutError, MemoryError) as error:
        result.update(status="resource_refusal", error=str(error), operation=elapsed(operation))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    result["peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if posterior is not None and result["status"] in ("complete", "zero_valid_mass"):
        result["exact_total"] = str(posterior.total)
        result["exact_denominator"] = str(posterior.mass.denominator)
    if numerators is not None:
        result["matrix_sha256"] = audit_matrix(
            args.matrices / (args.case + ".gz"), numerators, total
        )
        result["matrix_audit"] = "byte-for-byte equal to canonical exact original matrix"
    for output, source in (("prepared_total", "operation"), ("sampling_total", "first_sample")):
        if source in result:
            result[output] = {
                unit: result[source][unit] + result["forward"][unit] for unit in ("wall", "cpu")
            }
    result["cold_total"] = {
        unit: result["operation"][unit] + result["startup"][unit] + result["forward"][unit]
        for unit in ("wall", "cpu")
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--case", required=True)
    parser.add_argument("--method", choices=("raw", "global", "local", "rejection"), required=True)
    parser.add_argument("--repeat", type=int, required=True)
    parser.add_argument("--matrices", type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads((WORK / "protocol.json").read_text())
    limit = protocol["limits"]["address_space_gib"] * 1024**3
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    result = worker(args, protocol)
    result["commit"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
