# Contrato, equivalência e custo (prova escrita)

## Entradas e operação

Uma gramática G, n slots, tokens originais em suportes finitos D_i, conversão
composicional token→bytes, canvas fixado e propostas ordenadas por
(-confiança, posição, token). A gramática é a de JSON RFC 8259. Compilação
mantida: LL(1) verificada, EOS ausente, limites explícitos. Não criar palavras
abstratas Sigma*, agregar aliases, ignorar slots ou usar probabilidades para
descartar conclusões estruturais. Um top-K inicial define o suporte declarado;
não afirma cobertura do vocabulário inteiro.

F é o conjunto de conclusões válidas. O guloso visita TODAS as propostas e
aceita p_j se há y em F com p_j e todas as anteriores aceitas. Depois filtra
as aceitas por confiança >=theta, conserva os primeiros c slots distintos
e fixa seus tokens. Se esse lote é vazio, fixa a primeira proposta aceita.
Se nenhuma proposta foi aceita, fixa o menor token viável no primeiro slot
livre. Esse fallback é parte do contrato dos novos controles; não é o fallback
arbitrário da M24, nem se presume igualdade de saídas com aquele experimento.

## Lema 1 — equivalência lexicográfica

Para y válido, b_j(y) indica o casamento de p_j. Maximize
L(y)=sum_j 2^(m-j-1)b_j(y), com inteiros exatos. O bit de uma prioridade é
maior que a soma dos posteriores. Se há conclusão contendo a primeira proposta,
o máximo a contém; caso contrário todas a rejeitam. Restrinja à decisão e repita.
Por indução, o vetor b coincide com todas as decisões do guloso. Propostas
duplicadas contribuem bits distintos, uma vez por proposta; cada token tem um
único fechamento na floresta. A soma entre filhos é válida por decomponibilidade
dos slots. Empates de testemunho não afetam o lote; fallback especificado à parte.

Este é um lema clássico de prioridades lexicográficas, não uma descoberta.

Na consulta nativa, multiplicar L por 2^(-m+1) transporta os mesmos bits
como díades 2^-j. Para m<=1075, cada peso é exatamente representável em
binary64, inclusive subnormais. A comparação NÃO soma pesos arredondados:
normalização preserva termos originais como Fraction e o parser mantido soma
BigUint em unidades de 2^-1074. Logo todos os bits que definem a decisão
permanecem exatos. O objetivo público arredondado é somente diagnóstico;
recupera-se o vetor pelo casamento dos tokens originais. Uma API/backend que
só compare somas arredondadas não satisfaz este contrato. Recusar m>1075 nesta
referência. O caminho foi reconstruído/testado também nos bits de menor peso.

O refinamento compacto transporta diretamente 2^(m-j-1-1074). Em unidades
2^-1074, a soma BigUint é o inteiro L de m bits, removendo bits de escala
desnecessários. Para m<=1075 todos os pesos são díades representáveis, não
há arredondamento na comparação. Exige IEEE subnormais preservados; o runner
desativa flush_denormal explicitamente e registra isso. Confidências originais
continuam separadas da prioridade. Não deduzir decisões do score público float.

Na representação compacta, cada slot possui uma árvore de prefixos próprios
compartilhados. Cada token tem uma aresta terminal privada que emite seu último
byte e carrega sua identidade/recompensa. Um token que é prefixo de outro
fecha numa aresta para a próxima fronteira, enquanto a continuação segue para
um nó próprio; aliases têm fechamentos distintos. Toda sequência de tokens
originais determina um único caminho, e todo caminho completo fecha exatamente
um token por slot. Os bytes e a soma das prioridades são os mesmos. Assim
interseção com a gramática e maximização são preservadas, mesmo se produções
sintáticas cruzam limites entre tokens. Tokens suportados não têm emissão vazia;
EOS ausente. É a representação já usada em cfg_posterior.py, não uma invenção
desta tentativa. Os três métodos nativos recebem a mesma GLC compacta obtida
por binarização seguida de normalização, que preserva a linguagem; muda a
representação, não o JSON ou suporte admitidos.

