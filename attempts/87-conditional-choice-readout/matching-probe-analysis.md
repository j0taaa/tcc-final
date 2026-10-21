# A87 — auditar somente alvos não casados

Nova operação algorítmica, separada das fontes, protocolos e dados congelados
de `online_probe.py`, `multiple_probe.py` e da captura neural V1. Esta nota
contém uma prova escrita e um protocolo CPU ainda não executado. Não estabelece
prioridade científica, ganho neural nem seleção do tema central do TCC.

## 1. Operação e hipóteses

Seja H=(V,E) um grafo bipartido finito, público. Consultar um vértice custa uma
unidade e revela uma resposta determinística. A instância real, fixa antes do
sorteio, define M⊆V. Exigimos:

1. Q é certificado se, e somente se, contém M e é vertex cover de H.
2. A previsão fixa Mhat e, para cada p∈Mhat, uma testemunha selecionada
   u(p)∈N_H(p). Consultar u(p) permite testar p; aprovação implica p∈M.
3. Depois de consultar qualquer cover C, somente vértices ainda ausentes de M
   podem ser necessários para concluir. A resposta final é validada com os
   resultados reais; a previsão nunca substitui uma resposta.

A adjacência da testemunha na hipótese 2 é essencial para o limite sem termo
aditivo de robustez. A aprovação unilateral, sozinha, não basta para essa prova.
Previsão perfeita significa Mhat=M **e todas as testemunhas selecionadas
aprovam**. Acertar somente o conjunto M não garante a segunda condição.

O ótimo offline é

\[
OPT=|M|+vc(H-M).
\]

O problema é residual: consultas anteriores, obtenção do incumbente e do limiar
não estão incluídas em OPT. Não se reivindica um limite para o custo completo
de um decoder que ainda precise encontrar um incumbente verdadeiro.

## 2. Algoritmo

Calcule Cpred=MVC(H-Mhat), P=Mhat∪Cpred e C0=MVC(H); escreva h=|C0|.
Aqui MVC é um cover mínimo exato de custo unitário.

Comece com um matching máximo W0 de H-Mhat. Aumente-o por caminhos aumentantes
em H até obter um matching máximo global W. Defina

\[
R=P\setminus V(W).
\]

Todas essas escolhas e desempates são fixados usando somente H e a previsão,
antes de qualquer resposta real ou sorteio.

- Se R=∅, consulte P e conclua com as pendências reais da hipótese 3.
- Caso contrário, sorteie p uniformemente em R. Consulte/cacheie u(p).
  Se seu teste aprovar, consulte P; se rejeitar, consulte C0. Depois conclua
  somente com pendências reais de M. Toda consulta repetida usa o cache.

O sorteio é sobre R, não sobre todos os alvos previstos. A política usa apenas
o teste do alvo sorteado para escolher o ramo. Informações adicionais da mesma
resposta podem ajudar a certificação final, mas não são necessárias à prova.
Poda de consultas já dispensadas por um certificado real somente reduz o custo.

## 3. Por que R é auditável e sua fonte pertence ao fallback

Por König, |W0|=|Cpred|. Cada aresta de W0 encontra Cpred, e as arestas são
disjuntas; portanto W0 satura todos os vértices de Cpred. Um aumento preserva
todos os **vértices anteriormente casados**, embora possa trocar suas arestas.
Assim o matching máximo global W ainda satura Cpred. Consequentemente,

\[
R\subseteq Mhat.
\]

Também |W|=h. Cada uma de suas h arestas encontra C0, de tamanho h; logo W
satura todos os vértices de C0, com exatamente uma ponta de C0 por aresta.
Nenhum p∈R pertence a C0. Como C0 cobre H, todo vizinho de p pertence a C0.
Em particular,

\[
u(p)\in C0.
\]

A auditoria já está contabilizada no cover consultado quando há rejeição.

## 4. Garantias globais

**Teorema.** Sob as hipóteses acima, a política sempre retorna um certificado
real e satisfaz

\[
\boxed{\mathbb E ALG\le 2OPT.}
\]

Com previsão perfeita, cada execução satisfaz ALG≤OPT+1; se R=∅, ALG≤OPT.
A expectativa usa somente o sorteio uniforme, com instância e previsão fixas.

