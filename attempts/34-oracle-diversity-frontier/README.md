# A34 — Fronteira matemática entre custo e diversidade de um oráculo

Iniciada em 2026-10-11 durante a campanha CONGELADA A32/v4. Investigação
independente, por enquanto escrita: não altera aquele produtor, não herda
seus timings e não tem novidade ou publicação confirmadas.

## Oito critérios, antes de qualquer implementação

1. **Uso real.** Coordenar dois candidatos de um decoder dLLM+GLC sem calcular
   a probabilidade de uma classe de transições. O primeiro candidato permanece
   literal e cada marginal continua sendo a do decoder original. Um head
   congelado permite draws auxiliares sem outro forward, mas rankings,
   recuperação e parsing continuam custando. JSON/DSL tem verificador externo;
   a classe nunca é a resposta correta obtida do gabarito.
2. **Diferença candidata.** Ruína do jogador, Cramér–Rao sequencial, fábricas
   de moedas e antitéticos são antigos. Investigar uma fronteira EXATA, para
   todo orçamento esperado real, da fração minimax do ganho de Fréchet obtida
   por QUALQUER acoplador p-blind regular. A contribuição NÃO é uma nova prova
   de correção desses princípios. A integridade dos outputs introduz um limite
   mais forte que Cramér–Rao quando o orçamento não é inteiro. A prioridade
   desse contrato específico ainda precisa de revisão, especialmente DeGroot
   1959, Ghosh1987 e os antecedentes de fábricas de Bernoulli.
3. **Por que escolher.** Para orçamento b>=2, a candidata fornece pelo menos
   eta(b)=1-2(2m+1-b)/(m(m+1)) da melhoria máxima binária sobre iid, m=floor(b),
   para TODA probabilidade desconhecida p. Nenhum algoritmo da classe pode
   garantir mais com esse orçamento. b=3 dá pelo menos1/3, b=4 pelo menos1/2.
   Isto não é vitória contra quem conhece p, iid com mais saídas, EPIC em
   latência total ou qualidade semântica geral. Esses controles são obrigatórios.
4. **Matemática.** Especificar oráculo, acesso apenas por amostragem, outputs,
   orçamento TOTAL e regularidade. Primeiro provar a fronteira inferior com
   score parado e aritmética inteira; depois a construção que a atinge, lei
   completa e corolário para uma transição estruturada. Provas escritas em
   `work/theory-v1.md`, ainda sem revisão independente ou Lean.
5. **Testes.** Não iniciar mais uma campanha neural apenas porque a fórmula
   parece nova. Primeiro resolver reduções e contraexemplos. Se sobreviver,
   oráculos independentes pequenos e protocolo externo congelado, controles
   com probabilidades conhecidas, corridas, walks, pools e custo completo.
   A32/v4 permanece uma avaliação distinta e conserva TODOS seus resultados.
6. **Custo completo.** Esperança b é contagem de draws, não tempo. A cauda da
   parada é exponencial, mas sua constante depende do orçamento; classificar
   transições pode ser caro. Incluir memória, bits, setup, forwards, parsing,
   transferência, recuperação e saída. O bound é de um passo; só a dominância
   fraca por encontro pode passar ao processo adaptativo, não a fração minimax.
7. **Objeções.** O resultado pode estar inteiro em estimação sequencial ou ser
   um corolário imediato pequeno demais. Uma classe sem sinal semântico dá
   ganho ZERO; eventos raros têm ganho absoluto no máximo p². Mais candidatos
   podem ser melhores. A prova não autoriza escolher p=1/2 num benchmark ou
   excluir um comparador prático que dispõe de logits/probabilidades.
8. **Artigo.** Faltam prioridade específica, argumento de significância,
   revisão matemática, implementação mínima e aplicação barata útil. Nenhuma
   dessas obrigações é cumprida por organizar outra tentativa. Se a redução
   eliminar a diferença científica, preservar e recusar, sem campanha extensa.

## Contrato e gate inicial

Somente notas matemáticas e revisão em `work/`. Não importa código de outra
tentativa. Não chamar uma construção clássica, uma lista de buscas negativas
ou um futuro oráculo de correção de confirmação de novidade/publicabilidade.

## Refinamento delimitado, depois da prova inicial

`work/bounded-runtime-v2.md` responde novamente aos oito critérios e deriva
fallback por contagem determinística que conserva as marginais completas.
Um bound espectral clássico certifica a perda de diversidade normalizada;
não é exatidão da lei conjunta infinita nem fallback por timeout físico.
`work/ruin.py` é referência mínima para procurar erros, com quatro oráculos
independentes passando0.159s depois do encerramento dos timings A32. Não é integração neural ou implementação maior. A32/v4 não muda.

Quatro verificações independentes PASSARAM em
`tests/test_oracle_diversity_frontier.py`: coeficientes de todos os transcripts
pequenos, equações de absorção racionais, payloads originais e validação prévia.
Enumeração verifica12.264 transcripts binários,66 sistemas racionais de
absorção e5 orçamentos fracionários,5.832 transcripts de payloads/aliases
e todos os eventos pequenos. Suíte inteira139 testes passa67.511s; Ruff
passa. São checks de correção, não medição de novidade/utilidade. Na versão
v2 somente o abstract de Wasan1964 tinha sido lido; esse fato histórico não
é a fronteira atual de leitura.

## V3: fonte primária e custo antes da expansão nativa

