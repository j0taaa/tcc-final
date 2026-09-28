#!/usr/bin/env python3
"""Validate official-recovery replay against immutable original decoding records."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from summarize_epic_tools import read_cohort, seconds

from mwpc_research.tool_screen import execute_tool_call, normalize_tool_call

ROOT = Path(__file__).resolve().parents[2]


def summarize(directory):
    manifest_path = directory / "manifest.json"
    if manifest_path.exists():
        for name, digest in json.loads(manifest_path.read_text())["sha256"].items():
            assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == digest
    config_bytes = (directory / "config.json").read_bytes()
    config = json.loads(config_bytes)
    metadata = json.loads((directory / "metadata.json").read_text())
    raw = (
        (directory / "results.jsonl").read_bytes()
        if (directory / "results.jsonl").exists()
        else gzip.decompress((directory / "results.jsonl.gz").read_bytes())
    )
    recovery_rows = [json.loads(line) for line in raw.splitlines()]
    groups = defaultdict(list)
    parents = {}
    decoded = {}
    for name in config["cohorts"]:
        folder = ROOT / name
        read_cohort(folder)
        compressed = (folder / "results.jsonl.gz").read_bytes()
        parents[name] = [json.loads(line) for line in gzip.decompress(compressed).splitlines()]
        decoded[name] = {
            "hash": hashlib.sha256(compressed).hexdigest(),
            "support": json.loads((folder / "support.json").read_text()),
        }
    seen = set()
    for row in recovery_rows:
        name, index = row["cohort"], row["parent_record"]
        assert (name, index) not in seen
        seen.add((name, index))
        original = parents[name][index]
        assert row["method"] == original["method"] != "exact"
        assert row["task_id"] == original["task"]["id"]
        assert row["parent_sha256"] == decoded[name]["hash"]
        assert row["config_sha256"] == hashlib.sha256(config_bytes).hexdigest()
        assert row["git_commit"] == metadata["git_commit"]
        assert row["model_forwards"] == 0
        calls = [decoded[name]["support"]["catalog"][i] for i in original["active_catalog_indices"]]
        status = row["recovery_status"]
        assert status in {"not_needed", "recovered", "no_completion", "timeout", "error"}
        if original["status"] == "complete":
            assert status == "not_needed" and row["recovery_output"] is None
            assert row["recovery_seconds"] == 0
        else:
            assert status != "not_needed"
        effective = row["recovery_output"] if status == "recovered" else original["output"]
        complete = original["status"] == "complete" or status == "recovered"
        assert row["effective_complete"] == complete
        assert row["effective_output"] == effective
        normal = normalize_tool_call(effective)
        assert row["correct"] == (complete and normal == original["task"]["expected"])
        assert row["valid_call"] == (complete and normal in calls)
        assert row["numeric_correct"] == (
            complete
            and normal in calls
            and execute_tool_call(effective) == execute_tool_call(original["task"]["expected"])
        )
        if status == "recovered":
            fragments = []
            for token in original["token_ids"]:
                if token in (126081, 126348):
                    break
                fragments.append(
                    ".*"
                    if token == 126336
                    else re.escape(bytes(original["token_emissions"][str(token)]).decode())
                )
            if not any(t in (126081, 126348) for t in original["token_ids"]):
                fragments.append(".*")
            preserved = re.fullmatch("".join(fragments), effective, re.DOTALL) is not None
            assert preserved == row["fixed_fragments_preserved"]
            assert preserved, (name, row["task_id"], row["method"])
        row["reconstructed_seconds"] = seconds(original) + row["recovery_seconds"]
        groups[(name, row["method"])].append(row)
    expected = {
        (name, i)
        for name, rows in parents.items()
        for i, r in enumerate(rows)
        if r["method"] != "exact"
    }
    assert seen == expected
    cells = []
    for family, names in (("bytes", config["cohorts"][:2]), ("lexical", config["cohorts"][2:])):
        methods = [r["method"] for r in parents[names[0]][: 7 if family == "bytes" else 5]]
        for method in dict.fromkeys(methods):
            cohorts = []
            for name in names:
                if method == "exact":
                    cohort = [
                        {
                            "task_id": r["task"]["id"],
                            "correct": r["correct"],
                            "numeric_correct": execute_tool_call(r["output"])
                            == execute_tool_call(r["task"]["expected"]),
                            "reconstructed_seconds": seconds(r),
                            "recovery_status": "not_needed",
                            "effective_output": r["output"],
                            "recovery_seconds": 0.0,
                        }
                        for r in parents[name]
                        if r["method"] == method
                    ]
                else:
                    cohort = groups[(name, method)]
                cohorts.append({r["task_id"]: r for r in cohort})
            assert set(cohorts[0]) == set(cohorts[1]) and len(cohorts[0]) == 100
            stable = all(
                cohorts[0][tid][key] == cohorts[1][tid][key]
                for tid in cohorts[0]
                for key in ("correct", "numeric_correct", "effective_output", "recovery_status")
            )
            cells.append(
                {
                    "family": family,
                    "method": method,
                    "correct": [sum(r["correct"] for r in c.values()) for c in cohorts],
                    "numeric_correct": [
                        sum(r["numeric_correct"] for r in c.values()) for c in cohorts
                    ],
                    "recovery_statuses": [
                        dict(Counter(r["recovery_status"] for r in c.values())) for c in cohorts
                    ],
                    "median_reconstructed_ms": 1000
                    * median(
                        median(c[tid]["reconstructed_seconds"] for c in cohorts)
                        for tid in cohorts[0]
                    ),
                    "median_recovery_ms_when_needed": median(
                        [
                            1000 * r["recovery_seconds"]
                            for c in cohorts
                            for r in c.values()
                            if r["recovery_status"] != "not_needed"
                        ]
                    )
                    if method != "exact"
                    and any(
                        r["recovery_status"] != "not_needed" for c in cohorts for r in c.values()
                    )
                    else 0.0,
                    "stable": stable,
                }
            )
    result = {"metadata": metadata, "records": len(recovery_rows), "cells": cells}
    lines = [
        "# M23 — EPIC com a recuperação oficial",
        "",
        "100 pedidos sintéticos por método, duas execuções. Acerto principal: AST da chamada.",
        "A recuperação usa a função original do wrapper, sem modelo ou gabarito.",
        "",
        "| Representação | Método | Chamadas corretas (1 / 2) | Valor correto (1 / 2) | "
        "Tempo reconstruído (ms) |",
        "|---|---|---:|---:|---:|",
    ]
    for cell in cells:
        lines.append(
            f"| {cell['family']} | {cell['method']} | {' / '.join(map(str, cell['correct']))} | "
            f"{' / '.join(map(str, cell['numeric_correct']))} | "
            f"{cell['median_reconstructed_ms']:.1f} |"
        )
    lines += [
        "",
        "Tempo reconstruído = geração previamente medida + recuperação CPU reexecutada",
        "sobre o estado final salvo. Não é uma medição conjunta do pipeline. O setup",
        "recriado no replay fica excluído, pois o wrapper já possui gramática e lexer.",
        "A recuperação não faz forwards e pode ultrapassar os slots/domínios do MWPC.",
        "A métrica numérica é secundária; coincidência do valor não garante a chamada pedida.",
        "Os resultados sem recuperação permanecem nos relatórios dos geradores.",
        "",
        "| Representação | Método | Status de recuperação (rodada 1) | "
        "Mediana da recuperação quando necessária (ms) | Saídas estáveis |",
        "|---|---|---|---:|---|",
    ]
    for c in cells:
        lines.append(
            f"| {c['family']} | {c['method']} | {c['recovery_statuses'][0]} | "
            f"{c['median_recovery_ms_when_needed']:.3f} | {c['stable']} |"
        )
    return result, "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data, report = summarize(args.directory)
    for path, text in ((args.output, json.dumps(data, indent=2) + "\n"), (args.report, report)):
        if args.check:
            assert path.read_text() == text, path
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    print(report)


if __name__ == "__main__":
    main()
