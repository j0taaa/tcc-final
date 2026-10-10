# Uso dos marginais: aumento certificado da probabilidade de JSON válido

Corolário de aplicação, não uma invenção do princípio de reponderação.
Seja q produto congelado, J a linguagem completa com seus trechos fixos,
Z=q(J)>0 e mu=q(.|J). Para um slot livre p e ID original t, ponha
r=q_p(t), m=mu_p(t). Multiplique o peso desse ID por um inteiro a>1 e
renormalize SOMENTE sua linha. O novo produto q' preserva todos os suportes
positivos, os outros pesos relativos, slots e IDs fixos. Ele não é q.

Particionar J segundo Y_p=t dá a identidade exata

    q'(J)/q(J) = [1+(a-1)m]/[1+(a-1)r].

Logo m>r implica aumento estrito para QUALQUER a>1. Não é uma aproximação
de primeira ordem nem depende de amostras. Aumentar uma probabilidade sem
comprovar essa condição não tem a mesma garantia; sintaxe válida não assegura
acerto semântico, e a igualdade não implica uma trajetória global melhor.

O certificado oferece J_d⊆J, massa L=q(J_d), upper tail U>=q(J\J_d),
e o numerador A=q(J_d∩{Y_p=t}). Como Z<=L+U e A<=q(J∩{Y_p=t}),

    m >= A/(L+U) = (1-delta) nu_p(t),  delta=U/(L+U).

Se b=A/(L+U)>r, o aumento tem certificado ANTES da alteração:

    q'(J)/q(J) >= [1+(a-1)b]/[1+(a-1)r] >1.

É importante dividir pelo limite da massa válida COMPLETA. Usar apenas
nu_p(t)>r pode amplificar um token que a distribuição completa desfavorece.
Se o intervalo não determina o sinal, recusar a alteração é conclusivo
apenas quanto ao certificado atual, não uma prova de que não existe melhoria.

## Aritmética e implementação

Use as unidades inteiras comuns da consulta: l para J_d, u para sua cauda
superior e N_pt para o numerador original do marginal em J_d. Em p, pesos
w_pt somam D_p. A condição e o multiplicador inferior são

    N_pt D_p > w_pt (l+u),
    g = D_p[(l+u)+(a-1)N_pt] / [(l+u)(D_p+(a-1)w_pt)].

Todas as comparações são inteiras; não testar o sinal usando log/float.
O novo vetor inteiro troca w_pt por a w_pt e usa denominador
D'_p=D_p+(a-1)w_pt. Nenhuma massa de suporte é removida, inclusive aliases
e eventos profundos que podem ter marginal zero em J_d.

`amplification.py` escolhe deterministicamente o maior g certificado entre
as coordenadas admitidas e retorna cópia do produto e o certificado, ou None.
Não há recompilação do modelo nem mudança de parâmetros treinados. O custo
ADICIONAL é O(nV) comparações de inteiros de B bits, com custo de multiplicação
M(B), e O(V) cópia da linha; consulta/normalização/forward continuam custos
anteriores. Implementações que usam um grupo de IDs podem aplicar a mesma
identidade ao evento Y_p∈A, mas esta referência não promete essa extensão.

## Utilidade e fronteira

Uma dLLM que desenha um rascunho paralelo do produto passa a ter maior
probabilidade de satisfazer a GLC. Rejeição sobre q' requer em média menos
propostas por saída válida do que sobre q, por um fator de pelo menos g;
essas saídas têm outra distribuição, explicitamente escolhida pelo usuário.
O custo total pode piorar se a consulta de marginais não se amortiza. O mesmo
resultado com marginais exatos é clássico, sem erro de certificado, e é um
comparador competente. A utilidade desta aplicação é obter uma decisão segura
dos marginais mais baratos QUANDO a consulta certificada já é vantajosa.

Não alegar conservação de q(.|J), menor latência de toda geração, calibração
semântica, treinamento ou exclusividade desse corolário. A25 é a operação
separada que mantém exatamente o produto original nas amostras aceitas.
