"""Frozen development-only conditional moment tables; no population claim."""

import argparse
import itertools
import json
from pathlib import Path

import numpy as np

from .conditional_probe_v18 import BLOCKS, paired_conditional_trace, select_family
from .consumer_resource import serial, write_json

METHODS = (
    "full_triple",
    "anchor_integrated",
    "class_integrated",
    "length_integrated",
    "combined_partial",
    "known_anchor",
    "collapsed",
)
BASELINES = ("zero", "half", "proxy_state", "proxy_root")
COEFFICIENTS = tuple(itertools.product((0.0, 0.5, 1.0), repeat=3))


def queries(method, baseline, coef, variant):
    result = set()
    if method in ("collapsed", "length_integrated", "combined_partial") or variant != "iid1":
        result.add("base_action")
    if method == "known_anchor":
        result.add("anchor_conditioned")
    if coef[0]:
        result.update(("base_action", "proxy_action"))
    if baseline == "proxy_state":
        result.add("proxy_prior")
    if baseline == "proxy_root":
        result.add("proxy_root_prior")
    return sorted(result)


def run(capture, output):
    output.mkdir(parents=True, exist_ok=False)
    summary = json.loads((capture / "summary.json").read_text())
    if summary["status"] != "PASS":
        write_json(
            output / "summary.json",
            {"status": "NEGATIVE_RESOURCE_INCOMPLETE", "original_summary": summary},
        )
        return
    preparations = json.loads((capture / "preparations.json").read_text())
    records = [json.loads(x) for x in (capture / "records.jsonl").read_text().splitlines()]
    if len(preparations) != 70 or len(records) != 8960:
        raise ValueError("ALL70 states/8960 auxiliaries required")
    preps = {(r["case"], r["replica"], r["step"]): r for r in preparations}
    score = np.zeros((2, 16, 64, 7, 9))
    baseline = np.zeros((2, 16, 64, 7, 4, 9))
    semantic_full = np.zeros((2, 16, 64, 9))
    semantic_anchor = np.zeros_like(semantic_full)
    regular, rewards = np.zeros((16, 9)), np.full(16, np.nan)
    certificates, seen = 0, set()
    for p in preparations:
        path = 2 * p["case"] + p["replica"]
        reward = float(p["old_final_reward"])
        if np.isfinite(rewards[path]) and rewards[path] != reward:
            raise ValueError("old path reward differs across states")
        rewards[path] = reward
        certificates += int(p["tail_certificate"])
        if not p["tail_certificate"]:
            regular[path] += p["C_regular_actor"]
    for r in records:
        key = r["case"], r["replica"], r["step"]
        p = preps[key]
        mode = int(r["method"] == "prefix_stratified")
        index, path = r["draw_index"], 2 * r["case"] + r["replica"]
        fullkey = (*key, mode, index)
        if fullkey in seen or r["status"] != "PASS" or r["head"] != p["head"]:
            raise ValueError("duplicated/failed/mismatched original state")
        if not 0 <= index < 64 or index != r["batch"] * 8 + r["within_batch"]:
            raise ValueError("conditional batch index differs")
        seen.add(fullkey)
        if set(r["actor_scores"]) != set(METHODS):
            raise ValueError("all seven score methods required")
        if p["tail_certificate"]:
            continue
        v = np.asarray([r["actor_scores"][m] for m in METHODS])
        if v.shape != (7, 9) or not np.isfinite(v).all():
            raise ValueError("finite fixed nine-coordinate actor required")
        score[mode, path, index] += v
        baseline[mode, path, index] += np.asarray(p["baselines"])[None, :, None] * v[:, None, :]
        semantic_full[mode, path, index] += r["semantic_correct_proposal"] * v[0]
        semantic_anchor[mode, path, index] += r["semantic_correct_proposal"] * v[1]
    if not np.isfinite(rewards).all() or len(seen) != 8960:
        raise ValueError("incomplete path rewards/auxiliaries")
    np.savez_compressed(
        output / "path-sufficient-statistics.npz",
        score=score,
        baseline=baseline,
        semantic_full=semantic_full,
        semantic_anchor=semantic_anchor,
        regular=regular,
        rewards=rewards,
    )
    table, rloo = [], []
    with (output / "ALL756-moment-details.jsonl").open("x") as stream:
        for method_index, baseline_index, coef in itertools.product(
            range(7), range(4), COEFFICIENTS
        ):
            gradients = (
                rewards[None, :, None, None] * score[:, :, :, method_index]
                - baseline[:, :, :, method_index, baseline_index]
                - coef[0] * regular[None, :, None, :]
                - coef[1] * semantic_full
                - coef[2] * semantic_anchor
            )
            moments = {
                q: paired_conditional_trace(
                    gradients[0, 2 * q],
                    gradients[0, 2 * q + 1],
                    gradients[1, 2 * q].reshape(8, 8, 9).mean(1),
                    gradients[1, 2 * q + 1].reshape(8, 8, 9).mean(1),
                    8,
                )
                for q in range(8)
            }
            aggregate = {
                block: {
                    key: sum(m[block][key] for m in moments.values()) / 64
                    for key in moments[0][block]
                }
                for block in BLOCKS
            }
            common = {
                "method": METHODS[method_index],
                "baseline": BASELINES[baseline_index],
                "coefficients": coef,
            }
            stream.write(
                json.dumps({**common, "by_question": moments, "aggregate": aggregate}) + "\n"
            )
            for variant, field in (
                ("iid1", "iid1"),
                ("iid8", "iid_batch"),
                ("prefix_stratified8", "stratified_batch"),
            ):
                table.append(
                    {
                        **common,
                        "variant": variant,
                        "estimate": aggregate["total"][field],
                        "actor_blocks": {b: aggregate[b][field] for b in BLOCKS},
                        "aggregate_mean_gap_u": aggregate["total"]["mean_gap_u_estimate"],
                        "aggregate_mean_gap_cross": aggregate["total"]["mean_gap_cross_estimate"],
                        "query_types": queries(common["method"], common["baseline"], coef, variant),
                        "draw_count": 1 if variant == "iid1" else 8,
                    }
                )
    # RLOO conditional auxiliary noise is filled below; total variance stays null.
    for method_index, coef in itertools.product(range(7), COEFFICIENTS):
        contexts = []
        for q in range(8):
            a, b = 2 * q, 2 * q + 1
            group = (
                (rewards[a] - rewards[b])
                * (score[:, a, :, method_index] - score[:, b, :, method_index])
                - coef[0] * (regular[a] + regular[b])[None, None, :]
                - coef[1] * (semantic_full[:, a] + semantic_full[:, b])
                - coef[2] * (semantic_anchor[:, a] + semantic_anchor[:, b])
            ) / 2
            iid_noise = group[0].var(0, ddof=1)
            strat_noise = group[1].reshape(8, 8, 9).mean(1).var(0, ddof=1)
            contexts.append(
                {
                    "case": q,
                    "conditional_auxiliary_noise": {
                        block: {
                            "iid1": float(iid_noise[s].sum()),
                            "iid8": float(iid_noise[s].sum() / 8),
                            "prefix_stratified8": float(strat_noise[s].sum()),
                        }
                        for block, s in BLOCKS.items()
                    },
                }
            )
        rloo.append(
            {
                "method": METHODS[method_index],
                "coefficients": coef,
                "full_unconditional_variance": None,
                "independent_visible_groups_per_question": 1,
                "conditional_contexts": contexts,
            }
        )
    write_json(output / "ALL2268-estimates.json", serial(table))
    write_json(output / "RLOO-conditional-noise-NOT-total-variance.json", serial(rloo))
    single = [e for e in table if e["variant"] == "iid1"]
    family_a = select_family(
        [e for e in single if e["method"] == "collapsed"],
        [e for e in single if e["method"] != "collapsed"],
    )
    family_b = select_family([e for e in table if e["variant"] == "prefix_stratified8"], single)
    result = {
        "status": "DEVELOPMENT_ANALYSIS_COMPLETE",
        "scope": "conditional audit of SAME16 known paths; not independent evaluation",
        "table_entries": len(table),
        "states": 70,
        "auxiliary_words": 8960,
        "tail_certified_pre_states": certificates,
        "family_A": family_a,
        "family_B": family_b,
        "new_model_forwards": 0,
        "updates": 0,
        "full_RLOO_variance": None,
        "negative_estimates_retained": sum(e["estimate"] < 0 for e in table),
        "full_cost_or_population_superiority_claim": False,
    }
    write_json(output / "summary.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--capture", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    run(a.capture, a.output)
