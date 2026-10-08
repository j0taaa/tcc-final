# Caderno de contribuição — M36

Data da investigação: 2026-10-07. Este caderno executa as partes independentes
do plano recebido; não registra aprovação do orientador, revisão humana,
prioridade científica ou resultados experimentais que não ocorreram.
O usuário autorizou completar o item 22 e decidir as tarefas posteriores;
também confirmou que ainda não dispõe de comentários externos.

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
- [Grünwald e Halpern, Updating Probabilities, 2003](https://arxiv.org/pdf/cs/0306124),
  §3, Teorema 3.1: ignorar como uma observação foi selecionada preserva o
  posterior se a probabilidade de revelá-la é constante entre os mundos
  compatíveis de massa positiva (CAR). É antecedente direto para a pergunta
  sobre os tokens descartados. O diagnóstico quantitativo abaixo é uma
  especialização de condicionamento, não um novo princípio estatístico.

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
| Ignorar seleção só preserva o posterior quando o mecanismo é constante nos mundos compatíveis de massa positiva. | Conhecido | CAR, Grünwald–Halpern Teorema 3.1. |
| Quantificar a diferença entre condicionar na ação e só nos valores revelados. | Consequência direta | Identidades de condicionamento em eventos aninhados; §8.1. |
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

### 8.1. Diagnóstico exato da informação de seleção omitida

Seja `A = {y em F : y_B=a_B}` o evento que considera só os valores
revelados. O evento completo E da Proposição E satisfaz `E contido em A`.
Para `P(E)>0`, defina `beta = P(E)/P(A)`. Então:

```text
beta = Z(q^E) / Z(q^A), com q^A filtrado só nos valores de B
TV(P(.|E), P(.|A)) = 1 - beta
KL(P(.|E) || P(.|A)) = -log(beta).
```

TV usa metade da soma das diferenças absolutas. A igualdade de TV resulta
de separar E de A\E: dentro de E, `P(.|E)=P(.|A)/beta`; fora de E,
o primeiro posterior tem massa zero e o segundo massa `1-beta`.
A razão das densidades em E é constante `1/beta`, provando KL. Os demais
mundos têm massa zero nas duas leis e não contribuem. A orientação oposta
de KL pode ser infinita quando `beta<1`; não confundir as duas.

Portanto condicionar só nos valores é correto para esse evento positivo
**se e somente se beta=1**. Para seleção determinística, isso é a condição
CAR no suporte de A: o indicador de escolher B deve ser constante nele;
como E tem massa positiva, a constante deve ser 1. Para seleção aleatória,
CAR admite outras constantes e o filtro binário top-k não se aplica.

No exemplo `[A,B]` abaixo, observar B=0 dá `beta=(1/6)/(2/3)=1/4`:
TV entre as leis dos **tokens propostos restantes** é `3/4`, e KL é
`log(4)`. Duas consultas de massa quantificam essa diferença sem estimar
frequências. São identidades clássicas aplicadas ao evento; não estabelecem
novidade nem erro semântico do JSON.

**Limite essencial:** comparar esses dois posteriors do mesmo sorteio
latente não mede automaticamente o desvio do próximo passo do decoder.
Ele pode intencionalmente descartar o sorteio e fazer outro forward.
Também não certifica qualidade, distribuição do texto final ou ganho RL.
Este diagnóstico serve para uma auditoria que realmente procure reconstruir
a lei da proposta a partir do log, não para declarar incorreto outro alvo.

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

### Item 22 concluído por decisão autorizada: protocolo de avaliação

**Estado: desenho definido; execução e configuração final não liberadas.**
A escolha do teorema e os gates de novidade/revisão continuam necessários.
Estes parâmetros são uma decisão prévia, não resultados nem uma aprovação de
A1. Se outro candidato mudar a operação, versionar o protocolo **antes** da
avaliação; não aplicar retrospectivamente essas decisões a dados já vistos.

1. **Desenvolvimento versus avaliação.** Todos os inputs M34, casos externos
   já examinados no projeto, exemplos deste caderno e os 8.016 eventos são
   desenvolvimento/regressão. Reparti-los agora por hash não cria avaliação
   inédita. Usar uma captura prospectiva de regras externas como avaliação;
   nenhum resultado do solver decide sua inclusão.
2. **Uma aplicação real.** Manter árvores de filtros como aplicação principal,
   ligando-as ao formato [JsonLogic oficial](https://jsonlogic.com/): regras
   JSON aninhadas executadas sobre dados. O AST explicativo da §3 pode ser
   traduzido: `eq/ne` para `===/!==`, `field` para `var`, `all/any/not` para
   `and/or/!`. Por exemplo,
   `{"===":[{"var":"status"},"open"]}`. Não há adaptador implementado nem
   garantia de equivalência semântica para coerções/tipos não especificados.
   Uma primeira avaliação pode usar a gramática JSON atual: então só a
   sintaxe é garantida, não aridade, operadores válidos ou resposta correta.
3. **Origem externa previamente definida.** Os testes oficiais de aplicação
   usam `https://jsonlogic.com/tests.json`, conforme
   [tests/tests.js, linhas 58–79](https://github.com/jwadhams/json-logic-js/blob/c5c73601c90b11e98f6846609bac4dec203d1c18/tests/tests.js#L58).
   Revisão do consumidor: `c5c73601c90b11e98f6846609bac4dec203d1c18`.
   Em 2026-10-07 a identidade dos bytes do corpus foi obtida, sem enumerar
   regras nem executar modelos/solvers: 17.574 bytes, SHA-256
   `a202b65edda0d7ab687c758b8f10cfe9ba75561cd7166e5650710f88f26303a4`.
   A URL é mutável: exigir esse hash; se não estiver mais disponível, registrar
   falha de aquisição e uma nova versão, nunca substituir silenciosamente.
   Conferir licença/permissão de redistribuição do corpus antes de copiá-lo
   ao repositório. O consumidor MIT não determina sozinho a licença do site.
4. **Seleção e divisão antes dos resultados.** Considerar todas as entradas
   não comentário que sejam triplas `(regra,dados,esperado)`, com regra
   serializada em JSON compacto UTF-8 de até 4.096 bytes. Preservar tipos;
   proibir NaN/Infinity. Deduplicar/agrupar pelo JSON canônico da regra,
   independentemente dos dados, para não colocar a mesma regra em ambos os
   conjuntos. Remover da avaliação qualquer regra já utilizada no projeto,
   com motivo registrado. Ordenar grupos pelo SHA-256 de
   `"m36-v1:20261007:" + regra_canônica`; os de digest inteiro módulo 5 igual
   a zero são calibração, os demais avaliação. Se exceder 128 grupos de
   avaliação, usar os primeiros 128 nessa ordem. Não alegar generalização
   para famílias de AST inteiramente novas só por essa divisão. Salvar IDs,
   hashes, contagens e todas as exclusões antes de rodar o candidato.
5. **Capture uma vez, compare no mesmo input.** Para todos os métodos, mesmos
   canvas, probabilidades racionais originais, bytes/IDs, posições fixas e
   EOS ABSENT. Captura nova de dLLM é opt-in; modelo/tokenizer e suas revisões
   devem ser fixados antes dela, reaproveitando o pipeline existente quando
   adequado. Não prometer uma captura sem esses artefatos. Na avaliação de
   infilling, ocultar posições por semente `20261007`, com frações
   `1/4, 1/2, 3/4`, arredondadas para cima e limitadas ao número de posições.
   Suportes top-K `16,32,64` são declarados; não inserir a referência no
   suporte após observar massa zero. Logs continuam distinguindo massa
   omitida e massa gramatical válida.
6. **Operação e comparadores.** Para A1, o alvo é a probabilidade de uma
   transição, não a perplexidade do texto final. Usar WMC/inside-outside com
   os filtros corretos e FactorDLM com boa codificação/evidência unária quando
   a classe for admitida. Enumeração é oráculo pequeno; a fórmula acumulada
   é o controle competente no produto independente. Monte Carlo estima a
   mesma transição e recebe o mesmo orçamento total, incluindo amostragem
   condicionada. Produtos que omitem seleção são controles negativos, nunca
   o único adversário. EPIC/serial continuam comparadores da operação de
   geração/validade, sem lhes atribuir a distribuição deste sampler.
7. **Consultas sem seleção favorável.** Nos casos pequenos, enumerar todos
   os eventos quando o espaço declarado couber em 100.000 combinações de
   IDs; o limite depende do tamanho, não do resultado. Nas instâncias maiores,
   usar `k` em `{1,ceil(|U|/2),|U|}` (sem duplicatas) e 16 propostas válidas
   por semente para consultas observadas. Adicionar 16 eventos escolhidos
   uniformemente entre posições/IDs do suporte por k, independentemente da
   viabilidade. Relatar separadamente essa população; ela não é amostragem
   do decoder. Falha em produzir propostas é registrada, não substituída por
   um caso mais fácil. Sem posições livres, só o evento vazio é admitido.
8. **Recursos e medição.** Por processo de solver: 30 segundos para preparar
   e 30 por consulta; limite externo de memória de 2 GiB. O backend CFG usa
   200.000 células, 1.000.000 alternativas e 1.000.000 unidades de preparação.
   Orçamentos sem correspondência em outro método não são chamados de iguais;
   manter iguais os tetos externos. Uma repetição de aquecimento e cinco
   medidas, ordem de métodos alternada por semente. Medir preparação e
   consulta separadas e o total para 1, 16 e 64 consultas, além de memória e
   bitlength. Separar forward, suporte/DAG, compilação e consulta; CUDA
   sincronizada quando houver GPU. Excluir loading somente da métrica por
   passo e informá-lo no custo de reprodução. Não confundir refusas com zero.
9. **Análise previamente escolhida.** Igualdade racional com oráculo é o
   gate de correção. Reportar contagens por status e cobertura sobre todos os
   inputs inscritos, mediana por caso e razões pareadas apenas nos casos
   resolvidos por ambos, sempre junto à cobertura. Mostrar também censura por
   tempo/memória; não converter timeout em um tempo exato. Intervalos de 95%
   por bootstrap pareado de grupos de regras, 2.000 reamostragens, semente
   `20261007`, somente com pelo menos 20 grupos pareados; abaixo disso,
   mostrar resultados por grupo sem um intervalo agregado de bootstrap.
   MC relata erro/incerteza, não igualdade racional. `beta`/TV da §8.1 medem
   informação descartada nesse sorteio, não qualidade do texto ou drift global.
10. **Proveniência e decisões.** Congelar uma config versionada, manifesto
    de inputs e código num commit antes do primeiro timing. JSONL inclui
    commit, hash de config/input/gramática, seed, revisões modelo/tokenizer,
    política/ranking/suporte/exactness_scope, hardware, versões, recursos,
    status e tempos; logits opcionais permanecem separados. Dados brutos
    append-only, produtos derivados por script. Correções que usem avaliação
    tornam esse conjunto desenvolvimento para uma próxima rodada. Preservar
    resultados desfavoráveis e registrar desvios do protocolo.

**Critério científico:** igualdade com WMC competente não demonstra novidade.
Se A1 apenas especializar inferência/ranking conhecidos e não houver resultado
adicional distintivo, rejeitá-lo como protagonista, mesmo com erro mensurável
do controle negativo. Não escolher a contribuição pelo maior speedup observado.
Uma conclusão negativa sobre A1 orienta a pesquisa; não é o resultado novo
positivo que o usuário exige para o TCC. Nenhum timing ou captura foi executado.

### Tarefas posteriores escolhidas: 23–27

- **23 — Executar o protocolo congelado após os gates.** Conferir correção
  antes de desempenho, registrar todos os status e comparar a mesma operação.
  Entregável: JSONL brutos, manifesto e relatório gerado, incluindo derrotas.
- **24 — Demonstrar consumo real de uma regra.** Completar uma regra JsonLogic
  admitida preservando o canvas, executar o resultado no intérprete de revisão
  fixada e mostrar a consulta/auditoria exigida pela contribuição escolhida.
  Sintaxe, execução e decisão semanticamente desejada são critérios distintos.
  Uma regra executável sozinha não comprova necessidade de um algoritmo novo.
- **25 — Fechar revisão e formalização delimitada.** Responder a críticas
  humanas reais, formalizar o resultado distintivo em Lean se apropriado e
  declarar a fronteira entre especificação e implementação. Provas existentes
  não passam a verificar automaticamente um decoder novo.
- **26 — Revisar o artigo sobre o resultado efetivamente aprovado.** Mapear
  cada afirmação a fonte/prova/código/evidência, manter os antecedentes e
  limitações, gerar tabelas e verificar PDF. Sem substituir o protagonista por
  uma hipótese nem transformar superioridade condicionada em promessa geral.
- **27 — Preparar pacote de reprodução e publicação.** Uma reprodução mínima
  offline, config/artefatos pequenos/licenças, limitações e escopo formal claros;
  revisão final, commit/push/CI e candidato de publicação. Escolher veículo
  somente com resultado e orientação; não submeter nem prometer aceite.

Essas tarefas ficam sob T3604–T3605; não criam outra estrutura de código.
Marcos são relativos às dependências, não confirmação das datas institucionais.

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
O usuário confirmou não ter comentários externos. Essa ausência não impede
investigação própria ou rejeição de um candidato fraco; tampouco constitui
parecer favorável. A próxima revisão recebe também o diagnóstico CAR da §8.1
e o protocolo completo da §13. As datas continuam sem confirmação.

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
| 22 | Completado por decisão autorizada: protocolo definido, ainda sem congelamento final/medições. |
| 23–27 | Execução, consumo real, revisão/formalização, artigo e pacote definidos; seus gates continuam pendentes. |
| Publicação | Dossiê/estrutura preparados; artigo central não foi reescrito nem submetido. |

Sem nova implementação principal, novos resultados de modelo,
alteração das tabelas do artigo, revisão humana ou submissão. A falta do
restante do item 22 foi resolvida pela autorização do usuário. Calendário e
parecer permanecem externos; a investigação da novidade permanece nossa
obrigação, não uma aprovação que possa ser inferida desse silêncio.

Follow-up: consulta ao Teorema 3.1 de Grünwald–Halpern e derivação do diagnóstico
TV/KL em §8.1; conferência da documentação JsonLogic e do consumidor fixado;
identificação dos bytes do corpus com `urllib.request.urlopen`/SHA-256, sem
enumerar regras ou executar inferência. O corpo do corpus não foi arquivado.
Uma enumeração analítica independente dos quatro mundos do exemplo, com
`Fraction` e ordenação direta, confirmou `beta=1/4`, `TV=3/4` e razão constante
4 no evento (portanto `KL=log(4)`). Não acrescentou outro teste à suíte nem
constitui benchmark ou prova geral.
Revisão documental e `git diff --check`; nenhuma mudança em código/provas/
artigo exige reapresentar os checks anteriores como evidência nova.
O commit anterior `9ed17c1` teve CI aprovado no run `37642046640`: o log
confirma os 12 testes e 8.016 eventos, além de Rust/artefatos e Lean existentes.

## 14. Continuação substantiva: condicionamento de regras por execução

A orientação posterior do usuário foi trabalhar até obter uma realização útil,
e não apenas criar tarefas. O candidato de likelihood de ações permanece como
diagnóstico conhecido. A direção abaixo tem uma operação diferente, um limite
de custo demonstrável e um protótipo de pesquisa pequeno; não é uma aprovação
humana, declaração de prioridade mundial nem um novo decoder de produção.

### Contrato e aplicação

Entrada: a mesma predição fatorizada congelada `q`, slots/tokens originais,
suporte declarado, canvas e EOS `ABSENT`; uma gramática de regras booleanas
recursivas; `m` registros de campos booleanos; um vetor de resultados desejados.
Saída: massa de cada vetor de execução e amostra original de tokens condicionada
simultaneamente à sintaxe e aos resultados solicitados. O alvo não altera a
gramática, o suporte ou os pesos. Massa zero não é orçamento esgotado.

É preenchimento de uma regra executável a partir de exemplos: filtros,
visibilidade de formulários e condições de habilitação podem usar regras
JsonLogic consumidas diretamente pelo software. A garantia é acertar os
**registros declarados**. Não garante uma intenção não especificada ou acerto
em registros novos. A biblioteca JsonLogic é um consumidor real; uma aplicação
ilustrativa com essa biblioteca não vira automaticamente benchmark externo.

O protótipo admite `{"var":"a"}`, `{"and":[E,E]}`, `{"or":[E,E]}`,
`{"!":[E]}`, sem espaços, campos de uma letra ASCII e valores estritamente
booleanos. Apelidos de campos podem ser explicitamente mapeados pela aplicação.
Não implementa toda a linguagem JsonLogic, coerção numérica, treinamento ou
garantia sobre a trajetória neural. Admite 1–12 registros, com caps explícitos
de entradas e trabalho. A ciência geral não pressupõe que esse limite prático
seja removido silenciosamente. Probabilidades truncadas não são renormalizadas.

### Antecedentes e a diferença delimitada

1. Wang, Dillig e Singh, *Synthesis of Data Completion Scripts using Finite
   Tree Automata* (2017), [§6.1–6.3, Exemplo 6.2 e Teorema 6.3](https://arxiv.org/pdf/1707.01469):
   estados de execução de subprogramas, interseção por exemplos e síntese já
   existem. O exemplo 6.2 já apresenta fórmulas booleanas! Não reivindicamos
   inventar geração semanticamente restrita, FTAs ou parsing com atributos.
   O ranking de §6.3 é distinto da lei ponderada sobre tokens originais, mas
   autômatos ponderados e inferência gramatical já fornecem esse princípio.
2. Björklund, Husfeldt, Kaski e Koivisto, *Fourier meets Möbius* (2007),
   [§2.2 e §2.5, eqs. (7), (8), (15), (17)](https://arxiv.org/pdf/cs/0611101):
   produto de cobertura em `O(m 2^m)` por transformadas é **conhecido**.
   É o produto OR, não a convolução de subconjuntos disjuntos que usa
   `O(m² 2^m)`. Atribuímos o algoritmo aos autores.
3. [FactorDLM §3.1](https://arxiv.org/html/2609.32900v1): fatores e auxiliares
   determinísticos podem codificar execução. Eliminação e amostragem exatas
   são comparadores competentes; não alegamos incapacidade de resolver a
   tarefa. Uma implementação que incorpore o mesmo produto de cobertura
   compartilha nossa vantagem algébrica.
4. [JsonLogic oficial](https://jsonlogic.com/operations.html): `and` e `or`
   retornam operandos, não necessariamente booleanos. No domínio declarado,
   todos os operandos são booleanos e a álgebra coincide exatamente. O
   consumidor foi fixado no commit `c5c73601c90b11e98f6846609bac4dec203d1c18`,
   `logic.js`, 14.844 bytes, SHA-256
   `73a6dc521e8990c2eed330dcfdb35605d7e1065a6e19d26673cb7ad4cd09d881`.
   MIT, Copyright Jeremy Wadhams; permanece cache local, não nova dependência.

O resultado delimitado é um condicionador de **sintaxe e comportamento**,
com interpretação explícita de tokens e uma separação entre planos bilineares
não negativos e planos que usam inversão de Möbius. A busca primária adicional
não encontrou o enunciado exato da rank não negativa abaixo, mas ausência em
busca não prova novidade. A rank é uma consequência de um argumento clássico
de retângulos/fooling sets. Sua prioridade e suficiência acadêmica continuam
pendentes de revisão independente. O limite/correção não dependem dessa
prioridade: são afirmações matemáticas verificáveis com escopo declarado.

### Teorema A2.1 — operação e amostragem

Seja `h(y) ⊆ [m]` o conjunto de registros em que a regra `y` resulta em `true`.
Para cada nó da floresta, guarde `W[S]`, a soma dos pesos dos caminhos cujo
subprograma tem perfil `S`. Terminais de variável têm perfil fixo; pontuação
de sintaxe é escalar. NOT permuta `S` para seu complemento. OR combina

`C[T] = sum_{A union B = T} U[A] V[B]`;

AND é o mesmo produto conjugado por complemento. Nós com uma expressão e
pontuação apenas multiplicam sua distribuição pelo peso escalar. Alternativas
de parsing somam distribuições. A floresta só admite sintaxe LL(1) não ambígua;
aliases são eventos de tokens distintos, fechados pelas arestas originais.

**Prova.** Indução sobre spans estritamente crescentes. Cada derivação válida
tem exatamente um perfil determinado pelos filhos. As alternativas são
disjuntas por caminho original; a multiplicação combina escolhas em spans
disjuntos. Assim, o vetor da raiz é exatamente a partição do conjunto de
completions por execução, sem acrescentar multiplicidade semântica.
Escalas inteiras por posição multiplicam todo caminho pelo mesmo denominador
`D`; a massa final é `W[T]/D`, preservando os pesos do suporte original.

Para amostrar OR condicionado a `T`, defina `V_T[B]=V[B]` se `B⊆T`, zero
caso contrário, e `sup[S]=sum_{B⊇S} V_T[B]` por zeta superior. Escolha `A⊆T`
com peso `U[A] sup[T\A]`; depois escolha `B` com peso `V[B]` entre os que
satisfazem `A∪B=T`. O produto das duas probabilidades é
`U[A] V[B]/C[T]`. AND usa complementos; NOT e pontuação são determinísticos
quanto ao perfil. Escolha alternativas com a massa do perfil solicitado e
aplique a mesma recursão. Os fatores telescopam para
`Pr(Y=y | syntax,h(Y)=T) = prod_i q_i(y_i)/Z_T`.

A implementação tipa os helpers da binarização forçada pela presença de um
filho booleano. AND/OR já têm dois filhos booleanos antes da normalização;
NOT aplica-se ao filho booleano com pontuação escalar; Field tem um terminal
ASCII. Não há regras epsilon ou unit nessa gramática. Logo, a normalização
só cria cadeias e proxies de pontuação; não mistura duas ações semânticas.
Essa restrição é essencial: não estendemos o argumento a normalização
arbitrária com atributos. Os metadados de cabeça/produção na floresta são
inertes para a API posterior anterior.
Quando o produto dos tamanhos dos suportes positivos dos filhos é no máximo
`2^m`, a implementação enumera só esses pares, também na amostragem. Caso
contrário usa as transformadas. Essa seleção é conhecida e preserva as mesmas
somas; ignorar pesos zero na consulta não remove caminhos da floresta compilada
nem impede reponderação futura. O custo continua `O(m 2^m)` e há no máximo
`2^m` produtos bilineares por join. A adaptação não pertence à classe de planos
fixos não negativos do lower bound.

### Teorema A2.2 — comparação competente, não uma codificação ruim

Considere o mapa **completo** de perfis de OR, para vetores não negativos
arbitrários de dimensão `2^m`. Um plano bilinear não negativo de `r` produtos
tem a forma

`C[T] = sum_j w[j,T] (sum_A u[j,A] U[A]) (sum_B v[j,B] V[B])`,

com todos os coeficientes não negativos. Então o menor `r` é exatamente
`3^m`. Permitindo coeficientes de qualquer sinal, o menor `r` é `2^m`.
São multiplicações **bilineares entre as duas entradas**, não todo custo
de software, coeficientes constantes, memória ou tempo físico.

**Limite inferior não negativo.** Cada produto induz um retângulo de suporte
`L_j × R_j × O_j`. Como não há cancelamento e cada monômio `U[A]V[B]`
aparece em apenas `C[A∪B]`, um retângulo útil só pode contribuir ao seu
único perfil de saída. Para cada `T` considere as `2^|T|` testemunhas
`(A,T\A,T)`, `A⊆T`. Um retângulo que contém duas testemunhas com o mesmo
`T` também contém os dois cruzamentos. Eles teriam que satisfazer
`A∪(T\A')=T` e `A'∪(T\A)=T`, implicando `A'⊆A` e `A⊆A'`: são a mesma
testemunha. Saídas diferentes também não compartilham um retângulo útil.
Logo precisa de pelo menos `sum_T 2^|T|=3^m` produtos. Equivalentemente,
cada coordenada da testemunha está em `00`, `01` ou `10`.

**Limite superior não negativo.** Para cada `T` e `A⊆T` multiplique
`U[A]` por `sum_{B⊆T, B⊇T\A} V[B]` e some no respectivo `T`.
Há exatamente `3^m` produtos. Existe também um controle recursivo competente:
particione pela última coordenada; compute
`C0=join(U0,V0)` e
`C1=join(U1,V0+V1)+join(U0,V1)`.
São `3^m` produtos e `2(3^m−2^m)` adições, sem tabela densa `4^m`.
Assim, o adversário do teorema já é ótimo na classe declarada.

**Caso com sinais.** Zeta, produto pontual e inversão de Möbius realizam o
mapa com `2^m` produtos e `3m 2^(m−1)` adições/subtrações. Os polinômios
`C[T]` são linearmente independentes: o monômio `U[T]V[∅]` ocorre só no
polinômio de saída `T`. Toda realização bilinear com `r` produtos gera um
espaço de dimensão no máximo `r`. Logo `r≥2^m`, atingido pelo algoritmo
conhecido. AND herda os limites por permutação de complementos.

**Fronteiras.** Não é um lower bound de toda inferência, de uma só massa
alvo, de programas com divisão/branching dependente das entradas, circuitos
que exploram esparsidade específica, ou toda representação por fatores.
Não diz que o FactorDLM precisa materializar esse join, nem que todo input
real atinge o pior caso. Não é superioridade sobre EPIC em latência neural:
EPIC com um executor/reparador resolve outra estratégia; rejeição a partir
do mesmo posterior sintático também resolve a operação de amostragem,
com custo esperado `1/Pr(h(Y)=T | syntax)` tentativas (quando positivo).

### Custo total e em bits

Sejam `F` as alternativas/nós da floresta sintática já compilada, `S` o
tamanho do suporte e `B` o custo limitado da preparação gramatical/token-DAG.
A avaliação semântica custa `B + O(S+F m 2^m)` operações aritméticas e
`O(F 2^m)` entradas de memória. A implementação também chama o posterior
escalar em `O(F+S)` para validar as restrições/alinhamento e conferir que os
perfis particionam exatamente a massa sintática; esse custo não é omitido.
Uma amostra recalcule contribuições em nós visitados e usa zeta superior
para pares: custa no máximo `O(F m 2^m)`, não tempo constante. Há caps de
entradas e trabalho cooperativo antes de expansão; não há promessa de hard
timeout para uma multiplicação de inteiros arbitrariamente grandes.

Se `L` limita os bits dos pesos/massas de spans (limitável pelos bits dos
pesos por posição, número de caminhos do DAG e univocidade da gramática),
as transformadas somam até `2^m` valores, o produto dobra os bits e a
inversão acrescenta no máximo `m` bits. Intermediários têm `O(L+m)` bits.
Cada join custa `O(m 2^m (L+m) + 2^m M(L+m))` em bits, para custo de
multiplicação `M`; custos de conversão racional, `lcm`, leitura e escrita
também existem. A redução de multiplicações não elimina esses custos nem
prova menor tempo para qualquer `m`. O método é exponencial no número de
registros, linear/polinomial no tamanho explícito da floresta com `m` fixo.

### Evidência de pesquisa e revisão que permanece necessária

O algoritmo está em `scripts/exact_commit/semantic_json.py`; não foi ligado
ao decoder de produção. `tests/test_semantic_json.py` usa `json.loads` e
avaliação recursiva independente, produtos exaustivos de tokens, pesos
reduzidos/zero, commitments, aliases, recusas por orçamento e enumeração
de todas as decisões aleatórias de um caso pequeno. O núcleo de OR foi
confrontado com pares enumerados para `m=0..7`, seed `20261007`; a lei
condicional dos pares foi calculada por todas as decisões inteiras, não
frequências. São verificações de correção, não benchmarks favoráveis.

`formal/MWPC/SemanticProfiles.lean` mecaniza a separação de testemunhas,
a lista ternária distinta de cardinalidade `3^m` e o lower bound de cobertura
por retângulos, além de reduzir diretamente planos de coeficientes naturais
com escala positiva comum a essa cobertura. A rota é sobre o subtipo **finito** de testemunhas enumeradas;
não exige cobrir listas de todos os comprimentos com uma família finita,
o que tornaria a hipótese impossível. O caso racional usa limpeza de
denominadores na prova escrita; a redução dos coeficientes reais a
retângulos, optimalidade com sinais, distribuição de amostragem e compilador
Python permanecem provas escritas/obrigações; Lean não verificou o software
inteiro. O audit usa o checker do kernel, sem novas admissões.

`configs/experiments/m36_semantic_reference_v1.json` foi definido antes de
uma captura. Ele fixa dois alvos positivos e paridade não representável nesse
canvas, oito registros, 108 regras na mesma sintaxe, lexical domains
independentes dos alvos, modelo/tokenizer via config M31 e consumidor oficial.
É uma demonstração declaradamente ilustrativa de execução, não o protocolo
externo de §13 ou uma comparação de desempenho. Ainda é necessário obter
parecer humano e verificar prioridade bibliográfica para promover o recorte
a protagonista publicado. A realização concreta e a matemática não dependem
de inventar esse parecer.

### Captura concluída e utilidade demonstrada

O commit limpo `2be61a9773a016930dc407ab051d6f2d497704a0` produziu a captura
real de MDLM em `docs/artifacts/raw/m36_semantic_reference_v1/`. Os logits
completos foram verificados localmente por softmax NumPy independente; o Git
contém os pesos racionais declarados, hashes e todas as saídas, não o checkpoint
ou o NPZ local. O consumidor oficial executou todas as 108 regras nos oito
registros. As duas metas positivas produziram dezesseis amostras cada; paridade
permaneceu massa zero nesse canvas. Não foram descartadas saídas desfavoráveis.

Uma recomputação sem modelo/rede reproduz as massas arquivadas e as confronta
com a enumeração completa por JSON/executor independente. Esse caminho passa
a integrar o CI. A soma dos perfis de **cada célula** é agora comparada com
sua massa sintática antes da normalização final; uma perda/duplicação não pode
ser escondida por renormalização. Isso não equivale a uma prova do código.

`docs/research/generated/m36-semantic-summary.md` é gerado pelo replayer e
mostra probabilidades condicionadas à sintaxe e `Z_syntax/Z_target`. A segunda
quantidade é o número esperado de tentativas de **rejeição independente com
a mesma lei**, uma identidade geométrica, não um tempo medido nem o EPIC
nativo. Para massa positiva, rejeição é correta e termina quase certamente,
mas não tem limite determinístico de tentativas; para massa zero nunca aceita.
O condicionador, quando cabe nos caps declarados, decide essa impossibilidade
e oferece amostragem sem tentativas de rejeição. Outros inferidores exatos
competentes podem compartilhar essa capacidade.

Essa aplicação demonstrou regras executáveis e exatidão no suporte; não
estabeleceu o recorte de teste externo de §13, desempenho de todo decoder,
qualidade semântica aprendida ou prioridade científica. A contribuição
matemática é o enunciado delimitado A2.2 com seu comparador ótimo na classe,
e sua utilidade está ligada à operação especificada A2.1. A avaliação humana
da originalidade/suficiência acadêmica permanece T3603, sem aprovação criada.
## 16. Continuação de 8 de outubro: refinamento e núcleo semântico certificado

O pedido para não parar foi retomado como investigação e implementação, não
como mera abertura de tarefas. A transformação anterior continua atribuída
aos antecedentes. O novo recorte é uma operação de inferência que admite
requisitos de execução não expressos por prefixos e mudanças posteriores dos
pesos de uma dLLM, preservando todas as conclusões válidas no suporte original.
Serial, EPIC e MWPC de produção permanecem separados.

### Antecedentes que eliminaram falsas novidades

- [CARS, versão 2 de 2/6/2026](https://arxiv.org/html/2510.01902v2), algoritmo 1,
  equações 1–3, teorema 3.2 e apêndice E: já preserva a distribuição ao remover
  prefixes comprovadamente inválidos. O teorema R1 não inventa esse princípio.
  A implementação descrita mantém uma trie e pode continuar rejeitando quando
  não registra todas as classes de prefixos. Seu oracle perfeito foi concedido
  ao controle desta investigação, não artificialmente enfraquecido.
- [Denise e Zimmermann, 1999](https://doi.org/10.1016/S0304-3975(98)00323-5),
  relatório INRIA 3242, seção 4, proposição 4.2 e teorema 4.3: a geração ADZ
  já usa intervalos certificados e conserva o número aleatório ao aumentar a
  precisão. O texto menciona explicitamente dobrar a mantissa. Essa direção
  foi descartada como novidade baseada apenas em precisão adaptativa.
- [Björklund e coautores, Fast Zeta Transforms for Lattices with Few
  Irreducibles](https://thorehusfeldt.com/wp-content/uploads/2010/08/7c52e3293a74298f.pdf),
  equações 1.1–1.3 e teoremas 1.1–1.3: o produto em reticulados e a compressão
  por cadeias também são antecedentes; não bastam para reivindicar novo método.
- [Jha, Gulwani, Seshia e Tiwari, ICSE 2010](https://www.csl.sri.com/users/tiwari/papers/icse2010.pdf),
  seção 5: seleção de exemplos, teaching dimension e cobertura já são conhecidos.
  O núcleo suficiente aqui não é apresentado como invenção desses conceitos.

### Contrato e resultados escritos

Fixar gramática LL(1), tokens originais, probabilidades racionais por posição,
slots físicos e EOS ausente. Os exemplos e suas respostas não alteram a sintaxe,
o suporte ou os pesos. Cada conclusão deve preservar o canvas comprometido.
Mudanças de modelo são novas consultas locais, não uma inferência exata da
trajetória inteira. Zero massa, zero soluções estruturais e recusa de recursos
são afirmações distintas. A exatidão continua `exact_on_support`.

**R1 — Fluxo exato com orçamento finito de rejeições.** Amostrar condicionado
apenas nos exemplos ativos; verificar o candidato contra todos os exemplos;
se falhar, adicionar um exemplo violado. A distribuição de cada saída aceita
é o produto original condicionado em todos os exemplos. As saídas são iid,
embora os conjuntos ativos sejam adaptativos. Um lote de N saídas rejeita no
máximo m candidatos, para m requisitos, desde que as avaliações necessárias
caibam nos recursos. A prova por indução em requisitos ainda inativos está
no suplemento. Os pesos e o prompt permanecem fixos após cada falha.

**R2 — Separação de representação, não um benchmark.** N escolhas de `!`/`!!`
envolvendo uma variável codificam paridade em JsonLogic. Nenhum prefixo próprio
determina a resposta. Para uma proposta sem qualquer rejeição, exclusões de
prefixo precisam distinguir pelo menos `2^(n-1)` escolhas inválidas. Isso vale
com oracle perfeito. Um perfil de execução de um exemplo tem dois estados;
uma rejeição ativa o exemplo e elimina toda a classe inválida. O compilador
CFG permanece polinomial em n. A rejeição simples de paridade balanceada usa
apenas duas tentativas em média; portanto esse resultado não promete ganho de
latência para a primeira amostra. Um DFA de paridade com dois estados ou outro
solver semântico compacto compartilha a vantagem. A comparação não é exclusiva.

**R3 — Certificado independente dos pesos.** Para um conjunto ativo A, contar
separadamente as conclusões que satisfazem A e violam cada exemplo omitido i.
Usar pesos auxiliares estritamente positivos em todo o suporte, inclusive nos
tokens cuja probabilidade atual é zero. Se todos os contadores forem zero,
então satisfazer A equivale a satisfazer todos os exemplos, para cada caminho
de tokens representado. A equivalência preserva massa e amostragem para
quaisquer pesos posteriores e sobre contrações do suporte/novos commitments.
Expansão de suporte, desfazer commitments ou mudar exemplos exige recertificar.
Certificar com os pesos do modelo, que podem ter zeros, seria incorreto.

O compilador escolhe a maior contagem de violações, com desempate por índice,
e verifica cada obrigação com `|A|+1` dimensões, sem construir a distribuição
conjunta dos exemplos omitidos. Encontra um núcleo suficiente, não mínimo.
Um núcleo sugerido também precisa ser verificado. Um domínio ativo vazio
certifica impossibilidade estrutural; um limite esgotado continua não resolvido.
O tamanho ativo permanece limitado a onze para deixar uma dimensão de prova.

### Uso e custo que justificam a operação

O usuário de um gerador de filtros/regras pode declarar muitos exemplos,
certificar uma vez um núcleo e então amostrar regras válidas sob novas
probabilidades da dLLM. Os pesos auxiliares são usados apenas na certificação;
as amostras conservam os pesos reais do modelo e os aliases de tokens.

Há famílias com exemplos distintos e núcleo pequeno: regras monotônicas são
determinadas nos exemplos pelas fronteiras positivas mínimas e negativas
máximas. Para o comportamento `f(x)=x_a` no cubo Booleano de d campos, dois
exemplos de fronteira implicam os `2^d` exemplos. A gramática permanece genérica
e fórmulas diferentes, como `a and a` e `a or a`, continuam saídas distintas.
Isso é consequência conhecida de monotonicidade. O compilador não supõe que
a gramática inteira seja monotônica: ele verifica cada implicação no suporte.

Com F alternativas/células, S suporte, g gramática e núcleo final k, a
certificação custa `O(m(k+1)(g+S+F)+Fm(k+1)2^k)` operações e usa no máximo
`O(F2^(k+1)+md)` entradas/dados. Cada nova consulta usa
`O(g+S+F max(1,k2^k))`. Para T consultas, somar a preparação mais todas as T
avaliações. Os custos em bits dos inteiros/racionais também são necessários.
Comparado ao backend denso atual, a dimensão de perfil por consulta cai de
`2^m` para `2^k`. Isso não é lower bound para todo solver competente de um alvo.
Núcleo grande ou poucas consultas podem tornar a certificação mais cara.

### Verificação e protocolo antes das medidas

`scripts/exact_commit/adaptive_semantics.py` materializa R1 e R3. O limite de
trabalho para amostrar é reservado para toda a derivação CNF antes do sorteio;
uma recusa dependente do caminho escolhido poderia introduzir viés. As recusas
de refinamento ocorrem entre candidatos completos e encerram a sessão.
Não há promessa de preempção dura de uma multiplicação inteira.

Seis oráculos novos verificam a lei conjunta de duas saídas por toda a árvore
de decisões (consolidando intervalos categóricos após verificar todos os
sorteios inteiros do helper), a lei ponderada do controle de prefixos, a
família `!`/`!!`, recusas/snapshots, todos os alvos pequenos e certificados sob
novos pesos, inclusive tokens inicialmente zerados. Enumeradores independentes
executam árvores JSON, sem usar o parser/normalizador como reconhecedor.
Lean mecaniza dezesseis resultados selecionados de progresso, prefixos e
núcleos; lei iid completa, construção CFG e código Python não estão refinados
em Lean. Revisão humana e prioridade científica não são inferidas desses checks.

O protocolo `configs/experiments/m36_adaptive_semantics_v1.json` foi definido
antes de executar a auditoria. Usa a captura MDLM já existente e TODOS os 256
vetores de respostas, com três sementes e quatro amostras por alvo positivo.
São cinco métodos: fluxo adaptativo, posterior exato ávido compartilhado,
enumeração compartilhada, controle de trie do algoritmo CARS com oracle
perfeito por enumeração, e núcleo estrutural certificado. Preparação e consulta
são separadas; cada núcleo é preparado uma vez por alvo e reutilizado nas
sementes. Nenhum dado externo novo ou subconjunto de vitórias é inventado.
A captura é desenvolvimento, não um benchmark externo/held-out. O controle
de prefixos não mede velocidade do CARS nativo; EPIC nativo tampouco é executado.

### Auditoria concluída, incluindo os custos desfavoráveis

O commit limpo `30e6ac38aac69ddc0e9ccad6c0ac06d36016fa9c` produziu
`docs/artifacts/raw/m36_adaptive_semantics_v1/` com o comando registrado em
REPRODUCING.md. Todos os 256 alvos e três sementes foram executados: 768 linhas,
108 programas originais, 17 alvos de massa positiva. Os cinco métodos resolvem
51 linhas positivas e 717 negativas, sem recusas. A enumeração independente
recalcula massas, executa todas as amostras e verifica equivalência de todos os
núcleos contra **todos** os caminhos, não apenas os amostrados.

`docs/research/generated/m36-adaptive-summary.md` e a tabela LaTeX são gerados
pelo replayer. Enumeração é o controle mais rápido neste suporte pequeno. O
lote mediano do núcleo é mais barato que o do posterior completo, mas sua
certificação e avaliação total custam mais, inclusive quando compartilhadas
entre sementes. A hipótese de amortização em várias novas predições continua
uma condição matemática, não um ganho de trajetória já medido. Nenhum resultado
desfavorável foi omitido. O máximo de rejeições adaptativas foi sete, sob o
limite de oito requisitos. A origem dos logits é a captura anterior; não houve
novo forward de modelo.

Uma verificação de capacidade separada usa os 64 registros **distintos** de
seis campos e todas as 72 conclusões de um canvas AND/OR genérico. Duas
exigências de fronteira certificadas implicam todos os registros; os dois
programas restantes são enumerados independentemente. O posterior ávido recusa
64 registros pelo seu cap de doze; o núcleo usa três dimensões por prova e duas
por consulta. Isso é um corolário de correção/capacidade, sem medidas de tempo
ou pretensão de derrotar todo algoritmo semântico competente. O caso não é
usado como benchmark científico favorável.

CI acrescenta uma recomputação corrente dos primeiros alvos positivo e zero,
com massas e amostras determinísticas do fluxo adaptativo e do núcleo.
O trie de identificadores admite nomes ASCII reais e prefixos compartilhados,
como `active`/`active_admin`, inclusive quando os tokens cortam o nome. Não
resta a restrição artificial de campos de uma letra; caminhos pontuados e tipos
não Booleanos continuam fora do contrato. A construção tradicional por trie
não é reivindicada como novidade e preserva a identidade da gramática arquivada.
Um oráculo independente adicional verifica massas/comportamentos desses nomes.
### C1: uma vantagem comparativa em rejeições, não apenas representação

A leitura novamente do original CARS v2 confirmou o update publicado em §3,
``Updating W``: depois de cada candidato, adicionar todos os continuadores
inválidos dos prefixos visitados, inclusive quando o candidato foi válido.
Algoritmo 1, equações 1–3 e **Teorema 3.2**, não 3.1, são os locadores
corretos dessa versão. O controle implementa esse update com oracle perfeito.

Na família R2 com escolhas uniformes, há L=2^(n−1) grupos. Cada grupo contém
uma regra válida e uma inválida com o mesmo prefixo de n−1 escolhas. A primeira
visita falha com probabilidade 1/2; o update elimina a única regra inválida desse
grupo, sem eliminar nenhum outro grupo. Depois, o grupo nunca mais rejeita.

Se U_N é o número de grupos visitados até a N-ésima saída, somar expectativas
condicionais antes dos sorteios dá E[R_N]=E[U_N]/2. O tempo de parada é limitado
por N+L candidatos, portanto não há troca informal de uma parada não limitada.
As saídas válidas do CARS são iid uniformes nos L grupos; elas visitam em média
L(1−(1−1/L)^N) grupos distintos, número no máximo U_N. Assim:

    E[R_N] >= L/2 * (1 - (1 - 1/L)**N).

Isso cresce como Omega(min(N,L)); no fluxo infinito a expectativa total é
L/2. Nosso refinamento usa no máximo uma rejeição nessa mesma tarefa/law,
com preparação polinomial, e sua expectativa até N saídas é 1−2^(−N).
Para pesos positivos não uniformes, a mesma prova dá
E[R_N] >= alpha * sum_g(1−(1−pi_g)^N), com pi_g a lei dos programas válidos
e alpha a menor probabilidade relativa das duas escolhas da última posição.
Uma distribuição muito concentrada enfraquece o ganho finito; não é omitida
essa hipótese. O orçamento de uma rejeição do refinamento independe dela.

O resultado é **uma análise comparativa delimitada de um algoritmo publicado**,
não uma reivindicação de novo princípio de amostragem. Não mede wall time e
não impede um automato semântico de dois estados de compartilhar a vantagem.
Pré-carregar todos os prefixos inválidos transfere trabalho exponencial para
a preparação; uma mudança na regra de update requer outra comparação.
O caso não é um benchmark com dados escolhidos: o ganho segue do argumento
para todos os n e N admitidos e recursos suficientes para o compilador.

O novo oráculo enumera todas as decisões categóricas do controle, incluindo
rejeições, e compara expectativas racionais a uma recursão Markov independente
sobre grupos visitados. Cobre casos uniformes e pesos desiguais, incluindo
um lote em que o lower bound já supera o orçamento total do refinamento.
Também verifica um ramo de probabilidade positiva com L rejeições antes da
primeira saída. Isso procura erros na derivação, não mede superioridade empírica.
A prova de expectativa C1 é escrita; não é atribuída às 66 provas Lean.

Buscas direcionadas por CARS/parity, counterexample/exact sampling/program
synthesis e counterexample-guided rejection sampling não localizaram a mesma
fórmula no antecedente principal. Ausência em buscas não prova prioridade.
O alcance próprio é construção/implementação para tokens de dLLM e essa
comparação explícita; métodos clássicos compactos continuam antecedentes e
controles competentes. Revisão humana real continua separada.

O artigo principal e sua avaliação histórica continuam
preservados; o suplemento contém as novas provas e seus limites. A novidade
defensável é o recorte operacional/implementação de certificação e inferência
semântica reutilizável em tokens de uma dLLM; prioridade teórica exclusiva e
superioridade universal não estão estabelecidas. T3603 segue sem comentários
reais do orientador. Isso não impede continuar as obrigações técnicas autorizadas.