**Prova.** Ambos os ramos consultam um cover e suas pendências reais; por isso
são corretos independentemente da previsão. Para a contagem, ponha

\[
r=|R|,\quad s=|P\cap V(W)|,\quad t=|R\cap M|,\quad
u_0=|M\setminus(P\cup V(W))|.
\]

Qualquer certificado consulta ao menos uma ponta de cada uma das h arestas
disjuntas de W. Além disso, precisa consultar os t+u0 vértices mandatory
indicados acima, que estão fora de V(W). Portanto

\[
OPT\ge h+t+u_0. \tag{1}
\]

Há exatamente 2h-s vértices casados fora de P. Assim

\[
|P|+|M\setminus P|
\le(r+s)+(2h-s)+u_0=r+2h+u_0. \tag{2}
\]

Se r=0, não há auditoria e (2) dá ALG≤2h+u0≤2OPT, por (1).

Agora suponha r>0. Seja q a probabilidade de aprovação. Pela aprovação
unilateral e pelo sorteio uniforme, q≤t/r. No ramo aprovado há no máximo uma
consulta extra, além de P e M fora de P. No rejeitado a fonte está em C0.
Logo os respectivos tetos são

\[
A=1+r+2h+u_0,\qquad B=h+OPT.
\]

Por (1), D=A-B≤r-t+1. Se D≤0, EALG≤B≤2OPT. Se t=0, q=0 e vale o mesmo.
Nos demais casos t≥1 é inteiro, de modo que D≤r e

\[
\mathbb E ALG\le B+qD
\le h+OPT+(t/r)r
=h+OPT+t\le2OPT.
\]

Com previsão perfeita, P é um certificado ótimo. Se r>0, seu teste sempre
aprova; a fonte custa no máximo uma consulta além de P. Se r=0, nem essa
consulta existe. Isso prova a consistência aditiva. ∎

O teorema cobre P com arestas internas: não exige que P seja independente.
Por exemplo, numa única aresta com Mhat contendo suas duas pontas, R é vazio;
não se deve chamar uma dessas pontas de «excesso» usando somente P-C0.
O fator 2 não foi provado ótimo entre todos os algoritmos randomizados.

## 5. Consumidores e custo completo

O oráculo A87 de dois blocos com limiar τ conhecido satisfaz o contrato:
H contém ab quando α_a+β_b>τ; a consulta de a revela u_ab; ela testemunha b
quando u_ab+β_b>τ, e simetricamente. Mantém-se a política CLOSED de preferência
do incumbente nos empates hipotéticos. Não mudar limiar, posições, pins,
tokenização, EOS/PAD, normalização ou alvo J para obter esse corolário.

Outro consumidor matemático é orientação de um grafo bipartido com valores
independentes desconhecidos w_v em intervalos abertos I_v. Descarte arestas de
intervalos disjuntos. Então M={v: existe vizinho u com w_u∈I_v}; certificados
são exatamente cover+M. Previsões de valores dão Mhat e testemunhas vizinhas,
e o teste é w_u(p)∈I_p. Portanto o mesmo algoritmo/prova se aplica. Isto não
alega melhorar sorting pleno, cujo conjunto de comparações é diferente.

A preparação usa covers e matchings bipartidos exatos e aumentos de matching,
todos polinomiais; o tempo do solver não é uma consulta gratuita. A aplicação
precisa contabilizar construção de H, previsão, preparação, memória, resposta
completa do oráculo, validação e saída. Sortear um inteiro uniforme em [0,r)
exige RNG exato; sua contagem de bits e tempo não é a contagem de consultas.
Custos distintos por vértice e adversário que escolhe respostas depois do
sorteio não estão cobertos. A adjacência da fonte, bipartição e custo unitário
não podem ser descartados na transferência.

No decoder, uma chamada revela um vetor de condicionais e custa tempo/memória
do modelo. O teorema não demonstra melhora de acurácia, latência ou throughput,
nem que um checkpoint produza boas previsões para R. A captura neural V1 já
congelada permanece a mesma: seus seis incumbentes iniciais corretos já eram
certificados pelas duas consultas iniciais, sem oportunidade para essa auditoria.

