# Transformação de colisões por um kernel estacionário

Prova escrita candidata. Mecanismos clássicos explicitamente reconhecidos;
este documento não demonstra prioridade acadêmica, publicação, melhora de
pass@1, aceleração ou superioridade geral sobre decoders publicados.

## 1. Operação geral e preservação

Sejam P,Q distribuições num mesmo conjunto finito Y. Sorteie X~P e Y~Q
independentemente. Denote d(x)=P(x)Q(x), D=sum_x d(x). Se D=0, devolva o
par original. Caso contrário, a lei do valor comum, condicionado a X=Y,
é R(x)=d(x)/D. Seja K QUALQUER kernel que preserve R. O algoritmo é:

    se X != Y: devolver (X,Y);
    se X == Y == x: sortear Z~K(x,·); devolver (x,Z).

Não é necessário trocar os rótulos aleatoriamente. O primeiro resultado
fica intacto. Fora da diagonal, a distribuição conjunta nova é

    J(x,z)=P(x)Q(z)+d(x)K(x,z),                 x != z;
    J(x,x)=d(x)K(x,x).

As somas das linhas são P(x). As somas das colunas são
Q(z)-d(z)+sum_x d(x)K(x,z)=Q(z), pela estacionariedade. Isso prova ambas
as marginais. Não há burn-in: a ativação fornece EXATAMENTE o estado inicial
R, não um estado arbitrário que só converge para R.

## 2. Toda pontuação e todo verificador

Para qualquer f:Y→R, a diferença para o momento cruzado independente é

    E_J[f(X)f(Y)]-E_P[f]E_Q[f]
       = D E_RK[f(x)f(z)-f(x)^2]
       = -(D/2) E_RK[(f(x)-f(z))^2] <= 0.       (1)

A última igualdade usa que x e z têm a MESMA marginal R; não precisa de
reversibilidade de K. A covariância nova é, portanto, não positiva, mesmo
quando P != Q. A esperança da média é (P f+Q f)/2, e sua variância diminui
em (D/4) E_RK[(f(x)-f(z))^2] em relação ao par independente.

Para qualquer conjunto E de saídas aceitáveis, sem conhecer E no algoritmo,
tomar f=1_E e usar inclusão/exclusão dá

    pass_J(E)=P(E)+Q(E)-P(E)Q(E)
                  +(D/2) Pr_RK[1_E(x) != 1_E(z)].          (2)

Logo a chance de pelo menos uma saída aceitável nunca diminui. Aplicar (2)
a E={y:f(y)>a} demonstra dominância estocástica do máximo para QUALQUER
pontuação; integrar caudas dá dominância das esperanças quando existem.
O número esperado de saídas distintas também não diminui. Nada disso
afirma que ambas as saídas ficam melhores individualmente.

O sinal favorável é uma forma de Dirichlet clássica, não uma descoberta
nova desse princípio. Um kernel K ruim pode dar ganho zero. Usar uma regra
de número de passos dependente do valor x pode quebrar estacionariedade.
Um número FIXO de passos preserva R, mas não oferece ganho monotônico.

## 3. Referência com uma proposta adicional, sem conhecer D

Não queremos preparar R explicitamente. Seja w_Q(x) um peso racional
não negativo, proporcional a Q(x), com um mesmo fator em todo o suporte.
No caso X=Y=x, necessariamente w_Q(x)>0. Sorteie z~P e aceite com

    alpha(x,z)=min(1,w_Q(z)/w_Q(x)).

Quando rejeita, Z=x. É Metropolis–Hastings independente para R, pois

    d(x) P(z) alpha(x,z)
       = P(x)P(z) min(Q(x),Q(z))
       = d(z) P(x) alpha(z,x).                              (3)

A igualdade também cobre P(z)=0/Q(z)=0 por fluxo zero; estados de R zero
nunca ativam o ramo. As linhas/complementos tornam K um kernel estacionário
para R. Não é preciso calcular P(x), D ou o normalizador de Q.

Substituir (3) em (1)-(2) fornece as identidades exatas

    Cov_J(f(X),f(Y))
       = -(1/2) sum_{x,z} P(x)P(z)min(Q(x),Q(z))
                                         (f(x)-f(z))^2;
    ganho_pass(E)
       = sum_{x in E,z notin E} P(x)P(z)min(Q(x),Q(z)).    (4)

O ganho é estrito se e somente se E e seu complemento contêm elementos
de suporte comum P(x)>0,Q(x)>0. Para P=Q de suporte positivo, TODO
verificador não trivial melhora estritamente. Isso não fornece um limite
inferior grande e independente da distribuição.

## 4. Corolário CFG/dLLM e custo

Considere duas predições produto congeladas de um passo, condicionadas por
uma mesma GLC não ambígua, com slots e IDs originais definidos. Admitem-se
pesos, suportes e clamps diferentes se os samplers individuais preservarem
suas leis e as palavras estiverem num espaço comum de IDs. Não admitir uma
GLC arbitrariamente ambígua contando várias derivações do mesmo evento.
Para uma palavra y, defina

    w_Q(y)=1[y admitida pelo suporte/clamps/gramática Q]
                      * prod_i w_Q[i,y_i].

O fator normalizador cancela em (3). Assim a reparação funciona com o
sampler gramatical P já preparado e pesos por posição de Q. Não é necessário
compilar uma gramática que descreva P·Q, nem enumerar palavras. Se as
restrições Q diferem, a avaliação de admissão/reconhecimento também é um
custo obrigatório. Suporte top-K continua exato SOMENTE nesse suporte;
EOS ausente e demais hipóteses do sampler usado continuam explícitas.

