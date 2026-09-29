#!/usr/bin/env python3
"""Paired confirmation report; repeated executions are not independent tasks."""

import argparse
import json
from math import comb
from pathlib import Path
from random import Random
from statistics import median

from summarize_policy_screen import read


def binomial_interval(count, n):
    """97.5% exact binomial interval; two intervals give conservative 95% joint coverage."""
    alpha = 0.0125

    def cdf(k, p):
        return sum(comb(n, j) * p**j * (1 - p) ** (n - j) for j in range(k + 1))

    lower, upper = 0.0, 1.0
    if count:
        lo, hi = 0.0, 1.0
        for _ in range(70):
            mid = (lo + hi) / 2
            if 1 - cdf(count - 1, mid) < alpha:
                lo = mid
            else:
                hi = mid
        lower = (lo + hi) / 2
    if count < n:
        lo, hi = 0.0, 1.0
        for _ in range(70):
            mid = (lo + hi) / 2
            if cdf(count, mid) > alpha:
                lo = mid
            else:
                hi = mid
        upper = (lo + hi) / 2
    return lower, upper


def build(
    first,
    second,
    secondary_first=None,
    secondary_second=None,
    controls_first=None,
    controls_second=None,
    *,
    comparator_override=None,
):
    config, a = read(first)
    config_b, b = read(second)
    assert config["tasks"] == config_b["tasks"]
    assert sorted(p["name"] for p in config["policies"]) == sorted(
        p["name"] for p in config_b["policies"]
    )
    primary_names = {p["name"] for p in config["policies"]}
    policies = list(config["policies"])
    for extra_first, extra_second in (
        (secondary_first, secondary_second),
        (controls_first, controls_second),
    ):
        if (extra_first is None) != (extra_second is None):
            raise ValueError("Both repetitions are required for each additional cohort")
        if extra_first is None:
            continue
        extra_config, extra_a = read(extra_first)
        extra_config_b, extra_b = read(extra_second)
        assert extra_config["tasks"] == extra_config_b["tasks"] == config["tasks"]
        extra_names = {p["name"] for p in extra_config["policies"]}
        assert extra_names == {p["name"] for p in extra_config_b["policies"]}
        assert not {p["name"] for p in policies} & extra_names
        policies += extra_config["policies"]
        a += extra_a
        b += extra_b
    maps = [{(r["task"]["id"], r["method"]): r for r in rows} for rows in (a, b)]
    ids = [t["id"] for t in config["tasks"]]
    table, pairs = [], {}
    is_schema = config.get("schema_calls", False)
    is_grounded = config.get("grounded_calls", False)
    comparator = comparator_override or config.get("primary_comparator", "epic_lexical_24")
    for policy in policies:
        name = policy["name"]
        repetitions = [[m[tid, name] for tid in ids] for m in maps]
        total = [median(m[tid, name]["total_seconds_including_setup"] for m in maps) for tid in ids]
        base = [
            median(m[tid, comparator]["total_seconds_including_setup"] for m in maps) for tid in ids
        ]
        ratios = [x / y for x, y in zip(base, total, strict=True)]
        diffs = [
            int(maps[0][tid, name]["correct"]) - int(maps[0][tid, comparator]["correct"])
            for tid in ids
        ]
        wins, losses = diffs.count(1), diffs.count(-1)
        discordant = wins + losses
        win_ci, loss_ci = binomial_interval(wins, len(ids)), binomial_interval(losses, len(ids))
        p = min(
            1.0, 2 * sum(comb(discordant, k) for k in range(min(wins, losses) + 1)) / 2**discordant
        )
        rng = Random(240999)
        acc_boot, speed_boot = [], []
        for _ in range(2000):
            selected = [rng.randrange(len(ids)) for _ in ids]
            acc_boot.append(100 * sum(diffs[i] for i in selected) / len(ids))
            speed_boot.append(median(ratios[i] for i in selected))
        acc_boot.sort()
        speed_boot.sort()
        pairs[name] = {
            "comparator": comparator,
            "wins_first_repeat": wins,
            "losses_first_repeat": losses,
            "mcnemar_exact_two_sided": p,
            "accuracy_difference_pp": 100 * sum(diffs) / len(ids),
            "paired_accuracy_conservative95_pp": [
                100 * (win_ci[0] - loss_ci[1]),
                100 * (win_ci[1] - loss_ci[0]),
            ],
            "accuracy_difference_bootstrap95_pp": [acc_boot[50], acc_boot[1949]],
            "median_paired_speed_ratio": median(ratios),
            "speed_ratio_bootstrap95": [speed_boot[50], speed_boot[1949]],
            "bootstrap_seed": 240999,
            "bootstrap_replicates": 2000,
        }
        table.append(
            {
                "method": name,
                "analysis": (
                    "external_grounded_confirmation"
                    if is_grounded
                    else ("external_pilot" if is_schema else "frozen_confirmation")
                )
                if name in primary_names
                else "secondary_ablation",
                "n": len(ids),
                "correct": [sum(r["correct"] for r in rows) for rows in repetitions],
                "numeric_correct": None
                if is_schema
                else [sum(r["numeric_correct"] is True for r in rows) for rows in repetitions],
                "valid": [sum(r["syntax_valid"] for r in rows) for rows in repetitions],
                "forwards": [sum(r["forwards"] for r in rows) for rows in repetitions],
                "median_total_ms": 1000 * median(total),
                "p95_total_ms": 1000 * sorted(total)[min(len(total) - 1, int(0.95 * len(total)))],
                "changed_outputs_between_repeats": sum(
                    maps[0][tid, name]["output"] != maps[1][tid, name]["output"] for tid in ids
                ),
            }
        )
    table.sort(key=lambda r: (-r["correct"][0], r["median_total_ms"]))
    result = {
        "source_commits": sorted({r["git_commit"] for r in a + b}),
        "unique_requests": len(ids),
        "records": len(a) + len(b),
        "primary_method": config.get("primary_method"),
        "table": table,
        "paired_comparisons": pairs,
        "comparator": comparator,
        "frozen_primary_comparator": config.get("primary_comparator"),
        "comparison_role": "secondary"
        if (is_schema and not is_grounded) or comparator_override
        else "frozen_primary",
        "scope": (
            "family-disjoint public BFCL scalar queries; question/schema-derived finite support; "
            "own strict AST evaluator, not official BFCL score; all selected cases retained; "
            "two timing repetitions, not independent samples; secondary CIs unadjusted"
        )
        if is_grounded
        else (
            "eight schema-finite public BFCL cases; own strict AST evaluator, not official "
            "BFCL score; two repetitions, not independent samples; exploratory CIs"
        )
        if is_schema
        else (
            "same synthetic calculator templates; two timing repetitions, not independent "
            "samples; CIs unadjusted across secondary comparisons"
        ),
    }
    lines = [
        "# M25 — confirmação externa pareada"
        if is_grounded
        else ("# M24 — piloto externo pareado" if is_schema else "# M24 — confirmação pareada"),
        "",
        result["scope"],
        "",
        "| Método | Chamadas corretas 1 / 2 | Resultado numérico 1 / 2 | "
        "Forwards 1 / 2 | Mediana total (ms) | p95 (ms) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in table:
        numeric = (
            "não se aplica"
            if r["numeric_correct"] is None
            else f"{r['numeric_correct'][0]} / {r['numeric_correct'][1]}"
        )
        lines.append(
            f"| {r['method']} | {r['correct'][0]} / {r['correct'][1]} de {r['n']} | "
            f"{numeric} | "
            f"{r['forwards'][0]} / {r['forwards'][1]} | "
            f"{r['median_total_ms']:.1f} | {r['p95_total_ms']:.1f} |"
        )
    lines += [
        "",
        "Tempos incluem preparação e recuperação; "
        "duas medições agregadas por pedido antes da mediana.",
        "Comparações pareadas e intervalos estão no JSON; bootstrap por pedido, não por execução.",
        "A repetição não aumenta o número de tarefas independentes; "
        "diferenças secundárias não têm ajuste por multiplicidade.",
    ]
    return result, "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("first", type=Path)
    parser.add_argument("second", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--secondary-first", type=Path)
    parser.add_argument("--secondary-second", type=Path)
    parser.add_argument("--controls-first", type=Path)
    parser.add_argument("--controls-second", type=Path)
    parser.add_argument(
        "--comparator", help="Secondary comparison; never alters the frozen primary"
    )
    args = parser.parse_args()
    result, report = build(
        args.first,
        args.second,
        args.secondary_first,
        args.secondary_second,
        args.controls_first,
        args.controls_second,
        comparator_override=args.comparator,
    )
    for path, text in ((args.output, json.dumps(result, indent=2) + "\n"), (args.report, report)):
        if args.check:
            assert path.read_text() == text
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    print(report)


if __name__ == "__main__":
    main()
