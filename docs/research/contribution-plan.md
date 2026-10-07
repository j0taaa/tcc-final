# Caderno de contribuição — M36

Data da investigação: 2026-10-07. Este caderno executa as partes independentes
do plano recebido; não registra aprovação do orientador, revisão humana,
prioridade científica ou resultados experimentais que não ocorreram.

## 1. Base e decisão atual

Base preservada: `c018c3843b7b5c4dda41cb72f3f7cfc19ad7af80`, branch `main`,
inicialmente limpa e sincronizada com `origin/main`. M34 e M35 estão concluídos;
testes no CI, posterior e limites de preparação não são tarefas novas.
Os arquivos científicos arquivados não serão sobrescritos. Exploração fica
neste caderno e em uma verificação matemática pequena, separada dos decoders.

**Gate de novidade/avanço: ainda aberto.** Não há uma nova contribuição
teórica selecionada e validada para substituir o artigo atual.

**Decisão:** rejeitar cache convencional e projeção genérica como novidade
central. Investigar, dentro da direção A, a **probabilidade exata da transição
observável de commitment escolhido depois de sortear a proposta**. Há uma
redução e prova escrita abaixo. A contribuição incremental possível é essa
operação com seleção dependente dos valores e seu custo adicional limitado;
Bayes, inside/outside e contagem ponderada são antecedentes.

Não encontramos nos trabalhos examinados o enunciado específico com o
filtro de fronteira e a mesma representação compilada. Isso é uma observação
da busca, **não uma prova de ineditismo**. A redução pode ser considerada uma
consequência simples de técnicas conhecidas; sua suficiência para TCC ou
publicação precisa de avaliação humana. Não substituir o protagonista do
artigo antes desse gate, nem alegar maior qualidade/velocidade de geração.

## 2. Contrato científico do candidato (uma página)

| Questão | Definição verificável |
| --- | --- |
| Problema | Depois de sortear uma conclusão válida e revelar os `k` tokens com maiores escores, qual é a probabilidade do novo canvas realmente observado? |
| Entradas | Gramática de bytes, slots finitos, suporte de IDs originais, probabilidades racionais de um passo, bytes dos tokens, canvas fixo, escores locais `s_i(v)` e desempate determinístico por posição. |
| Saída | Probabilidade exata de uma transição `(B,a_B)`, com suporte declarado; opcionalmente, marginais condicionadas ao evento. |
| Garantia principal | Integrar corretamente todas as propostas descartadas usando uma consulta com filtros unários ao plano já compilado, sem adicionar uma restrição global ao parser. |
| Comparador competente | Contagem ponderada/inside-outside ou eliminação exata com a mesma evidência. DUEL é comparado pela diferença de política, não por uma falsa corrida entre operações distintas. |
| Escopo implementável | Posterior atual: fonte LL(1) admitida, bytes composicionais não vazios, EOS ABSENT, suporte finito, massa válida positiva. O lema de evento vale para qualquer distribuição conjunta, mas não torna sua inferência tratável automaticamente. |
| Exclusões | Não calcular a probabilidade marginal do texto final somando implicitamente todas as trajetórias; não provar novidade mundial, acerto semântico, treinamento melhor ou superioridade geral sobre EPIC/FactorDLM. |

O objetivo MWPC anterior permanece inalterado: maximizar pesos de propostas
compatíveis com uma conclusão válida no suporte, por passo, com certificado.
O candidato calcula uma probabilidade de evento; não redefine esse objetivo
nem apresenta filtragem do evento como pruning seguro do problema original.

**Critério de investimento:** a operação precisa ser demandada por uma
avaliação/auditoria real de políticas que sorteiam antes de escolher posições.
Se o uso só pedir uma conclusão válida, o sampler existente já atende.
Se as posições forem escolhidas antes do sorteio, usar a consulta de evidência
comum; esse caso não justifica este recorte como novidade.

## 3. Aplicação principal: preenchimento de filtros JSON recursivos

Um programa recebe uma árvore de filtro parcialmente escrita, preserva os
trechos aprovados e completa várias lacunas. Uma gramática abstrata compacta:

```text
Filter = {"field": Field, "op": Op, "value": Value}
       | {"all": [Filter, ...]}
       | {"any": [Filter, ...]}
       | {"not": Filter}
Field  = "status" | "region" | "priority"
Op     = "eq" | "ne"
Value  = "open" | "closed" | "BR" | "EU" | 0 | 1
```

`...` significa lista não vazia, separada por vírgulas, de qualquer comprimento
que caiba nos slots. É EBNF explicativa: uma implementação de bytes precisa
fatorar prefixos das chaves e verificar LL(1). As alternativas não garantem
compatibilidade semântica entre campo e valor. Se isso for exigido, precisa
entrar explicitamente em uma gramática tipada ou em relações adicionais.

Exemplos de estruturas permitidas, e não respostas de um benchmark:

```json
{"field":"status","op":"eq","value":"open"}
{"all":[{"field":"status","op":"eq","value":"open"},{"not":{"field":"region","op":"eq","value":"EU"}}]}
{"any":[{"field":"priority","op":"eq","value":1},{"all":[{"field":"region","op":"eq","value":"BR"},{"field":"status","op":"ne","value":"closed"}]}]}
```

No uso candidato, registrar o novo canvas permite atribuir probabilidade
correta à ação observada para auditoria de políticas ou, futuramente,
razões de likelihood em treinamento. Não implementamos treinamento RL nem
afirmamos melhora nessa tarefa. O corolário abaixo vale também para JSON
completo atual, sem construir uma gramática que imponha um documento-alvo.

[TypeSafe, cookbook oficial de perguntas paralelas](https://docs.typesafe.ai/cookbooks/parallel_questions)
explica que cada pergunta é avaliada separadamente sobre o mesmo documento.
Isso motiva decisões consumidas por software; não demonstra que Jev gere
árvores conjuntamente, use o nosso método ou forneça um comparador de latência.

## 4. Fichas dos antecedentes e redução à solução competente

### Rivaud e Pachet, 2017

[Sampling Markov Models under Constraints](https://arxiv.org/html/1711.10436v1),
§3.1–3.3, em particular §3.2 e equações 3.1–3.2. Inferência/amostragem com
restrição de GLC não ambígua já é tratável; um produto por posição é um caso
mais simples que o modelo Markov considerado. §3.1 mostra a dificuldade da
contagem de palavras em representações ambíguas; §3.3 examina uma restrição
adicional de ambiguidade. Logo, M34 não descobriu a tratabilidade de CFGs.
A transformação de tokens em caminhos e a admissão LL(1) materializam uma
interface específica. O candidato M36 acrescentaria uma consulta de evento
da política de revelação, e não um novo algoritmo geral de parsing.

### Amarilli, Monet, Paul Raphaël e Salvati, STACS 2026

[On the Complexity of Language Membership for Probabilistic Words, v2](https://arxiv.org/html/2510.08127v2),
Proposição 3.1, Proposições 5.1–5.3, Corolário 5.4 e §6. Para uCFGs,
contagem ponderada tem limite `O(|G| n^3)` em operações aritméticas.
Circuitos decomponíveis e determinísticos capturam fatias de comprimento e
permitem avaliar probabilidades em tempo linear no circuito. O trabalho
também encontra classes ambíguas tratáveis; não é correto dizer que toda
gramática ambígua é intratável. Reavaliar um circuito quando mudam pesos
ou evidências é antecedente direto. O filtro unário proposto cabe nessa
infraestrutura; o custo linear da reavaliação não é uma nova descoberta.

### Dang e Ermon, 2026

[Constrained Decoding via Efficient Inference over Finite Automata, v1](https://arxiv.org/html/2607.07026v1),
§4.1–4.3, Proposição B.1 e §7. O alvo por passo é o produto mean-field
condicionado à restrição. O algoritmo fornece amostragem, marginais e
paralelismo; a prova B.1 trata da amostra completa daquele passo.
§7 exclui CFGs mais expressivas. A compatibilidade com remasking não é
uma prova de que a distribuição final seja o posterior do primeiro passo.
Autômatos determinísticos/unambíguos evitam viés pela multiplicidade de
caminhos; §3.2 distingue esse efeito. Não cobrar dessa abordagem a expansão
de pilhas quando uma cadeia compacta já resolve o caso regular.

### EPIC, revisão de 4 de outubro de 2026

[Efficient and Parallel Inference under CFG Constraints, v2](https://arxiv.org/html/2606.00722v2),
§3, §4.1–4.4 e Apêndice D. Conferimos a data `04 Oct 2026` no original.
O problema é testar completabilidade de atualizações em paralelo. O método
usa cache de lexing, cobertura regular com verificação exata posterior,
redução do lote e parsing Earley sobre ENFA. O parser evita determinização;
não é uma implementação que simplesmente enumera pilhas. A recuperação
extrai um witness válido e é explicitamente diferente de amostrar pelo
modelo. EPIC não oferece no texto examinado a massa de uma transição
estocástica do candidato. Sua política deve ser preservada na comparação:
não atribuir a ela a lei de um sampler exato distinto. O snapshot de código
vendorizado continua com seu commit pinado, sem atualização silenciosa.

### FactorDLM, setembro de 2026

[Constraints Are Graphs, Not Chains, v1](https://arxiv.org/html/2609.32900v1),
§3.1–3.3, Proposições 1–3, Algoritmo 1/D.1 e Apêndice B, composed-sampler drift.
Eliminação exata entrega MAP, massa, marginais e amostras; o plano é reutilizado
com novos unários e recusado quando as tabelas excedem o orçamento.
Há codificações compactas com auxiliares funcionais e quociente de alfabeto.
O Algoritmo 1 calcula confiança **no token amostrado** e só então escolhe
posições: é uma motivação operacional direta de M36. O estudo de drift
reconhece a diferença entre exatidão por passo e composição. Não demonstra
que o nosso backend seja mais rápido: os filtros do candidato também podem
ser usados nesse plano, sem aumentar seus escopos/largura.

### SparseMAP, 2018; LP-SparseMAP, 2020

[SparseMAP](https://proceedings.mlr.press/v80/niculae18a/niculae18a.pdf),
§3.1, equação (5), §3.2 e Apêndice A;
[LP-SparseMAP](https://proceedings.mlr.press/v119/niculae20a/niculae20a.pdf),
§2.2–3, equações (5), (8)–(10). Projetar unários sobre o politopo de marginais
válidas com penalidade quadrática já está no objetivo SparseMAP. Um oráculo
MAP gramatical é uma escolha de backend, não uma diferença no objetivo.
LP-SparseMAP trata decomposições em fatores e relaxações locais: uma relaxação
não integral não certifica automaticamente uma distribuição conjunta válida.
Trocar colunas por fluxos de parsing exigiria demonstrar a formulação exata
e seu custo; apenas escrever outro QP não resolve o gate de novidade.

### Predd e coautores, 2009

[Probabilistic coherence and proper scoring rules](https://arxiv.org/pdf/0710.3183),
§3, Teorema 1; §4, Proposições 1–3. Coerência equivale à pertinência ao
fecho convexo dos vetores de eventos realizáveis. Previsões incoerentes são
dominadas por previsões coerentes segundo as regras próprias admitidas.
Projeção euclidiana e sua garantia de Brier são antecedentes, não uma prova
nova por trocar eventos por tokens. A distribuição conjunta deve ser
construída; sortear marginais coerentes independentemente pode violar as
restrições. Isso elimina a direção B genérica como contribuição central.

### Antecedentes adicionais exigidos pelo novo recorte

- [DUEL, v1](https://arxiv.org/html/2603.01367v1), Definição 3.1,
  Algoritmos 1–2 e Teorema 4.3: `F(z)` escolhe posições antes de sortear;
  confiança é o máximo da distribuição por posição. Há um único caminho
  consistente com o texto. Não estender esse teorema ao sorteio seguido de
  seleção pelo valor sorteado. Nossa saída seria likelihood de transição/
  trajetória observada, não a likelihood marginal do texto prometida ali.
- [Lookahead Path Likelihood Optimization](https://arxiv.org/html/2602.03496v1),
  §3, equação (4), e §4: score por uma ordem de revelação e busca POKE-SMC.
  A avaliação deve distinguir um score condicionado à ordem da probabilidade
  de a política estocástica produzir essa ordem e esses valores.
- [Mask-Aware Policy Gradients](https://arxiv.org/html/2607.15200v1), §3.1–3.2,
  equações (5), (9): inclui a seleção na política e utiliza Plackett–Luce.
  Essa seleção aleatória não é o top-k determinístico do candidato. Não
  alegar que esquecem as máscaras, nem aplicar nosso filtro a PL sem prova.
- [Zhang e Chomicki, relatório de dezembro de 2007](https://cse.buffalo.edu/tech-reports/2007-13.pdf),
  Definições 2.1–2.5 e §§3–4: probabilidades de rankings/top-k em mundos
  possíveis são antigas, inclusive alternativas exclusivas por entidade.
  Nosso evento também é um evento top-k. A diferença candidata fica no
  condicionamento gramatical e na interface da transição dLLM, não em
  descobrir que se pode somar os mundos que produzem um ranking.

Leitura direcionada: formulações, algoritmos e resultados citados; não
alegamos leitura integral de todos os apêndices ou auditoria dos experimentos
desses autores. Fontes secundárias retornadas pela busca não sustentam as
afirmações acima. Buscas adicionais incluíram “top-k unmasking likelihood”,
“confidence transition probability masked diffusion”, “top-k probabilistic
databases” e “coarsening at random”. A busca é datada e não exaustiva.

## 5. Matriz de novidade

| Afirmação | Classificação | Fonte/objeção que delimita o resultado |
| --- | --- | --- |
| Produto por posição condicionado a uCFG é tratável. | Conhecido | Rivaud–Pachet §3.2; Amarilli Prop. 3.1. |
| Compilar uma floresta/circuito e trocar pesos. | Conhecido | Amarilli Prop. 5.1–5.3; FactorDLM §3.1. |
| Remover suporte alterando somente pesos das folhas. | Consequência direta | Consulta de evidência nos mesmos circuitos/fatores. |
| Massas e marginais exatas por inside/outside. | Conhecido | Parsing probabilístico e inferência em circuitos; M34 já credita. |
| CFG recursiva evita estados de pilha explícitos exponenciais. | Conhecido/escopado | Separação representacional M34; não é limite contra todo FactorDLM. |
| Projeção de Brier melhora previsões incoerentes. | Conhecido | Predd Teorema 1 e Proposições 1–3. |
| Parser MAP + projeção esparsa seria um método novo. | Consequência direta | SparseMAP eq. (5), §3.2. Rejeitado como protagonista. |
| Likelihood exata com posições escolhidas a partir só do canvas. | Conhecido | DUEL Def. 3.1 e Teorema 4.3. |
| Probabilidade de um resultado top-k integra mundos possíveis. | Conhecido | Zhang–Chomicki Def. 2.5, §§3–4. |
| A seleção posterior aos valores pode ser integrada por filtros unários sem nova compilação. | Candidato delimitado | Proposição E abaixo; avaliar se a especialização acrescenta suficiente conteúdo além de WMC/ranking. |
| Probabilidade da trajetória observada é produto das transições E. | Consequência direta | Regra da cadeia; não soma trajetórias de um mesmo texto. |
| Backend CFG supera todo FactorDLM/EPIC nessa operação. | Sem sustentação | FactorDLM também admite os filtros; EPIC resolve outra lei/política. |

## 6. Duas direções e decisão de eliminação

**A0 — Custo amortizado de atualizações:** mudar todos os logits pode exigir
ler todos os unários. Entregar todas as marginais também custa pelo menos o
tamanho da saída. Cache/propagação de alterações esparsas não é avanço sem
uma hipótese operacional justificável e comparação com circuitos dinâmicos.
Descartado como tese de novidade; não foi implementado outro cache.

**B — Coerência:** para os vetores one-hot válidos `phi(y)`, seja
`P = conv{phi(y)}`. Minimizar `||r-p||²/2` em `P` equivale a maximizar
`pᵀr - ||r||²/2`, ignorando a constante `||p||²/2`: exatamente SparseMAP
quando os features são os tokens. A desigualdade de projeção
`||r-z||² <= ||p-z||² - ||p-r||²`, para `z` válido, é conhecida.
Os scores ajustados do oráculo podem ser negativos: somar em cada slot a
constante `max(0,-min_v score_i(v))` os torna não negativos e acrescenta
o mesmo total a toda conclusão de n slots. Portanto a fronteira de pesos
não negativos do MWPC não impede essa redução nem cria uma novidade.
Um exemplo instrutivo não cria novidade: se só `00` e `11` são válidos e
as duas marginais são `9/10`, elas já são coerentes; condicionar o produto
gera probabilidade `81/82` para `00`, enquanto a projeção mantém `9/10`.
São operações diferentes. Rejeitar B como protagonista, preservar a objeção.

**A1 — Consulta da transição selecionada por valores:** a pergunta deixa de
ser “como reavaliar uma floresta?” e passa a ser “qual evidência representa a
ação observável do decoder?”. Proposição E resolve essa representação e
usa a consulta conhecida. Há uso possível em auditar likelihoods de
commitment/treinamento; não exige outro decoder. Avança à prova exploratória,
mas **não passa automaticamente pelo gate de significância/novidade**.

Outra tentativa examinada dentro de A foi acelerar o inside por multiplicação
de matrizes. [Mikhelson e Okhotin, MFCS 2023](https://drops.dagstuhl.de/storage/00lipics/lipics-vol272-mfcs2023/LIPIcs.MFCS.2023.67/LIPIcs.MFCS.2023.67.pdf),
§1, já descrevem a adaptação de Valiant a pesos em anéis sem contar a mesma
árvore duas vezes. Não promover simplesmente “parsing ponderado subcúbico” a
novidade. Não implementamos essa direção nem presumimos ganho prático dela.

## 7. Especificação e comparadores

`n >= 1` slots; suportes finitos de IDs originais `S_i`; emissão composicional
`b(v)` não vazia. `c` é o canvas; `U` contém suas posições livres.
Com EOS ausente, uma conclusão consome exatamente `n` tokens.

```text
F = { y em produto S_i : y preserva c e b(y) pertence a L(G) }
w(y) = produto q_i(y_i)
Z(q) = soma_{y em F} w(y)
P_q(y) = w(y) / Z(q), se Z(q) > 0
```

Cada `q_i` é racional não negativo; linhas livres podem somar menos que 1
(massa omitida explícita), linhas fixas são delta de peso 1. Não renormalizar
por linha para avaliar o evento. Aliases de bytes continuam eventos distintos.
O score `s_i(v)` pode ser `q_i(v)` original ou uma tabela local declarada;
não pode depender de valores em outras posições. Não confundir top-k de
**posições** com top-K de **vocabulário**.

Sorteie `Y ~ P_q`, escolha `k` posições de `U` de maior score `s_i(Y_i)`,
desempatando por menor índice. A observação é `E=(B,a_B)`; o resto da
proposta não é revelado. `k` é determinado pelo canvas antes do sorteio,
`0 <= k <= |U|`. Entrada malformada é erro; `Z=0` torna o kernel indefinido;
evento impossível tem probabilidade 0; orçamento esgotado é não resolvido.

| Método | Mesma entrada/saída? | Comparação válida |
| --- | --- | --- |
| WMC/inside-outside com evidência exata E | Sim | Backend competente e redução alvo; não adversário exponencial artificial. |
| FactorDLM + filtro E | Sim, se representação admitida | Mesma redução, largura inalterada; nenhum limite de exclusividade. |
| Enumeração completa | Sim, em casos pequenos | Oráculo independente, não evidência de superioridade. |
| Frequência Monte Carlo | Mesma probabilidade, aproximada | Erro/variância, custo por amostra e zeros observados explícitos; não chamar zero observado de evento impossível. |
| DUEL | Política diferente no caso geral | Coincidir somente quando B é função do canvas antes do sorteio. |
| EPIC | Política de propostas/aceitação diferente | Validar utilidade/completabilidade; não atribuir a massa do nosso kernel a seu rejection/recovery. |
| Produto das probabilidades dos tokens fixados | Geralmente não | Controle negativo de omissão da seleção/correlação, não melhor algoritmo conhecido. |

## 8. Proposição E — redução exata do evento de commitment

Defina a chave `r_i(v) = (s_i(v), -i)`, ordenada lexicograficamente;
maior chave significa prioridade maior. Para `k>0`, `|B|=k` e valores
`a_i em S_i`, seja `tau = min_{i em B} r_i(a_i)`.
Defina filtros por posição:

```text
g_i(v) = 1[v = a_i]                         se i em B
       = 1[r_i(v) < tau]                    se i em U fora de B
       = 1                                 se i já estava fixada
q^E_i(v) = q_i(v) g_i(v).
```

Então a probabilidade da transição observada é

\[
K_q(B,a_B) = Z(q^E) / Z(q).
\]

`k=0`: só o evento vazio existe e tem probabilidade 1. `k=|U|`: não há
filtros de ranking restantes; o numerador é o peso da conclusão observada.
Um conjunto de tamanho diferente de `k` não é uma transição desse kernel.

**Prova da representação.** Se o top-k produz `(B,a_B)`, os tokens em `B`
são os observados e nenhuma posição não selecionada pode superar a pior
chave selecionada. Como o índice desempata posições distintas, não existe
empate entre suas chaves; a condição é estrita. Reciprocamente, se esses
filtros valem, todos os `k` elementos de `B` precedem todos os outros.
Portanto, a aplicação do top-k produz exatamente esse evento. Isso prova
equivalência pontual, inclusive para propostas de peso zero.

**Prova da massa.** Multiplicar unários pelos indicadores mantém exatamente
os termos da soma em `F` que produzem `E`. Dividir por `Z(q)` é somar suas
probabilidades sob a lei original. Os eventos possíveis particionam as
conclusões, logo suas probabilidades somam 1. Não houve hipótese de
independência depois do condicionamento gramatical.

**Comparação correta.** Sem restrição conjunta, o numerador se fatoriza:
`produto_{i em B} q_i(a_i)` vezes as massas acumuladas abaixo da fronteira
nas posições restantes, dividido pela massa total do suporte. Usar essa
fórmula especializada é mais barato que compilar JSON só para um produto
independente. Com CFG, o filtro fornece evidência que o backend atual não
recebia de um log contendo somente os tokens fixados.

**O que a prova não faz:** ela não prova que ninguém já publicou a redução,
não fornece amostragem global da distribuição neural, nem melhora o
tempo de gerar um documento que já era gerado pelo sampler.

## 9. Exemplo manual e corolário JSON

Em `[A,B]`, pontuação fixa e dois valores `0/1`, tome
`q_A=(3/4,1/4)`, `q_B=(2/3,1/3)`, `s=q`, `k=1`.
Todos os quatro documentos são JSON válido, portanto `Z=1`.

| Documento sorteado | Peso | Token fixado |
| --- | --- | --- |
| `[0,0]` | 1/2 | A=0 |
| `[0,1]` | 1/4 | A=0 |
| `[1,0]` | 1/6 | B=0 |
| `[1,1]` | 1/12 | B=1 |

Assim `K(A=0)=3/4`, `K(B=0)=1/6`, `K(B=1)=1/12` e `K(A=1)=0`.
Usar somente `q_B(0)=2/3` superestima a segunda ação por fator 4:
para B vencer, também precisa ter ocorrido A=1, fato que o canvas esconde.
Esse contraexemplo é uma conta analítica, não um benchmark de desempenho.

**Corolário.** Para qualquer suporte de tokens finitos que represente
conclusões admitidas pela gramática JSON recursiva LL(1) atual, incluindo
campos existentes e alternativas de objetos/arrays/subárvores, o evento de
top-k de posições da Proposição E é calculável por reavaliação da mesma
floresta. A classe admite toda estrutura representada no suporte, não
apenas aberturas com fechamentos previamente determinados. A prova usa
equivalência de eventos e o teorema M34 do posterior; não exige particularizar
o documento nem pressupor uma resposta semanticamente correta.

## 10. Custo total e precisão

Sejam `S=sum |S_i|`, `F` o tamanho da floresta (células+alternativas),
`v,e` os vértices/arestas do DAG, `r` as regras binárias, `h` os heads.
Denote por `P_G` todo custo de admissão/comparação/normalização; ele não
é omitido nem alegado polinomial na gramática-fonte da API atual.

| Etapa | Limite/contabilização |
| --- | --- |
| Preparação | `P_G + custo dos bytes/trie + O(r v^3 + e h)` operações após normalização; limites cooperativos atuais podem recusar. |
| Base Z/marginais | `O(F+S)` operações e saída com S marginais. |
| Formar filtro de um evento | `O(k+S)` comparações se lookup local disponível; leitura/construção desse lookup é O(S). |
| Numerador | Uma reavaliação `O(F+S)`; API atual calcula outside também, mesmo se apenas Z for usado. |
| T consultas | Preparação + `O((T+1)(F+S))`, mais armazenamento/leitura dos inputs e outputs. Não há aceleração amortizada inventada. |
| Memória adicional | O(S+F) ao materializar a nova avaliação; nenhuma nova regra/fator/forest. |
| Aritmética | Racionais convertidos em inteiros por denominadores de linha; filtros 0/1 não aumentam denominadores. Reportar b, maior bitlength intermediário, e custo de multiplicação/gcd, não apenas número de operações. |

Em particular, com `b` bits intermediários e `Mul(b)` como custo de produto,
a avaliação custa `O(F Mul(b))`, além de alinhamento, lcm/gcd e construção de
S frações. Entrada racional de precisão arbitrária não é custo constante.
Os filtros acrescentam comparações racionais (produtos cruzados) e zeros.

**Limite conservador em bits para o plano admitido.** Seja
`D_i = lcm{denominadores de q_i}` e `B = sum_i ceil(log2(D_i+1))`.
Cada peso inteiro de uma folha de closure é no máximo D_i. Um caminho
do DAG acíclico usa no máximo uma closure por slot; seu produto é no máximo
`D=produto_i D_i`. Uma derivação CNF não vazia tem no máximo `v-1` folhas
e menos de `2v` nós. Há no máximo F escolhas de alternativas em cada nó.
O limite de Catalan para as formas das árvores dá no máximo
`N=v [4(1+F)^2]^v` árvores decoradas, usando um limite deliberadamente maior
que o número de caminhos aceitos. Logo cada inside
é no máximo ND. Um outside conta contextos de árvore com um buraco:
preencher o buraco com uma derivação fixa da célula injeta esses contextos
em árvores decoradas com um nó marcado; há menos de 2vN deles e seu peso
é no máximo D. Células sem contexto têm outside zero. Assim outside é no
máximo 2vND, e produtos intermediários usam
`b=O(B+v log(F+2)+log(v+1))` bits. Pesos não negativos mantêm somas
parciais abaixo do total. B é limitado pela soma dos bits dos denominadores
da entrada (lcm não excede o produto). Isso contabiliza precisão de inside,
outside e produtos; reduzir frações também tem custo de gcd.

Para escores racionais de L bits, formar E custa
`O((S+k) Mul(L+log(n+1)))` em uma implementação por produtos cruzados.
Portanto o custo adicional é polinomial no plano e na entrada numérica.
Não é um limite polinomial de toda preparação a partir da fonte: P_G
continua separado e limitado por orçamento. Os fatos usados nesta análise
(contagem de árvores e aritmética de inteiros) são clássicos; a revisão
humana deve conferir sua aplicação ao DAG de tokens e aos contextos.

No backend por fatores, são evidências unárias: os escopos e a ordem de
eliminação são os mesmos. Um fator global de ranking construído de forma
ingênua seria um comparador inadequado; a redução elimina sua necessidade.
Isso é uma vantagem de formulação disponível também a FactorDLM.

## 11. Ligação com o ciclo de dLLM

```text
compile a gramática e o suporte inicial admitidos
para cada passo:
    obtenha q_t e s_t do forward registrado, preservando probabilidades originais
    avalie P_t no canvas atual
    se massa zero/recusa: mantenha a distinção de status e pare esse cálculo
    sorteie uma conclusão Y válida
    escolha B pelo top-k de s_i(Y_i), com desempate declarado
    antes de atualizar o canvas, calcule K_t(B,Y_B) com a Proposição E
    registre evento, suporte, scores, q_t e K_t
    fixe Y_B; no próximo passo use o novo forward e o novo canvas
```

O filtro E é uma **consulta de likelihood**, não uma restrição a persistir
silenciosamente no próximo passo. O decoder original condiciona só nos tokens
que fixou; manter o filtro mudaria a política. A probabilidade de uma trajetória
observável registrada é `produto_t K_t`; isso usa a regra da cadeia.
Dois caminhos podem produzir o mesmo texto final: somá-los não é automático.
Remasking de posições antigas, expansão de suporte e mudanças de gramática/
tokenizer/EOS requerem recompilação conforme a API existente. Seleção aleatória
de posições, quotas ou score dependente da proposta inteira exige outra prova.

**Corolário opcional de gradiente, ainda sem validação de implementação:**
com ranking fixo localmente e q positivo parametrizado por logits, derivar
`log K` dá marginais condicionadas a E menos marginais de P nas posições
livres. Isso é a identidade conhecida de partições exponenciais. Em fronteiras
de ranking o kernel pode mudar de forma descontínua; não prometer gradiente
global nem vantagem RL só com essa identidade.

## 12. Revisão adversarial

| Objeção/caso | Tratamento |
| --- | --- |
| Z=0 | Kernel indefinido; nunca devolver uma probabilidade condicional inventada. |
| Evento impossível com Z>0 | Numerador zero; distinto de timeout. |
| Valores empatados | Chave (score,-posição), desigualdade estrita; omitir desempate quebra o filtro. |
| Token de peso zero | Incluído na equivalência de conjuntos, massa zero. |
| Aliases/prefixos | Comparar IDs originais; eventos de bytes não substituem eventos de tokens. |
| Posição já fixa | Fora de U; preservada com delta de peso 1. |
| Top-K/vocabulário incompleto | Resultado exact_on_support; não estender ao vocabulário omitido. |
| Fixar a posição no input do numerador com peso 1 | Perde o fator q_i(a_i); usar pesos originais com alternativas zeradas. |
| Produto de marginais | Não integra seleção nem dependências; contraexemplo acima. |
| Parser ambíguo | Lema E continua correto, mas massa do backend precisa de representação sem dupla contagem. LL(1) atual permanece. |
| Reusar um witness congelado | Preserva a distribuição congelada e pode ser mais barato; não chamar resampling corrigido de avanço geral. |
| Alterações neurais futuras | Lei/likelihood por transição registrada; sem otimalidade ou posterior global implícitos. |

## 13. Validação pequena e protocolo antes de desempenho

Uma verificação de pesquisa pode enumerar produtos de IDs pequenos, reconhecer
JSON com `json.loads` ou delimitadores com pilha independente, agrupar cada
conclusão pelo top-k diretamente e comparar cada massa agrupada com filtros
de fronteira+posterior atual. Deve cobrir **todos** os k e eventos dessas
instâncias, incluindo eventos impossíveis. Isso procura erros na Proposição E;
não mede novidade, superioridade de latência ou software inteiro.

Protocolo de desempenho **provisório, não executado**: só registrar versão
imutável depois de completar o item 22 recebido e passar pelo gate humano.
Separar os exemplos usados para encontrar erros de uma população de avaliação
selecionada por origem/tamanho antes de executar o candidato. Usar todos os
eventos viáveis nas instâncias pequenas; nas grandes, escolher eventos por
semente/política fixa, incluindo massa rara e recusas. Não selecionar vitórias.

Comparadores: WMC com filtro correto, FactorDLM quando a mesma codificação é
admitida, fórmula acumulada independente quando aplicável, enumeração pequena
e Monte Carlo com o mesmo orçamento. Produtos que omitem seleção são controles
negativos, nunca a única comparação de “superioridade”. EPIC continua baseline
de geração/validade; não recebe artificialmente outra distribuição-alvo.

Métricas: igualdade racional onde há oráculo; tempo/preparação/consulta,
memória/bitlength, recusas/status; variância/erro de MC. Separar forward,
construção de suporte/token-DAG, compilação e consulta; contabilizar total.
Salvar commit, config, seed, revisões de modelo/tokenizer, hash de gramática,
escores/política de suporte e ambiente nos JSONL. Nenhuma captura de modelo,
treinamento ou timing novo é resultado deste caderno.

## 14. Dossiê pronto para revisão, sem aprovação fictícia

O orientador/revisor recebe contrato (§2), antecedentes (§4), matriz (§5),
redução concorrente (§6), prova (§8), aplicação (§9), custos/limite aberto
(§10) e escopo de integração (§11). Questões específicas para sua avaliação:

1. O filtro para top-k pós-sorteio é uma contribuição incremental suficiente
   ou apenas consequência direta de WMC/ranking sem conteúdo de pesquisa?
2. Há antecedente que já calcula o mesmo kernel observável com o mesmo custo?
3. Qual uso exige esse kernel: auditoria de políticas, avaliação de trajetórias
   ou treinamento? Só afirmar utilidade de treinamento depois de validá-la.
4. A prova de equivalência e o custo total têm alguma lacuna? Conferir o
   limite conservador de bits, especialmente a contagem de contextos outside.
5. O recorte cabe na entrega institucional e no tempo disponível?

Datas trazidas pelo usuário, ainda **não conferidas no regulamento original**:
resultados/análises 21/10/2026, artigo para banca 23/11/2026, defesas 02–10/12/2026.
Não há contato autorizado com destinatário/canal nem parecer fornecido.
Preparar o dossiê não equivale a obter revisão independente.

Após o parecer: se insuficiente, rejeitar A1 como protagonista sem apagar
seu contraexemplo; formular outro gargalo antes de ampliar código. Se aceito,
implementar uma API pequena sobre a reavaliação atual, com status/suporte
explícitos, checks independentes no CI e protocolo completo. Formalizar o
lema distintivo em Lean somente se o retorno justificar o esforço; não
apresentar certificados existentes como mecanização de E.

Publicação: rascunho futuro centrado na operação e no comparador equivalente,
com definição → redução → prova → custo → aplicação → limites. Introdução
credita parsing/WMC e posiciona DUEL/ranking; EPIC e FactorDLM recebem suas
garantias reais. A seção experimental complementa o resultado matemático,
não determina sua validade. Não prometemos aceite nem submissão automática.

Estrutura concreta para uma eventual seção nova, **ainda não incorporada ao
artigo**: título provisório “Probabilidade de transições de commitment com
seleção por confiança”; problema que distingue canvas/proposta/evento;
Proposição E e proof map representação → massa → custo → aplicação;
controle analítico `[A,B]`; relação com DUEL/WMC/rankings e uso possível do
kernel; limites de trajetórias finais, treinamento, EOS e top-K. A frase de
contribuição precisa ser revista depois do parecer, antes de chamar isso de
avanço teórico original. Um resultado de correção pode ser útil e ainda
assim não satisfazer o gate de novidade pedido.

## 15. Evidência executada e pendências

`tests/test_cfg_posterior.py::test_top_k_commitment_event_reduction` executou
8.016 consultas de eventos, sem divergência racional contra agrupamento por
ordenação direta de propostas enumeradas. São 24 inputs em quatro famílias:
13 têm massa positiva, 11 massa zero. Todas as cardinalidades e todos os
eventos, inclusive impossíveis, são examinados nos inputs de massa positiva.
Reconhecedores independentes: pilha e `json.loads`; semente 20261007.
Há aliases, tokens prefixos, posições fixas, massa omitida, zeros e empates.
A família JSON de cinco slots admite listas de dois valores (`[0,1]`),
arrays aninhados (`[[0]]`), objetos aninhados (`{"a":{"b":0}}`) e documentos
com um único valor e espaços (`[0]  `), com os mesmos suportes declarados.
Não é apenas uma família de aberturas/fechamentos predeterminados.
Não há seleção por desempenho nem medida de latência. O teste de pesquisa
fica na suíte pequena existente e é descoberto pelo CI sem outra estrutura.

Comando: `.venv/bin/python -m unittest discover -s tests
-k top_k_commitment_event -v` (uma verificação de pesquisa passou).
Antes de ampliar a cobertura estrutural de JSON, a versão exploratória
inicial já havia verificado 2.076 eventos; essa conta não é um ganho medido.
Gates locais executados: `make check test` (lint/formatação, mypy em 58 módulos
e suíte focada), `make build-rust`,
`make check-formal LAKE="$HOME/.elan/bin/lake"` (41 statements existentes,
exemplo canônico e auditoria), `make paper` (inclui `article-results-check`:
3.683 arquivos científicos preservados; artigo de 16 páginas sem overflow ou
referências pendentes). Depois de ampliar o caso JSON, `make test` passou
os 12 checks com os 8.016 eventos finais. `ruff check` no arquivo de testes
e `git diff --check` passaram. Fontes/tabelas do artigo não mudaram; E não
está mecanizada em Lean. Builds não validam novidade ou toda a implementação.

| Itens do plano recebido | Situação |
| --- | --- |
| 1, 2, 4 | Base, contrato candidato e aplicação documentados. |
| 5–8 | Revisão direcionada, matriz e reduções executadas. |
| 9 | Gate de escolha de protagonista aberto: não há avanço novo suficientemente validado. |
| 10–18 | Especificação/prova/custos/integração exploratórios e verificação pequena; não são aprovação da novidade. |
| 3, 19 | Alinhamento e revisão humana reais pendentes. |
| 20, 21 | Implementação principal e sua validação aguardam os gates; só foi acrescentado o oráculo de pesquisa do item 18. |
| 22 | Protocolo provisório sem medições; texto recebido termina em “Separe casos usados”. |
| Publicação | Dossiê/estrutura preparados; artigo central não foi reescrito nem submetido. |

Sem nova implementação principal, novos resultados de modelo,
alteração das tabelas do artigo, revisão humana ou submissão. O restante do
item 22 e o calendário/parecer foram solicitados ao usuário enquanto as partes
independentes continuam.
