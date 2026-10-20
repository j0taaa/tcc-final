# A80 — prova escrita e limites

Esta prova matemática recebeu revisão de subagentes em R25 e R26. Isso não é
revisão humana, Lean, auditoria de software ou prova de prioridade. A realização
numérica e os experimentos têm obrigações adicionais no [protocolo](README.md).

## Projeção e canal declarado

Seja `L` finito público, `mu(x)>0`, `sum mu=sum P=1`, admitindo zeros de `P`.
Fixe `R>1`, `b=log R`, `a in [1/R,1]`. Escreva

\[
c_a=\operatorname{clip}(P,a\mu,Ra\mu),\quad Z(a)=\sum c_a,
\quad Q_a=c_a/Z(a),
\quad\mathcal C_R=\{q:q(x)\mu(y)\le Rq(y)\mu(x)\}.
\]

`Z` é contínua e crescente, `Z(1/R)<=1<=Z(1)`. Portanto existe uma raiz `a*`.
Monotonicidade componente a componente mostra que quaisquer raízes dão o mesmo
vetor `q*=c_a*`. Esse vetor minimiza `KL(P||q)` em `C_R`. Uma prova KKT usa
`lambda=1`, `alpha=(1-P/q*)_+`, `beta=(P/q*-1)_+`; a estacionariedade em `a`
é `(sum q* - sum P)/a*=0`. Positividade de `q*` cobre zeros de `P`.

Todo `Q_a` pertence a `C_R`, mesmo para um `a` privado mal estimado. A classe é
convexa, pois suas desigualdades são lineares. Para duas leis nela,

