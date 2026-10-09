# Contrato escrito: transdutor, slots e expansão

Seja T um transdutor determinístico finito que lê bytes, emite terminais
lexicais e tem finalização EOF parcial. Escreva T_q(w)=(q',z), ou rejeição.
Defina t~u quando T_q(bytes(t))=T_q(bytes(u)) para TODO estado q.
Ausência de emissão de um token especial é rejeição para todos os estados;
não é uma palavra vazia permitida. Tokens com mesmo texto preservam seus IDs.

**Lema (congruência, conhecido).** Substituir qualquer token por outro de sua
classe preserva estado e cadeia lexical de toda sequência, inclusive EOF.
Prova por indução: o estado anterior coincide; a definição exige mesmos estado
posterior e emissão nesse estado, logo ambas cadeias e estados coincidem.
EOF coincide pois é função do estado. Não se assume estado conhecido na lacuna.

**Corolário CFG.** Para qualquer G sobre os terminais de T, validade é constante
em cada produto de classes. As cadeias originais válidas são exatamente todas
as expansões das cadeias de classes aceitas. JSON usa STRING/NUMBER/literais,
seis pontuações, DFA de escapes/UTF8/número e CFG recursiva de objetos/arrays.
Estruturas não se reduzem a catálogos finitos e podem ter diversas conclusões.
Gramática que distingue conteúdo de strings exige T refinado; esta aplicação
não finge cobrir JSON Schema ou semântica geral.

**Lema (slots).** O produto em camadas (posição, estado de T) emite os terminais
lexicais do token e depois um marcador MARK com a escolha (posição, token).
Uma cadeia lê exatamente um MARK por slot. G é levantada inserindo MARK* antes
DE CADA terminal lexical e uma vez no final. Não inserir em limites arbitrários
de não-terminais: isso poderia multiplicar derivações. Retirar MARK recupera G;
atribuir cada corrida de MARK ao próximo terminal (ou fim) é único. Para JSON,
G é não ambígua e o levantamento também. Nosso teste de commitment não requer
amostragem/prova de todo normalizador e não amplia a API pública LL(1).

**Lema (expansão sem recompilação).** Se D'_i contém D_i e suas imagens no
quociente são iguais para cada slot livre, o grafo de classes e sua linguagem
permanecem idênticos. Apenas a lista de IDs disponíveis/representante de saída
muda. Commit original t fixa [t]; um plano monotônico por classes continua
correto. Uma classe nova em qualquer slot exige recompilação, salvo reserva
preparada com a classe inativa e explicitamente bloqueada. Não liberar commits.

**Equivalência de política.** Com no máximo uma proposta original por posição
(NN argmax), a viabilidade de aceitar (i,t) é igual à de aceitar (i,[t]); entre
palavras de uma classe podemos sempre expandir o slot para t. A ordem/confiança
originais permanecem. Por indução a seleção gulosa tem mesmos compromissos.
Fallback escolhe menor ID ORIGINAL viável, não menor número de classe. Tokens
sem proposta são expandidos em ID original admitido; nunca enviar representante
sintético ao forward. Igualdade dos canvases implica próximos logits iguais e
suportes-union iguais, portanto trajetória completa igual em execuções
conclusivas. Múltiplas propostas distintas na mesma posição são recusadas por
esta fachada; generalização requer máximo de utilidades POR TOKEN dentro da
classe, não somar recompensas de tokens incompatíveis.

**Custo/benefício, delimitado.** Com S estados e U palavras únicas tocadas,
classificação custa O(S sum_{w in U}|w|), armazenando assinaturas/IDs. Atualizar
D e ler q custa pelo menos O(sum_i |D_i|); escrever n tokens custa Omega(n).
Grafo de classes tem O(sum_i sum_{c in C_i}sum_{q alcançável}(1+|z(q,c)|))
arestas; sem classes substitui C_i por D_i. Cada recompilação tem custo do
parser escolhido; não escondê-la em tempo de consulta. Se expansão não cria
classes, evita-se exatamente essa compilação mantendo todos os tokens novos;
isso não torna o processamento completo sublinear nem garante wall universal.

Família ilustrativa de PROVA, não benchmark favorável: palavras não vazias
sobre {h,z} têm a mesma assinatura lexical JSON (STR->STR sem emissão; demais
estados rejeitam), portanto 2^ell escolhas de comprimento ell formam uma classe
num slot entre aspas. A topologia não cresce com essas escolhas. Todo custo de
identificá-las/ler probabilidades permanece. FactorDLM com partição adequada ou
outro solver lexical pode obter o mesmo benefício; esta redução não é exclusiva.

Este documento prova uma especialização de princípios conhecidos, não prioridade,
energia, velocidade em todo hardware, acerto semântico ou aceitação do artigo.
