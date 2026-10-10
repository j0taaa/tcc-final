# Separação matemática: profundidade constante certificada versus primeira passagem

**Resultado escrito independente de benchmarks.** Família de prova sobre JSON
e probabilidades produto; não é evidência de desempenho de um modelo. A
comparação de certificados vale independentemente da implementação. A separação
de espaço é delimitada ao recognizer de pilhas explícitas; parsing CFG compacto
pode evitar a explosão e continua um comparador necessário.

## Família com tokenizer FIXO e documentos JSON consumíveis

Vocabulario fixo de bytes: `{"payload":`, `"`, `[`, `{"k":`, espaço ASCII ` `, `0`,
`]`, `}`. Há 3n+4 slots, n>=2. Prefixo `{"payload":` e último `}` são fixos.
Nos slots intermediários, a predição produto é:

1. Primeiro valor: quote com3/4 ou `[` com1/4.
2. n slots: `[` com1-1/n, `{"k":` com1/(2n), whitespace com1/(2n).
3. Um slot: quote com1/2 ou `0` com1/2.
4. 2n slots: `]` comφ_j/(4n), `}` com(1-φ_j)/(4n), whitespace com1-1/(4n),
   com1/4<=φ_j<=3/4. φ_j pode variar por posição; não supor exchangeability.

Não existem strings-resposta impostas pela gramática. `payload` pode ser
string, array ou objeto aninhado; os valores e strings têm muitas conclusões.
Whitespace nesta família é SOMENTE o byte ASCII0x20, que pode aparecer sem
escape dentro da string; não é tab/newline/cr. Isso especifica o mesmo token
fixo usado pelo argumento, sem alterar pesos, algoritmo ou benchmark.
No ramo quote, `[` e esse espaço são texto interno; `{"k":` é lexicalmente
inválido nessa string (seu quote seguido de k fora dela). No ramo array,
os dois tipos de abertura são gramaticais e geram pilhas distintas.

O papel específico da dLLM é fornecer todas essas distribuições de posição
num único passo. A prova usa a predição produto congelada, nunca alega que
uma dLLM real produz esta família, nem que é a distribuição conjunta aprendida.

## Teorema — Força de certificado

Seja L_1 a massa válida de profundidade até1 (somente objeto externo, sem
containers dentro do payload), e U_1 o counter fechado ou handoff proposto.
Então

    L_1 >= 3/32,
    U_1 <= 1/[8 (n+1)!],
    TV(q(.|J_1),q(.|J)) <= 4/[3 (n+1)!].

Em contraste, o certificado por primeira ultrapassagem de um prefixo
gramatical, U_G/(L_d+U_G), é >=1/9 para todo d<=n+1. Isso continua válido
com coacessibilidade lexical e testes NECESSÁRIOS exatos de existência de uma
conclusão: todo prefixo usado no argumento possui conclusão no suporte.
Para epsilon<1/9, tal certificado precisa d>=n+2 ou inferência completa.

Em particular, para n>=6, o counter autoriza d=1 com epsilon=1/1000, pois
4*1000<=3*7! e factorial é crescente. É uma vantagem comprovada de
CERTIFICAÇÃO com profundidade constante, sem executar códigos ou selecionar
benchmarks favoráveis.

## Prova

No ramo quote, escolher nenhum token `{"k":` nos n slots, encerrar com quote
e escolher whitespace nos2n slots finais produz JSON válido de profundidade1.
Cada token `{"k":` tem probabilidade1/(2n); por união de eventos, a chance
de nenhum é pelo menos1/2. Nos2n slots finais, cada não-whitespace tem
probabilidade1/(4n); a chance de todos serem whitespace é pelo menos1/2.
Independência de posições dá L_1>= (3/4)(1/2)(1/2)(1/2)=3/32.

Todo evento profundo lexicalmente completo tem o ramo array inicial, o
slot central `0`, e não quote (que não teria fechamento posterior). Se W é
o número de whitespace nos n slots de abertura e C o número de fechamentos
nos2n slots finais, terminar com contador zero exige C+W=n+1. W+C soma3n
Bernoulli independentes cuja soma de probabilidades é1/2+1/2=1.

Para qualquer soma S de Bernoulli independentes de probabilidades p_i e k>0,

    P(S>=k) <= Σ_{|A|=k} ∏_{i∈A} p_i <= (Σ_i p_i)^k / k!.

A primeira desigualdade é união sobre subconjuntos de k sucessos. A segunda
expande a potência: cada subconjunto de índices distintos aparece k! vezes,
e os termos com índices repetidos são não negativos. Portanto
U_1<=(1/4)(1/2)P(C+W>=n+1)<=1/[8(n+1)!]. A identidade de condicionamento
e U/(L+U)<=U/L dão o limite TV declarado. Tipos e regras ignorados no counter
somente aumentam a massa; não é necessário conhecer R ou a massa completa.

Para primeira passagem, o ramo array tem probabilidade1/4. Todos os n slots
seguintes podem escolher algum token de abertura, sem whitespace, com chance
(1-1/(2n))^n>=1/2 pela mesma união. Há2^n escolhas de tipos; qualquer uma
possui uma conclusão com `0`, os n+1 fechamentos correspondentes nos2n slots
e whitespace nos demais. Sua profundidade atinge n+2. Para d<=n+1, pelo menos
1/8 da massa alcança uma primeira ultrapassagem gramatical. Ignorar a
PROBABILIDADE do fechamento, mantendo somente sua possibilidade, dá U_G>=1/8.
Como L_d<=1, U_G/(L_d+U_G)>=1/9. Isso prova a separação de certificados.

## Consequência de espaço, com fronteiras

O DFA/pilha de profundidade1 tem tamanho constante para esse tokenizer/grammar.
O counter tem O(n) alturas e O(n) slots: O(n²) operações aritméticas, além
dos bytes/tabela e saída. Os denominadores têm O(n log n) bits para entradas
racionais com φ_j de O(log n) bits; o custo em bits continua polinomial.

Um procedimento de primeira-passagem que expande pilhas explícitas precisa,
ao admitir d>=n+2, guardar ao menos2^n pilhas ao final do bloco de aberturas:
todas as sequências de tipos são distintas, possuem peso positivo e admitem
conclusão dentro do bound. Trimming de existência não as remove. Esse é o
controle natural implementado, com memoização e guards, não um controle que
ignora uma poda válida.

**Não é um lower bound de todo solver CFG.** Parsing gramatical compacto,
gramáticas indexadas pela profundidade ou outra abstração inteligente podem
compartilhar trabalho e ser polinomiais. Certificar a profundidade pequena
continua uma capacidade diferente do certificado G, mas a vantagem de
runtime contra esses algoritmos requer as medições externas preservadas.
Assimetria por posição dos φ_j não prova impossibilidade de outro algoritmo
especializado rápido. Denkinger2017 já oferece o princípio de upper bounds
ponderados por abstração; não reivindicar nova teoria geral de storage.

Zeros fora dos suportes são hipóteses explícitas desta família. Uma perturbação
produto com massa total de alterações <=τ muda qualquer massa de evento em
no máximoτ por acoplamento. Assim L>=3/32-τ e U<=1/[8(n+1)!]+τ, permitindo
versões com probabilidades estritamente positivas quando τ é pequeno frente
à tolerância. Isso é um corolário matemático, não captura real de logits.
