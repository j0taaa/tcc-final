"""Validate every declared case and generate the bounded usefulness decision."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from string import Template

from scripts.exact_commit.build_cfg_posterior_results import load_inputs

from mwpc_exact.conflict_proof import read_state

METHOD_VARIANCE = {
    "base_iid": "two_iid",
    "single_iid": "two_iid",
    "mixture_iid": "two_iid",
    "profiles_iid": "two_iid",
    "profiles_coarse2_iid": "two_iid",
    "profiles_coarse4_iid": "two_iid",
    "base_imh_rb": "base_imh_rb",
    "single_imh_rb": "single_imh_rb",
    "conditional_mean": "conditional_mean",
}


def read_rows(folder):
    return [json.loads(line) for line in (folder / "rows.jsonl").read_text().splitlines()]


def neural(folder):
    rows = read_rows(folder)
    meta = json.loads((folder / "metadata.json").read_text())
    names = meta.get("method_names") or [
        name
        for name in METHOD_VARIANCE
        if not name.startswith("profiles_coarse")
        and (name != "profiles_iid" or meta.get("strengthened", False))
    ]
    active = {name: METHOD_VARIANCE[name] for name in names}
    assert len(meta["selected"]) == 6 and len(rows) == 156 + 432 * len(active)
    assert all(row["status"] == "complete" for row in rows)
    cases = []
    for case in meta["selected"]:
        for power in (1, 2):
            chosen = [r for r in rows if r["case"] == case["key"] and r["power"] == power]
            v = next(r for r in chosen if r["stage"] == "variance")
            baseline = [r for r in chosen if r["stage"] == "neural_cost"]
            assert len(baseline) == 12
            comparisons = {}
            for method, vname in active.items():
                extra = [r for r in chosen if r["stage"] == "extra_cost" and r["method"] == method]
                assert len(extra) == 36
                ratios = defaultdict(list)
                costs = defaultdict(list)
                for rep in range(3):
                    c = mean(
                        r["forward_seconds"][rep]
                        + r["backward_seconds"][rep]
                        + r["primitive_seconds"]
                        for r in baseline
                    )
                    warm = c + mean(
                        r["input_seconds"] + r["normalization_seconds"] for r in baseline
                    )
                    cold = warm + mean(r["compilation_seconds"] for r in baseline)
                    cpu = mean(
                        r["forward_cpu_seconds"][rep] + r["backward_cpu_seconds"][rep]
                        for r in baseline
                    )
                    marginal = mean(r["seconds"] for r in extra if r["repetition"] == rep)
                    marginal_cpu = mean(r["cpu_seconds"] for r in extra if r["repetition"] == rep)
                    factor = v["variances"][vname] / v["variances"]["original"]
                    for scope, common, added in [
                        ("neural_wall_floor", c, marginal),
                        ("warm_wall", warm, marginal),
                        ("cold_wall", cold, marginal),
                        ("neural_cpu_floor", cpu, marginal_cpu),
                    ]:
                        ratios[scope].append((1 + added / common) * factor)
                        costs[scope].append(dict(original=common, extra=added))
                comparisons[method] = dict(
                    variance_ratio=factor,
                    relative_cost_times_variance=dict(ratios),
                    costs=dict(costs),
                )
            cases.append(
                dict(
                    case=case["key"],
                    source_file=case["file"],
                    power=power,
                    mean_reward=v["mean_reward"],
                    valid_paths=v["valid_token_paths"],
                    events=v["events"],
                    observable_events=v["observable_events"],
                    variances=v["variances"],
                    target_missing=v["target_missing"],
                    comparisons=comparisons,
                )
            )
    assert len({(c["case"], c["power"]) for c in cases}) == 12
    return dict(
        producer=meta["commit"],
        configurations=cases,
        statuses=dict(Counter(r["stage"] for r in rows)),
        max_autograd_relative_norm_error=max(
            r.get("autograd_relative_norm_error", 0) for r in rows
        ),
        max_finite_difference_relative_error=max(
            r.get("relative_derivative_error", 0) for r in rows
        ),
        scope=(
            "finite population output-head gradient moments; "
            "12 native actions x3 cost repetitions; no learning curve"
        ),
    )


def iid_cost_floor(result):
    """Recompute the ideal one-replica comparison, without invented timings."""
    rows = []
    for case in result["configurations"]:
        lower = case["variances"]["two_iid"] / case["variances"]["original"]
        exact = case["comparisons"]["conditional_mean"]["relative_cost_times_variance"]
        for scope, ratios in exact.items():
            value = median(ratios)
            rows.append(
                dict(
                    case=case["case"],
                    power=case["power"],
                    scope=scope,
                    iid_zero_extra_cost_lower_bound=lower,
                    enumeration_ratio=value,
                    margin=lower - value,
                )
            )
    assert len(rows) == 48
    return dict(
        operation="one additional iid replica with the same neural cost",
        assumption="sampler preparation, draw and extra score costs are nonnegative",
        enumeration_beats_every_zero_extra_cost_floor=all(r["margin"] > 0 for r in rows),
        minimum_margin=min(r["margin"] for r in rows),
        rows=rows,
    )


def bulk(folder, prefix=False):
    rows = read_rows(folder)
    metadata = json.loads((folder / "metadata.json").read_text())
    batch_size = metadata.get("batch_size", 1024)
    if prefix:
        assert metadata["prefix_checkpoint"] == 1024
        batch_size = 1024
        rows = [dict(row, **row.get("prefix_1024", {})) for row in rows]
    runs, inputs, _ = load_inputs()
    assert {r["case"] for r in rows} == {r["case"] for r in runs["json-model"]["rows"]}
    queries = [r for r in rows if r["stage"] == "query"]
    methods = metadata.get("methods", ["mixture", "base", "single", "enumeration"])
    assert len(queries) == 144 * len(methods)
    groups = {}
    for row in queries:
        key = (row["case"], row["power"], row["k"], row["repetition"], row["method"])
        assert key not in groups
        groups[key] = row
        raw = inputs[
            next(
                r["archived_input"] for r in runs["json-model"]["rows"] if r["case"] == row["case"]
            )
        ]
        state = read_state(raw["input"])
        assert len(row["histograms"]) == len(state.canvas)
        assert row["accepted"] <= batch_size and row["attempts"] >= row["accepted"]
        if row["status"] == "complete":
            assert row["accepted"] == batch_size
        for i, h in enumerate(row["histograms"]):
            assert sum(h.values()) == row["accepted"]
            assert all(int(t) in state.support.rows[i] and count > 0 for t, count in h.items())
            fixed = state.canvas[i] if state.canvas[i] is not None else row["observed"].get(str(i))
            if fixed is not None and row["accepted"]:
                assert h == {str(fixed): row["accepted"]}
    events = sorted({key[:3] for key in groups})
    assert len(events) == 48
    comparisons = []
    for event in events:
        values = {}
        for method in methods:
            selected = [groups[(*event, rep, method)] for rep in range(3)]
            values[method] = dict(
                statuses=[r["status"] for r in selected],
                complete=all(r["status"] == "complete" for r in selected),
                seconds=[r["seconds"] for r in selected],
                cpu_seconds=[r["cpu_seconds"] for r in selected],
                cold_seconds=[
                    r["seconds"] + (0 if method == "enumeration" else r["compilation_seconds"])
                    for r in selected
                ],
                cold_cpu_seconds=[
                    r["cpu_seconds"]
                    + (0 if method == "enumeration" else r["compilation_cpu_seconds"])
                    for r in selected
                ],
                accepted=[r["accepted"] for r in selected],
                preparation_seconds=[r.get("preparation_seconds") for r in selected],
                cache_max_bits=max(r.get("cdf_integer_bits", 0) for r in selected),
            )
        mix = values["mixture"]
        controls = {m: v for m, v in values.items() if m != "mixture" and v["complete"]}
        paired = {}
        if mix["complete"]:
            for method, control in controls.items():
                paired[method] = dict(
                    wall_ratio=median(control["seconds"]) / median(mix["seconds"]),
                    cpu_ratio=median(control["cpu_seconds"]) / median(mix["cpu_seconds"]),
                    cold_wall_ratio=median(control["cold_seconds"]) / median(mix["cold_seconds"]),
                    cold_cpu_ratio=median(control["cold_cpu_seconds"])
                    / median(mix["cold_cpu_seconds"]),
                    wall_ratios=[
                        a / b for a, b in zip(control["seconds"], mix["seconds"], strict=True)
                    ],
                    cpu_ratios=[
                        a / b
                        for a, b in zip(control["cpu_seconds"], mix["cpu_seconds"], strict=True)
                    ],
                    cold_wall_ratios=[
                        a / b
                        for a, b in zip(control["cold_seconds"], mix["cold_seconds"], strict=True)
                    ],
                    cold_cpu_ratios=[
                        a / b
                        for a, b in zip(
                            control["cold_cpu_seconds"], mix["cold_cpu_seconds"], strict=True
                        )
                    ],
                )
        comparisons.append(
            dict(
                case=event[0],
                power=event[1],
                k=event[2],
                methods=values,
                paired=paired,
                mixture_faster_than_all_completed=bool(paired)
                and all(p["wall_ratio"] > 1 and p["cpu_ratio"] > 1 for p in paired.values()),
                stable_substantial_advantage=bool(paired)
                and all(
                    min(p["wall_ratio"], p["cpu_ratio"]) >= 1.25
                    and min(*p["wall_ratios"], *p["cpu_ratios"]) > 1
                    for p in paired.values()
                ),
                cold_substantial_advantage=bool(paired)
                and all(
                    min(p["cold_wall_ratio"], p["cold_cpu_ratio"]) >= 1.25
                    and min(*p["cold_wall_ratios"], *p["cold_cpu_ratios"]) > 1
                    for p in paired.values()
                ),
            )
        )
    return dict(
        producer=metadata["producer"],
        timing_design=metadata.get(
            "comparison", "Métodos rotacionados nas três repetições de uma mesma campanha."
        ),
        batch_size=batch_size,
        prefix_of_larger_campaign=prefix,
        methods=methods,
        query_count=len(queries),
        events=comparisons,
        statuses={
            method: dict(Counter(r["status"] for r in queries if r["method"] == method))
            for method in methods
        },
        compile_refusals=[r for r in rows if r["stage"] == "compile"],
        accepted_draws=sum(r["accepted"] for r in queries),
        completed_queries=sum(r["status"] == "complete" for r in queries),
        attempt_scope=(
            "Only attempts ending at recorded accepted draws; unfinished final draw "
            "counts unavailable, full failed wall/CPU costs retained"
        ),
    )


def build(args):
    n = neural(args.neural)
    floor = iid_cost_floor(n)
    assert floor["enumeration_beats_every_zero_extra_cost_floor"], (
        "The report's neural recommendation is not supported by the zero-cost bound"
    )
    b = bulk(args.bulk, args.prefix_1024)
    geometry = json.loads(args.geometry.read_text())
    assert len(geometry["verified"]) == 12
    assert {(r["case"], r["power"]) for r in geometry["verified"]} == {
        (c["case"], c["power"]) for c in n["configurations"]
    }
    assert max(max(r["errors"].values()) for r in geometry["verified"]) < 1e-7
    for filename, checksum in geometry.get("inputs", {}).items():
        assert hashlib.sha256((args.neural / filename).read_bytes()).hexdigest() == checksum
    result = dict(
        neural=n,
        iid_zero_extra_cost_decision=floor,
        bulk=b,
        independent_geometry=geometry,
        files={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in (args.neural, args.bulk)
            for p in folder.iterdir()
            if p.is_file()
        },
        limitation=(
            "CPU output-head auxiliary denoising objective; no optimizer convergence/"
            "full-model/GPU/EPIC-generation/novelty claim"
        ),
    )
    configs = n["configurations"]
    reductions = [1 - c["comparisons"]["mixture_iid"]["variance_ratio"] for c in configs]
    ratios = [
        median(c["comparisons"]["mixture_iid"]["relative_cost_times_variance"]["neural_wall_floor"])
        for c in configs
    ]
    best_rb = sum(
        median(
            c["comparisons"]["conditional_mean"]["relative_cost_times_variance"][
                "neural_wall_floor"
            ]
        )
        < min(
            median(c["comparisons"][m]["relative_cost_times_variance"]["neural_wall_floor"])
            for m in c["comparisons"]
            if m != "conditional_mean"
        )
        for c in configs
    )
    wins = [c for c in b["events"] if c["mixture_faster_than_all_completed"]]
    substantial = [c for c in b["events"] if c["stable_substantial_advantage"]]
    cold = [c for c in b["events"] if c["cold_substantial_advantage"]]
    table = [
        "| Documento / potência | Redução iid | Mistura: custo x variância / original |"
        " Enumeração: custo x variância / original |",
        "|---|---:|---:|---:|",
    ]
    for c in configs:
        values = c["comparisons"]
        mix = median(values["mixture_iid"]["relative_cost_times_variance"]["neural_wall_floor"])
        rb = median(values["conditional_mean"]["relative_cost_times_variance"]["neural_wall_floor"])
        reduction = 100 * (1 - values["mixture_iid"]["variance_ratio"])
        table.append(
            f"| {c['source_file']} / {c['power']} | {reduction:.2f}% | {mix:.4f} | {rb:.4f} |"
        )
    statuses = ["| Método | Status das 144 consultas |", "|---|---|"]
    for method, counts in b["statuses"].items():
        statuses.append(f"| {method} | {json.dumps(counts, ensure_ascii=False)} |")
    details = [
        json.dumps({k: w[k] for k in ("case", "power", "k", "paired")}, ensure_ascii=False)
        for w in wins
    ]
    text = Template((Path(__file__).parent / "utility-report.md.in").read_text()).substitute(
        min_reduction=f"{min(reductions) * 100:.2f}",
        max_reduction=f"{max(reductions) * 100:.2f}",
        min_ratio=f"{min(ratios):.4f}",
        max_ratio=f"{max(ratios):.4f}",
        rb_best=best_rb,
        norm_error=f"{n['max_autograd_relative_norm_error']:.3g}",
        derivative_error=f"{n['max_finite_difference_relative_error']:.3g}",
        table="\n".join(table),
        accepted=f"{b['accepted_draws']:,}",
        complete=b["completed_queries"],
        batch_size=b["batch_size"],
        method_count=len(b["methods"]),
        query_count=b["query_count"],
        wins=len(wins),
        substantial=len(substantial),
        cold_substantial=len(cold),
        timing_design=b["timing_design"],
        statuses="\n".join(statuses),
        winner_details="\n\n".join(details) if details else "Nenhum evento.",
    )
    with args.json.open("x") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
    with args.markdown.open("x") as stream:
        stream.write(text)
    print(
        json.dumps(
            dict(
                neural_configurations=len(configs),
                variance_reduction_range=[min(reductions), max(reductions)],
                mixture_efficiency_range=[min(ratios), max(ratios)],
                enumeration_best=best_rb,
                bulk_wins=len(wins),
                stable_substantial_wins=len(substantial),
                cold_substantial_wins=len(cold),
            )
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("neural", "bulk", "geometry", "json", "markdown"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--prefix-1024", action="store_true")
    build(parser.parse_args())
