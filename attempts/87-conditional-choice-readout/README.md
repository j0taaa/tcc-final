# A87 — Consistência e consultas para escolhas com vários tokens

Estado: **resultado teórico candidato; nenhum tema central ou experimento
neural selecionado**. Esta tentativa não reabre A65, A69 ou A86. O consumidor
proposto é classificação por alternativas textuais, incluindo rótulos com
vários tokens; não é previsão da saída terminal de um decoder.

## Operação e hipótese que não pode ficar implícita

Sejam `K >= 2` alternativas distintas, codificadas por palavras de comprimento
comum `L` em IDs originais. Comprimentos diferentes exigem uma convenção
explícita de EOS/PAD. Para esta análise finita, cada alternativa tem exatamente
uma codificação; aliases exigem outra análise, não renormalização silenciosa.

O oráculo teórico recebe posições fixadas e devolve todas as marginais de uma
mesma distribuição `pi` **já apoiada nessas alternativas**. Um forward nativo
de LLaDA não fornece esse contrato automaticamente. Coerência das condicionais,
massa fora das alternativas e erro de previsão são problemas separados.

A operação desejada é identificar a alternativa mais provável, ou suas massas,
usando menos forwards que avaliar separadamente todos os preenchimentos.
As equações abaixo se referem ao oráculo declarado, não à lei produto congelada
da biblioteca nem à trajetória nativa do modelo.

## Antecedentes e diferença ainda em investigação