\[
\operatorname{osc}_x\log\frac{q(x)}{q'(x)}\le2\log R.
\]

Logo o canal entre quaisquer prompts é `2b` bounded-range e `2b`-DP, se somente
a palavra final for liberada e o mecanismo total permanecer nessa classe.
Projeção por clipping, mollifiers e esse princípio de privacidade são
[antecedentes](https://proceedings.mlr.press/v108/husain20a.html).

## Lema global de Bernstein

Seja `rho=(P+mu)/2`, `r=P/mu`, `tau=log a`,

\[
g_\tau=\frac{2[\operatorname{clip}(r,e^\tau,Re^\tau)-r]}{1+r}.
\]

Temos `|g|<=2` e `E_rho g=Z-1`. Uma primitiva finita individual `ell_tau`
é convexa. Ponha `Psi=E ell`, `Delta=Psi(tau)-Psi(tau*)`. Quase em toda parte,

\[
\Psi'=Z-1,\qquad\Psi''=Z-P_M,\quad
\frac{d}{d\tau}\mathrm{KL}(P\|Q_{e^\tau})
=\frac{P_M}{Z}(Z-1),
\]

onde `P_M=P{e^tau<r<Re^tau}`. Como `0<=P_M/Z<=1`, a integração em ambos os
lados da raiz dá excesso KL no intervalo `[0,Delta]`. Átomos nos breakpoints
são tratados por continuidade e derivadas laterais.

O lema candidato próprio é

\[
E_\rho(\ell_\tau-\ell_{\tau^*})^2\le(16+8b)\Delta(\tau).
\tag{1}
\]

Para prová-lo, escreva `c*=clip(r,a*,Ra*)` e

\[
d=E_\mu(c^*-r)_+=E_\mu(r-c^*)_+,
\quad E_\rho g_*^2\le4d.
\]

A última desigualdade usa `|c*-r|<=1+r`. Além disso,
`d<=A=a* mu{r<a*}` e `d<=B=P{r>Ra*}`.

À direita, `t=tau-tau*>=0` e `h=ell_tau-ell_* = t g_*+u` satisfazem
`0<=u<=4b`, `E u=Delta`. A cauda inferior da raiz permanece inferior, logo
`Delta>=A(e^t-1-t)>=At^2/2`. Portanto

\[
E h^2\le2t^2E g_*^2+2E u^2\le16\Delta+8b\Delta.
\]

À esquerda, `s=tau*-tau`, `kappa=1-exp(-s)`. O clipping é 1-Lipschitz e
homogêneo, o que dá `g_(tau*-v)<=exp(-v)g_*`. Assim,
`h=-kappa g_*+k`, com `0<=k<=4b`, `E k=Delta`. Na cauda superior original,
`E[k 1_H]=B(s-kappa)`. Como `kappa^2<=2(s-kappa)`,

\[
\kappa^2E g_*^2\le4B\kappa^2\le8\Delta,
\quad E h^2\le16\Delta+8b\Delta.
\]

Isso prova (1), inclusive quando `d=0` e a raiz pertence a um platô. Não há
hipótese de curvatura mínima nem exp-concavidade de cada observação.

## Garantia finita de calibração

Defina `D_b=32+56b/3`. Num ponto determinístico com `Delta=xi`, temos
`|h|<=2b`, `|h-Eh|<=4b`, `Var h<=(16+8b)xi`. Bernstein dá probabilidade no
máximo `exp(-M xi/D_b)` para diferença empírica não positiva.

Em cada lado da raiz, fixe previamente o primeiro ponto de nível `Delta=xi`,
se existir. Se o ERM ultrapassá-lo, convexidade força diferença empírica não
positiva nesse ponto. São dois eventos, sem união sobre o limiar escolhido.
Para erro empírico de no máximo `xi/4`, uma constante conservadora é

\[
M\ge\frac{2D_b}{\xi}\log\frac2\beta
\quad\Longrightarrow\quad
\Pr\{\Delta(\widehat\tau)>\xi\}\le\beta.
\tag{2}
\]

Essa é uma garantia para `Delta`, que também controla excesso KL. A análise
clássica de ERM sob Bernstein é ferramenta utilizada; o trabalho específico de
(1) não é atribuído a essa ferramenta.

## Realização comprimida

Use `gamma=P/(P+mu)`. O score torna-se

\[
g_a(\gamma)=2[\operatorname{clip}(\gamma,a(1-\gamma),Ra(1-\gamma))-\gamma].
\]

Ele é contínuo e tem inclinações em `gamma` de módulos no máximo `2(R+1)`.
Quantizar `gamma` numa grade uniforme com erro `<=1/Q` dá erro uniforme de
score `delta<=2(R+1)/Q`. Integrar entre os dois minimizadores, em vez de
comparar cada um com uma origem, limita a suboptimalidade empírica por
`b delta`. Assim `Q=ceil(32(R+1)max(1,bar_b)/xi)`, com `bar_b>=b`, basta em (2).

Uma grade diádica alternativa usa `h=ceil(log2(R+1))` e
`m=ceil(32 max(1,bar_b)/xi)`: subdividir cada faixa de `t=1-gamma`,
`[2^(-k-1),2^(-k)]`, e a cauda `[0,2^-h]` em `m` partes. Seus
`m(h+1)+1` pontos têm denominador comum `D=m 2^h`. A variação do score em uma
célula é no máximo `2/m`, dando o mesmo erro empírico `<=xi/16`.

Para bins `gamma_j=u_j/D` com contagens `N_j`, o score entre breakpoints é

\[
\widetilde F(a)=\frac2{MD}[a(S_L+RS_U)-T].
\]

`S_L=sum_lower N_j(D-u_j)`, `S_U=sum_upper N_j(D-u_j)` e
`T=sum_active N_j u_j`. Os eventos são `a=r_j` e `a=r_j/R`,
`r_j=u_j/(D-u_j)`. Intercalar suas listas ordenadas e atualizar os três
acumuladores encontra raiz ou platô exatamente. Para `R=RN/RD`, a raiz é
`RD*T/(RD*S_L+RN*S_U)`.

Na fronteira inicial é obrigatório representar o trecho à direita: inferior
com `r_j<=1/R`, superior com `r_j>1`. Empates são processados conjuntamente.
Bins `gamma=0` e `gamma=1` contribuem `2a` e `-2`, sem breakpoint finito.
Se não existe raiz empírica, devolver a fronteira ótima restrita.

Acumuladores e raiz precisam de `O(bits(R)+log M+log D)` bits. O estado de
contagens usa `O(H log(M+1))` bits, mais samplers e um operando transitório.
A coleta ainda paga **M palavras completas e avaliações de probabilidades**.
Contagens, índices compactados e resumos de quantis são controles legítimos;
uma CDF a erro `eta` altera este score monótono de variação `<=4` por `<=4eta`.

## Emissão e garantia marginal

Use propostas novas de `rho`, aceite por `c_a/(P+mu)` e, após `K` falhas,
retorne uma amostra fresca de `mu`. A lei condicional é
`S_a=(1-t_a)Q_a+t_a mu`, `t_a=(1-Z(a)/2)^K`. Toda calibração e toda mistura
dessas leis ficam em `C_R`.

Como `0<=Psi''<=2`, `|Z-1|<=2 sqrt(Delta)`. Para garantia marginal de excesso
KL `zeta<=1/4`, usar `xi=zeta/4`, `beta=zeta/8` em **todos** os parâmetros e

\[
M\ge\frac{8D_b}{\zeta}\log\frac{16}{\zeta},\qquad
K\ge\frac{\log(8/\zeta)}{\log(2/(1+\sqrt\zeta))}.
\]

A lei boa tem fallback no máximo `zeta/8`; a mistura ruim custa no máximo
`-log(1-beta)`. Convexidade fornece excesso marginal no máximo
`zeta/4-2log(1-zeta/8)<=zeta`. Isso não é a esperança de KL condicionada à
calibração, nem o orçamento menor do desenvolvimento V1.

O envelope melhor `c_a<=(1-1/R)P+a mu` conserva `Q_a` e melhora a aceitação.
Deve ser concedido aos controles. Emissão racional exata exige bits IID no
modelo matemático, com término quase certo; a prova não autoriza abortos
dependentes da palavra durante rejeição.

## Separação e limites científicos

A mediana com uniforme auxiliar pode necessitar `Omega(xi^-2)` amostras para
**excesso KL condicional com alta probabilidade**. Para `R=2`, `p<=1/100`, use
`mu=(5p,1-6p,p)` e `P=(5p/3,1-14p/3,3p)`. A raiz é `2/3`; em `a=5/6`,

\[
Z=1+7p/6,\quad
\mathrm{KL}(P\|Q_a)-\mathrm{KL}(P\|q^*)
=\log(1+7p/6)-(14p/3)\log(5/4)>p/10.
\]

A CDF usada pela mediana vale `1/2+7p/12` nesse ponto. Para `M` ímpar no máximo
`1/(100p^2)`, comparação binomial por Pinsker dá probabilidade de erro maior
que `0.4`. Isso é lower bound **da mediana**, não de todos os calibradores,
nem da KL marginal dos protocolos finais misturados.

SAA/ERM competente usa o mesmo lema e a mesma taxa. MetaGrad pode usá-lo para
taxa em esperança com estado pequeno. Resumos de quantis podem superar o
histograma denso. Não há alegação de amostragem ótima, necessidade universal de
calibrar ou novo princípio de privacidade.

Finalmente, para evento útil `A`, toda lei em `C_R` satisfaz
`q(A)<=R mu(A)/(1+(R-1)mu(A))`. A utilidade absoluta depende da referência.
Uma GLC fornece samplers implícitos, mas isso não comprova competência de um
head congelado nem qualidade semântica de um dLLM. Essas pendências permanecem.
