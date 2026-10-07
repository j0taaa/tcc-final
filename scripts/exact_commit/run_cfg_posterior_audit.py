"""Frozen M34 grid and all M31 replays; bounded workers, no success selection."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import multiprocessing as mp
import platform
import queue as queues
import resource
import subprocess
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from random import Random
from time import perf_counter

from scripts.exact_commit.cfg_stack_control import StackLimit, compile_stack_plan
from scripts.exact_commit.probability_audit_controls import compile_array_plan

from mwpc_exact.cfg_posterior import CompilationLimit, compile_cfg_sampler
from mwpc_exact.conflict_proof import read_state, state_data
from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.mass_certificate import ProbabilityInput
from mwpc_exact.reference.byte_grammars import _SourceGrammarBuilder
from mwpc_exact.reference.json_grammar import json_source_grammar
from mwpc_exact.reference.normalization import normalize_to_cnf
from mwpc_exact.state import SelectionInput
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import SupportKind

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "configs/experiments/m34_cfg_posterior_v1.json"


def source_grammar(kind):
    if kind == "json":
        return json_source_grammar()
    if kind == "dyck":
        b = _SourceGrammarBuilder(("S", "N"), start="S")
        b.rule("S", "N", "S")
        b.rule("S")
        for opening, closing in ((b"(", b")"), (b"[", b"]")):
            b.rule("N", opening, "S", closing)
    else:
        b = _SourceGrammarBuilder(("S", "Items", "Tail"), start="S")
        b.rule("S", b"[", "Items", b"]")
        b.rule("Items")
        b.rule("Items", "S", "Tail")
        b.rule("Tail")
        if kind == "recursive_arrays":
            b.rule("Tail", b",", "S", "Tail")
    return b.build()


def scaling_inputs(slots, distribution, control, seed):
    source = source_grammar("dyck")
    fixed = tuple((0 if i % 2 == 0 else 2) if i < slots // 2 else None for i in range(slots))
    canvas = fixed if control == "fixed_alternating_opening_half" else (None,) * slots
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(kind=SupportKind.FULL, vocabulary_size=4),
        explicit_support={
            i: (token,) if token is not None else (0, 1, 2, 3) for i, token in enumerate(canvas)
        },
    )
    state = SelectionInput(
        normalize_to_cnf(source).grammar,
        canvas,
        (),
        support,
        CompositionalByteLevelAdapter((b"(", b")", b"[", b"]")),
        EOSPolicy(EOSMode.ABSENT),
    )
    rng = Random(seed + slots)
    rows = []
    for fixed_token, row in zip(canvas, support.rows, strict=True):
        weights = [1 if distribution == "uniform" else rng.randrange(1, 18) for _ in row]
        rows.append(
            (Fraction(1),)
            if fixed_token is not None
            else tuple(Fraction(w, sum(weights)) for w in weights)
        )
    return ProbabilityInput(state, tuple(rows))


def worker(queue, data, kind, method, grid):
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    record = {"method": method, "status": "ERROR"}
    try:
        started = perf_counter()
        if method == "cfg":
            plan = compile_cfg_sampler(
                source_grammar(kind),
                data.state,
                max_chart_cells=grid["compiler_cell_limit"],
                max_alternatives=grid["compiler_alternative_limit"],
                timeout_seconds=grid["external_deadline_seconds"],
            )
            cells, arcs = len(plan.terms), plan.alternatives
        elif kind == "dyck":
            plan = compile_stack_plan(
                data.state.tokenizer_adapter.emissions,
                data.state.support.rows,
                max_cells=grid["compiler_cell_limit"],
                max_transitions=grid["compiler_alternative_limit"],
                timeout_seconds=grid["external_deadline_seconds"],
            )
            cells, arcs = plan.cells, plan.transitions
        else:
            plan = compile_array_plan(
                data.state.tokenizer_adapter.emissions,
                data.state.support.rows,
                one_child=kind == "recursive_one_child_arrays",
                max_state_cells=grid["compiler_cell_limit"],
            )
            cells = plan.state_cells
            arcs = sum(len(arcs) for layer in plan.edges for arcs in layer.values())
        record.update(compilation_seconds=perf_counter() - started, cells=cells, alternatives=arcs)
        timings = []
        for repetition in range(grid["timing_repeats"] + 1):
            started = perf_counter()
            if method == "cfg":
                posterior = plan.evaluate(data)
                mass = posterior.valid_mass
                marginal = [[str(x) for x in row] for row in posterior.marginals]
                detail = {
                    "mass_seconds": posterior.inside_seconds,
                    "marginal_seconds": posterior.marginal_seconds,
                }
                sample_start = perf_counter()
                sample = posterior.sample(Random(repetition)) if mass else ()
            elif kind == "dyck":
                posterior = plan.evaluate(data.probabilities)
                mass = posterior.valid_mass
                marginal = [[str(x) for x in row] for row in posterior.marginals]
                detail = {
                    "mass_seconds": posterior.mass_seconds,
                    "marginal_seconds": posterior.marginal_seconds,
                }
                sample_start = perf_counter()
                sample = posterior.sample(Random(repetition)) if mass else ()
            else:
                mass, count = plan.forward(data.probabilities)
                plan.backward(data.probabilities)
                detail = {
                    "mass_backward_seconds": perf_counter() - started,
                    "positive_token_paths": count,
                }
                marginal = None  # original M31 control interface; do not invent timing
                sample_start = perf_counter()
                sample = ()
            detail.update(
                query_seconds=sample_start - started, sample_seconds=perf_counter() - sample_start
            )
            if repetition:
                timings.append(detail)
        record.update(
            status="EXACT_ON_SUPPORT" if mass else "ZERO_MASS_ON_SUPPORT",
            valid_mass=str(mass),
            marginals=marginal,
            sample=sample,
            timings=timings,
        )
        if sample:
            word = data.state.tokenizer_adapter.detokenize_bytes(sample)
            if kind == "dyck":
                from scripts.exact_commit.cfg_stack_control import step

                stack = ()
                for byte in word:
                    stack = step(stack, byte)
                    if stack is None:
                        raise ValueError("invalid sample")
                if stack:
                    raise ValueError("unfinished sample")
            else:
                decoded = json.loads(word)
                if kind != "json" and not isinstance(decoded, list):
                    raise ValueError("invalid recursive-array sample")
        record["max_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    except (CompilationLimit, StackLimit) as error:
        record.update(status="TIMEOUT_WORK_LIMIT", detail=str(error))
    except Exception as error:
        record.update(status="ERROR", detail=f"{type(error).__name__}: {error}")
    queue.put(record)


def run_job(data, kind, method, grid):
    context = mp.get_context("spawn")
    queue = context.Queue()
    process = context.Process(target=worker, args=(queue, data, kind, method, grid))
    started = perf_counter()
    process.start()
    try:
        result = queue.get(timeout=grid["external_deadline_seconds"])
    except queues.Empty:
        result = {
            "method": method,
            "status": "TIMEOUT_EXTERNAL" if process.exitcode is None else "ERROR",
            "exitcode": process.exitcode,
        }
    finally:
        if process.is_alive():
            process.terminate()
        process.join()
        queue.close()
    result["worker_wall_seconds"] = perf_counter() - started
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("scaling", "replay"), required=True)
    args = parser.parse_args()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise ValueError("commit producing code/config before measurements")
    config = json.loads(CONFIG.read_text())
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    metadata = {
        "git_commit": commit,
        "seed": config["seed"],
        "config_sha256": hashlib.sha256(CONFIG.read_bytes()).hexdigest(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "cpu": platform.processor(),
        "memory_scope": "fresh 2-GiB worker, including imports",
        "distribution_scope": "frozen mean-field; exact on original represented tokens",
        "model_id": None if args.mode == "scaling" else config["replay"]["model_id"],
        "model_revision": None if args.mode == "scaling" else config["replay"]["model_revision"],
        "tokenizer_revision": None
        if args.mode == "scaling"
        else config["replay"]["tokenizer_revision"],
        "sampling_seeds": [0, 1, 2, 3],
        "saved_model_prediction_seed": None if args.mode == "scaling" else 310000,
    }
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (args.output / "config.json").write_bytes(CONFIG.read_bytes())
    cases = []
    if args.mode == "scaling":
        grid = config["scaling"]
        for slots in grid["slots"]:
            for distribution in grid["distributions"]:
                for control in grid["controls"]:
                    cases.append(
                        (
                            f"dyck-{slots}-{distribution}-{control}",
                            "dyck",
                            scaling_inputs(slots, distribution, control, config["seed"]),
                            None,
                        )
                    )
    else:
        original = ROOT / "docs/artifacts/raw/m31_probability_v1/primary/inputs"
        for path in sorted(original.glob("*.json.gz")):
            archived = json.load(gzip.open(path, "rt"))
            kind = archived["case"]["probe"]["grammar"]
            state = replace(
                read_state(archived["input"]),
                grammar=normalize_to_cnf(source_grammar(kind)).grammar,
            )
            data = ProbabilityInput(
                state, tuple(tuple(Fraction(*p) for p in row) for row in archived["probabilities"])
            )
            cases.append(
                (archived["case"]["id"], kind, data, hashlib.sha256(path.read_bytes()).hexdigest())
            )
        if len(cases) != config["replay"]["case_count"]:
            raise ValueError("incomplete replay cohort")
    with (args.output / "rows.jsonl").open("x") as output:
        for name, kind, data, original_sha in cases:
            raw = {
                "input": state_data(data.state),
                "probabilities": [
                    [[p.numerator, p.denominator] for p in row] for row in data.probabilities
                ],
            }
            payload = json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
            with gzip.open(args.output / f"{name}-input.json.gz", "wb") as stream:
                stream.write(payload)
            pair = [run_job(data, kind, method, config["scaling"]) for method in ("cfg", "stack")]
            if all("valid_mass" in result for result in pair):
                if pair[0]["valid_mass"] != pair[1]["valid_mass"]:
                    raise ValueError(f"independent mass disagreement: {name}")
                if kind == "dyck" and pair[0]["marginals"] != pair[1]["marginals"]:
                    raise ValueError(f"independent marginal disagreement: {name}")
            if "-uniform-all_masked" in name and "valid_mass" in pair[0]:
                n = len(data.state.canvas) // 2
                catalan = math.comb(2 * n, n) // (n + 1)
                if Fraction(pair[0]["valid_mass"]) != Fraction(catalan * 2**n, 4 ** (2 * n)):
                    raise ValueError("closed-form Catalan mass disagreement")
            row = {
                **metadata,
                "case": name,
                "kind": kind,
                "input_sha256": hashlib.sha256(payload).hexdigest(),
                "original_artifact_sha256": original_sha,
                "support": data.state.support.exactness_scope.to_dict(),
                "grammar_sha256": hashlib.sha256(
                    json.dumps(data.state.grammar.to_dict(), sort_keys=True).encode()
                ).hexdigest(),
                "omitted_mass": str(data.omitted_mass),
                "results": pair,
            }
            output.write(json.dumps(row) + "\n")
            output.flush()
            print(json.dumps({"case": name, "statuses": [r["status"] for r in pair]}), flush=True)


if __name__ == "__main__":
    main()
