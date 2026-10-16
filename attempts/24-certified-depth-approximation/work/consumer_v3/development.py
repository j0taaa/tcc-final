"""Frozen first315 V4 cost records; can prove NEGATIVE gate, never positive."""

import argparse
import gc
import hashlib
import json
import resource
import signal
import subprocess
from fractions import Fraction
from pathlib import Path
from time import perf_counter, process_time

import numpy as np
import torch

from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from ..consumer_v2.benchmark import alarm
from ..consumer_v2.block_stats import Partition
from ..consumer_v2.query import BoundaryWeights, FullSparseOutside
from ..consumer_v2.service import run_timed
from .development_audit import FIRST_METHODS, audit
from .development_methods import CPUQuery, SparseQuery
from .termination import CPUCache, surrogate_table, terminated_graph

WORK = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now():
    return perf_counter(), process_time()


def elapsed(start):
    return dict(wall=perf_counter() - start[0], cpu=process_time() - start[1])


def serializable(value):
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, dict):
        return {
            str(k): serializable(v) for k, v in value.items() if not isinstance(v, torch.Tensor)
        }
    if isinstance(value, (list, tuple)):
        return [serializable(v) for v in value]
    return value


def validate(result, canvas, table, gold, outside, method, protocol):
    word = tuple(result["tokens"].cpu().tolist())
    confidence = result["confidence"].cpu().numpy()
    selected = tuple(result["commit_mask"].nonzero().flatten().cpu().tolist())
    fixed_ok = all(t is None or word[p] == t for p, t in enumerate(canvas))
    k = word.index(50256)
    if not fixed_ok or any(t != 50256 for t in word[k + 1 :]):
        raise ValueError("sample changed fixed IDs or EOT/PAD phase")
    text = table.adapter.detokenize_bytes(word[:k]).decode("utf8")
    json.loads(text, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    values = {
        p: Fraction(outside.at(p, word[p]), gold.total) for p, t in enumerate(canvas) if t is None
    }
    exact_set = tuple(sorted(sorted(values, key=lambda p: (-values[p], p))[: min(4, len(values))]))
    error = max(abs(confidence[p] - float(v)) for p, v in values.items())
    tolerance = 0.005 if method.endswith("fp32") else 1e-8
    tolerance += float(result["confidence_delta"])
    correct = np.isfinite(confidence).all() and error <= tolerance
    if result["exact_common_ranking"]:
        correct = correct and selected == exact_set
        if result["draw_delta"] > Fraction(protocol["query_tv_budget"]):
            raise ValueError("draw exceeded its ORIGINAL structural budget")
        if gold.mass - result["draw_mass"] > result["draw_upper"]:
            raise ValueError("draw certificate failed against exact full mass")
        if 1 - result["draw_mass"] / gold.mass > result["draw_delta"]:
            raise ValueError("draw conditional TV failed against exact full mass")
    return dict(
        sample=word,
        text=text,
        selected=selected,
        correctness_gate=bool(correct),
        max_absolute_confidence_error=float(error),
        confidence_tolerance=tolerance,
        exact_rank_set_matches=selected == exact_set,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    subprocess.run(["git", "diff", "--quiet", "HEAD", "--"], check=True)
    protocol_path = WORK / "consumer-v4-development-protocol.json"
    protocol = json.loads(protocol_path.read_text())
    if len(protocol["candidate_family"]) + len(protocol["mandatory_controls"]) != 17:
        raise ValueError("premeasurement strengthened protocol required")
    args.output.mkdir(parents=True, exist_ok=False)
    signal.signal(signal.SIGALRM, alarm)
    torch.set_num_threads(1)
    torch.set_flush_denormal(False)
    torch.set_float32_matmul_precision("high")
    start = now()
    adapter = CompositionalByteLevelAdapter.from_token_pieces(
        json.loads((args.input / "vocabulary.json").read_text())
    )
    table = surrogate_table(adapter.emissions, 50256, 50256)
    partition = Partition(tuple(table.class_of), len(table.classes), 1024)
    torch.empty(1, device="cuda").add_(1)
    torch.cuda.synchronize()
    paths = sorted(p for p in args.input.glob("*.json") if p.with_suffix(".npy").exists())
    if len(paths) != 15:
        raise ValueError("ALL15 old states required")
    metadata = dict(
        scope=protocol["phase"],
        commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        protocol_sha256=digest(protocol_path),
        input_metadata_sha256=digest(args.input / "metadata.json"),
        vocabulary_sha256=digest(args.input / "vocabulary.json"),
        static_setup=elapsed(start),
        torch=torch.__version__,
        cuda=torch.version.cuda,
        gpu=torch.cuda.get_device_name(),
        source_sha256={p.name: digest(p) for p in sorted(Path(__file__).parent.glob("*.py"))},
        stage="FIRST315 necessary-condition negative-only audit; all765 needed for positive",
    )
    (args.output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n"
    )
    rows = []
    for rep in range(protocol["repetitions"]):
        order = FIRST_METHODS[rep:] + FIRST_METHODS[:rep]
        for path in paths:
            case = json.loads(path.read_text())
            if digest(path.with_suffix(".npy")) != case["probabilities_sha256"]:
                raise ValueError("old full head changed")
            head = np.load(path.with_suffix(".npy"), allow_pickle=False)
            canvas = (*case["canvas"], 50256)
            dense = np.zeros((len(canvas), table.adapter.vocabulary_size), dtype=np.float64)
            free = [p for p, t in enumerate(canvas) if t is None]
            dense[free] = head
            for p, t in enumerate(canvas):
                if t is not None:
                    dense[p, t] = 1
            probabilities = torch.from_numpy(dense).cuda()
            torch.cuda.synchronize()
            validation_start = now()
            limits = {
                key: protocol["resources"][key] for key in ("max_cells", "max_edges", "max_terms")
            }
            limits["timeout_seconds"] = protocol["resources"]["seconds_per_operation"]
            graph = terminated_graph(table, canvas, None, 50256, 50256, symbolic=True, **limits)
            gold_cache = CPUCache(graph, table, **limits)
            gold = gold_cache.reweight(BoundaryWeights(table, head, canvas, partition))
            outside = FullSparseOutside(gold)
            gold_cost = elapsed(validation_start)
            del graph
            for method in order:
                query = None
                row = dict(
                    case=path.stem,
                    repetition=rep,
                    method=method,
                    exact_validation_setup=gold_cost,
                    full_true_mass=str(gold.mass),
                )
                for phase in ("cold", "warm"):
                    if phase == "warm" and query is None:
                        row[phase] = dict(status="not_reached", correctness_gate=False)
                        continue
                    seed = protocol["seed"] + rep
                    torch.manual_seed(seed)
                    torch.cuda.synchronize()
                    torch.cuda.reset_peak_memory_stats()

                    def operation(
                        method_now=method,
                        canvas_now=canvas,
                        probabilities_now=probabilities,
                        seed_now=seed,
                    ):
                        nonlocal query
                        if query is None:
                            query = (
                                CPUQuery(method_now, table, partition, canvas_now, protocol)
                                if method_now.endswith("cpu")
                                else SparseQuery(method_now, table, canvas_now, protocol)
                            )
                        result = query.query(probabilities_now, seed_now)
                        torch.cuda.synchronize()
                        return result

                    operation_start = now()
                    response = run_timed(operation, protocol["resources"]["seconds_per_operation"])
                    del operation
                    timing = elapsed(operation_start)
                    peak = torch.cuda.max_memory_allocated()
                    item = serializable(response)
                    item.update(
                        measured=timing,
                        peak_cuda_allocated=peak,
                        projected={
                            key: timing[key] + case["forward_and_softmax"][key] for key in timing
                        },
                    )
                    if response["status"] == "complete":
                        validation_start = now()
                        try:
                            item.update(
                                validate(response, canvas, table, gold, outside, method, protocol)
                            )
                        except Exception as error:
                            item.update(correctness_gate=False, validation_error=str(error))
                        item["validation_cost_outside_timer"] = elapsed(validation_start)
                        if peak > protocol["resources"]["gpu_bytes"]:
                            item.update(
                                status="resource_refusal",
                                correctness_gate=False,
                                reason="observed GPU allocation budget",
                            )
                    else:
                        query = None
                        item["correctness_gate"] = False
                    row[phase] = item
                    del response
                if (
                    method.endswith("cpu")
                    and row["cold"]["status"] == row["warm"]["status"] == "complete"
                ):
                    same = row["cold"].get("sample") == row["warm"].get("sample") and row[
                        "cold"
                    ].get("selected") == row["warm"].get("selected")
                    row["cache_literal_match"] = same
                    row["warm"]["correctness_gate"] &= same
                rows.append(row)
                with (args.output / "rows.jsonl").open("a") as stream:
                    stream.write(json.dumps(row, sort_keys=True) + "\n")
                print(
                    json.dumps(
                        dict(
                            case=path.stem[:11],
                            rep=rep,
                            method=method,
                            cold=row["cold"]["status"],
                            warm=row["warm"]["status"],
                            correct=row["warm"].get("correctness_gate"),
                        )
                    ),
                    flush=True,
                )
                del query
                gc.collect()
                torch.cuda.empty_cache()
                if (
                    resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
                    > protocol["resources"]["cpu_rss_bytes"]
                ):
                    raise MemoryError(
                        "entire first-stage campaign invalid: observed CPU peak over budget"
                    )
            del outside, gold, gold_cache, probabilities
            gc.collect()
            torch.cuda.empty_cache()
    decision = audit(rows, [p.stem for p in paths], protocol)
    (args.output / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({k: v for k, v in decision.items() if k != "rejected_states"}), flush=True)


if __name__ == "__main__":
    main()
