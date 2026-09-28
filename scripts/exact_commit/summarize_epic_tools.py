#!/usr/bin/env python3
"""Validate M23 archives and generate the EPIC comparison without model access."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import Counter
from math import fsum, isfinite
from pathlib import Path
from statistics import median

from mwpc_research.tool_screen import normalize_tool_call, operand_preserving_indices, tool_catalog


def read_cohort(directory):
    if (directory / "manifest.json").exists():
        manifest = json.loads((directory / "manifest.json").read_text())
        for name, digest in manifest["sha256"].items():
            assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == digest, name
    config_bytes = (directory / "config.json").read_bytes()
    config = json.loads(config_bytes)
    metadata = json.loads((directory / "metadata.json").read_text())
    support = json.loads((directory / "support.json").read_text())
    assert support["catalog"] == list(tool_catalog("nested"))
    emissions = {
        int(k): bytes(v)
        for k, v in json.loads((directory / "token_emissions.json").read_text()).items()
    }
    raw = (
        (directory / "results.jsonl").read_bytes()
        if (directory / "results.jsonl").exists()
        else gzip.decompress((directory / "results.jsonl.gz").read_bytes())
    )
    records = [json.loads(line) for line in raw.splitlines()]
    tasks = {t["id"]: t for t in config["tasks"]}
    assert len(records) == len(tasks) * len(config["methods"])
    by_key = {}
    for row in records:
        task = tasks[row["task"]["id"]]
        assert row["task"] == task
        assert row["method"] in config["methods"]
        assert row["config_sha256"] == hashlib.sha256(config_bytes).hexdigest()
        for key in (
            "git_commit",
            "model_id",
            "model_revision",
            "tokenizer_revision",
            "support_sha256",
            "upstream_epic_commit",
        ):
            assert row[key] == metadata[key]
        assert (
            row["support_sha256"]
            == hashlib.sha256(json.dumps(support["paths"]).encode()).hexdigest()
        )
        indices = list(operand_preserving_indices(support["catalog"], task["instruction"]))
        assert indices == row["active_catalog_indices"]
        calls = [support["catalog"][i] for i in indices]
        paths = [support["paths"][i] for i in indices]
        domains = [{p[i] for p in paths} for i in range(config["slots"])]
        assert row["active_grammar_hash"] == hashlib.sha256(json.dumps(calls).encode()).hexdigest()
        complete = row["status"] == "complete"
        normalized = normalize_tool_call(row["output"])
        assert row["correct"] == (complete and normalized == task["expected"])
        assert row["syntax_valid"] == (complete and normalized in calls)
        assert 0 <= row["forwards"] <= config["max_forwards"]
        if row["method"] == "exact":
            canvas = [None] * config["slots"]
            for trace in row["trace"]:
                assert trace["canvas_before"] == canvas
                witness = trace["witness_token_ids"]
                assert len(witness) == len(canvas)
                assert all(t in domains[i] for i, t in enumerate(witness))
                assert all(t is None or t == witness[i] for i, t in enumerate(canvas))
                end = witness.index(126081)
                assert all(t == 126081 for t in witness[end:])
                decoded = b"".join(emissions[t] for t in witness[:end]).decode()
                assert decoded in calls
                proposals = trace["proposals"]
                assert all(isfinite(w) and w >= 0 for _, _, w in proposals)
                assert all(canvas[p] is None for p, _, _ in proposals)
                matched = [p for p, t, w in proposals if w > 0 and witness[p] == t]
                score = fsum(w for p, t, w in proposals if witness[p] == t)
                assert matched == trace["selected_positions"]
                assert abs(score - trace["objective"]) < 1e-10
                native = trace["production_result"]
                assert native["status"] == "optimal"
                assert native["witness_token_ids"] == witness
                assert native["selected_proposal_ids"] == matched
                assert abs(native["score"] - score) < 1e-10
                assert trace["fallback"] == (not matched)
                commits = matched or [canvas.index(None)]
                assert commits == trace["committed_positions"]
                for position in commits:
                    canvas[position] = witness[position]
            assert complete == all(t is not None for t in canvas)
            if complete:
                end = canvas.index(126081)
                assert row["output"] == b"".join(emissions[t] for t in canvas[:end]).decode()
        else:
            assert row["forwards"] == len(row["epic_forwards"])
            assert not row["epic_batch_errors"], row["epic_batch_errors"]
            assert all(
                value == "1"
                for key, value in row["epic_environment"].items()
                if not key.endswith("MIN_BATCH")
            )
            if row["epic_events"]:
                assert row["token_ids"] == row["epic_events"][-1]["canvas"]
                assert complete == row["epic_events"][-1]["complete"]
            if complete:
                assert 126336 not in row["token_ids"]
                end = row["token_ids"].index(126081)
                assert all(t == 126081 for t in row["token_ids"][end:])
                # All completed calls in this language use the archived byte adapter.
                # Unknown IDs require an explicitly archived emission, never guessing.
                native_emissions = {int(t): bytes(b) for t, b in row["token_emissions"].items()}
                assert all(t in native_emissions for t in row["token_ids"][:end])
                assert (
                    row["output"]
                    == b"".join(native_emissions[t] for t in row["token_ids"][:end]).decode()
                )
                if row["method"].startswith("epic_domains_"):
                    assert all(t in domains[p] for p, t in enumerate(row["token_ids"]))
        key = (task["id"], row["method"])
        assert key not in by_key
        by_key[key] = row
    assert set(by_key) == {(task, method) for task in tasks for method in config["methods"]}
    return config, metadata, by_key


def seconds(row):
    return (
        row["elapsed_excluding_shadow_seconds"]
        + row["grammar_setup_seconds"]
        + row.get("epic_setup_seconds", 0)
    )


def build(directories):
    cohorts = [read_cohort(d) for d in directories]
    primary = [c for c in cohorts if c[0]["task_count"] == 100]
    assert len(primary) == 2
    config, _, first = primary[0]
    second = primary[1][2]
    assert set(first) == set(second)
    stable = all(
        first[k][field] == second[k][field]
        for k in first
        for field in ("status", "output", "correct", "forwards")
    )
    cells = []
    for method in config["methods"]:
        rows = [first[(t["id"], method)] for t in config["tasks"]]
        timings = {
            t["id"]: median(seconds(c[2][(t["id"], method)]) for c in primary)
            for t in config["tasks"]
        }
        cells.append(
            {
                "method": method,
                "correct_per_repeat": [
                    sum(r["correct"] for (t, m), r in c[2].items() if m == method) for c in primary
                ],
                "syntax_valid": sum(r["syntax_valid"] for r in rows),
                "statuses": dict(Counter(r["status"] for r in rows)),
                "forwards_per_repeat": [
                    sum(r["forwards"] for (t, m), r in c[2].items() if m == method) for c in primary
                ],
                "median_total_ms": 1000 * median(timings.values()),
                "median_forward_ms": 1000
                * median(
                    median(
                        (
                            r["epic_times"]["forward_seconds"]
                            if method != "exact"
                            else sum(t["forward_seconds"] for t in r["trace"])
                        )
                        for r in (c[2][(task["id"], method)] for c in primary)
                    )
                    for task in config["tasks"]
                ),
                "batch_calls": sum(r.get("epic_counters", {}).get("batch_calls", 0) for r in rows),
                "batch_selected": sum(
                    r.get("epic_counters", {}).get("batch_selected", 0) for r in rows
                ),
                "rejections": sum(len(r.get("epic_resamples", [])) for r in rows),
            }
        )
    pairs = []
    for method in config["methods"]:
        if method == "exact":
            continue
        wins, losses, both, ratios = [], [], [], []
        for task in config["tasks"]:
            tid = task["id"]
            a, b = first[(tid, "exact")], first[(tid, method)]
            if a["correct"] and not b["correct"]:
                wins.append(tid)
            if b["correct"] and not a["correct"]:
                losses.append(tid)
            if a["correct"] and b["correct"]:
                both.append(tid)
                ratios.append(
                    median(seconds(c[2][(tid, method)]) for c in primary)
                    / median(seconds(c[2][(tid, "exact")]) for c in primary)
                )
        pairs.append(
            {
                "method": method,
                "exact_only_correct": wins,
                "epic_only_correct": losses,
                "both_correct": len(both),
                "median_paired_epic_over_exact_seconds": median(ratios) if ratios else None,
            }
        )
    result = {
        "stable_outputs_status_forwards": stable,
        "cells": cells,
        "pairs": pairs,
        "producing_commits": sorted({c[1]["git_commit"] for c in cohorts}),
        "all_cohorts": [
            {
                "experiment": c[0]["experiment_id"],
                "records": len(c[2]),
                "statuses": dict(Counter(r["status"] for r in c[2].values())),
            }
            for c in cohorts
        ],
    }
    lines = [
        "# M23 — comparação com EPIC",
        "",
        "Gerado dos arquivos validados; 100 pedidos sintéticos já usados no M22, duas",
        "execuções por método. Repetições não são tarefas independentes.",
        "",
        "| Método | Acertos (execuções 1 / 2) | Forwards (1 / 2) | Mediana total (ms) |",
        "|---|---:|---:|---:|",
    ]
    for c in cells:
        lines.append(
            f"| {c['method']} | {' / '.join(map(str, c['correct_per_repeat']))} | "
            f"{' / '.join(map(str, c['forwards_per_repeat']))} | {c['median_total_ms']:.1f} |"
        )
    lines += [
        "",
        "Mediana calculada após agregar as duas medições de cada pedido. Inclui",
        "inferência, decodificação e setup da gramática/lexemas/domínios; exclui",
        "carregamento, warmup e diagnóstico contrafactual MWPC.",
        "",
        "| Comparador | Só MWPC acerta | Só EPIC acerta | Ambos acertam | Tempo EPIC / MWPC* |",
        "|---|---:|---:|---:|---:|",
    ]
    for p in pairs:
        ratio = p["median_paired_epic_over_exact_seconds"]
        lines.append(
            f"| {p['method']} | {len(p['exact_only_correct'])} | "
            f"{len(p['epic_only_correct'])} | {p['both_correct']} | {ratio:.2f} |"
        )
    lines += [
        "",
        "*Mediana dos quocientes pareados somente onde ambos acertam; >1 favorece MWPC.",
        "",
        f"Saídas, status e forwards idênticos nas repetições: **{stable}**.",
        "",
        "## Limites da comparação",
        "",
        "EPIC original usa vocabulário nativo, rejeições no mesmo forward e lacunas",
        "abstratas. A variante `domains` recebe os domínios do MWPC, mas a máscara",
        "renormaliza a confiança; não torna os seletores isoladamente equivalentes.",
        "Etapas EPIC 1/4/24 são orçamentos de geração distintos, não 24 forwards garantidos.",
        "MWPC usa até 24 forwards e otimiza propostas dentro de suporte finito por etapa.",
        "A representação de lexemas de um byte é compartilhada por equivalência de",
        "linguagem; não se afirma que seja a representação mais rápida para EPIC.",
        "Um modelo quantizado, uma GPU e uma linguagem pequena e finita. Não há",
        "evidência aqui de superioridade geral em APIs reais ou sobre outras configurações.",
        "",
    ]
    return result, "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directories", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result, report = build(args.directories)
    for path, content in (
        (args.output, json.dumps(result, indent=2) + "\n"),
        (args.report, report),
    ):
        if args.check:
            assert path.read_text() == content, path
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    print(report)


if __name__ == "__main__":
    main()
