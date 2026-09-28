#!/usr/bin/env python3
"""Recheck catalog certificates and summarize complete live screening cohorts."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import defaultdict
from math import fsum
from pathlib import Path
from statistics import median

from mwpc_research.tool_screen import (
    CatalogSelection,
    operand_preserving_indices,
    screen_tasks,
    select_catalog,
    tool_catalog,
)


def summarize(directory: Path) -> dict:
    manifest_path = directory / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        for name, expected in manifest["sha256"].items():
            assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == expected, name
    config = json.loads((directory / "config.json").read_text())
    support = json.loads((directory / "support.json").read_text())
    raw_path = directory / "results.jsonl"
    raw = (
        raw_path.read_bytes()
        if raw_path.exists()
        else gzip.decompress((directory / "results.jsonl.gz").read_bytes())
    )
    records = [json.loads(line) for line in raw.decode().splitlines()]
    family = config.get("family", "simple")
    assert support["catalog"] == list(tool_catalog(family))
    task_list = config.get("tasks") or screen_tasks(config["seed"], config["task_count"], family)
    tasks = {t["id"]: t for t in task_list}
    production = config.get("backend") == "rust"
    emissions = (
        {
            int(t): bytes(b)
            for t, b in json.loads((directory / "token_emissions.json").read_text()).items()
        }
        if production
        else {}
    )

    def decode_witness(witness):
        endpoint = witness.index(126081)
        assert all(t == 126081 for t in witness[endpoint:])
        return b"".join(emissions[t] for t in witness[:endpoint]).decode()

    paths = support["paths"]
    support_hash = hashlib.sha256(json.dumps(paths).encode()).hexdigest()
    groups = defaultdict(list)
    paired = defaultdict(dict)
    seen = set()
    gaps = []
    for row in records:
        active_indices = list(range(len(support["catalog"])))
        if config.get("preserve_operands", False):
            active_indices = list(
                operand_preserving_indices(support["catalog"], row["task"]["instruction"])
            )
        assert row.get("active_catalog_indices", active_indices) == active_indices
        paths = [support["paths"][i] for i in active_indices]
        calls = [support["catalog"][i] for i in active_indices]
        domains = [{path[p] for path in paths} for p in range(config["slots"])]
        key = (row["task"]["id"], row["method"], row["budget"])
        assert key not in seen
        seen.add(key)
        assert row["task"] == tasks[key[0]]
        assert row["support_sha256"] == support_hash
        assert (
            row["config_sha256"]
            == hashlib.sha256((directory / "config.json").read_bytes()).hexdigest()
        )
        canvas = [None] * config["slots"]
        assert row["forwards"] == len(row["trace"]) + bool(row.get("failure"))
        for trace in row["trace"]:
            assert trace["canvas_before"] == canvas
            if production:
                witness = tuple(trace["witness_token_ids"])
                assert len(witness) == config["slots"]
                assert all(t in domains[p] for p, t in enumerate(witness))
                assert all(t is None or t == witness[p] for p, t in enumerate(canvas))
                assert decode_witness(witness) in calls
                matched = tuple(p for p, t, w in trace["proposals"] if w > 0 and witness[p] == t)
                score = fsum(w for p, t, w in trace["proposals"] if witness[p] == t)
                result = CatalogSelection(trace["witness_index"], matched, score, witness)
                native = trace["production_result"]
                assert native["status"] == (
                    "optimal" if row["method"] == "exact" else "feasible_on_support"
                )
                assert native["witness_token_ids"] == list(witness)
                assert abs(native["score"] - score) < 1e-10
                other_score = trace["other_objective"]
                if other_score is not None:
                    assert (
                        (score + 1e-10 >= other_score)
                        if row["method"] == "exact"
                        else (other_score + 1e-10 >= score)
                    )
            else:
                result = select_catalog(paths, canvas, trace["proposals"], method=row["method"])
                assert result.witness_index == trace["witness_index"]
                other = select_catalog(
                    paths,
                    canvas,
                    trace["proposals"],
                    method="greedy" if row["method"] == "exact" else "exact",
                )
                other_score = other.objective
                assert abs(other_score - trace["other_objective"]) < 1e-10
            assert list(result.selected_positions) == trace["selected_positions"]
            assert abs(result.objective - trace["objective"]) < 1e-10
            if other_score is not None and abs(result.objective - other_score) > 1e-10:
                gaps.append(
                    {
                        "task": key[0],
                        "method": row["method"],
                        "budget": row["budget"],
                        "step": trace["step"],
                        "score": result.objective,
                        "other_score": other_score,
                    }
                )
            assert trace["fallback"] == (not result.selected_positions)
            expected_commits = list(result.selected_positions) or [canvas.index(None)]
            assert expected_commits == trace["committed_positions"]
            for p in expected_commits:
                assert canvas[p] is None
                canvas[p] = result.witness_token_ids[p]
        complete = all(t is not None for t in canvas)
        assert complete == (row["status"] == "complete")
        if complete:
            if production:
                assert row["output"] == decode_witness(canvas)
                assert row["output"] in calls
            else:
                assert canvas in paths
                assert row["output"] == support["catalog"][active_indices[paths.index(canvas)]]
        assert row["correct"] == (complete and row["output"] == row["task"]["expected"])
        groups[(row["budget"], row["method"])].append(row)
        paired[(row["budget"], key[0])][row["method"]] = row
    assert len(records) == len(tasks) * len(config["methods"]) * len(config["proposal_budgets"])
    cells = []
    comparisons = []
    for (budget, method), rows in sorted(groups.items()):
        cells.append(
            {
                "budget": budget,
                "method": method,
                "n": len(rows),
                "correct": sum(r["correct"] for r in rows),
                "forwards": sum(r["forwards"] for r in rows),
                "median_seconds_including_grammar_setup": median(
                    r["elapsed_excluding_shadow_seconds"] + r.get("grammar_setup_seconds", 0)
                    for r in rows
                ),
            }
        )
    for budget in config["proposal_budgets"]:
        pairs = [pair for (b, _), pair in paired.items() if b == budget]
        wins = [
            p["exact"]["task"]["id"]
            for p in pairs
            if p["exact"]["correct"] and not p["greedy"]["correct"]
        ]
        losses = [
            p["exact"]["task"]["id"]
            for p in pairs
            if p["greedy"]["correct"] and not p["exact"]["correct"]
        ]
        fewer = [
            p["exact"]["task"]["id"]
            for p in pairs
            if p["exact"]["correct"]
            and p["greedy"]["correct"]
            and p["exact"]["forwards"] < p["greedy"]["forwards"]
        ]
        more = [
            p["exact"]["task"]["id"]
            for p in pairs
            if p["exact"]["correct"]
            and p["greedy"]["correct"]
            and p["exact"]["forwards"] > p["greedy"]["forwards"]
        ]
        comparisons.append(
            {
                "budget": budget,
                "exact_only_correct": wins,
                "greedy_only_correct": losses,
                "both_correct_exact_fewer_forwards": fewer,
                "both_correct_exact_more_forwards": more,
                "both_correct_median_speed_ratio_greedy_over_exact": median(
                    [
                        (
                            p["greedy"]["elapsed_excluding_shadow_seconds"]
                            + p["greedy"].get("grammar_setup_seconds", 0)
                        )
                        / (
                            p["exact"]["elapsed_excluding_shadow_seconds"]
                            + p["exact"].get("grammar_setup_seconds", 0)
                        )
                        for p in pairs
                        if p["exact"]["correct"] and p["greedy"]["correct"]
                    ]
                )
                if any(p["exact"]["correct"] and p["greedy"]["correct"] for p in pairs)
                else None,
            }
        )
    return {
        "experiment": config["experiment_id"],
        "records": len(records),
        "unique_tasks": len(tasks),
        "cells": cells,
        "comparisons": comparisons,
        "score_gap_states": gaps,
        "producing_commits": sorted({r["git_commit"] for r in records}),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directories", type=Path, nargs="+")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = [summarize(directory) for directory in args.directories]
    text = json.dumps(result, indent=2) + "\n"
    if args.output:
        if args.check:
            assert args.output.read_text() == text, "generated summary differs"
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text)
    if args.report:
        report = build_report(args.directories, result)
        if args.check:
            assert args.report.read_text() == report, "generated report differs"
        else:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(report)
    print(text)


def build_report(directories, summaries):
    """Aggregate timing repetitions by task, never counting them as extra tasks."""
    confirmation = [d for d in directories if d.name in ("confirmation", "repeat")]
    assert len(confirmation) == 2, "both order-balanced runs required"
    by_key = defaultdict(list)
    for directory in confirmation:
        path = directory / "results.jsonl.gz"
        data = (
            gzip.decompress(path.read_bytes())
            if path.exists()
            else (directory / "results.jsonl").read_bytes()
        )
        for row in map(json.loads, data.decode().splitlines()):
            by_key[(row["task"]["id"], row["method"])].append(row)
    assert len(by_key) == 200
    times = {}
    first = {}
    for key, repeats in by_key.items():
        assert len(repeats) == 2
        assert repeats[0]["task"] == repeats[1]["task"]
        for field in ("correct", "output", "status", "forwards"):
            assert repeats[0][field] == repeats[1][field], (key, field, "unstable result")
        times[key] = median(
            r["elapsed_excluding_shadow_seconds"] + r["grammar_setup_seconds"] for r in repeats
        )
        first[key] = repeats[0]
    task_ids = sorted({task for task, _ in by_key})
    wins = [
        t
        for t in task_ids
        if first[(t, "exact")]["correct"] and not first[(t, "greedy")]["correct"]
    ]
    losses = [
        t
        for t in task_ids
        if first[(t, "greedy")]["correct"] and not first[(t, "exact")]["correct"]
    ]
    both = [
        t for t in task_ids if first[(t, "exact")]["correct"] and first[(t, "greedy")]["correct"]
    ]
    ratio = median(times[(t, "greedy")] / times[(t, "exact")] for t in both)
    lines = [
        "# M22 — Geração real por dLLM: resultados verificados",
        "",
        "Arquivo gerado por `scripts/exact_commit/summarize_tool_screen.py`.",
        "",
        "## Confirmação com parser Rust",
        "",
        "LLaDA-8B-Instruct, NF4, RTX 3080 Ti; 100 pedidos únicos, duas execuções",
        "com ordem inicial invertida. As repetições não são novas tarefas.",
        "",
        "| Método | Acertos/100 | Forwards por execução | Mediana total por pedido |",
        "| --- | ---: | ---: | ---: |",
    ]
    for method in ("greedy", "exact"):
        records = [first[(t, method)] for t in task_ids]
        correct = sum(r["correct"] for r in records)
        forwards = sum(r["forwards"] for r in records)
        elapsed = median(times[(t, method)] for t in task_ids)
        lines.append(f"| {method} | {correct} | {forwards} | {elapsed * 1000:.1f} ms |")
    lines += [
        "",
        "Tempo: mediana das duas execuções por pedido/método, depois entre pedidos;",
        "inclui inferência sincronizada, candidatos, seleção, atualização e compilação",
        "da gramática por pedido; exclui carregar pesos, aquecimento e consulta-sombra",
        "diagnóstica. Não equivale a latência de um serviço implantado.",
        "",
        f"Nos {len(both)} pares que ambos acertam, a mediana da razão",
        f"tempo guloso / tempo exato é **{ratio:.2f}x**.",
        "",
        f"Diferenças de acerto: **{len(wins)} vitórias e {len(losses)} derrotas** do exato.",
        "Poucos pares discordantes não sustentam superioridade populacional de acurácia.",
        "O ganho de tempo não veio de menos forwards: veio da seleção/validação.",
        "",
        "O comparador é viabilidade gulosa por confiança com reutilização de testemunha,",
        "usando o mesmo parser, suporte, gramática e fallback. **Não é EPIC.**",
        "Não se demonstrou superioridade sobre geração livre ou todos os decodificadores.",
        "",
        "## Exemplos da confirmação",
        "",
    ]
    for task_id in wins:
        exact, greedy = first[(task_id, "exact")], first[(task_id, "greedy")]
        ordinary = {}
        for method, row in (("exact", exact), ("greedy", greedy)):
            trace = row["trace"][0]
            ordinary[method] = sum(
                p in trace["selected_positions"] and token != 126081
                for p, token, _ in trace["proposals"]
            )
        lines += [
            f"- `{task_id}`: {exact['task']['instruction']}",
            f"  Exato: `{exact['output']}`; guloso: `{greedy['output']}`.",
            f"  Primeira etapa: {ordinary['exact']} propostas ordinárias retidas pelo exato, "
            f"contra {ordinary['greedy']} pelo guloso; EOS/PAD excluídos dessa contagem.",
        ]
    lines += [
        "",
        "## Todas as tentativas exploratórias",
        "",
        "| Coorte | Orçamento | Método | Acertos/pedidos | Forwards |",
        "| --- | ---: | --- | ---: | ---: |",
    ]
    for result in summaries:
        if "screen" not in result["experiment"]:
            continue
        for cell in result["cells"]:
            lines.append(
                f"| {result['experiment']} | {cell['budget']} | {cell['method']} | "
                f"{cell['correct']}/{cell['n']} | {cell['forwards']} |"
            )
    lines += [
        "",
        "V1: chamadas simples. V2: chamadas aninhadas determinísticas. V3:",
        "propostas amostradas. V4: preservação do multiconjunto de operandos",
        "dentro da geração; houve uma vitória e uma derrota, com empate global.",
        "A triagem usou enumeração canônica; a confirmação usou o parser Rust",
        "sobre domínios posicionais e CFG de bytes, permitindo outras tokenizações.",
        "",
        "## Alcance científico",
        "",
        "São pedidos sintéticos de compilação de expressões para chamadas de funções,",
        "com inferência real, um único modelo quantizado e templates compartilhados.",
        "A restrição preserva operandos lidos do pedido; não recebe a resposta esperada.",
        "O domínio é finito/regular: não isola uma vantagem de expressividade de CFGs.",
        "A garantia é por etapa e suporte, com testemunha verificada; não garante semântica.",
        "A linguagem de calculadora é uma aplicação limitada de geração de programas,",
        "não um benchmark de APIs reais. A enumeração também continua sendo uma",
        "alternativa forte quando todo o catálogo é pequeno e explícito.",
        "",
        "A contribuição observada é um benefício restrito durante a geração pela dLLM:",
        f"seleção exata mais rápida que a viabilidade gulosa comparada e {len(wins)} pedidos",
        "novos recuperados corretamente. Os resultados negativos anteriores permanecem.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