O parser nativo pode guardar apenas a melhor derivação de cada célula, pois
as prioridades são conhecidas ANTES de construir/normalizar o grafo da consulta.
Isso dispensa materializar todas as alternativas de uma floresta reutilizável,
mas repete construção/parsing nos forwards seguintes. Seja Q o custo completo
de uma consulta nativa, incluindo grafo, precisão, reconstrução e validação:
lex costuma pagar sum_t Q_t (mais fallback quando necessário), o guloso nativo
paga sum_t sum_j Q_tj. Os domínios restringidos podem baixar Q_tj, testemunhos
podem dispensar consultas e a floresta pode amortizar preparação. Portanto NÃO
há teorema de superioridade universal: o benefício físico precisa ser medido
contra esses controles com o mesmo kernel e informação.

## Lema 2 — prefixo observável

Fallback conjunto: seja p o primeiro slot livre, d=|D_p|,
b=ceil(log2(d)) e r(t)=d-1-index_ordenado(t). Maximizar
2^b L(y)+r(y_p) preserva todo vetor primário, pois r<=2^b-1.
Se nenhuma proposta livre é aceita, todos os bits livres são zero sobre F
(bits de posições fixadas são constantes); então o mesmo testemunho contém
o menor token viável no slot p. Logo uma única consulta nativa resolve também
esse fallback, sem testar cada token. Exigir m+b<=1075 no transporte atual.
É um desempate lexicográfico clássico, delimitado à política especificada.

Controles usam a mesma informação: uma consulta gramatical ponderada obtém
o menor token de um slot; SAT pesquisa prefixos de domínio por bisseção.
No guloso nativo, uma consulta sem propostas também calcula esse mínimo.
Se seu slot permanece livre e o testemunho continua válido após contrações,
ele continua mínimo: restringir F não pode criar um valor menor antes ausente.
Se o slot muda ou o testemunho foi substituído, invalide esse certificado e
recalcule. Nenhuma propriedade de mínimo é inferida de uma consulta que falhou.

Atalho comum: se as propostas cobrem exatamente os slots livres e seu
completamento concreto pertence a F, o guloso aceita todas, em qualquer ordem.
O filtro/cap/fallback é conhecido diretamente. Aplique isso igualmente a todos
os métodos e prepare seus engines apenas no primeiro passo em que for preciso.
Atualize estruturas já preparadas com somente os commits observáveis, e
substitua/invalide testemunhos e certificados de mínimo conforme necessário.
O checker linear JSON é válido apenas para a gramática JSON aqui declarada.

Top-K parcial: seja c o k-ésimo maior valor, H os IDs com valor>c, E os IDs
com valor=c. Sempre |H|<k<=|H|+|E|. H junto aos k-|H| menores IDs de E,
ordenados por (-valor,ID), é exatamente o prefixo do sort estável completo.
O custo é O(V+k log k) com seleção linear, em vez de ordenar V itens.
Isso beneficia TODOS os métodos; não alterar probabilidades ou suporte.

As propostas acima de theta formam um prefixo da ordem. Uma decisão gulosa
depende apenas de anteriores aceitas, nunca de posteriores. Logo, quando há
uma aceitação elegível, basta visitar o prefixo até atingir c slots distintos
ou seu final. Propostas posteriores não mudam esses commits. Se o lote fica
vazio, não houve aceitação no prefixo: a primeira aceitação global é viável
contra o canvas original. Procurá-la e fixá-la reproduz o fallback. Se nenhuma
existe, o fallback canônico depende somente de F. Portanto o propagador só
precisa aplicar os commits que realmente aparecerão no canvas seguinte.
Não se pode persistir TODAS as aceitações de uma consulta gulosa especulativa:
o filtro deixaria no estado interno tokens que o modelo ainda verá mascarados.

## Lema 3 — suporte exato por inside e reachability

A floresta acíclica é uma disjunção de alternativas AND. Cada AND combina
filhos com slots disjuntos. Cada conclusão da raiz consome exatamente n escolhas.
Um nó é live se possui uma alternativa com escolhas permitidas e filhos live.
Uma alternativa é reachable se seu pai OR é reachable e ela é live. Um token
é viável iff alguma alternativa de fechamento sua é live e reachable.

