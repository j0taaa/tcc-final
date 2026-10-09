# Eliminação lexical exata e seu custo

Complemento matemático da tentativa22. Os resultados experimentais permanecem
separados; nenhum teorema abaixo é apresentado como princípio novo de inferência.

## Objetos e operação

Há n posições físicas e f posições atualmente livres. Cada original t tem
emissão de bytes, inclusive emissões UTF8 parciais; controles sem emissão não
são palavras admitidas. T é um transdutor determinístico, com S estados, que
retorna efeito (estado seguinte, palavra de terminais lexicais), ou recusa.
Uma gramática não ambígua reconhece os terminais; finalização é determinística.
Na implementação, T e a gramática são os de JSON recursivo, não JSON Schema.

Para cada posição livre, q_i(t)=I_i(t)/D_i, com D_i=sum_t I_i(t).
Fixados têm delta no original e D_i=1. Probabilidades F64 são interpretadas
como racionais binários e normalizadas exatamente. Isto não torna exata a
softmax de números reais nem a distribuição de toda a trajetória neural.
Z é a massa de conclusões válidas para esse produto congelado. Quando Z=0,
não existe posterior; recusa por recursos deixa a inferência inconclusiva.

## Preservação de eventos originais

No estado s, um grupo g reúne exatamente os originais com o mesmo efeito de T.
O grafo coloca um fechamento de posição após a emissão inteira desse efeito.
Grupos de estados diferentes podem sobrepor-se como conjuntos de originais.

**Lema das fibras.** Um caminho de grupos c corresponde ao produto dos conjuntos
de membros dos seus grupos, respeitando o suporte estrutural inicial. Esses
produtos particionam os eventos de tokens originais admitidos.

Prova: qualquer membro de um grupo produz o mesmo próximo estado e os mesmos
terminais. Indução nas posições mantém o caminho ao substituir seus membros.
Reciprocamente, determinismo de T atribui um único caminho a cada sequência
original. A gramática não ambígua atribui uma única derivação ao caminho válido.
Os fechamentos não consomem bytes: a gramática os coloca exclusivamente antes
do próximo terminal, inclusive o terminal final, sem duplicar sua alocação.

**Teorema do posterior.** Use W_i(g)=sum_{t em g} I_i(t). A avaliação interna
calcula M=sum_{c valido} prod_i W_i(g_i) e Z=M/prod_i D_i. Se M>0,
os marginais originais têm numeradores

    N_i(t)=I_i(t) sum_{g:t em g} dM/dW_i(g),

e denominador comum M. Amostrar um caminho com massa proporcional a seu produto
de W e depois seus membros com probabilidades I/W retorna exatamente
prod_i I_i(t_i)/M. Aliases são eventos distintos mesmo quando seus bytes coincidem.

Prova: distributividade e o lema das fibras dão a igualdade de massas.
Cada caminho fecha cada posição uma única vez; logo o polinômio é multilinear
por posição, e diferenciação atribui a contribuição de cada original.
A conservação sum_t N_i(t)=M segue da mesma multilinearidade. Na amostragem,
os fatores W cancelam; nenhuma marginal é amostrada independentemente.

## Redução estrutural comparativa

Sejam R_i os estados lexicais alcançáveis antes da posição i, considerando
todo o suporte estrutural inicial, sem consultar probabilidades ou gabarito.
Considere quatro representações de escolhas: originais, classes por todos os
estados, classes por R_i e grupos por um estado específico. As três primeiras
refinam os grupos locais. Todas conservam o mesmo R_i, por indução nos slots.

**Teorema da representação.** Para a construção com caminhos internos privados,
o número de arestas da representação k é

    E_k=E_final+sum_i sum_{s em R_i} sum_{c valido} (1+|emissao_s(c)|).

Portanto E_local <= E_posicao <= E_global <= E_originais. A mesma ordem vale
para os vértices internos privados. A desigualdade é estrita quando ao menos
dois códigos refinados válidos no mesmo estado têm o mesmo efeito e são unidos.

Prova: uma fibra local possui efeito e comprimento constantes. O refinamento
repete o seu caminho uma vez por código; a representação local usa um único
caminho. Arestas finais e fronteiras de posição são comuns. Não se deduz daqui
otimalidade sobre todos os parsers, fatorizações ou velocidade física universal.
Uma implementação clássica que realize a mesma eliminação compartilha a redução.

## Custo e precisão

A tabela requer O(S sum_t |bytes(t)|) processamento lexical. A construção de
assinaturas/refinamento por hashing custa O(S|V|) em expectativa; não é um limite
de pior caso para dicionários Python. Classes globais refinadas permitem somar
coeficientes uma vez por classe/estado e expandir em originais. Se há C classes,
essa etapa usa O(fSC+f|V|) operações, além das verificações de posições fixas.
A referência atual verifica conservação dos fixados percorrendo coeficientes
por posição fixa: acrescente O((n-f)L), para L chaves de fechamento. Não omitir
esse custo ou tratá-lo como vantagem científica necessária.

Para a gramática CNF preparada, v vértices, e arestas, h não terminais e r regras
binárias, o limite clássico é O(rv^3+eh) alternativas e O(hv^2) células.
Dentro/fora percorrem as alternativas retidas; normalização, tabela, construção,
ordenação/agendas, reconstrução e saída têm custos próprios. Inteiros têm limite
conservador B=b+O(v log(e+r+h+1)), onde b soma os comprimentos dos denominadores.
Adições custam O(B), e multiplicações custam o custo de multiplicar B bits.