IDs com os mesmos bytes são eventos distintos. Colisão em texto renderizado
não equivale a colisão em IDs; sua lei exige uma outra prova/implementação.
Somar pesos por classes e depois multiplicar suas somas também não calcula
a lei de colisão de IDs: sum_t p_t q_t != (sum_t p_t)(sum_t q_t).

Se S_P/S_Q são custos dos samplers já preparados, L_Q o custo de peso e
admissão e B o tamanho em bits da razão exata, uma chamada ao algoritmo tem
até três draws e custa, incluindo sorteios originais,

    preparo_P+preparo_Q+S_P+S_Q
       + D*(S_P+2L_Q+RNG(B))                               (esperança).

O preço de comparação/armazenamento dos dois IDs completos é O(n); pode
ser feito enquanto os resultados são produzidos, mas não omitido. Pesos
por palavra podem ter O(sum_i bitlen(w[i])) bits, e multiplicações/randrange
dessas larguras não são custo unitário. Um limite conservador da avaliação
de peso é O(n M(B)), além do reconhecedor quando necessário. Preparação
e modelo não somem do custo total porque não aparecem nesse ramo extra.

Não há forward adicional quando os dois samplers compartilham cabeças já
calculadas. Se P é um decoder inteiro que precisa executar novos forwards
para um novo draw, estes entram em S_P. Não esconder a terceira saída:
se validá-la é barato e a aplicação aceita três candidatos, três iid são
um controle necessário, com um orçamento de validação diferente.

## 5. Fronteira da trajetória

Para DUAS execuções da mesma política com horizonte finito, só acople um
passo quando os históricos completos forem idênticos. Nesse grupo P=Q é
o kernel individual completo de ações; K deve implementar o ramo correto
desse kernel. Quando os históricos divergem, use draws independentes e
não reúna históricos só porque seus canvases coincidem.

Defina a(h)=probabilidade de uma execução original falhar no verificador
terminal a partir de h. Por indução de trás para frente, a probabilidade
conjunta de falha após o próximo passo é no máximo E_J[a(hX)a(hY)].
Pela (1), isso é no máximo (E_P[a(hX)])^2=a(h)^2. Nas folhas a vale0/1.
Cada marginal segue a política original por indução. Portanto todo
verificador terminal tem pass@2 pelo menos igual ao iid da MESMA política.

A interpretação inclui uma ação latente completa seguida por uma função
determinística de commitment: tomar f da ação como a chance futura após
essa função conserva (1). Densidade da ação latente não é automaticamente
a densidade da transição observável: não usar somente parte dos tokens
para declarar colisão de ações completas sem outra prova.

Para P != Q com POLÍTICAS FUTURAS DIFERENTES, as duas chances futuras são
f e g diferentes, e (1) não determina o sinal de E[f(X)g(Y)]. Logo o
teorema de um passo NÃO prova automaticamente o resultado terminal de
dois decoders diferentes ou temperaturas que continuam diferentes.
Limites de tempo adaptados à carga/coordenação podem mudar o kernel FAIL;
não recebem preservação incondicional. Nada afirma que EPIC nativo tenha
densidade final produto ou que sua versão determinística passe a ter
diversidade preservando a distribuição delta original.

## 6. Limites e tamanho do ganho

O método não consegue criar uma melhora significativa para qualquer
problema arbitrário. Em P=Q uniforme com N eventos, (4) dá

    ganho_pass(E)=p(1-p)/N,
    Var_J(media)/Var_iid(media)=1-1/N

para qualquer f não constante. O ótimo sem reposição nesse caso tem
fator1-1/(N-1), ligeiramente melhor, conhecido antes deste projeto.
N grande torna ambos os ganhos pequenos; Ren et al.2019 já demonstra
o limite minimax para a referência uniforme. Estratificação de A26 ou
um método antitético competente pode obter ganho maior em certos eventos.
Este documento não oferece dominância sobre esses métodos.

O ponto a investigar é um contrato implícito e heterogêneo, com normalização
desnecessária e intervenção rara. Uma prova de correção desse contrato,
sem diferença científica e magnitude útil, NÃO satisfaz o objetivo atual.

## 7. Limite de QUALQUER reparo que só altera colisões

Esta objeção independe da escolha de MH, do tempo do kernel, de código e de
benchmarks. A marginal de massa alterada é d. Para E qualquer, o fluxo que
pode cruzar de E para fora e vice-versa é limitado por

    ganho_pass(E) <= min(d(E), D-d(E)).

Isso segue da estacionariedade: os fluxos nos dois sentidos são iguais e
cada lado possui no máximo sua massa original de colisões. Para P=Q com
apenas dois eventos de massas1-epsilon e epsilon, epsilon<=1/2, o melhor
reparo possível tem ganho<=epsilon^2. Um acoplamento direto de duas
amostras que preserva P pode atingir ganho epsilon(1-epsilon) para o evento
raro, por evitar redundância também nos pares originalmente não iguais.
Em epsilon=0.01, os limites são0.0001 e0.0099: diferença de99 vezes.

Logo trocar MH por um sampler perfeito de R não resolve o gargalo desta
operação em distribuições concentradas. Em distribuições uniformes amplas,
o limite da seção6 já torna a garantia universal pequena. Estes fatos não
negam utilidade em toda distribuição, mas refutam a ideia de que este
reparo seja automaticamente um protagonista mais forte que métodos
antitéticos competentes. É necessário um uso/diferença científica adicional
antes de uma campanha extensa. Não continuar refinando este ramo apenas
para encontrar um benchmark onde a desigualdade seja visualmente grande.
