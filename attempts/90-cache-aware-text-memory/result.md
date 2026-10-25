# A90 — Resultado do piloto e decisão

**Gate negativo. Não há vantagem específica da difusão, contribuição original
substancial estabelecida ou justificativa para pós-treino nesta implementação.**
A candidata local foi mais lenta e reteve menos informação que os controles.
A investigação foi executada, não ficou em plano. Nenhuma campanha anterior,
checkout raiz ou tentativa da outra thread foi alterada. Sem publicação ou PR.

## Contrato, execução e falha preservada

Protocolo e dados foram fixados antes do primeiro forward A90, conforme
`evidence/freeze-v1.json`. Quatro histórias sintéticas × três estados, com
contradições e atualizações dependentes; sete histórias completas LongMemEval
cleaned/oracle, selecionadas por hash de ID em seis categorias mais abstenção.
Sem perguntas futuras, respostas ou `has_answer` no compressor. Não se escolheu
subconjunto por comprimento, sucesso ou tipo favorável à candidata.

Foram produzidos 140 estados neurais (dois métodos AR e dois dLLM), 105 estados
de controles CPU e 245 interações do leitor. As sete variantes tiveram o mesmo
consumidor e prefix cache real, com teto de memória de 320 tokens incluindo
separadores (payload máximo 256); full-history foi a exceção explícita ao teto.
Mesmo seletor e formato de patch para AR-local e dLLM-local, sem regiões-oráculo.

A V1 NF4 falhou na auditoria de cache, antes de responder qualquer tarefa.
Erro máximo 0,875 > limite 0,25; diagnóstico BF16 posterior também falhou.
Falhas e fontes originais foram preservadas. A emenda **V1a**, anterior à primeira
resposta de avaliação, trocou somente o consumidor por Qwen2.5-1.5B-Instruct
**FP32**, sem offload, comum aos sete métodos. Os cinco casos passaram, saídas
gulosas iguais e erro máximo 0,000143. Não se aumentou tolerância.
Isso não valida retrospectivamente o consumidor NF4 nem identifica a causa da
falha. Ver `cache-audit.md` e `protocol-v1a-runtime-amendment.md`.

Editores congelados: LLaDA-8B-Instruct NF4/BF16, 16 passos; AR Qwen2.5-3B-Instruct
NF4/BF16. Consumidor final 1,5B FP32. Nenhum offload ou treinamento. Não são modelos
pareados por pré-treino/capacidade: esta comparação não isola arquitetura.

## Qualidade × custo integral residente

Tempos em segundos, soma de seleção + montagem + edição + respostas, medidos em
fases separadas e sincronizadas. **Não são latência intercalada observada** com
modelos simultaneamente residentes. Uma execução por célula, sem IC de latência.

| Método | Atualização | Leitor | Total | Sintético completo, lexical /12 | Externo completo /7 |
| --- | ---: | ---: | ---: | ---: | ---: |
| dLLM local | 254,35 | 7,69 | **262,03** | **0** | 1 |
| AR, mesma edição local | 155,00 | 9,22 | **164,23** | **5** | 1 |
| dLLM reescrita global | 260,42 | 6,62 | 267,04 | 0 | 1 |
| AR resumidor incremental global | 158,94 | 9,06 | 167,99 | 9 | 1 |
| Seleção extrativa | 0,78 | 9,98 | 10,76 | 8 | 2 |
| Cauda textual | 0,06 | 9,60 | 9,67 | 10 | 1 |
| Histórico completo + cache | <0,001 | 30,86 | **30,86** | **12** | **2** |

A candidata custa **1,596×** o AR com a mesma interface e **8,492×** full-history.
O leitor sozinho foi 75,1% mais rápido que full-history, mas economizou cerca de
23,17 s enquanto atualizar a memória custou 254,35 s. Produzir/ler menos texto não
pagou o compressor. Parte da redução veio acompanhada de perda de fatos.

O critério lexical exige as sete menções esperadas no estado. Auditoria semântica
posterior de **todas as 84 respostas sintéticas**, com nomes dos métodos ocultos,
aceitou duas respostas equivalentes com “dia anterior ao compromisso”. Os totais
semânticos ficaram: dLLM-local 0, AR-local 5, dLLM-global 0, AR-global 9,
extrativo 9, cauda 11, full-history 12, todos de 12 estados. O resultado lexical
original foi preservado; a auditoria não substitui o gate nem reabre a campanha.

