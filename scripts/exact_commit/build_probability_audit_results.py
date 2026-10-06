"""Offline scientific verdict from complete M31 inputs, proofs and controls.

No CFG search or model inference is executed. A --capture check
additionally binds retained probabilities to the locally archived full logits.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from fractions import Fraction
from itertools import product
from math import isfinite
from pathlib import Path
from random import Random
from statistics import median

from scripts.exact_commit.io_utils import _reject_json_constant, read, sha
from scripts.exact_commit.probability_audit_controls import START, compile_array_plan

from mwpc_exact.budget_proof import _fraction, fraction_data
from mwpc_exact.conflict_proof import read_state
from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.mass_certificate import PosteriorScope, ProbabilityInput, verify_mass_proof
from mwpc_exact.reference.byte_grammars import _SourceGrammarBuilder
from mwpc_exact.reference.normalization import normalize_to_cnf
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "docs/artifacts/raw/m31_probability_v1"
PROCESSED = ROOT / "docs/artifacts/processed/m31_probability_v1"
GENERATED = ROOT / "paper/generated/m31_probability_v1"


def manifest(directory):
    values = read(directory / "manifest.json")
    paths = {
        str(p.relative_to(directory))
        for p in directory.rglob("*")
        if p.is_file() and p != directory / "manifest.json"
    }
    if paths != set(values):
        raise ValueError("manifest differs from complete archive inventory")
    for name, digest in values.items():
        if Path(name).is_absolute() or ".." in Path(name).parts or sha(directory / name) != digest:
            raise ValueError("archive path/hash changed")
    return sha(directory / "manifest.json")


def schema_array(raw, one_child):
    if not raw or any(byte not in b"[]," for byte in raw):
        return False
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeError):
        return False
    pending = [value]
    while pending:
        item = pending.pop()
        if not isinstance(item, list) or (one_child and len(item) > 1):
            return False
        pending.extend(item)
    return True


def expected_grammar(one_child):
    # Reconstruct the declared schema independently of the measurement driver.
    builder = _SourceGrammarBuilder(("S", "L"), start="S")
    builder.rule("S", b"[]")
    builder.rule("S", b"[", "S" if one_child else "L", b"]")
    if not one_child:
        builder.rule("L", "S")
        builder.rule("L", "S", b",", "L")
    return normalize_to_cnf(builder.build()).grammar


def check_capture(capture, encoded, inputs, config):
    import numpy as np

    case = encoded["case"]
    original_adapter = CompositionalByteLevelAdapter.from_token_pieces(
        read(capture / "tokenizer-pieces.json.gz")
    )
    if original_adapter.emissions != inputs.state.tokenizer_adapter.emissions:
        raise ValueError("original tokenizer bytes differ from archived input semantics")
    path = capture / case["array_file"]
    if sha(path) != encoded["source_array_sha256"]:
        raise ValueError("full-logit source changed")
    with np.load(path, allow_pickle=False) as data:
        logits, raw = data["logits"], data["probabilities"]
    if logits.shape != (case["slots"], inputs.state.tokenizer_adapter.vocabulary_size):
        raise ValueError("original full-logit shape differs")
    logits = logits.astype(np.float64)
    logits[:, config["mask_token_id"]] = -np.inf
    logits -= logits.max(axis=1, keepdims=True)
    expected = np.exp(logits)
    expected /= expected.sum(axis=1, keepdims=True)
    if not np.allclose(raw, expected, rtol=2e-14, atol=0):
        raise ValueError("full softmax does not reproduce stored probabilities")
    for offset, position in enumerate(case["masked_positions"]):
        original = tuple(Fraction(float(p)) for p in raw[offset])
        total = sum(original, Fraction())
        if total != _fraction(encoded["normalization"][offset]):
            raise ValueError("full-row rational normalization differs")
        wanted = tuple(original[t] / total for t in inputs.state.support.rows[position])
        if wanted != inputs.probabilities[position]:
            raise ValueError("retained original probabilities differ from full capture")


def audit(primary, followup, capture=None):
    primary_hash, followup_hash = manifest(primary), manifest(followup)
    config = read(primary / "config.json")
    meta, cap = read(primary / "metadata.json"), read(primary / "capture-metadata.json")
    later = read(followup / "metadata.json")
    source_config = ROOT / cap["config_source"]
    if (
        config != read(source_config)
        or cap["config_sha256"] != sha(source_config)
        or meta["config_sha256"] != cap["config_sha256"]
        or cap["git_commit"] != meta["git_commit"]
        or any(m["git_dirty"] is not False for m in (meta, cap, later))
        or cap["checkpoint_sha256"] != config["checkpoint_sha256"]
        or later["primary_manifest_sha256"] != primary_hash
        or later["new_model_forwards"] != 0
    ):
        raise ValueError("frozen capture/measurement/follow-up provenance differs")
    ids = [f"{probe['id']}-{n}" for probe in config["probes"] for n in config["slots"]]
    if len(ids) != len(set(ids)) or cap["recorded_forwards"] != len(ids):
        raise ValueError("new forward inventory differs from complete frozen grid")
    if capture is not None:
        if read(capture / "manifest.json") != read(primary / "capture-manifest.json"):
            raise ValueError("local full capture differs from archived lineage")
        manifest(capture)
    rows = [
        json.loads(line, parse_constant=_reject_json_constant)
        for line in (primary / "rows.jsonl").read_text().splitlines()
    ]
    if Counter((r["id"], r["limit"]) for r in rows) != Counter(
        product(ids, config["oracle_limits"])
    ):
        raise ValueError("missing, duplicate or foreign method jobs")
    references, original_inputs = {}, {}
    for case_id in ids:
        input_path = primary / "inputs" / f"{case_id}.json.gz"
        encoded = read(input_path)
        case = encoded["case"]
        state = read_state(encoded["input"])
        inputs = ProbabilityInput(
            state, tuple(tuple(_fraction(p) for p in row) for row in encoded["probabilities"])
        )
        if inputs.fingerprint != encoded["input_fingerprint"]:
            raise ValueError("original input fingerprint differs")
        probe = next(p for p in config["probes"] if case_id == f"{p['id']}-{case['slots']}")
        one_child = probe["grammar"] == "recursive_one_child_arrays"
        masked = case["masked_positions"]
        if (
            case["id"] != case_id
            or case["probe"] != probe
            or tuple(case["canvas"]) != state.canvas
            or case["slots"] not in config["slots"]
            or case["seed"] != config["seed"]
            or masked != [i for i, t in enumerate(state.canvas) if t is None]
            or masked != list(range(masked[0], masked[0] + case["slots"]))
            or case["model_revision"] != config["model_revision"]
            or case["tokenizer_revision"] != config["tokenizer_revision"]
            or state.eos_policy != EOSPolicy(EOSMode.ABSENT)
            or state.grammar != expected_grammar(one_child)
        ):
            raise ValueError("declared schema/canvas/config differs from original input")
        emissions = state.tokenizer_adapter.emissions
        prefix = b"".join(emissions[t] for t in state.canvas[: masked[0]])
        suffix = b"".join(emissions[t] for t in state.canvas[masked[-1] + 1 :])
        if prefix != probe["prefix"].encode() or suffix != probe["suffix"].encode():
            raise ValueError("fixed bytes differ from the declared application")
        alphabet = {91, 93} if one_child else {91, 93, 44}
        required = {t for t, e in enumerate(emissions) if e is not None and set(e) <= alphabet}
        if any(not required <= set(state.support.rows[i]) for i in masked):
            raise ValueError("missing compatible original token invalidates full scope")
        if capture is not None:
            check_capture(capture, encoded, inputs, config)
        ref = read(followup / f"{case_id}.json")
        lineage = read(followup / f"{case_id}-lineage.json")
        if (
            lineage["input_sha256"] != sha(input_path)
            or lineage["git_commit"] != later["git_commit"]
        ):
            raise ValueError("reference worker input/code lineage differs")
        plan = compile_array_plan(emissions, state.support.rows, one_child=one_child)
        z, count = plan.forward(inputs.probabilities)
        if plan.backward(inputs.probabilities)[0].get(START, Fraction()) != z:
            raise ValueError("independent forward/backward masses disagree")
        original_ref = read(primary / "references" / f"{case_id}.json")
        if (
            _fraction(ref["valid_mass"]) != z
            or ref["positive_valid_token_paths"] != count
            or original_ref["valid_mass"] != ref["valid_mass"]
            or ref["state_cells"] != plan.state_cells
            or len(ref["timings"]) != config["reference_repetitions"]
        ):
            raise ValueError("archived exact reference does not recompute")
        for value in (
            ref["coverage_seconds"],
            ref["compilation_seconds"],
            *(t for timing in ref["timings"] for t in timing.values()),
        ):
            if type(value) not in (float, int) or not isfinite(value) or value < 0:
                raise ValueError("invalid reference timing")
        if z and not schema_array(ref["sample"].encode(), one_child):
            raise ValueError("reference sample fails independent JSON/schema validation")
        references[case_id] = ref
        original_inputs[case_id] = inputs, one_child, z
    checked = 0
    for row in rows:
        inputs, one_child, z = original_inputs[row["id"]]
        if (
            row["input_fingerprint"] != inputs.fingerprint
            or row["git_commit"] != meta["git_commit"]
            or row["config_sha256"] != cap["config_sha256"]
            or row["seed"] != config["seed"]
            or row["model_revision"] != config["model_revision"]
            or row["tokenizer_revision"] != config["tokenizer_revision"]
            or row["support_sha256"] != inputs.state.support.fingerprint
            or row["exactness_scope"] != inputs.state.support.exactness_scope.to_dict()
            or row["reference_scope"] != PosteriorScope.FULL.value
        ):
            raise ValueError("method row differs from its original input/provenance")
        if row["status"] in ("external_timeout", "worker_error"):
            if row["admitted"] is not False or row.get("sample") is not None:
                raise ValueError("failed job presented as admitted sample")
            continue
        expected_artifact = f"jobs/{row['id']}-k{row['limit']}.json.gz"
        if row["artifact"] != expected_artifact:
            raise ValueError("certificate path differs from frozen method job")
        job = read(primary / expected_artifact)
        proof = job["proof"]
        result = verify_mass_proof(proof, expected_input=inputs)
        if (
            proof["reference_scope"] != PosteriorScope.FULL.value
            or _fraction(proof["requested_tv"]) != Fraction(*config["tolerance"])
            or row["status"] != proof["status"]
            or result.oracle_calls > row["limit"]
            or not result.lower <= z <= result.upper(PosteriorScope.FULL)
        ):
            raise ValueError("invalid status/work/scope or true mass outside envelope")
        for witness, mass in result.accepted:
            if not schema_array(
                inputs.state.tokenizer_adapter.detokenize_bytes(witness), one_child
            ) or mass != inputs.box_mass(tuple((t,) for t in witness)):
                raise ValueError("accepted original-token mass/path is invalid")
        tv = 1 - result.lower / z if result.lower else None
        bound = result.tv_bound(PosteriorScope.FULL)
        admitted = bound is not None and bound <= Fraction(*config["tolerance"])
        generic = (
            (result.unresolved + result.omitted)
            / (result.lower + result.unresolved + result.omitted)
            if result.lower
            else None
        )
        expected = {
            "lower": fraction_data(result.lower),
            "upper": fraction_data(result.upper(PosteriorScope.FULL)),
            "certified_tv": fraction_data(bound),
            "true_tv": fraction_data(tv),
            "generic_tv": fraction_data(generic),
            "admitted": admitted,
            "oracle_calls": result.oracle_calls,
            "accepted_paths": len(result.accepted),
        }
        if any(row[k] != v for k, v in expected.items()) or (tv is not None and tv > bound):
            raise ValueError("method mass/error/admission does not recompute")
        sample = None
        if admitted:
            witness = result.sample(
                Random(config["seed"]),
                scope=PosteriorScope.FULL,
                max_tv=Fraction(*config["tolerance"]),
            )
            sample = inputs.state.tokenizer_adapter.detokenize_bytes(witness).decode()
        if row["sample"] != sample:
            raise ValueError("admitted/refused sample does not recompute")
        if row["solve_internal_check_seconds"] != job["solve_internal_check_seconds"]:
            raise ValueError("timing row differs from the original worker")
        checked += 1
    return (
        rows,
        references,
        {
            "primary_manifest_sha256": primary_hash,
            "reference_manifest_sha256": followup_hash,
            "producing_commit": meta["git_commit"],
            "reference_followup_commit": later["git_commit"],
            "certificates_checked": checked,
            "new_model_forwards": len(ids),
            "full_local_logits_checked": capture is not None,
        },
    )


def reference_cost(ref):
    return (
        ref["coverage_seconds"]
        + ref["compilation_seconds"]
        + median(sum(t.values()) for t in ref["timings"])
    )


def summarize(rows, references, provenance):
    successful = [r for r in rows if r["status"] not in ("external_timeout", "worker_error")]
    return {
        "verification": "PASS",
        "provenance": provenance,
        "jobs": len(rows),
        "status_counts": dict(Counter(r["status"] for r in rows)),
        "by_slots_at_64": [
            {
                "slots": n,
                "cases": sum(r["slots"] == n and r["limit"] == 64 for r in rows),
                "admitted": sum(
                    r["slots"] == n and r["limit"] == 64 and r["admitted"] for r in rows
                ),
            }
            for n in (4, 8, 16)
        ],
        "exact_reference_cases": len(references),
        "reference_core_ms_range": [
            1000 * min(reference_cost(r) for r in references.values()),
            1000 * max(reference_cost(r) for r in references.values()),
        ],
        "reference_faster_returned_jobs": sum(
            reference_cost(references[r["id"]])
            < r["solve_internal_check_seconds"] + r["external_check_seconds"]
            for r in successful
        ),
        "returned_job_pairs": len(successful),
        "largest_positive_valid_token_path_count": max(
            r["positive_valid_token_paths"] for r in references.values()
        ),
        "verdict": {
            "mathematical_validity": (
                "supported under stated hypotheses; no observed bound/path violation"
            ),
            "practical_superiority": (
                "not established; compact exact transfer is preferable on these schemas"
            ),
            "scaling": (
                "limited-work admission declines on this complete grid; "
                "no general JSON scaling claim"
            ),
            "engineering_utility": (
                "portable checked certificates and fail-closed admission "
                "demonstrated as a prototype"
            ),
            "scientific_priority": (
                "incremental specialization of established principles; "
                "world novelty not established"
            ),
            "semantic_accuracy": "not measured or implied by these guarantees",
            "certainty": (
                "no finite test campaign establishes 100 percent relevance, "
                "priority or universal correctness"
            ),
        },
    }


def number(value):
    return "--" if value is None else f"{float(_fraction(value)):.6g}"


def seconds(value):
    return "--" if value is None else f"{value:.6f}"


def render(summary, rows, references):
    p = summary["provenance"]
    scaling = "\n".join(
        f"| {r['slots']} | {r['cases']} | {r['admitted']} |" for r in summary["by_slots_at_64"]
    )
    detail = []
    for r in rows:
        detail.append(
            f"| {r['id']} | {r['limit']} | {r['status']} | "
            f"{number(r.get('certified_tv'))} | {number(r.get('true_tv'))} | "
            f"{seconds(r.get('solve_internal_check_seconds'))} | "
            f"{seconds(r.get('external_check_seconds'))} | "
            f"{1000 * reference_cost(references[r['id']]):.3f} |"
        )
    job_table = "\n".join(detail)
    low, high = summary["reference_core_ms_range"]
    statuses = json.dumps(summary["status_counts"], sort_keys=True)
    largest = summary["largest_positive_valid_token_path_count"]
    faster, pairs = summary["reference_faster_returned_jobs"], summary["returned_job_pairs"]
    return f"""# Scientific relevance audit: complete larger-canvas results

