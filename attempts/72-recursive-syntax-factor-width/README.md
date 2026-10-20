# A72 — Limite robusto para representações de sintaxe recursiva

Investigação de 2026-10-20 (UTC). Há uma prova escrita e oráculos finitos.
A auditoria adicional abaixo sustenta o argumento original e acrescenta
um teorema de erro tendendo a um e um corolário para circuitos estruturados.
A prioridade específica e a suficiência científica continuam abertas.
Nenhuma campanha neural, ganho de latência ou aprovação acadêmica é alegada.

## Operação e contrato da tentativa

1. **Operação real:** condicionar um produto de pesos posicionais à GLC
   LL(1) fixa `S -> P # P; P -> ( P ) | [ P ] | ε`. São cinco tokens
   originais de um byte, N slots e EOS/PAD ausentes. O limite inferior
   usa pesos uniformes, sem treinamento nem logits adversariais.
2. **Antecedente mais próximo:** Kadioglu/Sellmann (2010) e Wang/Yap
   (2023) já separam sintaxe e árvores de restrições no caso EXATO.
   A candidata é a resistência QUANTITATIVA à aproximação da lei, com
   ocultos arbitrários e qualquer grafo escolhido depois de conhecer o alvo.
3. **Benefício verificável:** determinar se uma aproximação pequena permite
   trocar recursão por um grafo de baixa capacidade. Um limite para todas
   as codificações admitidas evita culpar apenas uma codificação ruim.
4. **Hipóteses e prova:** um observado categórico por posição original,
   fatores não negativos, domínios finitos e grafo primal. Cardinalidades
   dos ocultos contam. [A prova](proof.md) explicita os contratos e os lemas.
5. **Comparador competente:** qualquer grafo e quantidade de auxiliares;
   permitir estados contraídos e permutação interna de posições. O controle
   positivo enumera marcadores e resolve matchings de largura 1. CFDs e
   circuitos contextuais são alternativas eficientes reconhecidas.
6. **Custo completo:** capacidade é soma de log2 dos domínios por bolsa;
   número de nós sozinho não basta. Contar bits dos pesos e massas, RNG,
   preparação e saída. O controle paga O(N²) operações aritméticas para
   pesos gerais; nenhum forward neural entra como gratuito.
7. **Objeções:** a linguagem-base e os argumentos de separadores e afinidade
   são clássicos. A extensão pode ser pequena para o objetivo do usuário.
   O limite não proíbe algoritmos simbólicos, circuitos ou enumeração de
   contextos, nem mede o comportamento dos logits de um dLLM real.
8. **O que falta:** julgar a prioridade e a relevância da extensão frente à
   literatura de aproximação de modelos probabilísticos. Não iniciar uma
   campanha neural apenas porque os oráculos passaram.

## Resultado escrito

Para N=2l+1, seja P a distribuição uniforme da gramática acima. Qualquer
lei Q na interface de fatores, com erro total de variação e<1/5, exige

    W >= l/6 + log2(5(1/5-e)^2),

onde W é a maior capacidade de bolsa em qualquer decomposição em árvore,
incluindo ocultos. Para erro de 10%, alguma bolsa tem pelo menos

    2^((N-1)/12) / 20 estados conjuntos.

O grafo pode ser escolhido especificamente para esse único alvo. Não se
exige uma topologia preparada para servir a vários pesos. A prova usa
apenas pesos uniformes. Ao mesmo tempo, um sampler clássico representa a
mesma lei com trabalho linear, escolhendo o marcador e os bits dos pares.

**O que a utilidade significa:** uma garantia uniforme de aproximação não
justifica tratar toda sintaxe recursiva como tabelas pequenas num único
plano genérico de fatores. A estrutura de cada caso pode ser necessária.
Isso é uma obstrução de representação; não prova que um novo decoder é
mais rápido, gera respostas melhores ou vence métodos sensíveis ao contexto.

