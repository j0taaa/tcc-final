# Lei de lotes com tabelas locais e visitantes assíncronos

Prova escrita candidata. Não é prioridade confirmada, prova de implementação
ou promessa de latência. Estratificação e desigualdades simétricas são clássicas.

## 1. Kernel, histórias e tickets

Fixe K>=1 rótulos antes de produzir qualquer saída. O decoder individual é
uma árvore de horizonte finito T, com histórico completo h. No nó h ele usa
I uniforme em {0,...,W_h-1}, W_h inteiro positivo, e aleatoriedade auxiliar
Z_h independente. A ação é F_h(I,Z_h). O modelo, o parser, as probabilidades,
a coordenada escolhida e W_h podem depender arbitrariamente de h.

O filho registra TODA a ação relevante e a história anterior. Histórias
divergentes não se reunificam. FAIL/parada são absorventes. Os kernels não
dependem das outras trajetórias, dos seus resultados ou da ordem de serviço.
Os auxiliares são independentes por rótulo/nó. RNGs ideais independentes são
a especificação probabilística; um PRNG real não é uma prova de independência.

Para cada nó h, atribua independentemente uma permutação uniforme pi_h dos
K estratos. O rótulo i, se visitar h, recebe

    R_hi uniforme em {0,...,W_h-1},
    I_hi = floor((pi_h(i)*W_h + R_hi)/K).

Permutações e R são independentes entre histórias; não há fase aleatória
compartilhada. As tabelas podem ser sorteadas preguiçosamente. Não se espera
outro visitante. Uma chave repetida (h,i) retorna o mesmo ticket; não sorteia
um segundo kernel. Cada nova chamada aleatória exige um novo nó/chave.

A permutação também é preguiçosa: ao chegar um rótulo ainda não atendido,
sorteie uniformemente um dos estratos não atribuídos e remova-o por uma troca
Fisher–Yates esparsa. Condicionadas as entradas reveladas de uma permutação
uniforme, o estrato de qualquer rótulo não revelado é uniforme nos restantes.
Indução no número de consultas prova a mesma lei, até para ordem de consultas
adaptativa sem acesso às entradas ainda não reveladas. Não é preciso alocar K
estratos quando apenas um rótulo visita o nó.

## 2. Lema local para QUALQUER subconjunto de visitantes

Defina a_s=E[a(floor((sW+R)/K))], s=0,...,K-1, para a>=0. Os KW valores
sW+R particionam {0,...,KW-1}; cada ticket tem K preimagens. Portanto

    (1/K) sum_s a_s = E_uniforme[a(I)].                    (1)

Para m rótulos distintos, 1<=m<=K, a permutação lhes atribui um subconjunto
uniforme de m estratos. Seus R são independentes. Logo

    E[prod_{i em visitantes} a(I_i)]
       = e_m(a_0,...,a_{K-1}) / binom(K,m)
       <= ((1/K)sum_s a_s)^m.                             (2)

e_m é a soma dos produtos de m índices distintos. A última desigualdade é
Maclaurin. Também pode ser provada sem invocá-la: para soma fixa, substituir
duas entradas x,y por (x+y)/2 preserva os termos lineares e aumenta xy; a
expansão e_m=e_m(resto)+(x+y)e_{m-1}(resto)+xy e_{m-2}(resto), com coeficientes
não negativos, não diminui e_m. O máximo no simplex compacto é atingido no
vetor constante por suavizações (ou maximização e continuidade); nele a
expressão é binom(K,m)*media^m. Z auxiliares independentes podem ser integrados
em a(I) sem modificar (1)-(2).

Cada visitante individual tem ticket uniforme, mesmo W<K e K não divide W.
Para g real, seja mu_s=E[g(I)|estrato s], mu=media_s mu_s. Para dois rótulos
distintos, os resíduos dentro dos estratos são independentes, e

    Cov(g(I_i),g(I_j)) = -Var_s(mu_s)/(K-1), K>1.          (3)

Assim, para m visitantes,

    Var(sum_i g(I_i))
      = m Var_uniforme(g) - m(m-1)Var_s(mu_s)/(K-1).        (4)

Auxiliares Z independentes são novamente admitidos, substituindo mu_s por
E[g(F(I,Z))|s]. Não se usa ordenação segundo o verificador desconhecido.

## 3. Lei de execução preguiçosa

