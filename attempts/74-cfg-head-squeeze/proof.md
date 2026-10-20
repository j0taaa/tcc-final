# A74 — Derivação e ataque independente

## Lei e consultas

Seja G um conjunto finito de tuplas de IDs originais de comprimento n, não
uma coleção de árvores. Defina f(x)=prod_i f_i,xi e Zf=sum_G f(x).
Assuma w_i,a>0, 0<=L_i,a<=w_i,a<=U_i,a, ZU>0 e acesso exato à amostra U/ZU.
Como L(x)<=w(x)<=U(x), o squeeze é subconjunto da aceitação de referência.
Com o MESMO v uniforme, a massa de propor e aceitar x é

    U(x)/ZU * w(x)/U(x) = w(x)/ZU.

Logo cada sucesso tem lei w/Zw e repetir dá essa lei, com probabilidade de
aceitação p=Zw/ZU>0. A normalização original por posição cancela; esta
operação não calcula a massa válida no produto softmax original.

Por tentativa a probabilidade de consulta é q=1-ZL/ZU. Renovação dá
E[N]=1/p e E[C]=q/p=(ZU-ZL)/Zw, mesmo correlacionando C com aceitação.
Se ZL>0, R=ZU/ZL limita E[N]<=R e E[C]<=R-1. Consultar todas as n linhas
quando acionado dá E[rows]=n E[C], ou <= com cache/curto-circuito. Se
ZL=0, R é infinito, mas as identidades com Zw continuam válidas.
O evento "alguma consulta antes do output" equivale a falhar o PRIMEIRO
squeeze: se passar, encerra; se falhar, já houve consulta. Portanto sua
probabilidade é q, não E[C]. Estas fórmulas não incluem fallback denso.

Um cap fixo J seguido de amostra densa INDEPENDENTE exata dá, para cada x,

    sum_{j=0}^{J-1}(1-p)^j w(x)/ZU + (1-p)^J w(x)/Zw = w(x)/Zw.

J=0 também vale. Cada ramo de sucesso tem a mesma lei; escolher devolver
somente outputs sem referência, porém, dá L/ZL e costuma enviesar. Exemplo
n=1, G={a,b}, L=(1,1), w=(1,2), U=(2,2): sem consultar, sucesso uniforme;
alvo=(1/3,2/3). Deadline dependente do candidato pode censurar a lei. FAIL
é inconclusivo e não é uma amostra alvo.

## CFG e controle competente

Para cada c em {0,1}, terminais A_c e B_c (com m aliases originais livres):

    S_c -> A_c T_c B_c S_c | B_c U_c A_c S_c | epsilon
    T_c -> A_c T_c B_c T_c | epsilon
    U_c -> B_c U_c A_c U_c | epsilon

A raiz escolhe c pela primeira excursão NÃO vazia, expandindo as duas
produções não vazias de S_c, sem duas alternativas epsilon na raiz.
T é Dyck positivo e U sua reflexão. Cada palavra balanceada de S se
decompõe unicamente no primeiro retorno ao saldo zero, e recursivamente
nas duas partes. Isso prova cobertura e uma árvore por palavra. FIRST
das alternativas não vazias são distintos; FOLLOW(T)={B_c},
FOLLOW(U)={A_c}, FOLLOW(S)={fim}; logo a versão descrita é LL(1).
Epsilon fica fora do consumidor n>=2. A raiz ingênua S0|S1 daria duas
árvores da palavra vazia: não usar em n=0.

Há 2 binom(n,n/2) m^n tuplas originais para n par positivo. O controle
agrega as quatro classes por posição e usa DP de contagens O(n²), depois
amostra o ID dentro da classe proporcionalmente ao seu peso. Aliases
não são deduplicados. Os testes comparam esse DP à enumeração e um parser
independente que conta derivações, sem reutilizar a recorrência de contagens.
Rejeitar propostas uniformes independentes tem massa válida
2 binom(n,n/2)/4^n=Theta(2^-n/sqrt(n)); isso derrota esse controle fraco,
não LazyGumbel associado ao mesmo DP nem todos os métodos de MIPS.

## Kernel racional e regime positivo construído

Seja 0<delta<=1/4, b=ceil(log2(40n/delta)), K=b+4,
P_K(t)=sum_{k=0}^K t^k/k!, E_b(t)=2^-b floor(2^b P_K(t)).
Em [-1,1], P'_K=P_{K-1}>0: para t negativo, agrupar pares da série
alternante prova positividade. Logo E_b é monótono (não estritamente).
O resto de Taylor é <=3/(K+1)!, e a quantização adiciona <2^-b. Para
b>=8, e*(3/(b+5)!+2^-b)<=4*2^-b. Assim E_b é positivo e o erro relativo
contra exp é <=alpha=4*2^-b<=delta/(10n). Exatidão é com relação a E_b,
não exp ideal nem torch.exp. A grade testada não prova esta desigualdade
universal; o argumento analítico é a evidência escrita.