A direção inversa baseada em cópias, considerada num rascunho inicial,
foi retirada: uma permutação interna põe os pares juntos e torna a GLC
pequena. Não se alega uma incomparabilidade geral com esse argumento.

## Auditoria de antecedentes

| Fonte primária e trecho lido | Consequência para a candidata |
| --- | --- |
| [Kadioglu/Sellmann (2010)](https://www.researchgate.net/publication/225789014_Grammar_Constraints), Teorema 6; [Wang/Yap, AAAI 2023](https://ojs.aaai.org/index.php/AAAI/article/download/25526/25298), definições e Proposições 4, 7, 8 | A família de dois palíndromos e a separação exata com ocultos são antecedentes diretos. Não são contribuição própria. A Proposição 8 também impede usar cópia reordenável como separação inversa. |
| [McAllester/Collins/Pereira, UAI 2004](https://arxiv.org/pdf/1207.4135), CFDs e parsing | Circuitos sensíveis ao contexto já evitam limitações de grafos. O controle por marcador é clássico. |
| [Braun/Pokutta, revisão de 2016](https://eccc.weizmann.ac.il/report/2013/056/revision/4/download/), introdução e enquadramento de informação comum | Interpretar fatoração não negativa como mistura produto e usar informação/afinidade para limites inferiores é conhecido. |
| [Kučera, CP 2023](https://drops.dagstuhl.de/storage/00lipics/lipics-vol280-cp2023/LIPIcs.CP.2023.22/LIPIcs.CP.2023.22.pdf), introdução, equivalência BCT/SDNNF e compilação por largura | Liga árvores de restrições a decomposição estruturada. A equivalência declarada é de representação exata de relações; não estabelece automaticamente o novo contrato de TV. |
| [Leland/Choi, NeurIPS 2025](https://arxiv.org/html/2506.01281), Seções 3–4 | Já prova dificuldades de aproximação em TV e uma separação entre PCs decomponíveis e também determinísticos. Não reivindicar a ideia geral de que aproximação pode manter separações exponenciais. A candidata cobra capacidade de grafos para uma GLC fixa e um alvo já tratável. |
| [Amarilli et al., STACS 2026](https://drops.dagstuhl.de/storage/00lipics/lipics-vol364-stacs2026/html/LIPIcs.STACS.2026.5/LIPIcs.STACS.2026.5.html), Proposições 3.1, 5.3 e conclusão | Condicionamento por GLC não ambígua e circuitos tratáveis já são antecedentes. O artigo pergunta pela classificação de linguagens em representações estruturadas; isso não torna toda resposta parcial nova. |
| [Zhao et al. (2026)](https://arxiv.org/html/2605.12940), Seção 5 e Apêndice A.4 | A rigidez de uma decomposição fixa já é estudada em modelos de linguagem. A separação ali enunciada é exata, com uma hipótese de incompatibilidade entre estruturas; conferir aproximações/corolários continua necessário. |
| [FactorDLM (2026)](https://arxiv.org/html/2609.32900), Seções 2–3 | Compila fatores reutilizados por passo e cobra largura ponderada, reconhecendo circuitos como extensão. Não promete que toda recursão é barata; A72 não refuta uma promessa que o artigo não faz. |

Não foi encontrado um enunciado equivalente ao limite quantitativo nas
fontes conferidas. Isso é uma conclusão limitada desta busca, não prova
de prioridade mundial, de publicação futura ou de impacto. Uma prova
correta de um refinamento também pode ser insuficiente como contribuição.

## Reprodução e fronteira da verificação

```bash
python3 attempts/72-recursive-syntax-factor-width/check.py
.venv/bin/python attempts/72-recursive-syntax-factor-width/check.py --library
.venv/bin/ruff check attempts/72-recursive-syntax-factor-width/check.py
```

O primeiro comando usa somente a biblioteca padrão. Confere 20 coberturas
de matching, 107.929 partições balanceadas de componentes (exaustivas até
N=9 e amostras maiores), 5.256 contrações para o lema de afinidade,
128 palavras de palíndromos e 80 partições ponderadas do controle forte.
As comparações usam inteiros, inclusive após elevar afinidades ao quadrado.

O segundo comando também confere LL(1), massa e TODAS as marginais da
biblioteca contra palavras construídas independentemente para N=3,5,7,9.
O suporte é explicitamente o alfabeto finito de cinco tokens; não é uma
medição no vocabulário inteiro de um tokenizer real.

Os oráculos finitos não enumeram todos os grafos nem substituem a prova.
Não houve treinamento, modelo ou medição de desempenho neural. Esta
tentativa não altera o solver, o baseline ou fontes científicas congeladas.

## Auditoria adicional: resultado e decisão

Ponto de partida preservado: commit
`1804e5d94f860f46c69d67b39596b56f2624d709`. As seções 1–6 de `proof.md`
e os oráculos originais foram mantidos. A seção 7 acrescenta a auditoria,
as novas provas escritas e contraexemplos a interpretações mais amplas.

**Juízo:** o limite de erro 0,1 passou pela auditoria escrita realizada
nesta tentativa. Isso não é uma revisão humana independente. Isoladamente,
ele é uma robustificação bastante direta de um exemplo clássico; não há
base para apresentá-lo como contribuição própria suficiente para o TCC.
O resultado mais forte abaixo melhora o objeto teórico em investigação,
mas tampouco resolve sozinho prioridade, relevância e suficiência.

### Avanço teórico adjacente obtido

Na MESMA gramática fixa e com pesos unitários:

    capacidade máxima de bolsa W=o(N)  =>  TV(P_N,Q_N) -> 1.

Logo, qualquer erro constante menor que 1 exige capacidade linear em N,
e número exponencial de estados numa bolsa. A prova usa vários
separadores, não muda a linguagem nem os pesos e trata explicitamente
observados com domínio unitário. Mantém-se a cota original, melhor para
erro 0,1. Não se promove a nova prova a fonte científica já revisada.

Há ainda uma consequência precisa para representações mais próximas
da discussão atual de circuitos probabilísticos (PCs):

- P_N admite um PC suave, decomponível e determinístico de tamanho O(N²).
- Todo PC suave e estruturado por UM vtree, com folhas univariadas e
  tamanho `m=2^o(N)`, tem erro TV tendendo a 1. Para erro constante e<1,
  seu tamanho precisa ser `2^Ω_e(N)`, mesmo sem exigir determinismo.

A redução ponderada de PC estruturado a fatores é escrita na seção 7.3;
não se infere um resultado sobre probabilidades apenas de uma tradução
booleana de suportes. A construção quadrática por marcador e essa
redução são controles clássicos. O objeto candidato é a separação
ROBUSTA explícita, com erro tendendo a 1, para esse posterior fixo.

### Auditoria de prioridade mais específica

Fontes primárias consultadas em 2026-10-20 UTC; os trechos abaixo
complementam a tabela anterior. Buscas por combinações de palíndromos,
aproximação, TV, treewidth e structured decomposability não localizaram
o mesmo enunciado. Essa busca limitada não estabelece prioridade universal.

| Fonte e trecho | O que já cobre e o que não foi demonstrado ali |
| --- | --- |
| [Kadioglu/Sellmann, *Grammar Constraints* (2010)](https://doi.org/10.1007/s10601-009-9073-4), Teorema 6; texto dos autores disponível no link da tabela anterior | A MESMA linguagem binária de dois palíndromos, a cobertura dos pares de paridades opostas e a separação de autômatos sob reordenação são anteriores. Precisão de atribuição: esse Teorema 6 trata do controle regular; o limite para BCT com ocultos é a Proposição 7 de Wang/Yap. |
| [Wang/Yap (2023)](https://ojs.aaai.org/index.php/AAAI/article/download/25526/25298), Proposições 4, 7, 8 e Lema 1 | O centroide, a contagem dos pares e a separação exata de BCTs são antecedentes imediatos. Agrupar uma decomposição em bolsas para obter estados maiores também é clássico. A prova usa exatidão do suporte; não enuncia a lei aproximadora arbitrária em TV considerada aqui. |
| [de Colnet/Mengel (2021)](https://arxiv.org/pdf/2110.13014), Teorema 2, Seção 5.2 e Proposição 4 | Produtos balanceados e limites de fatoração para circuitos estruturados já são ferramentas estabelecidas; há separações exatas exponenciais. Não reivindicar separação geral entre classes de circuitos como ideia própria. |
| [Kučera (2023)](https://drops.dagstuhl.de/storage/00lipics/lipics-vol280-cp2023/LIPIcs.CP.2023.22/LIPIcs.CP.2023.22.pdf), Seções 3–4 | Equivalência polinomial entre BCT e SDNNF; o caminho exato entre esses formalismos já existe. A redução da seção 7.3 conserva somas e pesos, em vez de usar somente existência de testemunho. |
| [Pelekis/Ramon/Wang (2015), Teorema 2.1, atribuído a Finner (1992)](https://arxiv.org/html/1511.07204) | O lema multicomponente de afinidade é uma aplicação de desigualdade clássica, e não uma nova desigualdade. A prova por contrações apenas o torna autocontido. |
| [Leland/Choi (NeurIPS 2025), v2](https://arxiv.org/html/2506.01281v2), Teorema 4.1 e Seções 3.1, 5 | Limites exponenciais robustos em TV já são conhecidos. Ali o eixo da separação é acrescentar DETERMINISMO, e o alvo de Sauerhoff não é este posterior LL(1). Aqui o circuito pequeno já é determinístico, e a restrição custosa é UMA estrutura de decomposição. Não há reivindicação da ideia geral de robustificar uma separação exata. |
| [Amarilli et al. (STACS 2026)](https://drops.dagstuhl.de/storage/00lipics/lipics-vol364-stacs2026/html/LIPIcs.STACS.2026.5/LIPIcs.STACS.2026.5.html), Proposições 3.1, 5.3 e conclusão | Produtos posicionais condicionados a GLCs não ambíguas e compilação em circuitos tratáveis são antecedentes diretos. O resultado novo pretendido precisa ser inferior/robusto; compilar e avaliar uma gramática corretamente não bastaria. |
| [Zhao et al. (2026), v1](https://arxiv.org/html/2605.12940v1), Seção 7 e Teorema A.4 | A.4 assume que dois componentes não admitem um vtree comum pequeno e conclui uma separação EXATA por um seletor. A72 fornece um alvo explícito de gramática fixa e uma afirmação robusta mais forte, se a prova adicional estiver correta. A Proposição 2 sobre inexistência de reestruturação universal eficiente não substitui aquela hipótese de existência. |

O refinamento por vários separadores é também uma técnica clássica.
O corolário de circuitos é uma consequência do teorema, não uma segunda
contribuição independente. Não se encontrou uma lacuna no resultado
original que obrigasse a retirá-lo; a limitação encontrada foi a força
da afirmação e a distância até um benefício operacional.

### Consumidor em dLLMs e limites que realmente importam

O consumidor pertinente é uma camada que precisa REAMOSTRAR CONJUNTAMENTE
os slots ainda livres de um passo, sob a lei produto congelada condicionada
pela gramática. A pergunta arquitetural é se ela pode substituir recursão
por uma representação de estrutura única pequena com garantia de TV.
O teorema dá uma resposta negativa de pior caso a essa pergunta precisa.
Não cobre automaticamente seleção por marginais, MAP, validade ou qualidade.

[CoDD, ICML 2026](https://proceedings.mlr.press/v306/li26fd.html), Seções
4.1–4.3 e 5 da [v3 dos autores](https://arxiv.org/html/2603.00045v3), é
um consumidor real da operação produto de potenciais neurais com prior
em circuito, seguido de amostragem conjunta. Entretanto CoDD requer
DECOMPONIBILIDADE, não uma estrutura única na sua definição geral.
Assim, o circuito quadrático é compatível com esse formalismo: A72
não é uma impossibilidade para CoDD nem um resultado sobre seus dados.
A implementação/aprendizado de seu prior também não vira novidade nossa.

[FactorDLM, v1](https://arxiv.org/html/2609.32900v1), discussão de inferência
e Apêndice E, escolhe tabelas densas com custo pela largura e reconhece
circuitos como alternativa. A72 delimita esse parâmetro de representação;
não refuta uma promessa universal ausente do artigo. Não existe aqui
medição de que logits de um dLLM produzam a distribuição difícil.

Três controles impedem exagerar a consequência (provas na seção 7.4):

1. O produto das marginais de P tem todas as marginais univariadas exatas,
   mas sua TV conjunta tende a 1. Erro conjunto não é erro de toda consulta.
2. Uma palavra válida fixa dá validade 100% com capacidade zero.
3. Pesos ESTRITAMENTE POSITIVOS podem concentrar um marcador, permitindo
   aproximar o posterior por um único matching com erro arbitrariamente
   pequeno. Uniformidade é uma hipótese substantiva, não detalhe numérico.

Para esse alvo, condicionamento por marcador e PC contextual são controles
fortes suficientes. Para GLCs gerais não ambíguas, circuitos de parsing
e fatores simbólicos também precisam participar da comparação.
Seu custo pode depender de N, da gramática e do número de contextos;
o teorema não os declara baratos em toda aplicação. As contas de bits,
RNG e saída da seção 5 continuam válidas; os novos argumentos não
envolvem execução de modelo nem precisam de uma RTX 3080 Ti.

### Próximo avanço operacional, ainda não obtido

Uma direção mais substancial é caracterizar QUANDO os pesos e os
compromissos deixam uma família de GLCs/PCs mudar de decomposição de
forma compacta, com garantia de erro para a lei conjunta e custo menor
que avaliar o circuito completo. Operação pretendida: receber um circuito
gramatical não ambíguo já preparado e novos pesos racionais/commitments
compatíveis, e produzir amostras conjuntas com certificado de TV<=ε,
contando também o trabalho necessário para decidir quais ramos omitir.

Um teorema útil precisaria dar uma condição estrutural verificável e um
limite de preparação + atualização + amostragem que seja melhor em uma
classe com consumidor real. Apenas manter contextos de massa 1-ε e
renormalizar tem a garantia clássica TV=ε: NÃO é a contribuição. Só olhar
pesos do marcador tampouco basta, pois Z_j depende de todos os pares.
Ganhar depois de calcular exatamente todos os Z_j pode não poupar nada.

Ainda não há esse algoritmo nem teorema de vantagem; não se inventa um.
Antes de protótipo extenso ou campanha na GPU, esta própria tentativa
deverá fixar a classe de entradas, condição, prova, comparadores por
condicionamento/inside-outside/circuitos, custo em bits, caso favorável
natural e caso de recusa. Só então congelar casos, seeds e métricas.
O resultado desta rodada é a auditoria e o fortalecimento teórico acima,
não a seleção de um novo decoder para benchmark.

### Oráculos adicionais

`check.py` acrescenta, com seed separada 72002, verificações finitas do
separador múltiplo em árvores ponderadas, contagem com componentes de
peso l/K, atribuições fixadas, passo de mistura/aproximação da lei
projetada de tipos em aritmética racional e os controles de
marginais/validade/concentração. Não são
timings, revisão da prova inteira ou evidência de prioridade. Os casos
e as saídas originais da seed 72001 permanecem reproduzíveis.