Para a interface que representa fixados como deltas esparsos, a leitura das
linhas livres e escrita dos marginais originais densos exigem Omega(f|V|+n).
Omega(n|V|) aplica-se se todas as posições forem livres ou se for exigida saída
densa também para fixados. Esta é uma correção do limite demasiado geral na
versão anterior da especificação; não muda os kernels medidos.

## Corolário de uso na dLLM

Além de propostas conjuntas válidas e confiança por token, os marginais dão
um gradiente analítico da massa de validade. Nas posições livres, para q_i=softmax(z_i), Z>0 e
suporte/predição congelados neste passo,

    d log Z / d z_i(t)=P(y_i=t | valido)-q_i(t).

Prova: derive cada produto q(y); a derivada de log q_i é o indicador do token
menos q_i(t). Somar sobre os eventos válidos e dividir por Z dá a identidade.
Assim -log Z pode funcionar como regularizador de validade de um passo,
sem estimador Monte Carlo para essa derivada. Não houve treinamento realizado
nem demonstração de acerto semântico. É um uso conhecido da inferência exata,
não uma nova identidade estatística ou garantia global de geração. A derivação
se refere à família matemática softmax; não diferencia a operação discreta de
arredondamento/serialização de F64 usada nas capturas.

## Antecedentes que delimitam a contribuição

Rivaud e Pachet (2017) já tratam amostragem gramatical não ambígua.
FactorDLM, proposição2, já demonstra inferência por quocientes globais.
Boutilier et al. (UAI1996, arXiv:1302.3562) e Chavira e Darwiche (2008)
tratam independência contextual e estrutura local na inferência exata.
Opedal et al. (ACL2023) fornece o antecedente do parsing ponderado empregado.
O OpenFst já oferece soma de arcos com mesmos rótulos e destino; a eliminação
local também é uma especialização dessa operação, com rastreamento dos eventos
originais e seu outside. Cognetta e Okazaki (2025) já formalizam tokenização
como transdução; respeitar fronteiras BPE não cria novidade isoladamente.

O candidato próprio é o compilador/auditoria de tokens originais em fronteiras
arbitrárias para JSON recursivo, com benefício delimitado; prioridade científica
e suficiência para publicação não são provadas por estes resultados.

Fontes primárias adicionais: [OpenFst StateMap](https://www.openfst.org/twiki/bin/view/FST/StateMapDoc),
[Cognetta e Okazaki](https://aclanthology.org/2025.cl-4.2/),
[FactorDLM](https://arxiv.org/html/2609.32900v1),
[CSI](https://arxiv.org/abs/1302.3562),
[Opedal et al.](https://aclanthology.org/2023.acl-long.204/),
[Rivaud e Pachet](https://arxiv.org/abs/1711.10436).

## Coacessibilidade lexical (v5)

Compute R_i por alcance a partir de OUT e B_i de trás para frente: B_n contém
os estados com finish definido; s está em B_i se uma escolha admitida chega a
B_(i+1). Restringir R_i a B_i e descartar transições fora desses conjuntos
preserva TODOS os caminhos lexicais completos, portanto todos os JSON válidos.
Nada usa pesos ou gabarito. Atualizações de pesos/clamps/remasking nas lacunas
originais não criam caminhos ausentes dessa estrutura completa.
O custo é O(n soma_s |grupos_s|), memória O(nS), com escolhas fixas O(1) por estado.
A partição por posição usa efeitos efetivos: qualquer transição para estado
sem sufixo é recusa. As desigualdades de arestas e a lei original permanecem
quando TODAS as representações recebem esse mesmo trimming clássico.
É uma melhoria comum de implementação e um controle obrigatório, não novidade.

## Common grammar-terminal coarsening and independent stack control

For the JSON grammar, NUMBER, TRUE, FALSE and NULL appear only as the same
right-hand side of V. Replacing these four terminal labels by ATOM preserves
recognition provided the deterministic scanner validates the literal and
preserves its original token fiber. STRING is distinct because object keys
require STRING. This is a classical grammar homomorphism, applied equally to
all nine exact representations, not a new theorem or loss of original values.

The predictive-stack control runs the deterministic LL(1) grammar without CNF
forest compilation. Its state is (lexical state, residual predictive stack).
At each slot it applies each admitted lexical word; equivalent target states
share an arc whose weight is the sum of disjoint original lexical fibers.
Backward path sums, forward/backward derivatives and conditional path sampling
compute the same original-token law. The initial stack is V; the final number
flush is accepted iff the residual stack is empty. Literal terminals and V
require at least one future emitted terminal each; any literal closing bracket
or brace in the residual stack requires a future closing delimiter. Bounding
these by the sum of maximum emissions per remaining slot (plus one possible
final number flush) gives safe necessary pruning, without a depth assumption.

Its cost is proportional to processed lexical words and residual stack lengths,
plus exact forward/backward arithmetic, original lifting and output. Explicit
stacks can grow exponentially, but their compactness on specific frames can
make this control cheaper than CFG parsing. The edge inequality among lexical
partition DAGs does NOT imply superiority over this independent algorithm.
Any final adoption claim must also survive its fully charged implementation.