Original-input certificates, independent exact controls, complete grid and provenance: **PASS**.

{p["new_model_forwards"]} fresh official CPU MDLM predictions; {summary["jobs"]} partition jobs;
{p["certificates_checked"]} returned certificates independently accepted.

## Verdict

Mathematical validity and the checked admission/refusal interface survive this
audit. A general practical advantage does **not** follow. The compact exact
control resolves every canvas with zero conditional approximation error and
lower observed inference cost than every returned partition job. This rejects
a superiority claim on these two schemas; it does not prove that every CFG
has such a compact representation.

The contribution is an incremental finite-slot/token-provenance certification
specialization. Conditioning, WMC, deterministic anytime bounds and alphabet
filters are established. Novelty priority, semantic accuracy, production benefit
and universal runtime superiority remain unestablished. No percentage of
scientific certainty is assigned.

## Complete scaling outcomes at 64 calls

| Free token slots | Canvases | Admitted at TV <= 0.05 |
|---:|---:|---:|
{scaling}

All-job statuses: `{statuses}`.

The exact control sums as many as {largest:,} positive original-token paths
without enumerating them. Its measured coverage + compilation + median
forward/backward/sample cost ranges from {low:.3f} to {high:.3f} ms. It is faster
in {faster}/{pairs} returned-job comparisons. External timeouts are retained and
excluded from paired numeric timing ratios.

