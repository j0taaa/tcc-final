# Reparo certificado de JSON: resultados controlados M21

Relatório gerado a partir de arquivos brutos com hashes e avaliação independente. Não contém inferência de modelo nem comparação com uma nova chamada ao modelo.

Os perfis de bytes e LLaDA são separados. O segundo usa o tokenizer real, não saídas reais do modelo. Valores e tamanhos da confirmação diferem do piloto; os exemplos compartilham mecanismos de corrupção definidos previamente. A mistura balanceada não estima a frequência de erros em produção.

Sucesso exige recuperar todos os dados, preservando tipos e estrutura. Um documento só conta como sucesso estável se todas as repetições passarem. Tempos são medianas das medianas por documento, incluindo falhas e censura; razões de velocidade só usam pares conjuntamente bem-sucedidos.

## pilot

Commit de medição: `47b93c475ca961b97063d409f9b8c4c29ba580c8`. Configuração: `m21_repair_pilot_v1`. Chamadas: 384.

| Perfil | Classe | Método | Documentos corretos | Mediana total (ms) |
|---|---|---|---:|---:|
| bytes | valid | Unchanged | 4/4 | 0.01 |
| bytes | valid | JSON repair | 4/4 | 0.10 |
| bytes | valid | Schema standard | 4/4 | 0.55 |
| bytes | valid | Schema salvage | 4/4 | 0.51 |
| bytes | valid | Enumeration | 4/4 | 3.22 |
| bytes | valid | Unweighted CFG | 4/4 | 69.24 |
| bytes | valid | Greedy CFG | 4/4 | 69.88 |
| bytes | valid | Exact MWPC | 4/4 | 68.43 |
| bytes | opening | Unchanged | 0/4 | 0.01 |
| bytes | opening | JSON repair | 0/4 | 0.41 |
| bytes | opening | Schema standard | 0/4 | 0.50 |
| bytes | opening | Schema salvage | 0/4 | 0.93 |
| bytes | opening | Enumeration | 4/4 | 5.32 |
| bytes | opening | Unweighted CFG | 4/4 | 75.95 |
| bytes | opening | Greedy CFG | 4/4 | 75.66 |
| bytes | opening | Exact MWPC | 4/4 | 71.28 |
| bytes | closing | Unchanged | 0/4 | 0.01 |
| bytes | closing | JSON repair | 2/4 | 0.39 |
| bytes | closing | Schema standard | 2/4 | 0.95 |
| bytes | closing | Schema salvage | 2/4 | 0.91 |
| bytes | closing | Enumeration | 4/4 | 4.10 |
| bytes | closing | Unweighted CFG | 4/4 | 68.08 |
| bytes | closing | Greedy CFG | 4/4 | 72.30 |
| bytes | closing | Exact MWPC | 4/4 | 69.28 |
| bytes | separator | Unchanged | 0/4 | 0.01 |
| bytes | separator | JSON repair | 4/4 | 0.46 |
| bytes | separator | Schema standard | 4/4 | 0.99 |
| bytes | separator | Schema salvage | 4/4 | 0.97 |
| bytes | separator | Enumeration | 4/4 | 29.15 |
| bytes | separator | Unweighted CFG | 4/4 | 68.33 |
| bytes | separator | Greedy CFG | 4/4 | 76.46 |
| bytes | separator | Exact MWPC | 4/4 | 68.92 |
| bytes | missing_suffix | Unchanged | 0/4 | 0.01 |
| bytes | missing_suffix | JSON repair | 4/4 | 0.43 |
| bytes | missing_suffix | Schema standard | 4/4 | 1.11 |
| bytes | missing_suffix | Schema salvage | 4/4 | 1.09 |
| bytes | missing_suffix | Enumeration | 0/4 | 969.82 |
| bytes | missing_suffix | Unweighted CFG | 0/4 | 9.27 |
| bytes | missing_suffix | Greedy CFG | 0/4 | 9.79 |
| bytes | missing_suffix | Exact MWPC | 0/4 | 10.08 |
| bytes | semantic | Unchanged | 0/4 | 0.01 |
| bytes | semantic | JSON repair | 0/4 | 0.11 |
| bytes | semantic | Schema standard | 0/4 | 0.52 |
| bytes | semantic | Schema salvage | 0/4 | 0.54 |
| bytes | semantic | Enumeration | 0/4 | 3.60 |
| bytes | semantic | Unweighted CFG | 0/4 | 69.08 |
| bytes | semantic | Greedy CFG | 0/4 | 70.62 |
| bytes | semantic | Exact MWPC | 0/4 | 69.28 |
| llada | valid | Unchanged | 4/4 | 0.01 |
| llada | valid | JSON repair | 4/4 | 0.10 |
| llada | valid | Schema standard | 4/4 | 0.50 |
| llada | valid | Schema salvage | 4/4 | 0.50 |
| llada | valid | Enumeration | 4/4 | 61.74 |
| llada | valid | Unweighted CFG | 4/4 | 167.86 |
| llada | valid | Greedy CFG | 4/4 | 196.69 |
| llada | valid | Exact MWPC | 4/4 | 170.37 |
| llada | opening | Unchanged | 0/4 | 0.01 |
| llada | opening | JSON repair | 0/4 | 0.41 |
| llada | opening | Schema standard | 0/4 | 0.47 |
| llada | opening | Schema salvage | 0/4 | 0.92 |
| llada | opening | Enumeration | 4/4 | 62.65 |
| llada | opening | Unweighted CFG | 4/4 | 171.60 |
| llada | opening | Greedy CFG | 4/4 | 251.58 |
| llada | opening | Exact MWPC | 4/4 | 170.75 |
| llada | closing | Unchanged | 0/4 | 0.01 |
| llada | closing | JSON repair | 2/4 | 0.40 |
| llada | closing | Schema standard | 2/4 | 1.03 |
| llada | closing | Schema salvage | 2/4 | 0.93 |
| llada | closing | Enumeration | 4/4 | 66.63 |
| llada | closing | Unweighted CFG | 4/4 | 165.91 |
| llada | closing | Greedy CFG | 4/4 | 258.82 |
| llada | closing | Exact MWPC | 4/4 | 166.78 |
| llada | separator | Unchanged | 0/4 | 0.01 |
| llada | separator | JSON repair | 4/4 | 0.48 |
| llada | separator | Schema standard | 4/4 | 1.02 |
| llada | separator | Schema salvage | 4/4 | 1.02 |
| llada | separator | Enumeration | 4/4 | 77.46 |
| llada | separator | Unweighted CFG | 4/4 | 163.94 |
| llada | separator | Greedy CFG | 4/4 | 299.12 |
| llada | separator | Exact MWPC | 4/4 | 165.29 |
| llada | missing_suffix | Unchanged | 0/4 | 0.01 |
| llada | missing_suffix | JSON repair | 4/4 | 0.38 |
| llada | missing_suffix | Schema standard | 4/4 | 0.92 |
| llada | missing_suffix | Schema salvage | 4/4 | 0.98 |
| llada | missing_suffix | Enumeration | 0/4 | 228.77 |
| llada | missing_suffix | Unweighted CFG | 0/4 | 110.26 |
| llada | missing_suffix | Greedy CFG | 0/4 | 137.07 |
| llada | missing_suffix | Exact MWPC | 0/4 | 112.35 |
| llada | semantic | Unchanged | 0/4 | 0.01 |
| llada | semantic | JSON repair | 0/4 | 0.12 |
| llada | semantic | Schema standard | 0/4 | 0.52 |
| llada | semantic | Schema salvage | 0/4 | 0.51 |
| llada | semantic | Enumeration | 0/4 | 61.90 |
| llada | semantic | Unweighted CFG | 0/4 | 166.79 |
| llada | semantic | Greedy CFG | 0/4 | 193.23 |
| llada | semantic | Exact MWPC | 0/4 | 167.41 |

Comparações pareadas e intervalos descritivos por documento:

| Perfil | Classe | Comparador | Só exato vence | Só comparador vence | Ambos vencem | Velocidade comparador/exato (IC 95%) |
|---|---|---|---:|---:|---:|---|
| bytes | closing | enumeration | 0 | 0 | 4 | 0.06 (0.06-0.07) |
| bytes | closing | feasibility | 0 | 0 | 4 | 1.00 (0.91-1.03) |
| bytes | closing | greedy | 0 | 0 | 4 | 1.06 (1.00-1.08) |
| bytes | closing | json_repair | 2 | 0 | 2 | 0.01 (0.01-0.01) |
| bytes | closing | schema_salvage | 2 | 0 | 2 | 0.02 (0.02-0.02) |
| bytes | closing | schema_standard | 2 | 0 | 2 | 0.02 (0.02-0.02) |
| bytes | closing | unchanged | 4 | 0 | 0 | - |
| bytes | missing_suffix | enumeration | 0 | 0 | 0 | - |
| bytes | missing_suffix | feasibility | 0 | 0 | 0 | - |
| bytes | missing_suffix | greedy | 0 | 0 | 0 | - |
| bytes | missing_suffix | json_repair | 0 | 4 | 0 | - |
| bytes | missing_suffix | schema_salvage | 0 | 4 | 0 | - |
| bytes | missing_suffix | schema_standard | 0 | 4 | 0 | - |
| bytes | missing_suffix | unchanged | 0 | 0 | 0 | - |
| bytes | opening | enumeration | 0 | 0 | 4 | 0.09 (0.06-0.15) |
| bytes | opening | feasibility | 0 | 0 | 4 | 0.99 (0.96-1.24) |
| bytes | opening | greedy | 0 | 0 | 4 | 1.06 (1.02-1.09) |
| bytes | opening | json_repair | 4 | 0 | 0 | - |
| bytes | opening | schema_salvage | 4 | 0 | 0 | - |
| bytes | opening | schema_standard | 4 | 0 | 0 | - |
| bytes | opening | unchanged | 4 | 0 | 0 | - |
| bytes | semantic | enumeration | 0 | 0 | 0 | - |
| bytes | semantic | feasibility | 0 | 0 | 0 | - |
| bytes | semantic | greedy | 0 | 0 | 0 | - |
| bytes | semantic | json_repair | 0 | 0 | 0 | - |
| bytes | semantic | schema_salvage | 0 | 0 | 0 | - |
| bytes | semantic | schema_standard | 0 | 0 | 0 | - |
| bytes | semantic | unchanged | 0 | 0 | 0 | - |
| bytes | separator | enumeration | 0 | 0 | 4 | 0.33 (0.09-0.56) |
| bytes | separator | feasibility | 0 | 0 | 4 | 0.98 (0.97-1.01) |
| bytes | separator | greedy | 0 | 0 | 4 | 1.11 (1.09-1.11) |
| bytes | separator | json_repair | 0 | 0 | 4 | 0.01 (0.01-0.01) |
| bytes | separator | schema_salvage | 0 | 0 | 4 | 0.02 (0.01-0.02) |
| bytes | separator | schema_standard | 0 | 0 | 4 | 0.02 (0.01-0.02) |
| bytes | separator | unchanged | 4 | 0 | 0 | - |
| bytes | valid | enumeration | 0 | 0 | 4 | 0.05 (0.03-0.08) |
| bytes | valid | feasibility | 0 | 0 | 4 | 1.00 (0.98-1.05) |
| bytes | valid | greedy | 0 | 0 | 4 | 1.00 (0.99-1.07) |
| bytes | valid | json_repair | 0 | 0 | 4 | 0.00 (0.00-0.00) |
| bytes | valid | schema_salvage | 0 | 0 | 4 | 0.01 (0.01-0.02) |
| bytes | valid | schema_standard | 0 | 0 | 4 | 0.01 (0.01-0.01) |
| bytes | valid | unchanged | 0 | 0 | 4 | 0.00 (0.00-0.00) |
| llada | closing | enumeration | 0 | 0 | 4 | 0.41 (0.33-0.49) |
| llada | closing | feasibility | 0 | 0 | 4 | 0.99 (0.97-1.00) |
| llada | closing | greedy | 0 | 0 | 4 | 1.50 (1.43-1.59) |
| llada | closing | json_repair | 2 | 0 | 2 | 0.00 (0.00-0.00) |
| llada | closing | schema_salvage | 2 | 0 | 2 | 0.01 (0.01-0.01) |
| llada | closing | schema_standard | 2 | 0 | 2 | 0.01 (0.01-0.02) |
| llada | closing | unchanged | 4 | 0 | 0 | - |
| llada | missing_suffix | enumeration | 0 | 0 | 0 | - |
| llada | missing_suffix | feasibility | 0 | 0 | 0 | - |
| llada | missing_suffix | greedy | 0 | 0 | 0 | - |
| llada | missing_suffix | json_repair | 0 | 4 | 0 | - |
| llada | missing_suffix | schema_salvage | 0 | 4 | 0 | - |
| llada | missing_suffix | schema_standard | 0 | 4 | 0 | - |
| llada | missing_suffix | unchanged | 0 | 0 | 0 | - |
| llada | opening | enumeration | 0 | 0 | 4 | 0.39 (0.32-0.52) |
| llada | opening | feasibility | 0 | 0 | 4 | 1.00 (0.99-1.01) |
| llada | opening | greedy | 0 | 0 | 4 | 1.50 (1.40-1.54) |
| llada | opening | json_repair | 4 | 0 | 0 | - |
| llada | opening | schema_salvage | 4 | 0 | 0 | - |
| llada | opening | schema_standard | 4 | 0 | 0 | - |
| llada | opening | unchanged | 4 | 0 | 0 | - |
| llada | semantic | enumeration | 0 | 0 | 0 | - |
| llada | semantic | feasibility | 0 | 0 | 0 | - |
| llada | semantic | greedy | 0 | 0 | 0 | - |
| llada | semantic | json_repair | 0 | 0 | 0 | - |
| llada | semantic | schema_salvage | 0 | 0 | 0 | - |
| llada | semantic | schema_standard | 0 | 0 | 0 | - |
| llada | semantic | unchanged | 0 | 0 | 0 | - |
| llada | separator | enumeration | 0 | 0 | 4 | 0.47 (0.45-0.51) |
| llada | separator | feasibility | 0 | 0 | 4 | 0.99 (0.98-1.00) |
| llada | separator | greedy | 0 | 0 | 4 | 1.79 (1.69-1.90) |
| llada | separator | json_repair | 0 | 0 | 4 | 0.00 (0.00-0.00) |
| llada | separator | schema_salvage | 0 | 0 | 4 | 0.01 (0.00-0.01) |
| llada | separator | schema_standard | 0 | 0 | 4 | 0.01 (0.01-0.01) |
| llada | separator | unchanged | 4 | 0 | 0 | - |
| llada | valid | enumeration | 0 | 0 | 4 | 0.39 (0.28-0.51) |
| llada | valid | feasibility | 0 | 0 | 4 | 1.00 (0.99-1.01) |
| llada | valid | greedy | 0 | 0 | 4 | 1.16 (1.14-1.19) |
| llada | valid | json_repair | 0 | 0 | 4 | 0.00 (0.00-0.00) |
| llada | valid | schema_salvage | 0 | 0 | 4 | 0.00 (0.00-0.00) |
| llada | valid | schema_standard | 0 | 0 | 4 | 0.00 (0.00-0.00) |
| llada | valid | unchanged | 0 | 0 | 4 | 0.00 (0.00-0.00) |

Contagens completas de status:

```json
[
  {
    "profile": "bytes",
    "family": "closing",
    "method": "enumeration",
    "statuses": {
      "optimal": 4
    }
  },
  {
    "profile": "bytes",
    "family": "closing",
    "method": "exact",
    "statuses": {
      "optimal": 4
    }
  },
  {
    "profile": "bytes",
    "family": "closing",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 4
    }
  },
  {
    "profile": "bytes",
    "family": "closing",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 4
    }
  },
  {
    "profile": "bytes",
    "family": "closing",
    "method": "json_repair",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "bytes",
    "family": "closing",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "bytes",
    "family": "closing",
    "method": "schema_standard",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "bytes",
    "family": "closing",
    "method": "unchanged",
    "statuses": {
      "unchanged": 4
    }
  },
  {
    "profile": "bytes",
    "family": "missing_suffix",
    "method": "enumeration",
    "statuses": {
      "infeasible_on_support": 4
    }
  },
  {
    "profile": "bytes",
    "family": "missing_suffix",
    "method": "exact",
    "statuses": {
      "infeasible_on_support": 4
    }
  },
  {
    "profile": "bytes",
    "family": "missing_suffix",
    "method": "feasibility",
    "statuses": {
      "infeasible_on_support": 4
    }
  },
  {
    "profile": "bytes",
    "family": "missing_suffix",
    "method": "greedy",
    "statuses": {
      "infeasible_on_support": 4
    }
  },
  {
    "profile": "bytes",
    "family": "missing_suffix",
    "method": "json_repair",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "bytes",
    "family": "missing_suffix",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "bytes",
    "family": "missing_suffix",
    "method": "schema_standard",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "bytes",
    "family": "missing_suffix",
    "method": "unchanged",
    "statuses": {
      "unchanged": 4
    }
  },
  {
    "profile": "bytes",
    "family": "opening",
    "method": "enumeration",
    "statuses": {
      "optimal": 4
    }
  },
  {
    "profile": "bytes",
    "family": "opening",
    "method": "exact",
    "statuses": {
      "optimal": 4
    }
  },
  {
    "profile": "bytes",
    "family": "opening",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 4
    }
  },
  {
    "profile": "bytes",
    "family": "opening",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 4
    }
  },
  {
    "profile": "bytes",
    "family": "opening",
    "method": "json_repair",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "bytes",
    "family": "opening",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "bytes",
    "family": "opening",
    "method": "schema_standard",
    "statuses": {
      "error": 4
    }
  },
  {
    "profile": "bytes",
    "family": "opening",
    "method": "unchanged",
    "statuses": {
      "unchanged": 4
    }
  },
  {
    "profile": "bytes",
    "family": "semantic",
    "method": "enumeration",
    "statuses": {
      "optimal": 4
    }
  },
  {
    "profile": "bytes",
    "family": "semantic",
    "method": "exact",
    "statuses": {
      "optimal": 4
    }
  },
  {
    "profile": "bytes",
    "family": "semantic",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 4
    }
  },
  {
    "profile": "bytes",
    "family": "semantic",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 4
    }
  },
  {
    "profile": "bytes",
    "family": "semantic",
    "method": "json_repair",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "bytes",
    "family": "semantic",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "bytes",
    "family": "semantic",
    "method": "schema_standard",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "bytes",
    "family": "semantic",
    "method": "unchanged",
    "statuses": {
      "unchanged": 4
    }
  },
  {
    "profile": "bytes",
    "family": "separator",
    "method": "enumeration",
    "statuses": {
      "optimal": 4
    }
  },
  {
    "profile": "bytes",
    "family": "separator",
    "method": "exact",
    "statuses": {
      "optimal": 4
    }
  },
  {
    "profile": "bytes",
    "family": "separator",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 4
    }
  },
  {
    "profile": "bytes",
    "family": "separator",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 4
    }
  },
  {
    "profile": "bytes",
    "family": "separator",
    "method": "json_repair",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "bytes",
    "family": "separator",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "bytes",
    "family": "separator",
    "method": "schema_standard",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "bytes",
    "family": "separator",
    "method": "unchanged",
    "statuses": {
      "unchanged": 4
    }
  },
  {
    "profile": "bytes",
    "family": "valid",
    "method": "enumeration",
    "statuses": {
      "optimal": 4
    }
  },
  {
    "profile": "bytes",
    "family": "valid",
    "method": "exact",
    "statuses": {
      "optimal": 4
    }
  },
  {
    "profile": "bytes",
    "family": "valid",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 4
    }
  },
  {
    "profile": "bytes",
    "family": "valid",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 4
    }
  },
  {
    "profile": "bytes",
    "family": "valid",
    "method": "json_repair",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "bytes",
    "family": "valid",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "bytes",
    "family": "valid",
    "method": "schema_standard",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "bytes",
    "family": "valid",
    "method": "unchanged",
    "statuses": {
      "unchanged": 4
    }
  },
  {
    "profile": "llada",
    "family": "closing",
    "method": "enumeration",
    "statuses": {
      "optimal": 4
    }
  },
  {
    "profile": "llada",
    "family": "closing",
    "method": "exact",
    "statuses": {
      "optimal": 4
    }
  },
  {
    "profile": "llada",
    "family": "closing",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 4
    }
  },
  {
    "profile": "llada",
    "family": "closing",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 4
    }
  },
  {
    "profile": "llada",
    "family": "closing",
    "method": "json_repair",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "llada",
    "family": "closing",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "llada",
    "family": "closing",
    "method": "schema_standard",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "llada",
    "family": "closing",
    "method": "unchanged",
    "statuses": {
      "unchanged": 4
    }
  },
  {
    "profile": "llada",
    "family": "missing_suffix",
    "method": "enumeration",
    "statuses": {
      "infeasible_on_support": 4
    }
  },
  {
    "profile": "llada",
    "family": "missing_suffix",
    "method": "exact",
    "statuses": {
      "infeasible_on_support": 4
    }
  },
  {
    "profile": "llada",
    "family": "missing_suffix",
    "method": "feasibility",
    "statuses": {
      "infeasible_on_support": 4
    }
  },
  {
    "profile": "llada",
    "family": "missing_suffix",
    "method": "greedy",
    "statuses": {
      "infeasible_on_support": 4
    }
  },
  {
    "profile": "llada",
    "family": "missing_suffix",
    "method": "json_repair",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "llada",
    "family": "missing_suffix",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "llada",
    "family": "missing_suffix",
    "method": "schema_standard",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "llada",
    "family": "missing_suffix",
    "method": "unchanged",
    "statuses": {
      "unchanged": 4
    }
  },
  {
    "profile": "llada",
    "family": "opening",
    "method": "enumeration",
    "statuses": {
      "optimal": 4
    }
  },
  {
    "profile": "llada",
    "family": "opening",
    "method": "exact",
    "statuses": {
      "optimal": 4
    }
  },
  {
    "profile": "llada",
    "family": "opening",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 4
    }
  },
  {
    "profile": "llada",
    "family": "opening",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 4
    }
  },
  {
    "profile": "llada",
    "family": "opening",
    "method": "json_repair",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "llada",
    "family": "opening",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "llada",
    "family": "opening",
    "method": "schema_standard",
    "statuses": {
      "error": 4
    }
  },
  {
    "profile": "llada",
    "family": "opening",
    "method": "unchanged",
    "statuses": {
      "unchanged": 4
    }
  },
  {
    "profile": "llada",
    "family": "semantic",
    "method": "enumeration",
    "statuses": {
      "optimal": 4
    }
  },
  {
    "profile": "llada",
    "family": "semantic",
    "method": "exact",
    "statuses": {
      "optimal": 4
    }
  },
  {
    "profile": "llada",
    "family": "semantic",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 4
    }
  },
  {
    "profile": "llada",
    "family": "semantic",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 4
    }
  },
  {
    "profile": "llada",
    "family": "semantic",
    "method": "json_repair",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "llada",
    "family": "semantic",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "llada",
    "family": "semantic",
    "method": "schema_standard",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "llada",
    "family": "semantic",
    "method": "unchanged",
    "statuses": {
      "unchanged": 4
    }
  },
  {
    "profile": "llada",
    "family": "separator",
    "method": "enumeration",
    "statuses": {
      "optimal": 4
    }
  },
  {
    "profile": "llada",
    "family": "separator",
    "method": "exact",
    "statuses": {
      "optimal": 4
    }
  },
  {
    "profile": "llada",
    "family": "separator",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 4
    }
  },
  {
    "profile": "llada",
    "family": "separator",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 4
    }
  },
  {
    "profile": "llada",
    "family": "separator",
    "method": "json_repair",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "llada",
    "family": "separator",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "llada",
    "family": "separator",
    "method": "schema_standard",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "llada",
    "family": "separator",
    "method": "unchanged",
    "statuses": {
      "unchanged": 4
    }
  },
  {
    "profile": "llada",
    "family": "valid",
    "method": "enumeration",
    "statuses": {
      "optimal": 4
    }
  },
  {
    "profile": "llada",
    "family": "valid",
    "method": "exact",
    "statuses": {
      "optimal": 4
    }
  },
  {
    "profile": "llada",
    "family": "valid",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 4
    }
  },
  {
    "profile": "llada",
    "family": "valid",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 4
    }
  },
  {
    "profile": "llada",
    "family": "valid",
    "method": "json_repair",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "llada",
    "family": "valid",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "llada",
    "family": "valid",
    "method": "schema_standard",
    "statuses": {
      "repaired": 4
    }
  },
  {
    "profile": "llada",
    "family": "valid",
    "method": "unchanged",
    "statuses": {
      "unchanged": 4
    }
  }
]
```

## confirmation

Commit de medição: `47b93c475ca961b97063d409f9b8c4c29ba580c8`. Configuração: `m21_repair_confirmation_v1`. Chamadas: 3840.

