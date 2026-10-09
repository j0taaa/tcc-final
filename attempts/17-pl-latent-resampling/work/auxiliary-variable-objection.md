# Objeção de aplicação: réplicas independentes podem ser desnecessárias

Fonte primária conferida: Caron e Doucet, *Efficient Bayesian Inference for
Generalized Bradley–Terry Models*, §4, equações 36–41, pp. 13–14 do manuscrito
[dos autores](https://www.stats.ox.ac.uk/~doucet/caron_doucet_bayesianbradleyterry.pdf)
([publicação de 2012](https://doi.org/10.1080/10618600.2012.638220)). Introduzem
auxiliares exponenciais com taxas dadas pelas somas restantes de PL, tornando
a verossimilhança aumentada fatorável e permitindo Gibbs. O trabalho trata
parâmetros de ranking, não tokens de uma dLLM/GLC. A derivação abaixo é uma
**aplicação inferida nesta auditoria**, não um teorema que os autores enunciaram.

## Redução

Fixados o canvas e a ordem/token-evidência `A`, o alvo é

\[
 \mu_A(y)\propto w(y)\prod_r b_r/(S(y)+c_r).
\]

Introduza tempos `T_r>=0`. A densidade conjunta é proporcional a

\[
 w(y)\prod_r b_r\exp[-(S(y)+c_r)T_r].
\]

Integrar cada tempo recupera exatamente o alvo. As duas condicionais são

\[
 T_r\mid y,A\sim\operatorname{Exp}(S(y)+c_r),\qquad
 y\mid\mathbf T,A\propto w(y)\exp[-(\sum_r T_r)S(y)].
\]

A segunda é uma única reponderação das unárias da floresta gramatical, não
uma proposta que precise corrigir o fator PL completo por rejeição.

## Por que não é obrigatório esperar uma cadeia convergir

Num rollout realmente on-policy, a proposta descartada original `Y_0` já tem
lei `mu_A` **condicionalmente a A**. Portanto sortear `T|Y_0,A` e depois
`Y_1|T,A` é um passo Gibbs iniciado em estacionariedade:

\[
 Y_0\mid A\sim\mu_A\quad\Longrightarrow\quad Y_1\mid A\sim\mu_A.
\]

Não há burn-in nessa afirmação. `Y_1` não é independente de `Y_0` condicionado
a `A`; não se pode atribuir-lhe a fórmula de covariância de réplicas iid.
Mas independência não é necessária para manter a média do score sem viés.

Se `G(Y,A)` é o score completo multiplicado pela recompensa observável,
`G_0,G_1` são condicionalmente iid **dado `(A,T)`**, pelo argumento da conjunta.
Assim, por covariância total,

\[
 \operatorname{Cov}((G_0+G_1)/2\mid A)
 =\tfrac12\operatorname{Cov}(G_0\mid A)
  +\tfrac12\operatorname{Cov}(E[G_0\mid A,T]\mid A)
 \preceq\operatorname{Cov}(G_0\mid A).
\]

A média permanece sem viés e a variância não aumenta, mesmo sem o kernel iid
completo. O ganho pode ser menor que com réplicas independentes; compara-se
custo vezes variância, e não somente a redução estatística ideal.

## Consequência para a decisão científica

A mistura auditada fornece réplicas iid exatas e tem uma garantia uniforme
em bits sobre um circuito racional. A cadeia acima, em primitivas reais ideais,
usaria um conjunto de tempos e uma reavaliação gramatical. Sua implementação
exata requer tratar exponenciais contínuas/irracionais, não simplesmente
chamar `exp` float e anunciar exatidão. Não foi implementada ou medida aqui;
não inventar latência, erro ou benefício neural para esse controle.

Ainda assim, é uma alternativa competente para **a aplicação de redução de
variância em treinamento**. Pode usar aproximações controladas aceitáveis
para uma política neural numérica; sua vantagem/erro também precisam ser
quantificados. Não é lícito dizer que treinamento exige réplicas iid, nem
anunciar o benefício da mistura comparando apenas contra o gradiente original.

A prova contra qualquer produto único continua válida: o passo aumentado usa
uma mistura contínua correlacionada com a amostra original, fora dessa classe.
O resultado não refuta o kernel; impede usá-lo para concluir prematuramente
que se achou o melhor caminho de treinamento. Uma conquista prática completa
exige comparar essa alternativa e o score completo no mesmo rollout, incluindo
normalização, preparo, gradiente e custo neural.
