"""Frozen development audit; numerical boundary, not whole neural generation."""

import argparse
import gzip
import hashlib
import json
import platform
import subprocess
from collections import Counter
from pathlib import Path
from random import Random
from time import perf_counter, process_time

import numpy as np
import torch
from scripts.exact_commit.mdlm_cpu import load_cpu_model

from mwpc_exact.cfg_posterior import CompilationLimit
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from .block_sampler import BlockPosterior, cuda_fetch, numpy_fetch
from .block_stats import Partition, numpy_stats
from .frozen.stack_control import StackPrepared
from .frozen.table import LexerTable
from .gpu_stats import DevicePartition, torch_stats, triton_stats

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def timed(operation):
    torch.cuda.synchronize()
    start, cpu = perf_counter(), process_time()
    result = operation()
    torch.cuda.synchronize()
    return result, dict(wall=perf_counter() - start, cpu=process_time() - cpu)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--weights-cache", type=Path, required=True)
    args = parser.parse_args()
    if subprocess.check_output(["git", "status", "--porcelain"]).strip():
        raise ValueError("freeze code/protocol before timings")
    if args.output.exists():
        raise FileExistsError(args.output)
    if args.weights_cache.exists():
        raise FileExistsError(args.weights_cache)
    protocol = json.loads((WORK / "protocol-v3.json").read_text())
    files = sorted(
        p for p in args.input.glob("*.json") if p.name not in ("metadata.json", "vocabulary.json")
    )
    if len(files) != 18:
        raise ValueError("all18 original development states required")
    torch.set_num_threads(protocol["threads"])
    torch.set_flush_denormal(False)
    torch.manual_seed(protocol["seed"])
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    config = json.loads((ROOT / protocol["model_config"]).read_text())

    def load():
        model, hashes, adapted = load_cpu_model(config, ROOT / ".cache/mdlm")
        model.to("cuda:0")
        for parameter in model.parameters():
            parameter.requires_grad_(False)
        with torch.inference_mode():
            model(
                input_ids=torch.full((1, 32), config["mask_token_id"], device="cuda:0"),
                timesteps=torch.zeros(1, device="cuda:0"),
            )
        return model, hashes, adapted

    (model, hashes, adapted), model_setup = timed(load)
    forward_count = 1

    def head(case):
        nonlocal forward_count
        ids = [config["mask_token_id"] if t is None else t for t in case["canvas"]]
        with torch.inference_mode():
            logits = model(
                input_ids=torch.tensor([ids], device="cuda:0"),
                timesteps=torch.zeros(1, device="cuda:0"),
            )[0]
            scores = logits[case["positions"]].to(torch.float64)
            scores[:, config["mask_token_id"]] = float("-inf")
            q = torch.softmax(scores, dim=-1)
        forward_count += 1
        return q

    adapter, adapter_setup = timed(
        lambda: CompositionalByteLevelAdapter.from_token_pieces(
            json.loads((args.input / "vocabulary.json").read_text())
        )
    )
    table, setup = timed(lambda: LexerTable(adapter))
    partitions, mappings, partition_costs = {}, {}, {}
    for size in protocol["blocks"]:
        partitions[size], cpu_cost = timed(
            lambda size=size: Partition(table.class_of, len(table.classes), size)
        )
        mappings[size], gpu_cost = timed(
            lambda size=size: DevicePartition(partitions[size], "cuda:0")
        )
        partition_costs[size] = dict(cpu=cpu_cost, gpu_upload=gpu_cost)
    args.output.mkdir(parents=True)
    args.weights_cache.mkdir(parents=True)
    metadata = dict(
        producer_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        protocol_sha256=sha(WORK / "protocol-v3.json"),
        protocol=protocol,
        python=platform.python_version(),
        numpy=np.__version__,
        torch=torch.__version__,
        cuda=torch.version.cuda,
        device=torch.cuda.get_device_name(0),
        vocabulary_sha256=sha(args.input / "vocabulary.json"),
        grammar_table_setup=setup,
        vocabulary_adapter_setup=adapter_setup,
        partition_setup=partition_costs,
        frame_inventory={
            p.name: dict(json_sha256=sha(p), weights_sha256=sha(p.with_suffix(".npy")))
            for p in files
        },
        probability_cache=str(args.weights_cache),
        model_config=config,
        model_hashes=hashes,
        adapted_model_sha256=adapted,
        model_setup=model_setup,
        new_neural_forwards=forward_count,
        scope="New CUDA head, paired step cost; not a whole trajectory",
    )
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    configs = [(method, size) for method in protocol["methods"] for size in protocol["blocks"]]
    counts, records = Counter(), 0
    with gzip.open(args.output / "rows.jsonl.gz", "xt") as log:

        def record(row):
            nonlocal records
            log.write(json.dumps(row) + "\n")
            log.flush()
            counts[row["status"]] += 1
            records += 1

        for file in files:
            case = json.loads(file.read_text())
            if sha(file.with_suffix(".npy")) != case["probabilities_sha256"]:
                raise ValueError("archived weights hash changed")
            if case["positions"] != [p for p, t in enumerate(case["canvas"]) if t is None]:
                raise ValueError("free positions changed from archived frame")
            name, original = file.stem, case["canvas"]
            prepare_start, prepare_cpu = perf_counter(), process_time()
            try:
                plan = StackPrepared(
                    table,
                    original,
                    **{
                        k: protocol[k]
                        for k in ("max_cells", "max_edges", "max_terms", "timeout_seconds")
                    },
                )
            except (CompilationLimit, TimeoutError) as e:
                cost = dict(wall=perf_counter() - prepare_start, cpu=process_time() - prepare_cpu)
                for repeat in range(protocol["repetitions"]):
                    for method, size in configs:
                        record(
                            dict(
                                case=name,
                                repeat=repeat,
                                method=method,
                                block_size=size,
                                status="shared_preparation_refused",
                                reason=str(e),
                                preparation=cost,
                            )
                        )
                print(
                    json.dumps(
                        dict(case=name, records=records, status="shared_preparation_refused")
                    ),
                    flush=True,
                )
                continue
            preparation = dict(
                wall=perf_counter() - prepare_start, cpu=process_time() - prepare_cpu
            )
            paired_tokens, first_calls = {}, {}

            def run(method, size, seed, q, plan=plan, original=original):
                torch.cuda.synchronize()
                start, cpu = perf_counter(), process_time()
                if method == "numpy":
                    host = q.cpu().numpy()  # Required new full transfer; NOT cached archive matrix.
                    stats = numpy_stats(host, partitions[size])
                    fetch = numpy_fetch(host, partitions[size])
                else:
                    stats = (triton_stats if method == "triton" else torch_stats)(q, mappings[size])
                    fetch = cuda_fetch(q, mappings[size])
                torch.cuda.synchronize()
                boundary = dict(wall=perf_counter() - start, cpu=process_time() - cpu)
                posterior = BlockPosterior(plan, stats, fetch)
                tokens = posterior.sample(Random(seed))
                rendered = adapter.detokenize_bytes(tokens).decode("utf8")
                json.loads(rendered)
                if any(t is not None and tokens[p] != t for p, t in enumerate(original)):
                    raise RuntimeError("fixed original token changed")
                torch.cuda.synchronize()
                return (stats, posterior.mass, tokens, rendered, boundary), dict(
                    wall=perf_counter() - start, cpu=process_time() - cpu
                )

            q, first_head = timed(lambda case=case: head(case))
            for method, size in configs:
                try:
                    _, first_calls[method + str(size)] = run(method, size, protocol["seed"], q)
                except Exception as e:
                    first_calls[method + str(size)] = dict(error=repr(e))
            (args.output / (name + "-first-calls.json")).write_text(
                json.dumps(first_calls, indent=2) + "\n"
            )
            for repeat in range(protocol["repetitions"]):
                q, head_cost = timed(lambda case=case: head(case))
                expected_mass = None
                order = configs[repeat:] + configs[:repeat]
                for method, size in order:
                    if "error" in first_calls[method + str(size)]:
                        record(
                            dict(
                                case=name,
                                repeat=repeat,
                                method=method,
                                block_size=size,
                                status="warmup_error",
                                reason=first_calls[method + str(size)]["error"],
                            )
                        )
                        continue
                    torch.cuda.reset_peak_memory_stats()
                    before = torch.cuda.memory_allocated()
                    try:
                        (stats, mass, tokens, rendered, boundary), cost = run(
                            method, size, protocol["seed"] + repeat, q
                        )
                        if expected_mass is None:
                            expected_mass = mass
                        if mass != expected_mass:
                            raise RuntimeError("exact joint mass differs")
                        # Block layouts change RNG ticket traversal, so only equal
                        # layout configurations must have identical paired IDs.
                        key = (repeat, size)
                        if key in paired_tokens and paired_tokens[key] != tokens:
                            raise RuntimeError("same-layout original IDs differ")
                        paired_tokens[key] = tokens
                        first = {
                            metric: preparation[metric] + cost[metric] for metric in ("wall", "cpu")
                        }
                        total_step = {
                            metric: first[metric] + head_cost[metric] for metric in ("wall", "cpu")
                        }
                        static = {
                            metric: adapter_setup[metric]
                            + setup[metric]
                            + partition_costs[size]["cpu"][metric]
                            + (
                                0
                                if method == "numpy"
                                else partition_costs[size]["gpu_upload"][metric]
                            )
                            for metric in ("wall", "cpu")
                        }
                        session_cold = {
                            metric: static[metric]
                            + preparation[metric]
                            + first_calls[method + str(size)][metric]
                            + first_head[metric]
                            + model_setup[metric]
                            for metric in ("wall", "cpu")
                        }
                        record(
                            dict(
                                case=name,
                                repeat=repeat,
                                method=method,
                                block_size=size,
                                status="complete",
                                valid_mass=str(mass),
                                tokens=tokens,
                                output_utf8=rendered,
                                query=cost,
                                boundary=boundary,
                                preparation=preparation,
                                first_sample=first,
                                new_forward_and_gpu_softmax=head_cost,
                                total_step=total_step,
                                session_cold=session_cold,
                                additional_cuda_peak_bytes=torch.cuda.max_memory_allocated()
                                - before,
                                digit_words=stats.digit_words,
                                blocks=len(stats.partition.blocks),
                            )
                        )
                    except Exception as e:
                        record(
                            dict(
                                case=name,
                                repeat=repeat,
                                method=method,
                                block_size=size,
                                status="error",
                                reason=repr(e),
                            )
                        )
                # Audit/cache outside timed queries, never given to CPU baseline.
                matrix = q.cpu().numpy()
                head_sha = hashlib.sha256(matrix.tobytes()).hexdigest()
                cache_file = args.weights_cache / (name + f"-head{repeat}.npy")
                np.save(cache_file, matrix, allow_pickle=False)
                (args.output / (name + f"-head{repeat}.json")).write_text(
                    json.dumps(
                        dict(
                            weights_raw_sha256=head_sha,
                            weights_npy_sha256=sha(cache_file),
                            probability_cache_file=cache_file.name,
                            shape=list(q.shape),
                            forward_and_gpu_softmax=head_cost,
                            dtype="binary64",
                            policy="Full-V excluding MASK; exact row normalization by sampler",
                        ),
                        indent=2,
                    )
                    + "\n"
                )
            metadata["new_neural_forwards"] = forward_count
            (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
            print(
                json.dumps(
                    dict(
                        case=name, records=records, new_forwards=forward_count, status_counts=counts
                    )
                ),
                flush=True,
            )
    (args.output / "summary.json").write_text(
        json.dumps(
            dict(
                records=records,
                expected=18 * len(configs) * protocol["repetitions"],
                status_counts=counts,
                complete=records == 18 * len(configs) * protocol["repetitions"],
            ),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
