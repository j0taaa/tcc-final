"""Recheck fresh-prediction probability archives and generate manuscript evidence.

No model forward or search is run. All frozen cells, including refusals/errors,
are retained. Exact specialized controls remain visible instead of being called
an inferior decoder or hidden behind the generic certificate engine.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from fractions import Fraction
from itertools import product
from pathlib import Path
from random import Random
from statistics import median

from scripts.exact_commit.run_conflict_real import read, sha
from scripts.exact_commit.run_probability_probes import inputs_for, sha_json

from mwpc_exact.budget_proof import fraction_data
from mwpc_exact.mass_certificate import PosteriorScope, verify_mass_proof
from mwpc_exact.probabilistic_update import certified_parallel_update

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "docs/artifacts/raw/m30_probability_v1"
PROCESSED = ROOT / "docs/artifacts/processed/m30_probability_v1"
GENERATED = ROOT / "paper/generated/m30_probability_v1"


def fraction(value):
    return None if value is None else Fraction(*value)


def manifest(directory):
    values = read(directory / "manifest.json")
    paths = {
        str(p.relative_to(directory))
        for p in directory.rglob("*")
        if p.is_file() and p != directory / "manifest.json"
    }
    if paths != set(values):
        raise ValueError("manifest does not match the complete archive inventory")
    for name, digest in values.items():
        if Path(name).is_absolute() or ".." in Path(name).parts or sha(directory / name) != digest:
            raise ValueError("archive path/hash changed")
    return sha(directory / "manifest.json")


def check_case(config, case, case_id, emissions):
    """Bind a prediction's actual fixed bytes and masks to its frozen probe."""
    probe = next((p for p in config["probes"] if f"{p['id']}-{case['slots']}" == case_id), None)
    if (
        probe is None
        or case["probe"] != probe
        or case["id"] != case_id
        or case["slots"] not in config["slots"]
        or case["model_revision"] != config["model_revision"]
        or case["tokenizer_revision"] != config["tokenizer_revision"]
        or case["seed"] != config["seed"]
        or case["array_file"] != f"{case_id}.npz"
    ):
        raise ValueError("capture case differs from its frozen probe/configuration")
    masked = case["masked_positions"]
    actual = [i for i, t in enumerate(case["canvas"]) if t is None]
    if (
        len(masked) != case["slots"]
        or any(type(i) is not int for i in masked)
        or masked != actual
        or masked != list(range(masked[0], masked[0] + case["slots"]))
    ):
        raise ValueError("capture mask positions differ from its physical canvas")
    fixed = [*case["canvas"][: masked[0]], *case["canvas"][masked[-1] + 1 :]]
    if any(
        type(t) is not int or not 0 <= t < len(emissions) or emissions[t] is None for t in fixed
    ):
        raise ValueError("capture fixed tokens have invalid byte emissions")
    prefix = b"".join(emissions[t] for t in case["canvas"][: masked[0]])
    suffix = b"".join(emissions[t] for t in case["canvas"][masked[-1] + 1 :])
    if prefix != probe["prefix"].encode() or suffix != probe["suffix"].encode():
        raise ValueError("capture fixed bytes differ from the declared application")


