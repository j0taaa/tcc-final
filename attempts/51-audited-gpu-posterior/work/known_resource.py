"""ALL15 old real heads: functional/resource screen, no positive timing claim."""

import argparse
import gc
import hashlib
import json
import signal
import subprocess
from fractions import Fraction as F
from pathlib import Path
from random import Random

import numpy as np
import torch

from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from .exact_control import ExactDAG
from .frozen_compiler import load
from .interval_sampler import IntervalSampler


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def timeout(_signum, _frame):
    raise TimeoutError("declared known-head resource screen deadline")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    subprocess.run(["git", "diff", "--quiet", "HEAD", "--"], check=True)
    work = Path(__file__).parent
    protocol = json.loads((work / "known-resource-protocol-v5.json").read_text())
    args.output.mkdir(parents=True, exist_ok=False)
    paths = sorted(p for p in args.input.glob("*.json") if p.with_suffix(".npy").exists())
    if len(paths) != 15:
        raise ValueError("ALL15 old cases required")
    frozen = load()
    term, query, blocks = frozen["termination"], frozen["query"], frozen["blocks"]
    adapter = CompositionalByteLevelAdapter.from_token_pieces(
        json.loads((args.input / "vocabulary.json").read_text())
    )
    table = term.surrogate_table(adapter.emissions, 50256, 50256)
    partition = blocks.Partition(tuple(table.class_of), len(table.classes), protocol["block_size"])
    limits = {key: protocol[key] for key in ("max_cells", "max_edges", "max_terms")}
    limits["timeout_seconds"] = protocol["seconds_per_case"]
    signal.signal(signal.SIGALRM, timeout)
    torch.set_num_threads(1)
    torch.set_flush_denormal(False)
    generator = np.random.default_rng(protocol["seed"])
    metadata = dict(
        commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        protocol_sha256=digest(work / "known-resource-protocol-v5.json"),
        input_metadata_sha256=digest(args.input / "metadata.json"),
        vocabulary_sha256=digest(args.input / "vocabulary.json"),
        compiler_producer=frozen["producer"],
        compiler_archive_sha256=frozen["archive_sha256"],
        torch=torch.__version__,
        cuda=torch.version.cuda,
        gpu=torch.cuda.get_device_name(),
        new_model_forwards=0,
        speed_claim=False,
    )
    (args.output / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n"
    )

    def run_case(index, path):
        row = dict(case=path.stem, status="ERROR", new_model_forwards=0)
        signal.alarm(protocol["seconds_per_case"])
        try:
            case = json.loads(path.read_text())
            if digest(path.with_suffix(".npy")) != case["probabilities_sha256"]:
                raise ValueError("old real binary64 head changed")
            head = np.load(path.with_suffix(".npy"), allow_pickle=False)
            canvas = (*case["canvas"], 50256)
            free = [p for p, t in enumerate(canvas) if t is None]
            dense = np.zeros((len(canvas), table.adapter.vocabulary_size), dtype=np.float64)
            dense[free] = head
            for p, t in enumerate(canvas):
                if t is not None:
                    dense[p, t] = 1
            graph = term.terminated_graph(
                table, canvas, None, 50256, 50256, symbolic=True, **limits
            )
            prepared = term.prepare_graph(graph, table, canvas, **limits)
            layers = tuple(
                tuple(
                    tuple(
                        (
                            dst,
                            tuple(
                                sorted({c for g in gids for c in prepared.table.local_to_class[g]})
                            ),
                        )
                        for dst, gids in outgoing
                    )
                    for outgoing in layer
                )
                for layer in prepared.arcs
            )
            control = IntervalSampler(
                table.classes, layers, prepared.accepting, block_size=protocol["block_size"]
            )
            source = generator.integers(
                0,
                1 << protocol["uniform_prefix_bits"],
                (protocol["samples_per_case"], len(canvas), 3),
                dtype=np.int64,
            )
            result = control.sample(
                torch.from_numpy(dense).cuda(),
                torch.from_numpy(source).cuda(),
                [Random(protocol["seed"] + index * 100 + i) for i in range(len(source))],
                bits=protocol["uniform_prefix_bits"],
            )
            samples = [tuple(w) for w in result["tokens"].cpu().tolist()]
            exact = result["exact_fallback"] or ExactDAG(
                control.engine.classes, control.engine.layers, control.engine.accepting, dense
            )
            weights = query.BoundaryWeights(table, head, canvas, partition)
            gold = term.CPUCache(graph, table, **limits).reweight(weights)
            denominator = F(1)
            for class_row in exact.class_weights:
                denominator *= sum(class_row, F())
            raw_mass = exact.beta[0][0]
            if (
                raw_mass / denominator != gold.mass
                or not result["mass_lower"] <= raw_mass <= result["mass_upper"]
            ):
                raise AssertionError("independent exact terminated mass or enclosure mismatch")
            for i, word in enumerate(samples):
                expected = exact.sample(
                    source[i].tolist(),
                    protocol["uniform_prefix_bits"],
                    Random(protocol["seed"] + index * 100 + i),
                )
                if word != expected or any(
                    t is not None and word[p] != t for p, t in enumerate(canvas)
                ):
                    raise AssertionError("full original ID replay/fixed canvas mismatch")
                k = word.index(50256)
                if any(t != 50256 for t in word[k + 1 :]):
                    raise AssertionError("bad native EOT/PAD suffix")
                text = adapter.detokenize_bytes(word[:k]).decode("utf8")
                json.loads(text, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
            row.update(
                status="COMPLETE",
                samples=samples,
                gpu_certified=result["gpu_certified"],
                exact_fallbacks=result["fallback_count"],
                literal_word_matches=len(samples),
                mass_checks=2,
                relative_enclosure_gap=str(
                    (result["mass_upper"] - result["mass_lower"]) / result["mass_upper"]
                ),
                graph_nodes=sum(map(len, layers)),
                classes=len(control.engine.classes),
            )
        except (TimeoutError, MemoryError, torch.cuda.OutOfMemoryError) as error:
            row.update(
                status="RESOURCE_REFUSAL", exception_type=type(error).__name__, exception=str(error)
            )
        except ValueError as error:
            row.update(
                status="ZERO_MASS"
                if "zero exact target mass" in str(error)
                else "RESOURCE_REFUSAL"
                if "guard" in str(error)
                else "ERROR",
                exception_type=type(error).__name__,
                exception=str(error),
            )
        except Exception as error:
            row.update(status="ERROR", exception_type=type(error).__name__, exception=str(error))
        finally:
            signal.alarm(0)
        return row

    rows = []
    for index, path in enumerate(paths):
        row = run_case(index, path)
        with (args.output / "rows.jsonl").open("a") as stream:
            stream.write(json.dumps(row, sort_keys=True) + "\n")
        rows.append(row)
        print(json.dumps({k: v for k, v in row.items() if k != "samples"}), flush=True)
        gc.collect()
        torch.cuda.empty_cache()
    summary = dict(
        records=len(rows),
        complete=sum(r["status"] == "COMPLETE" for r in rows),
        errors=sum(r["status"] == "ERROR" for r in rows),
        new_model_forwards=0,
        speed_claim=False,
        goal_met=False,
    )
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
