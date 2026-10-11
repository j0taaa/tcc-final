# Score de um output limitado: basta custo finito no ponto analisado

2026-10-11. Prova ESCRITA posterior a V11, com contrato próprio abaixo.
Não altera os snapshots, a prova histórica nem os dois diagnósticos negativos.
Não é revisão humana, formalização integral, prioridade ou benefício neural.

## 1. Contrato

Um procedimento independente de p observa bits iid Bernoulli(p), além de
aleatoriedade auxiliar R cuja lei não depende de p. Seu número TOTAL de bits
N é uma parada inteira não negativa. Ele termina quase certamente para TODO
p em um intervalo aberto J contido em (0,1). O output H é a MESMA função
mensurável do transcript terminado/R em todos os p e satisfaz |H|<=C.

Fixe p0 interior e suponha SOMENTE E_{p0}N=a<infinito. Não se exige finitude
de E_pN em outros pontos, bound local uniforme, momento de ordem2 de N,
continuidade de E_pN ou cauda exponencial. Então g(p)=E_pH é diferenciável
EM p0 e

    g'(p0) = E_{p0}[H (S_N-p0 N)] / [p0(1-p0)].

Não concluir continuidade de g' apenas desta hipótese pontual. V11 fornece
C1 quando o orçamento é localmente uniforme. Procedimentos que não terminam
em parâmetros vizinhos ou que recebem informações dependentes de p estão
fora deste contrato. Não se permite alterar H com p depois da execução.

## 2. Experimento parado e identidade de informação

Considere a lei Q_p do transcript terminado, incluindo R. Uma medida comum
é a soma, sobre palavras binárias finitas u, da medida de R restrita às
decisões que terminam exatamente em u. Em cada folha de comprimento n e s
bits1, sua densidade é p^s(1-p)^(n-s). Tanto Q_p0 como Q_t têm massa1, pois
o algoritmo termina em ambos os parâmetros. Suas densidades são positivas
nas mesmas folhas. Isto também cobre N0 e aleatoriedade auxiliar contínua;
não substitui a execução por uma árvore finita nem integra R como se fosse
informação sobre o parâmetro.

Para t vizinho de p0, o logaritmo da razão de densidades é

    S_N log(p0/t) + (N-S_N) log((1-p0)/(1-t)).

Se t permanece interior, cada incremento é limitado em valor absoluto por
uma constante finita. O logaritmo completo é integrável em Q_p0 porque
E_{p0}N=a. Wald, ou diretamente a soma de incrementos previsíveis, fornece
E_{p0}S_N=p0 a. Portanto

    D(Q_p0 || Q_t) = a * kl(p0 || t),

onde kl é a divergência entre Bernoulli. Esta identidade sequencial e o uso
de divergência são princípios clássicos, não uma invenção reivindicada.

Defina a distância de Hellinger sem o fator1/2 por

    d_H(Q_p0,Q_t)^2 = integral (sqrt(q_p0)-sqrt(q_t))^2.

Usando -log x >= 1-x com x=sqrt(q_t/q_p0), temos d_H^2<=D. Consequentemente

    limsup_{t->p0} d_H(Q_p0,Q_t)/|t-p0|
      <= sqrt(a / [2 p0(1-p0)]).

Em particular d_H->0. A desigualdade de Cauchy implica convergência em
variação total, logo Q_t(N>m)->Q_p0(N>m) para cada m fixo. Não há suposição
de que E_tN seja limitada ou sequer finita. O lado da divergência importa:
o custo usado aqui é E_{p0}N, nunca E_tN.

## 3. Controlar a DERIVADA da cauda, não somente sua probabilidade

Escreva H_m=H 1_{N<=m}, F_m=H 1_{N>m}, g_m(t)=E_tH_m e r_m(t)=E_tF_m.
Para m fixo, g_m é uma soma FINITA de monômios t^s(1-t)^(n-s) com coeficientes
integrados sobre R, portanto é diferenciável. A mesma função F_m das folhas
é usada nos dois parâmetros. Por Cauchy e pela desigualdade triangular L2,

    |r_m(t)-r_m(p0)|
      = |integral F_m (sqrt(q_t)-sqrt(q_p0))
                       (sqrt(q_t)+sqrt(q_p0))|
      <= C [sqrt(Q_t(N>m))+sqrt(Q_p0(N>m))] d_H(Q_p0,Q_t).

Divida por |t-p0| e primeiro passe t->p0, mantendo m FIXO:

    limsup_{t->p0} |r_m(t)-r_m(p0)|/|t-p0|
      <= 2C sqrt(Q_p0(N>m)) sqrt(a / [2p0(1-p0)]).

O lado direito tende a0 quando m->infinito. A ordem desses limites é
essencial. Não se aplicou Markov com E_tN, não se diferenciou uma série
infinita sem controle e não se pressupôs uma cauda uniforme nos vizinhos.

## 4. Recuperar o score e a derivada

No ponto p0, os incrementos (B_k-p0)1_{N>=k} têm média0 e são ortogonais
em L2. Como a<infinito, sua soma converge em L2 e coincide com
W_N=S_N-p0 N. Assim

    E_{p0}W_N=0,   E_{p0}W_N^2=p0(1-p0)a.

Diferenciação FINITA dá

    g_m'(p0) = E_{p0}[H W_N 1_{N<=m}]/[p0(1-p0)].

