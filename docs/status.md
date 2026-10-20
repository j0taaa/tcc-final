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
| A72 | Não selecionada como contribuição central após a V2. Provas escritas de obstrução robusta preservadas; hipótese adjacente por convoluções medida em 36 casos sintéticos e seis capturas reais LLaDA. Gate neural 0/6: quatro propostas corretas porém mais lentas e duas recusas. Não há vantagem de decoder. |
| A79 | Prova escrita para erro da lei média sob arredondamento estocástico interno. Aplicação offline completa: 2.160 consultas válidas; candidata mais lenta em 27/27 casos e zero famílias aprovadas no gate de tempo. Memória total e prioridade suficiente permanecem inconclusivas. Não selecionada como tema central; [resultado e dados](../attempts/79-stochastic-circuit-sampling/result.md). |
| A80 | Lema escrito de calibração por clipping, revisado sob hipóteses explícitas. Aplicação offline V1 completa: 144 execuções, 2.048 saídas válidas, 16 recusas previstas da enumeração. Gate de custo completo falhou nas duas famílias; razões medianas 1,128/1,213 frente ao melhor controle. Prova preservada, sem utilidade dLLM estabelecida; [resultado e dados](../attempts/80-private-clipping-calibration/result.md). |
| A81 | Prova escrita revisada por subagente para temperamento de dois pesos gramaticais com derivação comum: ordem raiz de beta de charts e rejeição com limite constante. Melhora a expansão por réplicas nesta representação; prioridade suficiente, consumidor com vantagem integral e viabilidade em 12 GB pendentes. Nenhuma campanha selecionada; [contrato e prova](../attempts/81-sparse-tempered-mixture/README.md). |
| A82 | Triagem de cinco operações distintas após a mudança de abordagem solicitada: antirrepetição, alternativas sem reposição, campos antecipados, coerência marginal e esclarecimento de entradas. Provas delimitadas e oráculos finitos; cinco threads de verificação, sem campanha neural ou prioridade suficiente estabelecida. [Propostas e fronteiras](../attempts/82-five-operator-screening/README.md). |

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
