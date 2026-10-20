# Prova escrita e ataques independentes

Esta é uma prova em Q/R, não Lean, prova do software ou revisão humana.

## 1. Contração

Fixe v e uma palavra âncora a∈L. Seja A uma base de LINHAS de U_v em Q^n,
q=rank(A), J um conjunto ordenado de q colunas com A[:,J] invertível e
B=A[:,J]^{-1} A. Para D=A^T c, D[J]=A[:,J]^T c; logo
B^T D[J]=A^T A[:,J]^{-T} A[:,J]^T c=D. Para q=0 os dois lados são zero.
Em particular a RREF de A é uma escolha de B, com B[:,J]=I.

Escreva l_v=H W_v + 1 b_v e defina l'_v fora de J igual a zero e
l'_v[J]=B l_v. Para y,z∈L,

    (x_v(y)-x_v(z))^T l_v = D[J]^T B l_v
                              = (x_v(y)-x_v(z))^T l'_v.

Somar sobre IDs dá s(y)-s(z)=s'(y)-s'(z). Assim s(y)=s'(y)+c, com
c=s(a)-s'(a), independente de y. Os conjuntos de maximizadores e desempate
lexicográfico de IDs são preservados. Para Gibbs ideal com temperatura fixa,
e^{s(y)}/Σ_z e^{s(z)}=e^{s'(y)}/Σ_z e^{s'(z)}. O normalizador absoluto exige
Z=e^c Z'. Com q=0 um token pode ter escore constante NÃO nulo.

Bias precisa de (B1)b_v. Somar b_v somente uma vez por pivô é errado: para
duas cópias B=[1,1], o bias correto é 2b_v. Não se preservam softmax/marginais
por posição antes do condicionamento nem confidências de um scheduler.

## 2. Compilador de um forest

Uma folha fixa (posição, ID) gera uma atribuição parcial. Um AND combina
escopos disjuntos; um OR não vazio une linguagens do mesmo escopo. O DAG é
finito e todos os nós considerados são alcançáveis da raiz. A raiz cobre
exatamente os n slots. Escolha recursivamente uma atribuição a_N: a folha,
a união dos anchors filhos de AND ou o primeiro filho de OR.

Para cada aresta OR N→C gere g_{N,C,v}=x_v(a_C)-x_v(a_N), estendido por
zeros fora do escopo. Reúna esses geradores de TODOS os ORs alcançáveis.

**Inclusão no U da raiz.** N produtivo e alcançável possui um contexto de
raiz: escolha a ocorrência de N num caminho e anchors dos irmãos em ANDs.
Escopos disjuntos permitem substituir a_N por a_C mantendo o contexto.
As duas palavras resultantes são válidas e diferem exatamente em g.
Compartilhamento de DAG é expandido por ocorrência; escopo vazio só produz g=0.

**Geração de todas as diferenças.** Por indução na derivação, x_v(y)-x_v(a_N)
é soma de geradores nos descendentes: numa folha é zero; em AND é a soma
das diferenças nos filhos; em OR que escolhe C some a diferença de y para
a_C e g_{N,C,v}. Na raiz, subtraia as expressões de y e z. Portanto o span
dos geradores é exatamente U_v. Contexto fixo e posições disjuntas são
hipóteses essenciais; filtros globais posteriores ao forest invalidam a prova.

Ambiguidade repete palavras e não altera o span nem MAP. Para Gibbs, contar
derivações pode alterar a lei: L={0,1}, derivação de 0 duplicada e escores zero
dá 2/3 por árvores e 1/2 por palavras. O protótipo não oferece sampler em DAG
ambíguo. Um grammar parser/forest builder completo é custo adicional e não
está implicitamente coberto por receber um DAG já pronto.

## 3. Limite de consultas e alternativas clássicas

Para H fixo, as diferenças de escores que dependem de W_v ocupam o espaço
H^T U_v. Em um modelo que só consulta produtos escalares contra cada linha
arbitrária W_v, sem a ler, preprocessar, misturar ou usar conhecimento prévio,
menos de rank(H^T U_v) consultas deixam uma direção invisível: no transcript
de W_v=0 escolha uma perturbação ortogonal a todas as consultas mas não ao
espaço requerido. Ela muda algum contraste e mantém as respostas zero.
Somar por v dá o limite para recuperar TODOS os contrastes nesse modelo.
Não é um lower bound universal de MAP, de software ou de GPU. q_v pode ser
maior que rank(H^T U_v); A73 usa preparação independente de H.

Uma distribuição estritamente positiva sobre todas as palavras tem covariância
C_v dos indicadores com ker(C_v)=U_v^⊥, pois t^T C_v t=Var(t·x_v)=0 se e
somente se t·x_v é constante. Assim image(C_v)=U_v. Semirings de segunda
ordem dão outra rota conhecida; duplicar derivações com pesos positivos não
altera esse núcleo, embora altere o posterior. A construção de hull e a
mudança de base são ingredientes clássicos, não novos teoremas gerais.

## 4. Casos que atacam o benefício e os contratos

- L=D^n, |D|>=2: variar só uma posição produz e_i para cada token; q_v=n.
- Cópia L={(v,...,v):v∈D}, |D|>=2: U_v=span(1), q_v=1. Somar H antes do head
  é a mesma operação do pooling manual/flattening antecipado.
- Contagem: L binária com y_0+y_1=y_2+y_3. Há seis palavras e U_1 tem
  dimensão 3, U_0 igual. Nenhum par de posições é sempre igual: há economia
  além de equality pooling, mas só dois IDs e transformação adicional.
- Aliases: IDs 0 e 1 emitem `a`, ID 2 emite `b`, dois slots iguais em bytes.
  São válidos 00,01,10,11,22. Unárias [[10,0,6],[0,10,6]] têm MAP 01 de
  score 20; impor igualdade de IDs devolve 22 de score 12. Cada alias tem
  q=2 e não pode ser comprimido como singleton. Para pesos [[9,1,2],[1,9,2]],
  massa da classe `a` é 100 e massa com pooling de IDs seria só 18.
- Slots fixados e suportes contraídos reduzem L, preservando relações antigas;
  uma expansão pode introduzir contrastes fora do span e exige recompilação.
- Em binary32: (2^24+1)-2^24 pode arredondar para zero enquanto
  2^24+(1-2^24) vale 1. Associatividade não é contrato de CUDA.

O auditor enumera palavras por um caminho independente dos anchors e verifica
reconstrução de CADA contraste, MAP, constante e leis racionais de Gibbs
quando exp(score) é racional (pesos potência de 2). Cobertura finita não
substitui as provas acima nem garante uma implementação neural exata.
