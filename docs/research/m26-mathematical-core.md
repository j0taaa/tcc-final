# M26 — Contribuição matemática: compromisso ótimo sob orçamento

## O que mudou e o que esta contribuição garante

O resultado principal passa a ser um algoritmo e suas provas. Os experimentos
M24/M25 são evidência secundária histórica, incluindo todos os resultados ruins;
não fundamentam a relevância deste resultado. O novo algoritmo escolhe
conjuntamente a conclusão válida **e as posições a comprometer**, respeitando um
orçamento B. As antigas políticas primeiro limitavam o conjunto de propostas.

O teorema garante o maior peso de propostas comprometidas entre **todos** os
lotes permitidos na mesma etapa, com os mesmos dados. Um checker independente
verifica uma prova de optimalidade, não apenas se a saída é gramatical. A prova
vale para toda entrada finita que satisfaz as hipóteses, sem taxa de sucesso em
benchmark. O protótipo usa aritmética racional exata. Isso não é um teorema de
acurácia semântica, menor tempo de execução ou otimalidade da trajetória futura.

## Antecedentes e fronteira da contribuição

Parsing ponderado, programação dinâmica com recursos e algoritmos certificadores
são ferramentas estabelecidas. Não reivindicamos inventá-las. O incremento é a
formulação e solução do orçamento físico de compromisso no problema MWPC, sua
compilação com bytes/EOS/PAD, a prova verificável da fronteira de todos os
orçamentos e a separação assintótica de seleção por confiança/pré-seleção.

Fontes primárias verificadas em 30/09/2026:

