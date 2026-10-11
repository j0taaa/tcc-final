# A fronteira não precisa de uma hipótese de cauda exponencial

2026-10-11. Extensão ESCRITA do contrato A34, depois dos dois diagnósticos
nativos negativos. Não altera `theory-v1.md`, os snapshots ou seus resultados.
Não é evidência de benefício neural, prioridade ou publicação confirmada.

## 1. Enunciado auxiliar e alcance

Um único procedimento, independente de p, observa bits iid Bernoulli(p) e
aleatoriedade auxiliar R independente deles. N é seu número TOTAL de bits
observados, uma parada inteira não negativa. O procedimento termina quase
certamente para todo p em um intervalo aberto J contido em (0,1). Seu output
H é uma função mensurável do transcript terminado e de R, com |H|<=C, onde
C não depende de p. Para todo intervalo compacto I contido em J, suponha

    b_I = sup_{p em I} E_p N < infinito.

Então g(p)=E_p H é continuamente diferenciável em J e

    g'(p) = E_p[H (S_N-pN)] / [p(1-p)],

onde S_N é a soma dos bits observados. NÃO se exige momento exponencial,
segundo momento de N, continuidade de E_p N ou cauda rápida do procedimento.
Limitação do output e bound LOCALMENTE UNIFORME da esperança são essenciais
para esta prova; não substituir o bound por mera finitude pontual sem prova.
Side information cuja lei/valor dependa de p não faz parte deste contrato.

## 2. Prova por aproximações finitas, sem troca de séries não justificada

Fixe I compacto e escreva q=1-p. Revele R no início: como R é independente
dos bits, B_k-p continua tendo média condicional zero, variância pq, e
1_{N>=k} é mensurável antes de B_k. Portanto os incrementos parados são
ortogonais em L². Como E_p N é finita, sua soma converge em L² e fornece

    W_N = S_N-pN,
    E_p W_N = 0,
    E_p W_N² = pq E_p N.

Este passo usa o passeio COMPENSADO W_N. Não pressupõe E_p N² finita,
nem afirma uma identidade de segundo momento para 2S_N-N quando p!=1/2.

Para m>=1 defina g_m(p)=E_p[H 1_{N<=m}]. Para cada palavra binária u de
comprimento n<=m, a integral sobre as decisões auxiliares que terminam em u
é um coeficiente independente de p. Assim g_m é uma soma FINITA de termos
a_u p^{s(u)}q^{n-s(u)}, inclusive o caso n0. Diferenciar essa soma é legítimo:

    g_m'(p) = E_p[H W_N 1_{N<=m}] / (pq).

Defina h(p)=E_p[H W_N]/(pq). A expectativa existe por Cauchy--Schwarz e
a identidade L² acima. Markov e Cauchy--Schwarz dão, uniformemente em I,

    |g(p)-g_m(p)| <= C P_p(N>m) <= C b_I/m,

    |h(p)-g_m'(p)|
      <= C sqrt(E_p W_N² P_p(N>m))/(pq)
      <= C b_I/sqrt(m pq).

Como inf_{p em I} pq>0, g_m converge UNIFORMEMENTE a g e g_m' converge
UNIFORMEMENTE a h. Cada g_m' é contínua; logo h é contínua. Para x,y em I,

    g_m(y)-g_m(x) = integral_x^y g_m'(t) dt.

Passe ao limite uniforme para obter g(y)-g(x)=integral_x^y h(t)dt. O teorema
fundamental do cálculo, com h contínua, dá g'=h no interior de I. Como I
é arbitrário, isto vale em todo J. QED.

## 3. Corolário: ampliar a classe de TODOS os comparadores A34

No contrato de `theory-v1.md`, mantenha o algoritmo p-blind, ambas marginais
Bernoulli(p) para TODO p interior, e sup_p E_p N<=b. RETIRE a hipótese
E_{1/2} exp(aN)<infinito. Tome H=Z=X+Y-1, limitado por1. As marginais dão

    g(p)=2p-1,  g'(p)=2.

