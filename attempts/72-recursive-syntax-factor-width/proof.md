# Prova escrita candidata: aproximação não remove o custo de representação

Não é uma verificação Lean, revisão humana ou prova de prioridade científica.
O argumento usa ingredientes clássicos; a extensão quantitativa é a candidata.

## 1. Operação e interfaces

Fixe a GLC de bytes

    S -> P # P,
    P -> ( P ) | [ P ] | ε.

Ela gera dois blocos inteiramente aninhados, separados por `#`, e não
toda a linguagem Dyck. A gramática é fixa, não ambígua e LL(1): FIRST
das alternativas não vazias de P são `(` e `[`, enquanto FOLLOW(P)
é {`)`, `]`, `#`, fim}, disjunto delas.

A interface tem N posições, cada uma com um token original de um byte
em Σ={`(`,`)`,`[`,`]`,`#`}; EOS/PAD estão ausentes. Para pesos unários
racionais não negativos, o posterior de UM passo congelado é

    P_w(x) = 1[x∈L, |x|=N] ∏_i w_i(x_i) / Z_w,    Z_w>0.

O limite inferior usa apenas pesos iguais a 1. Não usa zeros, infinito,
treinamento, logits adversariais nem consultas neurais. Escreva N=2l+1,
l>=1, e P para essa lei uniforme. Existem (l+1)2^l palavras: o marcador
fica em 2j, 0<=j<=l, e cada um dos l pares de delimitadores recebe um
bit de tipo independente. Portanto j é uniforme.

O concorrente representa uma lei Q como marginal normalizada de um
produto de fatores não negativos, com domínios finitos e um observado
X_i por posição original. Aceita-se QUALQUER grafo, qualquer quantidade
de ocultos, qualquer cardinalidade e fatores escolhidos depois de conhecer
P. Nem os fatores nem os ocultos precisam ser determinísticos. Permutação
interna das posições é admitida; os tokens de saída conservam sua posição.

No grafo PRIMAL, cada escopo de fator induz uma clique. Para uma
decomposição em árvore, defina

    c(B) = Σ_{v∈B} log2 |dom(v)|,       W = max_B c(B).

Um fator de aridade N não é uma árvore de largura pequena: seu grafo
primal é uma clique, mesmo que o grafo bipartido de fatores seja estrela.
Domínios originais podem ser contraídos, sem esconder seu custo em
auxiliares. Se TV(P,Q)<1/2, cada X_i precisa de pelo menos dois estados:
cada delimitador tem probabilidade marginal <=1/2 por seu bit de tipo;
o marcador tem probabilidade 1/(l+1)<=1/2. Portanto nenhum átomo de
uma marginal univariada de P supera 1/2. Um X_i constante já daria
TV>=1/2, pela contração de TV sob projeção na posição i.

## 2. Matching e uma bolsa balanceada

Numere posições de 0 a 2l. Para o marcador 2j, defina M_j pelos pares
à esquerda de soma 2j-1 e à direita de soma 2l+2j+1. Cada par tem uma
abertura à esquerda e um fechamento à direita. Separe
E={0,2,...,2l} e O={1,3,...,2l-1}.

**Lema 1.** Ao variar j, cada par de E×O ocorre em exatamente um M_j.

**Prova.** Para (a,b)∈E×O, a+b é ímpar. Se a+b<2l+1, o único marcador
possível é a+b+1, à direita de ambos; caso contrário é a+b-(2l+1),
à esquerda de ambos. Os dois casos ficam nas posições 0,2,...,2l. ∎

**Lema 2.** Existe uma bolsa S tal que cada componente do grafo menos S
contém no máximo l/2 observados de O. Se S contém s observados no total,
e t_j conta os pares de M_j entre componentes DIFERENTES fora de S,
então, para s<l/2,

    (1/(l+1)) Σ_j t_j >= l/2-s.

**Prova.** Atribua peso 1 de cada observado de O a uma bolsa que o
contém. Um centroide da árvore de bolsas tem a propriedade desejada:
a conexidade das bolsas de cada variável coloca cada componente do
grafo menos S num componente da árvore menos a bolsa escolhida.

Escreva s_E=|S∩E| e s_O=|S∩O|. Cada posição de E fora de S tem,
dentre seus l parceiros de O, ao menos l/2-s_O em outros componentes
fora de S. Pelo Lema 1,

    Σ_j t_j >= (l+1-s_E)(l/2-s_O).

