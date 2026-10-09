# Amostrar exatamente não exige escrever o normalizador exato

Este refinamento explicita o contrato da tentativa 17 e o custo em bits. Não
é uma nova direção de decoder nem reivindicação de primeiro resultado sobre
amostragem versus contagem. Oito critérios: (1) uso é auditar/estimar o posterior
de propostas descartadas após commitments PL em JSON; (2) a obstrução de saída
abaixo fortalece a delimitação matemática, mas não confirma prioridade; (3) o
comparador é qualquer algoritmo obrigado a escrever a fração normalizadora
reduzida, **não qualquer amostrador**; (4) o benefício de dispensar essa saída
segue de prova, com custo completo em bits; (5) a família é objeto de prova,
não benchmark de vantagem; (6) taxas são as próprias probabilidades q, positivas
e moderadas, não prioridades artificiais; (7) rejeição simples já resolve esta
família em tempo polinomial, portanto não é ganho exclusivo da mistura;
(8) para publicar faltam anterioridade/revisão humana e delimitar o resultado
próprio do kernel geral versus este corolário. Não esconder esses antecedentes.

## Enunciado

Há uma família de arrays JSON e predições produto racionais, de descrição
O(m^2) bits, com taxas PL lambda=q e apenas uma posição selecionada, tal que:

1. o denominador reduzido da probabilidade do evento de seleção observado tem
   pelo menos 2^m bits para m>=20;
2. é possível obter uma conclusão latente condicional exata sem calcular esse
   denominador, com esperança de menos de duas propostas de rejeição simples.

Assim, qualquer procedimento que **escreva a fração reduzida desse normalizador**
exige Omega(2^m) trabalho somente para sua saída. Isso não limita representação
simbólica/circuitos, aproximação certificada, amostragem ou outros contratos.

## Construção com taxas de confiança

Use m+1 posições inicialmente livres, cada uma contendo o token original 0
ou 1. Delimitadores/virgulas do array são fixos. Toda conclusão é JSON válido;
uma gramática LL(1) compacta admite todas as escolhas, sem embutir gabarito.
A primeira posição tem q(0)=q(1)=1/2. Nas outras m, indexadas i=0,...,m-1,
ponha C=2^m e

    q_i(0)=(C-2^i)/(2C),   q_i(1)=(C+2^i)/(2C).

Todas essas probabilidades ficam em [1/4,3/4]. Seus numeradores/denominadores
têm O(m) bits, e a entrada completa tem O(m^2) bits. As taxas são lambda=q,
como na seleção por confiança com potência 1, não pesos externos ao modelo.
Observe o evento A: o PL escolheu somente a primeira posição e seu token é 0.

Para bits ocultos y_i, B=sum_i 2^i y_i varia bijetivamente em 0,...,C-1.
A soma das taxas ocultas e a probabilidade de selecionar a primeira posição são

    S=((m-1)C+1+2B)/(2C),
    f(S)=(1/2)/(S+1/2)=C/(mC+1+2B).

Escreva W_B=prod_i(C+(2y_i-1)2^i), K=mC+1 e U=(m+2)C-1. Como a primeira
posição tem probabilidade de token 1/2 e a massa gramatical é 1,

    P(A) = [1/(4(2C)^(m-1))] * sum_{B=0}^{C-1} W_B/(K+2B).

Este é precisamente o normalizador do posterior PL, não uma distribuição
sem ligação com a regra de seleção da dLLM. A construção trata uma predição
produto congelada; não afirma que um checkpoint produz esses números.

## Divisores primos que não cancelam

Para m>=2, todo primo p em [K,U] é ímpar e aparece como exatamente um dos
K+2B: a sequência percorre todos os ímpares do intervalo e U<2K. Cada fator
de W_B é positivo e no máximo 3C/2, menor que p. Portanto p não divide W_B.

Se L é o MMC dos denominadores K+2B, o numerador comum é
sum_B W_B L/(K+2B). Reduzindo módulo p, todos os termos salvo aquele de
K+2B=p desaparecem. O restante W_B L/p não é zero módulo p, pois p^2 não
divide L e p não divide W_B. Logo p permanece no denominador reduzido.
O prefator 1/(4(2C)^(m-1)) só acrescenta potências de 2 e não remove p.

O denominador reduzido D de P(A) é, portanto, divisível pelo produto de todos
os primos desse intervalo. Com theta(x)=sum_{p<=x} log p,

    log D >= theta(U)-theta(K-1).

Usamos um resultado conhecido, não provado pelo projeto: [Dusart (2010),
Teorema 5.2, tabela k=2, eta=0,2, x0=3.594.641](https://arxiv.org/pdf/1002.0442),
p. 4, fornece |theta(x)-x| <0,2 x/(log x)^2 para x>=x0. O original foi conferido.
Para m>=20 ambos os argumentos excedem x0, e log(K-1)>=m log 2>=m/2.
Como U+K-1<(2m+2)C<=4mC,

    theta(U)-theta(K-1)
      >= 2C-1 - 0,2*(U+K-1)/(log(K-1))^2
      >= 2C-1 - 3,2 C/m
      >= C.

Logo log_2 D >= C/log 2 > C=2^m. Escrever D em binário exige mais de 2^m bits.
Esse lower bound é incondicional dado o resultado clássico citado; não usa
benchmark, hipótese de Riemann, conjectura de complexidade ou número de caminhos
como substituto de uma análise em bits.

## Amostragem polinomial e o controle que também a obtém

A proposta produto gramatical condicionada ao token observado custa O(m)
operações com O(m)-bit probabilidades. As taxas ocultas satisfazem

    L=((m-1)C+1)/(2C),   H=((m+1)C-1)/(2C).

Use majorante f(L), avalie f(S) exatamente e aceite com f(S)/f(L). A lei aceita
é exatamente mu_A; a esperança de propostas é no máximo

    f(L)/f(H) = ((m+2)C-1)/(mC+1) < 2.

A moeda tem numerador/denominador O(m) bits. O custo esperado em bits é
polinomial, apesar de D ter tamanho exponencial. A mistura da tentativa também
funciona, mas o controle simples é preferível aqui. Não alegar exclusividade.

O motivo para manter o kernel geral vem de **outro** resultado:
[separação contra qualquer produto único](product-proposal-separation.md).
Ele fornece a garantia uniforme relativa ao circuito nos casos em que rejeição
por produto perde seu limite polinomial. Juntar os resultados delimita melhor
as operações: posterior gramatical produto; posterior PL não fatorado;
amostragem condicional exata; normalizador exato; estimação com precisão.
Nenhum deles deve ser confundido com melhora semântica da geração inteira.