Menções lexicais de fatos nas respostas: dLLM-local 25/84, AR-local 71/84,
AR-global 76/84 e full-history 84/84. Na memória, as menções explícitas necessárias
foram 38/84, 68/84, 72/84 e 72/84 respectivamente; são diagnóstico superficial,
**não** uma medida semântica perfeita de retenção (relações implícitas podem bastar).

Todos os sete sinalizadores de valores superados foram auditados: dLLM-local 3,
extrativo 3 e cauda 1. Em todos, a resposta afirma a cidade antiga como endereço
atual; nenhum era menção histórica/negada. Os outros métodos tiveram zero desses
sinalizadores. Exemplo: após Oslo → Bergen, dLLM-local respondeu cidade Oslo,
empregador Iris e código desconhecido. Dados completos em `superseded-audit.json`.

Externamente, as quatro variantes neurais acertaram **somente a abstenção**;
zero das seis perguntas respondíveis receberam resposta plenamente correta.
Full-history acertou abstenção + atualização de conhecimento e teve duas parciais.
Extrativo acertou abstenção + uma recuperação factual. Pontos de rubrica 0–2:
neurais/cauda 2/14, extrativo 4/14 e full-history 6/14. A revisão das 49 respostas
ocultou nomes de métodos; foi feita pelo mesmo agente, sem judge pago ou avaliador
humano independente. **Não é acurácia oficial LongMemEval.**

A baixa qualidade de full-history (2/7 completas) também mostra limitação do
leitor, não apenas do compressor. Não se atribuem todos os erros externos à
memória. Mesmo assim, não surgiu vantagem da candidata sobre os controles.

## Cache, trabalho e recursos

O cache retém somente o LCP de IDs do prompt/template reais, até o comprimento
realmente materializado no KV. Tudo após divergência é descartado. Não se
reutiliza KV de sufixo causalmente alterado nem se usa semelhança textual como
critério. A auditoria CPU `foo` → `foobar` confirma que prefixo de caracteres
pode mudar o token de fronteira. Os dois tokenizers produziram IDs de memória
iguais nos 245 estados; o template de leitura é o do consumidor efetivo.

| Método | Prefill executado no leitor | Tokens de prefixo reutilizados | Forwards editor | Forwards leitor |
| --- | ---: | ---: | ---: | ---: |
| dLLM local | 5.413 | 1.462 | 560 | 501 |
| AR local | 7.209 | 1.587 | 5.744 | 591 |
| dLLM global | 5.254 | 1.252 | 560 | 427 |
| AR global | 7.359 | 1.579 | 5.907 | 575 |
| Extrativo | 6.409 | 3.619 | 0 | 660 |
| Cauda | 8.328 | 1.776 | 0 | 605 |
| Full-history | 33.141 | **50.880** | 0 | 883 |

Prefill inclui tokens novos e sufixo refeito; não são apenas tokens antigos
reprocessados. A soma do KV descartado entre interações também está no JSON
(`discarded_cached_tokens`), distinguindo invalidação de trabalho efetivamente
executado. Full-history usou cache competente; não foi comparado sem cache.
Menos forwards dLLM não significou menor custo, pois o contexto/canvas é refeito.

AR-local fez 7 ações locais e 28 globais; dLLM-local, 11 locais e 24 globais.
Memórias divergentes explicam conjuntos distintos sob a **mesma regra**. No
externo foram só 1 e 3 ações locais, respectivamente. Esse fallback frequente
limita a conclusão sobre um localizador melhor. AR-local economizou apenas 2,2%
frente ao AR-global, perdendo qualidade (5 versus 9 estados). dLLM-local economizou
1,9% frente à global, sem recuperar fidelidade e introduzindo três usos superados.
Não se estabeleceu nem mesmo uma vantagem útil da organização local nesta V1a.

RTX 3080 Ti confirmada, 12.288 MiB. Toda carga, warmup, forward e limpeza ocorreu
sob `/tmp/tcc-final-gpu-pilot.lock`, com verificação de PIDs compute antes da carga.
Nenhum trabalho alheio foi morto/interrompido. A89 foi consultada apenas para
leitura. Houve espera limitada, documentada, enquanto ela usava a GPU.