Considere primeiro TODAS as tabelas independentes previamente sorteadas na
árvore finita (árvore infinita contável com horizonte finito usa a construção
produto correspondente). Elas determinam as K trajetórias. Executar rótulos
em série, em lockstep ou numa ordem intercalada apenas revela entradas já
definidas: a lei conjunta não muda. O serviço precisa terminar todas as
trajetórias pedidas; não selecionar o conjunto final com base em resultados.

Os visitantes de h são determinados por tabelas de ancestrais, independentes
da tabela de h. Portanto, condicionando nos ancestrais, qualquer conjunto de
m visitantes ainda recebe (2)-(4). Tabelas previamente reveladas de outros
ramos não interferem, pois nunca são reunidos. A geração preguiçosa por um
RNG ideal corresponde a essa lei, embora uma mesma seed não precise produzir
realizações idênticas quando se muda a ordem dos pedidos.

Para a marginal de UM rótulo, condicione somente em sua história: a tabela
seguinte é nova e a atribuição de estrato é uniforme. Seu kernel é exatamente
F_h com ticket uniforme e Z original. Indução preserva toda a trajetória.
Não confundir isto com independência condicional dado o histórico de TODO o
lote: revelar tickets de outros rótulos muda a lei condicional restante.

Projetividade com K FIXO: a lei de qualquer subconjunto de rótulos é a mesma
se os demais rótulos não forem executados, mantendo as tabelas de K estratos.
Nas tabelas previamente sorteadas, o caminho de um rótulo é função apenas de
suas entradas e auxiliares. Revelar entradas de outros não altera esse caminho.
Isso não autoriza trocar K pelo tamanho do subconjunto: mudaria a partição.

## 4. Teorema de cobertura para qualquer verificador terminal

Se Q_h é a lei terminal do decoder individual a partir de h, para TODO
conjunto A, sem acesso a A durante a geração,

    Pr_S(algum dos K resultados em A) >= 1-(1-Q_raiz(A))^K. (5)

Mais geralmente, m visitantes em h têm probabilidade de falharem todos
<= (1-Q_h(A))^m, mesmo que m seja desconhecido ao atender o primeiro pedido.

Prova por indução no horizonte restante. Nas folhas o resultado é imediato.
Após as ações no nó, grupos nos filhos hx são independentes e o indutivo
limita sua falha por prod_i a(x_i), a(x)=1-Q_hx(A). A média de a sob o kernel
é 1-Q_h(A). Integre Z por visitante, aplique (2) e conclua. Nada pressupõe
proximidade dos logits de histórias diferentes.

O máximo de QUALQUER pontuação terminal domina estocasticamente o máximo iid:
aplique (5) ao conjunto de saídas cuja pontuação é maior que cada limiar.
Isso não é pass@1 melhor nem acerto semântico de uma amostra.

## 5. Variância terminal

Para f de segundo momento finito, a média do lote é não enviesada e

    Var_S((1/K)sum_i f(Y_i)) <= Var_Q(f)/K.                (6)

Prove recursivamente que dois visitantes no mesmo h têm Cov(f(Y_i),f(Y_j))
<=0. Condicionadas as próximas ações, visitantes em filhos diferentes têm
futuros independentes; os no mesmo filho têm covariância <=0 por indução.
As médias condicionais formam g(x)=E_Q_hx[f]. A covariância destas médias
é (3), integrando os auxiliares. A lei da covariância total conclui o passo.
Cada marginal é Q; expandir a variância da soma prova (6).

## 6. Estriteza e uso com CFGs

Para K=2 no primeiro nó, a diferença de cobertura é pelo menos
Var_s(E[1-Q_hx(A)|s]); melhorias posteriores só podem aumentá-la. O benefício
é estrito quando o ruído escolhido influencia diferentemente a chance de
sucesso entre os estratos. Para evento que é prefixo dos tickets da raiz,
K visitantes alcançam min(1,Kp), ótimo entre lotes com as mesmas marginais.
Essa hipótese é uma condição matemática, não um benchmark ou hipótese que
todo evento semântico satisfaz. Se a coordenada não informa A, o ganho pode
ser zero. Não há um piso de ganho estrito universal para todos os verificadores.

Corolário: tome F_h como a transição COMPLETA de um EPIC/dLLM sob sua GLC,
com rankings, filtros, tentativas recusadas, EOS/PAD e commits originais.
Estratifique uma coordenada bruta de seu ruído e deixe todo o resto iid.
As leis marginais de tokens ORIGINAIS e trajetórias permanecem as nativas;
(5)-(6) valem para qualquer verificador de JSON/DSL, incluindo dry-run. Isto
não calcula o posterior exato, não fortalece a garantia sintática do EPIC e
não garante ausência de FAIL. Seu parser/tokenizador e suas ambiguidades
permanecem parte do kernel original, sem serem reimplementados.