Suficiência: uma alternativa live tem derivações em cada filho; decomponibilidade
permite combiná-las. Um caminho reachable fornece um contexto até a raiz,
também com derivações nos irmãos. Assim há uma conclusão completa contendo
a escolha. Necessidade: toda derivação válida testemunha live e reachability
em cada um dos seus nós/alternativas. Ambiguidade não afeta existência; a
restrição LL(1) vem do compilador mantido, não de uma necessidade do propagador.

## Teorema — geração gulosa sem recomputações globais

Inicialize contadores live (alternativas viáveis por OR) e reach (entradas de
alternativas reachable por nó), e índices dos fechamentos de cada token.
Ao fixar um slot, desative apenas escolhas alternativas. Um AND que perde um
filho live fica false; um OR cujo contador live zera propaga aos AND pais.
Remova o fluxo de alternativas false e de nós que perdem seu último contexto
reachable. Todas as mudanças são true→false. Nenhuma escolha é removida só por
baixa probabilidade. Pela invariância do Lema 3, o suporte de tokens permanece
exato. Pelo Lema 2, cada lote coincide com a política completa especificada.

Se gramática/tokenizer/domínios iniciais permanecem iguais, commits não são
desfeitos e forwards determinísticos recebem o mesmo canvas, a trajetória
inteira e os tokens finais coincidem por indução. Novas probabilidades/ranks
não alteram a floresta. Uma execução recusada/timeout é inconclusiva; equivalência
é de execuções conclusivas, não dos seus prazos físicos.

Corolário de preservação de resultado: para qualquer avaliador semântico
aplicado somente à saída, g(y_lex)=g(y_guloso), quando os decoders compartilham
predições/propostas e concluem. Com aleatoriedade compartilhada que não é
consumida pelos seletores, a distribuição das saídas também é a mesma. Isso
evita justificar qualidade por uma soma substituta; não prova que o guloso seja
bom, nem que sua política seja equivalente à do EPIC ou da M24 histórica.

## Custo e antecedente

Se H conta nós, alternativas, incidências de filhos e escolhas indexadas,
preparação dos contadores custa O(H). Cada alternativa/fluxo desaparece no
máximo uma vez; cada incidência é visitada um número constante de vezes.
Visitar escolhas de um slot é necessário somente quando ele é fixado uma vez.
Ao longo de T forwards, com P propostas totais, custo de seleção/propagação
é O(H+P+n), além da ordenação (sum_t O(P_t log P_t)) e escrita dos updates.
Contadores usam O(log H) bits, prioridades lexicográficas m bits. Assim não
esconder custo em bits: O((H+P+n)log(H+n+max token_id)) é um limite conservador
para bookkeeping. Não inclui custo real dos forwards nem compilação da floresta.

Uma avaliação lexicográfica por passo visita O(H) alternativas com scores de
m bits; reconstrução custa O(tamanho da derivação). Booleano com testemunho
faz uma a P_t+1 avaliações por passo; problemas fáceis podem exigir só uma.
Isto explica uma economia de trabalho, não uma promessa de aceleração física.

