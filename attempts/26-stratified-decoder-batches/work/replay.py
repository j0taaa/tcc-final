"""Replay one pre-existing complete MDLM head; no new model or timing campaign."""

import argparse
import io
import json
from fractions import Fraction as F
from math import prod
from pathlib import Path
from random import Random
from time import perf_counter
from zipfile import ZipFile

from scripts.exact_commit.full_head_packet import check

from mwpc_exact.cfg_posterior import CompilationLimit, compile_cfg_sampler
from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.mass_certificate import ProbabilityInput
from mwpc_exact.reference.json_grammar import json_source_grammar
from mwpc_exact.reference.normalization import normalize_to_cnf
from mwpc_exact.state import SelectionInput
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import SupportKind

from .batch import draw_batch
from .ranks import CfgRanks


def event_audit(ranks, allowed, size):
    """Exact pass@K for a token-evidence event, not a Monte Carlo estimate."""
    total = ranks.total
    stops = {total}
    for z in range(size + 1):
        ticket, residual = divmod(z * total, size)
        stops.add(ticket)
        if residual:
            stops.add(ticket + 1)
    ordered = sorted(stops)
    counts = dict(zip(ordered, ranks.evidence_prefix(allowed, ordered), strict=True))

    def lifted(z):
        ticket, residual = divmod(z, size)
        return size * counts[ticket] + (
            residual * (counts[ticket + 1] - counts[ticket]) if residual else 0
        )

    ps = tuple(F(lifted((j + 1) * total) - lifted(j * total), total) for j in range(size))
    p = F(counts[total], total)
    if sum(ps) != size * p:
        raise RuntimeError("replicated-ticket marginal partition failed")
    iid, stratified = 1 - (1 - p) ** size, 1 - prod(1 - v for v in ps)
    if stratified < iid:
        raise RuntimeError("universal dominance contradicted on archived head")
    return dict(
        event_probability=str(p),
        stratum_probabilities=list(map(str, ps)),
        iid_pass=str(iid),
        stratified_pass=str(stratified),
        iid_pass_float=float(iid),
        stratified_pass_float=float(stratified),
        strict=stratified > iid,
    )


def main():
    import numpy as np

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    audit = check(args.packet)
    with ZipFile(args.packet) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        name = manifest["case"]
        case = json.loads(archive.read(name + ".json"))
        metadata = json.loads(archive.read("metadata.json"))
        adapter = CompositionalByteLevelAdapter.from_token_pieces(
            json.loads(archive.read("vocabulary.json"))
        )
        matrix = np.load(io.BytesIO(archive.read(name + ".npy")), allow_pickle=False)
    source_ids = next(x["tokens"] for x in metadata["selected"] if x["key"] == case["case"])
    rows, probabilities = {}, []
    model_rows = dict(zip(case["positions"], matrix, strict=True))
    for p, fixed in enumerate(case["canvas"]):
        if fixed is not None:
            rows[p], values = (fixed,), (F(1),)
        else:
            full = tuple(F(float(x)) for x in model_rows[p])
            denominator = sum(full)
            # Fixed rule: top16 ordinary tokens, with all excluded mass declared.
            ordered = np.argsort(-model_rows[p], kind="stable")
            rows[p] = tuple(int(t) for t in ordered if adapter.emissions[int(t)] is not None)[:16]
            values = tuple(full[t] / denominator for t in rows[p])
        probabilities.append(values)
    support = build_per_position_support(
        canvas=tuple(case["canvas"]),
        policy=SupportPolicy(kind=SupportKind.EXPLICIT, vocabulary_size=adapter.vocabulary_size),
        explicit_support=rows,
    )
    source = json_source_grammar()
    state = SelectionInput(
        normalize_to_cnf(source).grammar,
        tuple(case["canvas"]),
        (),
        support,
        adapter,
        EOSPolicy(EOSMode.ABSENT),
    )
    data = ProbabilityInput(state, tuple(probabilities))
    started = perf_counter()
    result = dict(
        packet_sha256=audit["packet_sha256"],
        source_case=name,
        scope="Exact posterior on top16 ordinary original-token support; archived forward only",
        omitted_product_mass=str(data.omitted_mass),
        input_fingerprint=data.fingerprint,
        support_rows={str(p): list(row) for p, row in rows.items() if case["canvas"][p] is None},
        source_ids_used_only_by_auditor=True,
        new_neural_forwards=0,
    )
    try:
        plan = compile_cfg_sampler(source, state, timeout_seconds=30)
        posterior = plan.evaluate(data)
        result.update(
            valid_mass=str(posterior.valid_mass),
            chart_cells=len(plan.terms),
            alternatives=plan.alternatives,
        )
        if not posterior.valid_mass:
            result["status"] = "zero_valid_mass_on_support"
        else:
            ranked = CfgRanks(posterior)
            allowed = {p: {source_ids[p]} for p in case["positions"]}
            result.update(status="complete", root_integer_bits=ranked.total.bit_length())
            result["exact_source_id_event"] = {
                str(size): event_audit(ranked, allowed, size) for size in (2, 8, 32)
            }
            result["samples"] = {}
            for method, stratified in (("iid", False), ("stratified", True)):
                words = draw_batch(ranked.kernel, 32, Random(2026101026), stratified=stratified)
                samples = []
                for word in words:
                    text = adapter.detokenize_bytes(word).decode("utf8")
                    value = json.loads(
                        text, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x))
                    )
                    if any(f is not None and word[p] != f for p, f in enumerate(state.canvas)):
                        raise RuntimeError("original fixed ID changed")
                    samples.append(dict(original_ids=list(word), text=text, parsed_value=value))
                result["samples"][method] = samples
            result["observed_scope"] = (
                "64 valid replay candidates; no empirical superiority or "
                "whole-trajectory measurement"
            )
    except CompilationLimit as error:
        result.update(status="resource_refusal", error=str(error))
    result["preparation_and_replay_wall"] = perf_counter() - started
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as file:
        json.dump(result, file, indent=2)
        file.write("\n")
    print(json.dumps({k: result[k] for k in ("status", "scope", "preparation_and_replay_wall")}))


if __name__ == "__main__":
    main()
