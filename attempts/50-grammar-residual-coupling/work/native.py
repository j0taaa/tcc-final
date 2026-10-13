"""Prospective all-frame real-head insertion screen; no competitive timing claim."""

import argparse
import hashlib
import importlib
import json
import os
import resource
import signal
import subprocess
import sys
import traceback
from fractions import Fraction as F
from pathlib import Path
from random import Random
from time import perf_counter, process_time

import numpy as np

from mwpc_exact.cfg_posterior import CompilationLimit, compile_cfg_sampler
from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.mass_certificate import ProbabilityInput
from mwpc_exact.reference.json_grammar import json_source_grammar
from mwpc_exact.reference.normalization import normalize_to_cnf
from mwpc_exact.state import SelectionInput
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import SupportKind

from .residual import Residual

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[2]
SOURCE = ROOT / ".cache/a49-external-capture-v25"
META_SHA = "1c25a740ba5d5fa8b5d855055c69ca110f41fb95210895abbf3f6922eee20e97"
FACTORIES = {
    "scalar": ("scalar", "ScalarResidual"),
    "marginal": ("rounded", "RoundedResidual"),
    "precision": ("precision", "PrecisionResidual"),
    "profile": ("upper", "UpperResidual"),
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def metadata():
    assert digest(SOURCE / "metadata.json") == META_SHA
    meta = json.loads((SOURCE / "metadata.json").read_text())
    assert digest(SOURCE / "vocabulary.json") == meta["vocabulary_sha256"]
    assert len(meta["selected"]) == 5
    return meta


def frame(name):
    data = json.loads((SOURCE / (name + ".json")).read_text())
    assert digest(SOURCE / (name + ".npy")) == data["probabilities_sha256"]
    return data, np.load(SOURCE / (name + ".npy"), allow_pickle=False)


def state_inputs(data, matrix, kind, canvas):
    adapter = CompositionalByteLevelAdapter.from_token_pieces(
        json.loads((SOURCE / "vocabulary.json").read_text())
    )
    source = json_source_grammar()
    original = np.load(SOURCE / (data["case"] + f"-{data['mask_count']}.npy"), allow_pickle=False)
    indices = {p: j for j, p in enumerate(data["positions"])}
    domains = {
        p: (fixed,)
        if fixed is not None
        else tuple(range(adapter.vocabulary_size))
        if kind == "full"
        else tuple(
            sorted(range(adapter.vocabulary_size), key=lambda t: (-original[indices[p], t], t))[:16]
        )
        for p, fixed in enumerate(canvas)
    }
    support = build_per_position_support(
        canvas=tuple(canvas),
        policy=SupportPolicy(
            SupportKind.FULL if kind == "full" else SupportKind.EXPLICIT,
            adapter.vocabulary_size,
        ),
        explicit_support=domains,
    )
    state = SelectionInput(
        normalize_to_cnf(source).grammar,
        tuple(canvas),
        (),
        support,
        adapter,
        EOSPolicy(EOSMode.ABSENT),
    )
    rows = []
    for p, tokens in enumerate(support.rows):
        if canvas[p] is not None:
            rows.append((F(1),))
            continue
        ratios = [float(x).as_integer_ratio() for x in matrix[indices[p]]]
        assert all(a >= 0 for a, _ in ratios)
        scale = max(b for _, b in ratios)
        integers = [a * (scale // b) for a, b in ratios]
        total = sum(integers)
        rows.append(tuple(F(integers[t], total) for t in tokens))
    return source, ProbabilityInput(state, tuple(rows))


def valid(ids, state):
    assert len(ids) == len(state.canvas)
    assert all(v in row for v, row in zip(ids, state.support.rows, strict=True))
    assert all(t is None or t == v for t, v in zip(state.canvas, ids, strict=True))
    raw = b"".join(state.tokenizer_adapter.emissions[t] for t in ids)
    json.loads(raw.decode("utf8"), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    return raw.decode("utf8")


def compile_plan(source, state):
    return compile_cfg_sampler(
        source,
        state,
        max_chart_cells=200_000,
        max_alternatives=1_000_000,
        max_preprocessing_work=5_000_000,
        timeout_seconds=30,
    )


def worker(stage, name, kind, output, method):
    started = perf_counter(), process_time()
    result = dict(stage=stage, frame=name, support=kind, method=method)

    def expired(*_):
        raise TimeoutError("30s functional stage deadline")

    limit = 3 << 30
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, 30)
    try:
        metadata()
        data, original = frame(name)
        offset = int(data["case"][:12], 16) + data["mask_count"]
        if stage == "initial":
            source, draft = state_inputs(data, original, kind, data["canvas"])
            plan = compile_plan(source, draft.state)
            posterior = plan.evaluate(draft)
            result.update(
                nodes=len(plan.terms),
                alternatives=plan.alternatives,
                valid_mass=str(posterior.valid_mass),
                omitted_mass=str(draft.omitted_mass),
            )
            if not posterior.valid_mass:
                result["status"] = "ZERO_VALID_MASS"
            else:
                ids = posterior.sample(Random(202610135013 + offset))
                canvas = list(data["canvas"])
                canvas[min(data["positions"])] = ids[min(data["positions"])]
                result.update(
                    status="ADMITTED", draft=list(ids), canvas=canvas, text=valid(ids, draft.state)
                )
        else:
            initial = json.loads((output / f"{name}-{kind}.json").read_text())
            capture = json.loads((output / f"{name}-{kind}-head.json").read_text())
            target_path = output / capture["probabilities_file"]
            assert digest(target_path) == capture["probabilities_sha256"]
            matrix = np.load(target_path, allow_pickle=False)
            source, draft = state_inputs(data, original, kind, initial["canvas"])
            _, target = state_inputs(data, matrix, kind, initial["canvas"])
            assert draft.state == target.state
            plan = compile_plan(source, draft.state)
            base = Residual(plan, target, draft)
            ids = tuple(initial["draft"])
            p, q = base.point(ids, 0), base.point(ids, 1)
            assert q > 0
            accept = min(F(1), p / q)
            rng = Random(202610135014 + offset)
            retained = rng.randrange(accept.denominator) < accept.numerator
            result.update(
                accept_probability=str(accept),
                retained=retained,
                attempts=0,
                source_head_sha256=data["probabilities_sha256"],
                target_head_sha256=capture["probabilities_sha256"],
            )
            if not retained:
                module, constructor = FACTORIES[method]
                factory = getattr(importlib.import_module(f"{__package__}.{module}"), constructor)
                sampler = factory(plan, target, draft)
                ids, attempts = sampler.sample(Random(202610135015 + offset), max_attempts=4096)
                result["attempts"] = attempts
            if ids is None:
                result["status"] = "BOUNDED_FAIL"
            else:
                result.update(
                    status="VALID_CORRECTED", output=list(ids), text=valid(ids, target.state)
                )
    except (CompilationLimit, TimeoutError, MemoryError, RuntimeError) as exc:
        result.update(status="RESOURCE_REFUSAL", reason=str(exc) or type(exc).__name__)
    except Exception:
        result.update(status="ERROR", traceback=traceback.format_exc())
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    result["diagnostic_wall_cpu"] = [perf_counter() - started[0], process_time() - started[1]]
    suffix = f"-{method}" if stage == "correct" else ""
    dump(output / f"{name}-{kind}{suffix}.json", result)


def run(stage, output):
    meta = metadata()
    if stage == "initial":
        output.mkdir(parents=True, exist_ok=False)
        dump(
            output / "origin.json",
            dict(
                producer=subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
                ).strip(),
                source_metadata_sha256=META_SHA,
                protocol_sha256=digest(WORK / "native-consumer-v13.md"),
            ),
        )
    rows = []
    for example in meta["selected"]:
        for masks in [4, 8, 16]:
            name = f"{example['key']}-{masks}"
            for kind in ["full", "top16"]:
                if (
                    stage == "correct"
                    and json.loads((output / f"{name}-{kind}.json").read_text())["status"]
                    != "ADMITTED"
                ):
                    continue
                for method in FACTORIES if stage == "correct" else ["scalar"]:
                    cmd = [
                        sys.executable,
                        "-m",
                        __package__ + ".native",
                        "--worker",
                        stage,
                        "--frame",
                        name,
                        "--support",
                        kind,
                        "--method",
                        method,
                        "--output",
                        str(output),
                    ]
                    env = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1")
                    suffix = f"-{method}" if stage == "correct" else ""
                    path = output / f"{name}-{kind}{suffix}.json"
                    try:
                        done = subprocess.run(
                            cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=45
                        )
                        if done.returncode or not path.exists():
                            dump(
                                path,
                                dict(
                                    stage=stage,
                                    frame=name,
                                    support=kind,
                                    method=method,
                                    status="ERROR",
                                    stderr=done.stderr,
                                    returncode=done.returncode,
                                ),
                            )
                    except subprocess.TimeoutExpired:
                        dump(
                            path,
                            dict(
                                stage=stage,
                                frame=name,
                                support=kind,
                                method=method,
                                status="RESOURCE_REFUSAL",
                                reason="45s supervisor deadline",
                            ),
                        )
                    result = json.loads(path.read_text())
                    rows.append(result)
                    print(
                        json.dumps({k: result[k] for k in ["frame", "support", "status"]}),
                        flush=True,
                    )
                    dump(output / f"{stage}-rows.json", rows)
    dump(
        output / f"{stage}-summary.json",
        dict(
            scope="FUNCTIONAL_RESOURCE_ONLY",
            records=len(rows),
            counts={
                s: sum(r["status"] == s for r in rows) for s in sorted({r["status"] for r in rows})
            },
        ),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["initial", "correct"])
    parser.add_argument("--worker", choices=["initial", "correct"])
    parser.add_argument("--frame")
    parser.add_argument("--support", choices=["full", "top16"])
    parser.add_argument("--method", choices=list(FACTORIES), default="scalar")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.worker:
        worker(args.worker, args.frame, args.support, args.output, args.method)
    else:
        run(args.stage, args.output)
