"""Opt-in real iterative MDLM consumer; every changed canvas pays a new forward."""

import argparse
import ctypes
import json
import os
import platform
import resource
import selectors
import subprocess
import sys
import time
from fractions import Fraction
from pathlib import Path

from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from ..generation import Service as OriginalService
from .benchmark import ROOT, WORK, digest, elapsed, now


def process_cpu_clock(pid):
    """POSIX process CPU clock through libc; Python only exposes pthread's helper."""
    function = ctypes.CDLL(None).clock_getcpuclockid
    function.argtypes = (ctypes.c_int, ctypes.POINTER(ctypes.c_int))
    function.restype = ctypes.c_int
    clock = ctypes.c_int()
    error = function(pid, ctypes.byref(clock))
    if error:
        raise OSError(error, os.strerror(error))
    return clock.value


class Service(OriginalService):
    def __init__(self, method, vocabulary, error_log):
        self.errors = error_log.open("w")
        self.process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "attempts.24-certified-depth-approximation.work.consumer_v2.service",
                "--method",
                method,
                "--vocabulary",
                str(vocabulary.resolve()),
            ],
            cwd=ROOT,
            env=dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1"),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self.errors,
            text=True,
        )
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)
        try:
            self.child_clock = process_cpu_clock(self.process.pid)
            self.ready = self.read()
            if self.ready["status"] != "ready":
                raise RuntimeError("CPU consumer service failed startup")
            self.ready["complete_process_startup_cpu"] = time.clock_gettime(self.child_clock)
        except Exception:
            self.close()
            raise


