# A81 — Prova escrita V1

Origem: construção do root nas rodadas R30–R31, revista independentemente
pelo subagente R31-B em 20/10/2026. A cobertura angular mais forte e a
correção conjunta da revisão estão incorporadas abaixo. Atribuições,
operação, consumidor e limites científicos ficam no [contrato](README.md).
Esta é prova escrita; não é especificação Lean ou verificação de software.

## 1. Envelope universal positivo

Sejam beta racional, beta >= 1, e t1,t2 >= 0. Escreva f=t1+t2.
Todos os logaritmos são naturais. Para p em [0,1], defina

$$
H(p)=-p\log p-(1-p)\log(1-p),\qquad
h_p=e^{\beta H(p)}t_1^{\beta p}t_2^{\beta(1-p)}.
$$

Usamos 0 log 0 = 0 e fatores com expoente zero iguais a 1.
Quando f>0 e q=t1/f, a definição de KL binária fornece

$$
h_p/f^\beta=e^{-\beta D(p\|q)}.
\tag{1}
$$

Nos extremos a identidade usa os limites correspondentes.

Defina inteiramente por comparações racionais

$$
J=\min\{j\in\mathbb N:j^2\ge4\beta\},\qquad
p_j=\frac{4j^2J^2}{(J^2+j^2)^2},\quad j=0,\ldots,J.
$$

Se L=soma h_pj e E=3L, então

$$
\boxed{f^\beta\le E<19f^\beta\quad(f>0),\qquad R=J+1.}
\tag{2}
$$

Para f=0, E=0. Os extremos do grid garantem suporte quando somente
um componente é positivo.

### Cobertura

Use somente na prova theta_j=2 arctan(j/J). Temos p_j=sin²(theta_j).
A derivada de 2 arctan(u), para u em [0,1], pertence a [1,2].
Assim, os espaçamentos angulares estão entre 1/J e 2/J.

Para q em (0,1), ponha theta=arcsin(sqrt(q)) e escolha o theta_j mais
próximo, com desempate fixo. Escreva d=|theta_j-theta|. A presença dos
extremos e o espaçamento máximo dão

$$
d\le1/J,\qquad d\le\min(\theta,\pi/2-\theta).
\tag{3}
$$

Considere F(psi)=D(sin²(psi)||sin²(theta)). No interior,

$$
F'(\theta)=0,\qquad
F''(\psi)=4+2\cos(2\psi)
\log\frac{\tan^2\psi}{\tan^2\theta}.
$$

Se o segundo termo é positivo com psi <= pi/4, então
theta <= psi <= 2 theta ao longo do segmento em (3). Consequentemente,

$$
\frac{\tan\psi}{\tan\theta}
\le\frac{\tan\psi}{\tan(\psi/2)}
=1+\sec\psi\le1+\sqrt2<e.
$$

Isso implica F''<8. O caso positivo no semiquadrante superior segue
substituindo os dois ângulos por seus complementos. Nos demais casos
o segundo termo não é positivo e F''<=4. Integrando e usando F(theta)=0,
obtemos F(psi)<=4(psi-theta)². A continuidade inclui as âncoras extremas.
Logo,

$$
D(p_j\|q)\le4/J^2\le1/\beta,\qquad L/f^\beta\ge e^{-1}.
\tag{4}
$$

### Sobreposição

A desigualdade KL–Hellinger dá, com psi=arcsin(sqrt(p)),

$$
D(p\|q)\ge-2\log\cos(\psi-\theta)\ge(\psi-\theta)^2.
\tag{5}
$$

Qualquer intervalo de comprimento l contém no máximo 1+Jl pontos
theta_j. Integrando os conjuntos de nível da função Gaussiana:

$$
\begin{aligned}
\sum_j e^{-\beta(\theta_j-\theta)^2}
&=\int_0^1\#\{j:e^{-\beta(\theta_j-\theta)^2}>u\}\,du\\
&\le1+2J\int_0^1\sqrt{\log(1/u)/\beta}\,du\\
&=1+J\sqrt{\pi/\beta}.
\end{aligned}
$$

Como J<=3 sqrt(beta), (1), (4) e (5) implicam

$$
f^\beta\le3L\le(3+9\sqrt\pi)f^\beta<19f^\beta.
$$

Isso prova (2). Em t1=0 ou t2=0, E=3 f^beta por inspeção.

## 2. Compilação gramatical