| Perfil | Classe | Método | Documentos corretos | Mediana total (ms) |
|---|---|---|---:|---:|
| bytes | valid | Unchanged | 20/20 | 0.01 |
| bytes | valid | JSON repair | 20/20 | 0.11 |
| bytes | valid | Schema standard | 20/20 | 0.60 |
| bytes | valid | Schema salvage | 20/20 | 0.58 |
| bytes | valid | Enumeration | 20/20 | 4.19 |
| bytes | valid | Unweighted CFG | 20/20 | 253.50 |
| bytes | valid | Greedy CFG | 20/20 | 256.03 |
| bytes | valid | Exact MWPC | 20/20 | 251.65 |
| bytes | opening | Unchanged | 0/20 | 0.01 |
| bytes | opening | JSON repair | 0/20 | 0.50 |
| bytes | opening | Schema standard | 0/20 | 0.59 |
| bytes | opening | Schema salvage | 0/20 | 1.07 |
| bytes | opening | Enumeration | 20/20 | 203.94 |
| bytes | opening | Unweighted CFG | 20/20 | 252.41 |
| bytes | opening | Greedy CFG | 20/20 | 269.19 |
| bytes | opening | Exact MWPC | 20/20 | 251.72 |
| bytes | closing | Unchanged | 0/20 | 0.01 |
| bytes | closing | JSON repair | 0/20 | 0.46 |
| bytes | closing | Schema standard | 0/20 | 0.99 |
| bytes | closing | Schema salvage | 0/20 | 1.01 |
| bytes | closing | Enumeration | 20/20 | 263.71 |
| bytes | closing | Unweighted CFG | 20/20 | 250.29 |
| bytes | closing | Greedy CFG | 20/20 | 267.73 |
| bytes | closing | Exact MWPC | 20/20 | 251.19 |
| bytes | separator | Unchanged | 0/20 | 0.01 |
| bytes | separator | JSON repair | 20/20 | 0.60 |
| bytes | separator | Schema standard | 20/20 | 1.19 |
| bytes | separator | Schema salvage | 20/20 | 1.24 |
| bytes | separator | Enumeration | 0/20 | 2000.01 |
| bytes | separator | Unweighted CFG | 20/20 | 258.79 |
| bytes | separator | Greedy CFG | 20/20 | 293.91 |
| bytes | separator | Exact MWPC | 20/20 | 260.43 |
| bytes | missing_suffix | Unchanged | 0/20 | 0.01 |
| bytes | missing_suffix | JSON repair | 20/20 | 0.48 |
| bytes | missing_suffix | Schema standard | 20/20 | 1.13 |
| bytes | missing_suffix | Schema salvage | 20/20 | 1.17 |
| bytes | missing_suffix | Enumeration | 0/20 | 2000.02 |
| bytes | missing_suffix | Unweighted CFG | 0/20 | 14.07 |
| bytes | missing_suffix | Greedy CFG | 0/20 | 15.09 |
| bytes | missing_suffix | Exact MWPC | 0/20 | 15.92 |
| bytes | semantic | Unchanged | 0/20 | 0.01 |
| bytes | semantic | JSON repair | 0/20 | 0.12 |
| bytes | semantic | Schema standard | 0/20 | 0.59 |
| bytes | semantic | Schema salvage | 0/20 | 0.61 |
| bytes | semantic | Enumeration | 0/20 | 4.06 |
| bytes | semantic | Unweighted CFG | 0/20 | 254.32 |
| bytes | semantic | Greedy CFG | 0/20 | 251.64 |
| bytes | semantic | Exact MWPC | 0/20 | 252.39 |
| llada | valid | Unchanged | 20/20 | 0.01 |
| llada | valid | JSON repair | 20/20 | 0.11 |
| llada | valid | Schema standard | 20/20 | 0.58 |
| llada | valid | Schema salvage | 20/20 | 0.59 |
| llada | valid | Enumeration | 20/20 | 88.87 |
| llada | valid | Unweighted CFG | 20/20 | 383.98 |
| llada | valid | Greedy CFG | 20/20 | 409.68 |
| llada | valid | Exact MWPC | 20/20 | 385.81 |
| llada | opening | Unchanged | 0/20 | 0.01 |
| llada | opening | JSON repair | 0/20 | 0.51 |
| llada | opening | Schema standard | 0/20 | 0.59 |
| llada | opening | Schema salvage | 0/20 | 1.05 |
| llada | opening | Enumeration | 20/20 | 229.00 |
| llada | opening | Unweighted CFG | 20/20 | 384.17 |
| llada | opening | Greedy CFG | 20/20 | 546.50 |
| llada | opening | Exact MWPC | 20/20 | 386.57 |
| llada | closing | Unchanged | 0/20 | 0.01 |
| llada | closing | JSON repair | 0/20 | 0.46 |
| llada | closing | Schema standard | 0/20 | 0.97 |
| llada | closing | Schema salvage | 0/20 | 1.02 |
| llada | closing | Enumeration | 20/20 | 304.96 |
| llada | closing | Unweighted CFG | 20/20 | 384.97 |
| llada | closing | Greedy CFG | 20/20 | 543.66 |
| llada | closing | Exact MWPC | 20/20 | 384.92 |
| llada | separator | Unchanged | 0/20 | 0.01 |
| llada | separator | JSON repair | 20/20 | 0.59 |
| llada | separator | Schema standard | 20/20 | 1.19 |
| llada | separator | Schema salvage | 20/20 | 1.29 |
| llada | separator | Enumeration | 10/20 | 1877.04 |
| llada | separator | Unweighted CFG | 20/20 | 389.29 |
| llada | separator | Greedy CFG | 20/20 | 685.46 |
| llada | separator | Exact MWPC | 20/20 | 391.78 |
| llada | missing_suffix | Unchanged | 0/20 | 0.01 |
| llada | missing_suffix | JSON repair | 20/20 | 0.47 |
| llada | missing_suffix | Schema standard | 20/20 | 1.09 |
| llada | missing_suffix | Schema salvage | 20/20 | 1.15 |
| llada | missing_suffix | Enumeration | 0/20 | 2000.01 |
| llada | missing_suffix | Unweighted CFG | 0/20 | 140.87 |
| llada | missing_suffix | Greedy CFG | 0/20 | 168.44 |
| llada | missing_suffix | Exact MWPC | 0/20 | 142.03 |
| llada | semantic | Unchanged | 0/20 | 0.01 |
| llada | semantic | JSON repair | 0/20 | 0.12 |
| llada | semantic | Schema standard | 0/20 | 0.57 |
| llada | semantic | Schema salvage | 0/20 | 0.59 |
| llada | semantic | Enumeration | 0/20 | 93.46 |
| llada | semantic | Unweighted CFG | 0/20 | 367.36 |
| llada | semantic | Greedy CFG | 0/20 | 396.63 |
| llada | semantic | Exact MWPC | 0/20 | 370.77 |

Comparações pareadas e intervalos descritivos por documento:

| Perfil | Classe | Comparador | Só exato vence | Só comparador vence | Ambos vencem | Velocidade comparador/exato (IC 95%) |
|---|---|---|---:|---:|---:|---|
| bytes | closing | enumeration | 0 | 0 | 20 | 0.87 (0.19-1.58) |
| bytes | closing | feasibility | 0 | 0 | 20 | 0.99 (0.99-1.00) |
| bytes | closing | greedy | 0 | 0 | 20 | 1.07 (1.06-1.07) |
| bytes | closing | json_repair | 20 | 0 | 0 | - |
| bytes | closing | schema_salvage | 20 | 0 | 0 | - |
| bytes | closing | schema_standard | 20 | 0 | 0 | - |
| bytes | closing | unchanged | 20 | 0 | 0 | - |
| bytes | missing_suffix | enumeration | 0 | 0 | 0 | - |
| bytes | missing_suffix | feasibility | 0 | 0 | 0 | - |
| bytes | missing_suffix | greedy | 0 | 0 | 0 | - |
| bytes | missing_suffix | json_repair | 0 | 20 | 0 | - |
| bytes | missing_suffix | schema_salvage | 0 | 20 | 0 | - |
| bytes | missing_suffix | schema_standard | 0 | 20 | 0 | - |
| bytes | missing_suffix | unchanged | 0 | 0 | 0 | - |
| bytes | opening | enumeration | 0 | 0 | 20 | 0.68 (0.15-1.22) |
| bytes | opening | feasibility | 0 | 0 | 20 | 1.00 (0.99-1.00) |
| bytes | opening | greedy | 0 | 0 | 20 | 1.07 (1.07-1.07) |
| bytes | opening | json_repair | 20 | 0 | 0 | - |
| bytes | opening | schema_salvage | 20 | 0 | 0 | - |
| bytes | opening | schema_standard | 20 | 0 | 0 | - |
| bytes | opening | unchanged | 20 | 0 | 0 | - |
| bytes | semantic | enumeration | 0 | 0 | 0 | - |
| bytes | semantic | feasibility | 0 | 0 | 0 | - |
| bytes | semantic | greedy | 0 | 0 | 0 | - |
| bytes | semantic | json_repair | 0 | 0 | 0 | - |
| bytes | semantic | schema_salvage | 0 | 0 | 0 | - |
| bytes | semantic | schema_standard | 0 | 0 | 0 | - |
| bytes | semantic | unchanged | 0 | 0 | 0 | - |
| bytes | separator | enumeration | 20 | 0 | 0 | - |
| bytes | separator | feasibility | 0 | 0 | 20 | 0.99 (0.99-1.00) |
| bytes | separator | greedy | 0 | 0 | 20 | 1.13 (1.12-1.13) |
| bytes | separator | json_repair | 0 | 0 | 20 | 0.00 (0.00-0.00) |
| bytes | separator | schema_salvage | 0 | 0 | 20 | 0.01 (0.00-0.01) |
| bytes | separator | schema_standard | 0 | 0 | 20 | 0.00 (0.00-0.01) |
| bytes | separator | unchanged | 20 | 0 | 0 | - |
| bytes | valid | enumeration | 0 | 0 | 20 | 0.02 (0.01-0.02) |
| bytes | valid | feasibility | 0 | 0 | 20 | 1.00 (1.00-1.01) |
| bytes | valid | greedy | 0 | 0 | 20 | 1.00 (1.00-1.01) |
| bytes | valid | json_repair | 0 | 0 | 20 | 0.00 (0.00-0.00) |
| bytes | valid | schema_salvage | 0 | 0 | 20 | 0.00 (0.00-0.00) |
| bytes | valid | schema_standard | 0 | 0 | 20 | 0.00 (0.00-0.00) |
| bytes | valid | unchanged | 0 | 0 | 20 | 0.00 (0.00-0.00) |
| llada | closing | enumeration | 0 | 0 | 20 | 0.76 (0.37-1.09) |
| llada | closing | feasibility | 0 | 0 | 20 | 0.99 (0.99-1.00) |
| llada | closing | greedy | 0 | 0 | 20 | 1.42 (1.40-1.44) |
| llada | closing | json_repair | 20 | 0 | 0 | - |
| llada | closing | schema_salvage | 20 | 0 | 0 | - |
| llada | closing | schema_standard | 20 | 0 | 0 | - |
| llada | closing | unchanged | 20 | 0 | 0 | - |
| llada | missing_suffix | enumeration | 0 | 0 | 0 | - |
| llada | missing_suffix | feasibility | 0 | 0 | 0 | - |
| llada | missing_suffix | greedy | 0 | 0 | 0 | - |
| llada | missing_suffix | json_repair | 0 | 20 | 0 | - |
| llada | missing_suffix | schema_salvage | 0 | 20 | 0 | - |
| llada | missing_suffix | schema_standard | 0 | 20 | 0 | - |
| llada | missing_suffix | unchanged | 0 | 0 | 0 | - |
| llada | opening | enumeration | 0 | 0 | 20 | 0.58 (0.35-0.76) |
| llada | opening | feasibility | 0 | 0 | 20 | 0.99 (0.99-1.00) |
| llada | opening | greedy | 0 | 0 | 20 | 1.42 (1.41-1.44) |
| llada | opening | json_repair | 20 | 0 | 0 | - |
| llada | opening | schema_salvage | 20 | 0 | 0 | - |
| llada | opening | schema_standard | 20 | 0 | 0 | - |
| llada | opening | unchanged | 20 | 0 | 0 | - |
| llada | semantic | enumeration | 0 | 0 | 0 | - |
| llada | semantic | feasibility | 0 | 0 | 0 | - |
| llada | semantic | greedy | 0 | 0 | 0 | - |
| llada | semantic | json_repair | 0 | 0 | 0 | - |
| llada | semantic | schema_salvage | 0 | 0 | 0 | - |
| llada | semantic | schema_standard | 0 | 0 | 0 | - |
| llada | semantic | unchanged | 0 | 0 | 0 | - |
| llada | separator | enumeration | 10 | 0 | 10 | 5.21 (5.01-5.53) |
| llada | separator | feasibility | 0 | 0 | 20 | 0.99 (0.99-1.00) |
| llada | separator | greedy | 0 | 0 | 20 | 1.76 (1.73-1.78) |
| llada | separator | json_repair | 0 | 0 | 20 | 0.00 (0.00-0.00) |
| llada | separator | schema_salvage | 0 | 0 | 20 | 0.00 (0.00-0.00) |
| llada | separator | schema_standard | 0 | 0 | 20 | 0.00 (0.00-0.00) |
| llada | separator | unchanged | 20 | 0 | 0 | - |
| llada | valid | enumeration | 0 | 0 | 20 | 0.26 (0.23-0.28) |
| llada | valid | feasibility | 0 | 0 | 20 | 1.00 (0.99-1.00) |
| llada | valid | greedy | 0 | 0 | 20 | 1.07 (1.06-1.08) |
| llada | valid | json_repair | 0 | 0 | 20 | 0.00 (0.00-0.00) |
| llada | valid | schema_salvage | 0 | 0 | 20 | 0.00 (0.00-0.00) |
| llada | valid | schema_standard | 0 | 0 | 20 | 0.00 (0.00-0.00) |
| llada | valid | unchanged | 0 | 0 | 20 | 0.00 (0.00-0.00) |

