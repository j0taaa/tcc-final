"""Generate every status/comparison; no hand-edited timing tables."""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median


def analyze(folder, candidate="monotone"):
    metadata = json.loads((folder / "metadata.json").read_text())
    rows = [json.loads(line) for line in (folder / "rows.jsonl").read_text().splitlines()]
    methods = metadata.get(
        "methods",
        [
            "greedy_witness",
            "lex_integer",
            "greedy_cached_prefix",
            "monotone",
            "enumeration",
            "sat_cached_prefix",
        ],
    )
    if candidate not in methods:
        raise ValueError("candidate absent from declared methods")
    expected = len(metadata["selected"]) * 3 * 3 * len(methods)
    if len(rows) != expected:
        raise ValueError(f"incomplete campaign {folder}: {len(rows)}/{expected}")
    grouped, configurations = defaultdict(dict), defaultdict(dict)
    statuses = {m: dict(Counter(r["status"] for r in rows if r["method"] == m)) for m in methods}
    for row in rows:
        key = (row["case"], row["mask_count"], row["repetition"])
        if row["method"] in grouped[key]:
            raise ValueError("duplicate timing record")
        grouped[key][row["method"]] = row
        configurations[row["case"], row["mask_count"]].setdefault(row["method"], []).append(row)
        if row["status"] == "complete" and row["method"] == "monotone" and "propagation" in row:
            if any(v > row["forest"]["alternatives"] for v in row["propagation"].values()):
                raise ValueError("monotonic operation count exceeded forest alternatives")
    equality_checks = 0
    for group in grouped.values():
        complete = [r for r in group.values() if r["status"] == "complete"]
        for row in complete[1:]:
            first = complete[0]
            for field in ("tokens", "output", "support_rows", "support_sha256", "trace"):
                if row[field] != first[field]:
                    raise ValueError(f"unexplained {field} mismatch: {first['case']}")
            equality_checks += 1
    comparisons = []
    for (case, count), group in sorted(configurations.items()):
        own = group[candidate]
        controls = {}
        if all(r["status"] == "complete" for r in own):
            own = sorted(own, key=lambda r: r["repetition"])
            for name, alternatives in group.items():
                if name == candidate or not all(r["status"] == "complete" for r in alternatives):
                    continue
                alternatives = sorted(alternatives, key=lambda r: r["repetition"])
                controls[name] = {
                    metric: dict(
                        own_median=median(r[metric] for r in own),
                        control_median=median(r[metric] for r in alternatives),
                        ratio=median(r[metric] for r in alternatives)
                        / median(r[metric] for r in own),
                        repetition_ratios=[
                            b[metric] / a[metric] for a, b in zip(own, alternatives, strict=True)
                        ],
                    )
                    for metric in ("wall", "cpu")
                }
        qualifies = bool(controls) and all(
            control[metric]["ratio"] >= 1.25 and min(control[metric]["repetition_ratios"]) > 1
            for control in controls.values()
            for metric in ("wall", "cpu")
        )
        comparisons.append(
            dict(case=case, mask_count=count, controls=controls, qualifies=qualifies)
        )
    return dict(
        path=str(folder),
        device=metadata["device"],
        candidate=candidate,
        growing_support=metadata.get("growing_support", False),
        root_pruning=metadata.get("root_pruning", False),
        native_binding=metadata.get("native_binding"),
        common_startup=metadata.get("common_startup"),
        phase=metadata["phase"],
        producer_commit=metadata["commit"],
        protocol_sha256=metadata["protocol_sha256"],
        metadata_sha256=hashlib.sha256((folder / "metadata.json").read_bytes()).hexdigest(),
        rows_sha256=hashlib.sha256((folder / "rows.jsonl").read_bytes()).hexdigest(),
        records=len(rows),
        statuses=statuses,
        equality_checks=equality_checks,
        complete_records=sum(r["status"] == "complete" for r in rows),
        configurations=len(comparisons),
        wins=sum(c["qualifies"] for c in comparisons),
        comparisons=comparisons,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate", default="monotone")
    args = parser.parse_args()
    summaries = [analyze(folder, args.candidate) for folder in args.campaign]
    report = [
        "# Geração completa com política gulosa preservada",
        "",
        "Todos os métodos executam seus próprios forwards. Os custos incluem preparação e saída; "
        "carregamento/aquecimento comum, tokenização do corpus e gramática fixa preparada uma vez "
        "são externos ao decoder em serviço já preparado. "
        "Suporte adaptativo é a união dos top16 atuais/anteriores; sem tokens de referência. "
        "Reservas dos controles mantêm candidatos futuros inativos nas consultas. "
        "Não há comparação nativa com EPIC, nem promessa de melhora semântica.",
        "",
        "O critério predeclarado exige redução de pelo menos 20% em mediana wall e CPU contra "
        "todos os controles concluídos e sinal favorável nas três repetições. "
        "CPU não mede trabalho/energia da GPU. As três repetições não são intervalo de confiança. "
        "A extensão GPU é secundária, declarada após desenvolvimento CPU, antes de seus timings.",
        "",
    ]
    for result in summaries:
        report += [
            f"## {result['phase']} / {result['device']}",
            "",
            f"{result['records']} registros; {result['complete_records']} completos; "
            f"{result['equality_checks']} comparações exatas de suporte/trajectory/output. "
            f"{result['wins']}/{result['configurations']} configurações atingem o critério.",
            "",
            "| Método | Status |",
            "| --- | --- |",
        ]
        for method, status in result["statuses"].items():
            report.append(f"| {method} | `{json.dumps(status, sort_keys=True)}` |")
        report += [
            "",
            "| Documento / máscaras | Melhor controle completo (wall) | "
            f"{args.candidate} (s) | Controle (s) | Razão controle/candidata | Critério |",
            "| --- | --- | ---: | ---: | ---: | --- |",
        ]
        for comparison in result["comparisons"]:
            controls = comparison["controls"]
            if not controls:
                report.append(
                    f"| {comparison['case'][:12]} / {comparison['mask_count']} | "
                    "— | — | — | — | inconclusivo/sem solução |"
                )
                continue
            best = min(controls, key=lambda m: controls[m]["wall"]["control_median"])
            wall = controls[best]["wall"]
            report.append(
                f"| {comparison['case'][:12]} / {comparison['mask_count']} | {best} | "
                f"{wall['own_median']:.6f} | {wall['control_median']:.6f} | "
                f"{wall['ratio']:.3f} | {'sim' if comparison['qualifies'] else 'não'} |"
            )
        report.append("")
    report += [
        "A propagação amortizada AND/OR e a otimização lexicográfica são antecedentes clássicos. "
        "Os ganhos que esta avaliação estabelecer pertencem à implementação e integração "
        "delimitadas. Não provam prioridade histórica ou significância para publicação; "
        "revisão humana permanece ausente.",
        "",
    ]
    args.output.with_suffix(".json").write_text(json.dumps(summaries, indent=2) + "\n")
    args.output.with_suffix(".md").write_text("\n".join(report))


if __name__ == "__main__":
    main()