def main():
    import numpy as np
    import torch
    from scripts.exact_commit.mdlm_cpu import load_cpu_model

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--development-decision", type=Path, required=True)
    parser.add_argument("--compact-decision", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    subprocess.run(["git", "diff", "--quiet", "HEAD", "--"], cwd=ROOT, check=True)
    development = json.loads(args.development_decision.read_text())
    compact_decision = json.loads(args.compact_decision.read_text())
    if not development["practical_development_gate"] or not development["campaign_complete"]:
        raise ValueError("complete positive development required before NEW forwards")
    if (
        not compact_decision["campaign_complete"]
        or not compact_decision["surviving_scoped_benefit"]
    ):
        raise ValueError("complete surviving matched compact gate required")
    protocol = json.loads((WORK / "consumer-v2-neural-protocol.json").read_text())
    capture = json.loads((args.input / "metadata.json").read_text())
    if capture["phase"] != "independent" or len(capture["selected"]) != 5:
        raise ValueError("ALL five original pinned external documents required")
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "heads").mkdir()
    config = capture["config"]
    torch.set_num_threads(config["torch_cpu_threads"])
    torch.set_flush_denormal(False)
    torch.manual_seed(protocol["seeds"][0])
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    begin = now()
    model, hashes, adapted = load_cpu_model(config, ROOT / ".cache/mdlm")
    if hashes != capture["model_hashes"] or adapted != capture["adapted_model_sha256"]:
        raise ValueError("pinned public backbone/checkpoint changed")
    model.to("cuda")
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    with torch.inference_mode():
        model(
            input_ids=torch.full((1, 32), config["mask_token_id"], device="cuda"),
            timesteps=torch.zeros(1, device="cuda"),
        )
    torch.cuda.synchronize()
    model_setup = elapsed(begin)
    vocabulary = args.input / "vocabulary.json"
    if digest(vocabulary) != capture["vocabulary_sha256"]:
        raise ValueError("original full tokenizer changed")
    adapter = CompositionalByteLevelAdapter.from_token_pieces(json.loads(vocabulary.read_text()))
    source_paths = [*WORK.glob("*.py"), *Path(__file__).parent.glob("*.py")]
    metadata = dict(
        protocol=protocol,
        protocol_sha256=digest(WORK / "consumer-v2-neural-protocol.json"),
        input_capture=capture,
        input_capture_sha256=digest(args.input / "metadata.json"),
        development_decision_sha256=digest(args.development_decision),
        compact_decision_sha256=digest(args.compact_decision),
        producer_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        sources={str(p.relative_to(ROOT)): digest(p) for p in source_paths},
        model_hashes=hashes,
        adapted_model_sha256=adapted,
        model_setup=model_setup,
        model_parameters_updated=False,
        torch=torch.__version__,
        cuda=torch.version.cuda,
        gpu=torch.cuda.get_device_name(),
        python=platform.python_version(),
        warmup_forwards=1,
        cold_scope=(
            "Reconstructed fresh-request cost: measured model/warmup plus same-method "
            "service startup plus actual warm case. Not a separately timed cold run."
        ),
    )
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    services = {}
    try:
        with (args.output / "rows.jsonl").open("w") as log:
            count = 0
            for repeat, seed in enumerate(protocol["seeds"]):
                for i, example in enumerate(capture["selected"]):
                    for masks in (4, 8, 16):
                        methods = protocol["methods"]
                        offset = (repeat + i + masks) % len(methods)
                        for method in methods[offset:] + methods[:offset]:
                            name = f"{example['key']}-{masks}-{method}-seed{seed}"
                            initial = json.loads(
                                (args.input / (f"{example['key']}-{masks}.json")).read_text()
                            )
                            canvas = list(initial["canvas"])
                            result = dict(
                                case=example["key"],
                                masks=masks,
                                method=method,
                                seed=seed,
                                repeat=repeat,
                                steps=[],
                                status="started",
                                new_forwards=0,
                            )
                            setup = None
                            try:
                                if method not in services:
                                    begin = now()
                                    services[method] = Service(
                                        method, vocabulary, args.output / (name + ".stderr")
                                    )
                                    parent_startup = elapsed(begin)
                                    setup = dict(
                                        wall=parent_startup["wall"],
                                        cpu=parent_startup["cpu"]
                                        + services[method].ready["complete_process_startup_cpu"],
                                    )
                                    services[method].measured_setup = setup
                                service = services[method]
                                case_clock = now()
                                child_start = time.clock_gettime(service.child_clock)
                                reaped_before = resource.getrusage(resource.RUSAGE_CHILDREN)
                                torch.cuda.reset_peak_memory_stats()
                                for step in range(masks):
                                    positions = [p for p, t in enumerate(canvas) if t is None]
                                    if not positions:
                                        break
                                    torch.cuda.synchronize()
                                    begin = now()
                                    with torch.inference_mode():
                                        result["new_forwards"] += 1
                                        logits = model(
                                            input_ids=torch.tensor(
                                                [
                                                    [
                                                        config["mask_token_id"] if t is None else t
                                                        for t in canvas
                                                    ]
                                                ],
                                                device="cuda",
                                            ),
                                            timesteps=torch.zeros(1, device="cuda"),
                                        )[0]
                                        scores = logits[positions].to(
                                            device="cpu", dtype=torch.float64
                                        )
                                        scores[:, config["mask_token_id"]] = -float("inf")
                                        head_values = scores.softmax(-1).numpy().copy()
                                    torch.cuda.synchronize()
                                    forward = elapsed(begin)
                                    path = args.output / "heads" / (name + f"-step{step}.npy")
                                    np.save(path, head_values, allow_pickle=False)
                                    case_path = path.with_suffix(".json")
                                    case_path.write_text(
                                        json.dumps(
                                            dict(
                                                canvas=list(canvas),
                                                positions=positions,
                                                mask_count=masks,
                                                probabilities_sha256=digest(path),
                                                forward_and_softmax=forward,
                                            )
                                        )
                                        + "\n"
                                    )
                                    begin = now()
                                    before = time.clock_gettime(service.child_clock)
                                    response = service.query(
                                        dict(
                                            case_path=str(case_path.resolve()),
                                            seed=seed + int(example["key"][:12], 16) + masks + step,
                                        )
                                    )
                                    cpu = time.clock_gettime(service.child_clock) - before
                                    rpc_wall = elapsed(begin)["wall"]
                                    record = dict(
                                        step=step,
                                        input_canvas=list(canvas),
                                        positions=positions,
                                        head_name=path.name,
                                        head_sha256=digest(path),
                                        forward=forward,
                                        service_wall=rpc_wall,
                                        service_cpu=cpu,
                                        response=response,
                                    )
                                    result["steps"].append(record)
                                    if response["status"] != "complete":
                                        result["status"] = response["status"]
                                        break
                                    word = response["sample"]
                                    if any(
                                        t is not None and word[p] != t for p, t in enumerate(canvas)
                                    ):
                                        raise RuntimeError(
                                            "actual sample changed fixed original IDs"
                                        )
                                    json.loads(
                                        adapter.detokenize_bytes(word).decode("utf8"),
                                        parse_constant=lambda _: (_ for _ in ()).throw(
                                            ValueError()
                                        ),
                                    )
                                    commits = response["committed"]
                                    if not commits or any(canvas[p] is not None for p in commits):
                                        raise RuntimeError(
                                            "commit changed fixed IDs or failed progress"
                                        )
                                    for p in commits:
                                        canvas[p] = word[p]
                                if all(t is not None for t in canvas):
                                    text = adapter.detokenize_bytes(canvas).decode("utf8")
                                    json.loads(
                                        text,
                                        parse_constant=lambda _: (_ for _ in ()).throw(
                                            ValueError()
                                        ),
                                    )
                                    delta = sum(
                                        (
                                            Fraction(r["response"]["certificate"]["delta"])
                                            for r in result["steps"]
                                        ),
                                        Fraction(),
                                    )
                                    if delta > Fraction(protocol["trajectory_total_tv"]):
                                        raise RuntimeError(
                                            "observed local certificate budget exceeded"
                                        )
                                    result.update(
                                        status="complete",
                                        output=text,
                                        original_token_ids=canvas,
                                        observed_local_certificate_sum=str(delta),
                                    )
                            except (
                                RuntimeError,
                                ValueError,
                                TimeoutError,
                                ProcessLookupError,
                                OSError,
                            ) as error:
                                result.update(
                                    status="error", reason=type(error).__name__ + ": " + str(error)
                                )
                            if method in services:
                                service = services[method]
                                result["measured_service_startup"] = service.measured_setup
                                try:
                                    child_total = (
                                        time.clock_gettime(service.child_clock) - child_start
                                    )
                                    result["child_cpu_source"] = "live Linux process CPU clock"
                                except OSError:
                                    service.close()
                                    services.pop(method)
                                    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
                                    child_total = (
                                        usage.ru_utime
                                        + usage.ru_stime
                                        - reaped_before.ru_utime
                                        - reaped_before.ru_stime
                                        - child_start
                                    )
                                    result["child_cpu_source"] = "reaped POSIX child usage"
                                cost = elapsed(case_clock)
                                result["actual_warm_total"] = dict(
                                    wall=cost["wall"], cpu=cost["cpu"] + child_total
                                )
                                result["parent_peak_rss_kib"] = resource.getrusage(
                                    resource.RUSAGE_SELF
                                ).ru_maxrss
                                result["gpu_peak_allocated_bytes"] = (
                                    torch.cuda.max_memory_allocated()
                                )
                            if result["status"] != "complete" and method in services:
                                services.pop(method).close()
                            result["service_setup"] = setup
                            if "actual_warm_total" in result:
                                result["reconstructed_cold_total"] = {
                                    u: result["actual_warm_total"][u]
                                    + result["measured_service_startup"][u]
                                    + model_setup[u]
                                    for u in ("wall", "cpu")
                                }
                            log.write(json.dumps(result) + "\n")
                            log.flush()
                            count += 1
                            print(
                                json.dumps(
                                    dict(
                                        records=count,
                                        case=example["key"][:8],
                                        masks=masks,
                                        method=method,
                                        seed=seed,
                                        status=result["status"],
                                        forwards=result["new_forwards"],
                                    )
                                ),
                                flush=True,
                            )
            print(
                json.dumps(dict(records=count, planned=protocol["planned_trajectories"])),
                flush=True,
            )
    finally:
        for service in services.values():
            service.close()


if __name__ == "__main__":
    main()
