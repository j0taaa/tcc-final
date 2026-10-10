# Corolário: a gramática também precisa filtrar erros rasos

Este corolário amplia a família escrita em `theory.md`, preservada. Não é
um benchmark nem uma observação de dLLM. Não usar a família para escolher
casos de avaliação prática.

Acrescente m slots livres ANTES do token fixo `{"payload":`. Cada slot
emite espaço ASCII0x20 com probabilidade1/2 ou `:` com probabilidade1/2. Acrescente
apenas esse token ao tokenizer fixo; são4m+4 slots e10 tokens, sem crescimento
de vocabulário com m. O restante da família e todos seus pesos permanecem.

Se A significa que todos esses slots são whitespace, q(A)=2^(-m).
JSON válido exige A. O lexer/counter completo, que esquece a sintaxe, aceita
ambos os tokens iniciais: `:` não altera altura nem estado lexical OUT.
Portanto seu evento C é independente das escolhas desses novos slots.

Denote Z0,L0,U0 as massas da família original. Para o envelope handoff, a
gramática é verificada ANTES da primeira ultrapassagem. Um `:` inicial nunca
chega ao overflow; tampouco é um JSON raso válido. Logo

    Z=2^(-m) Z0, L=2^(-m) L0, U_B=2^(-m) U0.

O certificado permanece delta<=1/[3(m+1)!], e a amostra aceita continua EXATA.
Preparação segue polinomial, O(m²) operações e precisão polinomial conforme
as hipóteses do teorema original. Todos2^m payloads rasos e2^m classes de
pilhas profundas continuam representados; o algoritmo não recebe um gabarito.

No counter-only, M_C=q(C)>=Z0, pois todos os eventos JSON originais pertencem
a C e as novas escolhas são independentes do counter. Assim

    P(aceitar counter-only)=Z/M_C <=2^(-m),
    E[propostas counter-only]>=2^m.

Na rejeição bruta Z<=2^(-m)·(1/2)2^(-m); são pelo menos2^(2m+1) propostas
esperadas. Na versão CARS publicada, todos os prefixos do ramo array que
passaram os slots novos corretamente ainda são viáveis até terminar as m
aberturas. Cada candidato visitado modifica no máximo uma das2^m classes
desse ramo. Sua massa não eliminada após t candidatos é pelo menos

    A_t >=2^(-m) (1/4)(1-t/2^m).

Para t<=2^(m-1), A_t>=2^(-m)/8, enquanto Z<=2^(-m) Z0. Cancelar o fator
comum recupera probabilidade de sucesso<=4·2^(-m), e o mesmo lower bound
Omega(2^m) da primeira saída de CARS. Nenhuma independência das tentativas
adaptativas é pressuposta.

**Objeção e controle mais forte.** Um híbrido que combine o counter com
pruning gramatical adaptativo pode aprender os erros rasos e obter a mesma
ordem polinomial; uma projeção regular que filtre globalmente esses prefixos
também consegue isso. Este corolário NÃO separa o envelope dessas alternativas.
Por isso counter+CARS é obrigatório no protocolo de custo real, junto dos
solvers compactos. A vantagem matemática demonstrada é contra os três
algoritmos especificados, não contra toda abordagem possível nem exclusividade
do princípio de relaxação ponderada. O requisito de adoção prático não pode
ser satisfeito apenas por esta família.
