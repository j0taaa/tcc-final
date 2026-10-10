# Dominância finita sobre lotes iid de um decoder probabilístico

Prova escrita. Os princípios de estratificação são clássicos. Esta formulação
não estabelece prioridade acadêmica ou superioridade sobre toda alternativa.

## 1. Kernel inteiro e custo

Num histórico h, um decoder tem um kernel finito representado por uma função
determinística f_h:{0,...,W_h-1}→ações, W_h>0. Um ticket uniforme determina a
ação; diferentes tickets podem produzir a mesma ação. A próxima história
conserva TODAS as decisões anteriores. O modelo e os pesos podem depender
arbitrariamente dessa história. O horizonte T é finito; saída antecipada e FAIL
são absorventes. Políticas aleatórias adicionais precisam integrar o kernel ou
ser representadas como passos extras, com suas leis originais.

K execuções iid sorteiam seus tickets independentemente. O algoritmo S faz
algo diferente somente quando m candidatos têm o MESMO histórico h:

    R_j iid Uniforme{0,...,W_h-1}, j=0,...,m-1;
    I_j = floor((j W_h + R_j)/m);
    aplicar f_h(I_j), depois de atribuir os m tickets aos candidatos
    por uma permutação uniforme independente.

Sorteios de grupos distintos e de passos seguintes são independentes. Após
uma divergência de históricos, grupos não são reunidos, mesmo quando dois
canvases voltam a coincidir. Somente histórias integralmente idênticas
compartilham a estratificação. Não usar uma única fase aleatória comum.

Há O(m) somas/divisões adicionais de B+log m bits, B=bitlen(W_h), mais uma
permutação. Essa coordenação não é gratuita. O custo esperado da SOMA de uma
função de custo individual de trajetória é o mesmo que no iid (teorema2),
mas a latência, o custo de deduplicação de forwards e o máximo dos custos não
são uma soma dessas funções. Não há teorema de aceleração física.

## 2. Lema local — partição exata, inclusive m não divisor de W

Os mW valores jW+r particionam {0,...,mW-1}. Cada ticket i∈{0,...,W-1}
possui exatamente m preimagens pela divisão inteira por m. Logo, escolher
um estrato uniforme j e r uniforme dá i uniforme. Uma permutação torna cada
rótulo individual uma escolha uniforme de estrato. Nenhum denominador é
aproximado ou renormalizado; também funciona para W<m e W=1.

Para qualquer função a de tickets, escreva a_j=E[a(I_j)]. Então

    (1/m) sum_j a_j = E[a(I)], I uniforme.

Se 0≤a≤1, independência dos R_j e média geométrica/aritmética dão

    E[prod_j a(I_j)] = prod_j a_j ≤ (E[a(I)])^m.             (1)

Para uma função g real de variância finita, a variância da soma no passo é

    Var(sum_j g(I_j))
       = sum_j Var(g(I_j))
       = m Var(g(I)) - sum_j (E[g(I_j)]-E[g(I)])²
       ≤ m Var(g(I)).                                      (2)

A permutação não altera produto nem soma. (1) é estrita quando as médias
dos estratos diferem e são positivas; zeros também podem dar dominância
estrita. (2) é estrita se alguma média difere.

## 3. Teorema — trajetórias inteiras, sem estabilidade dos logits

Se Q_h é a lei final de UMA execução original a partir de h, então:

(i) Cada rótulo de S tem a lei original Q_h, inclusive compromissos,
    próximos forwards, parada e FAIL especificado pelo kernel.
(ii) Para QUALQUER conjunto A de saídas aceitáveis, sem fornecer A ao sampler,

    P_S(algum candidato em A) ≥ 1-(1-Q_h(A))^K.             (3)

(iii) Para QUALQUER pontuação real finita s, o máximo do lote S domina
    estocasticamente o máximo iid. Em particular E[max s(S)]≥E[max s(iid)].
(iv) Para QUALQUER pontuação g de segundo momento finito,

    E_S[(1/K)sum_i g(Y_i)] = E_Q[g(Y)],
    Var_S[(1/K)sum_i g(Y_i)] ≤ Var_Q(g(Y))/K.                (4)

**Prova (i).** Condicione no histórico completo de todos os candidatos.
O lema local e a permutação preservam o kernel de cada rótulo. Indução no
tempo preserva a lei marginal de sua trajetória inteira. Não é necessário
que logits de canvases DIFERENTES sejam semelhantes. É necessário que o
kernel de um histórico não dependa das outras trajetórias do lote.

