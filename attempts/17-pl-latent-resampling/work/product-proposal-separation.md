# Separação contra qualquer proposta produto única

Resultado escrito nesta auditoria, ainda sem revisão humana ou formalização
Lean. Não é reivindicação de prioridade: separar novidade de correção continua
obrigatório. Esta família é objeto de prova, não benchmark de treinamento.

## Enunciado

Considere um array JSON com `2m` valores binários, slots de pontuação fixos,
`q_i(0)=1/10`, `q_i(1)=9/10` e taxas PL `lambda_i=q_i`. Observe `m` valores
selecionados iguais a 1 numa ordem fixada. Nas `m` posições descartadas,
escreva `z` para o número de valores 1 e

\[
 S=m/10+4z/5,\quad L=m/10,\quad H=9m/10,\quad
 f(s)=\prod_{r=1}^{m}\frac{9/10}{s+9r/10}.
\]

Todos os caminhos têm probabilidade positiva. A lei condicional é
`mu(y) proportional w(y)f(S(y))`, onde `w` é o produto dos Bernoullis ocultos.
O fator dos tokens observados é comum e cancela apenas nesta comparação.

**Proposição.** Todo amostrador exato que propõe uma única distribuição produto
nos valores ocultos e corrige por aceitação/rejeição precisa de pelo menos

\[
 \frac13 e^{m/360}
\]

tentativas em esperança, mesmo escolhendo as probabilidades de cada posição e
o melhor envelope possível. A mistura da nota tem `O(sqrt(m))` tentativas,
preparação e aritmética polinomiais no circuito e na entrada. O ganho é
assintótico na classe de comparadores declarada, não em segundos universais.

## 1. O melhor produto pode ser tomado simétrico

Como o alvo tem suporte total, qualquer proposta produto exata por rejeição
precisa de probabilidades positivas. Parametrize cada Bernoulli da proposta
por um número real `t_i`, reponderando a base por `exp(-t_i lambda_i)`.
Essa parametrização cobre toda probabilidade estritamente entre 0 e 1.

Defina

\[
 C(\mathbf t)=\max_y f(S(y))\exp(\sum_i t_i\lambda_i(y_i)),\qquad
 Z(\mathbf t)=\prod_i[\tfrac1{10}e^{-t_i/10}
                         +\tfrac9{10}e^{-9t_i/10}].
\]

O melhor normalizador de envelope dessa proposta é `B(t)=C(t)Z(t)`.
Se `Z_A=sum_y w(y)f(S(y))`, a esperança mínima de tentativas é `B(t)/Z_A`:
uma aceitação exata necessariamente é proporcional a alvo/proposta e não
pode exceder 1 em nenhum caminho.

`log C` é máximo de funções afins e `log Z` é soma de log-sum-exp: `log B`
é convexo. Também é invariante por permutações das posições. Aplicar Jensen
à média de todas as permutações dá

\[
 B(\bar t,\ldots,\bar t)\le B(t_1,\ldots,t_m).
\]

Logo um produto assimétrico não melhora o melhor produto simétrico.

## 2. A melhor taxa simétrica é a secante

Se `h=log f`, então `h(s)+ts` é convexo. Ambos os extremos `L,H` pertencem
ao suporte, portanto

\[
 C(t)=\max\{f(L)e^{tL},f(H)e^{tH}\}.
\]

Os termos cruzam em
`t_*=(h(L)-h(H))/(H-L)>0`. Antes do cruzamento, a derivada de `log B` é
`L-E_t[S]<0`; depois é `H-E_t[S]>0`. Todos os valores ocultos continuam com
probabilidade positiva. Assim `t_*` minimiza `B` em todos os reais, inclusive
taxas negativas. Sob essa proposta,

\[
 z\sim\operatorname{Binomial}(m,p_*),\qquad
 p_*=\frac9{9+e^{4t_*/5}}.
\]

Limites da derivada e uma soma de Riemann dão

\[
 \frac59\le t_*\le
 \sum_{r=1}^{m}\frac1{m/10+9r/10}
 \le\int_0^m\frac{dx}{m/10+9x/10}=\frac{10}9\log10.
\]

Como `10^8<9^9`, vale `exp(4t_*/5)<9`; como `exp(4/9)>=13/9`, obtemos
`1/2<p_*<=81/94`.

## 3. Aceitação exponencialmente pequena

Hoeffding e `37/40-81/94>1/16` implicam

\[
 P\{z/m\notin[3/8,37/40]\}\le2e^{-m/128}.
\]

No intervalo restante, `S-L>=3m/10` e `H-S>=3m/50`. Além disso,

\[
 h''(s)=\sum_{r=1}^m(s+9r/10)^{-2}\ge\frac{25}{81m}
 \quad(s\in[L,H]).
\]

Se `ell` é a secante de `h`, a convexidade de
`h(s)-25s²/(162m)` fornece

\[
 \ell(s)-h(s)\ge\frac{25}{162m}(s-L)(H-s)\ge\frac m{360}.
\]

No ótimo `t_*`, o envelope exponencial é `exp(ell(s))`; a aceitação é
`exp(h(s)-ell(s))`. Ela é no máximo `exp(-m/360)` nesse intervalo e no máximo
1 fora. Portanto

\[
 P(\text{aceitar})\le e^{-m/360}+2e^{-m/128}
 \le3e^{-m/360},\qquad E[N]\ge e^{m/360}/3.
\]

Como o produto ótimo já satisfaz essa cota, todos os produtos a satisfazem.
Na mistura, `k=m`, `kappa=9`, `J=O(sqrt(m))` e `E[N]<=2J+1`. O circuito
da gramática/suporte pode ser uma cadeia produto de tamanho `O(m)`; o parser
geral também tem tamanho polinomial nessa família. O número de bits das
precisões racionais, inclusive `-log f(H)=O(m log m)`, é polinomial.

## Alcance científico

A separação é mais forte que comparar contra uma escolha ruim de taxa ou
contra repetir o evento PL inteiro até dar certo. Inclui a melhor proposta
produto, mesmo com probabilidades diferentes por slot. É uma vantagem
matemática de uma mistura corrigida sobre esse modelo de proposta única.

Não abrange mistura adaptativa, propostas com dependências globais, um circuito
ampliado por contadores, tabelas condicionais ou todas as codificações por
fatores. Nesta família homogênea, o contador binomial de `m+1` estados também
resolve a tarefa em tempo polinomial, possivelmente mais barato. Portanto a
prova não torna o método exclusivo ou obrigatório para arrays binários.

Sua função no TCC seria justificar por que reponderar unárias uma única vez
não basta como garantia geral para propostas descartadas PL. A mistura opera
também em circuitos gramaticais menos especializados, mas prioridade e
significância acadêmica desse recorte continuam sem confirmação externa.