Seja G um domínio finito com plano acíclico e derivação única por palavra
de IDs originais. Suponha

$$
t_j(x)=a_j
\prod_r\theta_{jr}^{\nu_r(x)}
\prod_i b_{j,i}(x_i)w_i(x_i),\quad j=1,2.
$$

As contagens nu_r pertencem à mesma derivação, inclusive para os dois
componentes. Então h_p é calculado no mesmo plano, com coeficiente
e^(beta H(p)) a1^(beta p) a2^(beta(1-p)), pesos de regra

$$
\theta_{1r}^{\beta p}\theta_{2r}^{\beta(1-p)}
$$

e pesos posicionais

$$
b_{1,i}(x_i)^{\beta p}
b_{2,i}(x_i)^{\beta(1-p)}w_i(x_i)^\beta.
$$

Portanto, cada âncora exige uma reponderação, não uma interseção de charts.
O fator comum w_i elevado é compartilhável. Zeros permanecem zeros quando
o expoente é positivo; o suporte do envelope coincide com o do alvo.

Esta redução não vale automaticamente para estruturas com vários
testemunhos por palavra. Somar derivações e depois elevar não equivale
a elevar o peso de cada derivação e somar.

## 3. Correção conjunta local

Seja sigma(x) a âncora angular mais próxima de q(x)=t1(x)/f(x).
As fronteiras são racionais:

$$
b_j=\sin^2\frac{\theta_j+\theta_{j+1}}2
=\frac{J^2(2j+1)^2}
{(J^2+j^2)(J^2+(j+1)^2)}.
$$

É suficiente buscar q nas fronteiras por comparações racionais. Nos
extremos q=0 ou 1, sigma seleciona a âncora extrema correspondente.
O desempate nas fronteiras é determinístico.

Prepare funções fatorizadas racionais e_j com zeros preservados e

$$
3h_{p_j}(x)\le\widehat e_j(x)\le3\eta h_{p_j}(x),
\qquad \eta\ge1.
$$

O alvo tem massa Z_beta>0. Calcule Z_j=soma_x e_j(x) e Zhat=soma_j Z_j.
Escolha j com probabilidade Z_j/Zhat, ignore componentes de massa zero,
e sorteie x pelo chart j. Aceite o par com probabilidade

$$
\alpha(j,x)=1_{\{j=\sigma(x)\}}\,
\frac{f(x)^\beta}{\widehat e_j(x)}.
\tag{6}
$$

A cobertura (4) e 3/e>1 asseguram alpha<=1 na região selecionada.
A massa proposta aceita de (j,x) é

$$
\frac{\widehat e_j(x)}{\widehat Z}\alpha(j,x)
=\frac{1_{\{j=\sigma(x)\}}f(x)^\beta}{\widehat Z}.
$$

Somar em j deixa f(x)^beta/Zhat. Logo, após rejeições independentes,
o x aceito tem lei Q_beta, e

$$
\mathbb E N=\widehat Z/Z_\beta<19\eta.
\tag{7}
$$

A seleção de região custa O(log R) comparações. Cada tentativa avalia
os dois pesos originais e somente a parcela proposta. Nenhum chart
precisa representar as regiões sigma.

Com teto público T de tentativas independentes, a probabilidade de
não aceitar é no máximo exp(-T/(19 eta)). Se for emitido um fallback
válido nesse evento, essa é também uma cota de TV. Emitir FAIL é outro
contrato. Interrupção dependente da execução não recebe esse limite
automaticamente.

## 4. Realização racional e aleatoriedade

Para a realização racional geral, escolha eta>1 racional. O caso eta=1
da seção anterior pressupõe fatores já exatos; não exige que todo fator
irracional tenha representação racional exata.

Os p_j e expoentes são racionais. Coeficientes e potências podem ser
irracionais, mas os samplers dos charts usam apenas majorantes racionais.
Se cada testemunho tem até D fatores e um coeficiente de raiz, arredonde
cada fator positivo para cima com erro relativo <=delta e escolha
(1+delta)^(D+1)<=eta. Zeros não recebem arredondamento positivo.

Intervalos certificados para log e exp permitem calcular esses majorantes
sem elevar inteiros ao denominador de beta. Para log, reduza z=2^k v,
1<=v<2, e use y=(v-1)/(v+1)<=1/3 na série

$$
\log v=2\sum_{\ell=0}^{m-1}\frac{y^{2\ell+1}}{2\ell+1}
+\text{cauda},\qquad
0\le\text{cauda}\le
\frac{2y^{2m+1}}{(2m+1)(1-y^2)}.
$$