## 6. Comparadores e prioridade ainda aberta

Mandatory, witness sets, covers e matchings já fazem parte de algoritmos de
aquisição. [Erlebach et al., ESA 2022](https://arxiv.org/abs/2206.15201) estudam
MST com previsões e garantias de consistência/robustez. Seu Teorema 9 e
Algoritmos 1–2 já usam MVC, matching, cobrança por pares e extensão por
caminhos aumentantes, obtendo consistência 1/robustez 2 na fase
prediction-mandatory-free. Essas ferramentas são antecedentes explícitos;
o custo para chegar a essa fase impede transferir a garantia global por mera
invocação dela. Para orientação,
[Erlebach et al., IJCAI 2023](https://arxiv.org/abs/2305.09245), Teoremas 2.1,
3.1 e 3.9, oferecem tradeoffs determinísticos e erros dependentes da previsão;
o Teorema 4.2 já oferece sorting 1-consistente/2-robusto. A versão anterior
[Learning-Augmented Query Policies](https://arxiv.org/abs/2011.07385) também
deve integrar a auditoria de prioridade. Esses trabalhos são controles
competentes, não alegações de que toda combinação de suas ferramentas é nova.

O candidato específico desta nota é auditar um único alvo previsto não casado
por W, com a carga conjunta (1) e a fonte já pertencendo ao fallback, obtendo
robustez esperada estrita 2 e consistência aditiva 1. Não se localizou aqui um
antecedente idêntico; isso não comprova prioridade. Exigem-se busca/revisão
independentes, inclusive da literatura de orientação bipartida e verificação
randomizada de conselhos. Uma revisão independente das provas ESA/IJCAI e
dos combinadores de [Antoniadis et al., TALG 2023, Teorema 19](https://arxiv.org/abs/2003.02144)
não encontrou o mesmo passo de auditar uniformemente um mandatory previsto
não saturado, nem uma redução que forneça a garantia por parâmetros.
Essa busca é evidência delimitada de prioridade, não prova de ausência de
antecedente. Não há reivindicação de ótimo global.

A barreira determinística por estrelas disjuntas da seção 5 de
`multiple-probe-analysis.md` continua pertinente: consistência OPT+a para a
constante e robustez constante são incompatíveis naquele contrato. Esta prova
randomizada não a contradiz. O resultado mais forte também mostra por que a
sharpness de 2+c_k para sorteio entre **todos** os heads não estabelece uma
fronteira ótima entre algoritmos competentes. Não alterar as provas ou dados
congelados anteriores para incorporar esta mudança de política.

## 7. Protocolo CPU proposto, ainda não executado

Congelar esta nota e uma fonte nova antes de executar qualquer auditoria.
Reutilizar a interface dos oráculos exatos de `online_probe.py`; as fontes e
execuções antigas permanecem congeladas. Para a política nova:

- Usar todos os 15 grafos 2×2 não vazios, cap=1/32 em todos os vértices e
  τ=9cap/8. Para cada subconjunto dos 2|E| arcos dirigidos, a componente real
  é cap/4 quando o arco está presente e cap/16 caso contrário. Cada tabela
  realiza exatamente seu conjunto de arcos; grau≤2 garante somas normalizadas
  estritamente abaixo da cap. Todos os scores reais são menores que τ.
  Para cada tabela, usar **todos** os subconjuntos de arcos como previsão.
  São 5^4−1=624 tabelas reais e 17^4−1=83.520 pares real/previsão.
- Usar também as estrelas disjuntas já fixadas: r=1,2,4,8 centros e n=2,3
  folhas, tabelas high/low e previsões high/actual/sem arcos do auditor anterior.
  Previsões coincidentes permanecem como entradas declaradas do protocolo.

Acrescentar somente dois checks estruturais públicos: uma aresta com ambas as
pontas em Mhat, portanto P contém a aresta e R=∅; e H com arestas
a0b0,a1b0,a1b1, Mhat={a0}, Cpred={a1}, W0={a1b0}. O caminho aumentante
a0,b0,a1,b1 troca a aresta inicial e preserva todos os vértices casados de W0.
Esses checks validam a construção do matching, sem novos dados neurais.

Para cada caso, calcular W0 e W, verificar que ambos são matchings, que suas
cardinalidades igualam os respectivos covers mínimos e que W satura Cpred.
Verificar R⊆Mhat, R∩C0=∅ e u(p)∈C0 para todo p∈R. Enumerar exatamente cada
p∈R com peso racional 1/|R|; com R vazio executar uma única vez sem auditoria.
Não usar PRNG, arredondar médias ou inspecionar respostas não consultadas na
política. Confrontar OPT com a referência congelada de quatro cortes e, nos
grafos 2×2, com todos os 16 subconjuntos de consultas por tabela real:
9.984 checks de subconjuntos antes das estrelas. A preparação pública pode
ser cacheada por grafo/caps/limiar e previsão, nunca por respostas reais.

Cada execução deve terminar com certificado validado independentemente,
sem repetir uma consulta real. Conferir a probabilidade exata de aprovação
pelas testemunhas fixas, EALG≤2OPT e, quando os arcos previstos são exatos,
ALG≤OPT+1 em **cada** execução. Com R vazio e previsão perfeita, conferir
ALG≤OPT. As estrelas high com previsão high têm custo algébrico rn+1;
as low com previsão high têm custo r; high sem arcos tem custo rn+r.
São valores a testar, não resultados medidos. Preservar erros, recusas e
interrupções; não ajustar casos após dados. O auditor testa correção finita,
não prioridade, desempenho de modelo nem utilidade neural.

## 8. Resultado da auditoria exaustiva

Esta nota e `matching_probe.py` foram congelados em `c57da4a3` antes da
primeira execução. Comando:

```bash
.venv-live/bin/python attempts/87-conditional-choice-readout/matching_probe.py --audit
```

Resultado: **PASS**, sem recusa ou falha. Saída dos contadores:

```json
{"forecast_cases":83568,"instances":640,"named_public_checks":2,"policy_runs":83679,"public_plans":642,"subset_checks":10016}
```

Os 83.520 pares exaustivos real/previsão foram executados, mais 48 entradas
nas estrelas, incluindo as previsões coincidentes anunciadas. Houve 624
tabelas reais na grade e 16 nas estrelas. Os 10.016 subconjuntos incluem os
9.984 previstos na grade mais os 32 dos dois casos de estrelas com quatro
vértices. Cada custo esperado foi somado exatamente com racionais, sem PRNG.

Passaram certificados independentes, custos sem consultas duplicadas,
robustez esperada 2OPT, consistência por execução, probabilidade de aprovação,
referências de OPT, saturação/otimalidade dos matchings e os dois checks
estruturais públicos. Para r=1,2,4,8 e n=2,3, os casos high confirmaram
rn+1 com previsão high e rn+r sem previsão; os low confirmaram r.

Exemplo racional previsto, não um benchmark neural: r=8,n=3 deu 25 consultas
com previsão correta, contra 32 para MVC seguido de mandatory. Confiar
cegamente na mesma previsão faria 24 no caso correto, mas 24 no caso low,
onde a auditoria faz 8. Isso demonstra o tradeoff da família matemática,
não dominância uniforme sobre todos os controles nem redução de latência.

A auditoria finita não substitui a prova geral e não estabelece prioridade.
O resultado sustenta uma candidata de contribuição teórica em aquisição
certificada de informação; a exigência de ganho próprio em dLLMs continua
pendente e a V1 negativa permanece preservada.

## 9. Outro consumidor: conjunto por limiar, sem incumbente

Esta seção declara uma operação diferente da escolha do máximo na V1.
Seja um catálogo externo finito E de palavras de mesmo comprimento, dividido
em dois blocos. Uma lei de dois blocos/mistura de ordens atribui

\[
J(a,b)=\tfrac12R(a)Q_B(b\mid a)+\tfrac12C(b)Q_A(a\mid b)
=u_{ab}+v_{ab}.
\]

R e C vêm da raiz; Q_B e Q_A são produtos de heads dos blocos nas respectivas
consultas condicionais. Esses fatores normalizam sobre palavras completas do
vocabulário, sem renormalizar o catálogo. Políticas agrupadas/misturas têm
antecedentes em [TUBE, seção 2.3](https://arxiv.org/html/2605.24292v1);
essa lei não é a contribuição reivindicada. Não se exige que heads de
diferentes consultas sejam condicionais de uma única posterior Bayesiana.

A operação é devolver exatamente {e∈E:J(e)≥τ}, com τ externo conhecido,
pagando por consultas condicionais compartilhadas. Exija 0<u<α=R/2,
0<v<β=C/2 e somas de estrelas estritamente menores que suas caps; cabeças
com zeros atingíveis requerem outro contrato. Para τ≤0, todo o catálogo é
aceito sem consulta condicional. Para τ>0, ponha

\[
H=\{ab:α_a+β_b>τ\},\quad
M=\{b:τ-β_b<u_{ab}<τ\}\cup\{a:τ-α_a<v_{ab}<τ\}.
\]

**Certificado iff cover+M.** Uma aresta de H com nenhuma ponta consultada
admite valores dos dois lados do limiar. Se uma ponta retorna x, a outra só
é ambígua quando τ−cap<x<τ. Se x≥τ, a positividade do outro componente já
garante J>τ. Se x+cap≤τ, a cap estritamente inatingível garante J<τ.
No intervalo aberto de ambiguidade, o componente ainda desconhecido admite
ambas as respostas: seu alvo é mandatory mesmo revelando todos os outros
vértices. Reciprocamente, um cover contendo M resolve todas as arestas.
Isso também cobre J=τ: ambas as pontas ficam mandatory e são consultadas.
As desigualdades de H/M são as mesmas para saída J>τ ou J≥τ neste contrato
interior; com zeros/caps atingíveis, as fronteiras são diferentes.

Uma testemunha selecionada verifica o teste real τ−cap_p<x<τ; portanto é
adjacente e unilateral. Depois de qualquer cover, só faltam tais alvos de M.
O teorema das seções 3–4 aplica-se com caps arbitrárias, **sem** consultar
cegamente todas as caps≥τ e sem supor um vencedor. A raiz, construção do
catálogo, previsão e preparação continuam tendo custos próprios.

[Conformal Language Modeling, ICLR 2024, seção 5.2](https://arxiv.org/html/2306.10193v2)
emprega likelihood como qualidade e rejeição por limiar; não apresenta
exatamente este catálogo/score. Split conformal com score −J, função de
score/catálogo fixos antes da calibração, dados permutáveis e inclusão de
empates fornece a cobertura usual. A aquisição exata preservaria o MESMO
conjunto para cada seed e, assim, essa cobertura. **Cobertura sozinha não
demonstra utilidade**: um score ruim pode devolver o catálogo inteiro.

Objeções prospectivas: se o catálogo foi gerado pela própria política J,
reutilizar as consultas da geração pode já fornecer um cover; resta apenas
mandatory e desaparece a escolha que esta auditoria melhora. Se um bloco tem
massas muito menores que o outro, um lado inteiro pode ser mandatory e o MVC
já pode ser ótimo. Além disso J bruto não é posterior das classes do catálogo;
normalizá-lo por soma desconhecida mudaria o certificado. Para catálogo externo,
é preciso comparar tamanho/qualidade dos conjuntos em cobertura semelhante
contra produto raiz, score indexado/dJev e a própria previsão barata Jhat,
todos calibrados separadamente. Para custo, os controles são capped-lazy e
advice-first-lazy com a mesma previsão, pagando também preparo e calibração.

### Diagnóstico estrutural exploratório, a congelar antes de ler os dados

Uma fonte nova `threshold_set_diagnostic.py` reutilizará as oito capturas de
treino já publicadas em `docs/artifacts/raw/a87_native_v1.jsonl.gz`, sem novos
forwards, reabrir o gate MAP da V1 ou alegar validação conformal. É uma análise
exploratória de dados antigos, não um teste prospectivo de qualidade.

Verificar SHA256 descompactado
`c828867d81991ee26f8887858839471e2c3fdbdac6a677993d47cdd024675f04`,
proveniência dos inputs e oito casos completos/interiores. Para CADA caso e
TODOS os 40 limiares públicos τ=2^(−j), j=1,…,40, calcular os arcos filtrados
reais e os previstos pelo produto raiz, hat_u=hat_v=2αβ. Preparar o plano
de matching usando só caps/previsão e calcular R. Descrever tamanho de H/M/R,
OPT=|M|+vc(H−M), custo do cover C0 unido a M, erros do conjunto previsto,
testemunhas de R que aprovam e tamanho do conjunto J≥τ. São 320 linhas.

Não selecionar o melhor limiar, calibrar, medir política adaptativa ou promover
o custo offline a economia do método. Preservar todas as linhas/recusas.
O diagnóstico pergunta se há trabalho que a auditoria possa influenciar antes
de justificar uma coleta nova; não é um gate positivo de benefício neural.

### Resultado do diagnóstico e protocolo de replay separado

Fonte/contrato do diagnóstico congelados em `b527e890`. Comando:

```bash
.venv-live/bin/python attempts/87-conditional-choice-readout/threshold_set_diagnostic.py \
  --output artifacts/a87-threshold-structure-v1.json
```

Resultado: `EXPLORATORY_COMPLETE`, todas as 320 linhas, sem recusa. R não vazio
em 121 linhas, máximo |R|=3. Nessas 121 há ao menos uma testemunha que aprova;
111 têm todas aprovando e dez contêm alguma que rejeita. Nas 121 o controle
simples C0∪M tem custo maior que OPT; em 106 das 320 ele já é ótimo. Somado
sobre toda a grade, |C0∪M|=10.495 e OPT=6.308. Esses são custos de conjuntos
offline; um controle ativo pode fazer melhor. Não há ganho de política medido
nesse diagnóstico nem limiar escolhido depois dos dados.

O próximo replay é uma versão separada, sem novos dados neurais e sem alterar
o diagnóstico congelado. Congelar `threshold_set_replay.py` e este protocolo
antes de calcular custos de políticas. Usar TODOS os mesmos 320 pares, com
as mesmas caps, arcos filtrados e previsão produto-raiz. Enumerar cada alvo
de R com peso uniforme exato; R vazio dá uma execução sem auditoria. A
candidata usa o teste filtrado e a escolha P/C0 do teorema. Em toda conclusão,
pular consultas sem aresta ativa e consultar imediatamente pontas forçadas.

Controles predefinidos, todos vendo somente respostas realmente consultadas:

1. C0 com a mesma poda e conclusão forced.
2. P com a mesma poda/conclusão, confiando na mesma previsão sem auditoria.
3. Capped-lazy: escolher aresta ativa com maior soma de caps desconhecidas;
   consultar sua ponta desconhecida de maior cap. Empates por menor ID.
4. Degree-greedy: escolher vértice desconhecido com mais arestas ativas
   incidentes; empates por maior cap e depois menor ID. Mesma conclusão forced.

Para J≥τ e τ>0, aresta com nenhuma ponta conhecida está ativa se a soma de
caps supera τ; com uma ponta x conhecida, se τ−cap<x<τ; com ambas conhecidas,
seu rótulo já está resolvido. A política não lê valores futuros. Validar
independentemente que os intervalos finais decidem os MESMOS 77 rótulos do
scorer integral, sem consulta repetida. Conferir EALG≤2OPT e a consistência
por execução quando os arcos previstos forem exatos. Registrar custos de cada
controle, média racional da candidata, wins/ties/losses contra cada controle
e contra o menor custo dos quatro por linha, além da soma sobre TODAS as
320 linhas. Contar raiz separadamente como uma chamada comum.
Cada linha é um cenário alternativo executado de forma independente. As
somas não representam uma sequência de 320 pedidos ao mesmo cache: reutilizar
heads entre limiares do mesmo prompt mudaria igualmente o problema de todas
as políticas e poderia tornar consultas posteriores gratuitas.

Não escolher seeds, limiar, controle ou subconjunto depois dos custos.
Comparar ao melhor controle por linha é deliberadamente mais forte que um
único controle implementável sem conhecer resultados. Este é um replay
exploratório de trabalho sobre dados de treino antigos, não um teste de
cobertura, qualidade semântica, latência online ou novo gate MAP da V1.

## 10. Corolário online contando a raiz

Para a operação da seção 9, considere um oráculo global que permite consultar
a raiz e os canvases condicionais do catálogo em qualquer ordem. Cada resposta
é um array de heads positivos e normalizados; arrays de contextos distintos
podem variar independentemente. Não usar coerência Bayesiana, limites dos
logits, análise dos pesos da rede nem outra fonte gratuita de informação.
Catálogo, τ e prior estático são públicos; funções da raiz atual só ficam
disponíveis após consultá-la. O conselho não confiável guia escolhas, mas não
restringe as completações admissíveis como se fosse informação verificada.

A projeção para produtos por estrela não perde informação relevante à
certificação por limiar nesse oráculo: se uma aresta permanece ambígua, há
um contexto ainda não consultado cujos heads podem concentrar ou retirar
probabilidade da palavra-alvo para cruzar o limiar, mantendo TODOS os arrays
já consultados. Isso requer ao menos uma posição livre em cada bloco e
vocabulário com símbolos alternativos. São exatamente as completações usadas
na prova de cover+M. Não é uma hipótese sobre o que um checkpoint fixo faria
ao alterar seus pesos, e sim o modelo de consulta/certificação declarado.

Seja OPT_global o menor certificado no oráculo global e OPT_cond o ótimo
após dar a raiz gratuitamente. Para qualquer certificado global S, as consultas
S sem a raiz continuam certificando quando a raiz é dada. Portanto

\[
OPT_{cond}\le |S\setminus\{raiz\}|\le OPT_{global},\qquad
\mathbb E ALG_{online}\le1+2OPT_{global}.
\]

Sob conselho perfeito, ALG_online≤OPT_global+2. Se algum ótimo consulta a
raiz, os limites melhoram para 2OPT_global−1 e OPT_global+1. Uma condição
suficiente natural é saída real não vazia com τ>0: sem observar a raiz,
reduzir suas probabilidades em ambos os blocos remove uma alternativa
incluída, preservando todas as respostas condicionais conhecidas; logo não
há certificado global sem raiz.

São limites de chamadas online da operação com τ e conselho disponíveis.
Preparo estático A e calibração devem ser somados: numa sequência de N pedidos,
o limite contabiliza A mais a soma dos respectivos custos online. Isso não é
garantia de latência ou de conjuntos semanticamente melhores.

## 11. Resultado exploratório contra os controles de limiar

Produtor/protocolo congelados em `51f10fc5`, antes de calcular os custos das
políticas. Comando:

```bash
.venv-live/bin/python attempts/87-conditional-choice-readout/threshold_set_replay.py \
  --output artifacts/a87-threshold-replay-v1.json
```

Resultado: `EXPLORATORY_COMPLETE`, 320/320 cenários e todos os certificados
válidos, sem recusa. Custos condicionais somados sobre toda a grade:

| Política | Consultas condicionais | Vitórias / empates / derrotas da candidata |
| --- | ---: | ---: |
| Candidata, média racional exata | 39491/6 | — |
| MVC com poda e forced | 10347 | 214 / 106 / 0 |
| Advice-first com a mesma previsão | 6308 | 0 / 199 / 121 |
| Capped-lazy | 6308 | 0 / 199 / 121 |
| Degree-greedy | 6429 | 0 / 310 / 10 |
| Melhor controle por cenário | 6308 | 0 / 199 / 121 |

Há uma raiz comum em cada cenário (320 no somatório contrafactual). Advice-first
e capped-lazy alcançaram OPT em TODOS os 320 cenários; a candidata não pôde
economizar chamadas frente a eles e acrescentou custo em 121. As reduções
frente ao MVC mais fraco não constituem benefício próprio contra controles
competentes. Nenhum limiar, caso ou controle foi removido.

Decisão: esta qualificação exploratória também não justifica uma campanha
neural do consumidor com previsão produto-raiz nem sua seleção como aceleração
de dLLM. Não modificar limiares, casos ou partição para salvar esse resultado.
A prova geral de robustez/consistência e a aplicação clássica de orientação
permanecem válidas; não dependem de ganho nesta realização neural. A decisão
de aceitar o núcleo teórico em FTC como tema central, mantendo a aplicação
dLLM por justificar, é uma mudança de enfoque que permanece pendente do usuário.