Contagens completas de status:

```json
[
  {
    "profile": "bytes",
    "family": "closing",
    "method": "enumeration",
    "statuses": {
      "optimal": 40
    }
  },
  {
    "profile": "bytes",
    "family": "closing",
    "method": "exact",
    "statuses": {
      "optimal": 40
    }
  },
  {
    "profile": "bytes",
    "family": "closing",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 40
    }
  },
  {
    "profile": "bytes",
    "family": "closing",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 40
    }
  },
  {
    "profile": "bytes",
    "family": "closing",
    "method": "json_repair",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "bytes",
    "family": "closing",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "bytes",
    "family": "closing",
    "method": "schema_standard",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "bytes",
    "family": "closing",
    "method": "unchanged",
    "statuses": {
      "unchanged": 40
    }
  },
  {
    "profile": "bytes",
    "family": "missing_suffix",
    "method": "enumeration",
    "statuses": {
      "timeout": 40
    }
  },
  {
    "profile": "bytes",
    "family": "missing_suffix",
    "method": "exact",
    "statuses": {
      "infeasible_on_support": 40
    }
  },
  {
    "profile": "bytes",
    "family": "missing_suffix",
    "method": "feasibility",
    "statuses": {
      "infeasible_on_support": 40
    }
  },
  {
    "profile": "bytes",
    "family": "missing_suffix",
    "method": "greedy",
    "statuses": {
      "infeasible_on_support": 40
    }
  },
  {
    "profile": "bytes",
    "family": "missing_suffix",
    "method": "json_repair",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "bytes",
    "family": "missing_suffix",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "bytes",
    "family": "missing_suffix",
    "method": "schema_standard",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "bytes",
    "family": "missing_suffix",
    "method": "unchanged",
    "statuses": {
      "unchanged": 40
    }
  },
  {
    "profile": "bytes",
    "family": "opening",
    "method": "enumeration",
    "statuses": {
      "optimal": 40
    }
  },
  {
    "profile": "bytes",
    "family": "opening",
    "method": "exact",
    "statuses": {
      "optimal": 40
    }
  },
  {
    "profile": "bytes",
    "family": "opening",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 40
    }
  },
  {
    "profile": "bytes",
    "family": "opening",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 40
    }
  },
  {
    "profile": "bytes",
    "family": "opening",
    "method": "json_repair",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "bytes",
    "family": "opening",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "bytes",
    "family": "opening",
    "method": "schema_standard",
    "statuses": {
      "error": 40
    }
  },
  {
    "profile": "bytes",
    "family": "opening",
    "method": "unchanged",
    "statuses": {
      "unchanged": 40
    }
  },
  {
    "profile": "bytes",
    "family": "semantic",
    "method": "enumeration",
    "statuses": {
      "optimal": 40
    }
  },
  {
    "profile": "bytes",
    "family": "semantic",
    "method": "exact",
    "statuses": {
      "optimal": 40
    }
  },
  {
    "profile": "bytes",
    "family": "semantic",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 40
    }
  },
  {
    "profile": "bytes",
    "family": "semantic",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 40
    }
  },
  {
    "profile": "bytes",
    "family": "semantic",
    "method": "json_repair",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "bytes",
    "family": "semantic",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "bytes",
    "family": "semantic",
    "method": "schema_standard",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "bytes",
    "family": "semantic",
    "method": "unchanged",
    "statuses": {
      "unchanged": 40
    }
  },
  {
    "profile": "bytes",
    "family": "separator",
    "method": "enumeration",
    "statuses": {
      "timeout": 40
    }
  },
  {
    "profile": "bytes",
    "family": "separator",
    "method": "exact",
    "statuses": {
      "optimal": 40
    }
  },
  {
    "profile": "bytes",
    "family": "separator",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 40
    }
  },
  {
    "profile": "bytes",
    "family": "separator",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 40
    }
  },
  {
    "profile": "bytes",
    "family": "separator",
    "method": "json_repair",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "bytes",
    "family": "separator",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "bytes",
    "family": "separator",
    "method": "schema_standard",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "bytes",
    "family": "separator",
    "method": "unchanged",
    "statuses": {
      "unchanged": 40
    }
  },
  {
    "profile": "bytes",
    "family": "valid",
    "method": "enumeration",
    "statuses": {
      "optimal": 40
    }
  },
  {
    "profile": "bytes",
    "family": "valid",
    "method": "exact",
    "statuses": {
      "optimal": 40
    }
  },
  {
    "profile": "bytes",
    "family": "valid",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 40
    }
  },
  {
    "profile": "bytes",
    "family": "valid",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 40
    }
  },
  {
    "profile": "bytes",
    "family": "valid",
    "method": "json_repair",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "bytes",
    "family": "valid",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "bytes",
    "family": "valid",
    "method": "schema_standard",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "bytes",
    "family": "valid",
    "method": "unchanged",
    "statuses": {
      "unchanged": 40
    }
  },
  {
    "profile": "llada",
    "family": "closing",
    "method": "enumeration",
    "statuses": {
      "optimal": 40
    }
  },
  {
    "profile": "llada",
    "family": "closing",
    "method": "exact",
    "statuses": {
      "optimal": 40
    }
  },
  {
    "profile": "llada",
    "family": "closing",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 40
    }
  },
  {
    "profile": "llada",
    "family": "closing",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 40
    }
  },
  {
    "profile": "llada",
    "family": "closing",
    "method": "json_repair",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "llada",
    "family": "closing",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "llada",
    "family": "closing",
    "method": "schema_standard",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "llada",
    "family": "closing",
    "method": "unchanged",
    "statuses": {
      "unchanged": 40
    }
  },
  {
    "profile": "llada",
    "family": "missing_suffix",
    "method": "enumeration",
    "statuses": {
      "timeout": 40
    }
  },
  {
    "profile": "llada",
    "family": "missing_suffix",
    "method": "exact",
    "statuses": {
      "infeasible_on_support": 40
    }
  },
  {
    "profile": "llada",
    "family": "missing_suffix",
    "method": "feasibility",
    "statuses": {
      "infeasible_on_support": 40
    }
  },
  {
    "profile": "llada",
    "family": "missing_suffix",
    "method": "greedy",
    "statuses": {
      "infeasible_on_support": 40
    }
  },
  {
    "profile": "llada",
    "family": "missing_suffix",
    "method": "json_repair",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "llada",
    "family": "missing_suffix",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "llada",
    "family": "missing_suffix",
    "method": "schema_standard",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "llada",
    "family": "missing_suffix",
    "method": "unchanged",
    "statuses": {
      "unchanged": 40
    }
  },
  {
    "profile": "llada",
    "family": "opening",
    "method": "enumeration",
    "statuses": {
      "optimal": 40
    }
  },
  {
    "profile": "llada",
    "family": "opening",
    "method": "exact",
    "statuses": {
      "optimal": 40
    }
  },
  {
    "profile": "llada",
    "family": "opening",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 40
    }
  },
  {
    "profile": "llada",
    "family": "opening",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 40
    }
  },
  {
    "profile": "llada",
    "family": "opening",
    "method": "json_repair",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "llada",
    "family": "opening",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "llada",
    "family": "opening",
    "method": "schema_standard",
    "statuses": {
      "error": 40
    }
  },
  {
    "profile": "llada",
    "family": "opening",
    "method": "unchanged",
    "statuses": {
      "unchanged": 40
    }
  },
  {
    "profile": "llada",
    "family": "semantic",
    "method": "enumeration",
    "statuses": {
      "optimal": 40
    }
  },
  {
    "profile": "llada",
    "family": "semantic",
    "method": "exact",
    "statuses": {
      "optimal": 40
    }
  },
  {
    "profile": "llada",
    "family": "semantic",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 40
    }
  },
  {
    "profile": "llada",
    "family": "semantic",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 40
    }
  },
  {
    "profile": "llada",
    "family": "semantic",
    "method": "json_repair",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "llada",
    "family": "semantic",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "llada",
    "family": "semantic",
    "method": "schema_standard",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "llada",
    "family": "semantic",
    "method": "unchanged",
    "statuses": {
      "unchanged": 40
    }
  },
  {
    "profile": "llada",
    "family": "separator",
    "method": "enumeration",
    "statuses": {
      "optimal": 20,
      "timeout": 20
    }
  },
  {
    "profile": "llada",
    "family": "separator",
    "method": "exact",
    "statuses": {
      "optimal": 40
    }
  },
  {
    "profile": "llada",
    "family": "separator",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 40
    }
  },
  {
    "profile": "llada",
    "family": "separator",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 40
    }
  },
  {
    "profile": "llada",
    "family": "separator",
    "method": "json_repair",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "llada",
    "family": "separator",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "llada",
    "family": "separator",
    "method": "schema_standard",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "llada",
    "family": "separator",
    "method": "unchanged",
    "statuses": {
      "unchanged": 40
    }
  },
  {
    "profile": "llada",
    "family": "valid",
    "method": "enumeration",
    "statuses": {
      "optimal": 40
    }
  },
  {
    "profile": "llada",
    "family": "valid",
    "method": "exact",
    "statuses": {
      "optimal": 40
    }
  },
  {
    "profile": "llada",
    "family": "valid",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 40
    }
  },
  {
    "profile": "llada",
    "family": "valid",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 40
    }
  },
  {
    "profile": "llada",
    "family": "valid",
    "method": "json_repair",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "llada",
    "family": "valid",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "llada",
    "family": "valid",
    "method": "schema_standard",
    "statuses": {
      "repaired": 40
    }
  },
  {
    "profile": "llada",
    "family": "valid",
    "method": "unchanged",
    "statuses": {
      "unchanged": 40
    }
  }
]
```

