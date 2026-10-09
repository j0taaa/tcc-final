"""Derive the complete PL audit assessment from immutable replay records."""

from __future__ import annotations

import argparse
import json
from fractions import Fraction as Q
from pathlib import Path
from statistics import median

from summarize import summarize

MIX = "certified_tangent_mixture"
CAMPAIGNS = ("reference-replay", "dyadic-replay", "tight-replay", "final-control-replay")


def assess(evidence):
    summaries, records, events = {}, {}, {}
    for campaign in CAMPAIGNS:
        folder = evidence / campaign
        summaries[campaign] = summarize(folder)
        assert all(
            r["error"].startswith("TimeoutError(")
            for r in summaries[campaign]["unresolved_queries"]
        ), "unexpected query error"
        rows = [json.loads(line) for line in (folder / "rows.jsonl").read_text().splitlines()]
        records[campaign] = {}
        for row in rows:
            if row["stage"] != "query":
                continue
            event = (row["case"], row["rate_power"], row["k"])
            identity = {
                key: row[key]
                for key in (
                    "archived_input",
                    "event_seed",
                    "order",
                    "observed",
                    "conditional_product",
                )
            }
            assert event not in events or events[event] == identity, "different native PL event"
            events[event] = identity
            records[campaign][(*event, row["method"], row["repetition"])] = row
    final = records[CAMPAIGNS[-1]]
    exact, timing = [], []
    for event in sorted(events):
        normalizers = {}
        for method in summaries[CAMPAIGNS[-1]]["methods"]:
            values = [final[(*event, method, r)].get("normalizer") for r in range(3)]
            present = [
                Q(int(v["numerator_hex"], 16), int(v["denominator_hex"], 16))
                for v in values
                if v is not None
            ]
            assert not present or len(set(present)) == 1, "nondeterministic normalizer"
            if present:
                assert present[0] > 0
                normalizers[method] = present[0]
        if MIX in normalizers:
            ratios = {
                method: float(n / normalizers[MIX])
                for method, n in normalizers.items()
                if method not in (MIX, "enumeration")
            }
            item = {
                "case": event[0],
                "rate_power": event[1],
                "k": event[2],
                "alternative_over_mixture_expected_attempts": ratios,
                "mixture_has_strictly_fewer_expected_attempts": {
                    method: n > normalizers[MIX]
                    for method, n in normalizers.items()
                    if method not in (MIX, "enumeration")
                },
            }
            if "enumeration" in normalizers:
                target = normalizers["enumeration"]
                assert all(n >= target for n in normalizers.values())
                bound = 2 * final[(*event, MIX, 0)]["components"] + 1
                assert normalizers[MIX] / target <= bound
                item["absolute_expected_attempts"] = {
                    method: float(n / target) for method, n in normalizers.items()
                }
            exact.append(item)
        for size in (1, 4, 16):
            candidates = {}
            for campaign, rows in records.items():
                for method in summaries[campaign]["methods"]:
                    values = []
                    for repetition in range(3):
                        row = rows[(*event, method, repetition)]
                        batch = next((b for b in row["batches"] if b["accepted"] == size), None)
                        if batch:
                            values.append(batch["query_seconds"])
                    if len(values) == 3:
                        candidates[campaign + "/" + method] = median(values)
            own = candidates.get(CAMPAIGNS[-1] + "/" + MIX)
            controls = {
                key: value for key, value in candidates.items() if not key.endswith("/" + MIX)
            }
            control = min(controls, key=controls.get) if controls else None
            timing.append(
                {
                    "case": event[0],
                    "rate_power": event[1],
                    "k": event[2],
                    "batch": size,
                    "final_mixture_seconds": own,
                    "best_completed_control": control,
                    "best_control_seconds": controls[control] if control else None,
                    "control_over_mixture": controls[control] / own
                    if control and own is not None
                    else None,
                }
            )
    comparisons = {}
    for method in ("rejection_with_f_L_envelope", "single_tilt_rejection"):
        values = [
            e["alternative_over_mixture_expected_attempts"][method]
            for e in exact
            if method in e["alternative_over_mixture_expected_attempts"]
        ]
        comparisons[method] = {
            "events": len(values),
            "mixture_fewer_expected_attempts": sum(
                e["mixture_has_strictly_fewer_expected_attempts"].get(method, False) for e in exact
            ),
            "median_alternative_over_mixture": median(values) if values else None,
        }
    best_control_summary = {}
    for size in (1, 4, 16):
        rows = [r for r in timing if r["batch"] == size]
        paired = [r for r in rows if r["control_over_mixture"] is not None]
        best_control_summary[str(size)] = {
            "paired_events": len(paired),
            "mixture_faster_events": sum(r["control_over_mixture"] > 1 for r in paired),
            "only_mixture_completed": sum(
                r["final_mixture_seconds"] is not None and r["best_control_seconds"] is None
                for r in rows
            ),
            "only_control_completed": sum(
                r["final_mixture_seconds"] is None and r["best_control_seconds"] is not None
                for r in rows
            ),
        }
    correctness = json.loads((evidence / "final-control-correctness.json").read_text())
    return {
        "correctness": correctness,
        "campaigns": summaries,
        "exact_attempt_comparisons": comparisons,
        "exact_events": exact,
        "best_control_summary": best_control_summary,
        "timing_events": timing,
        "scope": "Exact rational attempt ratios; three-repeat timing is descriptive. "
        "Controls include all development refinements; no training/priority claim.",
    }