## Every method job

| Canvas | Cap | Status | TV bound | True TV | Solve/check (s) | Check (s) | Reference (ms) |
|---|---:|---|---:|---:|---:|---:|---:|
{job_table}

## Comparison and availability boundaries

These are controlled schema/scaling probes, not an external semantic benchmark,
production requests, or a new full denoising trajectory. They cover one-child
arrays and recursively nested arrays with multiple children. All prefixes and
4/8/16-slot combinations were frozen before predictions. The 36 cells reuse
18 predictions; repetitions are not new requests.

The control independently implements standard finite-state/counter transfer.
It is not an execution of Dang--Ermon, FactorDLM or CARS. It shares original
probabilities, token IDs, fixed slots and ABSENT EOS. Full vocabulary scope
requires every alphabet-compatible original token to be retained. Count tokens
once per original-token path, including aliases. Never renormalize retained rows.

Reference time includes coverage validation, transition compilation and a median
of three query repetitions after one warmup. Each query includes forward,
backward and sampled-output JSON/schema validation. Parser time includes proof
construction and internal validation; external portable checking is separate.
Call caps count primary selection queries; proof construction can issue further
parsing queries and is included in measured solver time.
Input/logit reconstruction and model forward are separate/shared in raw rows.
Process startup and serialization are outside reference/solver core; external
wall times are retained. A certifying engine and an exact numeric control expose
different interfaces: these are diagnostic inference-cost comparisons, not
full-deployment runtime rankings.