Construa W_v=beta_j e1+E_v, |beta_j|<=1, ||E_v||2<=delta/n,
||h_i||2<=1 e |h_i1|<=1/(2n). Então q=beta_j h_i1 e
|ell-q|<=delta/n. Tanto ell quanto q+-delta/n pertencem a [-1,1].
Limites E_b(q-delta/n), E_b(q+delta/n) são válidos e positivos.
Para cada fator,

    log(U/L) <= 2delta/n + log((1+alpha)/(1-alpha)).

Como alpha<=delta/(10n)<=1/80, log((1+alpha)/(1-alpha))<=4alpha,
portanto log(U(x)/L(x))<=2.4delta e R<=exp(2.4delta).
Isso funciona mesmo com resíduos densos genéricos; não é igualdade de logits
entre aliases. Não demonstra que um head aprendido tenha essa geometria.

Com pesos dyádicos escala 2^b, chart de comprimento n tem O(n(b+log V))
bits por inteiro. DP usa O(n²) operações aritméticas, cujo custo M(B) e
RNG inteiro devem contar. Para logits racionais de B bits, avaliar Taylor
exatamente também custa polinômio em B,K; "polylog" exige denominadores de
bits polylog no parâmetro, não entradas reais gratuitas. Retendo fatores
conhecidos, V=t^8,d=t^4,n=t, backbone de profundidade fixa custa O(t^9),
preparar resíduos por varredura custa O(t^12), proxy custa O(t^9) por estado,
head denso O(t^13). É separação em modelo aritmético condicionado, não
lower bound universal de circuitos nem medição CUDA.

## Limites, gauge e triagem

G={0^n,1^n}, U0=U1=L0=1, L1=s<1 dá R=2/(1+s^n)<2, embora o
pior U(x)/L(x)=s^-n. Razão de massas pode melhorar exponencialmente a
cota por pior palavra; isso é consequência clássica de somas ponderadas.
Multiplicar L_i e U_i pelo mesmo gauge positivo multiplica ambos os Z
pelo mesmo produto: R NÃO muda. E_b não é homogêneo em logits: subtrair
um gauge ANTES da racionalização muda em geral a própria lei.

No oráculo de duas referências, q é simétrico nos modos, L=q/r,U=rq,
w+_i=q_i r^(sign(c)), w-_i=q_i r^(-sign(c)). Então R=r^(2n) e
TV(w+|G,w-|G)=(R-1)/(R+1). Acople duas execuções pelos mesmos bits:
até a primeira consulta o transcript é igual, portanto a probabilidade
de alguma consulta de qualquer sampler exato universal é >=TV.
O squeeze aciona com 1-1/R, razão (R+1)/R<=2 sobre esse lower bound.
Isso limita o evento de consultar, não o número de linhas nem tempo GPU.

Para a triagem, fixe rho_v>=||Wv-Qv||2 e eta_i>=||hi||2; use idealexp
e bias exato em ambos. Então U_i,v/L_i,v=exp(2rho_v eta_i). Toda tupla
no suporte tem razão >=exp(2 min_v rho_v sum_i eta_i); somar ponderado
por L prova a mesma cota para R, independente da CFG/fixed positions.
Esta é uma prova de envelope largo mesmo que o erro REAL dos dots seja
pequeno; não é prova de que a aceitação real seja baixa.

Para certificar rho, cada coordenada |E| tem intervalo dyádico
[floor(2^24 |E|),ceil(2^24 |E|)]/2^24. Somar quadrados inteiros e aplicar
isqrt para fora certifica a norma. Diferenças W-Q são exatas em float64:
W é float32; Q é zero ou múltiplo da escala potência de dois mais próxima
com inteiro de até 7 bits, de ordem comparável a W. A subtração cabe em
53 bits (zero é imediato; caso não zero tem |W|>=escala/2). Para posto 1,
o resíduo é W ou zero. Conversões e somas int64 têm guards de overflow.
Mesmo procedimento para h float32 em grade 2^-16. O valor a do protocolo
usa os limites SUPERIORES escolhidos como envelope, não uma estimativa
estatística. sum_{k=0}^{16}a^k/k!<=exp(a) para a>=0 certifica R>4.

## Objeções que continuam abertas

Squeeze/razão de massas/DP são conhecidos; não há teorema próprio relevante
estabelecido. Gramáticas de poucos IDs já admitem head esparso competente;
políticas que usam confiança de todo o vocabulário perdem essa economia.
Nos casos densos, encontrar proxy barato COM envelope estreito e consumidor
natural é a hipótese essencial. Uma recusa da triagem não refuta proxies
melhores, intervalos direcionais, hardware especializado ou o teorema
construído, e tampouco autoriza trocar o proxy pós-dados nesta rodada.