Exp admite redução de argumento, série de Taylor com resto e quadraturas
sucessivas. Refinar até separar o majorante dyádico da tolerância fornece
um procedimento finito. Não se concede uma chamada unitária a um oráculo
real. Não há implementação competitiva dessa rotina preservada nesta V1.

Para a moeda em (6), um intervalo determinístico I_r contendo alpha, de
largura <=2^(-r-2), é comparado à célula dyádica J_r de um uniforme U,
obtida com r bits. Aceite se sup(J_r)<=inf(I_r); rejeite se
inf(J_r)>=sup(I_r); caso contrário refine. Eventos de igualdade entre
U e uma fronteira têm probabilidade zero. As células que encontram I_r cobrem
comprimento no máximo |I_r|+2|J_r|. Assim,

$$
\Pr(T>r)\le\min(1,(9/4)2^{-r}),\qquad \mathbb ET<4.
$$

O resultado é Bernoulli(alpha) exatamente, com término quase certo;
o evento U=alpha tem probabilidade zero. Essa cota conta somente bits
da moeda. A seleção do componente, traceback, escolhas lexicais e custo
de avaliar os intervalos continuam pagos. As técnicas numéricas e a
moeda por intervalos são clássicas, não contribuições separadas de A81.

## 5. Inferior na classe de envelopes

Considere uma fórmula fixa, positiva, válida para todos t1,t2>0:

$$
\widetilde E=\sum_{j=1}^R a_j
t_1^{\beta p_j}t_2^{\beta(1-p_j)},\quad
a_j>0,\quad0\le p_j\le1,\qquad
f^\beta\le\widetilde E\le\rho f^\beta.
$$

Ponha w_j=a_j exp(-beta H(p_j)). Avaliar em q=p_j, por limite nos
extremos, dá w_j<=rho. Por (5), integrando em theta:

$$
\frac\pi2
\le\int_0^{\pi/2}\widetilde E/f^\beta\,d\theta
\le\sum_j w_j\sqrt{\pi/\beta}
\le R\rho\sqrt{\pi/\beta}.
$$

Portanto,

$$
\boxed{R\ge\frac{\sqrt\pi}{2\rho}\sqrt\beta.}
\tag{8}
$$

Em uma soma positiva universal com razão global limitada, a variação de
escala dos dois argumentos força todo termo não nulo a ter grau total
beta. Expoentes negativos causariam divergência na fronteira. Assim,
essas formas alternativas não evitam (8) dentro da mesma classe positiva.
O resultado não é um inferior para qualquer sampler ou para uma
gramática/entrada específica.

Há uma consequência para aproximações universais: se uma fórmula positiva
homogênea fixa deve, depois de normalizada, garantir TV<=epsilon<1 para
todo domínio finito e toda atribuição positiva, sua razão relativa global
é no máximo

$$
\kappa_\varepsilon=
\left(\frac{1+\varepsilon}{1-\varepsilon}\right)^2.
$$

De fato, dois valores relativos a<b, com massas alvo escolhidas por
reescala independente dos dois átomos, atingem
(sqrt(b)-sqrt(a))/(sqrt(b)+sqrt(a)) de TV. Tomando ínfimo e supremo,
obtemos a razão acima. Reescalar a fórmula e aplicar (8) fornece
Omega(sqrt(beta)/kappa_epsilon) termos. A conclusão não cobre
aproximações adaptadas à entrada, coeficientes com sinais ou outras
representações.

## 6. Alcance de complexidade

Com R charts de mesmo tamanho S e larguras de mensagens comparáveis,
há O(sqrt(beta)) preparações, contra Theta(beta) da expansão por
réplicas para dois componentes. Para eta fixo, ambas têm uma cota
constante de propostas. Isso prova uma melhora assintótica de quantidade
de charts e armazenamento dessa compilação.

Não se conclui a mesma razão para segundos ou custo total. Em representação
racional convencional, fatores podem ter ordem beta B0 de bits, para
entradas de B0 bits; mensagens dependem ainda de D e da quantidade de
palavras. Custos numéricos, seletores, cabeça neural, memória e saída
integram o contrato. Secantes, histogramas, regiões e aproximações
certificadas podem vencer em entradas particulares. Nem esta prova nem
seus oráculos estabelecem prioridade científica ou desempenho de modelo.