Dividindo por l+1, isso é pelo menos l/2-s_O-s_E/2, e portanto
pelo menos l/2-s. ∎

## 3. O que um separador probabilístico pode transportar

Use TV(P,Q)=(1/2)Σ_x |P(x)-Q(x)| e a afinidade
F(P,Q)=Σ_x sqrt(P(x)Q(x)). Temos 1-TV(P,Q)<=F(P,Q). Agregar
estados não diminui F, por Cauchy–Schwarz em cada fibra da agregação.
Essas fórmulas também definem F para subprobabilidades.

**Lema 3.** Seja R a lei de t bits uniformes independentes, cada bit
copiado em dois extremos. Particione os extremos em blocos, sem colocar
os dois extremos de um par no mesmo bloco. Para qualquer lei produto
Q sobre os blocos,

    F(R,Q) <= 2^(-t/2).

**Prova.** O tensor A_b=sqrt(Q_b) de cada bloco tem norma euclidiana 1.
A afinidade é 2^(-t/2) vezes a contração desses tensores, com um índice
binário para cada dupla. Seu grafo não tem autoarestas. Mescle blocos,
contraindo TODOS os índices compartilhados em cada mescla. Cauchy–Schwarz
dá ||contrair(A,B)||_2<=||A||_2||B||_2, equivalente a
||AB||_F<=||A||_F||B||_F após achatar os índices contraídos. Uma
mescla sem índices compartilhados é produto tensorial. Nenhuma
autoaresta fica para trás. Ao final a contração escalar é <=1. ∎

Condicionadas TODAS as variáveis de S, as componentes do grafo menos S
são independentes, mesmo após somar seus ocultos. Por isso qualquer
representação de Q admite

    Q = Σ_{h=1}^r λ_h Q_h,       r<=|dom(S)|<=2^W,

com Σ_h λ_h=1, observados de S fixos em cada Q_h, e Q_h produto
sobre as componentes restantes. Esse é um argumento de separação do
grafo primal; não exige independência das posições dentro da componente.

## 4. Teorema e prova

**Teorema.** Para qualquer representação acima e qualquer decomposição
em árvore, se TV(P,Q)<=e<1/5, então

    W >= l/6 + log2(5(1/5-e)^2).

Em particular, com erro de no máximo 10%,

    W >= (N-1)/12 - log2(20).

Alguma bolsa tem, portanto, ao menos 2^((N-1)/12)/20 estados conjuntos.
O grafo pode ter sido escolhido especificamente para essa única lei.

**Prova.** Tome a bolsa S do Lema 2. Se s>=l/6, a bolsa já custa
pelo menos l/6 bits: nenhum observado pode ter domínio unitário, pela
hipótese e<1/5. Isso basta, pois 5(1/5-e)^2<=1/5<1.

Se s<l/6, a média dos t_j é maior que l/3. Como 0<=t_j<=l,
uma fração α>=1/5 dos marcadores tem t_j>=l/6; uma fração menor
daria média menor que (1/5)l+(4/5)(l/6)=l/3. Chame-os de bons.

Seja P_j o alvo condicionado a ter o único marcador em 2j, e E_j
o evento correspondente. E_j é interseção de restrições UNÁRIAS.
Assim, Q_h|E_j, quando definida, continua produto sobre as componentes.
Projete nos extremos dos t_j pares entre componentes e retenha apenas
seus bits de tipo, descartando as outras posições e os observados de S.
Sob P_j são t_j bits uniformes copiados. Pelo Lema 3 e pela
monotonicidade de afinidade,

    F(P_j,Q_h) <= sqrt(Q_h(E_j)) 2^(-t_j/2).

Seja P_G a subprobabilidade de P nos marcadores bons, e E_G sua união.
A massa de P_G é α. Como os E_j são disjuntos, Cauchy–Schwarz dá

    F(P_G,Q_h) <= sqrt(α Q_h(E_G)) 2^(-l/12),
    F(P_G,Q)   <= sqrt(α r) 2^(-l/12).

A segunda linha usa sqrt(Σ z_h)<=Σ sqrt(z_h) e
Σ_h sqrt(λ_h Q_h(E_G))<=sqrt(r Σ_h λ_h Q_h(E_G))<=sqrt(r).
A massa comum fora de E_G é <=1-α; dentro é <=F(P_G,Q). Logo

    1-TV(P,Q) <= 1-α + sqrt(α r) 2^(-l/12).