## mechanism

Commit de medição: `47b93c475ca961b97063d409f9b8c4c29ba580c8`. Configuração: `m21_repair_mechanism_v1`. Chamadas: 768.

| Perfil | Classe | Método | Documentos corretos | Mediana total (ms) |
|---|---|---|---:|---:|
| bytes | valid | Unchanged | 8/8 | 0.01 |
| bytes | valid | JSON repair | 8/8 | 0.10 |
| bytes | valid | Schema standard | 8/8 | 0.52 |
| bytes | valid | Schema salvage | 8/8 | 0.53 |
| bytes | valid | Enumeration | 8/8 | 2.98 |
| bytes | valid | Unweighted CFG | 0/8 | 231.32 |
| bytes | valid | Greedy CFG | 8/8 | 606.12 |
| bytes | valid | Exact MWPC | 8/8 | 231.36 |
| bytes | opening | Unchanged | 0/8 | 0.01 |
| bytes | opening | JSON repair | 0/8 | 0.39 |
| bytes | opening | Schema standard | 0/8 | 0.49 |
| bytes | opening | Schema salvage | 0/8 | 0.91 |
| bytes | opening | Enumeration | 8/8 | 3.82 |
| bytes | opening | Unweighted CFG | 0/8 | 222.41 |
| bytes | opening | Greedy CFG | 0/8 | 239.41 |
| bytes | opening | Exact MWPC | 8/8 | 225.88 |
| bytes | closing | Unchanged | 0/8 | 0.01 |
| bytes | closing | JSON repair | 4/8 | 0.39 |
| bytes | closing | Schema standard | 4/8 | 0.96 |
| bytes | closing | Schema salvage | 4/8 | 0.94 |
| bytes | closing | Enumeration | 8/8 | 4.46 |
| bytes | closing | Unweighted CFG | 0/8 | 223.99 |
| bytes | closing | Greedy CFG | 8/8 | 603.28 |
| bytes | closing | Exact MWPC | 8/8 | 226.69 |
| bytes | separator | Unchanged | 0/8 | 0.01 |
| bytes | separator | JSON repair | 8/8 | 0.46 |
| bytes | separator | Schema standard | 8/8 | 1.02 |
| bytes | separator | Schema salvage | 8/8 | 1.09 |
| bytes | separator | Enumeration | 8/8 | 28.81 |
| bytes | separator | Unweighted CFG | 0/8 | 224.75 |
| bytes | separator | Greedy CFG | 8/8 | 606.15 |
| bytes | separator | Exact MWPC | 0/8 | 234.40 |
| bytes | missing_suffix | Unchanged | 0/8 | 0.01 |
| bytes | missing_suffix | JSON repair | 8/8 | 0.39 |
| bytes | missing_suffix | Schema standard | 8/8 | 0.96 |
| bytes | missing_suffix | Schema salvage | 8/8 | 1.00 |
| bytes | missing_suffix | Enumeration | 0/8 | 959.30 |
| bytes | missing_suffix | Unweighted CFG | 0/8 | 10.07 |
| bytes | missing_suffix | Greedy CFG | 0/8 | 11.15 |
| bytes | missing_suffix | Exact MWPC | 0/8 | 12.39 |
| bytes | semantic | Unchanged | 0/8 | 0.01 |
| bytes | semantic | JSON repair | 0/8 | 0.11 |
| bytes | semantic | Schema standard | 0/8 | 0.54 |
| bytes | semantic | Schema salvage | 0/8 | 0.55 |
| bytes | semantic | Enumeration | 0/8 | 3.64 |
| bytes | semantic | Unweighted CFG | 0/8 | 226.56 |
| bytes | semantic | Greedy CFG | 0/8 | 604.41 |
| bytes | semantic | Exact MWPC | 0/8 | 227.97 |
| llada | valid | Unchanged | 8/8 | 0.01 |
| llada | valid | JSON repair | 8/8 | 0.10 |
| llada | valid | Schema standard | 8/8 | 0.57 |
| llada | valid | Schema salvage | 8/8 | 0.54 |
| llada | valid | Enumeration | 8/8 | 63.90 |
| llada | valid | Unweighted CFG | 0/8 | 330.15 |
| llada | valid | Greedy CFG | 8/8 | 786.30 |
| llada | valid | Exact MWPC | 8/8 | 330.66 |
| llada | opening | Unchanged | 0/8 | 0.01 |
| llada | opening | JSON repair | 0/8 | 0.41 |
| llada | opening | Schema standard | 0/8 | 0.47 |
| llada | opening | Schema salvage | 0/8 | 0.92 |
| llada | opening | Enumeration | 8/8 | 63.41 |
| llada | opening | Unweighted CFG | 0/8 | 330.63 |
| llada | opening | Greedy CFG | 0/8 | 521.29 |
| llada | opening | Exact MWPC | 8/8 | 330.08 |
| llada | closing | Unchanged | 0/8 | 0.01 |
| llada | closing | JSON repair | 4/8 | 0.40 |
| llada | closing | Schema standard | 4/8 | 1.01 |
| llada | closing | Schema salvage | 4/8 | 0.95 |
| llada | closing | Enumeration | 8/8 | 76.47 |
| llada | closing | Unweighted CFG | 0/8 | 326.97 |
| llada | closing | Greedy CFG | 8/8 | 837.79 |
| llada | closing | Exact MWPC | 8/8 | 331.62 |
| llada | separator | Unchanged | 0/8 | 0.01 |
| llada | separator | JSON repair | 8/8 | 0.47 |
| llada | separator | Schema standard | 8/8 | 1.00 |
| llada | separator | Schema salvage | 8/8 | 1.04 |
| llada | separator | Enumeration | 8/8 | 78.22 |
| llada | separator | Unweighted CFG | 0/8 | 321.69 |
| llada | separator | Greedy CFG | 8/8 | 885.88 |
| llada | separator | Exact MWPC | 0/8 | 322.40 |
| llada | missing_suffix | Unchanged | 0/8 | 0.01 |
| llada | missing_suffix | JSON repair | 8/8 | 0.39 |
| llada | missing_suffix | Schema standard | 8/8 | 0.93 |
| llada | missing_suffix | Schema salvage | 8/8 | 1.01 |
| llada | missing_suffix | Enumeration | 0/8 | 231.50 |
| llada | missing_suffix | Unweighted CFG | 0/8 | 113.31 |
| llada | missing_suffix | Greedy CFG | 0/8 | 140.24 |
| llada | missing_suffix | Exact MWPC | 0/8 | 115.40 |
| llada | semantic | Unchanged | 0/8 | 0.01 |
| llada | semantic | JSON repair | 0/8 | 0.11 |
| llada | semantic | Schema standard | 0/8 | 0.53 |
| llada | semantic | Schema salvage | 0/8 | 0.52 |
| llada | semantic | Enumeration | 0/8 | 64.04 |
| llada | semantic | Unweighted CFG | 0/8 | 326.51 |
| llada | semantic | Greedy CFG | 0/8 | 777.41 |
| llada | semantic | Exact MWPC | 0/8 | 330.06 |

