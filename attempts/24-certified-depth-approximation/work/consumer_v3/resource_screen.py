"""Frozen ALL-old-state resource screen. No fresh heads or timing victory."""

import argparse
import gc
import hashlib
import json
import logging
import signal
import subprocess
import traceback
from fractions import Fraction
from pathlib import Path
from time import perf_counter, process_time

import numpy as np

from mwpc_exact.cfg_posterior import CompilationLimit
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from ..certificate import CounterTable, conditional_error
from ..consumer_v2.block_stats import Partition
from ..consumer_v2.query import BoundaryWeights, ConfidenceCursor
from .mosaic_control import fixed_logits, load, materialize, minimize
from .termination import posterior, surrogate_table, terminated_graph

WORK = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now():
    return perf_counter(), process_time()


def elapsed(start):
    return dict(wall=perf_counter() - start[0], cpu=process_time() - start[1])


class Warnings(logging.Handler):
    def __init__(self):
        super().__init__(logging.WARNING)
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


def alarm(signum, frame):
    raise TimeoutError("known-data per-depth resource deadline")


def native_query(graph, table, post, rows, canvas, module, protocol, kind, mode):
    import torch

    start, stages = now(), {}
    dtype = torch.float64 if mode == "fp64" else torch.float32
    n, length, vocab = graph["num_nodes"], len(canvas), table.adapter.vocabulary_size
    padded = 1 << (length - 1).bit_length()
    estimate = 10 * padded * n * n * torch.empty((), dtype=dtype).element_size()
    estimate += 8 * length * vocab * torch.empty((), dtype=dtype).element_size()
    estimate += 24 * len(graph["edges"]) * vocab
    if estimate > protocol["resources"]["estimated_query_guard_bytes"]:
        return dict(
            status="allocation_guard",
            estimated_query_bytes=estimate,
            measured_oom=False,
            complete_diagnostic=elapsed(start),
        )
    sampler = logits = word = confidence = None
    torch.cuda.reset_peak_memory_stats()
    warnings = Warnings()
    logging.getLogger().addHandler(warnings)
    try:
        stage = now()
        sampler, stats = materialize(
            graph,
            module,
            kind=kind,
            device="cuda",
            dtype=dtype,
            max_bytes=protocol["resources"]["constructor_guard_bytes"],
        )
        if kind == "parallel":
            sampler.matmul_dtype = torch.float64 if mode in ("fp64", "fp32_product64") else None
        torch.cuda.synchronize()
        stages["native_materialize"] = elapsed(stage)
        stage = now()
        logits = torch.from_numpy(rows).log().to(device="cuda", dtype=dtype)[None]
        logits = fixed_logits(logits, canvas)
        forced = torch.tensor([-1 if t is None else t for t in canvas], device="cuda")
        torch.cuda.synchronize()
        stages["logits_transfer_and_fixed_rows"] = elapsed(stage)
        stage = now()
        torch.manual_seed(protocol["seed"])
        word, confidence = sampler.sample(logits, forced, return_marginal=True)
        torch.cuda.synchronize()
        stages["native_sample_and_confidence"] = elapsed(stage)
        stage = now()
        tokens = tuple(word[0].cpu().tolist())
        values = confidence[0].cpu().tolist()
        if any(t is not None and tokens[p] != t for p, t in enumerate(canvas)):
            raise AssertionError("native sample changed a fixed original ID")
        eot, pad = graph["eot_id"], graph["pad_id"]
        k = tokens.index(eot)
        if any(t != pad for t in tokens[k + 1 :]):
            raise AssertionError("native sample has ordinary content after EOT")
        text = table.adapter.detokenize_bytes(tokens[:k]).decode("utf8")
        json.loads(text, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        cursor, errors = ConfidenceCursor(post), []
        for p in post.weights.free:
            exact = Fraction(cursor.at(p, tokens[p]), post.total)
            errors.append(abs(values[p] - float(exact)))
        error = max(errors, default=0)
        tolerance = 1e-8 if mode == "fp64" else 0.005
        correct = np.isfinite(values).all() and error <= tolerance and not warnings.messages
        stages["transfer_json_and_integer_confidence_check"] = elapsed(stage)
        return dict(
            status="complete",
            correctness_gate=bool(correct),
            max_absolute_confidence_error=error,
            absolute_tolerance=tolerance,
            sample=tokens,
            text=text,
            warnings=warnings.messages,
            stages=stages,
            **stats,
            estimated_query_bytes=estimate,
            peak_cuda_allocated=torch.cuda.max_memory_allocated(),
            complete_diagnostic=elapsed(start),
        )
    finally:
        logging.getLogger().removeHandler(warnings)
        del sampler, logits, word, confidence
        gc.collect()
        torch.cuda.empty_cache()


def run(args):
    import torch

    protocol_path = WORK / "consumer-v3-resource-protocol.json"
    protocol = json.loads(protocol_path.read_text())
    subprocess.run(["git", "diff", "--quiet", "HEAD", "--"], check=True)
    args.output.mkdir(parents=True, exist_ok=False)
    module, origin = load(args.source)
    torch.set_num_threads(1)
    torch.set_float32_matmul_precision(protocol["torch_float32_matmul_precision"])
    signal.signal(signal.SIGALRM, alarm)
    start = now()
    vocabulary_path = args.input / "vocabulary.json"
    emissions = CompositionalByteLevelAdapter.from_token_pieces(
        json.loads(vocabulary_path.read_text())
    ).emissions
    table = surrogate_table(emissions, 50256, 50256)
    partition = Partition(tuple(table.class_of), len(table.classes), 1024)
    counter = CounterTable(table)
    setup = elapsed(start)
    paths = sorted(p for p in args.input.glob("*.json") if p.with_suffix(".npy").exists())
    if len(paths) != 15:
        raise ValueError("resource protocol requires ALL15 old states")
    metadata = dict(
        scope=protocol["phase"],
        protocol_sha256=digest(protocol_path),
        mosaic=origin,
        input_metadata_sha256=digest(args.input / "metadata.json"),
        vocabulary_sha256=digest(vocabulary_path),
        static_setup_diagnostic=setup,
        source_sha256={p.name: digest(p) for p in sorted(Path(__file__).parent.glob("*.py"))},
        commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        torch=torch.__version__,
        cuda=torch.version.cuda,
        gpu=torch.cuda.get_device_name(),
    )
    (args.output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n"
    )
    rows_out, plausible = [], set()
    for path in paths:
        case = json.loads(path.read_text())
        if digest(path.with_suffix(".npy")) != case["probabilities_sha256"]:
            raise ValueError("old full original head changed")
        canvas = (*case["canvas"], 50256)
        head = np.load(path.with_suffix(".npy"), allow_pickle=False)
        numeric_start = now()
        weights = BoundaryWeights(table, head, canvas, partition)
        numeric = elapsed(numeric_start)
        dense = np.ones((len(canvas), table.adapter.vocabulary_size), dtype=np.float64)
        for p, row in zip(weights.free, head, strict=True):
            dense[p] = row
        for depth in protocol["depths"]:
            row = dict(case=path.stem, depth=depth, numeric_diagnostic=numeric)
            started = now()
            try:
                signal.setitimer(signal.ITIMER_REAL, protocol["resources"]["seconds_per_depth"])
                limits = {
                    k: protocol["resources"][k] for k in ("max_cells", "max_edges", "max_terms")
                }
                limits["timeout_seconds"] = protocol["resources"]["seconds_per_depth"]
                stage = now()
                graph = terminated_graph(
                    table, canvas, depth, 50256, 50256, symbolic=True, **limits
                )
                row["raw_graph"] = dict(nodes=graph["num_nodes"], edges=len(graph["edges"]))
                graph = minimize(graph, table)
                row["minimized_graph"] = dict(nodes=graph["num_nodes"], edges=len(graph["edges"]))
                row["graph_diagnostic"] = elapsed(stage)
                stage = now()
                post = posterior(graph, table, weights, **limits)
                row["true_mass"] = str(post.mass)
                upper = (
                    counter.tail(weights, depth, sums=weights.sums)[0]
                    if depth is not None
                    else Fraction()
                )
                delta = conditional_error(post.mass, upper) if post.total else None
                row.update(upper_tail=str(upper), delta=None if delta is None else str(delta))
                row["integer_inside_and_certificate_diagnostic"] = elapsed(stage)
                row["native"] = []
                if post.total:
                    for specification in protocol["native_controls"]:
                        kind, mode = specification.split("/")
                        try:
                            result = native_query(
                                graph, table, post, dense, canvas, module, protocol, kind, mode
                            )
                        except (MemoryError, RuntimeError, AssertionError, ValueError) as error:
                            result = dict(
                                status="error", error=str(error), traceback=traceback.format_exc()
                            )
                            gc.collect()
                            torch.cuda.empty_cache()
                        row["native"].append(dict(method=specification, **result))
                    if (
                        depth is not None
                        and delta is not None
                        and delta <= Fraction(1, 1000)
                        and any(r.get("correctness_gate") for r in row["native"])
                    ):
                        plausible.add(path.stem)
                row["status"] = "complete" if post.total else "zero_true_mass"
            except (TimeoutError, CompilationLimit, MemoryError) as error:
                row.update(status="resource_refusal", reason=str(error))
            except Exception as error:
                row.update(status="error", reason=str(error), traceback=traceback.format_exc())
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
            row["depth_complete_diagnostic"] = elapsed(started)
            rows_out.append(row)
            with (args.output / "rows.jsonl").open("a") as stream:
                stream.write(json.dumps(row, sort_keys=True) + "\n")
            print(
                json.dumps(
                    dict(
                        case=path.stem[:11],
                        depth=depth,
                        status=row["status"],
                        graph=row.get("minimized_graph"),
                        delta=row.get("delta"),
                    )
                ),
                flush=True,
            )
    decision = dict(
        scope=protocol["phase"],
        rows=len(rows_out),
        expected_rows=45,
        all_rows_present=len(rows_out) == 45,
        plausible_states=sorted(plausible),
        resource_plausibility_gate=len(plausible) >= 3,
        new_model_forwards=0,
        timing_victory_claim=False,
        user_scientific_goal_met=False,
    )
    (args.output / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(decision), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