**Prova (ii).** Indução de trás para a frente no horizonte. Na folha, a chance
de todos falharem é 0 ou1, exatamente a referência. Suponha o resultado
para os descendentes. Após tickets no grupo de m candidatos, sejam n_x as
multiplicidades das ações x. As histórias hx diferentes permanecem em
grupos independentes. Se a(x)=1-Q_hx(A), a probabilidade condicional de todos
falharem é no máximo prod_x a(x)^(n_x)=prod_j a(f_h(I_j)). Pela (1), sua
esperança é ≤(sum_x P_h(x) a(x))^m=(1-Q_h(A))^m. É o passo indutivo.
Não há oracle de acerto, recompensa ou lookahead no algoritmo.

**Prova (iii).** Aplicar (ii) a A={y:s(y)>z} para cada z. Isso compara todas
as CDFs do máximo. Integrar as caudas prova a comparação das expectativas
quando estas existem; para pontuações limitadas não há questão de integração.

**Prova (iv).** Defina b(h)=E_Qh[g] e v(h)=Var_Qh(g). Para m candidatos,
prove por indução Var(sum g)≤m v(h). Dados os filhos, os grupos hx são
independentes e a hipótese indutiva limita sua variância por sum_x n_x v(hx).
A esperança condicional da soma é sum_j b(h f_h(I_j)). Sua variância é
≤m Var_P_h(b(hx)) pela (2). A esperança da primeira parcela é
m E_P_h[v(hx)] pelo lema local. Variância total dá m v(h). A base nas folhas
é zero. Dividir por K² e usar (i) conclui (4).

**Consequência de custo.** (i) preserva E[sum c(trajetória_i)] para qualquer
custo individual integrável c, inclusive número de forwards cobrados por
trajetória. Não preserva necessariamente o número de histórias ÚNICAS
visitadas. Um iid com caching pode pagar menos; não esconder essa fronteira.

**Corolário de cobertura e custo compartilhado.** Para qualquer coleção finita
de propriedades A_j e pesos c_j≥0, somar (3) fornece
E[sum_j c_j·1[alguma saída em A_j]] no mínimo igual ao iid. Tomando A_j como
singletons, o número esperado de saídas distintas não diminui. Tomando-os
como os eventos que visitam cada histórico completo até T, também não diminui
o número esperado de históricos distintos. Portanto uma implementação que
cacheia todo forward idêntico pode ter MAIS forwards únicos: não há teorema
de superioridade geral em tempo por resposta útil. Dois filhos equiprováveis
e K=2 já dão2 filhos distintos estratificados contra1,5 em esperança no iid.
O benefício provado é cobertura/pass@K e variância com K trajetórias, incluindo
a preservação do custo esperado individual; a coordenação é custo adicional.

## 4. Corolário CFG/dLLM — representação compacta de tickets

Num posterior CFG não ambíguo sobre suportes originais finitos, pesos por
posição são inteiros; o peso de um evento y é prod_p w[p,y_p]. O circuito
inside usa soma nas alternativas e produto nos filhos de posições disjuntas.
Se W é a massa inteira da raiz, existe unranking sem enumerar W tickets:

- nó soma: escolher o intervalo cumulativo que contém o rank;
- nó produto com massas A,B: ranks dos filhos são divmod(rank,B);
- folha de token com peso w: os w tickets emitem o MESMO ID original.

Indução estrutural mostra que cada evento original y tem exatamente
prod_p w[p,y_p] preimagens. Gramática ambígua não admitida; normalização e
IDs originais precisam preservar esse contrato. Aliases são eventos distintos,
não derivações extras. Posições fixas, tokens prefixos, epsilon gramatical e
múltiplos bytes seguem o contrato do núcleo; emissões de token vazias são
rejeitadas pela API. EOS ausente permanece a hipótese.

CDFs custam O(H) operações após inside, onde H conta todas as alternativas.
Um unranking visita S nós, com buscas O(log Amax) e divisões/multiplicações
em B bits; um limite em bits é O(H M(B)+K S[log Amax·B+D(B)]), mais preparo
de gramática/tokenizer, modelo e emissão Ω(Kn). M,D são custos de multiplicação
e divisão. B≤sum_p bitlen(den[p]); neutrals têm peso1 e não há peso de regra
estocástico oculto. O iid competente pode reutilizar as MESMAS CDFs e o mesmo
unranking. Estratificação acrescenta O(K D(B+log K)+K log K) operações de
bits/RNG/permutação, não remove o custo do posterior.

