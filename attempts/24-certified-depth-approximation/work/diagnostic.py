"""Frozen certificate-feasibility audit on all existing model inputs; no new model.

All failures and zero lower masses retained. This is a development diagnostic,
not a performance experiment or a new independent corpus confirmation.
"""

import argparse
import gc
import hashlib
import json
import resource
import signal
import subprocess
from pathlib import Path

from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from .certificate import CounterTable, conditional_error
from .posterior import Weights
from .stack_control import StackPosterior, StackPrepared
from .table import LexerTable

WORK = Path(__file__).resolve().parent


def deadline(signum, frame):
    raise TimeoutError("whole case resource deadline; not invalidity")


def main():
    import numpy as np

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    protocol = json.loads((WORK / "diagnostic-protocol.json").read_text())
    vocabulary = json.loads((args.capture / "vocabulary.json").read_text())
    adapter = CompositionalByteLevelAdapter.from_token_pieces(vocabulary)
    table = LexerTable(adapter)
    counter = CounterTable(table)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    metadata = dict(
        protocol=protocol,
        commit=commit,
        capture_metadata=json.loads((args.capture / "metadata.json").read_text()),
        groups=len(table.groups),
        counter_effects=len(counter.effects),
        operation="development certificate feasibility, no speed claim",
    )
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    for case in protocol["cases"]:
        info = json.loads((args.capture / (case + ".json")).read_text())
        probability_path = args.capture / (case + ".npy")
        if (
            hashlib.sha256(probability_path.read_bytes()).hexdigest()
            != info["probabilities_sha256"]
        ):
            raise RuntimeError("archived original model probability changed")
        probabilities = np.load(probability_path, allow_pickle=False)
        rows = [None] * len(info["canvas"])
        for p, row in zip(info["positions"], probabilities, strict=True):
            rows[p] = row
        weights = Weights(rows, info["canvas"], len(vocabulary))
        for depth in protocol["depths"]:
            record = dict(case=case, depth=depth, status="started", bounds={}, certificates={})
            signal.signal(signal.SIGALRM, deadline)
            signal.alarm(protocol["whole_depth_seconds"])
            try:
                for mode in ("closed", "suffix_hit", "hit"):
                    upper, stats = counter.tail(
                        weights,
                        depth,
                        mode=mode,
                        timeout_seconds=protocol["whole_depth_seconds"],
                        max_states=protocol["max_states"],
                    )
                    record["bounds"][mode] = dict(mass=str(upper), **stats)
                prepared = StackPrepared(
                    table,
                    info["canvas"],
                    max_depth=depth,
                    max_edges=10_000_000,
                    max_cells=10_000_000,
                    max_terms=50_000_000,
                    timeout_seconds=protocol["whole_depth_seconds"],
                )
                posterior = StackPosterior(prepared, weights)
                record["lower_mass"] = str(posterior.mass)
                record["nodes"] = prepared.graph_nodes
                record["edges"] = prepared.graph_edges
                record["status"] = "complete" if posterior.total else "zero_lower_mass"
                if posterior.total:
                    from fractions import Fraction

                    for mode, bound in record["bounds"].items():
                        delta = conditional_error(posterior.mass, Fraction(bound["mass"]))
                        record["certificates"][mode] = dict(
                            delta=str(delta),
                            tolerances=[t for t in protocol["tolerances"] if delta <= Fraction(t)],
                        )
            except (MemoryError, TimeoutError, RuntimeError) as error:
                from mwpc_exact.cfg_posterior import CompilationLimit

                if isinstance(error, RuntimeError) and not isinstance(error, CompilationLimit):
                    raise
                record.update(status="resource_refusal", error=str(error))
            finally:
                signal.alarm(0)
            with (args.output / "rows.jsonl").open("a") as stream:
                stream.write(json.dumps(record) + "\n")
            print(
                json.dumps(
                    dict(
                        case=case[:8],
                        depth=depth,
                        status=record["status"],
                        certificates={
                            m: v["tolerances"] for m, v in record["certificates"].items()
                        },
                    )
                ),
                flush=True,
            )
            if "posterior" in locals():
                del posterior
            if "prepared" in locals():
                del prepared
            gc.collect()


if __name__ == "__main__":
    # Match prior exact-control physical memory budget; never turn refusal into
    # a certificate, nor treat already captured inputs as independent evidence.
    resource.setrlimit(resource.RLIMIT_AS, (3 * 1024**3, 3 * 1024**3))
    main()
