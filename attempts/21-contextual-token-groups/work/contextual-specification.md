# Grupos contextuais, sem pressupor estado da lacuna

Mantenha o transdutor e CFG de20. Para posição i, estado lexical q e suporte D_i,
particione os tokens com T_q(t) definido pelo par (estado posterior, emissão).
Cada grupo g tem membros M_iqg. Arestas para essa emissão terminam em MARK(i,q,g).
Um caminho escolhe um grupo por posição e tem estado anterior q explícito.
Grupos de estados diferentes podem compartilhar originais. Não são uma
partição global independente do contexto, como uma aplicação direta da
Proposição2 de FactorDLM exigiria. Eliminação condicionada de variáveis e
composição ponderada são antecedentes, não uma nova álgebra de inferência.

**Representação.** Cada palavra original válida determina exatamente uma
sequência de estados/grupos. Qualquer escolha original entre os membros de
cada grupo de um caminho preserva por indução seus estados, emissões e CFG.
Logo o conjunto representado é EXATAMENTE o conjunto de palavras válidas no
suporte; tokens, aliases, slots e EOF são conservados. O lexer separado e MARK
usam a prova escrita anterior; esta implementação não é posterior mecanizado.

**Consulta original.** Um original t é viável em i se e somente se algum grupo
suportado nesse slot o contém. Comprometer t desativa TODOS os grupos que não o
contêm, mantendo aqueles com t, inclusive em estados distintos. Prova: a
representação acima é bidirecional. GAC clássico dentro/fora preserva os grupos
em algum caminho raiz, portanto a união é necessária e suficiente. Cada termo
pode ser desativado uma única vez entre reconstruções. A política gulosa visita
as mesmas propostas e recebe respostas iguais; fallback usa min ORIGINAL;
a indução na trajetória é a mesma de19. Uma proposta por posição na avaliação.

**Otimização.** O melhor score de um grupo é max_{t em M} score_i(t), com argmax
original. Não somar scores de tokens incompatíveis. Cada caminho lê exatamente
um token por posição, então a melhor expansão se separa por slot e max-plus
calcula exatamente o objetivo lexicográfico/commitment especificado. Na
referência, score primário usa bits inteiros e secundário prioriza menor
original no primeiro slot livre. Duplicatas de propostas, se admitidas no
oráculo, somam apenas quando casam O MESMO token. Transporte dyadic é exato.

**Expansão estável.** Prepare todos os estados alcançáveis por algum prefixo
sobre D inicial, inclusive aqueles sem completamento CFG. Se cada token novo,
em cada estado preparado de seu slot, rejeita ou produz um par já presente,
não cria nova transição, estado posterior ou emissão. Por indução de camadas,
o produto e circuito não mudam. Acrescentar membro só muda o mapa para IDs
originais. Em slots livres os grupos já eram habilitados; em slots comprometidos
não entram novos originais. Logo GAC decremental permanece válido. Se há
comportamento novo, RECOMPILAR; não ignorá-lo por estar ausente da floresta
podada pela raiz. Isso evitaria descobrir um novo caminho antes impossível.

**Comparação matemática delimitada.** Para cada q, classes globais de20 válidas
em q mapeiam para grupos contextuais. A definição global exige igualdade em
todos os estados, inclusive q, logo a aplicação é bem definida e sobrejetiva:
|grupos_q|<=|classes globais válidas_q|. A mesma relação vale para o número de
alternativas de token-close com igual emissão/estado por slot, sem multiplicar
ou apagar scores. Palavras 'a' e 'b' ficam juntas em STR, mas diferentes
em ESC; um contexto que só admite STR pode ativar b sem nova topologia local,
ainda que introduza classe global. Este é exemplo de PROVA, não benchmark.

O benefício inclui evitar uma recompilação quando há classe global nova mas
imagem contextual estável. Nenhum teorema prova wall universal, qualidade
semântica, prioridade ou exclusividade contra uma implementação clássica que
faça a mesma eliminação. Custos de ler/classificar originais permanecem.

**Custo completo.** Com cache, examinar token novo em Q_i custa
O(sum_i sum_{t novo}sum_{q em Q_i}|bytes(t)|), mais associação de membros e
probabilidades. Preparação tem O(sum_i sum_q sum_g (1+|emissão_g|)) arcos.
Uma consulta ponderada examina membros para max/argmax e o grafo de parsing,
incluindo inteiros de m+b bits; GAC paga cada termo desativado/flow uma vez
por reconstrução e consultas de união dos grupos de um original. Saída Omega(n).
Comparar preparação + TODAS as atualizações/consultas/forwards + limpeza.
EOF END neutral não consome token adicional; todo slot original fecha um MARK.
