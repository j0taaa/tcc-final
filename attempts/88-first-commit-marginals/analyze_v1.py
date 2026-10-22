"""Offline conditional moments and paired whole-replica bootstrap for A88 V1."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import itertools
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

VARIANTS = ("MC", "d0", "d1", "d2", "d4", "d8", "full", "eta.01", "eta.0001")
CANDIDATES = VARIANTS[2:]


def prefix_length(rows, name):
    if name in ("MC", "d0"):
        return 0
    if name == "full":
        return len(rows)
    if name.startswith("eta"):
        eta = float(name[3:])
        return next((i + 1 for i, row in enumerate(rows) if row["W_after"] <= eta), len(rows))
    return min(int(name[1:]), len(rows))


def path_moments(rows, name):
    """Every hit event is retained; no option renormalization or omitted tail."""
    a = np.array([r["a5"] for r in rows], dtype=float)
    w = np.array([r["W_before"] for r in rows])
    mass = np.array([r["A"] for r in rows])
    p = w * mass
    r = np.divide(a, mass[:, None], out=np.zeros_like(a), where=mass[:, None] > 0)
    y = (w[:, None] * a).sum(0)
    if not (np.all(y >= -1e-12) and abs(y.sum() - 1) < 1e-10 and abs(p.sum() - 1) < 1e-10):
        raise ValueError("non-normalized captured first-commit law")
    d = prefix_length(rows, name)
    if name == "MC":
        delta = max(0.0, 1.0 - float(y @ y))
    elif d == len(rows):
        delta = 0.0
    else:
        s = (w[:d, None] * a[:d]).sum(0)
        wd = w[d]
        z = s + wd * r[d:]
        delta = float(((p[d:] / wd) * ((z - y) ** 2).sum(1)).sum())
        if np.max(abs((p[d:, None] / wd * z).sum(0) - y)) > 1e-10:
            raise ValueError("partial variant conditional mean changed")
    visits = np.ones(len(rows))
    if d < len(rows):
        visits[d:] = w[d:] / w[d]
    kernels = np.zeros(len(rows))
    model_cost = np.zeros(len(rows))
    for t, row in enumerate(rows):
        cost = row["profile"]
        model_cost[t] = cost["model_seconds"] + cost["categorical_seconds"]
        common = sum(
            cost[k]
            for k in (
                "free_rng_seconds",
                "rank_seconds",
                "state_seconds",
                "cache_seconds",
            )
        )
        if t < d:
            kernels[t] = (
                common + cost["canvas_seconds"] + cost["a5_seconds"] + cost["update_seconds"]
            )
        else:
            kernels[t] = common + cost["f_rng_seconds"] + (1 - mass[t]) * cost["canvas_seconds"]
            if name != "MC":
                kernels[t] += mass[t] * (cost["a5_seconds"] + cost["update_seconds"])
    # Final product output once per independent replica; trace serialization is research overhead.
    output = np.mean(
        [
            r["profile"]["token_output_seconds" if name == "MC" else "vector_output_seconds"]
            for r in rows
        ]
    )
    return {
        "Y": y,
        "delta": delta,
        "visits": visits,
        "kernel_cost": visits * kernels,
        "model_cost": model_cost,
        "output": float(output),
        "d": d,
        "hits": p,
        "R": r,
    }


def unbiased_iid_product(ys, deltas, costs):
    """Distinct-third-replica U statistic, including cross-replica delta*cost."""
    n = len(ys)
    pair = [
        (float(np.sum((ys[i] - ys[j]) ** 2)) / 2, i, j) for i in range(n) for j in range(i + 1, n)
    ]
    between = np.mean(
        [distance * costs[k] for distance, i, j in pair for k in range(n) if k not in (i, j)]
    )
    within = np.mean([deltas[i] * costs[k] for i in range(n) for k in range(n) if i != k])
    return float(between + within)


def evaluate(paths, name, setup_per_case, summaries=None):
    if summaries is None:
        summaries = [path_moments(rows, name) for rows in paths]
    ys = np.array([s["Y"] for s in summaries])
    deltas = np.array([s["delta"] for s in summaries])
    variance = float(ys.var(axis=0, ddof=1).sum() + deltas.mean())
    # Root is shared ONCE, including in each bootstrap sample. Nonroot costs below
    # are a no-nonroot-cache comparator, then the optimistic global cache.
    root_cost = float(np.mean([s["model_cost"][0] for s in summaries]))
    iid_costs = np.array(
        [
            root_cost / len(paths)
            + setup_per_case / len(paths)
            + s["output"]
            + s["kernel_cost"].sum()
            + (s["visits"][1:] * s["model_cost"][1:]).sum()
            for s in summaries
        ]
    )
    states = defaultdict(list)
    kernels = sum(float(s["kernel_cost"].sum() + s["output"]) for s in summaries)
    for rows, summary in zip(paths, summaries, strict=True):
        for i, row in enumerate(rows):
            states[row["state_hash"]].append(
                (float(summary["visits"][i]), float(summary["model_cost"][i]))
            )
    unique_queries, global_model = 0.0, 0.0
    for entries in states.values():
        # At most one visit to any (canvas, public time) state per path. Separate
        # native stopping coins are independent between replicas, conditional on paths.
        probability = 1.0 - float(np.prod([1.0 - p for p, _ in entries]))
        unique_queries += probability
        global_model += probability * float(np.mean([c for _, c in entries]))
    block_cost = setup_per_case + global_model + kernels
    mean_cost = block_cost / len(paths)
    return {
        "variance_trace": variance,
        "conditional_delta_mean": float(deltas.mean()),
        "between_Y_sample_variance": float(ys.var(axis=0, ddof=1).sum()),
        "mean_Y5": ys.mean(0).tolist(),
        "mean_prefix_steps": float(np.mean([s["d"] for s in summaries])),
        "mean_logical_steps": float(np.mean([s["visits"].sum() for s in summaries])),
        "expected_unique_model_queries_block": unique_queries,
        "global_cache_model_seconds_block": global_model,
        "kernel_output_seconds_block": kernels,
        "global_cache_cost_seconds_block": block_cost,
        "mean_cost_seconds": mean_cost,
        "variance_times_cost_exploratory": variance * mean_cost,
        "root_only_cost_seconds_block": float(iid_costs.sum()),
        "root_only_distinct_replica_U_product": unbiased_iid_product(ys, deltas, iid_costs),
        "zero_empirical_variance_inconclusive": variance <= 1e-15,
    }


def audit_capture(records, inputs):
    begin, steps, complete, roots = {}, defaultdict(list), {}, {}
    terminals = [r for r in records if r["type"] == "terminal"]
    if len(terminals) != 1:
        raise ValueError("exactly one retained terminal required")
    for row in records:
        if row["type"] == "query_begin":
            if row["call"] in begin:
                raise ValueError("duplicate physical call number")
            begin[row["call"]] = row
        elif row["type"] == "step":
            steps[row["case"], row["replica"]].append(row)
        elif row["type"] == "replica_complete":
            complete[row["case"], row["replica"]] = row
        elif row["type"] == "root":
            roots[row["case"]] = row
    if len(begin) > 968 or sum(map(len, steps.values())) > 1024:
        raise ValueError("capture exceeded preregistered ceiling")
    # Reconstruct every exact canvas independently of the capture's evolving list.
    import native_v1 as native

    max_errors = defaultdict(float)
    for key, rows in steps.items():
        case, replica = key
        item = inputs["cases"][case]
        canvas = item["input_ids"].copy()
        w = 1.0
        first = None
        y = np.zeros(5)
        for t, row in enumerate(rows):
            if row["step"] != t or row["seed"] != 880001 + 1000 * case + replica:
                raise ValueError("step/seed changed")
            if (
                row["state_hash"] != native.state_hash(canvas, t)
                or begin[row["query_call"]]["state_hash"] != row["state_hash"]
            ):
                raise ValueError("state hash not reconstructible")
            eligible = [p for p in item["eligible"] if canvas[p] == native.MASK]
            selected = row["free_commit_positions"]
            tokens = row["free_commit_ids"]
            if (
                row["eligible_positions"] != eligible
                or item["observed"] in selected
                or len(set(selected)) != len(selected)
                or len(tokens) != len(selected)
                or any(p not in eligible for p in selected)
                or any(not 0 <= token < native.VOCAB or token == native.MASK for token in tokens)
                or len(selected) != (0 if row["forced"] else 2)
            ):
                raise ValueError("invalid irreversible free commits")
            a5 = np.array(row["a5"])
            q5 = np.array(row["qf5"])
            if (
                abs(q5.sum() - 1) > 1e-10
                or np.any(a5 < -1e-12)
                or np.any(a5 > q5 + 1e-12)
                or abs(a5.sum() - row["A"]) > 1e-10
                or abs(w - row["W_before"]) > 1e-12
                or abs(w * row["b"] - row["W_after"]) > 1e-12
            ):
                raise ValueError("invalid complete five-bin deposit")
            y += w * a5
            w = row["W_after"]
            for pos, token in zip(selected, tokens, strict=True):
                canvas[pos] = token
            if first is None and row["f_selected"]:
                first = {
                    "step": t,
                    "token": row["f_proposal"],
                    "group": inputs["groups"][row["f_proposal"]],
                }
            for name, value in row["numeric"].items():
                max_errors[name] = max(max_errors[name], value)
        if key in complete:
            claimed = complete[key]
            if w != 0 or np.max(abs(y - claimed["Y5"])) > 1e-10 or first is None:
                raise ValueError("incomplete/incorrect terminal vector")
            if any(claimed["native_first_hit"][k] != v for k, v in first.items()):
                raise ValueError("native first-hit record changed")
            # Covariance monotonicity for fixed nested budgets, independently reconstructed.
            deltas = [
                path_moments(rows, n)["delta"] for n in ("MC", "d0", "d1", "d2", "d4", "d8", "full")
            ]
            if any(left + 1e-10 < right for left, right in itertools.pairwise(deltas)):
                raise ValueError("conditional variance sandwich failed")
    if terminals[0]["status"] == "COMPLETE" and (len(complete) != 64 or len(roots) != 8):
        raise ValueError("COMPLETE without all fixed rows/replicas")
    return (
        steps,
        complete,
        {
            "physical_model_calls": len(begin),
            "logical_steps": sum(map(len, steps.values())),
            "completed_replicas": len(complete),
            "roots": len(roots),
            "terminal": terminals[0],
            "max_numeric_diagnostics": dict(max_errors),
        },
    )


def analyze(records, inputs, bootstrap):
    paths, complete, audit = audit_capture(records, inputs)
    producer = next((r for r in records if r["type"] == "producer"), {})
    setup_parts = {
        "input_source_preparation": producer.get("prepare_seconds", 0),
        "source_reverification": sum(
            r["wall_seconds"] for r in records if r["type"] == "model_verification"
        ),
        "load": sum(r["wall_seconds"] for r in records if r["type"] == "load"),
    }
    setup = sum(setup_parts.values()) / 8
    result = {
        "schema": "A88-analysis-v1",
        "source_commit": producer.get("commit"),
        "audit": audit,
        "bootstrap": {
            "replicates": bootstrap,
            "seed": 888801,
            "unit": "whole independent auxiliary replica, paired between methods",
            "interval": "percentile 2.5/97.5%; exploratory, N=8, no multiplicity correction",
        },
        "setup_seconds": setup_parts,
        "cost_status": "MODELED_REPLAY_NOT_END_TO_END_DECODER_LATENCY",
        "cases": [],
        "gate": {},
    }
    rng = np.random.default_rng(888801)
    for case in range(8):
        keys = [(case, r) for r in range(8)]
        if any(k not in complete for k in keys):
            result["cases"].append({"case": case, "status": "INCOMPLETE_NO_REPLACEMENT"})
            continue
        rows = [paths[k] for k in keys]
        summaries = {name: [path_moments(r, name) for r in rows] for name in VARIANTS}
        methods = {name: evaluate(rows, name, setup, summaries[name]) for name in VARIANTS}
        distributions = {name: [] for name in CANDIDATES}
        for _ in range(bootstrap):
            indices = rng.integers(0, 8, 8)
            sample = [rows[int(i)] for i in indices]
            replay = {
                name: evaluate(sample, name, setup, [summaries[name][int(i)] for i in indices])
                for name in VARIANTS
            }
            for name in CANDIDATES:
                v = replay[name]["variance_times_cost_exploratory"]
                comparisons = [replay[c]["variance_times_cost_exploratory"] for c in ("MC", "d0")]
                distributions[name].append(
                    [1 - v / c if c > 1e-15 else float("nan") for c in comparisons]
                )
        for name in CANDIDATES:
            metric = methods[name]["variance_times_cost_exploratory"]
            advantages = {
                c: (
                    1 - metric / methods[c]["variance_times_cost_exploratory"]
                    if methods[c]["variance_times_cost_exploratory"] > 1e-15
                    else None
                )
                for c in ("MC", "d0")
            }
            boot = np.array(distributions[name])
            cis = {}
            for j, c in enumerate(("MC", "d0")):
                valid = boot[:, j][np.isfinite(boot[:, j])]
                cis[c] = {
                    "interval": np.quantile(valid, [0.025, 0.975]).tolist() if len(valid) else None,
                    "valid_resamples": len(valid),
                    "total": bootstrap,
                }
            methods[name]["advantage_vs_controls"] = advantages
            methods[name]["paired_95pct_exploratory"] = cis
            methods[name]["material_point_advantage_both"] = not methods[name][
                "zero_empirical_variance_inconclusive"
            ] and all(value is not None and value >= 0.1 for value in advantages.values())
        mu = methods["full"]["mean_Y5"]
        result["cases"].append(
            {
                "case": case,
                "row": inputs["cases"][case]["row"],
                "subject": inputs["cases"][case]["subject"],
                "mean_Y5": mu,
                "useful_option_mass": sum(mu[:4]),
                "mass_gate": sum(mu[:4]) >= 0.9,
                "status": "ANALYZED",
                "methods": methods,
            }
        )
    analyzed = [c for c in result["cases"] if c["status"] == "ANALYZED"]
    coverage = sum(c["mass_gate"] for c in analyzed)
    wins = {
        name: sum(c["methods"][name]["material_point_advantage_both"] for c in analyzed)
        for name in CANDIDATES
    }
    selected = [n for n, count in wins.items() if count >= 6]
    if audit["terminal"]["status"] != "COMPLETE" or len(analyzed) != 8:
        decision = "INCONCLUSIVE_RESOURCE_OR_CAPTURE_FAILURE"
    elif coverage < 6 or not selected:
        decision = "NEGATIVE_DEVELOPMENT_QUALIFIER"
    else:
        decision = "POSITIVE_MODELED_DEVELOPMENT_SCREEN_ONLY_END_TO_END_COST_UNQUALIFIED"
    result["gate"] = {
        "option_mass_items_ge_0.9": coverage,
        "required_items": 6,
        "material_wins_both_by_variant": wins,
        "eligible_for_future_protocol": selected if coverage >= 6 else [],
        "decision": decision,
        "central_contribution_validated": False,
        "warning": (
            "Development selection and uncertainty only; shared global-cache costs "
            "are block nonlinear, not iid. No wall-time theorem or independent confirmation."
        ),
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument(
        "--inputs", type=Path, default=Path(__file__).with_name("native-inputs-v1.json")
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bootstrap", type=int, default=2000)
    args = parser.parse_args()
    started = time.perf_counter()
    raw = args.capture.read_bytes()
    decoded = gzip.decompress(raw) if args.capture.suffix == ".gz" else raw
    records = [json.loads(line) for line in decoded.splitlines()]
    result = analyze(records, json.loads(args.inputs.read_text()), args.bootstrap)
    result["capture_sha256"] = hashlib.sha256(raw).hexdigest()
    result["uncompressed_capture_sha256"] = hashlib.sha256(decoded).hexdigest()
    result["inputs_sha256"] = hashlib.sha256(args.inputs.read_bytes()).hexdigest()
    result["offline_analysis_seconds"] = time.perf_counter() - started
    with args.output.open("x") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(
        json.dumps(
            {
                "output": str(args.output),
                "audit": result["audit"],
                "gate": result["gate"],
                "seconds": result["offline_analysis_seconds"],
            }
        )
    )


if __name__ == "__main__":
    main()