[primary-reading-v3.md](work/primary-reading-v3.md) credita a expressão s_b
e mistura de orçamentos JÁ existentes em Wasan1964; apenas sharpness para
outputs de par restrito permanece diferença candidata. O aparente
contraexemplo de estrita desigualdade é objeção auditada, não descoberta
publicável declarada. Original Ghosh1987 e prioridade específica continuam
abertos.
[full-cost-v3.md](work/full-cost-v3.md) compara TODOS planos iid de contagem
não adaptativa no MESMO orçamento esperado. Preserva explicitamente a
vitória iid3 quando draws já geram outputs completos e a objeção de retry
verificado. Fronteira barata de transição realmente aceita e sinal da classe
continuam necessários; não foram demonstrados em dados neurais A34.

## Protótipo nativo mínimo: falha preservada e correção delimitada

O draft inicial comparou indevidamente timestamps de rejeição como decisões;
a recusa e fonte estão preservadas em v4 e `work/native-draft-audit-v4.md`.
A correção conserva os eventos/timestamps do upstream e compara IDs,
posições rejeitadas e status.36/36 replays completos CPU/CUDA com heads
FALSOS preservam literalmente a primeira trajetória e RNG do chamador;
54 forwards FALSOS. Dados em `work/evidence/native-fake-v5.json`.
A seleção usa o primeiro EVENTO nativo, inclusive ausência de progresso ou
falha, sem filtrar sucessos. Payload contém generator/control locals e
tapes Python/NumPy/Torch, não um canvas reconstruído. A equivalência da
política pressupõe consultas conclusivas; não se promete preservar a lei de
timestamps, deadlines físicos ou hardware não determinístico. O fixture
atual transfere um token por passo e ainda não verifica sucesso do batch
regular-cover. Nenhum head neural, ganho real ou novidade confirmada.

## V6--V8: cap exato, branch nativo e diagnóstico congelado

`work/barrier-three-cap-v6.md` e o quinto oráculo verificam a lei/custo exatos
com cap12:341/1024 do ganho binário máximo,1023/1024 da fronteira esperada3.
Não é percentual de qualidade/velocidade. A tentativa de cobrir batch com
gramática de um dígito foi recusada; o fixture de dois dígitos revelou deadlock
OnceCell no Rust externo, também preservado com fonte e trace. Preparar a
MESMA gramática duas vezes pela API nativa inicializa a flag antes da chamada
recursiva; nenhum fonte do vendor foi modificado. Com esse setup comum,
144/144 replays CPU/CUDA preservam decisões da primeira trajetória e streams
do chamador, incluindo132 sucessos reais do helper batch em289 chamadas.
198 forwards FALSOS; evidência `work/evidence/native-fake-v8.json`.

Os oito critérios refinados e screen de recursos ANTES de heads estão em
`work/arithmetic-protocol-v7.md/json`: oito primeiras questões públicas de
treino escolhidas anteriormente só pelo hash do input; GLC recursiva de
programas aritméticos JSON, sem gabaritos na gramática/classificador/producer.
O oráculo para quando bytes aceitos determinam QUALQUER operador raiz ou o
gerador termina/recusa. Pode gastar VÁRIOS forwards, todos contabilizados.
32 prefixos iid e uma continuação literal por input investigam apenas custo
e variedade de classes, não qualidade/superioridade/novidade. Falhas entram
na classe declarada, não são reamostradas. Recuperação externa autocomplete
não faz parte deste diagnóstico; será obrigatória numa comparação completa.
O interpreter tem guardas numéricos explícitos para entrada não confiável.
Suíte142 testes PASS68.228s; checks de Ruff e integridade35/96 passam.
Nenhum head A34 executado até este freeze. Não iniciar qualidade extensa se
o screen de recursos falhar; não chamar seu eventual sucesso de contribuição
confirmada ou novidade suficiente para publicar.

O diagnóstico raiz está COMPLETO no produtor fe3fa65: oito casos,256
prefixos,1.845 forwards novos, zero erros de execução do producer; só6/8
primeiras continuações foram programas executáveis completos. NENHUM caso
passou o screen. Classes variadas só ficaram disponíveis tarde; classes
baratas eram degeneradas. Dados/metadata/decisão/hashes estão em
`work/evidence/arithmetic-root-diagnostic-v7`. Sem gabaritos/acurácia ou
confirmação independente; NÃO iniciar campanha de qualidade desta raiz.

RefinamentoV8 em `work/arithmetic-protocol-v8.md/json` testa SOMENTE recursos
do primeiro token numérico efetivamente aceito, inclusive fora do prefixo
contíguo. Mesmos oito inputs,32 seeds novas, gate de custo inalterado. Classe
par/ímpar não é semântica; pode ter sinal zero mesmo variando. Checkpoint
independente preserva IDs/aliases, ignora tokens anteriores/propostas brutas
e não filtra falhas. Fonte/evidência V7 estão em v9 antes desta alteração.
Nenhuma capturaV8 executada neste freeze; não alegar utilidade/publicação.

V8 está COMPLETA no produtor f7114ac:8/8 registros,256 prefixos,2.330 novos
forwards, zero erros do producer,5/8 primeiras caudas executáveis.1/8 screen
positivo, abaixo dos2 predeclarados; não iniciar campanha de qualidade desta
classe. Dados integrais em `work/evidence/arithmetic-number-diagnostic-v8`.
Paridade variada não demonstrou sinal semântico ou vantagem integral.
`work/ranked-sampling-primary-v10.md` credita o antecedente de ranking
barato/medição cara e preserva a objeção de um controle adaptativo mais barato.