Para e<1/5<=α, rearranjar fornece

    r >= ((α-e)^2/α) 2^(l/6)
      >= 5(1/5-e)^2 2^(l/6).

Usamos que (α-e)^2/α cresce para α>e. Tome log2 e use r<=2^W. ∎

## 5. Contraparte eficiente e custo completo

O matching M_j é conhecido quando se conhece j. Para pesos arbitrários,

    Z_w = Σ_{j=0}^l w_{2j}(#) ∏_{(a,b)∈M_j}
                                  [w_a('(')w_b(')')+w_a('[')w_b(']')].

Calcular os l+1 termos custa O(N^2) operações aritméticas e O(N)
células de massas, calculando um marcador por vez. Sortear o marcador
proporcionalmente à sua massa e os tipos independentemente dentro de
M_j amostra o posterior inteiro. No caso uniforme bastam um marcador
uniforme e l bits independentes, com tempo e memória de saída O(N).
Esses algoritmos por condicionamento são CLÁSSICOS, não a contribuição.

Para inteiros de b bits, as massas têm O(Nb+N) bits. Um limite seguro
para preparar as massas é O(N^2 M(Nb+N)) em bits, com multiplicação de
custo M. Escolhas inteiras por rejeição pagam O(N(Nb+N)) bits aleatórios
em esperança. Para pesos uniformes são l+O(log(l+1)) bits em esperança.
Pesos racionais exigem pagar denominadores comuns por posição, que
cancelam na normalização. Ler os pesos e escrever a saída custa Ω(N).
Forward neural, RNG, consultas, memória e saída não são considerados
recursos gratuitos de uma implementação completa de dLLM.

## 6. Significado e limites

- A construção de dois palíndromos separados e a obstrução EXATA já
  aparecem em Kadioglu/Sellmann (2010) e Wang/Yap (2023). Anotar os
  tipos como aberturas/fechamentos torna a apresentação LL(1); isso,
  por si só, não é um avanço próprio.
- A candidata é a obstrução QUANTITATIVA para aproximação da lei
  normalizada, permitindo fatores não negativos, ocultos arbitrários,
  domínios contraídos e escolha de qualquer grafo após conhecer P.
- O limite é de representação por bolsas. Um algoritmo que usa tabelas
  densas não pode garantir custo polinomial apenas pela largura/domínios.
  Não é um limite inferior de memória ou tempo para TODO algoritmo.
- Condicionar no marcador deixa um matching de largura 1. Enumeração
  de contextos, CFDs e circuitos são controles competentes e escapam
  da restrição do grafo conjunto. Não alegamos vencê-los em latência.
- O alvo é um produto congelado condicionado pela gramática no suporte
  finito declarado, não a trajetória neural nativa completa. Isso não
  prova qualidade semântica, ganho neural nem exatidão no vocabulário
  inteiro de um tokenizer com tokens adicionais.
- A prova escrita e os oráculos finitos não estabelecem prioridade,
  aprovação acadêmica ou impacto. A auditoria de antecedentes está no
  README; a suficiência científica da extensão permanece aberta.

## 7. Auditoria adicional e fortalecimento (2026-10-20 UTC)

Origem: seções 1–6 no commit `1804e5d94f860f46c69d67b39596b56f2624d709`.
Elas foram preservadas. Não se encontrou um contraexemplo ao teorema da
seção 4. O limite e<1/5 resulta da escolha de um único separador, e não
é uma fronteira de aproximação. Segue uma prova escrita mais forte,
sem alegação de prioridade, revisão humana ou formalização integral.

### 7.1 Pontos delicados da prova original

- No Lema 1, “marcador” na prova significa sua POSIÇÃO 2j, não j.
  Para a+b=2l+1 vale o segundo caso, dando o marcador 0.
- O centroide pesa somente os l observados ímpares. Pesar ocultos ou
  contar todas as variáveis daria outro enunciado de balanceamento.
- Condicionar uma atribuição completa do separador não condiciona
  implicitamente a validade gramatical. A independência usada é de Q.
  O evento E_j fixa `#` em 2j e exclui `#` nas demais posições: é uma
  interseção unária, inclusive quando tem probabilidade zero em Q_h.
- A projeção de tipo pode ser total: `(` e `)` viram 0; `[` e `]`
  viram 1; `#` recebe, por exemplo, 0. Em E_j nenhum extremo projetado
  é `#`. A orientação abertura/fechamento é descartada, não trocada.
- O Lema 3 admite ciclos e múltiplas arestas. Contrair apenas uma
  aresta entre dois tensores e depois tomar um traço não justificaria
  a estimativa. É essencial contrair TODAS as arestas comuns.
  É também um caso da desigualdade clássica de Finner, com expoente
  1/2 nos blocos: cada bit pertence a exatamente dois blocos.
- Na aproximação, usa-se a massa comum `Σ min(P,Q)=1-TV`.
  A afinidade pode superar a massa de P_G; não se supõe o contrário.
  Componentes de mistura com peso zero podem ser eliminadas.

### 7.2 Vários separadores e um limite explícito de erro

Seja k o número de observados cujo domínio admitido em Q é unitário.
O contrato é o da seção 1, incluindo contração de domínios.
Para qualquer inteiro K>=2, escreva B=(K-1)W. Então

    TV(P,Q) >= 1 - 2^(-max(0,ceil((k-1)/2))),                 (A)
    TV(P,Q) >= 1 - 2/K - 2(B+k)/l - 2^(B/2-l/4).             (B)

As cotas podem ser negativas em tamanhos pequenos; continuam válidas.

**Prova de (A).** Q fixa k posições. Em qualquer contexto j compatível,
no máximo uma é marcador. As demais fixam os tipos de pelo menos
ceil((k-1)/2) pares distintos, porque cada par tem dois extremos.
Sob P_j os tipos são bits uniformes independentes. A probabilidade
de concordar com todas as posições fixadas é, portanto, no máximo
2^(-max(0,ceil((k-1)/2))). A média sobre j obedece à mesma cota.
Q dá massa 1 a esse evento; TV é pelo menos a diferença de massas. ∎

**Separação múltipla.** Numa árvore com pesos não negativos de soma l,
podemos remover no máximo K-1 nós deixando cada componente com peso
no máximo l/K. Para ver isso, enraíze a árvore e processe de baixo
para cima. Some o peso do nó aos resíduos dos filhos. Se o resíduo
excede l/K, selecione o nó e devolva resíduo zero; senão devolva a soma.
Cada seleção consome massa estritamente maior que l/K, disjunta da
consumida nas demais seleções. Logo há menos de K seleções. Cada
componente restante é um resíduo de filho de nó removido ou da raiz,
e tem peso no máximo l/K. Pesos concentrados numa bolsa são admitidos.

Aplique à árvore de bolsas, atribuindo como antes os observados de O.
Seja S a união das bolsas selecionadas e de TODOS os observados
unitários. Cada componente do grafo menos S tem no máximo l/K
observados de O. As bolsas selecionadas têm capacidade conjunta no
máximo B; adicioná-las por união pode apenas diminuir essa capacidade.
Os k observados unitários acrescentam zero bits. Cada observado não
unitário custa pelo menos um bit. Assim,

    |S observado| = s <= B+k,        |dom(S)| <= 2^B.

Como no Lema 2, mas agora com componentes de peso no máximo l/K,

    Σ_j t_j >= (l+1-s_E)(l(1-1/K)-s_O),
    média_j t_j >= l(1-1/K)-s.

A primeira desigualdade usa a contagem de parceiros quando o segundo
fator é não negativo. Se ele é negativo, a segunda desigualdade já é
trivial, pois seu lado direito é negativo. Chame bom o contexto com
t_j>=l/2. Como t_j<=l, a fração α de bons obedece a

    α >= 1 - 2/K - 2s/l.

Condicionar S decompõe Q em r<=2^B produtos de componentes. Repetir
a seção 4 com limiar l/2, em vez de l/6, dá

    α - TV(P,Q) <= F(P_G,Q) <= sqrt(α r) 2^(-l/4)
                                  <= 2^(B/2-l/4).

Se não há bons, a mesma cota final de TV é trivial. Substituir a cota
de α e s<=B+k prova (B). ∎

**Teorema de erro tendendo a um.** Para qualquer sequência das
representações admitidas, se W=o(N), então TV(P,Q) tende a 1.
Equivalentemente, para cada erro constante e<1, capacidade Ω_e(N)
é necessária. A constante depende do erro; não se alega uniformidade
quando e também tende a 1.

**Prova.** Se k>sqrt(l), (A) tende a 1. Nos demais casos, escolha
K=max(2,floor(sqrt(l/max(W,1)))). Como W=o(l), K tende ao infinito,
B=o(l) e k/l<=1/sqrt(l). Todos os termos subtraídos em (B) tendem
a zero; em particular B/2-l/4=-l/4+o(l). Isso cobre todos os índices
da sequência, mesmo alternando os dois casos. ∎

Uma versão com constantes: ponha δ=1-e>0, k_*=1+2log2(1/δ) e
K=ceil(8/δ). Se TV<=e, (A) implica k<=k_*. Para

    l >= max(8 k_*/δ, 8 log2(4/δ)),

(B) implica W>=δ l/[8(K-1)]. De fato, se B>=l/4 isso já basta;
caso contrário, 2^(B/2-l/4)<=2^(-l/8)<=δ/4. Os termos 2/K e
2k/l também são <=δ/4, forçando 2B/l>=δ/4. As constantes não
foram otimizadas; a seção 4 mantém a cota melhor para erro 0,1.

### 7.3 Consequência explícita para circuitos probabilísticos

Considere PCs não negativos, suaves, com folhas univariadas sobre os
cinco tokens, tamanho m contando nós e arestas, e produtos binários.
“Estruturado” significa respeitar UM vtree das posições: todo produto
separa os dois filhos do nó correspondente desse vtree. Somas podem
ser não determinísticas. O vtree pode ser escolhido depois de conhecer P.
Não são admitidas folhas multivariadas arbitrárias de custo unitário.

**Redução clássica, explicitada no caso ponderado.** Um PC estruturado
dessa forma admite uma representação de fatores com

    W <= max(3log2(m), log2(5m)) <= 3log2(m)+log2(5).

Para cada nó v do vtree, introduza H_v cujos estados são os gates do
circuito com aquele escopo (no máximo m). No interior, expandir apenas
cadeias de somas do mesmo escopo escreve cada gate g como

    f_g = Σ_{a,b} θ_{g,a,b} f_a f_b,       θ_{g,a,b}>=0,

com a e b gates dos dois escopos filhos. Use θ como fator de
(H_v,H_esq,H_dir). Nas folhas, use f_g(x_i) como fator (H_v,X_i).
Fixe H_raiz ao gate de saída. Por indução no vtree, somar os ocultos
reproduz exatamente o circuito, incluindo multiplicidades de caminhos
de soma e zeros. Não se usa uma tradução existencial que esqueça pesos.
As bolsas de três ocultos e as bolsas (H_v,X_i), ligadas pelo vtree,
formam uma decomposição válida com a capacidade declarada.
Normalizar preserva Q. Essa redução não é uma contribuição alegada.

**Corolário.** PCs estruturados de tamanho m=2^o(N) têm TV(P,Q)->1.
Para qualquer e<1 constante, aproximar P exige m=2^Ω_e(N).
Isso decorre da seção 7.2 e da redução acima.

Em contrapartida, P tem um PC suave, decomponível e DETERMINÍSTICO
de tamanho O(N²): some os l+1 contextos de marcador, de pesos 1/(l+1).
Cada ramo é o indicador de seu marcador vezes o produto, sobre M_j,
das duas atribuições equiprováveis do tipo de cada par. Esses produtos
têm escopos disjuntos; as duas atribuições de um par e os contextos
do marcador têm suportes disjuntos. A mesma construção calcula Z_w
com pesos unários, marginais e amostras por técnicas clássicas.

É uma separação robusta explícita entre decomposição geral e uma
estrutura única, para um posterior de GLC LL(1) fixa. Não é um limite
para TODOS os PCs: o circuito quadrático é precisamente uma alternativa.
A suficiência científica e a prioridade dessa especialização ainda
exigem auditoria; a redução, a separação exata e a operação de inferência
em circuitos já têm antecedentes diretos citados no README.

### 7.4 Contraexemplos a interpretações operacionais

1. **Marginais.** Q_ind=∏_i P(X_i) tem TODAS as marginais univariadas
   corretas e largura zero (capacidade log2(5)). Ainda assim, pela
   seção 7.2, TV(P,Q_ind)->1. Um consumidor que só exige marginais
   não está sujeito ao limite para a lei conjunta.
2. **Validade.** Uma massa pontual numa palavra válida tem validade
   100%, W=0 com domínios contraídos, e TV=1-1/((l+1)2^l).
   O teorema não impede um gerador pequeno de produzir sintaxe válida.
3. **Pesos não uniformes, todos positivos.** Dê peso M a `#` numa
   posição par 2j0 e peso 1 a todos os demais tokens/posições. A massa
   posterior desse marcador é M/(M+l). A lei Q=P_j0, representável
   por um matching, fica a TV=l/(M+l) do posterior. Tomar
   M>=l(1-e)/e dá erro <=e com largura 1 e O(log N+log(1/e)) bits
   por peso. A obstrução uniforme não cobre todos os logits positivos.

## 8. Hipótese operacional por convoluções, antes do protocolo V2

Esta seção é adicional à fonte `c74ab700`. FFT e decomposição de kernels
em somas de produtos são técnicas clássicas de matching (ver o README).
Não se reivindica sua invenção nem prioridade da composição abaixo.

Para pesos estritamente positivos, ponha A_i=w_i('(')+w_i('['),
C_i=w_i(')')+w_i(']'), x_i=(w_i('(')-w_i('['))/A_i e
y_i=(w_i(')')-w_i(']'))/C_i. A contribuição de um par a<b é

    w_a('(')w_b(')')+w_a('[')w_b(']') = A_a C_b (1+x_a y_b)/2.

O conjunto de aberturas no contexto j é [0,j) ∪ [2j+1,l+j+1), e
o de fechamentos é [j,2j) ∪ [l+j+1,2l+1). Assim, a contribuição
U_j das orientações e do marcador tem todos os seus logaritmos
calculáveis por prefixos de log A e log C em O(N) operações reais.

**Proposição condicional.** Se max_i|x_i| max_i|y_i|<=ρ<1, os
logaritmos das massas de todos os contextos admitem aproximação com
erro absoluto <=η em O(K N log² N) operações aritméticas reais e
O(K N) memória, onde K satisfaz

    l ρ^(K+1)/((K+1)(1-ρ)) <= η.

**Prova.** Trunque log(1+z) em Σ_{k=1}^K (-1)^(k+1) z^k/k.
Somar a série geométrica de valores absolutos da cauda limita seu
erro por |z|^(K+1)/((K+1)(1-|z|)). Cada contexto tem l pares.
Para cada grau k, sejam

    H_s(k) = Σ_{a<b, a+b=s} x_a^k y_b^k.

Cada par a<b é separado por exatamente um corte da árvore binária de
intervalos de posições. Nesse corte, a convolução dos x^k da metade
esquerda com os y^k da direita acumula sua contribuição no índice a+b.
Há O(log N) níveis, cada um com custo total O(N log N) por convolução
rápida; subproblemas vazios não contribuem. Os pares de M_j são
precisamente aqueles de soma 2j-1 e 2l+2j+1. Logo,

    log Z_j = log U_j - l log 2
        + Σ_{k=1}^K (-1)^(k+1) [H_{2j-1}(k)+H_{2l+2j+1}(k)]/k
        + erro_j,       |erro_j|<=η.

Índices fora do intervalo são zero. Esse argumento computa todos os
contextos, sem consultar um oráculo que esconda o custo dos pares. ∎

**Normalização e amostra.** Se cada log-massa tem erro em [-η,η],
as probabilidades normalizadas têm razão Q_j/P_j em
[exp(-2η),exp(2η)]. Consequentemente TV(P_j,Q_j)<=exp(2η)-1.
A lei da palavra, gerada escolhendo esse marcador e depois amostrando
EXATAMENTE os tipos condicionais com inteiros, tem a MESMA TV:
os suportes de contextos são disjuntos e as condicionais são iguais.
Esta última igualdade permite auditar a TV conjunta enumerando apenas
l+1 massas, sem enumerar as (l+1)2^l palavras.

**Limites materiais.** O enunciado conta aritmética real, não operações
de bits nem latência. Se ρ tende a 1, K pode ser grande; compromissos
e suporte contraído podem introduzir zeros e tornam a implementação
V2 não suportada. FFT64 introduz erros adicionais aos da série.
Não se transfere a cota escrita para o programa sem contabilizá-los.
O protocolo mede proposta e certificação racional independente, cobra
ambas no total certificado e mantém recusas. O circuito contextual
vetorizado é um controle de mesmo nível, não só um parser genérico.