| Trabalho | Antecedente reconhecido | Fronteira deste resultado |
|---|---|---|
| [Weighted CFG, Katsirelos et al. (2008)](https://doi.org/10.1007/978-3-540-68155-7_31) e [versão de 2011](https://doi.org/10.1007/s10479-010-0697-y) | Otimização por parsing ponderado | Sem alegação de novo princípio de parsing |
| [Semiring parsing, Goodman (1999)](https://aclanthology.org/J99-4004/) | Álgebra de inferência | A dimensão de recurso é uma aplicação desse princípio |
| [EPIC (2026)](https://arxiv.org/html/2606.00722v1) | Divisão ordenada por confiança, cobertura regular e verificação | Comparação formal do objetivo por etapa; não do desempenho de geração |
| [FactorDLM (2026)](https://arxiv.org/html/2609.32900v1) | Inferência exata em suporte finito por fatores | Não reivindicamos primeira inferência exata em dLLMs; objetivo de lote é distinto de MAP |
| [AXON (2026)](https://arxiv.org/html/2606.04236v1) | Seleção de revelações de apoio sob capacidade | Não reproduzimos sua função de atenção/submodularidade; otimizamos concordância compatível com CFG |
| [Demirović et al., CP 2024](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.CP.2024.9) | Certificação de programação dinâmica | Nosso checker de potenciais é específico da construção CFG/DAG/orçamento; não alegamos inventar proof logging |

A pesquisa não prova prioridade mundial. A validade dos teoremas e a diferença
em relação ao problema anterior são independentes dessa busca bibliográfica.
Uma contribuição matemática incremental de TCC não deve ser anunciada como
invenção de todos os seus ingredientes.

## Definições

Fixe a etapa, canvas x, conjunto finito de tokens por posição, política EOS/PAD,
emissão composicional em bytes e CFG G. Seja F o conjunto finito de conclusões
que preservam as posições fixas, consomem exatamente os slots físicos e cujos
bytes pertencem a L(G). I é o conjunto de posições ainda livres. Cada proposta
j tem identidade distinta, posição i_j, token t_j e peso racional w_j >= 0.
Propostas distintas para o mesmo par posição/token **não são descartadas**.

Defina a recompensa agregada na posição i:

    r_i(a) = sum_{j: i_j=i, t_j=a, w_j>0} w_j.

O novo problema é:

    OPT_B = max_{y in F, T subset I, |T|<=B} sum_{i in T} r_i(y_i).

Um lote compromete uma posição uma vez, mesmo que ela satisfaça vários IDs.
Posições previamente fixas não gastam orçamento nem somam recompensa nova.
Um token de testemunha sem proposta positiva pode servir como progresso, mas
não ganha recompensa. `matched_proposal_ids` da testemunha e
`committed_proposal_ids` do lote são campos diferentes. O contrato do resultado
MWPC original permanece intacto.

Se F é vazio, o estado é INFEASIBLE_ON_SUPPORT. B=0 é uma otimização válida com
valor zero quando F é não vazio, mas não dá progresso em um canvas incompleto.

## Teorema 1 — Equivalência com a melhor conclusão orçada

Para cada y, seja top_B(r(y)) a soma dos B maiores valores não negativos das
posições livres (ou todos, se houver menos). Então:

    OPT_B = max_{y in F} top_B(r(y)).

**Prova.** Fixado y, maximizar sobre T com |T|<=B escolhe seus B maiores valores.
Toda seleção de posições é compatível, pois y é uma testemunha comum. Inversamente,
todo lote compatível admite uma testemunha y; seu peso é no máximo top_B(r(y)).
Tomando o máximo em ambas as direções obtemos a igualdade. Cada ID positivo
coincidente na posição selecionada contribui à soma r_i, provando também o
tratamento de duplicatas. Não há leitura de gabarito. QED.

## Compilação para um DAG de recursos

Use o lattice finito de tokens composto com EOS/PAD. Cada macro-arco consome
um slot e é expandido em um caminho privado de bytes, ou em epsilon para um
controle EOS/PAD. No **primeiro** arco de uma escolha de token livre com
recompensa positiva, ofereça duas alternativas paralelas:

    não comprometer: (custo=0, recompensa=0)
    comprometer:     (custo=1, recompensa=r_i(a)).

Os outros arcos têm custo/recompensa zero. Tokens fixos também têm custo zero.
O pagamento no primeiro arco preserva token_id, posição e todos os IDs positivos;
não se paga uma vez por byte ou por derivação. O caminho original é preservado.

**Lema de compilação.** Há correspondência entre caminhos aceitos com custo <=B
e pares (y,T) permitidos; a recompensa do caminho é a recompensa do par.

**Prova.** Um caminho completo escolhe exatamente um macro-arco em cada slot.
Os caminhos internos privados impedem trocar a metade de um token pela de outro.
As transições EOS/PAD restringem a ordem dos controles antes da emissão. Tomar
uma alternativa paga identifica uma posição livre única em T. Portanto, o custo
é |T| e o peso é a soma r_i(y_i). A operação inversa usa as alternativas pagas
exatamente nas posições de T. Posições sem recompensa podem ser removidas de T
sem alterar o valor, permitindo omitir seus arcos pagos. QED.

## Teorema 2 — Programação dinâmica exata para todos os orçamentos

Considere qualquer DAG de recursos acíclico explícito. Arcos e têm emissão a_e
(terminal ou epsilon), custo inteiro c_e>=0 e recompensa racional w_e>=0. G está
em CNF estrita, com uma flag separada para a palavra vazia. Para k=0..B:

    E[u,v,k] = melhor recompensa de caminho somente epsilon, de u a v, custo k.
    D[A,u,v,k] = melhor recompensa de caminho com emissão não vazia derivável
                de A, de u a v, custo k.

Valores impossíveis são menos infinito, jamais zero. E[u,u,0]=0. Calcule E em
ordem topológica por transições epsilon. Para cada arco terminal e=(a,b,t),
produção A->t e k1+c_e+k2=k, inicialize:

    D[A,u,v,k] >= E[u,a,k1]+w_e+E[b,v,k2].

Para A->BC e nó intermediário z, componha:

    D[A,u,v,k] = max(base,
                    max_{z,k1+k2=k} D[B,u,z,k1]+D[C,z,v,k2]).

Calcule por distância topológica crescente. A resposta para o limite b<=B é o
máximo D[S,start,f,k] para finais f e k<=b. Se G aceita epsilon, compare também
E[start,f,k]. Retenha backpointers originais nos dois casos.

**Prova.** Primeiro, indução no nó final em ordem topológica prova E: qualquer
caminho epsilon não vazio tem um último arco, coberto pela transição, e cada
transição acrescenta um arco real. Para D, use indução na distância topológica.
Uma derivação terminal corresponde a um arco terminal cercado por caminhos
epsilon. Os máximos E com mesmos extremos e custo podem substituí-los sem
diminuir o peso; a aciclicidade impede sobreposição de segmentos. Uma derivação
binária divide o caminho em z e o custo em k1+k2. Os dois filhos têm distância
estritamente menor; por indução, seus valores são exatos. Toda concatenação
considerada é um caminho real e toda derivação é coberta. Para emissão vazia,
o caso E separado cobre todas as possibilidades, inclusive o caminho vazio.
Maximizar sobre k<=b resolve a restrição de orçamento. Aplicar o lema de
compilação e o Teorema 1 resolve OPT_b simultaneamente para todos os limites.
Ambiguidade gramatical toma máximo, sem multiplicar recompensa. QED.

Com q nós, m_e arcos epsilon, m_t arcos terminais e produções P_1/P_2, os limites
são O(q^2(B+1) + q m_e(B+1) + (|P_1|+1) m_t q^2(B+1)^2 + (|P_2|+1) q^3(B+1)^2) operações aritméticas/de chart e
O((|N|+1)q^2(B+1)) entradas, além da entrada e backpointers. São contagens de
operações com racionais/chart, não de tempo de GPU nem de bits unitários.
O limite é pseudopolinomial para B genérico codificado em binário; no orçamento
físico basta considerar B<=|I|. Os termos +1 incluem percursos sem produções
aplicáveis, e q^2(B+1) inclui a varredura do chart epsilon. Não afirmamos
que o novo protótipo seja mais rápido que EPIC.

## Teorema 3 — Certificado independente de optimalidade

Forneça potenciais superiores U_E/U_D para as mesmas células, com menos infinito
nas ausentes, satisfazendo:

1. U_E[u,u,0]>=0 e toda desigualdade de transição epsilon;
2. toda desigualdade de inicialização terminal, usando U_E;
3. toda desigualdade de composição binária, usando U_D.

Seja U_b o máximo superior dos estados finais de custo <=b, incluindo o caso
epsilon quando aceito. Um checker sem otimização valida essas desigualdades,
reconstrói o caminho original, confere sua emissão com um recognizer independente
e soma racionalmente sua recompensa L e seu custo.

**Prova de soundness.** Por indução no caminho epsilon, U_E limita superiormente
cada caminho desse tipo. Por indução na árvore de derivação, a desigualdade
terminal limita a folha e a desigualdade binária limita a concatenação dos
filhos. Logo, para todo caminho factível p, reward(p)<=U_b. Se um caminho
factível fornecido tem L=U_b, então L<=OPT_b<=U_b=L e ele é ótimo. Se não existe
estado final de bound finito, nenhum caminho aceito pode existir. Uma testemunha
factível sozinha estabelece apenas L<=OPT_b, não optimalidade. QED.

**Prova de completeness.** As células exatas do Teorema 2 satisfazem todas as
desigualdades. O caminho reconstruído atinge seu máximo, ou todas as células
finais são impossíveis. Portanto, todo resultado terminado tem certificado
aceitável. QED.

Floats finitos são convertidos em seus racionais binários exatos; somas e
comparações não usam tolerância. A garantia numérica é sobre os pesos fornecidos,
não sobre probabilidades ideais desconhecidas. Não há Lean/Coq instalado nem
prova mecanizada do teorema universal: são provas matemáticas escritas completas,
um checker executável e oráculos que validam a implementação em casos finitos.
**Testes não substituem as provas.**

## Teorema 4 — Dominação universal de lotes comparáveis

Para qualquer algoritmo H que devolva um lote de propostas representadas em
posições livres, com no máximo B posições e uma testemunha em F:

    weight(H(x,C,B)) <= OPT_B.

**Prova.** A testemunha e as posições de H constituem um par permitido na
definição de OPT_B. Se H omite um ID positivo coincidente de uma posição escolhida,
somar todos esses IDs só aumenta seu peso, pela não negatividade. O máximo
contém esse par. QED.

Aplica-se a um lote EPIC que satisfaça as mesmas hipóteses. A execução nativa pode
usar outro suporte, tokens reamostrados, gaps abstratos e outra política de
slots; o teorema não identifica automaticamente essas execuções com a entrada
comum, nem domina acurácia ou latência de ponta a ponta.

## Teorema 5 — Perda assintótica de pré-seleção e prioridade por confiança

Fixe **uma única linguagem regular**, independente de B:

    L = 0* h 0*  union  0* l+ 0*.

Para qualquer B>=2, há 2B slots. Nos primeiros B, permita {0,h} e proponha h com
peso 7/8. Nos últimos B, permita {0,l} e proponha l com peso 3/4. Todos os pesos
são constantes, válidos como confidências marginais. Cada proposta isolada tem
conclusão e a tokenização tem um terminal por token.

O lote dos B l tem peso 3B/4 e é compatível. Qualquer conclusão com h pode conter
somente um h e nenhum l; seu peso positivo máximo é 7/8. Toda conclusão sem h
tem no máximo B propostas l. Portanto OPT_B=3B/4.

Pré-selecionar os B maiores pesos retém somente h. Mesmo um solver perfeito
nesse conjunto reduzido obtém 7/8: a perda ocorreu antes da otimização.

A seleção por confiança que aceita o primeiro candidato extensível fixa um h
e impossibilita todas as demais propostas. O seletor upstream EPIC ordenado por
confiança, com verificador exato completo e cobertura regular sem falsos
negativos, também retém esse primeiro h: se uma lista passa a cobertura, mantém
o primeiro elemento; caso contrário, a recursão primeiro processa a metade
esquerda que o contém. A verificação/shrink exata usa a mesma prioridade. Ao
chegar ao singleton, ele é extensível e é mantido. As demais propostas não
podem passar a verificação exata na presença dele. Isso vale para a cobertura
exata e para uma cobertura universal; não depende de qualidade de parser.

Assim, nesses procedimentos:

    ALG_B / OPT_B = (7/8)/(3B/4) = 7/(6B) -> 0.

Logo não existe constante alpha>0 que garanta ALG_B>=alpha OPT_B para todas
essas entradas. Para qualquer alpha, basta B>7/(6 alpha). Isto é uma família
de contraexemplos para um teorema de aproximação, **não um benchmark de acurácia**.
A regra gramatical e os pesos são os mesmos para todo B. A prova não diz que
esses casos são frequentes nem que o EPIC produz respostas piores para usuários.

## Teorema 6 — Otimizar tudo e filtrar depois também pode perder arbitrariamente

Mantenha a mesma linguagem L e fixe B=1. Para n=2^k, k>=1, use n+1 slots:
o primeiro permite {0,h}, com proposta h de peso 7/8; os demais permitem {0,l},
cada proposta l tem peso 7/(4n). O MWPC sem orçamento prefere a conclusão
com n l, de peso 7/4, à conclusão com h, de peso 7/8. Filtrar sua testemunha
para uma única posição retém no máximo 7/(4n). Entretanto, OPT_1=7/8.

**Prova.** As duas formas de L excluem a coexistência de h e l. Qualquer
conclusão com h tem somente seu peso, e a conclusão com todos os l atinge 7/4.
Assim, toda testemunha ótima sem orçamento contém exclusivamente propostas l.
Com uma posição permitida, um lote ótimo é h, pois 7/(4n)<=7/8 (há empate quando n=2). A razão do
pós-filtro para OPT_1 é 2/n, que tende a zero quando k aumenta. Os pesos são
racionais binários exatos e a linguagem e orçamento permanecem fixos. QED.

Este resultado mostra que selecionar uma testemunha ótima para o objetivo
anterior e depois limitar seus commits não resolve o novo objetivo. Portanto,
o incremento não é apenas rebatizar a otimalidade já implementada.

## Corolários positivos de uso

**Fronteira de orçamento.** OPT_0<=OPT_1<=...<=OPT_B, pois os conjuntos factíveis
se incluem. Se F é não vazio, OPT_0=0; para B>=|I| recupera-se o objetivo completo
das posições livres. Para uma recompensa-alvo Q, o menor b com OPT_b>=Q é o
menor orçamento que pode atingi-la nesse estado. É uma decisão de capacidade
provada, sem escolher limiar por benchmark.

**Progresso com número ótimo de rodadas.** Suponha B>=1, suporte que preserva a
testemunha após cada atualização, e nenhuma remascaragem. Complete o lote pago
até min(B, slots livres) com tokens da mesma testemunha. Se houver capacidade
sobrando, nenhum desses tokens pode satisfazer uma proposta positiva não paga;
caso contrário, acrescentá-lo melhoraria OPT_B, contradizendo optimalidade.
O complemento não altera a recompensa e é registrado como fallback. A testemunha
continua válida. Após ceil(|I|/B) rodadas, o canvas está completo. Qualquer
programação que fixe no máximo B slots novos por rodada precisa de pelo menos
esse número, pela contagem de slots. Trata-se de optimalidade de rodadas sob
essas hipóteses, **não um limite inferior de chamadas de modelo para qualquer
algoritmo**, nem uma promessa de qualidade de linguagem.

## Correspondência com o código

| Obrigação | Implementação |
|---|---|
| Contratos e aritmética racional | `reference/budget_types.py` |
| Epsilon/DAG/recursos e backtracking | `reference/budgeted_parser.py` |
| Desigualdades e optimalidade independente | `reference/budget_certificate.py` |
| Slots, bytes, EOS/PAD e distinção dos IDs | `budgeted_commit.py` com os builders finitos existentes |
| Oráculos e regressões | `tests/exact_commit/test_budgeted_math.py` |

Os métodos anteriores `serial | epic | exact` não são substituídos, e os
experimentos anteriores não são resultados da nova dimensão de orçamento.
