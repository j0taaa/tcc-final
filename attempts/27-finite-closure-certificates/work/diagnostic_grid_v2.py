"""All existing18 cases: certificate feasibility only, no favorable selection."""

import argparse
import gc
import gzip
import hashlib
import json
import subprocess
from fractions import Fraction
from pathlib import Path
from time import monotonic

from mwpc_exact.cfg_posterior import CompilationLimit
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from .finite_closure import FiniteClosure
from .frozen.posterior import Weights, class_weights
from .frozen.stack_control import StackPosterior, StackPrepared
from .frozen.table import LexerTable

WORK = Path(__file__).resolve().parent


def main():
    import numpy as np

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=WORK / "grid-protocol-v2.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text())
    capture = Path(protocol["capture"])
    args.output.mkdir(parents=True, exist_ok=False)
    full_masses = {}
    reference = Path(protocol["reference_rows"])
    with gzip.open(reference, "rt") as file:
        for line in file:
            row = json.loads(line)
            if row["status"] == "complete" and row.get("valid_mass") is not None:
                case = f"{row['case']}-{row['mask_count']}"
                mass = Fraction(row["valid_mass"])
                if case in full_masses and mass != full_masses[case]:
                    raise RuntimeError("archived full controls disagree")
                full_masses[case] = mass
    vocabulary = capture / "vocabulary.json"
    adapter = CompositionalByteLevelAdapter.from_token_pieces(json.loads(vocabulary.read_text()))
    table = LexerTable(adapter)
    variants = [("residue", m) for m in protocol["moduli"]]
    variants += [("potential", k) for k in protocol["potential_exponents"]]
    metadata = dict(
        producer_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        protocol=protocol,
        protocol_sha256=hashlib.sha256(args.protocol.read_bytes()).hexdigest(),
        reference_rows_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),
        vocabulary_sha256=hashlib.sha256(vocabulary.read_bytes()).hexdigest(),
        vocabulary_size=adapter.vocabulary_size,
        new_neural_forwards=0,
        scope="All reused development cases; necessary feasibility, no timings or novelty claim",
    )
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    inventory, counts = {}, {}
    with gzip.open(args.output / "rows.jsonl.gz", "xt") as out:
        for case in protocol["cases"]:
            info_path = capture / (case + ".json")
            path = capture / (case + ".npy")
            info = json.loads(info_path.read_text())
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != info["probabilities_sha256"]:
                raise RuntimeError("original probability capture changed")
            inventory[case] = dict(probabilities_sha256=digest, frame=info)
            model_rows = dict(
                zip(info["positions"], np.load(path, allow_pickle=False), strict=True)
            )
            weights = Weights(
                [model_rows.get(p, ()) for p in range(len(info["canvas"]))],
                info["canvas"],
                adapter.vocabulary_size,
            )
            sums = class_weights(table, weights)
            for depth in protocol["depths"]:
                plan = finite = None
                prepared_error = None
                try:
                    plan = StackPrepared(
                        table,
                        weights.canvas,
                        max_depth=depth,
                        track_overflow=True,
                        **{
                            k: protocol[k]
                            for k in ("max_cells", "max_edges", "max_terms", "timeout_seconds")
                        },
                    )
                    lower = StackPosterior(plan, weights, sums=sums).mass
                    finite = FiniteClosure(plan, weights, sums=sums)
                except (CompilationLimit, TimeoutError, MemoryError) as error:
                    prepared_error = str(error)
                for method, parameter in variants:
                    row = dict(case=case, depth=depth, method=method, parameter=parameter)
                    try:
                        if prepared_error is not None:
                            raise CompilationLimit(prepared_error)
                        # Each query gets its declared own resource guard; not a timing.
                        finite.deadline = monotonic() + protocol["timeout_seconds"]
                        upper, cells = (
                            finite.residue(parameter)
                            if method == "residue"
                            else finite.potential(parameter)
                        )
                        actual = full_masses.get(case)
                        if actual is not None and not 0 <= actual - lower <= upper:
                            raise RuntimeError("bound or lower disagrees with archived exact mass")
                        delta = upper / (lower + upper) if lower else None
                        row.update(
                            status="complete" if lower else "zero_lower_mass",
                            lower=str(lower),
                            upper=str(upper),
                            suffix_cells=cells,
                            frontier_states=len(finite.frontier),
                            delta=str(delta) if delta is not None else None,
                            certifies=delta is not None
                            and delta <= Fraction(protocol["tolerance"]),
                            archived_full_mass=str(actual) if actual is not None else None,
                        )
                    except (CompilationLimit, TimeoutError, MemoryError) as error:
                        row.update(status="resource_refusal", error=str(error), certifies=False)
                    counts[row["status"]] = counts.get(row["status"], 0) + 1
                    out.write(json.dumps(row) + "\n")
                    out.flush()
                print(json.dumps(dict(case=case[:8], depth=depth, statuses=counts)), flush=True)
                del plan, finite
                gc.collect()
    (args.output / "input-inventory.json").write_text(json.dumps(inventory, indent=2) + "\n")
    (args.output / "summary.json").write_text(json.dumps(counts, indent=2) + "\n")


if __name__ == "__main__":
    main()
