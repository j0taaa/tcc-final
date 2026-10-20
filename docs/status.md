# Estado da pesquisa

A meta de uma contribuição própria, relevante e útil permanece **aberta**.
A biblioteca, o artigo histórico e as candidatas de pesquisa têm escopos distintos.

| Frente | Evidência e decisão |
| --- | --- |
| Biblioteca mantida | Inferência em suporte finito, posterior LL(1), certificados e referências Python/Rust; contratos em `architecture.md`. |
| A24 / artigo | O protocolo histórico confirmou ganho de consulta em 3/15 estados e 30/30 demonstrações iterativas válidas. O gate operacional posterior, com controles CPU/GPU mais fortes, falhou em 15/15 estados. Não há superioridade operacional atual estabelecida. |
| A49–A50 | As auditorias identificaram composições/especializações clássicas; a aplicação de precisão foi negativa e não há benefício neural integral confirmado. |
| A65, A68 e A70 | As aplicações delimitadas foram encerradas com gates negativos. Não repetir ou ampliar casos para resgatá-las. |
| A69 | Separações matemáticas construídas; prioridade específica e consumidor natural que necessite exatidão continuam pendentes. |
| A71 | Acoplar paradas de um lote finito preservando leis individuais e de pares. Provas escritas e oráculos finitos; novidade suficiente, implementação nativa e ganho completo ainda pendentes. |
| A72 | Auditoria escrita sustenta o limite original e acrescenta: capacidade sublinear implica TV tendendo a 1; corolário de separação robusta para PCs estruturados. Antecedentes exatos diretos e controles eficientes reconhecidos. Prioridade específica e suficiência científica abertas; não há vantagem de decoder estabelecida. |

## Onde conferir

- A24: [resultado operacional posterior](../attempts/24-certified-depth-approximation/work/evidence/consumer-v4-development-first-v1/report.md).
- A65: [decisão da aplicação](../attempts/65-terminal-forecast-readout/work/native-resource-result-v8.md).
- A68: [decisão de custo completo](../attempts/68-residual-bernstein-sampling/work/result-v7.md).
- A69: [auditoria de prioridade e uso](../attempts/69-adaptive-factory-separation/work/priority-and-use-audit-v4.md).
- A70: [última auditoria](../attempts/70-native-adam-erasure/work/result-v5-native.md).
- A71: [contrato e limites](../attempts/71-pairwise-stop-clocks/README.md),
  [resultado V1](../attempts/71-pairwise-stop-clocks/work/result-v1.md) e
  [protocolo local V2](../attempts/71-pairwise-stop-clocks/work/protocol-v2.md).
- A72: [operação, antecedentes e limites](../attempts/72-recursive-syntax-factor-width/README.md)
  e [prova escrita](../attempts/72-recursive-syntax-factor-width/proof.md).

Resultados locais ainda não versionados não são promovidos a evidência publicada
por esta página. O [índice](../attempts/README.md) dá acesso às demais frentes.
As [pendências atuais](../TASKS.md) substituem a antiga fila acumulada de marcos.