def markdown(result):
    report = result["correctness"]
    correctness = report["correctness"]
    reductions = [r["one_replica_relative_variance_reduction"] for r in report["gradient"]]
    overruns = sum(
        len(s["completed_prefix_deadline_overruns"]) for s in result["campaigns"].values()
    )
    lines = [
        "# Resultado da auditoria independente PL",
        "",
        "Gerado por `work/report.py` a partir de todos os registros. A nota original e",
        "as versões desfavoráveis permanecem preservadas. A amostragem condicional",
        "e a vantagem matemática delimitada são verificáveis; novidade/publicação",
        "e benefício em treinamento neural continuam sem confirmação.",
        "",
        "## Correção",
        "",
        f"- {correctness['events']} eventos, {correctness['conditional_original_paths']} "
        f"caminhos originais e {correctness['exact_mismatches']} divergências racionais.",
        f"- {len(report['gradient'])} casos de score completo/covariância.",
        f"- Redução com uma réplica iid nos oráculos: {min(reductions):.2%} a "
        f"{max(reductions):.2%}, mediana {median(reductions):.2%}. São fixtures, não treinamento.",
        f"- Omitir o score latente introduziu viés em "
        f"{sum(r['dropping_latent_score_is_biased'] for r in report['gradient'])} casos.",
        "- Enumeração independente, integração das decisões categóricas e reconhecedor JSON.",
        "- Não é prova integral do Python/Rust, resultado Lean novo ou revisão humana.",
        "",
        "## Todos os replays de modelo",
        "",
        "| Versão | Método | Lotes 16 completos | Inconclusivos | Fora do teto de enumeração |",
        "|---|---|---:|---:|---:|",
    ]
    for campaign, summary in result["campaigns"].items():
        for method, metrics in summary["methods"].items():
            statuses = metrics["statuses"]
            lines.append(
                f"| {campaign} | {method} | {metrics['batches']['16']['completed_prefixes']}"
                f" | {statuses.get('unresolved', 0)} | {statuses.get('not_applicable', 0)} |"
            )
    lines += [
        "",
        "Os nove inputs originais foram mantidos; oito compilaram, gerando 48",
        "eventos PL nativos. Uma preparação foi recusada pelo orçamento de células.",
        "Cada método tem três repetições por evento; preparação 30 s, amostragem",
        "cumulativa 10 s, enumeração no máximo um milhão de combinações.",
        "Os inputs já foram usados no desenvolvimento: não são avaliação externa nova.",
        "",
        f"Prefixos concluídos após o deadline cooperativo: "
        f"{overruns} "
        "nos quatro registros; os detalhes estão no JSON, sem descartá-los.",
        "",
        "## Comparação exata de tentativas",
        "",
        "`E[N]=normalizador_proposta/Z_alvo`; a razão cancela o alvo.",
        "Normalizadores racionais em hexadecimal estão nos registros originais.",
        "",
        "| Controle | Eventos comparáveis | Mistura com menos tentativas esperadas "
        "| Mediana controle/mistura |",
        "|---|---:|---:|---:|",
    ]
    for method, values in result["exact_attempt_comparisons"].items():
        ratio = values["median_alternative_over_mixture"]
        lines.append(
            f"| {method} | {values['events']} | {values['mixture_fewer_expected_attempts']}"
            f" | {ratio:.6g} |"
        )
    lines += [
        "",
        "A inclinação única usa o majorante secante ótimo de sua família, com taxa",
        "aproximada em 80 dígitos e rejeição racional exata. A diferença de tentativas",
        "não inclui preparação e não implica vantagem de tempo.",
        "",
        "## Custo completo da consulta contra o melhor controle registrado",
        "",
        "| Lote | Eventos pareados | Mistura mais rápida "
        "| Só mistura concluiu | Só controle concluiu |",
        "|---|---:|---:|---:|---:|",
    ]
    for size, values in result["best_control_summary"].items():
        lines.append(
            f"| {size} | {values['paired_events']} | {values['mixture_faster_events']}"
            f" | {values['only_mixture_completed']} | {values['only_control_completed']} |"
        )
    lines += [
        "",
        "Escolher o melhor controle entre versões é um controle otimista de",
        "diagnóstico, não um seletor implementado. Usa mediana das três repetições",
        "somente quando todas concluíram aquele prefixo. Timeouts permanecem censurados.",
        "O custo inclui preparação condicional; a compilação comum é publicada",
        "separadamente. Enumeração independente não requer essa compilação.",
        "Forward, backward e recompensa não foram executados.",
        "",
        "## O que a matemática sustenta",
        "",
        "A redução condicional PL, o envelope fatorável racional e o limite de",
        "tentativas estão em [mathematical-review.md](mathematical-review.md).",
        "A prova escrita [product-proposal-separation.md](product-proposal-separation.md)",
        "mostra uma família JSON em que **qualquer proposta produto única** precisa",
        "de esperança pelo menos `exp(m/360)/3`, contra `O(sqrt(m))` da mistura.",
        "A família é objeto de prova; um contador especializado também é polinomial.",
        "Não há alegação contra todos os solvers nem exclusividade do benefício.",
        "",
        "A identidade de Rao-Blackwellização garante redução de variância quando",
        "há ruído latente; ela é antecedente conhecido. Ganho por tempo exige que",
        "a redução supere o custo adicional, que este replay não mede em treinamento.",
        "A política deve registrar a seleção PL e incluir seu score/normalização.",
        "Não há justificativa automática para clipping PPO/GRPO.",
        "",
        "Há uma objeção adicional em "
        "[auxiliary-variable-objection.md](auxiliary-variable-objection.md):",
        "um passo Gibbs com auxiliares PL pode iniciar na proposta original já",
        "em estacionariedade, gerando uma réplica correlacionada sem viés e",
        "com variância não maior. Não foi implementado ou medido. Réplicas iid",
        "não são obrigatórias para reduzir variância; esse controle deve entrar",
        "na avaliação de treinamento antes de reivindicar vantagem de aplicação.",
        "",
        "## Decisão científica",
        "",
        "Confirmado nesta auditoria: consistência exata nas instâncias verificadas",
        "e prova escrita de uma vantagem assintótica contra uma classe precisa.",
        "Não confirmado: prioridade/significância acadêmica própria, redução de",
        "custo neural total, melhoria de geração ou treinamento de uma dLLM.",
        "Portanto isto não autoriza anunciar que todos os requisitos do TCC",
        "foram atendidos. O próximo gate é anterioridade do kernel/limite e",
        "benefício por custo em uma política on-policy real contra esse controle,",
        "não mais exemplos",
        "escolhidos para mostrar JSON válido.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()
    result = assess(args.evidence)
    with args.json.open("x") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
    with args.markdown.open("x") as stream:
        stream.write(markdown(result))