Comparações pareadas e intervalos descritivos por documento:

| Perfil | Classe | Comparador | Só exato vence | Só comparador vence | Ambos vencem | Velocidade comparador/exato (IC 95%) |
|---|---|---|---:|---:|---:|---|
| bytes | closing | enumeration | 0 | 0 | 8 | 0.02 (0.02-0.02) |
| bytes | closing | feasibility | 8 | 0 | 0 | - |
| bytes | closing | greedy | 0 | 0 | 8 | 2.38 (1.95-2.96) |
| bytes | closing | json_repair | 4 | 0 | 4 | 0.00 (0.00-0.00) |
| bytes | closing | schema_salvage | 4 | 0 | 4 | 0.01 (0.01-0.01) |
| bytes | closing | schema_standard | 4 | 0 | 4 | 0.01 (0.01-0.01) |
| bytes | closing | unchanged | 8 | 0 | 0 | - |
| bytes | missing_suffix | enumeration | 0 | 0 | 0 | - |
| bytes | missing_suffix | feasibility | 0 | 0 | 0 | - |
| bytes | missing_suffix | greedy | 0 | 0 | 0 | - |
| bytes | missing_suffix | json_repair | 0 | 8 | 0 | - |
| bytes | missing_suffix | schema_salvage | 0 | 8 | 0 | - |
| bytes | missing_suffix | schema_standard | 0 | 8 | 0 | - |
| bytes | missing_suffix | unchanged | 0 | 0 | 0 | - |
| bytes | opening | enumeration | 0 | 0 | 8 | 0.02 (0.01-0.02) |
| bytes | opening | feasibility | 8 | 0 | 0 | - |
| bytes | opening | greedy | 8 | 0 | 0 | - |
| bytes | opening | json_repair | 8 | 0 | 0 | - |
| bytes | opening | schema_salvage | 8 | 0 | 0 | - |
| bytes | opening | schema_standard | 8 | 0 | 0 | - |
| bytes | opening | unchanged | 8 | 0 | 0 | - |
| bytes | semantic | enumeration | 0 | 0 | 0 | - |
| bytes | semantic | feasibility | 0 | 0 | 0 | - |
| bytes | semantic | greedy | 0 | 0 | 0 | - |
| bytes | semantic | json_repair | 0 | 0 | 0 | - |
| bytes | semantic | schema_salvage | 0 | 0 | 0 | - |
| bytes | semantic | schema_standard | 0 | 0 | 0 | - |
| bytes | semantic | unchanged | 0 | 0 | 0 | - |
| bytes | separator | enumeration | 0 | 8 | 0 | - |
| bytes | separator | feasibility | 0 | 0 | 0 | - |
| bytes | separator | greedy | 0 | 8 | 0 | - |
| bytes | separator | json_repair | 0 | 8 | 0 | - |
| bytes | separator | schema_salvage | 0 | 8 | 0 | - |
| bytes | separator | schema_standard | 0 | 8 | 0 | - |
| bytes | separator | unchanged | 0 | 0 | 0 | - |
| bytes | valid | enumeration | 0 | 0 | 8 | 0.01 (0.01-0.02) |
| bytes | valid | feasibility | 8 | 0 | 0 | - |
| bytes | valid | greedy | 0 | 0 | 8 | 2.46 (1.87-2.96) |
| bytes | valid | json_repair | 0 | 0 | 8 | 0.00 (0.00-0.00) |
| bytes | valid | schema_salvage | 0 | 0 | 8 | 0.00 (0.00-0.00) |
| bytes | valid | schema_standard | 0 | 0 | 8 | 0.00 (0.00-0.00) |
| bytes | valid | unchanged | 0 | 0 | 8 | 0.00 (0.00-0.00) |
| llada | closing | enumeration | 0 | 0 | 8 | 0.24 (0.17-0.33) |
| llada | closing | feasibility | 8 | 0 | 0 | - |
| llada | closing | greedy | 0 | 0 | 8 | 2.35 (1.90-2.88) |
| llada | closing | json_repair | 4 | 0 | 4 | 0.00 (0.00-0.00) |
| llada | closing | schema_salvage | 4 | 0 | 4 | 0.01 (0.00-0.01) |
| llada | closing | schema_standard | 4 | 0 | 4 | 0.01 (0.00-0.01) |
| llada | closing | unchanged | 8 | 0 | 0 | - |
| llada | missing_suffix | enumeration | 0 | 0 | 0 | - |
| llada | missing_suffix | feasibility | 0 | 0 | 0 | - |
| llada | missing_suffix | greedy | 0 | 0 | 0 | - |
| llada | missing_suffix | json_repair | 0 | 8 | 0 | - |
| llada | missing_suffix | schema_salvage | 0 | 8 | 0 | - |
| llada | missing_suffix | schema_standard | 0 | 8 | 0 | - |
| llada | missing_suffix | unchanged | 0 | 0 | 0 | - |
| llada | opening | enumeration | 0 | 0 | 8 | 0.21 (0.15-0.31) |
| llada | opening | feasibility | 8 | 0 | 0 | - |
| llada | opening | greedy | 8 | 0 | 0 | - |
| llada | opening | json_repair | 8 | 0 | 0 | - |
| llada | opening | schema_salvage | 8 | 0 | 0 | - |
| llada | opening | schema_standard | 8 | 0 | 0 | - |
| llada | opening | unchanged | 8 | 0 | 0 | - |
| llada | semantic | enumeration | 0 | 0 | 0 | - |
| llada | semantic | feasibility | 0 | 0 | 0 | - |
| llada | semantic | greedy | 0 | 0 | 0 | - |
| llada | semantic | json_repair | 0 | 0 | 0 | - |
| llada | semantic | schema_salvage | 0 | 0 | 0 | - |
| llada | semantic | schema_standard | 0 | 0 | 0 | - |
| llada | semantic | unchanged | 0 | 0 | 0 | - |
| llada | separator | enumeration | 0 | 8 | 0 | - |
| llada | separator | feasibility | 0 | 0 | 0 | - |
| llada | separator | greedy | 0 | 8 | 0 | - |
| llada | separator | json_repair | 0 | 8 | 0 | - |
| llada | separator | schema_salvage | 0 | 8 | 0 | - |
| llada | separator | schema_standard | 0 | 8 | 0 | - |
| llada | separator | unchanged | 0 | 0 | 0 | - |
| llada | valid | enumeration | 0 | 0 | 8 | 0.22 (0.14-0.31) |
| llada | valid | feasibility | 8 | 0 | 0 | - |
| llada | valid | greedy | 0 | 0 | 8 | 2.23 (1.75-2.70) |
| llada | valid | json_repair | 0 | 0 | 8 | 0.00 (0.00-0.00) |
| llada | valid | schema_salvage | 0 | 0 | 8 | 0.00 (0.00-0.00) |
| llada | valid | schema_standard | 0 | 0 | 8 | 0.00 (0.00-0.00) |
| llada | valid | unchanged | 0 | 0 | 8 | 0.00 (0.00-0.00) |

Contagens completas de status:

```json
[
  {
    "profile": "bytes",
    "family": "closing",
    "method": "enumeration",
    "statuses": {
      "optimal": 8
    }
  },
  {
    "profile": "bytes",
    "family": "closing",
    "method": "exact",
    "statuses": {
      "optimal": 8
    }
  },
  {
    "profile": "bytes",
    "family": "closing",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 8
    }
  },
  {
    "profile": "bytes",
    "family": "closing",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 8
    }
  },
  {
    "profile": "bytes",
    "family": "closing",
    "method": "json_repair",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "bytes",
    "family": "closing",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "bytes",
    "family": "closing",
    "method": "schema_standard",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "bytes",
    "family": "closing",
    "method": "unchanged",
    "statuses": {
      "unchanged": 8
    }
  },
  {
    "profile": "bytes",
    "family": "missing_suffix",
    "method": "enumeration",
    "statuses": {
      "infeasible_on_support": 8
    }
  },
  {
    "profile": "bytes",
    "family": "missing_suffix",
    "method": "exact",
    "statuses": {
      "infeasible_on_support": 8
    }
  },
  {
    "profile": "bytes",
    "family": "missing_suffix",
    "method": "feasibility",
    "statuses": {
      "infeasible_on_support": 8
    }
  },
  {
    "profile": "bytes",
    "family": "missing_suffix",
    "method": "greedy",
    "statuses": {
      "infeasible_on_support": 8
    }
  },
  {
    "profile": "bytes",
    "family": "missing_suffix",
    "method": "json_repair",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "bytes",
    "family": "missing_suffix",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "bytes",
    "family": "missing_suffix",
    "method": "schema_standard",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "bytes",
    "family": "missing_suffix",
    "method": "unchanged",
    "statuses": {
      "unchanged": 8
    }
  },
  {
    "profile": "bytes",
    "family": "opening",
    "method": "enumeration",
    "statuses": {
      "optimal": 8
    }
  },
  {
    "profile": "bytes",
    "family": "opening",
    "method": "exact",
    "statuses": {
      "optimal": 8
    }
  },
  {
    "profile": "bytes",
    "family": "opening",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 8
    }
  },
  {
    "profile": "bytes",
    "family": "opening",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 8
    }
  },
  {
    "profile": "bytes",
    "family": "opening",
    "method": "json_repair",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "bytes",
    "family": "opening",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "bytes",
    "family": "opening",
    "method": "schema_standard",
    "statuses": {
      "error": 8
    }
  },
  {
    "profile": "bytes",
    "family": "opening",
    "method": "unchanged",
    "statuses": {
      "unchanged": 8
    }
  },
  {
    "profile": "bytes",
    "family": "semantic",
    "method": "enumeration",
    "statuses": {
      "optimal": 8
    }
  },
  {
    "profile": "bytes",
    "family": "semantic",
    "method": "exact",
    "statuses": {
      "optimal": 8
    }
  },
  {
    "profile": "bytes",
    "family": "semantic",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 8
    }
  },
  {
    "profile": "bytes",
    "family": "semantic",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 8
    }
  },
  {
    "profile": "bytes",
    "family": "semantic",
    "method": "json_repair",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "bytes",
    "family": "semantic",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "bytes",
    "family": "semantic",
    "method": "schema_standard",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "bytes",
    "family": "semantic",
    "method": "unchanged",
    "statuses": {
      "unchanged": 8
    }
  },
  {
    "profile": "bytes",
    "family": "separator",
    "method": "enumeration",
    "statuses": {
      "optimal": 8
    }
  },
  {
    "profile": "bytes",
    "family": "separator",
    "method": "exact",
    "statuses": {
      "optimal": 8
    }
  },
  {
    "profile": "bytes",
    "family": "separator",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 8
    }
  },
  {
    "profile": "bytes",
    "family": "separator",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 8
    }
  },
  {
    "profile": "bytes",
    "family": "separator",
    "method": "json_repair",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "bytes",
    "family": "separator",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "bytes",
    "family": "separator",
    "method": "schema_standard",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "bytes",
    "family": "separator",
    "method": "unchanged",
    "statuses": {
      "unchanged": 8
    }
  },
  {
    "profile": "bytes",
    "family": "valid",
    "method": "enumeration",
    "statuses": {
      "optimal": 8
    }
  },
  {
    "profile": "bytes",
    "family": "valid",
    "method": "exact",
    "statuses": {
      "optimal": 8
    }
  },
  {
    "profile": "bytes",
    "family": "valid",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 8
    }
  },
  {
    "profile": "bytes",
    "family": "valid",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 8
    }
  },
  {
    "profile": "bytes",
    "family": "valid",
    "method": "json_repair",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "bytes",
    "family": "valid",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "bytes",
    "family": "valid",
    "method": "schema_standard",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "bytes",
    "family": "valid",
    "method": "unchanged",
    "statuses": {
      "unchanged": 8
    }
  },
  {
    "profile": "llada",
    "family": "closing",
    "method": "enumeration",
    "statuses": {
      "optimal": 8
    }
  },
  {
    "profile": "llada",
    "family": "closing",
    "method": "exact",
    "statuses": {
      "optimal": 8
    }
  },
  {
    "profile": "llada",
    "family": "closing",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 8
    }
  },
  {
    "profile": "llada",
    "family": "closing",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 8
    }
  },
  {
    "profile": "llada",
    "family": "closing",
    "method": "json_repair",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "llada",
    "family": "closing",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "llada",
    "family": "closing",
    "method": "schema_standard",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "llada",
    "family": "closing",
    "method": "unchanged",
    "statuses": {
      "unchanged": 8
    }
  },
  {
    "profile": "llada",
    "family": "missing_suffix",
    "method": "enumeration",
    "statuses": {
      "infeasible_on_support": 8
    }
  },
  {
    "profile": "llada",
    "family": "missing_suffix",
    "method": "exact",
    "statuses": {
      "infeasible_on_support": 8
    }
  },
  {
    "profile": "llada",
    "family": "missing_suffix",
    "method": "feasibility",
    "statuses": {
      "infeasible_on_support": 8
    }
  },
  {
    "profile": "llada",
    "family": "missing_suffix",
    "method": "greedy",
    "statuses": {
      "infeasible_on_support": 8
    }
  },
  {
    "profile": "llada",
    "family": "missing_suffix",
    "method": "json_repair",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "llada",
    "family": "missing_suffix",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "llada",
    "family": "missing_suffix",
    "method": "schema_standard",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "llada",
    "family": "missing_suffix",
    "method": "unchanged",
    "statuses": {
      "unchanged": 8
    }
  },
  {
    "profile": "llada",
    "family": "opening",
    "method": "enumeration",
    "statuses": {
      "optimal": 8
    }
  },
  {
    "profile": "llada",
    "family": "opening",
    "method": "exact",
    "statuses": {
      "optimal": 8
    }
  },
  {
    "profile": "llada",
    "family": "opening",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 8
    }
  },
  {
    "profile": "llada",
    "family": "opening",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 8
    }
  },
  {
    "profile": "llada",
    "family": "opening",
    "method": "json_repair",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "llada",
    "family": "opening",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "llada",
    "family": "opening",
    "method": "schema_standard",
    "statuses": {
      "error": 8
    }
  },
  {
    "profile": "llada",
    "family": "opening",
    "method": "unchanged",
    "statuses": {
      "unchanged": 8
    }
  },
  {
    "profile": "llada",
    "family": "semantic",
    "method": "enumeration",
    "statuses": {
      "optimal": 8
    }
  },
  {
    "profile": "llada",
    "family": "semantic",
    "method": "exact",
    "statuses": {
      "optimal": 8
    }
  },
  {
    "profile": "llada",
    "family": "semantic",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 8
    }
  },
  {
    "profile": "llada",
    "family": "semantic",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 8
    }
  },
  {
    "profile": "llada",
    "family": "semantic",
    "method": "json_repair",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "llada",
    "family": "semantic",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "llada",
    "family": "semantic",
    "method": "schema_standard",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "llada",
    "family": "semantic",
    "method": "unchanged",
    "statuses": {
      "unchanged": 8
    }
  },
  {
    "profile": "llada",
    "family": "separator",
    "method": "enumeration",
    "statuses": {
      "optimal": 8
    }
  },
  {
    "profile": "llada",
    "family": "separator",
    "method": "exact",
    "statuses": {
      "optimal": 8
    }
  },
  {
    "profile": "llada",
    "family": "separator",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 8
    }
  },
  {
    "profile": "llada",
    "family": "separator",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 8
    }
  },
  {
    "profile": "llada",
    "family": "separator",
    "method": "json_repair",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "llada",
    "family": "separator",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "llada",
    "family": "separator",
    "method": "schema_standard",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "llada",
    "family": "separator",
    "method": "unchanged",
    "statuses": {
      "unchanged": 8
    }
  },
  {
    "profile": "llada",
    "family": "valid",
    "method": "enumeration",
    "statuses": {
      "optimal": 8
    }
  },
  {
    "profile": "llada",
    "family": "valid",
    "method": "exact",
    "statuses": {
      "optimal": 8
    }
  },
  {
    "profile": "llada",
    "family": "valid",
    "method": "feasibility",
    "statuses": {
      "feasible_on_support": 8
    }
  },
  {
    "profile": "llada",
    "family": "valid",
    "method": "greedy",
    "statuses": {
      "feasible_on_support": 8
    }
  },
  {
    "profile": "llada",
    "family": "valid",
    "method": "json_repair",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "llada",
    "family": "valid",
    "method": "schema_salvage",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "llada",
    "family": "valid",
    "method": "schema_standard",
    "statuses": {
      "repaired": 8
    }
  },
  {
    "profile": "llada",
    "family": "valid",
    "method": "unchanged",
    "statuses": {
      "unchanged": 8
    }
  }
]
```

## Interpretação e limites

A comparação com CFG sem pesos separa recuperação por restrição de esquema de minimização de edições. Empates no esquema rígido não demonstram benefício dos pesos. O estudo de gramática ambígua testa esse mecanismo separadamente.

Os reparadores simples podem ser muito mais rápidos e lidar com inserções fora do suporte. O resultado deve ser interpretado por classe, junto dos custos e das falhas. Erros semânticos já sintaticamente válidos não são corrigidos apenas pela gramática. Nenhum resultado estabelece superioridade geral sobre reparadores ou melhor geração de dLLMs.