def audit_phase(capture, probes):
    import numpy as np

    capture_hash, probe_hash = manifest(capture), manifest(probes)
    config = read(capture / "config.json")
    capture_meta, probe_meta = read(capture / "metadata.json"), read(probes / "metadata.json")
    if (
        read(probes / "config.json") != config
        or probe_meta["capture_metadata"] != capture_meta
        or probe_meta["capture_manifest_sha256"] != capture_hash
        or capture_meta["git_dirty"] is not False
        or probe_meta["git_dirty"] is not False
        or capture_meta["config_sha256"] != sha(ROOT / capture_meta["config_source"])
        or read(ROOT / capture_meta["config_source"]) != config
        or capture_meta["checkpoint_sha256"] != config["checkpoint_sha256"]
        or capture_meta["model_revision"] != config["model_revision"]
        or capture_meta["tokenizer_revision"] != config["tokenizer_revision"]
    ):
        raise ValueError("capture/evaluation/frozen-config provenance differs")
    rows = [json.loads(line) for line in (probes / "rows.jsonl").read_text().splitlines()]
    grid = set(
        product(
            (f"{p['id']}-{n}" for p in config["probes"] for n in config["slots"]),
            config["support_policies"],
            config["posterior_scopes"],
            config["oracle_limits"],
        )
    )
    actual = [
        (r["case_id"], r["support_policy"], r["coverage_mode"], r["oracle_limit"]) for r in rows
    ]
    if set(actual) != grid or len(actual) != len(grid):
        raise ValueError("frozen grid has duplicate or missing cells")
    cached, checked, cases = {}, 0, {}
    for row in rows:
        case_id, policy = row["case_id"], row["support_policy"]
        case = read(capture / f"{case_id}.json")
        if case_id not in cases:
            arrays = np.load(capture / case["array_file"], allow_pickle=False)
            logits, probs = arrays["logits"], arrays["probabilities"]
            if logits.shape != probs.shape or not np.isfinite(logits).all():
                raise ValueError("invalid source logits")
            shifted = logits.astype(np.float64)
            shifted[:, config["mask_token_id"]] = -np.inf
            shifted -= shifted.max(axis=-1, keepdims=True)
            reproduced = np.exp(shifted)
            reproduced /= reproduced.sum(axis=-1, keepdims=True)
            if not np.allclose(reproduced, probs, rtol=1e-12, atol=1e-18):
                raise ValueError("stored probabilities differ from archived full-vocabulary logits")
            cases[case_id] = case
        if (case_id, policy) not in cached:
            cached[case_id, policy] = inputs_for(capture, case, policy)
        predictive, exact = cached[case_id, policy]
        check_case(config, case, case_id, predictive.state.tokenizer_adapter.emissions)
        z = sum(exact.values(), Fraction())
        if (
            row["id"] != f"{case_id}-{policy}-{row['coverage_mode']}-{row['oracle_limit']}"
            or row["git_commit"] != probe_meta["git_commit"]
            or row["config_sha256"] != sha(capture / "config.json")
            or row["model_revision"] != config["model_revision"]
            or row["tokenizer_revision"] != config["tokenizer_revision"]
            or row["seed"] != config["seed"]
            or row["grammar_sha256"] != sha_json(predictive.state.grammar.to_dict())
            or row["support_sha256"] != predictive.state.support.fingerprint
            or row["exactness_scope"] != predictive.state.support.exactness_scope.to_dict()
            or row["input_fingerprint"] != predictive.fingerprint
            or row["reference_valid_mass"] != fraction_data(z)
            or row["reference_valid_token_paths"] != len(exact)
            or row["forward_seconds"] != case["forward_seconds"]
        ):
            raise ValueError(
                "row differs from original logits, canvas or independent exact control"
            )
        if row["status"] == "error":
            if not row.get("error_type") or not row.get("error"):
                raise ValueError("error outcome lacks its recorded reason")
            continue
        proof = read(probes / row["proof"])
        envelope = verify_mass_proof(proof, expected_input=predictive)
        checked += 1
        actual_tv = 1 - envelope.lower / z if envelope.lower and z else None
        bound = envelope.tv_bound(PosteriorScope.FULL)
        if not envelope.lower <= z <= envelope.upper(PosteriorScope.FULL):
            raise ValueError("exact probability violates the checked envelope")
        if actual_tv is not None and (bound is None or actual_tv > bound):
            raise ValueError("actual TV violates the claimed certificate")
        expected = {
            "status": proof["status"],
            "lower": fraction_data(envelope.lower),
            "unresolved": fraction_data(envelope.unresolved),
            "omitted": fraction_data(envelope.omitted),
            "outside_valid_upper": fraction_data(envelope.outside_valid_upper),
            "certified_full_tv": fraction_data(bound),
            "actual_full_tv": fraction_data(actual_tv),
            "support_tv_bound": fraction_data(envelope.tv_bound(PosteriorScope.REPRESENTED)),
            "oracle_calls": envelope.oracle_calls,
        }
        if any(row[k] != v for k, v in expected.items()):
            raise ValueError("reported bound/status does not match its portable proof")
        sample = None
        if row["status"] == "certified_tolerance":
            tolerance = (
                Fraction() if row["oracle_limit"] == 4096 else Fraction(*config["tolerance"])
            )
            update = certified_parallel_update(
                predictive,
                proof,
                committed_positions=case["masked_positions"],
                rng=Random(config["seed"]),
                scope=PosteriorScope.FULL,
                max_tv=tolerance,
            )
            if update.witness_token_ids not in exact:
                raise ValueError("admitted update violates independent application control")
            sample = predictive.state.tokenizer_adapter.detokenize_bytes(
                update.witness_token_ids
            ).decode()
        if sample != row["sample"]:
            raise ValueError("reported update differs from its reproducible certified sample")
    return rows, {
        "verification": "PASS",
        "portable_proofs": checked,
        "capture_manifest_sha256": capture_hash,
        "evaluation_manifest_sha256": probe_hash,
        "capture_metadata": capture_meta,
        "evaluation_metadata": probe_meta,
        "fresh_canvases": len(cases),
        "forward_seconds": {k: v["forward_seconds"] for k, v in cases.items()},
    }


