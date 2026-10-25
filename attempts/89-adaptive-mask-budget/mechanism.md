# Mecanismo e fronteira da contribuição

O parser determinístico deste subconjunto mantém (profundidade, estado lexical).
Como cada ID admitido abre no máximo b colchetes e a resposta tem no máximo B
IDs, profundidade <=bB é um limite exato, não aproximação da recursão admissível
neste orçamento. Não é uma construção eficiente para qualquer CFG. A tabela
de transições distingue efeitos inteiros dos tokens, não conta caracteres como
tokens. Aliases compartilham efeito, mas preservam seus IDs/escores originais.

Uma MASK consome exatamente uma transição da união A de todos os IDs admitidos;
um ID fixo consome sua transição própria. Prefixos alcançáveis F e sufixos
coacessíveis R dão o teste de compromisso em uma posição i:
existe q em F[i] com delta(q,ID) em R[i+1]. Após aceitação, atualizar só os
prefixos/sufixos afetados. Esse é um controle incremental clássico, não novidade.

Para expansão, usar o grafo (posição atual, estado do parser). Consumir uma
posição atual custa zero; inserir uma transição de A sem consumir posição custa
um. Caminho de menor custo até (fim,EOS) devolve mínimo de inserções conjuntas.
Distâncias de sufixo permitem reconstruir uma alocação: preferir consumir posição
quando ótimo, depois menor estado de destino; senão inserir pelo menor destino
que reduz a distância. Essa regra é idêntica nos dois backends. Não inserir os
tokens testemunha: inserir MASKs e comprometer apenas a proposta do modelo.
Existência da testemunha garante viabilidade da nova configuração.

Na CPU, fechamento de distâncias por Dijkstra multi-origem nas arestas reversas.
Na GPU, mesmo fechamento min-plus com matriz de distâncias preparada e operações
Torch inteiras, sem aproximação. Contratos e decisões são os mesmos; os
algoritmos físicos podem diferir. Preparação não é gratuita. Distâncias mínimas
não substituem o teste exato de posições: as posições obrigatórias são consumidas
explicitamente no grafo, inclusive MASKs entre compromissos e EOS.

Invariável: um estado viável só aceita compromisso que preserve uma conclusão
no canvas resultante. Logo não aparece falta de espaço espontânea. O algoritmo
adaptativo deliberadamente admite uma proposta que o fixo recusaria. Nenhuma
alegação de confiança crescente, acerto semântico ou preservação da distribuição
neural é feita. Inserção muda o contexto e invalida todos os logits do próximo
forward; a quota remanescente no forward atual usa logits anteriores à inserção
com índices remapeados, exatamente como no controle definido, até novo forward.

O grafo com custos, programação dinâmica min-plus e propagação bidirecional são
clássicos. A diferença investigável seria uma representação/algoritmo para CFGs
gerais com múltiplas lacunas e comprimentos em tokens que superasse esses controles
em execução completa. Este protótipo especializado não estabelece essa diferença.