Fresh reference and parser worker RSS include imported libraries. Original
controller-reference timings lacked a separately recorded coverage scan. They
are preserved unchanged but excluded from the final cost comparison. A separately
committed follow-up repeats only exact reference queries on the same inputs,
including coverage time and a fresh-worker memory boundary. No model or
partition outcome is repeated or replaced.

Full logits/probability matrices remain in the ignored local capture; large
traces are not committed. Git contains complete tokenizer semantics, retained
exact rational inputs, normalization/array hashes, every returned proof, all
statuses and generated evidence. The default verifier reproduces mathematics
and tables offline. `--capture` additionally checks every retained probability
and normalization against the full local logits/softmax and tokenizer bytes.
Full-logit availability is limited accordingly. A fresh opt-in checkpoint run
is a reproduction, not a claim of bitwise GPU equivalence.

Producing commit: `{p["producing_commit"]}`.
Reference timing follow-up: `{p["reference_followup_commit"]}`.
Immutable primary manifest: `{p["primary_manifest_sha256"]}`.
Immutable reference manifest: `{p["reference_manifest_sha256"]}`.

Prior-art scope and pre-measurement falsification criteria:
`docs/research/m31-relevance-audit.md` and
`docs/research/m30-probability-certificates.md`.
"""


def products(capture=None):
    rows, references, provenance = audit(RAW / "primary", RAW / "reference-followup", capture)
    # Local presence is a check outcome, not a deterministic scientific result.
    provenance["full_local_logits_checked"] = "optional_external_check_not_part_of_generated_tables"
    summary = summarize(rows, references, provenance)
    macros = {
        "MProbAuditCanvases": str(provenance["new_model_forwards"]),
        "MProbAuditJobs": str(summary["jobs"]),
        "MProbAuditProofs": str(provenance["certificates_checked"]),
        "MProbAuditTimeouts": str(summary["status_counts"].get("external_timeout", 0)),
        "MProbAuditFourAdmitted": str(summary["by_slots_at_64"][0]["admitted"]),
        "MProbAuditEightAdmitted": str(summary["by_slots_at_64"][1]["admitted"]),
        "MProbAuditSixteenAdmitted": str(summary["by_slots_at_64"][2]["admitted"]),
        "MProbAuditReferenceFaster": str(summary["reference_faster_returned_jobs"]),
    }
    tex = (
        "% Generated from the complete independently audited larger-canvas grid.\n"
        + "\n".join("\\newcommand{\\" + key + "}{" + value + "}" for key, value in macros.items())
        + "\n"
    )
    return {
        PROCESSED / "summary.json": json.dumps(summary, indent=2, sort_keys=True) + "\n",
        PROCESSED / "report.md": render(summary, rows, references),
        GENERATED / "numbers.tex": tex,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--capture", type=Path)
    args = parser.parse_args()
    for path, value in products(args.capture).items():
        if args.check:
            if not path.is_file() or path.read_text() != value:
                raise ValueError(f"generated audit result changed: {path.relative_to(ROOT)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(value)
    print(
        json.dumps({"verification": "PASS", "full_local_logits_checked": args.capture is not None})
    )


if __name__ == "__main__":
    main()