def summarize(rows, provenance):
    statuses = Counter(r["status"] for r in rows)
    by_mode = {}
    for mode in sorted({r["coverage_mode"] for r in rows}):
        selected = [r for r in rows if r["coverage_mode"] == mode]
        by_mode[mode] = dict(Counter(r["status"] for r in selected))
    examples = []
    for case in sorted({r["case_id"] for r in rows}):
        selected = [
            r
            for r in rows
            if r["case_id"] == case
            and r["oracle_limit"] == 64
            and r["support_policy"].startswith("top8_plus_")
        ]
        coverage = next(r for r in selected if r["coverage_mode"] != "generic_tail")
        generic = next(r for r in selected if r["coverage_mode"] == "generic_tail")
        examples.append(
            {
                "case": case,
                "valid_paths": coverage["reference_valid_token_paths"],
                "full_valid_mass": coverage["reference_valid_mass"],
                "expected_rejection_draws": fraction_data(
                    1 / Fraction(*coverage["reference_valid_mass"])
                    if coverage["reference_valid_mass"][0]
                    else None
                ),
                "raw_omitted_mass": coverage.get("omitted"),
                "generic_status": generic["status"],
                "generic_tv": generic.get("certified_full_tv"),
                "coverage_status": coverage["status"],
                "coverage_tv": coverage.get("certified_full_tv"),
                "actual_tv": coverage.get("actual_full_tv"),
                "sample": coverage.get("sample"),
                "solve_seconds": coverage["solve_and_internal_check_seconds"],
                "check_seconds": coverage.get("portable_check_seconds"),
                "oracle_calls": coverage.get("oracle_calls"),
            }
        )
    return {
        "verification": "PASS",
        "fresh_canvases": sum(p["fresh_canvases"] for p in provenance),
        "evaluations": len(rows),
        "portable_proofs": sum(p["portable_proofs"] for p in provenance),
        "status_counts": dict(statuses),
        "by_mode": by_mode,
        "examples": examples,
        "provenance": provenance,
        "source_sha256": {
            str(p.relative_to(ROOT)): sha(p)
            for p in (
                Path(__file__),
                ROOT / "scripts/exact_commit/run_probability_probes.py",
                ROOT / "src/mwpc_exact/mass_certificate.py",
                ROOT / "src/mwpc_exact/mass_solver.py",
                ROOT / "src/mwpc_exact/language_coverage.py",
                ROOT / "src/mwpc_exact/probabilistic_update.py",
            )
        },
    }


def number(value):
    return "--" if value is None else f"{float(Fraction(*value)):.6g}"


