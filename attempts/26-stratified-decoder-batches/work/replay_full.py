"""Full original-vocabulary replay of the same predeclared public MDLM head.

Functional demonstration and exact event audit, not a new model experiment.
No source tokens, verifier or scoring rule guide compilation or sampling.
"""

import argparse
import hashlib
import io
import json
import subprocess
from pathlib import Path
from random import Random
from time import perf_counter
from zipfile import ZipFile

from scripts.exact_commit.full_head_packet import check

from mwpc_exact.cfg_posterior import CompilationLimit
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from .batch import draw_batch
from .frozen.posterior import Weights
from .frozen.stack_control import StackPosterior, StackPrepared
from .frozen.table import LexerTable
from .layer_bridge import stack_ranks
from .replay import event_audit


def main():
    import numpy as np

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    audit = check(args.packet)
    source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    with ZipFile(args.packet) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        name = manifest["case"]
        case = json.loads(archive.read(name + ".json"))
        metadata = json.loads(archive.read("metadata.json"))
        adapter = CompositionalByteLevelAdapter.from_token_pieces(
            json.loads(archive.read("vocabulary.json"))
        )
        matrix = np.load(io.BytesIO(archive.read(name + ".npy")), allow_pickle=False)
    model_rows = dict(zip(case["positions"], matrix, strict=True))
    rows = [model_rows.get(p, ()) for p in range(len(case["canvas"]))]
    result = dict(
        source_commit=source_commit,
        producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        packet_sha256=audit["packet_sha256"],
        source_case=name,
        scope="Exact JSON posterior on all original ordinary tokens; EOS absent",
        vocabulary_size=adapter.vocabulary_size,
        unsupported_emissions_retain_probability_in_denominators=True,
        source_ids_used_only_by_auditor=True,
        seed=2026101026,
        new_neural_forwards=0,
        observed_scope="Archived-head functional replay; no semantic or latency benchmark",
    )
    began = perf_counter()
    try:
        weights = Weights(rows, case["canvas"], adapter.vocabulary_size)
        table = LexerTable(adapter)
        prepared = StackPrepared(
            table,
            case["canvas"],
            max_edges=1000000,
            max_cells=200000,
            max_terms=50000000,
            timeout_seconds=120,
        )
        posterior = StackPosterior(prepared, weights)
        result.update(
            valid_mass=str(posterior.mass),
            retained_states=prepared.retained_nodes,
            retained_edges=prepared.retained_edges,
            lexical_groups=len(table.groups),
            stack_preparation_wall=perf_counter() - began,
        )
        if not posterior.total:
            result["status"] = "zero_valid_mass_on_full_ordinary_vocabulary"
        else:
            began_ranks = perf_counter()
            ranked = stack_ranks(posterior)
            result.update(
                status="complete",
                root_integer_bits=ranked.total.bit_length(),
                rank_preparation_wall=perf_counter() - began_ranks,
            )
            # Only the auditor reads the source IDs, after the circuit is frozen.
            source_ids = next(x["tokens"] for x in metadata["selected"] if x["key"] == case["case"])
            allowed = {p: {source_ids[p]} for p in case["positions"]}
            result["exact_source_id_event"] = {
                str(size): event_audit(ranked, allowed, size) for size in (2, 8, 32)
            }
            result["samples"], result["batch_wall"] = {}, {}
            for method, stratified in (("iid", False), ("stratified", True)):
                began_batch = perf_counter()
                words = draw_batch(ranked.kernel, 32, Random(result["seed"]), stratified=stratified)
                result["batch_wall"][method] = perf_counter() - began_batch
                samples = []
                for word in words:
                    text = adapter.detokenize_bytes(word).decode("utf8")
                    value = json.loads(
                        text, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x))
                    )
                    if any(f is not None and word[p] != f for p, f in enumerate(case["canvas"])):
                        raise RuntimeError("original fixed ID changed")
                    samples.append(dict(original_ids=list(word), text=text, parsed_value=value))
                result["samples"][method] = samples
            result["valid_replay_candidates"] = 64
            result["timing_scope"] = (
                "One descriptive run, same rank circuit for iid; not a speed claim"
            )
    except CompilationLimit as error:
        result.update(status="resource_refusal", error=str(error))
    result["total_replay_wall"] = perf_counter() - began
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as file:
        json.dump(result, file, indent=2)
        file.write("\n")
    print(json.dumps({k: result[k] for k in ("status", "scope", "total_replay_wall")}))


if __name__ == "__main__":
    main()