Em p1/2, W_N=(2S_N-N)/2=M_N/2 e pq1/4. O lema implica

    E_{1/2}[Z M_N]=1,    E_{1/2} M_N²=E_{1/2} N.

Estas são exatamente as duas identidades necessárias à desigualdade inteira
de A34. Para m=floor(b), lambda=b-m e b>=2, o mesmo lower bound dá

    Pr_{1/2}(X=Y) >= s_b
      = (1-lambda)/m + lambda/(m+1),

    sup_A inf_{0<p<1} eta_A(p) = 1-2s_b.

A construção de ruína já existente continua sendo admissível e atingindo
o bound. Assim a fronteira vale agora para TODOS os factories com esse
budget uniforme, não só os de cauda exponencial. O corolário de igualdade
em `optimal-stopping-uniqueness-v11.md` também recebe a classe ampliada.
Algoritmos que leem probabilidades/ruídos ou informações dependentes de p,
e comparações em tempo físico ou com mais outputs, continuam fora do bound.

## 4. Antecedentes e objeções conferidos

[Mendo, original, Teorema3 e Seção7.5](https://arxiv.org/pdf/1612.08923)
apresenta um lower bound de Cramér--Rao para fábricas rápidas e justifica suas
condições pela continuidade da esperança e convergência de derivadas. Foi
conferida diretamente essa hipótese; não atribuir ao texto uma exclusão
universal de algoritmos lentos. [Nacu--Peres, original](https://arxiv.org/pdf/math/0309222)
é antecedente para fábricas, caudas e regularidade. DeGroot1959 já fornece
o score sequencial e identidade quadrática; Wasan1964 já fornece a expressão
s_b em outro contrato. Não reivindicar esses princípios nem a fórmula.

O [abstract original de Simons1980](https://www.sciencedirect.com/science/article/pii/0378375880900348)
alerta para estimadores sequenciais não limitados que violam Cramér--Rao.
O download do original institucional1979 respondeu com bloqueio anti-bot;
seu argumento completo NÃO foi lido. Este lema tem prova própria explícita,
output limitado e budget localmente uniforme; não se aplica automaticamente
aos contraexemplos normais/unbounded, nem pretende refutá-los.

Este refinamento pode já ser consequência conhecida de regularidade de
experimentos parados. A prioridade de seu enunciado e da fronteira output-
restrita permanece aberta. Uma prova escrita autocontida não decide novidade.

## 5. Oito critérios reavaliados antes de ampliar o trabalho

1. **Uso:** calibrar o compromisso entre draws e dois candidatos estruturados
   de um oráculo dLLM+GLC sem calcular probabilidades de eventos de commitment.
   A extensão impede que um concorrente de cauda lenta seja excluído sem razão.
2. **Diferença:** ampliar o contrato do lower bound, não inventar score,
   diferenciação, antitéticos ou uma aplicação nova. Significância própria
   ainda precisa confronto com resultados conhecidos e aplicação útil.
3. **Escolha:** a fração minimax 1-2s_b permanece ótima contra TODOS os
   factories p-blind de budget esperado uniforme b, incluindo caudas lentas.
   Não é superioridade pontual, semântica, de segundos ou sobre EPIC completo.
4. **Matemática:** a prova usa somente aproximações FINITAS e dois bounds
   uniformes explícitos; nenhum benchmark ou execução é necessário.
5. **Experimentos:** nenhum novo head/timing aqui. Os screens0/8 e1/8
   permanecem negativos, seus gates de qualidade continuam não acionados.
6. **Custos:** este budget conta TODOS os draws. Preparação, consumo/verificação,
   forwards, caching e latência continuam obrigações separadas, sem omissão.
7. **Objeção:** o resultado pode já ser implícito em estatística sequencial;
   side information e mais outputs podem ser melhores. Output não limitado
   ou budget apenas pontualmente finito invalidam esta justificativa.
8. **Artigo:** isto fecha uma restrição artificial no argumento escrito,
   NÃO a prioridade, revisão humana ou aplicação prática/publicável. Não
   expandir implementação ou anunciar conquista geral a partir deste lema.