Não basta estratificar o primeiro vencedor se a recuperação usa a ordem dos
demais Gumbels: isso modifica o kernel. O corolário trata o ruído original
inteiro e a mesma transformação determinística do decoder.

Na implementação EPIC auditada, somente a história dos inputs do modelo NÃO
basta: `resamples` é cumulativo e `max_resamples` afeta a parada futura. O
adaptador registra também snapshots do estado da função nativa ANTES do
ruído: bloco/passagem, palavras decodificadas/EOS, posições de rejeições
cumulativas, agenda de transferências e política. Toda essa sequência é
retida; estados anteriormente distintos não são reunidos. Tempos registrados
em `resamples` não afetam o controle, que usa seu comprimento, e são excluídos
da chave. Limites de parede continuam fora da equivalência garantida.

O snapshot é uma leitura transitória do frame nativo, sem alterar seu fluxo.
Hashes de fonte do ruído e da função `generate` são checados; código diferente
é recusado. Esses checks não verificam formalmente o binário/parser. A chave
inclui um namespace comum de modelo/tokenizador/GLC/configuração imutáveis;
o chamador não pode reutilizá-lo com pesos, léxico ou gramática diferentes.

## 7. Grades de ruído e implementação numérica

CPU torch float64 transforma z uniforme de53 bits em z*2^-53. No CUDA da
versão local2.8, curand_uniform2_double usa `_curand_uniform_double_hq`:
z=x XOR(y<<21),53 bits, depois RN(z*2^-53+2^-54). O kernel uniform CUDA troca
o valor1 por0. Portanto, a lei CUDA NÃO é simplesmente uniforme em z*2^-53:
alguns valores da metade superior são arredondados com duplicidade. Para
preservá-la, estratifique o ticket z e aplique EXATAMENTE a transformação
original, incluindo empate IEEE e inversão da borda. Não usar uniformização
silenciosa. A prova abstrai transformações determinísticas em F_h.

Esta leitura de fonte não prova o binário, a qualidade do PRNG ou que outro
hardware/PyTorch tenha a mesma regra. A integração precisa fixar/checar seu
perfil e recusar perfis não auditados. Em CPU e CUDA, aliases de tokens são
identidades distintas; não são agrupados por texto para coordenar ruído.

## 8. Custo e fronteiras adversariais

Uma permutação materializada exigiria O(K) por nó e até O(K²T) no lote.
A representação esparsa por decisões adiadas exige O(m) itens num nó com m
visitantes e O(KT) itens no lote, além das chaves de históricos. Há duas
chamadas randrange e O(1) acessos de dicionário esperados por visitante, com
aritmética de O(log W+log K) bits; geração imparcial de inteiros e custo em bits
não são gratuitos. Guardar histórias integrais ingenuamente pode acrescentar
O(KT²) de tamanho; IDs persistentes de prefixos podem evitá-lo. Para um visitante
único não dispensar a tabela supondo que ninguém mais chegará. Transferências
CUDA, seleção da coordenada e sua escrita contam integralmente.

Cada trajetória tem a lei Q, logo a esperança da SOMA de qualquer custo
individual é igual à de K execuções iid. Porém forwards únicos com caching,
latência com paralelismo, custo de coordenação e máximos NÃO são esse custo;
podem ser piores. Tempo de parede usado para interromper pode depender do
lote e violar a hipótese de kernel próprio. Usar horizonte/limite operacional
comum e preservar FAIL, em vez de alegar equivalência de timeouts físicos.

Não há dominância sobre A26 que recalcula m estratos ao conhecer o grupo:
as partições K e m não são sempre encaixadas e podem favorecer eventos
diferentes. Também não há dominância sobre STMC, DAST ou sem reposição.

Contraexemplo à estratificação global de duas coordenadas: K=2, dois bits
uniformes por trajetória, cada coordenada usa os estratos0/1 e permutação.
Os dois bits da segunda trajetória são complementos dos da primeira. Para
o evento de paridade igual, ambos acertam ou ambos erram: cobertura1/2,
contra3/4 iid. O mesmo problema ocorre ao estratificar por timestep após
histórias já divergirem. A restrição por história e uma coordenada são
essenciais, não uma otimização que possa ser retirada depois.
