# Continuação de fechamento de dimensão finita

Formulação independente da implementação. Resultados abaixo são consequências
de abstrações e limites clássicos; não constituem, sozinhos, prioridade científica.

Seja q um produto de probabilidades racionais sobre n slots de IDs originais.
Um lexer determinístico emite delimitadores de JSON, ignorando os delimitadores
dentro de strings. Cada token tem um efeito lexical determinístico e incremento
inteiro z de altura, possivelmente com vários picos internos. Seja J o conjunto
JSON válido, J_d o subconjunto de profundidade <=d, L=q(J_d) e R=q(J\J_d).

O recognizer gramatical limitado preserva todos os prefixos, inclusive os que
não terminam em J_d. Cada evento profundo tem um primeiro TOKEN que excede d.
Até o fim desse token, exigir prefixo gramatical válido. Agrupar o peso desses
prefixos por (próximo slot i, estado lexical s, altura final h), produzindo
a_i(s,h). Os grupos são disjuntos como eventos de prefixos. Macrotokens podem
ultrapassar e voltar abaixo de d dentro do mesmo token: h não precisa exceder d.
Nenhum trimming por aceitação rasa pode eliminar essa fronteira.

## Resíduo de fechamento

Para m>=1, seja B_m(i,s,r) a probabilidade de um sufixo lexicalmente completo
que, partindo do resíduo r, termina com altura congruente a zero módulo m.
Ignorar negatividade e tipos dos delimitadores no sufixo. A recorrência é

    B_m(n,s,r) = 1[finish(s) existe e r=0],
    B_m(i,s,r) = sum_t q_i(t) B_m(i+1,next(s,t),(r+z(s,t)) mod m).

Tokens lexicalmente inválidos contribuem zero, mas permanecem no denominador
original. Aliases são IDs diferentes e somam suas probabilidades exatamente.
Um fechamento válido tem altura final zero, logo

    R <= U_m = sum_(i,s,h) a_i(s,h) B_m(i,s,h mod m).

O cálculo é determinístico: não soma vários percursos para o mesmo token.
Quando m divide m', o evento com módulo m' está contido no evento com módulo m;
portanto U_m'<=U_m. Módulos arbitrários não são ordenados. Com módulos 2 e3,
interseção corresponde a módulo6; min(U_2,U_3) é um bound, não sua massa.

## Potencial de fechamento

Para b>0, defina a transformada do sufixo lexical

    T_b(i,s) = E_q[1[sufixo lexicalmente completo] b^(-sum z)].

Se o sufixo fecha uma altura h, sum z=-h. Todos os termos são não negativos;
portanto sua probabilidade é <=b^(-h) T_b(i,s). Isso vale também para b<1
e b=1, sem monotonicidade da altura. Escolher alguns b racionais permite
somar mínimos por fronteira:

    R <= U_pot = sum a_i(s,h) min_b {1, b^(-h) T_b(i,s)}.

O fator de normalização de a e do sufixo precisa usar as mesmas probabilidades
originais. Para b=2^k com k>=0, deslocamentos inteiros por camada eliminam
frações intermediárias. Se M_i>=max_t z(s,t), multiplicar pesos da camada
por 2^(k(M_i-z)) e dividir a submassa final por 2^(k sum M_i) é exato.
Ao consultar uma fronteira de altura h, acrescentar 2^(k h) ao denominador.
Não arredondar esses cálculos para float; um resultado arredondado para baixo
deixaria de ser certificado.

Ambas as continuações relaxam o contador fechado completo. Não alegar um
bound universalmente mais apertado que esse contador. Menor dimensão não
implica menor tempo físico, nem que um módulo pequeno atenda a tolerância.

## Uso e custo

Se L>0, qualquer desses U dá TV(q(.|J_d),q(.|J))<=U/(L+U), como em A24.
Esse corolário não é novo. O envelope J_d união evento modular de primeira
ultrapassagem é uma linguagem regular determinística, disjunta entre os ramos.
SE um sampler dessa linguagem for implementado, rejeitar palavras fora de J
produz exatamente q(.|J), com aceitação >=L/(L+U_m). O princípio é OS*, não
uma invenção desta tentativa. Orçamento finito introduz FAIL.

Se F conta as transferências agrupadas do lexer e H_d o DAG gramatical raso,
resíduos requerem O(H_d+n m F) operações aritméticas, potenciais g requerem
O(H_d+n g F), além de formação das somas sobre todos os IDs. Para consultar
toda fronteira, guardar todas as camadas custa O(n Q m) ou O(n Q g); acumular
fronteiras ao passar para trás permite duas camadas mais a própria fronteira.
Para módulo fixo e tokenizer fixo isso elimina o fator da altura possível no
contador, mas não prova novidade nem vence todo algoritmo compacto conhecido.
Os inteiros usuais têm O(sum bitlen(den_i)) bits. O potencial acrescenta
O(k sum_i(max z_i-min z_i)) bits; incluir o custo de multiplicação e shifts.
Fazer g grande ou buscar parâmetros sem pagar esse trabalho é proibido.

Ainda falta um teorema distintivo: não declarar a contribuição publicável
apenas por esta prova de correção ou por ela usar uma dLLM como fornecedora de q.
