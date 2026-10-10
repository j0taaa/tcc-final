# Orçamento finito: lei local exata e trajetória com estado de recusa

Refinamento da seção4 de `theory.md`, cuja primeira versão está congelada
em25/v1. Igualdade da trajetória SEM recusa vale com rejeição ilimitada e
recursos suficientes. Um orçamento finito de propostas não pode ser omitido.

Em um histórico h admitido, Z_h>0 e a preparação conclui. A predição produto
q_h, a gramática e os trechos fixos definem mu_h=q_h(.|J_h). A preparação
escolhe um envelope E_h determinístico em função dessas entradas, de massa
M_h=L_h+U_h, com delta_h=U_h/M_h. Fixe um inteiro k>=1 ANTES das propostas.
A refusa depois de k propostas tem

    a_h=(1-Z_h/M_h)^k <=delta_h^k.

Condicional ao sucesso, a lei da amostra é EXATAMENTE mu_h. Incondicionalmente
o kernel é (1-a_h)mu_h+a_h·FAIL. Sua TV contra mu_h (estendida com massa0
em FAIL) é a_h, não0. A igualdade por indução não pode usar apenas o kernel
normalizado ao sucesso, ignorando a chance de interrupção em cada histórico.

Uma política comum K_h que transforma a amostra em commitments, sem usar
marginais aproximadas de forma diferente, só contrai essa distância. Se
delta_h<=epsilon_t em TODO histórico admitido no passo t, acoplar a amostra
aceita com a do decoder completo até a primeira recusa dá

    TV(lei final incluindo FAIL, lei do decoder completo) <=sum_t epsilon_t^k.

Quando epsilon_t<=0.001 e k=3, são no máximo10^(-9) por passo por esgotamento
de propostas. T<=n passos de uma política que fixa ao menos um slot dão
TV<=n·10^(-9). A probabilidade de NÃO concluir pelo orçamento tem o mesmo
upper bound. Preparação com timeout/memória e custos variáveis do reconhecedor
são recusas ADICIONAIS; não recebem esse limite sem outra hipótese/medição.

Condicionar toda a trajetória à conclusão pode enviesar trajetórias precoces,
pois a_h depende do histórico. Pelo mesmo acoplamento, se a probabilidade total
de refusa é p, a lei final CONDICIONAL à conclusão fica no máximo p distante
da referência: a referência é mistura da lei no evento sem refusa (peso1-p)
e das trajetórias desacopladas (peso p). Não chamar essa lei de idêntica sem
demonstrar p=0. Essa conclusão pressupõe somente as recusas especificadas.

Os forwards seguintes podem depender dos tokens fixados. O produto é
recalculado em cada histórico; a prova não requer repetir logits antigos.
Comparador é o decoder de posteriors produto congelados completos, não a
trajetória NATIVA condicionada da MDLM: o viés distinto de Twister2026 permanece.
Acerto semântico, memória/latência física universal e prioridade científica
não decorrem do acoplamento.

Uso concreto: limitar o número de propostas entre forwards preservando a
lei condicional de cada resposta válida e publicando um risco de recusa
ANTES de desenhar a primeira amostra. A preparação e os limites em bits
continuam sendo contabilizados. Esse certificado é diferente de simplesmente
observar alta taxa de aceitação num benchmark.