def render(summary, rows):
    out = [
        "# Certified grammar-conditioned updates from fresh MDLM predictions",
        "",
        "Independent original-input/logit, complete-grid and portable-certificate audit: **PASS**.",
        "",
        f"{summary['fresh_canvases']} fresh CPU canvases, "
        f"{summary['evaluations']} repeated-measure evaluations, "
        f"{summary['portable_proofs']} independently checked proofs. Every outcome is retained.",
        "",
        "## Concrete use and mathematical guarantee",
        "",
        "A consumer selects a maximum tolerated distributional error. The certificate "
        "either authorizes "
        "a valid parallel update or refuses it, rather than silently renormalizing "
        "top-K predictions. "
        "The reference is the frozen product of original per-slot predictions "
        "conditioned on the declared "
        "grammar and fixed canvas. It is not the model's full generative joint or "
        "semantic accuracy.",
        "",
        "Disjoint token boxes yield valid-mass bounds [L,L+U] and TV <= U/(L+U). Ambiguous parses "
        "and token aliases cannot duplicate mass. Original omitted mass remains "
        "recorded. Closed-yield "
        "or terminal-alphabet proofs can establish zero valid omitted mass "
        "independently of its size. "
        "Lean checks partition, conditional-error algebra and CFG coverage; the full "
        "coupling argument "
        "and scope are in `docs/research/m30-probability-certificates.md`.",
        "",
        "## All admission outcomes",
        "",
        "| Coverage mode | Certified | Incomplete/refused | Zero on support | Timeout | Error |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for mode, counts in summary["by_mode"].items():
        out.append(
            f"| {mode} | {counts.get('certified_tolerance', 0)} | {counts.get('incomplete', 0)} | "
            f"{counts.get('zero_valid_probability_on_support', 0)} | "
            f"{counts.get('timeout', 0)} | {counts.get('error', 0)} |"
        )
    out += [
        "",
        "## Every new canvas at 64 calls (top-8 plus declared coverage support)",
        "",
        "| Canvas | Valid token paths | Full valid mass | Original omitted mass | "
        "Expected rejection draws | Generic TV bound | Coverage TV bound | "
        "True TV | Sample/update |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for e in summary["examples"]:
        out.append(
            f"| {e['case']} | {e['valid_paths']} | {number(e['full_valid_mass'])} | "
            f"{number(e['raw_omitted_mass'])} | {number(e['expected_rejection_draws'])} | "
            f"{number(e['generic_tv'])} | "
            f"{number(e['coverage_tv'])} | "
            f"{number(e['actual_tv'])} | `{e['sample']}` |"
        )
    out += [
        "",
        "## Limits and controls",
        "",
        "The rejection column is the exact mathematical expectation 1/Z for independent "
        "draws from the frozen mean-field prediction, not measured runtime or model forwards. "
        "A null value has Z=0, so no draw can succeed. No enormous sampling trial was performed. "
        "It quantifies why validity rejection can be impractical for rare constraints; the "
        "specialized exact controls can avoid it too. This is a post-hoc algebraic analysis "
        "of every new canvas, not an additional pre-registered performance experiment.",
        "",
        "The first six probes use the seven JSON-Schema type names, eight RFC9110 methods, and a "
        "declared three-license project policy. They concern format/schema "
        "admissibility, not correct "
        "type inference, selecting a safe HTTP action, or recommending a license. The "
        "follow-up uses "
        "canonical nested one-child JSON arrays (depths 1,3,8) and a genuinely recursive grammar. "
        "Its support is defined from grammar bytes, without injecting the most "
        "probable legal answer. "
        "One and two free token slots are deliberately small enough for exact "
        "independent controls; "
        "this does not demonstrate scaling to general JSON documents.",
        "",
        "The recursive protocol was developed after observing finite-catalog results. "
        "Its config was "
        "frozen before the new recursive predictions, but this is development "
        "evidence, not a held-out "
        "benchmark or twelve independent requests from a deployment population. The "
        "192 cells reuse "
        "twelve predictions across support/coverage/work limits. No selection by "
        "favorable output occurs.",
        "",
        "The specialized catalog control enumerates all one/two-token spellings using "
        "emission lookup "
        "and byte cut points. The recursive control enumerates alphabet-compatible "
        "token pairs and uses "
        "Python's JSON parser plus the one-child-list predicate. Both give exact "
        "full-vocabulary mass "
        "and true TV, including aliases. These cheap exact controls are preferable for these small "
        "instances; the generic engine is not claimed to beat them or FactorDLM, DFA "
        "inference, CARS, "
        "or the full EPIC decoder. The benefit demonstrated is an independently checkable error "
        "certificate for admission, including sound partial/refused outcomes, under "
        "arbitrary CFG ambiguity.",
        "",
        "WMC bounds, conditioning, support filters and coupling are established "
        "principles. The contribution "
        "is their explicit finite-slot/token-provenance certification and "
        "integration, with precisely scoped "
        "proofs and fresh dLLM executions. Exponential search or conservative bounds "
        "may prevent admission. "
        "A soft deadline is not a hard wall-time guarantee; proof "
        "construction/checking can exceed it.",
        "",
        "## Complete repeated-measure grid",
        "",
        "| Case | Support | Coverage | Limit | Status | Calls | Certified TV | True "
        "TV | Solve+internal check (s) | External check (s) |",
        "|---|---|---|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        out.append(
            f"| {row['case_id']} | {row['support_policy']} | {row['coverage_mode']} | "
            f"{row['oracle_limit']} | {row['status']} | {row.get('oracle_calls', '--')} | "
            f"{number(row.get('certified_full_tv'))} | {number(row.get('actual_full_tv'))} | "
            f"{row['solve_and_internal_check_seconds']:.6f} | "
            f"{row.get('portable_check_seconds', 0):.6f} |"
        )
    commits = sorted(
        {
            m["git_commit"]
            for p in summary["provenance"]
            for m in (p["capture_metadata"], p["evaluation_metadata"])
        }
    )
    out += [
        "",
        "## Provenance",
        "",
        "Producing commits: `" + "`, `".join(commits) + "`.",
        "",
        "Official MDLM-OWT checkpoint and GPT-2 tokenizer are pinned by revision and hashes; "
        "no weights are committed. CPU F32 network kernels are an audited attention/rotary port, "
        "not a bitwise GPU/FlashAttention equivalence claim. Full-vocabulary F64 softmax excludes "
        "MASK, then exact binary rationals are normalized over the whole vocabulary. "
        "Fixed positions "
        "have probability one; retained support rows are never renormalized. Full logs/logits, "
        "configurations, metadata and compact portable proofs are retained in the raw archive.",
        "",
    ]
    return "\n".join(out)


def outputs():
    r1, p1 = audit_phase(RAW / "capture", RAW / "probes")
    r2, p2 = audit_phase(RAW / "recursive_capture", RAW / "recursive_probes")
    rows = [*r1, *r2]
    summary = summarize(rows, [p1, p2])
    examples = summary["examples"]
    schema = next(e for e in examples if e["case"] == "json_schema_type-2")
    license_case = next(e for e in examples if e["case"] == "package_license_policy-2")
    mantissa, exponent = f"{float(Fraction(*license_case['expected_rejection_draws'])):.2e}".split(
        "e"
    )
    macros = {
        "MProbCanvases": str(summary["fresh_canvases"]),
        "MProbProofs": str(summary["portable_proofs"]),
        "MProbEvaluations": str(summary["evaluations"]),
        "MProbAdmitted": str(summary["status_counts"].get("certified_tolerance", 0)),
        "MProbRefused": str(summary["status_counts"].get("incomplete", 0)),
        "MProbCoverageAtLimit": str(
            sum(e["coverage_status"] == "certified_tolerance" for e in examples)
        ),
        "MProbGenericAtLimit": str(
            sum(e["generic_status"] == "certified_tolerance" for e in examples)
        ),
        "MProbSolveMedian": f"{median(e['solve_seconds'] for e in examples):.3f}",
        "MProbSchemaTV": f"{float(Fraction(*schema['coverage_tv'])):.4f}",
        "MProbLicenseRejectDraws": (
            r"\ensuremath{" + mantissa + r"\times 10^{" + str(int(exponent)) + "}}"
        ),
    }
    tex = (
        "% Generated from audited fresh MDLM archives.\n"
        + "\n".join("\\newcommand{\\" + k + "}{" + v + "}" for k, v in macros.items())
        + "\n"
    )
    return {
        PROCESSED / "summary.json": json.dumps(summary, sort_keys=True, indent=2) + "\n",
        PROCESSED / "report.md": render(summary, rows),
        GENERATED / "numbers.tex": tex,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for path, value in outputs().items():
        if args.check:
            if path.read_text() != value:
                raise ValueError(f"generated artifact differs: {path.relative_to(ROOT)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(value)
    print("PASS: all fresh predictions, frozen cells, controls, certificates and derivatives")


if __name__ == "__main__":
    main()