- [Mosaic](https://arxiv.org/html/2607.07026v1) e
  [FactorDLM, §3.1](https://arxiv.org/html/2609.32900v1#S3.SS1)
  condicionam exatamente o produto das cabeças ao suporte. Essa operação não
  pretende reconstruir o posterior verdadeiro das classes.
- [Allwein, Schapire e Singer, §3](https://www.jmlr.org/papers/volume1/allwein00a/allwein00a.pdf)
  já descrevem decoding por log-loss/produto em códigos de saída.
- [Ramaswamy et al., Teorema 6 e Corolário 7](https://proceedings.mlr.press/v35/ramaswamy14.pdf)
  já recuperam probabilidades de classe por inversão de uma matriz de códigos.
  **Inversão linear, seu critério de posto e ECOC não são contribuições nossas.**
- A independência das colunas de uma matriz de incidência de transporte quando
  o suporte é uma floresta é clássica; ver
  [Fu Liu, §3.1](https://dmtcs.episciences.org/3097/pdf).
- Simetria e concavidade já fornecem a direção suficiente por princípios de
  Schur–Ostrowski; ver [Resin, §4](https://www.jmlr.org/papers/volume24/23-0106/23-0106.pdf).
  A necessidade específica para essa família de produtos é a parte candidata.
- [PET multitoken](https://arxiv.org/pdf/2009.07118) usa preenchimento iterativo;
  o [dJev](https://github.com/mmastrac/djev) documenta rótulos de um token.

Não localizamos nas fontes acima o critério combinatório exato da seção
seguinte, nem a operação de consultas agrupadas com ótimo FVS descrita abaixo.
Isso delimita duas reivindicações candidatas, **não comprova prioridade mundial**.
A combinação direta de dLLM com ECOC conhecido seria um controle, insuficiente
para selecionar o tema central solicitado.

## Quando o produto preserva a alternativa mais provável

Cada posição induz uma partição das classes: um bloco contém as classes que
usam o mesmo ID naquela posição. Para um subconjunto não vazio `B` das classes,
seja `m(B)` a quantidade de vezes que ele aparece como bloco. Blocos universais
são irrelevantes. Com marginais ideais, o score produto da classe `c` é

\[
 S_c(\pi)=\prod_{B\ni c}\pi(B)^{m(B)},\qquad
 \pi(B)=\sum_{j\in B}\pi_j.
\]

**Teorema candidato.** Para alternativas distintas, o conjunto de máximos de
`S(pi)` coincide com o de `pi`, para todo posterior estritamente positivo, se e
somente se `m(B)` depende apenas de `|B|` para todos os subconjuntos próprios
não vazios. Essa condição também preserva toda a ordenação no interior.

**Suficiência.** Para duas classes `a,b`, cancelam-se os blocos que contêm
ambas. Escrevendo `m(B)=r_|B|`, o quociente restante é

\[
 \frac{S_a}{S_b}=
 \prod_{T\subseteq[K]\setminus\{a,b\}}
 \left(\frac{\pi_a+\pi(T)}{\pi_b+\pi(T)}\right)^{r_{|T|+1}}.
\]

Todos os fatores com expoente positivo apontam na direção de `pi_a-pi_b`.
Como as palavras são distintas, existe posição que distingue `a,b`; portanto
há pelo menos um desses fatores. O quociente é maior, igual ou menor que um
conforme a comparação entre as probabilidades.

**Necessidade.** Fixe `a,b` e considere o aberto relativo onde
`pi_a=pi_b` e ambas superam as outras classes. Preservar o conjunto MAP exige
`S_a=S_b`. Os scores são polinômios homogêneos de mesmo grau; a identidade
vale no hiperplano positivo correspondente, após remover a normalização.
Depois de cancelar os blocos comuns e substituir `pi_a=pi_b=t`, os fatores
restantes são formas `t+sum_{j in T} pi_j`. São formas lineares distintas e
não proporcionais, todas com coeficiente de `t` igual a um. Unicidade da
fatoração força

\[
 m(\{a\}\cup T)=m(\{b\}\cup T)
 \quad(T\subseteq[K]\setminus\{a,b\}).
\]

Trocas de um elemento conectam quaisquer subconjuntos de mesmo tamanho.
Para `K=2`, as duas multiplicidades singleton são iguais por construção e
o resultado também segue diretamente do quociente dos scores.

O teste não precisa enumerar `2^K` subconjuntos. Há no máximo `LK` blocos
observados: para cada tamanho `s` observado, devem aparecer exatamente
`binom(K,s)` blocos distintos, todos com a mesma multiplicidade.

O teste também permite gerar uma testemunha racional de falha. Escolha um par
com multiplicidades diferentes sob troca. No hiperplano de empate, a diferença
de scores é um polinômio não nulo de grau no máximo `L`. Fixe os pesos do par
em `2L+1` e sorteie os outros de `{1,...,2L}`. Por Schwartz–Zippel, a diferença
é não nula com probabilidade pelo menos `1/2` em cada sorteio ideal independente.
Seja `U` a soma desses pesos. Aumentar o peso da classe com menor score em
`epsilon=1/[4L(U+1)^L]` a torna o único MAP verdadeiro e preserva a desigualdade
contrária dos scores: a diferença inicial é um inteiro de módulo pelo menos
um, e sua derivada tem módulo no máximo `2L(U+1)^(L-1)` no segmento.
Normalizar os pesos não muda nenhuma comparação. O código limita a busca
aleatória e preserva uma eventual recusa como inconclusiva.

**Falha concreta.** Para códigos `00,01,10` e probabilidades `(.3,.4,.3)`,
o produto dá scores `(.42,.28,.18)` e escolhe a classe errada, mesmo com as
marginais ideais. O problema não é só calibrar a confiança.

**Equidistância não basta.** Um código de cinco classes e 16 posições pode ter
todas as distâncias de Hamming iguais a oito e violar a condição acima. O
oráculo constrói o exemplo a partir dos 15 cortes binários distintos: agrupa
as classes em `A={a,e}, B={b}, C={c}, D={d}`, duplica os quatro cortes de um
grupo contra os demais e remove os três cortes `AB|CD, AC|BD, AD|BC`.
Essa troca preserva todas as distâncias. Para
`pi=(.249,.251,.2,.15,.15)`, o score de `a` supera o de `b`.

## Consultas condicionais: caso de duas posições

Represente alternativas de dois tokens por arestas de um grafo bipartido;
os vértices de cada lado são os IDs da respectiva posição. Sob o contrato
apoiado no codebook, a consulta raiz devolve as somas dos pesos nos vértices.
Consultar `X_1=a` revela todos os pesos incidentes a `a`, multiplicando as
condicionais de `X_2` pela massa de `a` conhecida na raiz; vale o simétrico.

Depois de consultar vértices `Q`, os pesos restantes são unicamente
determinados, para todo posterior interior, se e somente se o grafo residual
sem `Q` é uma floresta. Em uma floresta, subtrações a partir das folhas
reconstroem os pesos. Um ciclo residual admite uma perturbação alternante
`+epsilon,-epsilon`, preservando as observações. Logo, o menor número de
consultas adicionais nesse modelo é o tamanho de um feedback vertex set.

O fato floresta/ciclo é anterior; a reivindicação candidata diz respeito ao
**modelo de consultas por todas as arestas de um vértice**, com custo por
consulta, e à sua realização em um readout. Não é um algoritmo novo para FVS.
Para reconstrução inteira, adaptação aos valores não evita esse limite no
interior. Uma parada antecipada para MAP poderia custar menos, mas falta um
método próprio e sua análise. A inversão ECOC permanece controle obrigatório.

## Objeção neural explícita e benefício que ainda falta

Mesmo condicionais perfeitas de uma lei global arbitrária não bastam. Se
`G={000,111}` e `P(000)=.30, P(111)=.29, P(110)=.41`, as marginais da raiz
produzem scores `.0639` e `.1421`. Escolhem `111`, enquanto o MAP de `P(.|G)`
é `000`. O código passa no critério combinatório. Renormalizar pelos tokens
que aparecem nas alternativas não elimina essa massa externa.

Assim, as provas não certificam acerto, calibração ou vantagem das cabeças
nativas. Um método útil precisa lidar com esse desvio explicitamente e ganhar
frente a controles competentes no mesmo orçamento. Não se justifica uma
campanha apenas porque a inversão ou um exemplo de oráculo funciona.

Controles necessários: dJev com IDs de um token e legenda; first/max/mean de
verbalizers; produto condicionado; inversão/coupling ECOC competente; avaliação
condicional por trie, incluindo o reaproveitamento de massas conhecidas; e
decoding nativo por confiança. Contabilizar compilação do codebook, rank,
solver/planejador, cada forward, projeção de vocabulário, memória e saída.
Nenhum ganho contra um produto inconsistente basta se ECOC resolve o caso
com o mesmo custo e a parte própria do método não contribui.

## Protocolo CPU V1, a congelar antes da execução

Este protocolo verifica a teoria candidata, não mede qualidade ou velocidade
de modelo. Executar `oracles.py --audit` somente após o commit produtor:

1. Gerar codebooks por multiconjuntos de partições de `K=2,3,4` classes e
   `L=1,2,3` posições, removendo palavras não distintas. Nos casos balanceados,
   conferir a ordenação para pesos inteiros positivos em `{1,2,3,4}^K`.
2. Nos desbalanceados, produzir e validar uma testemunha racional de MAP
   incorreto. Usar no máximo 128 sorteios, seed fixa zero; recusa preservada.
3. Conferir os exemplos de três classes, de cinco classes equidistantes e
   da massa externa descritos acima.
4. Para os 512 grafos bipartidos em `3 x 3` e seus 64 conjuntos de vértices
   consultados, comparar posto das observações lineares com a condição de
   floresta residual: 32.768 combinações, incluindo suporte vazio.

Uma auditoria finita não substitui a prova e não estabelece novidade. Não há
download de dados de avaliação nem uso de GPU neste protocolo.

## Resultado CPU V1 e auditoria posterior

Fonte e protocolo congelados em `a84d19db`. Comando:

```bash
.venv/bin/python attempts/87-conditional-choice-readout/oracles.py --audit
```

Resultado: `PASS`; 20 codebooks balanceados, 2.336 posteriors com ordenação
conferida, 586 codebooks desbalanceados e 586 testemunhas racionais de MAP
incorreto, usando 598 sorteios no total e nenhuma recusa. Outros 273 codebooks
foram excluídos porque não distinguem as classes, conforme o protocolo.
Passaram as 32.768 combinações de grafo/consultas e os três exemplos nomeados.
Isso verifica os casos enumerados, sem evidência neural, timing de decoder
ou certificação da hipótese de oráculo.

Um controle anterior adicional é especialmente pertinente:
[James e Hastie, NIPS 1997, Teorema 1](https://proceedings.neurips.cc/paper_files/paper/1997/file/4e8412ad48562e3c9934f45c3e144d48-Paper.pdf)
caracteriza Bayes-optimalidade do decoding **L1**, equivalente à perda esperada
de Hamming, por equidistância dos códigos binários. Não é a operação produto
do nosso teorema: o contraexemplo binário equidistante de cinco classes separa
as duas condições. Entretanto, esse antecedente fornece uma correção conhecida
que deve integrar os controles. Trocar produto por risco de Hamming ou por
inversão conhecida não estabelece um método próprio.

**Decisão:** preservar o resultado teórico; continuar a busca pelo método.
Nenhuma campanha de classificação, avaliação de modelo ou tema central foi
aprovado por esse resultado. A lacuna operacional é obter melhoria própria
lidando explicitamente com massa externa e condicionais nativas incompatíveis.