Por Cauchy,

    |g_m'(p0)-ell|
      <= C sqrt(a Q_p0(N>m)/[p0(1-p0)]) -> 0,

com ell=E_{p0}[H W_N]/[p0(1-p0)]. Como g=g_m+r_m, as seções anteriores dão

    limsup_{t->p0} |[g(t)-g(p0)]/(t-p0)-ell|
      <= 2C sqrt(Q_p0(N>m)) sqrt(a/[2p0(1-p0)])
         + |g_m'(p0)-ell|.

Agora faça m->infinito. O limsup é0, logo a derivada existe e é ell. QED.

Se a=0, a parada ocorre sem bits quase certamente em p0. Folhas de N0 têm
densidade independente de p; sua massa1 vale em todos os p, e o mesmo
argumento fornece g constante/derivada0. Não há divisão pelo custo a.

## 5. Consequências para a fronteira A34 e para CR

Para um factory de par, exija marginais X,Y~Bernoulli(p) e término a.s.
para TODO p interior. Tome H=Z=X+Y-1. Como g(p)=2p-1, em p0=1/2 o resultado
fornece E[Z M_N]=1, com M_N=2S_N-N e E M_N^2=E N. Portanto a fronteira
inferior A34 precisa SOMENTE de E_{1/2}N<=b: nenhum orçamento uniforme ou
regularidade adicional do concorrente é necessário para esse lower bound.

Para b>=2, m=floor(b) e lambda=b-m, a desigualdade inteira de V1 dá

    Pr_{1/2}(X=Y) >= s_b=(1-lambda)/m+lambda/(m+1),
    inf_{0<p<1} eta_A(p) <= 1-2s_b.

A construção de ruína/mistura já preservada atinge a fronteira e tem custo
esperado b em TODO p. Assim ela continua minimax ótima mesmo contra a classe
MAIOR de factories cujo único orçamento exigido é no ponto justo, incluindo
concorrentes que podem ter esperança infinita em outros parâmetros. Isto
não impõe p1/2 à aplicação ou ao benchmark: é um ponto adversarial do limite
minimax. Não promete otimalidade pontual nem inferioridade de métodos known-p.

Para output limitado geral, centrar H e aplicar Cauchy ao score dá

    E_{p0}N >= [g'(p0)]^2 p0(1-p0) / Var_{p0}(H),

quando a variância é positiva. Para H Bernoulli isto recupera CR com
Var(H)=g(1-g), SEM fastness, mas com output limitado, término em todo o
intervalo e custo finito no ponto. CR/score/informação parados são antecedentes;
esta demonstração não reivindica inventar o limite.

Uma função de saída não diferenciável em p0 não pode ter um factory deste
contrato com E_{p0}N finita. Por exemplo, um cotovelo interior, mesmo
Lipschitz, precisa de esperança infinita no próprio cotovelo. Esta é uma
consequência analítica, não uma nova aplicação dLLM ou publicação confirmada.

## 6. Ataques ao argumento e delimitação

- Revelar TODOS os bits futuros no transcript invalidaria a identidade KL:
  o experimento contém somente R independente e o prefixo observado.
- Término a.s. em t é indispensável para Q_t ser uma lei de probabilidade
  sobre as mesmas folhas. Massa em trajetórias infinitas não é ignorada.
- Apenas |H|<=C permite o bound de cauda com probabilidades. Estimadores
  não limitados podem violar regularidade sequencial; não se refuta Simons.
- H não pode depender de t diretamente; o score não conta essa dependência.
- Custo finito num ponto garante derivada NESSE ponto, não C1 num intervalo.
- Não usar tempo de hardware, truncar deadlines, filtrar recusas ou confundir
  a extensão de classe de comparadores com qualidade semântica maior.

## 7. Oito critérios, antes de qualquer expansão

1. **Uso:** coordenar dois payloads originais de uma dLLM+GLC sem a lei de
   um evento de commitment. A nota remove uma restrição dos comparadores;
   ainda falta uma fronteira nativa barata com sinal útil.
2. **Diferença:** sharpness da fronteira de par, não score/ruína/CR. O lema
   pontual pode ser conhecido em estatística sequencial. Prioridade aberta.
3. **Escolha:** a garantia minimax agora enfrenta todos os factories p-blind
   com custo justo<=b, não somente os localmente uniformes/rápidos. Continua
   sem enfrentar logits/ruídos known-p, mais outputs ou consumo de todo draw.
4. **Matemática:** prova por leis de folhas, Wald, KL/Hellinger e dois limites
   explícitos; nenhum benchmark serve para provar o enunciado.
5. **Experimentos:** nenhum modelo/timing aqui. Os screens0/8 e1/8 negativos
   conservam seus gates fechados. Testes do sampler não verificam este lema.
6. **Custos:** o budget é número TOTAL de bits/draws; setup, forwards, parsing,
   descarte e consumo continuam contabilizados em seus contratos separados.
7. **Objeção:** resultado pode ser consequência clássica; algoritmo com
   side information não pertence à comparação. Utilidade nativa ainda falta.
8. **Artigo:** confrontar fontes originais de regularidade antes de afirmar
   novidade. Não alegar resolver uma questão aberta ou cumprir o objetivo
   de publicação somente por esta nota. Leitura em primary-reading-v12.md.
