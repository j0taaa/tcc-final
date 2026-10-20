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
