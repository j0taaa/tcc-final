"""Rebuild the M21 report/table from hash-verified, independently checked outputs."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import median

from scripts.exact_commit.run_json_repair import read_archive, summarize

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "docs/artifacts/raw/m21_repair_v1"
OUT = ROOT / "paper/generated/m21_repair_v1"
COHORTS = {"pilot": "pilot", "confirmation": "confirmation", "mechanism": "mechanism"}
METHODS = (
    "unchanged",
    "json_repair",
    "schema_standard",
    "schema_salvage",
    "enumeration",
    "feasibility",
    "greedy",
    "exact",
)
NAMES = {
    "unchanged": "Unchanged",
    "json_repair": "JSON repair",
    "schema_standard": "Schema standard",
    "schema_salvage": "Schema salvage",
    "enumeration": "Enumeration",
    "feasibility": "Unweighted CFG",
    "greedy": "Greedy CFG",
    "exact": "Exact MWPC",
}
FAMILIES = ("valid", "opening", "closing", "separator", "missing_suffix", "semantic")
LABELS = {
    "valid": "Valid control",
    "opening": "Opening swaps",
    "closing": "Closing swaps",
    "separator": "Separator swaps",
    "missing_suffix": "Missing suffix",
    "semantic": "Wrong value",
}


def document_cells(rows):
    groups = defaultdict(lambda: defaultdict(list))
    for row in rows:
        groups[row["profile"], row["case"]["family"], row["method"]][
            row["case"]["document_id"]
        ].append(row)
    result = {}
    for key, documents in groups.items():
        result[key] = {
            "success": sum(
                all(r["evaluation"]["semantic_success"] for r in group)
                for group in documents.values()
            ),
            "count": len(documents),
            "median_ms": median(
                median(r["result"]["total_seconds"] for r in group) for group in documents.values()
            )
            * 1000,
        }
    return result


def outputs():
    rows = {key: read_archive(RAW / name) for key, name in COHORTS.items()}
    summaries = {key: summarize(value) for key, value in rows.items()}
    cells = {key: document_cells(value) for key, value in rows.items()}
    report = [
        "# Reparo certificado de JSON: resultados controlados M21",
        "",
        "Relatório gerado a partir de arquivos brutos com hashes e avaliação independente. "
        "Não contém inferência de modelo nem comparação com uma nova chamada ao modelo.",
        "",
        "Os perfis de bytes e LLaDA são separados. O segundo usa o tokenizer real, "
        "não saídas reais do modelo. Valores e tamanhos da confirmação diferem do piloto; "
        "os exemplos compartilham mecanismos de corrupção definidos previamente. "
        "A mistura balanceada não estima a frequência de erros em produção.",
        "",
        "Sucesso exige recuperar todos os dados, preservando tipos e estrutura. "
        "Um documento só conta como sucesso estável se todas as repetições passarem. "
        "Tempos são medianas das medianas por documento, incluindo falhas e censura; "
        "razões de velocidade só usam pares conjuntamente bem-sucedidos.",
        "",
    ]
    for cohort in COHORTS:
        metadata = rows[cohort][0]["metadata"]
        report += [
            f"## {cohort}",
            "",
            f"Commit de medição: `{metadata['git_commit']}`. Configuração: "
            f"`{metadata['config']['experiment_id']}`. Chamadas: {len(rows[cohort])}.",
            "",
            "| Perfil | Classe | Método | Documentos corretos | Mediana total (ms) |",
            "|---|---|---|---:|---:|",
        ]
        for profile in ("bytes", "llada"):
            for family in FAMILIES:
                for method in METHODS:
                    cell = cells[cohort][profile, family, method]
                    report.append(
                        f"| {profile} | {family} | {NAMES[method]} | "
                        f"{cell['success']}/{cell['count']} | {cell['median_ms']:.2f} |"
                    )
        report += [
            "",
            "Comparações pareadas e intervalos descritivos por documento:",
            "",
            "| Perfil | Classe | Comparador | Só exato vence | Só comparador vence | "
            "Ambos vencem | Velocidade comparador/exato (IC 95%) |",
            "|---|---|---|---:|---:|---:|---|",
        ]
        for pair in summaries[cohort]["paired_documents"]:
            ratio = pair["median_paired_speedup"]
            interval = pair["speedup_bootstrap_95"]
            speed = "-" if ratio is None else f"{ratio:.2f} ({interval[0]:.2f}-{interval[1]:.2f})"
            report.append(
                f"| {pair['profile']} | {pair['family']} | {pair['comparator']} | "
                f"{pair['exact_only_success']} | {pair['comparator_only_success']} | "
                f"{pair['both_success']} | {speed} |"
            )
        report += [
            "",
            "Contagens completas de status:",
            "",
            "```json",
            json.dumps(
                [
                    {
                        "profile": g["profile"],
                        "family": g["family"],
                        "method": g["method"],
                        "statuses": g["status_counts"],
                    }
                    for g in summaries[cohort]["groups"]
                ],
                indent=2,
            ),
            "```",
            "",
        ]
    report += [
        "## Interpretação e limites",
        "",
        "A comparação com CFG sem pesos separa recuperação por restrição de esquema "
        "de minimização de edições. Empates no esquema rígido não demonstram benefício "
        "dos pesos. O estudo de gramática ambígua testa esse mecanismo separadamente.",
        "",
        "Os reparadores simples podem ser muito mais rápidos e lidar com inserções "
        "fora do suporte. O resultado deve ser interpretado por classe, junto dos "
        "custos e das falhas. Erros semânticos já sintaticamente válidos não são "
        "corrigidos apenas pela gramática. Nenhum resultado estabelece superioridade "
        "geral sobre reparadores ou melhor geração de dLLMs.",
        "",
    ]
    table = [
        r"\begin{table}[ht]",
        r"\centering\small",
        r"\caption{Controlled JSON repair with the real LLaDA tokenizer, without model inference. "
        r"Cells count documents correct in every repetition. J: json\_repair; S/V: its "
        r"schema standard/salvage modes; N: enumeration; U: unweighted CFG; G: greedy; E: exact. "
        r"Schema cohort: 20 documents, two repetitions; "
        r"ambiguous cohort: eight documents, one repetition.}",
        r"\label{tab:repair}",
        r"\begin{tabular}{lrrrrrrr}\toprule",
        r"Error class & J & S & V & N & U & G & E\\\midrule",
    ]
    table_methods = (
        "json_repair",
        "schema_standard",
        "schema_salvage",
        "enumeration",
        "feasibility",
        "greedy",
        "exact",
    )
    for cohort, title in (
        ("confirmation", "Shared record schema"),
        ("mechanism", "Ambiguous JSON grammar"),
    ):
        table.append(r"\multicolumn{8}{l}{\emph{" + title + r"}}\\")
        for family in FAMILIES:
            entries = [cells[cohort]["llada", family, method] for method in table_methods]
            table.append(
                LABELS[family]
                + " & "
                + " & ".join(f"{c['success']}/{c['count']}" for c in entries)
                + r" \\"
            )
        table.append(r"\midrule")
    table[-1] = r"\bottomrule"
    table += [r"\end{tabular}", r"\end{table}", ""]
    values = []
    for cohort, prefix in (("confirmation", "Confirm"), ("mechanism", "Mechanism")):
        for family, label in (("opening", "Opening"), ("separator", "Separator")):
            for method, suffix in (
                ("exact", "Exact"),
                ("greedy", "Greedy"),
                ("enumeration", "Enumeration"),
            ):
                cell = cells[cohort]["llada", family, method]
                values.append(
                    r"\newcommand{\MRepair"
                    + prefix
                    + label
                    + suffix
                    + "}{"
                    + str(cell["success"])
                    + "}"
                )
                values.append(
                    r"\newcommand{\MRepair"
                    + prefix
                    + label
                    + suffix
                    + "Ms}{"
                    + f"{cell['median_ms']:.0f}"
                    + "}"
                )
    return {
        "repair-values.tex": "\n".join(values) + "\n",
        "summary.json": json.dumps(summaries, indent=2) + "\n",
        "repair-results.tex": "\n".join(table),
        "report.md": "\n".join(report),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = outputs()
    if args.check:
        for name, content in expected.items():
            if not (OUT / name).is_file() or (OUT / name).read_bytes() != content.encode():
                raise ValueError(f"repair derivative missing or modified: {name}")
        print("M21 report, table and paired analysis verified")
    else:
        OUT.mkdir(parents=True, exist_ok=True)
        for name, content in expected.items():
            (OUT / name).write_text(content)


if __name__ == "__main__":
    main()
