# Acoplamento por estado suficiente: identidade de ganho de reunião

Prova escrita candidata; novidade/suficiência para publicação em aberto.
Estratificação, Markovização e argumentos de martingale são antecedentes.

## 1. Especificação e comparadores

Fixe K>=2, horizonte T e estados suficientes s em cada camada t=0,...,T.
O kernel individual é s' = F_t(s,I,Z), I uniforme em {0,...,W_t(s)-1},
Z auxiliar independente. Estado suficiente determina esse kernel e a saída
terminal. Terminais/FAIL são absorventes; cada passo aumenta t, mesmo para
estado que permaneça igual. Não reutilizar a tabela numa camada diferente.

Para cada (t,s) crie independentemente uma permutação pi de K estratos e
R_i iid de W tickets. Cada visitante i recebe

    I_i = floor((pi(i)*W+R_i)/K).

M coordena rótulos que têm o mesmo (t,s), INCLUSIVE históricos diferentes.
H faz a mesma coisa só para históricos completos idênticos, com K fixo (A30).
Iid não coordena. Todos usam exatamente F_t; qualquer Z extra é iid por
rótulo. Não estratificar simultaneamente diferentes coordenadas independentes.

O resumo psi(h)=s é admitido somente se, para histórias h,h' de mesma camada
com psi(h)=psi(h'), suas próximas ações RESUMIDAS tiverem a mesma função
F_t(s,I,Z), não só um mesmo canvas ou mesma massa válida. Além disso, toda
saída observável/verificador reivindicado deve ser função do estado terminal.
Modelo/tokenizador/GLC/política são congelados e independentes do lote.

O tamanho K da tabela é fixo; marginalizar outros rótulos não muda o processo
de um subconjunto. Não comparar esta partição com a A26 que troca K por m.

## 2. Lema local conhecido

Para qualquer função g do filho, escreva

    mu_r = E[g(F_t(s, floor((rW+R)/K), Z))],
    mu = (1/K)sum_r mu_r,
    D_t(s,g) = Var_r(mu_r)/(K-1).

Permutação uniforme, R/Z independentes e a partição dos KW tickets dão:
cada marginal original; para quaisquer dois rótulos visitantes,

    Cov(g(s_i'),g(s_j') | ambos no mesmo (t,s)) = -D_t(s,g).

Para qualquer subconjunto de m visitantes e a>=0,

    E[prod_i a(s_i')] = e_m(mu_0,...,mu_{K-1})/binom(K,m)
                      <= (E_kernel[a])^m.

É Maclaurin, não um novo princípio. Vale para mapas arbitrários/descontínuos,
W não divisível por K e m desconhecido ao atender o primeiro visitante.

## 3. Teorema: marginais e cobertura SEM separação de históricos

Cada rótulo em M tem exatamente a lei original. Para todo conjunto A de
saídas terminais (não acessível ao algoritmo),

    Pr_M(algum Y_i em A) >= 1-(1-Q(A))^K.                  (1)

Prova da marginal: tabelas da camada t são independentes de todas as camadas
anteriores; condicionar na história de um rótulo mantém seu ticket uniforme.
Auxiliares mantêm sua lei. Indução nos passos.

Prova (1): seja q_t(s) a probabilidade original de NÃO chegar a A a partir
de s na camada t. No terminal q_T é o indicador de fracasso. Considere
U_t=prod_i q_t(S_i(t)). Dada a configuração COMPLETA da camada t, particione
por estado s. Tabelas de estados distintos são independentes. Dentro de
um estado com m visitantes, o lema local e a equação de backward original
q_t(s)=E[q_{t+1}(s')] dão

    E[U_{t+1}|configuração e passado] <= U_t.

Ao tomar expectativas e telescopar, E[U_T]<=q_0(s0)^K. Não se supõe que
futuros de histórias diferentes permaneçam independentes: podem se reunir.
É exatamente a diferença para uma indução somente em árvore de históricos.
O máximo de qualquer score final domina o máximo iid, aplicando (1) aos
seus conjuntos de supernível. Isto não promete pass@1 melhor.

## 4. Identidade exata de covariância

Se f é uma pontuação terminal de segundo momento finito, defina sua
continuação original g_t(s)=E[f(Y)|S_t=s]. Para dois rótulos i!=j,

    E_M[f(Y_i)f(Y_j)] - (E_Q[f])²
      = -sum_{t=0}^{T-1} E_M[1{S_i(t)=S_j(t)}
                             D_t(S_i(t),g_{t+1})].        (2)

Prova: V_t=g_t(S_i(t))*g_t(S_j(t)). Se os estados são distintos, tabelas
independentes e backward dão E[V_{t+1}|passado]=V_t. Se iguais, o lema local
subtrai D_t(s,g_{t+1}). Projetividade de K fixo torna o kernel do par
independente da presença de outros rótulos. Telescopar V_t conclui (2).
Não é necessário f monótono, ordem semântica de estados ou estabilidade de
logits. É necessário que f dependa somente do estado terminal suficiente.

Consequência: média não enviesada e

    Var_M((1/K)sum_i f(Y_i)) <= Var_Q(f)/K.                (3)

Todas as energias são não negativas. (2) quantifica quando a garantia é
estrita; não estabelece um piso positivo para todo f/kernel.

## 5. Vantagem comparativa contra H, além de não piorar iid

Seja B_t o evento de que os históricos do par já divergiram antes da
transição t. A identidade de diferença é

    Cov_H(f_i,f_j) - Cov_M(f_i,f_j)
      = sum_t E_M[1{B_t e S_i(t)=S_j(t)} D_t(S_i(t),g_{t+1})]
      >= 0.                                              (4)

Prova: até a primeira divergência, os kernels do par em H/M coincidem; podem
ser acoplados literalmente. A distribuição dos prefixos ainda iguais é,
portanto, a mesma. Em H, uma vez diferentes, os históricos nunca voltam a
coordenar: futuros do par são independentes, mesmo se estados coincidem.
A identidade telescópica de H só tem energias dos prefixos ainda iguais.
Em M, (2) acrescenta as energias das reuniões B_t. As contribuições antes
da divergência são iguais; subtrair prova (4). A projeção de dois rótulos
de um lote K é válida porque a tabela usa K fixo, independentemente de m.

Logo, para QUALQUER pontuação final,

    Var_M(media do lote) <= Var_H(media do lote).         (5)

Para K=2 e f=1_A,

    pass@2_M(A) - pass@2_H(A)
      = sum_t E_M[1{reunião após divergência}D_t(s,g_{t+1})]. (6)

Isso também dá dominância do máximo de TODO score em K=2. Para K>2, a prova
atual dá cobertura >=iid e variância <=H, MAS NÃO cobertura/max-score >=H.
Não generalizar a identidade de pares para probabilidade de união de K eventos.
H de raiz apenas é ainda outro controle, com menor custo; deve ser medido.

Corolário de retries/validação: fixe K=2 e gere candidatos em ordem; após
falha dos dois, inicie um par independente com nova tabela. O verificador
apenas decide parar/continuar, nunca modifica o sampler. Se p=Q(A)>0 e
c=pass@2 do método, a quantidade esperada de chamadas ao verificador até
o primeiro sucesso é

    E[N_validacoes] = (2-p)/c.

Prova: em cada ciclo, faz-se uma validação e uma segunda com probabilidade
1-p; custo médio2-p. Com probabilidade1-c, recomeça um ciclo independente.
A equação de renovação R=(2-p)+(1-c)R prova a fórmula. Por (1)/(6), M nunca
exige MAIS validações em esperança que iid ou H; é estrito quando (6)>0.
Na família da seção6, cai de2 para1.5 validações. Isso NÃO é um benchmark.

Não converter chamadas em tempo quando validações/candidatos têm custos
dependentes da saída. Os candidatos que seriam gerados possuem marginais
Q, mas o segundo realmente executado após uma falha tem lei condicional,
e a saída selecionada NÃO é automaticamente uma amostra de Q condicionada
em A. Provar a lei deste outro objeto exige análise adicional. O método não
solicita verificar JSONs que já falharam nem elimina falhas do denominador.

Se o par INTEIRO é gerado antes da verificação, sua soma esperada de custo
individual é2*mu, mas há coordenação extra gamma. Custo por ciclo até obter
sucesso é (2*mu+gamma)/c, sob ciclos independentes e custos finitos. A redução
contra H exige c_M/c_H > (2*mu+gamma_M)/(2*mu+gamma_H); não omitir o custo
extra. Uma estratégia iid que pára após cada candidato é controle competente
e pode ser mais barata que gerar pares inteiros; não alegar vitória de compute
contra ela somente a partir da cobertura do par.

## 6. Corolário de uso e separação matemática

Considere ordens distintas de commitment de campos sintáticos já determinados,
que voltam ao mesmo canvas/controle antes de uma decisão textual ainda livre.
Se a dLLM é stateless, os logits seguintes e o parser/fallback a partir desse
estado são os mesmos. M pode coordenar novamente; H não. A diferença de
pass@2 é exatamente a energia de continuação útil em (6).

Família de prova: primeira transição escolhe ordem0/1 com probabilidade1/2;
segunda preenche o restante e reúne todos no estado r; terceira produz
um de dois JSONs válidos com probabilidades1/2, por um ticket0/1. K=2:
H separa ordens na raiz e suas escolhas finais são iid, cobertura3/4 para
qualquer uma das alternativas; M reúne r e atinge cobertura1. Variância
da média de seu indicador passa de1/8 a0. São leis exatas por construção,
NÃO um benchmark nem uma medição de modelo. JSONs podem representar duas
ações candidatas sujeitas a dry-run; o algoritmo não conhece a ação aceitável.
Uma integração nativa com Gumbels auxiliares pode ter energia menor que1/4.

Sem reuniões ou sem energia de continuação, M não melhora H em resultado.
Se h omite um budget de rejeição, um estado do modelo ou parte da saída que
o verificador usa, o corolário falha. Não juntar apenas JSONs de mesmos bytes
com IDs/tokenização diferentes: o próximo kernel pode distingui-los.

## 7. Assincronia, implementação e custo

Tabelas pré-atribuídas por (t,s) determinam cada trajetória. Executá-las em
série/intercaladas apenas revela valores. Visitantes de camada t dependem
somente de tabelas anteriores; não há ciclos na chave. Uma permutação esparsa
por decisões adiadas dá a lei de visitantes desconhecidos. Não reúna visitas
de fases diferentes nem reutilize o estrato de um rótulo numa fase posterior.

O resumo nativo deve ser auditado contra TODOS os dados que afetam controle:
canvas de IDs, generated_words/EOS, bloco/passagem, agenda de transferência,
rejeições cumulativas, parâmetros e modelo/tokenizador/GLC/léxico congelados.
Tempo das rejeições não determina decisões na fonte auditada, mas timeouts
de parede dependentes do lote continuam fora da garantia de marginais.
O sampler só troca uma coordenada bruta e aplica sua transformação CPU/CUDA
original; não reconstrói logits, posteriores ou rankings alternativos.

Computação da chave, seleção de coordenada, RNG inteiro, acesso a tabela,
CPU/GPU e memória são custos. Coordenação não adiciona forwards por si,
mas cache pode aproveitar menos duplicatas ao aumentar diversidade. A prova
não estabelece superioridade de tempo contra EPIC/DAST/Array-RQMC ou toda
codificação por fatores. Estado suficiente é uma obrigação de prova/auditoria,
não um nome para um hash. Nenhuma hipótese de publicação foi concluída.
