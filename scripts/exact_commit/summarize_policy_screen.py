#!/usr/bin/env python3
"""Independently validate M24 records and generate the complete policy table."""

import argparse
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from math import fsum, isclose
from pathlib import Path
from statistics import median

from mwpc_research.schema_calls import normalize_schema_call, schema_catalog, strict_schema_grade
from mwpc_research.tool_screen import (
    execute_tool_call,
    normalize_tool_call,
    operand_preserving_indices,
)


def read(directory):
    if (directory / "manifest.json").exists():
        manifest = json.loads((directory / "manifest.json").read_text())
        for name, checksum in manifest["sha256"].items():
            assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == checksum, name
    cfg_bytes = (directory / "config.json").read_bytes()
    config = json.loads(cfg_bytes)
    support = json.loads((directory / "support.json").read_text())
    emissions = {
        int(t): bytes(b)
        for t, b in json.loads((directory / "token_emissions.json").read_text()).items()
    }
    path = directory / "results.jsonl"
    raw = (
        path.read_bytes()
        if path.exists()
        else gzip.decompress((directory / "results.jsonl.gz").read_bytes())
    )
    records = [json.loads(line) for line in raw.splitlines()]
    tasks = {t["id"]: t for t in config["tasks"]}
    policies = {p["name"]: p for p in config["policies"]}
    seen = set()

    def decoded(tokens):
        assert len(tokens) == config["slots"]
        end = tokens.index(126081)
        assert all(t == 126081 for t in tokens[end:])
        return b"".join(emissions[t] for t in tokens[:end]).decode()

    for row in records:
        task, policy = row["task"], row["policy"]
        assert task == tasks[task["id"]] and policy == policies[row["method"]]
        key = task["id"], row["method"]
        assert key not in seen
        seen.add(key)
        assert row["config_sha256"] == hashlib.sha256(cfg_bytes).hexdigest()
        is_schema = config.get("schema_calls", False)
        indices = (
            [support["catalog"].index(call) for call in schema_catalog(task["function"])]
            if is_schema
            else list(operand_preserving_indices(support["catalog"], task["instruction"]))
        )
        assert row["active_catalog_indices"] == indices
        calls = [support["catalog"][i] for i in indices]
        paths = [support["paths"][i] for i in indices]
        domains = [set(path[p] for path in paths) for p in range(config["slots"])]
        assert row["active_grammar_hash"] == hashlib.sha256(json.dumps(calls).encode()).hexdigest()
        normal = (normalize_schema_call if is_schema else normalize_tool_call)(row["output"])
        complete = row["status"] == "complete"
        assert row["correct"] == (
            complete
            and (
                strict_schema_grade(row["output"], task["function"], task["ground_truth"])
                if is_schema
                else normal == task["expected"]
            )
        )
        assert row["syntax_valid"] == (complete and normal in calls)
        assert row["numeric_correct"] == (
            None
            if is_schema
            else (
                complete
                and normal in calls
                and execute_tool_call(normal) == execute_tool_call(task["expected"])
            )
        )
        assert row["total_seconds_including_setup"] >= row["elapsed_seconds"] >= 0
        if policy["kind"] == "epic":
            assert row["recovery_status"] != "disabled"
            assert row["epic_steps"] == int(policy["method"].rsplit("_", 1)[1])
            assert row["proposal_support"] == "native_vocabulary"
            if row["recovery_status"] == "recovered":
                import re

                words = {int(t): bytes(b).decode() for t, b in row["token_emissions"].items()}
                pieces = []
                for t in row["token_ids"]:
                    if t in (126081, 126348):
                        break
                    pieces.append(".*" if t == 126336 else re.escape(words[t]))
                if not any(t in (126081, 126348) for t in row["token_ids"]):
                    pieces.append(".*")
                assert re.fullmatch("".join(pieces), row["output"], re.DOTALL)
            continue
        phases = ([row["draft"]] if "draft" in row else []) + [row]
        for phase in phases:
            canvas = [None] * config["slots"]
            for step in phase["trace"]:
                assert step["canvas_before"] == canvas
                witness = step["witness_token_ids"]
                assert decoded(witness) in calls
                assert all(t in domains[p] for p, t in enumerate(witness))
                assert all(t is None or t == witness[p] for p, t in enumerate(canvas))
                proposals = step["proposals"]
                native = step["production_result"]
                if native is not None:
                    matched = [
                        i for i, (p, t, w) in enumerate(proposals) if w > 0 and witness[p] == t
                    ]
                    score = fsum(w for p, t, w in proposals if witness[p] == t)
                    assert set(native["selected_proposal_ids"]) == set(matched)
                    assert isclose(native["score"], score, abs_tol=1e-9)
                    assert native["witness_token_ids"] == witness
                    assert native["status"] == (
                        "feasible_on_support"
                        if policy["kind"] == "greedy" or policy.get("selector") == "greedy"
                        else "optimal"
                    )
                gate = step["gate"]
                if gate:
                    assert gate["status"] == "optimal"
                    weight = fsum(w for _, _, w in proposals)
                    bonus = weight + max(1.0, weight)
                    expected_certified = []
                    for query in gate["queries"]:
                        other = query["result"]["witness_token_ids"]
                        assert decoded(other) in calls
                        assert all(t in domains[p] for p, t in enumerate(other))
                        assert all(t is None or t == other[p] for p, t in enumerate(canvas))
                        forced = other[query["position"]] == witness[query["position"]]
                        assert query["forced"] == forced
                        original = fsum(w for p, t, w in proposals if other[p] == t)
                        assert isclose(
                            query["result"]["score"],
                            original + (0 if forced else bonus),
                            abs_tol=1e-8,
                        )
                        if not forced:
                            assert isclose(query["alternative_score"], original, abs_tol=1e-9)
                            assert isclose(
                                query["margin"], native["score"] - original, abs_tol=1e-9
                            )
                        if forced or query["margin"] > policy[
                            "relative_tolerance"
                        ] * weight + 1e-10 * max(1, weight):
                            expected_certified.append(query["position"])
                    assert gate["certified_positions"] == expected_certified
                    assert gate["progress_fallback"] == (not expected_certified)
                    if expected_certified:
                        assert step["committed_positions"] == expected_certified
                for p in step["committed_positions"]:
                    assert canvas[p] is None
                    canvas[p] = witness[p]
            assert phase["token_ids"] == canvas
            if phase["status"] == "complete":
                assert decoded(canvas) == phase["output"]
    assert len(seen) == len(tasks) * len(policies), (len(seen), len(tasks) * len(policies))
    return config, records


