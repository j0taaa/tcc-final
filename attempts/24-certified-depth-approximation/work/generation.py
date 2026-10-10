"""Opt-in iterative MDLM application; neural forwards and solver budgets separate."""

import argparse
import hashlib
import json
import os
import platform
import selectors
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
from time import perf_counter, process_time

from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clock():
    return perf_counter(), process_time()


def elapsed(start):
    return dict(wall=perf_counter() - start[0], cpu=process_time() - start[1])


class Service:
    def __init__(self, method, vocabulary, error_log):
        self.errors = error_log.open("w")
        self.process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "attempts.24-certified-depth-approximation.work.generation_service",
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
            self.ready = self.read()
            if self.ready["status"] != "ready":
                raise RuntimeError("CPU service did not prepare")
        except Exception:
            self.close()
            raise

    def read(self):
        if not self.selector.select(timeout=150):
            raise TimeoutError("CPU service supervisor; no success inferred")
        line = self.process.stdout.readline()
        if not line:
            raise RuntimeError("CPU service exited; inspect retained stderr")
        return json.loads(line)

    def query(self, request):
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        return self.read()

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        self.selector.close()
        self.process.stdin.close()
        self.process.stdout.close()
        self.errors.close()


def main():
    import numpy as np
    import torch
    from scripts.exact_commit.mdlm_cpu import load_cpu_model

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--independent-decision", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise ValueError("freeze source/protocol before NEW trajectory forwards")
    decision = json.loads(args.independent_decision.read_text())
    if (
        not decision["campaign_complete"]
        or not decision["practical_gate"]
        or decision["selected"] != "handoff"
    ):
        raise ValueError("finish the selected independent query gate before this demonstration")
    args.output.mkdir(parents=True, exist_ok=False)
    protocol = json.loads((WORK / "generation-protocol.json").read_text())
    capture = json.loads((args.capture / "metadata.json").read_text())
    config = capture["config"]
    if capture["phase"] != "independent" or len(capture["selected"]) != 5:
        raise ValueError("all five pre-pinned external documents required")
    torch.set_num_threads(config["torch_cpu_threads"])
    torch.set_flush_denormal(False)
    torch.manual_seed(protocol["seed"])
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    start = clock()
    model, hashes, adapted = load_cpu_model(config, ROOT / ".cache/mdlm")
    if hashes != capture["model_hashes"] or adapted != capture["adapted_model_sha256"]:
        raise ValueError("pinned real model source/checkpoint changed")
    model.to("cuda")
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    with torch.inference_mode():
        model(
            input_ids=torch.full((1, 32), config["mask_token_id"], device="cuda"),
            timesteps=torch.zeros(1, device="cuda"),
        )
    torch.cuda.synchronize()
    loading = elapsed(start)
    vocabulary = args.capture / "vocabulary.json"
    if digest(vocabulary) != capture["vocabulary_sha256"]:
        raise ValueError("full original tokenizer changed")
    adapter = CompositionalByteLevelAdapter.from_token_pieces(json.loads(vocabulary.read_text()))
    (args.output / "metadata.json").write_text(
        json.dumps(
            dict(
                protocol=protocol,
                input_capture=capture,
                independent_decision_sha256=digest(args.independent_decision),
                producer_commit=subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True
                ).strip(),
                source_sha256={p.name: digest(p) for p in WORK.glob("*.py")},
                model_loading_and_warmup=loading,
                model_hashes=hashes,
                adapted_model_sha256=adapted,
                torch=torch.__version__,
                cuda=torch.version.cuda,
                python=platform.python_version(),
                gpu=torch.cuda.get_device_name(),
                model_parameters_updated=False,
                distribution_reference=(
                    "decoder of full frozen-product posteriors, NOT native conditioned MDLM"
                ),
            ),
            indent=2,
        )
        + "\n"
    )
    (args.output / "heads").mkdir()
    with (args.output / "rows.jsonl").open("w") as log:
        for method in protocol["methods"]:
            service = None
            try:
                for example in capture["selected"]:
                    for masks in (4, 8, 16):
                        name = f"{example['key']}-{masks}-{method}"
                        initial = json.loads(
                            (args.capture / (f"{example['key']}-{masks}.json")).read_text()
                        )
                        canvas = list(initial["canvas"])
                        result = dict(
                            case=example["key"],
                            masks=masks,
                            method=method,
                            steps=[],
                            status="started",
                            forward_attempts=0,
                        )
                        case_clock = clock()
                        try:
                            if service is None:
                                begin = clock()
                                service = Service(
                                    method, vocabulary, args.output / (name + ".stderr.log")
                                )
                                result["service_spawn_to_ready"] = elapsed(begin)
                                result["decoder_startup"] = service.ready["decoder_startup"]
                            for step in range(masks):
                                positions = [p for p, t in enumerate(canvas) if t is None]
                                if not positions:
                                    break
                                ids = [config["mask_token_id"] if t is None else t for t in canvas]
                                torch.cuda.synchronize()
                                begin = clock()
                                with torch.inference_mode():
                                    result["forward_attempts"] += 1
                                    logits = model(
                                        input_ids=torch.tensor([ids], device="cuda"),
                                        timesteps=torch.zeros(1, device="cuda"),
                                    )[0]
                                    scores = logits[positions].to(device="cpu", dtype=torch.float64)
                                    scores[:, config["mask_token_id"]] = -float("inf")
                                    probabilities = scores.softmax(-1).numpy().copy()
                                torch.cuda.synchronize()
                                forward = elapsed(begin)
                                head = args.output / "heads" / (name + f"-step{step}.npy")
                                np.save(head, probabilities, allow_pickle=False)
                                request = dict(
                                    probabilities=str(head.resolve()),
                                    probabilities_sha256=digest(head),
                                    canvas=list(canvas),
                                    positions=positions,
                                    initial_masks=masks,
                                    seed=protocol["seed"]
                                    + int(example["key"][:12], 16)
                                    + masks
                                    + step,
                                )
                                record = dict(
                                    step=step,
                                    input_canvas=list(canvas),
                                    positions=positions,
                                    forward_and_softmax=forward,
                                    probability_sha256=request["probabilities_sha256"],
                                    response=dict(status="request_started"),
                                )
                                result["steps"].append(record)
                                begin = clock()
                                try:
                                    response = service.query(request)
                                finally:
                                    record["service_wall"] = perf_counter() - begin[0]
                                record["response"] = response
                                if response["status"] != "complete":
                                    result["status"] = response["status"]
                                    break
                                sample = response["sample"]
                                if any(
                                    t is not None and sample[p] != t for p, t in enumerate(canvas)
                                ):
                                    raise RuntimeError("solver changed fixed original IDs")
                                json.loads(
                                    adapter.detokenize_bytes(sample).decode("utf8"),
                                    parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)),
                                )
                                if not response["committed"] or any(
                                    canvas[p] is not None for p in response["committed"]
                                ):
                                    raise RuntimeError(
                                        "commit lacks progress or rewrites fixed position"
                                    )
                                for p in response["committed"]:
                                    canvas[p] = sample[p]
                            if all(t is not None for t in canvas):
                                text = adapter.detokenize_bytes(canvas).decode("utf8")
                                json.loads(
                                    text,
                                    parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)),
                                )
                                result.update(
                                    status="complete",
                                    output=text,
                                    original_token_ids=canvas,
                                    exact_fixed_ids_preserved=True,
                                    observed_sum_of_local_tv_bounds=str(
                                        sum(
                                            (
                                                Fraction(
                                                    r["response"]["sample_certificate"]["delta"]
                                                )
                                                for r in result["steps"]
                                            ),
                                            Fraction(),
                                        )
                                    ),
                                )
                                if Fraction(result["observed_sum_of_local_tv_bounds"]) > Fraction(
                                    protocol["trajectory_total_tv"]
                                ):
                                    raise RuntimeError("trajectory TV budget exceeded")
                        except TimeoutError as error:
                            result.update(status="resource_refusal", error=str(error))
                            if service is not None:
                                service.close()
                                service = None
                        except (RuntimeError, ValueError) as error:
                            result.update(status="worker_error", error=str(error))
                            if service is not None:
                                service.close()
                                service = None
                        result["actual_case_wall"] = perf_counter() - case_clock[0]
                        result["new_model_forwards"] = result["forward_attempts"]
                        result["complete_neural_heads"] = len(result["steps"])
                        log.write(json.dumps(result) + "\n")
                        log.flush()
                        print(
                            json.dumps(
                                dict(
                                    case=example["key"][:8],
                                    masks=masks,
                                    method=method,
                                    status=result["status"],
                                    forwards=result["new_model_forwards"],
                                    wall=result["actual_case_wall"],
                                )
                            ),
                            flush=True,
                        )
            finally:
                if service is not None:
                    service.close()


if __name__ == "__main__":
    main()
