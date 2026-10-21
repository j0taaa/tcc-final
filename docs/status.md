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
| A81 | Prova escrita revisada para temperamento de dois pesos gramaticais: ordem raiz de beta de charts e rejeição constante. Auditoria posterior encontrou envelope positivo por monômios em Erdős–Kővári e controles baratos para componentes separados/proporcionais; não estabeleceu subsunção completa nem consumidor dLLM difícil. Prioridade, benefício integral e viabilidade pendentes. Nenhuma campanha selecionada; [contrato](../attempts/81-sparse-tempered-mixture/README.md) e [auditoria posterior](../attempts/81-sparse-tempered-mixture/priority-use-audit-v2.md). |
| A82 | Triagem de cinco operações com provas delimitadas e oráculos finitos em cinco threads. A auditoria posterior de B1 provou utilidade com custo real de colisão e cobertura de duas alternativas sob marginais fixas; top-2/WOR e contraexemplos impedem promover isso a ganho geral. Prioridade inicial de campanha B1 suspensa, sem execução neural. [Triagem](../attempts/82-five-operator-screening/README.md) e [prova de utilidade](../attempts/82-five-operator-screening/b1-utility.md). |
| A83 | Diagnóstico do EPIC original em três casos JSON com LLaDA NF4 na 3080 Ti. Dezoito decodes e uma sonda neural; controle de trabalho vazio reduz NFEs de 8 para 4 em dois casos preservando IDs/estados. Após leitura de LAVE/Saber/DecoCal e avaliação independente, a rota de atualização durante rejeições não foi selecionada como tema central: falta contribuição distinta que justifique o requisito de impacto. Sem campanha adicional. [Protocolo, evidências e decisão](../attempts/83-epic-operational-diagnosis/README.md). |
| A84 | Certificado local usando a segunda alternativa, com prova escrita de sharpness e teto de um token adicional frente a Fréchet. Piloto prospectivo na 3080 Ti: 64 decodes, 16 perguntas únicas, economia de 8,72%/12,13%, mas perda de um acerto único em cada família. Gate negativo; aplicação encerrada, sem seleção central. [Resultado e dados](../attempts/84-full-marginal-certificate/result-v1.md). |
| A85 | Construção escrita de um checksum regular para capturas livres, com amostragem por rejeição exata e reinício por orçamento, revisada por subagentes. O condicionamento por string é um controle mais forte que pode eliminar o ganho; nenhum consumidor com vantagem integral foi justificado. Sem protótipo ou campanha, não selecionada. [Prova, antecedentes e objeção](../attempts/85-checksum-backreferences/README.md). |
| A86 | Contrato de consultas especulativas e otimização local por prefixos, com antecedentes clássicos explícitos. Perfil V1 e fidelidade finita V2 passaram. V3 prospectiva capturou 1.760 eventos reais e avaliou oito casos TEST por replay completo: custo previsto com preparo 18,18%/22,68% maior que o serial, zero famílias aprovadas. O envelope afim selecionou consultas sem economia por batch; todos os controles escolheram o serial. Aplicação V3 encerrada, sem decoder acelerado ou seleção central. [Resultado e dados](../attempts/86-prefix-closure-planning/result-v3.md). |
| A87 | Método candidato de testemunha aleatória: prova escrita de `OPT+1` perfeito / esperança `3OPT+1` arbitrário no subproblema residual; auditoria CPU de 61 instâncias/664 execuções passou. Qualificação nativa V1: 944 forwards válidos na 3080 Ti; condição necessária 2/8, mas só nas propostas erradas. Nas seis corretas, as duas consultas iniciais já certificam e a auditoria não entra. V1 não justifica implementar/ampliar o método; provas preservadas, prioridade específica ainda aberta, sem seleção central. [Provas](../attempts/87-conditional-choice-readout/online-probe-analysis.md) e [resultado nativo/dados](../attempts/87-conditional-choice-readout/native-result-v1.md). |

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
