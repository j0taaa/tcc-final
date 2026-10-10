# Primeira ultrapassagem gramatical com continuação por contador

Prova escrita de um refinamento. Não prova prioridade na literatura nem
rapidez física; abstração de storage e DP ponderada são antecedentes.

## Linguagens e decomposição exclusiva

Siga o recognizer determinístico de JSON em tokens originais enquanto a
profundidade máxima não ultrapassa d. A primeira transição de token cujo
pico interno ultrapassa d é absorvida; não continua no DAG limitado.

G_d admite eventos que têm um primeiro token de ultrapassagem e cujo prefixo
até o FIM desse token é lexical/gramaticalmente válido. Testes necessários
seguros de contexto direito podem restringir esse prefixo. Todos os tokens
posteriores são livres. Cada evento tem no máximo uma primeira ultrapassagem.

B_d exige, além disso, que o sufixo posterior à ultrapassagem seja lexicalmente
completo, permaneça com contador não negativo e termine com contador zero.
Forget tipos/sintaxe apenas depois do primeiro token de ultrapassagem.
Não use o parser completo para computar o sufixo; ele é um counter.

Se R_d é o evento JSON válido com pico>d e C_d o counter-closed independente:

    R_d ⊆ B_d ⊆ G_d
    B_d ⊆ C_d

Uma conclusão de R_d possui prefixo válido até sua primeira ultrapassagem e
sufixo fechado. Todo evento de B_d possui picos não negativos, ultrapassa d
e termina lexicalmente completo com contador zero; logo pertence a C_d.
Os testes necessários são satisfeitos por toda conclusão admitida.

Portanto o upper bound U_handoff=q(B_d) satisfaz

    R ≤ U_handoff ≤ min(q(G_d), q(C_d)).

O erro condicionado U/(L+U) é crescente em U quando L>0. O certificado
handoff é sempre ao menos tão forte quanto os outros dois, para MESMO d.
Isso é uma vantagem de certificado, não de custo universal.

## Recorrência e IDs originais

α[p,a] soma pesos de todos os prefixos de p slots que chegam ao estado
gramatical/lexical a sem ultrapassar d. O DAG de prefixos precisa ser mantido
ANTES do trimming por aceitação em J_d: prefixos sem nenhuma conclusão em
J_d ainda podem contribuir para R_d. Trimmá-los prematuramente subestima U.

Para cada aresta de primeiro overflow g a partir de a, capture q', a altura
final h' e o peso agregado w[p,g]. O agrupamento soma IDs originais distintos
com o MESMO efeito determinístico; não soma derivações ambíguas de um evento.

Se β_counter[p+1,q',h'] é o peso inteiro dos sufixos lexicalmente completos,
não negativos e fechados, então

    U_handoff_int = Σ_{p,a,g_overflow} α[p,a] w[p,g] β_counter[p+1,q',h'].

Substituir β_counter pelo produto de denominadores restantes calcula G_d.
Todos os termos usam os denominadores originais; nenhuma cauda renormalizada.
Cada evento tem primeira ultrapassagem única: as parcelas são disjuntas,
portanto não há dupla contagem de massa original. A lei do sampler de J_d
continua intacta e os intervalos usam U_handoff/D.

## Aperto pode ser arbitrariamente grande

Objeto matemático de dois slots, d=1. No primeiro, tokens `[[`, `[[,]]`, `[]`
têm probabilidades s,t,1-s-t, com s,t>0 e s+t<1. No segundo, `]]` tem
probabilidade r>0 e whitespace tem1-r. Grammar-hit admite o prefixo `[[`:
seu futuro possui um fechamento possível, embora improvável. Counter-closed
também admite `[[,]]`+whitespace, que é lexical/balanceado mas inválido JSON.

    L = (1-s-t)(1-r)
    R = s r
    U_grammar_hit = s
    U_counter_closed = s r + t(1-r)
    U_handoff = s r = R.

Quando r→0 com s,t fixos, min(U_grammar_hit,U_counter_closed)/U_handoff
diverge. O certificado handoff tende a zero; os dois outros mantêm erro
condicionado positivo. Isso prova vantagem estrita de aperto em um objeto
JSON, independentemente de executar código. Um solver completo desta instância
é igualmente barato: esta família NÃO demonstra vantagem de runtime sobre CFGs.

## Custo e ligação ao decoder

Se H_d é a quantidade de estados/arestas efetivas do DAG limitado, calcular
α e detectar primeiros overflows é linear nesse DAG e nas arestas de fronteira.
Reconhecer os macrotokens de overflow também é pago; não atribuir-lhes custo0.
Cache do counter depende de (slot,q,altura), não da pilha/tipos do prefixo:
no máximo O(n Q Dmax) estados e O(n Dmax F) transições aritméticas. Memória
pode guardar essas submassas, em vez das duas camadas do bound independente.
Inteiros usam O(Σ bitlen(den[p])) bits. Saídas de marginais continuam lineares
no vocabulário original. Preparação de tabela, conversão e forward são pagos.

Quando q(G_d)/(L+q(G_d)) já atende a tolerância, um método adaptativo pode
evitar o counter. Caso contrário, calcular handoff e somente então aumentar d.
Contra o MESMO método sem essa etapa, o benefício candidato é evitar a próxima
preparação de profundidade maior. Ele só é útil se esse custo evitado exceder
o counter; precisa de análise/medição completa, com contraexemplos preservados.

O lema de acoplamento da especificação permanece aplicável com esse U e a
mesma política de geração. Probabilidades marginais da referência completa
têm intervalos [(1-δ)ν_i, (1-δ)ν_i+δ], não apenas uma estimativa pontual.
Isso não prova que o baseline seja semanticamente bom nem que o EPIC calcule
a mesma distribuição. Não há formalização Lean deste resultado ainda.