| Fase | Carga | Warmup | Parede da fase | Pico alocado PyTorch GiB | Pico reservado GiB | Pico RSS CPU GiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Editor AR (duas variantes) | 11,59 s | 0,45 s | 327,56 s | 2,173 | 3,307 | 2,380 |
| Editor dLLM (duas variantes) | 76,78 s | 2,06 s | 597,85 s | 6,072 | 7,492 | 3,466 |
| Leitor FP32 (sete métodos) | 8,79 s | 0,35 s | 95,70 s | 6,326 | 6,654 | 3,801 |

Cargas, imports e auditorias entram na parede da fase; não somá-los novamente.
As fases bem-sucedidas e CPU totalizaram 1.023,87 s de parede somada, abrangendo
**todos** os métodos, não um único sistema. Falha V1: 14,19 s adicionais;
diagnóstico separado sem parede total instrumentada. Downloads novos: cerca de
45 s/~1,9 GB (AR editor) e 71 s/~3,1 GB (leitor). Fontes/corpus/preparo intelectual
não tiveram duração total instrumentada; não se inventa um custo frio completo.
Picos PyTorch não incluem todo o driver; não se mediu energia nem pico NVML.
A vida do processo permanece sob o lock até liberar inclusive buffers residuais.

Não se mediu coexistência ou swapping editor+leitor por interação. A soma residente
não cobra esse custo adicional possível, portanto não justifica alegação de
latência de implantação. Treino/dados de treino/compute pago/API paga: **zero**.
Não há amortização de pós-treino a relatar; não se extrapola economia a um número
inventado de próximas interações, especialmente contra histórico já cacheado.

## Novidade, contribuição candidata e continuidade

[DiffuAgent §5.1 eqs. 3–4 e §6.1](https://aclanthology.org/2026.acl-long.2036.pdf)
já implementa memória incremental dLLM → AR. [DiffuMask](https://arxiv.org/abs/2604.06627)
já faz compressão por difusão e testa transferência. billion-context implementa
compressão incremental preservando prefixos; [CADOC](https://arxiv.org/abs/2609.37012),
[Self-GC](https://arxiv.org/abs/2607.00692) e
[TokenPilot](https://arxiv.org/abs/2606.17016) tratam política/semântica/custo de
cache. [ACON](https://arxiv.org/abs/2510.00615) já otimiza compressão com sinal
downstream. Leitura primária e mecanismos, inclusive LLMLingua-2, Elastic-dLLM,
edição multi-span e seleção por dependências, estão em `novelty.md` e complemento.
Ausência de artigo idêntico numa busca não provaria originalidade.

A contribuição desejada ainda teria de ser uma política ou pós-treino distinto,
com fidelidade dependente e vantagem integral específica sobre AR com igual
interface. O seletor lexical/fechamento/patch deste piloto é uma heurística de
triagem, não esse componente original. Também não implementa infill nativo
simultâneo em posições da memória inteira. Combinar mecanismos conhecidos ou
adicionar penalidade de cache ao objetivo não satisfaz o objetivo científico.

**Decisão: não avançar a pós-treino e não selecionar esta implementação como tema
central.** Não foi encontrada evidência positiva que sustente esse investimento.
O piloto não refuta toda política de memória por difusão: mede um único ponto
(16 passos, orçamento fixo, leitor pequeno, histórias oracle até ~6k tokens), sem
curva completa de qualidade/custo. Sintéticos cabem sem compressão e chamadas
periódicas desnecessárias poderiam ser evitadas por um agendador melhor.
Esses limites não autorizam promover novidade ou resgatar a campanha por outra
métrica. Nenhuma nova campanha ou treinamento foi selecionado.

## Reprodução e dados revisáveis

`reproducing.md`, `reproduce-v1a.sh`, `prepare.py`, `pilot.py`, `analyze.py` e
`verify.py`. `data/selection.json` fixa IDs; `data/streams.json` não contém alvos de
avaliação. Referências ficam em arquivo separado. `evidence/summary-v1a.json`,
JSONL brutos, revisões com nomes ocultos e respectivas chaves permitem auditoria.
`evidence/integrity-final.json`: 245 estados/leituras íntegros, 140 memórias neurais,
cinco verificações GPU de cache aprovadas na V1a. Correção de software não comprova
novidade ou utilidade científica. As falhas anteriores permanecem na mesma pasta.
