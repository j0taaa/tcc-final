"""Complete-cost development of A24's query consumer on ALL old external frames."""

import argparse
import gc
import hashlib
import json
import platform
import resource
import signal
import subprocess
import traceback
from fractions import Fraction
from math import prod
from pathlib import Path
from random import Random
from time import monotonic, perf_counter, process_time

import numpy as np

from mwpc_exact.cfg_posterior import CompilationLimit
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from ..generation_service import classify
from ..posterior import Weights
from ..sampler import evaluate_certified
from ..table import LexerTable
from .block_stats import Partition
from .query import BoundaryWeights, confidence, evaluate, sample

WORK = Path(__file__).resolve().parents[1]
ROOT = WORK.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now():
    return perf_counter(), process_time()


def elapsed(start):
    return dict(wall=perf_counter() - start[0], cpu=process_time() - start[1])


def alarm(signum, frame):
    raise TimeoutError("complete consumer deadline; no committed progress")


def operation(
    table, partition, case_path, method, outside, boundary, seed, protocol, compact_modules=None
):
    started = now()
    deadline = monotonic() + protocol["resources"]["seconds"]
    case = json.loads(case_path.read_text())
    head_path = case_path.with_suffix(".npy")
    if digest(head_path) != case["probabilities_sha256"]:
        raise ValueError("captured original head changed")
    head = np.load(head_path, allow_pickle=False)
    canvas = case["canvas"]
    if list(case["positions"]) != [p for p, t in enumerate(canvas) if t is None]:
        raise ValueError("original free-position order changed")
    numeric_start = now()
    if boundary == "numpy":
        weights = BoundaryWeights(table, head, canvas, partition)
    else:
        rows = [None] * len(canvas)
        for p, row in zip(case["positions"], head, strict=True):
            rows[p] = row
        weights = Weights(rows, canvas, table.adapter.vocabulary_size)
    numeric = elapsed(numeric_start)
    tolerance = Fraction(protocol["trajectory_total_tv"]) / case["mask_count"]
    inference_start = now()

    def infer(tol, selected_method=method):
        options = dict(
            timeout_seconds=deadline - monotonic(),
            depths=tuple(protocol["depths"]),
            max_cells=protocol["resources"]["max_cells"],
            max_edges=protocol["resources"]["max_edges"],
            max_terms=protocol["resources"]["max_terms"],
        )
        if boundary == "numpy":
            if selected_method in ("exact_local", "exact_bidir_local", "exact_eps_local"):
                from .compact import evaluate_compact

                options.pop("depths")
                return evaluate_compact(
                    table, weights, selected_method, modules=compact_modules, **options
                )
            return evaluate(table, weights, tol, method=selected_method, **options)
        return evaluate_certified(table, weights, tol, method=selected_method, **options)

    post, certificate = infer(tolerance)
    inference = elapsed(inference_start)
    if not post.total:
        return dict(
            status="zero_valid_mass",
            operation=elapsed(started),
            forward=case["forward_and_softmax"],
        )
    sample_start = now()
    sample_valid_mass = str(post.mass)
    if method in ("exact_local", "exact_bidir_local", "exact_eps_local"):
        from .compact import sample_compact

        word = sample_compact(post, weights, Random(seed))
    else:
        word = (
            sample(post, weights, Random(seed))
            if boundary == "numpy"
            else post.sample(Random(seed))
        )
    text = table.adapter.detokenize_bytes(word).decode("utf8")
    json.loads(text, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("non-JSON number")))
    if any(t is not None and word[p] != t for p, t in enumerate(canvas)):
        raise RuntimeError("sample changed original fixed IDs")
    sample_cost = elapsed(sample_start)
    sample_certificate = certificate
    queries_start, refinements = now(), []
    tolerances = iter((Fraction(1, 10**6), Fraction(1, 10**9), None))
    while True:
        if boundary == "numpy":
            if method in ("exact_local", "exact_bidir_local", "exact_eps_local"):
                from .compact import confidence_compact

                result = confidence_compact(
                    post,
                    word,
                    threshold=protocol["confidence_threshold"],
                    budget=protocol["commit_budget"],
                )
            else:
                result = confidence(
                    post,
                    certificate,
                    word,
                    threshold=protocol["confidence_threshold"],
                    budget=protocol["commit_budget"],
                    outside=outside,
                )
        else:
            numerators, lower = post.marginals()
            upper = Fraction(certificate["upper_tail"]) * prod(weights.denominators)
            if upper.denominator != 1:
                raise RuntimeError("dense confidence units differ")
            decisions, ambiguous = classify(
                word,
                canvas,
                numerators,
                lower,
                upper.numerator,
                Fraction(protocol["confidence_threshold"]),
            )
            accepted = [p for p, d in decisions.items() if d["accepted"]]
            result = dict(
                decisions=decisions,
                ambiguous=ambiguous,
                queries=len(decisions),
                committed=None
                if ambiguous
                else accepted[: protocol["commit_budget"]] or [min(decisions)],
            )
        if not result["ambiguous"]:
            break
        tol = next(tolerances)
        begin = now()
        if tol is None:
            if boundary == "numpy":
                post, certificate = infer(tolerance, "exact_stack")
            else:
                # Dense controls also receive the exact original full confidence fallback.
                from ..generation_service import full_query

                post = full_query(table, weights, deadline - monotonic())
                certificate = dict(delta="0", depth=None, upper_tail="0")
        else:
            post, certificate = infer(tol)
        refinements.append(dict(tolerance=None if tol is None else str(tol), cost=elapsed(begin)))
    if monotonic() > deadline:
        raise TimeoutError("complete confidence deadline; no success")
    query_cost = elapsed(queries_start)
    cost, forward = elapsed(started), case["forward_and_softmax"]
    return dict(
        status="complete",
        operation=cost,
        forward=forward,
        paid_total={unit: cost[unit] + forward[unit] for unit in ("wall", "cpu")},
        numeric=numeric,
        inference=inference,
        sample_cost=sample_cost,
        sample_valid_mass=sample_valid_mass,
        confidence_cost=query_cost,
        refinements=refinements,
        certificate=sample_certificate,
        sample=list(word),
        committed=result["committed"],
        decisions=result["decisions"],
        queries=result["queries"],
        valid_mass=str(post.mass),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    subprocess.run(["git", "diff", "--quiet", "HEAD", "--"], cwd=ROOT, check=True)
    protocol_path = WORK / "consumer-v2-protocol.json"
    protocol = json.loads(protocol_path.read_text())
    paths = sorted(p for p in args.input.glob("*.json") if p.with_suffix(".npy").exists())
    if len(paths) != 15:
        raise ValueError("development must include ALL15 original states")
    args.output.mkdir(parents=True, exist_ok=False)
    startup = now()
    vocabulary = args.input / "vocabulary.json"
    adapter = CompositionalByteLevelAdapter.from_token_pieces(json.loads(vocabulary.read_text()))
    table = LexerTable(adapter)
    partition = Partition(tuple(table.class_of), len(table.classes), protocol["block_size"])
    setup = elapsed(startup)
    source_paths = [*WORK.glob("*.py"), *Path(__file__).parent.glob("*.py")]
    metadata = dict(
        producer_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        protocol=protocol,
        protocol_sha256=digest(protocol_path),
        startup=setup,
        vocabulary_sha256=digest(vocabulary),
        cases={p.name: digest(p) for p in paths},
        sources={str(p.relative_to(ROOT)): digest(p) for p in source_paths},
        numpy=np.__version__,
        python=platform.python_version(),
        new_neural_forwards=0,
        numeric_scope="Exact normalized represented old binary64 heads; no new model evidence",
        law_scope=(
            "Unlimited kernel only; wall-censored COMPLETE outputs are not proven target-law draws"
        ),
    )
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    configs = [(m, o, "numpy") for m in protocol["methods"] for o in protocol["outside"]]
    configs += [(m, "dense", "python_dense") for m in protocol["candidate_family"]]
    signal.signal(signal.SIGALRM, alarm)
    count, paired, mass_pairs = 0, {}, {}
    with (args.output / "rows.jsonl").open("w") as log:
        for repeat in range(protocol["repetitions"]):
            for index, path in enumerate(paths):
                case = json.loads(path.read_text())
                order = (
                    configs[(repeat + index) % len(configs) :]
                    + configs[: (repeat + index) % len(configs)]
                )
                for method, outside, boundary in order:
                    gc.collect()
                    started = now()
                    row = dict(
                        case=path.stem,
                        mask_count=case["mask_count"],
                        repeat=repeat,
                        method=method,
                        outside=outside,
                        boundary=boundary,
                    )
                    signal.setitimer(signal.ITIMER_REAL, protocol["resources"]["seconds"])
                    try:
                        try:
                            result = operation(
                                table,
                                partition,
                                path,
                                method,
                                outside,
                                boundary,
                                protocol["seed"] + repeat,
                                protocol,
                            )
                        finally:
                            signal.setitimer(signal.ITIMER_REAL, 0)
                        row.update(result)
                        if row["status"] == "complete":
                            mass_key = path.stem, repeat, method
                            if (
                                mass_key in mass_pairs
                                and mass_pairs[mass_key] != row["sample_valid_mass"]
                            ):
                                raise RuntimeError(
                                    "numeric interfaces changed initial bounded mass"
                                )
                            mass_pairs[mass_key] = row["sample_valid_mass"]
                        if row["status"] == "complete" and boundary == "numpy":
                            key = path.stem, repeat, method
                            signature = (
                                row["sample"],
                                row["committed"],
                                row["decisions"],
                                row["valid_mass"],
                            )
                            if key in paired and paired[key] != signature:
                                raise RuntimeError(
                                    "sparse interfaces changed literal sample/commit/queries"
                                )
                            paired[key] = signature
                    except (CompilationLimit, MemoryError, TimeoutError, RecursionError) as error:
                        signal.setitimer(signal.ITIMER_REAL, 0)
                        row.update(
                            status="resource_refusal", reason=str(error), operation=elapsed(started)
                        )
                    except Exception as error:
                        signal.setitimer(signal.ITIMER_REAL, 0)
                        row.update(
                            status="error",
                            reason=str(error),
                            traceback=traceback.format_exc(),
                            operation=elapsed(started),
                        )
                    row["peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                    row["session_cold_total"] = {
                        unit: row.get("paid_total", row["operation"])[unit] + setup[unit]
                        for unit in ("wall", "cpu")
                    }
                    log.write(json.dumps(row, separators=(",", ":")) + "\n")
                    log.flush()
                    count += 1
                    if count % 12 == 0 or row["status"] == "error":
                        print(
                            json.dumps(
                                dict(
                                    records=count,
                                    case=path.stem,
                                    repeat=repeat,
                                    status=row["status"],
                                )
                            ),
                            flush=True,
                        )
    print(
        json.dumps(
            dict(
                records=count,
                planned=len(paths) * len(configs) * protocol["repetitions"],
                complete_campaign=True,
            )
        ),
        flush=True,
    )


if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_AS, (3 * 1024**3,) * 2)
    main()
