# Auditoria matemática independente da nota recebida

Esta é uma revisão escrita pelo agente, não revisão humana externa nem
formalização Lean. A nota original permanece inalterada. Código de referência,
enumeração independente e protocolo estão nesta tentativa. Resultados numéricos
ficam no relatório separado; exemplos construídos abaixo são objetos de prova.

## Operação e hipóteses indispensáveis

Em um estado fixo da dLLM, um circuito determinístico, decomponível e suave
representa exatamente os IDs de tokens válidos no suporte finito. Cada caminho
usa cada slot uma vez. Pesos `q` e taxas `lambda` são racionais positivos.
O modelo propõe uma conclusão inteira condicionada à gramática, e seleciona
`k` posições pela lei Plackett–Luce. Registram-se a ordem e os tokens fixados.
Somente esse novo canvas determina os próximos estados e a recompensa.

No backend reutilizado, a gramática é LL(1) verificada e EOS é ausente. Não há
garantia para gramática ambígua, vocabulário completo ou remasking arbitrário.
O suporte precisa permanecer localmente fixo ao diferenciar a política.
Não se pressupõe que um algoritmo de produção já use essa política.

Se `U` são os slots ocultos, `S(y)=sum_U lambda_i(y_i)`, `b_r` são as taxas
observadas e `c_r=sum_{j>=r} b_j`, a probabilidade da ordem observada é

\[
 f(S)=\prod_{r=1}^k \frac{b_r}{S+c_r}.
\]

Isso decorre diretamente dos denominadores restantes em cada escolha PL.
Logo a lei condicional dos tokens descartados é proporcional a `w(y) f(S(y))`
sobre caminhos válidos que respeitam a evidência, com `w=prod_i q_i`.
Condicionar apenas aos tokens escolhidos costuma produzir outra distribuição.

## Verificação dos limites da mistura

Para `h=log f`, `h''(s)=sum_r (s+c_r)^(-2)>0`. A tangente em `s_j`
exponenciada é um minorante global `M_j(s)=alpha_j exp(-t_j s)`, com
`t_j=-h'(s_j)`. A decomposição de `S` faz cada termo fatorar em pesos locais.

Com `d=ceil(sqrt(k))` e grade geométrica em `s+c_min`, o último ponto anterior
a `S` satisfaz `S-s_j <= (s_j+c_min)/d`. O resto integral de Taylor é no
máximo `k/(2d²)<=1/2`. Portanto

\[
 e^{-1/2}f(S)\le R(S)=\sum_jM_j(S)\le Jf(S),\qquad
 f(S)\le2R(S)\le2Jf(S).
\]

A mistura de componentes normalizados propõe `wR/Z_R`; aceitar com `f/(2R)`
devolve a lei alvo. A esperança de tentativas é `2Z_R/Z_A<=2J`. Não é preciso
calcular exatamente o normalizador `Z_A` do alvo.

O arredondamento racional superior também mantém o argumento. Escrevendo
`u_i=exp(-t_j lambda_i)` e `ubar_i>=u_i`, ambos em `[0,1]`, vale

\[
 \bar\alpha\prod_i\bar u_i-\alpha\prod_i u_i
 = (\bar\alpha-\alpha)\prod_i\bar u_i
   +\alpha(\prod_i\bar u_i-\prod_i u_i)
 \le\delta_a+3^k m\delta_u.
\]

Assim o erro somado é no máximo `f_min/2`, e o limite final é
`f<=2 Rbar<=(2J+1)f`. A moeda é uma fração exata; as exponenciais arredondadas
afetam a proposta, sem aproximar a lei aceita. O programa usa enclosures
inteiros com arredondamento para fora, não decisões em ponto flutuante.

O custo polinomial em bits é **relativo ao circuito fornecido**, não uma cota
linear nem uma garantia de compilação eficiente para toda GLC. Precisão,
denominadores comuns, todos os componentes e reconstrução entram no custo.
Um teto de recursos pode recusar a consulta. Condicionar resultados a um
timeout dependente dos sorteios não conserva automaticamente a lei alvo.

## Comparação matemática delimitada com a rejeição simples

Há uma separação demonstrável mesmo usando o melhor envelope constante, e
sem taxas artificialmente exponenciais. Considere arrays JSON com `2m` valores
binários, probabilidades `q(0)=1/10`, `q(1)=9/10` e `lambda=q`. Qualquer
combinação é válida; suporte, gramática e probabilidades não contêm gabarito.
Observe `m` posições selecionadas, todos os valores iguais a 1, numa ordem
fixada. As demais `m` posições são ocultas. Este evento tem probabilidade
positiva, mas não se afirma que seja representativo de um corpus.

Antes de observar a seleção, condicionado apenas aos tokens fixados,
`Z`, o número de valores 1 ocultos, tem lei `Binomial(m,9/10)`. Então
`S=m/10+4Z/5`, `L=m/10` e `c_r=9(m-r+1)/10`. A rejeição com a distribuição
gramatical/evidência como proposta e envelope `f(L)` tem aceitação média
`a=E[f(S)/f(L)]`. `L` é atingível com peso positivo; o envelope constante
não pode ser diminuído sem trocar a proposta ou considerar regiões.

Quando `Z>=m/2`, `S>=m/2`. Cada razão é limitada por

\[
 \frac{L+c_r}{S+c_r}\le
 \frac{m/10+9m/10}{m/2+9m/10}=\frac57.
\]