def summarize(directory):
    config, records = read(directory)
    groups = defaultdict(list)
    for row in records:
        groups[row["method"]].append(row)
    table = []
    for name, rows in groups.items():
        phases = [
            phase for row in rows for phase in ([row["draft"]] if "draft" in row else []) + [row]
        ]
        table.append(
            {
                "method": name,
                "n": len(rows),
                "correct": sum(r["correct"] for r in rows),
                "numeric_correct": None
                if config.get("schema_calls", False)
                else sum(r["numeric_correct"] is True for r in rows),
                "valid": sum(r["syntax_valid"] for r in rows),
                "forwards": sum(r["forwards"] for r in rows),
                "median_total_ms": 1000 * median(r["total_seconds_including_setup"] for r in rows),
                "p95_total_ms": 1000
                * sorted(r["total_seconds_including_setup"] for r in rows)[
                    min(len(rows) - 1, int(0.95 * len(rows)))
                ],
                "median_decode_ms": 1000 * median(r["elapsed_seconds"] for r in rows),
                "statuses": dict(Counter(r["status"] for r in rows)),
                "recovery_statuses": dict(
                    Counter(r.get("recovery_status", "not_applicable") for r in rows)
                ),
                "ordinary_commits": sum(
                    t["ordinary_commits"] for phase in phases for t in phase["trace"]
                ),
                "fallback_steps": sum(t["fallback"] for phase in phases for t in phase["trace"]),
                "counterfactual_queries": sum(
                    len(t["gate"]["queries"])
                    for phase in phases
                    for t in phase["trace"]
                    if t.get("gate")
                ),
                "peak_gpu_gib": max(r["gpu_peak_allocated_bytes"] for r in rows) / 2**30,
            }
        )
    table.sort(key=lambda r: (-r["correct"], r["median_total_ms"]))
    eligible = {
        p["name"]
        for p in config["policies"]
        if p["kind"] not in ("epic", "catalog_map") and p["name"] != "exact_b24"
    }
    catalog_controls = {p["name"] for p in config["policies"] if p["kind"] == "catalog_map"}
    frontier = [
        r
        for r in table
        if not any(
            other["correct"] >= r["correct"]
            and other["median_total_ms"] <= r["median_total_ms"]
            and (other["correct"] > r["correct"] or other["median_total_ms"] < r["median_total_ms"])
            for other in table
            if other["method"] not in catalog_controls
        )
    ]
    candidates = [r["method"] for r in frontier if r["method"] in eligible][:3]
    result = {
        "experiment_id": config["experiment_id"],
        "phase": config["phase"],
        "records": len(records),
        "source_commit": records[0]["git_commit"],
        "table": table,
        "frontier": [r["method"] for r in frontier],
        "frontier_scope": "catalog-only MAP is excluded as a dominator of production candidates",
        "confirmation_candidates": candidates,
    }
    lines = [
        "# M24 — comparação de políticas",
        "",
        f"Fase: {config['phase']}. {len(records)} gerações finais; revisão inclui duas fases.",
        "",
        "Tempo total inclui setup por pedido e recuperação oficial; exclui carregar o modelo. "
        "MAP usa catálogo canônico e não é o parser de produção.",
        "",
        "| Política | Chamadas corretas | Válidas | Forwards | Mediana total (ms) | p95 (ms) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    lines += [
        f"| {r['method']} | {r['correct']}/{r['n']} | {r['valid']}/{r['n']} | "
        f"{r['forwards']} | {r['median_total_ms']:.1f} | {r['p95_total_ms']:.1f} |"
        for r in table
    ]
    lines += [
        "",
        "Regra de seleção (aplicada à confirmação apenas na fase de desenvolvimento): "
        + (", ".join(candidates) or "nenhuma")
        + ".",
        "",
        "Acurácia observada não prova superioridade populacional. "
        "Todos os métodos e falhas estão incluídos.",
    ]
    return result, "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    summary, report = summarize(args.directory)
    for path, text in ((args.output, json.dumps(summary, indent=2) + "\n"), (args.report, report)):
        if args.check:
            assert path.read_text() == text, path
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
