"""All 27 saved model cases: exact support rejection and clamped forest reuse."""

from __future__ import annotations

import argparse
import bisect
import gzip
import hashlib
import itertools
import json
import math
import subprocess
from fractions import Fraction
from pathlib import Path
from random import Random
from time import perf_counter

from scripts.exact_commit.run_cfg_posterior_audit import ROOT, source_grammar

from mwpc_exact.cfg_posterior import CompilationLimit, compile_cfg_sampler
from mwpc_exact.conflict_proof import read_state
from mwpc_exact.mass_certificate import ProbabilityInput
from mwpc_exact.state import SelectionInput
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.types import SupportKind


def valid(word, kind):
    if word is None:
        return False
    try:
        value = json.loads(word)
    except (ValueError, UnicodeError):
        return False
    if kind == "json":
        return True
    pending = [value]
    while pending:
        node = pending.pop()
        if not isinstance(node, list) or (kind == "recursive_one_child_arrays" and len(node) > 1):
            return False
        pending.extend(node)
    return True


def rejection(data, kind, seed, budget, deadline):
    started = perf_counter()
    rng = Random(seed)
    cumulative = []
    for row in data.probabilities:
        denominator = math.lcm(*(p.denominator for p in row))
        weights = [p.numerator * (denominator // p.denominator) for p in row]
        cumulative.append(tuple(itertools.accumulate(weights)))
    preparation = perf_counter() - started
    attempts = 0
    while attempts < budget and perf_counter() - started < deadline:
        attempts += 1
        sample = tuple(
            row[bisect.bisect_right(cdf, rng.randrange(cdf[-1]))]
            for row, cdf in zip(data.state.support.rows, cumulative, strict=True)
        )
        words = [data.state.tokenizer_adapter.emissions[t] for t in sample]
        word = None if any(w is None for w in words) else b"".join(words)
        if valid(word, kind):
            return {
                "status": "SAMPLED",
                "attempts": attempts,
                "seconds": perf_counter() - started,
                "preparation_seconds": preparation,
                "sample": sample,
            }
    return {
        "status": "TRIAL_LIMIT" if attempts == budget else "TIMEOUT",
        "attempts": attempts,
        "seconds": perf_counter() - started,
        "preparation_seconds": preparation,
    }


def reuse(data, kind, seed):
    started = perf_counter()
    try:
        plan = compile_cfg_sampler(source_grammar(kind), data.state, timeout_seconds=30)
        initial = plan.evaluate(data)
        if not initial.valid_mass:
            return {"status": "ZERO_MASS_ON_SUPPORT"}
        sample = initial.sample(Random(seed))
        canvas = list(data.state.canvas)
        free = [i for i, token in enumerate(canvas) if token is None]
        for i in free[: max(1, len(free) // 2)]:
            canvas[i] = sample[i]
        rows = {
            i: (token,) if token is not None else data.state.support.rows[i]
            for i, token in enumerate(canvas)
        }
        support = build_per_position_support(
            canvas=tuple(canvas),
            policy=SupportPolicy(
                kind=SupportKind.EXPLICIT,
                vocabulary_size=data.state.support.exactness_scope.vocabulary_size,
            ),
            explicit_support=rows,
        )
        state = SelectionInput(
            data.state.grammar,
            tuple(canvas),
            (),
            support,
            data.state.tokenizer_adapter,
            data.state.eos_policy,
        )
        changed = ProbabilityInput(
            state,
            tuple(
                (Fraction(1),) if token is not None else row
                for token, row in zip(canvas, data.probabilities, strict=True)
            ),
        )
        initial_seconds = perf_counter() - started
        started = perf_counter()
        cached = plan.evaluate(changed)
        reuse_seconds = perf_counter() - started
        started = perf_counter()
        fresh = compile_cfg_sampler(
            source_grammar(kind), changed.state, timeout_seconds=30
        ).evaluate(changed)
        fresh_seconds = perf_counter() - started
        if (cached.valid_mass, cached.marginals) != (fresh.valid_mass, fresh.marginals):
            raise ValueError("cached/fresh disagreement")
        result = cached.sample(Random(seed))
        if any(token is not None and token != result[i] for i, token in enumerate(canvas)):
            raise ValueError("committed token changed")
        if not valid(changed.state.tokenizer_adapter.detokenize_bytes(result), kind):
            raise ValueError("independent sample rejection")
        return {
            "status": "EXACT_ON_SUPPORT",
            "initial_seconds": initial_seconds,
            "reuse_seconds": reuse_seconds,
            "fresh_seconds": fresh_seconds,
            "new_valid_mass": str(cached.valid_mass),
            "sample": result,
            "fixed_positions": [i for i, token in enumerate(canvas) if token is not None],
        }
    except CompilationLimit as error:
        return {"status": "TIMEOUT_WORK_LIMIT", "detail": str(error)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise ValueError("commit producing code before running")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    config = {
        "seed": 20261006,
        "trial_budget": 10000,
        "deadline_seconds": 30,
        "selection": "all 18 saved MDLM arrays and nine saved MDLM JSON inputs",
    }
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    with (args.output / "rows.jsonl").open("x") as output:
        for phase in ("integer-replay", "integer-json-model"):
            rows = [
                json.loads(line)
                for line in (args.inputs / phase / "rows.jsonl").read_text().splitlines()
            ]
            for row in rows:
                path = args.inputs / phase / f"{row['case']}-input.json.gz"
                archived = json.load(gzip.open(path, "rt"))
                data = ProbabilityInput(
                    read_state(archived["input"]),
                    tuple(tuple(Fraction(*p) for p in r) for r in archived["probabilities"]),
                )
                result = {
                    **row,
                    "source_commit": row["git_commit"],
                    "git_commit": commit,
                    "config_sha256": hashlib.sha256(
                        (args.output / "config.json").read_bytes()
                    ).hexdigest(),
                    "source_input_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "rejection": rejection(
                        data,
                        row["kind"],
                        config["seed"],
                        config["trial_budget"],
                        config["deadline_seconds"],
                    ),
                    "reuse": reuse(data, row["kind"], config["seed"]),
                }
                output.write(json.dumps(result) + "\n")
                output.flush()
                print(
                    json.dumps(
                        {
                            "case": row["case"],
                            "rejection": result["rejection"]["status"],
                            "reuse": result["reuse"]["status"],
                        }
                    ),
                    flush=True,
                )


if __name__ == "__main__":
    main()