Markov aplicado a `9^(-Z)` dá

\[
 P(Z<m/2)\le 3^m E[9^{-Z}]
 =3^m(1/10+(9/10)/9)^m=(3/5)^m.
\]

Separando os dois eventos,

\[
 a\le(3/5)^m+(5/7)^m\le2(5/7)^m,
 \qquad E[N_{\rm rejeição}]\ge\tfrac12(7/5)^m.
\]

Na mistura, `k=m`, `kappa=9` e
`J<=1+log(9)/log(1+1/ceil(sqrt(m)))=O(sqrt(m))`.
Preparação, memória, aritmética e tentativas têm custo polinomial no circuito
e em `m`, contra a esperança exponencial desse rejeitador. É uma separação
de algoritmos especificados; não depende de cronometrar um benchmark.

**Objeção necessária:** nesta família homogênea, um solver especializado pode
amostrar o contador binomial reponderado em `m+1` estados e depois os slots.
Ele também é polinomial e pode ser mais barato. Outros métodos de inclinação
exponencial podem evitar a rejeição ruim. Portanto esta prova não estabelece
exclusividade, novidade geral ou superioridade sobre todo amostrador competente.
Ela explica quando a garantia da mistura é útil frente à rejeição simples,
não decide sozinha qual método usar em uma aplicação.

A revisão posterior fortalece o comparador para **qualquer proposta produto
única**, inclusive assimétrica, em
[product-proposal-separation.md](product-proposal-separation.md). A prova usa
convexidade/simetrização, o majorante secante ótimo e concentração binomial.
Continua excluindo propostas correlacionadas e contadores especializados;
prioridade e revisão humana não são inferidas desse fortalecimento.

## Gradiente e benefício que realmente foi provado

O score completo é `R(C) grad log p_theta(Y,C)` e inclui a normalização
gramatical e a seleção. Sob a hipótese de estado Markoviano, condicionado ao
canvas observado e às ordens registradas, os tokens latentes fatoram pelos
posteriors de cada passo. Isso permite gerar réplicas sem novos forwards ou
recompensas. Não se diferencia o amostrador auxiliar.

Para `r` réplicas mais a proposta original, a covariância é

\[
 V_o+\frac{V_h}{r+1},\quad
 V_o=\operatorname{Cov}(E[G\mid C]),\quad
 V_h=E[\operatorname{Cov}(G\mid C)].
\]

A prova usa independência condicional e covariância total; não é um novo
teorema estatístico. A redução é estrita somente nas direções com variância
latente positiva. Registrar as ordens facilita computação, mas pode conservar
mais variância observável do que condicionar apenas aos canvases.

Com uma réplica, fração latente `beta=tr(V_h)/tr(V_o+V_h)` e sobrecusto relativo
`d`, a eficiência por tempo melhora exatamente quando `beta>2d/(1+d)`.
Não existe benefício universal de custo: se `beta` é pequeno, a preparação
pode custar mais que a economia. Essa identidade não valida PPO/GRPO com
clipping, convergência mais rápida ou melhor modelo ao fim do treinamento.

## Antecedentes conferidos e fronteira da novidade

- [Mask-Aware Policy Gradients](https://arxiv.org/html/2607.15200v1), §3.1,
  equação 9, já usa seleção PL de posições a partir das probabilidades dos
  tokens. As potências 1 e 2 do protocolo correspondem a temperaturas 1 e 1/2.
  A nota propõe uma operação condicional adicional, não inventa a política.
- [Liu et al., ICML 2019](https://proceedings.mlr.press/v97/liu19c.html),
  trata redução de variância de gradientes discretos mantendo o viés original.
  Rao–Blackwellização e covariância total são antecedentes, não novidade aqui.
- [Beylkin–Monzón 2010](https://amath.colorado.edu/faculty/beylkin/papers/BEY-MON-2010.pdf),
  Teorema 5, pp. 134–135, já constrói somas exponenciais positivas para potências
  inversas. O limite citado fixa a potência; não foi estabelecida equivalência
  com o produto de resolventes, `k` variável e moeda racional desta nota.
- [Raim–Livsey–Irimata, Vertical Weighted Strips](https://arxiv.org/html/2401.09696v2),
  §§2 e 3.2, já usa misturas, majorantes/minorantes exponenciais e rejeição
  exata. Seus componentes são truncados a regiões, requerendo massas dessas
  regiões. Aqui os termos cobrem globalmente e fatoram em unárias, evitando
  calcular no circuito uma restrição global de intervalo de `S`.
- [Koyama 2023](https://arxiv.org/html/2301.08931v3) trata aproximações positivas
  exponenciais de funções completamente monótonas em representação integral
  finita. Não foi verificado um teorema que elimine a diferença restante.

Essa diferença operacional é uma **candidata**: reamostragem latente PL em
circuitos de tokens, com limite uniforme em `sqrt(k) log(kappa)` e correção
racional. Ausência de um resultado idêntico nessas fontes não prova prioridade.
A nota precisa separar resultados conhecidos e provar que o recorte restante
não é consequência imediata de uma aproximação geral já estabelecida.

EPIC é um decoder de inferência; não entrega essa operação de treinamento.
Uma comparação de latência de geração com ele não comprova a vantagem aqui.
Circuitos/fatores também podem servir de backend para os componentes; parsing
gramatical é a especialização implementada, não uma vantagem exclusiva sobre
FactorDLM. O relatório prático deve manter esses limites.
