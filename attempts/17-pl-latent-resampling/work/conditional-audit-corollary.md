# Corolário de aplicação: auditoria condicional com precisão declarada

Este resultado escrito conecta a lei auditada a uma operação concreta. Não é
novo princípio de Monte Carlo, prova de prioridade na literatura ou vantagem
sobre todos os amostradores. A separação distintiva continua sendo a da
[prova contra produto único](product-proposal-separation.md).

## Operação

Um gerador dLLM/GLC registra a predição congelada, suporte, canvas, commitments
e ordem da seleção PL, mas não conserva a proposta completa descartada.
Um auditor pergunta pela probabilidade de uma alternativa latente, ou outra
estatística h(Y) em [0,1], **condicionada à decisão que foi observada**. Condicionar
apenas aos tokens observados não fornece essa lei: a chance de selecionar as
posições também depende dos tokens que foram descartados.

O posterior aqui é de um passo, não probabilidade semântica da resposta final.
O suporte e as taxas são os declarados; o auditor não descobre massa omitida
nem a verdadeira intenção do usuário. Uma pergunta possível é "com que
probabilidade esta posição descartada continha o token alternativo v, dadas
as prioridades e decisões deste passo?". Isso serve para analisar/calibrar a
política de commitment, não substituir um decoder ou um teste de software.

## Garantia

Admita o circuito de tokens determinístico/decomponível da nota, probabilidades
e taxas racionais positivas, evidência viável e moedas uniformes independentes.
A preparação foi concluída. Seja J o número de componentes e M=2J+1; nos casos
constantes, M=1. O kernel produz amostras iid do posterior mu_A, e cada saída
exige esperança de no máximo M propostas. J=O(sqrt(k) log kappa), com kappa
=(H+c_min)/(L+c_min); a análise em bits inclui as unárias/coeficientes dyádicos,
reponderação da floresta e preparação. Não é limite polinomial da normalização
de uma gramática arbitrária não admitida; é relativo ao circuito disponível.

Para N saídas e erro epsilon, Hoeffding dá

    P(|N^(-1) sum_j h(Y_j) - E_mu_A[h]| > epsilon)
      <= 2 exp(-2 N epsilon^2).

Além disso, existe uma versão com limite determinístico B de propostas que
recusa explicitamente quando o limite acaba. Se T é o total de propostas até
N saídas, E[T]<=NM e P(T>B)<=NM/B por Markov. Escolhendo B=ceil(40 NM) e
N=ceil(log(80)/(2 epsilon^2)), a probabilidade de completar **e** atingir o erro
desejado é pelo menos 0,95. Para N=1024, epsilon=sqrt(log(80)/2048)<0,0463.
Este número é para **uma** estatística definida; várias estatísticas exigem
alocar a probabilidade de erro entre elas. Não prometer simultaneidade sem isso.

A versão por limite de propostas é um algoritmo matemático; o replay mede a
versão com relógio. Não foi adicionado um certificado estatístico de 95% aos
resultados cronometrados. Um timeout dependente dos sorteios NÃO preserva
necessariamente a lei condicionada à conclusão antes do prazo.

## Por que o limite de propostas não seleciona respostas favoráveis

Fixados proposta nu e moeda a(y), escreva p=sum_y nu(y)a(y). Para uma saída,

    P(T=t,Y=y)=(1-p)^(t-1) nu(y)a(y)
             =P(T=t) mu_A(y).

Assim o número de propostas é independente da saída aceita. Para N saídas,
a mesma fatoração mostra que a sequência de números de propostas é independente
de todas as saídas. Completar antes de **B propostas**, portanto, não altera
a lei das N saídas. Uma implementação precisa interromper pelo número de
propostas, não fingir que o relógio, memória dinâmica ou sorteios de caminhos
são independentes das respostas. A contagem rejeitada é recurso, não
inviabilidade da evidência. A análise usual do gerador uniforme de inteiros
é em esperança de bits aleatórios; não é prazo físico absoluto de hardware.

## Comparação e limite da relevância

Com uma proposta produto única, a família escrita no documento vinculado
pode exigir Omega(exp(m/360)) propostas por saída, mesmo escolhendo o melhor
produto assimétrico. A mistura fornece a operação acima com custo esperado
polinomial relativo ao circuito. Esse benefício comparativo independe de
benchmark. Um algoritmo especializado que agrega somas pode ser polinomial
nessa família; o resultado não o exclui e não justifica ignorar esse controle.

Se Y0 foi conservado de um rollout on-policy, MH/Gibbs pode começar na lei
estacionária e obter uma réplica correlacionada sem burn-in. Isso é especialmente
relevante no treinamento. Quando Y0 não está disponível, uma inicialização
arbitrária não tem essa garantia após um passo: detalhamento balanceado não
significa convergência instantânea. Ainda é possível usar MCMC com uma análise
de mistura adequada; independência exata é uma escolha de contrato, não
necessidade universal. Recuperar Y0 por replay de uma semente, quando possível,
também deve ser considerado pelo usuário da operação.

Se a enumeração cabe, prefira-a quando for mais barata; fornece até a média
condicional exata e evita erro Monte Carlo. A campanha externa pequena fez
exatamente essa comparação. O corolário mostra um uso matematicamente válido
do kernel e explicita sua precisão, mas não estabelece que ele seja a melhor
solução prática, que melhore geração final ou que seja uma novidade publicável.