O limite amortizado e a propagação AND/OR são conhecidos: Quimper e Walsh
(https://arxiv.org/pdf/0903.0470), §GRAMMAR, p.3. A especificação acima os liga
a propostas tokenizadas, filtro/cap e commits observáveis de dLLMs. Não alegar
que adicionar o nome dLLM cria uma nova contribuição teórica.

## Corolário de uso e limites

Poda comum de relevância: retenha o fechamento transitivo da raiz pelas
dependências de TODAS as alternativas. Cada derivação da raiz só visita esse
fechamento, portanto nenhuma conclusão, escolha de token ou objetivo é perdido.
Conversamente, cada derivação do grafo retido já pertence ao original. A lei
de massa/amostragem e os seletores são preservados. Essa eliminação clássica
de células sem contexto custa O(H) e é cobrada igualmente a todos os métodos
baseados na floresta. O limite amortizado passa a usar H_retido, sem esconder
H_original pago na compilação/poda. Não constitui novidade científica.

Infilling de JSON com suporte inicial congelado, sem remasking, satisfaz as
hipóteses. Pode-se conservar a política de confiança e as saídas e pagar uma
compilação por documento, amortizando a propagação durante a geração. Isso
preserva o acerto observado do guloso especificado, sem inferir qualidade do
objetivo MWPC ou mudar a distribuição. Custo completo é compilação+contadores+
sum_t(forward+suporte/ordenação+seleção+update)+saída. Medir esse custo é necessário
para estabelecer utilidade física. Top-K dinâmico, crescimento do vocabulário,
gramática nova e remasking invalidam a hipótese e precisam de outra preparação.

## Controle de testemunha por contagem

Maximizar C(y), o número de propostas casadas, não reproduz em geral o
guloso lexicográfico. Use o testemunho apenas como cache e execute depois
a política gulosa. Reutilizar tokens desse testemunho evita consultas sem
alterar decisões: se ele contém uma proposta, ela tem completamento válido.
Se o máximo não casa nenhuma proposta de slot livre, nenhuma delas é
individualmente viável; contribuições de slots fixados são constantes.
Então 2^b C(y)+r(y_p) fornece o fallback canônico diretamente. Caso
contrário, a propriedade de mínimo global não pode ser inferida desse
testemunho e seu certificado é invalidado. Mesmo grafo/kernel/verificador
do lexicográfico, custo integral; nenhuma promessa de vantagem em geral.

## Referência de dedução guiada pela raiz

Preveja S na fronteira inicial. Em CNF sem consumo epsilon, prever A em v
ativa produções A->byte e expectativas A->B.C após B; agrupe previsões
repetidas por (A,v). O escaneamento cria células (A,v,w) nas arestas de
byte admissíveis. Completar B(s,v) cria expectativas por C em v, guardando
score/backpointer de B; completar C(v,w) soma seu score ao prefixo B e
completa A(s,w). Predições são condições de alcance, sem multiplicar o
score do contexto. Agrupar prefixos de mesmo(A,s,C,v) pelo maior score é
válido para max-plus, pois todo C(v,w) combina com qualquer desses prefixos.
Para a floresta, conserve TODOS os prefixos/alternativas, inclusive os que
não são os melhores; mudanças de tokens podem torná-los necessários.

A CNF não consome epsilon, e cada aresta vai para um vértice maior. Processe
finais crescentes e, dentro de cada final, inícios decrescentes. Completar
um filho direito(v,w) gera pai(s,w) com s<v, portanto o filho foi finalizado
antes do pai. Prefixos esquerdos acabam antes do filho direito começar;
nenhuma melhora pode chegar após a finalização. Previsões na posição atual
só escaneiam para vértices futuros. Por indução, cada célula guarda o máximo
exato; a variante que retém alternativas guarda todas as derivações que
um prefixo da raiz pode alcançar. Toda derivação completa da raiz satisfaz
as previsões ao percorrer seus filhos, logo nenhuma conclusão completa é
perdida. A reconstrução produz o mesmo caminho de tokens/bytes/recompensas.

Isto especializa EarleyFast/semiring parsing: Opedal et al. (2023), §§5/6,
notas7/10, https://aclanthology.org/2023.acl-long.204.pdf . Não é novo teorema
de parsing. O limite conservador usa O(|G| V^3+|G| E) deduções em DAG com
V vértices e E arestas, O(|G|V²+E) armazenamento de melhores prefixos/células,
multiplicado pelo custo de operações sobre scores de(m+b)bits. A floresta
acrescenta espaço/custo de suas alternativas, até O(|G|V³+|G|E), e não
herda o armazenamento do max-plus. Indexação, geometria, priorização na
agenda, validação e reconstrução são contados; não alegar aceleração
universal. A redução de células irrelevantes é uma vantagem de execução
condicional conhecida, a ser confrontada com os mesmos controles guiados.

Prefixo especulativo: teste conjuntamente as primeiras c propostas elegíveis
(todas com confiança>=theta, slots distintos). Se existe testemunho conjunto,
cada uma é aceita pelo guloso, pois o mesmo testemunho satisfaz seus prefixos;
o lote é exatamente esse prefixo. Sem propostas elegíveis, testar a primeira
proposta livre produz o fallback guloso se ela é viável. Se o teste falha,
não deduza impossibilidade individual: execute a consulta lexicográfica
completa e seu fallback canônico. Assim há no máximo duas consultas por
passo, uma delas em domínio restringido. Duplicatas conflitantes no prefixo
recusam o atalho. É batching clássico com resolução exata, não novo lema.
Compare também essa implementação nos dois kernels e com controles guiados.
