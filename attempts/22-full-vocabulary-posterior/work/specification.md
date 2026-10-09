# Operação matemática: posterior sem topK

Entrada: gramática lexical JSON recursiva não ambígua, transdutor determinístico
UTF8 completo T, vocabulário V de originais com emissões parciais, n slots,
posições fixadas e distribuições racionais normalizadas q_i em V nos slots
livres. Fixados usam delta no original. EOS ausente: controles/sem bytes não
podem pertencer a conclusão, mas sua probabilidade continua no denominador.
Floats softmax congelados são interpretados como dyadics e normalizados pela
soma RACIONAL exata da linha; não declarar mais que isso como exatidão.

Saída: Z=Pr_q(validade), TODOS os marginais sobre V, amostras iid exatas da lei
prod_i q_i(t_i)/Z nas palavras válidas. Z=0 e recusa por recursos são distintos.
A garantia é de um passo, não distribuição global/semântica da dLLM.

**Representação:** no estado q agrupe originais pelo par T_q(t)=(q',emissão).
Um MARK encerra o slot, mantendo q no grafo. Cada palavra original tem exatamente
um caminho e grupo por slot. Qualquer expansão original dentro dos grupos de um
caminho mantém seus estados/emissões, por indução. A CFG levantada põe MARK*
apenas antes de cada terminal e antes de END, logo não multiplica derivações.
Classes globais são refinamento de todos esses grupos. Não presumir contexto
conhecido, sequer para lacunas aparentemente dentro de aspas.

Escreva q_i(t)=I_i(t)/D_i com inteiros; para grupo g de i use
W_i(g)=sum_{t em M_i(g)} I_i(t). Fixados usam I_i(t_fixo)=D_i=1.

**Massa:** inside na floresta acíclica usa soma de alternativas/produto dos
filhos; folha MARK(i,g) tem peso W_i(g), demais terminais1. Pela representação,
a soma de pesos de cada caminho de grupos é a soma do produto I de suas
expansões originais. Caminhos são disjuntos sobre originais, então
Z=inside(root)/prod_i D_i. Isso não renormaliza cauda omitida: V inteiro entra.

**Marginais:** outside deriva inside(root) em relação aos W_i(g). Seja
C_i(g)=d inside(root)/d W_i(g), somando folhas do mesmo grupo/slot. Exatamente
um fechamento por posição em cada derivação garante multilinearidade por
slot. Numerador do marginal original t é
I_i(t) sum_{g:t em M_i(g)} C_i(g), com denominador inside(root).
Para grupos locais, some coeficientes dos estados possíveis. Como classes
globais refinam as locais, essa soma pode ser feita uma vez POR CLASSE global
e expandida em V, evitando n S |V| operações com inteiros grandes. Conservação:
sum_t marginal_i(t)=1; fixados têm marginal1. Z=0 não tem posterior.

**Lei de amostragem:** inside escolhe alternativa proporcional a seu peso
interno; para fechamento g, escolha t em M_i(g) proporcional a I_i(t).
A probabilidade do caminho de grupos é prod_i W_i(g_i)/inside(root).
Multiplicar por prod_i I_i(t_i)/W_i(g_i) cancela todos os W. A unicidade do
caminho/derivação dá exatamente prod_i I_i(t_i)/inside(root). Inteiros e
uniformes randrange usam seleção sem arredondamento. Não amostrar marginais
independentemente. As provas são escritas, não verificação de todo software.

**Benefício comparativo:** grupo local é imagem sobrejetiva das classes globais
válidas no estado, logo não aumenta alternativas token-close com igual efeito;
conteúdo livre em strings pode condensar dezenas de milhares de originais.
A tabela T requer O(S sum_t |bytes(t)|), partição/refinamento O(S |V|).
Parsing opera no grafo de efeitos, não no original V inteiro expandido em bytes.
Ler q e escrever TODOS os marginais requer Omega(n |V|): não prometer saída
sublinear. Contabilizar inteiros com até soma_i bitlength(D_i) e derivados.
Esta redução é especializada de técnicas conhecidas; não exclusiva contra um
parser/factor compiler que faça a mesma eliminação condicionada.

**Rejeição competente:** sobre a MESMA lei racional produto, tentativas até
validade são geométricas: E[N]=1/Z e P(N>R)=(1-Z)^R. É vantagem matemática
quando Z é pequena e compilação/consulta são limitadas; exemplos construídos
são ilustração, não evidência de modelo. Reportar custos e casos em que rejeição
vence; não usar sua incapacidade de dar Z exato como comparação de velocidade
para uma operação que não promete realizar.

**Reutilização completa nas lacunas originais.** Compilação mantém V inteiro
e não poda por peso. Novas q e clamps originais, ou liberação desses novos
clamps, só mudam I e D: delta em t desabilita grupos que não o contêm e dentro
dos restantes escolhe somente t. A prova de massa/lei não muda. Bytes inicialmente
fixados continuam fixados; tokenizer, gramática, n e política EOS são imutáveis.
Não é a API atual topK: esta capacidade pressupõe TODOS os originais retidos
nas lacunas iniciais, e não demonstra novidade geral de planos reutilizáveis.


**Controle global por posição (v2).** Determine os estados lexicais alcançáveis
ANTES do slot pelas escolhas de TODOS os originais nas lacunas prefixas e dos
originais inicialmente fixados, sem usar pesos ou gabarito. Restrinja as
assinaturas globais a esse conjunto de estados; uniões de classes originais
com assinatura igual são uma partição própria por variável, admitida pelo
quociente clássico. Não usa uma testemunha arbitrária. Agregue pesos somando
as classes refinadas e expanda marginais pela classe daquele slot. Todas as
provas acima continuam válidas. A preparação correspondente entra na medição.