Usar esse f_h em cada passo de uma dLLM, manter a política original de
commitments e agrupar por histórico completo satisfaz o teorema3. Pode usar
top-K DECLARADO ou vocabulário inteiro, se a preparação concluir. O teorema
não torna top-K exato no vocabulário inteiro. Também se aplica a um decoder
que usa um posterior aproximado: a lei individual preservada é a desse
decoder aproximado, não uma lei completa diferente. Todos os candidatos
que o decoder original garante válidos continuam válidos.

## 5. Um uso estritamente melhor, sem converter exemplo em benchmark

Se o posterior possui dois resultados JSON equiprováveis, K=2, e um dry-run
aceita somente um, o iid tem chance3/4 de fornecer algum resultado aceitável.
Uma ordenação com cada resultado ocupando metade dos tickets produz um de
cada: chance1. A identidade NÃO fornece o resultado aceitável ao sampler.
O mesmo ocorre com uma classe de resultados de massa1/2 ocupando um estrato.
Para estimar o indicador de aceitação, a variância cai de1/8 para0.
É um objeto de prova de desigualdade estrita, não evidência de probabilidade
de um modelo ou promessa de25 pontos percentuais em aplicações gerais.

## 5a. Auditar estratos em um circuito sem enumerar palavras

Um evento de evidência especifica conjuntos admitidos de IDs por posição.
Avaliar inside com folhas incompatíveis de peso0 dá F(v), a contagem
compatível de TODOS os tickets do nó v. Isso é uma consulta, não alteração
da lei do sampler. Seja C(v,r) a contagem compatível de tickets abaixo de r.
Num nó soma, somar F das alternativas completas anteriores e continuar na
única alternativa cortada. Num nó produto com massa direita B, escreva
r=aB+b. Então

    C(v,r)=C(esquerdo,a)·F(direito)
             + 1[ticket esquerdo a compatível]·C(direito,b).

O segundo termo só é avaliado quando b>0. As a linhas completas do produto
cartesiano fornecem o primeiro termo; a última linha parcial fornece o
segundo. Nas folhas de token, C=r ou0 conforme o ID admitido. Base em r=0
e r=inside(v) evita trabalho. A prova é indução no circuito decomponível.
Uma checagem de compatibilidade percorre uma derivação, não todas elas.
Para K cortes, um bound conservador é O(H+K S² log Amax) operações inteiras,
mais multiplicações/divisões de B bits; não prometer complexidade linear.

Para a divisão inteira do lema2, defina a contagem replicada

    G(z)=K C(raiz,floor(z/K))
          +(z mod K)·1[ticket floor(z/K) compatível].

A massa do evento no estrato j é [G((j+1)W)-G(jW)]/W. Assim a probabilidade
de algum passar é computável exatamente como1-prod_j(1-p_j), sem simular
lotes e sem usar o evento no sampler. A regra vale mesmo para pesos enormes
e tickets de uma mesma sequência não contíguos. Não é uma reivindicação de
invenção de unranking ou contagem em circuitos; o uso é uma auditoria exata
da alteração da dependência do lote.

## 6. Contraexemplos que delimitam a generalidade

**Fase comum sistemática.** Quatro resultados JSON equiprováveis em ordem
0,1,2,3, K=2. Uma fase comum fornece {0,2} ou{1,3}. Se o software aceita
0 e2, a chance é1/2, inferior ao iid3/4. Estratos independentes dão3/4 aqui,
igualdade correta. Reordenar tokens semanticamente pode ajudar em aplicações,
mas não fornece dominância para TODO verificador.

**Estratificar componentes locais.** Dois bits independentes, K=2. Forçar
um0 e um1 em CADA coordenada pode produzir dois vetores de paridade igual.
O verificador de paridade par passa no lote com chance1/2, contra3/4 iid.
Não equivale a estratificar uma ação inteira e, depois, somente grupos de
histórico idêntico. Essa distinção é essencial em dLLMs paralelas.

**Ganho de primeiro resultado.** (i) implica que a chance individual de
acerto é idêntica: não existe melhoria estrita de pass@1 nesta construção.
Quando K=1, o algoritmo inteiro é iid. Não prometer superioridade estrita em
TODAS as entradas: um decoder determinístico deixa qualquer método igual.

**Alterar a marginal.** Se um diversificador altera a lei individual, existe
uma propriedade de saída cuja esperança diminui: escolha um evento A cuja
probabilidade diminuiu. O nosso teorema preserva a marginal e melhora a
dependência do lote; não diz que vence a pontuação empírica de ODD ou SBS.
