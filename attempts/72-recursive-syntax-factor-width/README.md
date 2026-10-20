# A72 — Limite robusto para representações de sintaxe recursiva

Investigação de 2026-10-20 (UTC). **Decisão após a V2: não selecionar A72
como contribuição central do TCC.** A aplicação por convoluções falhou
em 6/6 casos neurais no critério congelado de cobertura e vantagem.
As provas e os resultados negativos ficam preservados nesta tentativa.

Há uma prova escrita e oráculos finitos.
A auditoria adicional abaixo sustenta o argumento original e acrescenta
um teorema de erro tendendo a um e um corolário para circuitos estruturados.
A prioridade específica e a suficiência científica continuam abertas.
As seções V1 abaixo antecedem as capturas neurais V2 documentadas ao final.
Não há ganho integral de decoder nem aprovação acadêmica estabelecidos.

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
Na V1 não houve treinamento, modelo ou medição de desempenho neural.
A V2 abaixo acrescenta capturas e medições separadas, sem treinamento.
Esta tentativa não altera o solver ou o baseline; as fontes e os dados
anteriores permanecem preservados nos respectivos commits.

## Auditoria adicional: resultado e decisão

Esta é a avaliação V1. A decisão posterior, com dados reais V2, está
na seção final e substitui sua condição de aposta central ainda aberta.

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

## V2 — Resultado operacional real e decisão final desta investigação

**A72 não foi selecionada como contribuição central do TCC.** Há um
resultado matemático escrito sobre representação, mas a operação
adjacente implementada não passou no critério de utilidade. Essa decisão
não depende de provar que nenhuma publicação possível contém a extensão.
O argumento positivo necessário — resultado próprio suficiente e
benefício pertinente — não foi estabelecido, e o gate operacional foi
negativo. Não se propõe outra campanha para salvar esta aplicação.

### Protocolo e fontes congelados antes dos dados

- `e763bc35`: [protocolo V2](protocol-v2.md) e seção 8 de [proof.md](proof.md),
  com operação, derivação, hipóteses, comparadores, custos, objeções e gate.
- `208b22b9`: [implementação produtora](operational_v2.py), antes de capturar
  os logits ou medir os 42 casos. Não foi alterada após observar resultados.
- [Captura](capture-v2.jsonl): seis forwards reais do LLaDA-8B-Instruct,
  snapshot `08b83a6feb34df1a6011b80c3c00c7563e963b07`, NF4, sem treinamento.
- [Resultados](results-v2.jsonl): todos os 36 casos sintéticos e seis
  casos neurais, cinco repetições, recusas, tempos, TV racional e
  testemunhos. SHA-256 da captura e do resultado são conferidos pelo auditor.
- [Auditor independente](audit_v2.py): refaz massas por outra construção
  de blocos aninhados, confere TV com inteiros, recusas e testemunhos.
  Ele lê os dados congelados e não produz novos timings.

A hipótese era evitar avaliar os O(N²) pares pela expansão de
`log(1+xy)` e convoluções triangulares, preparando a distribuição do
marcador e depois amostrando tipos com inteiros. A seção 8 prova a
aproximação em aritmética real quando `|xy|<=ρ<1`. Isso é mais preciso
que prometer “fatores mais rápidos”: especifica operação, erro e classe.
O protótipo FFT64 paga uma certificação inteira independente; a cota
de Taylor sozinha não certifica seus arredondamentos.

### Medições observadas

Todos os seis forwards terminaram na RTX 3080 Ti de 12 GiB, sem OOM
ou timeout. O pico próprio de alocação CUDA foi 6.217.531.904 bytes
(5,79 GiB); havia processos alheios na GPU, que foram preservados.
A carga levou 112,46 s; os seis forwards somaram 1,474 s e a normalização
e transferência dos pesos selecionados somou 0,252 s. Esses custos
não foram incluídos gratuitamente em nenhum suposto ganho do componente.
São capturas de um passo, não uma avaliação de trajetória ou qualidade.
O pico de reserva CUDA foi 6.396.313.600 bytes; o RSS do processo de
captura chegou a 3.841.636 KiB e o processo de medição CPU a 414.840 KiB.
O ambiente usou Python 3.11.16, NumPy 2.4.6, Torch 2.8.0+cu128,
Transformers 4.52.2 e bitsandbytes 0.50.1. Os registros também contabilizam
bits dos inteiros de entrada/massa e bits efetivamente usados pelo RNG.

| Casos | Propostas calculadas | Recusas pelo grau | Passaram erro e vantagem integral |
| --- | ---: | ---: | ---: |
| Sintéticos | 25/36 | 11/36 | 0/36 contra condicionamento inteiro |
| Pesos neurais reais | 4/6 | 2/6 | **0/6** |

Nas 29 propostas calculadas, a maior TV conjunta foi
`1,8674221832467788e-5`, abaixo de `ε=0,01`. Isso foi calculado
exatamente com racionais sobre as massas dos contextos, e não estimado
por um histograma de poucas amostras. A igualdade entre TV dos contextos
e TV das palavras é provada na seção 8: as condicionais são as mesmas
e os suportes dos marcadores são disjuntos.

As 13 recusas foram confirmadas pelo auditor com uma desigualdade
racional: nem grau 64 atende à cota de cauda fixada. Não significam
inviabilidade da gramática nem impossibilidade de outro aproximador.
Nos pesos neurais, ρ variou de 0,79166 a 0,92311; os quatro casos
aceitos exigiram graus 40–54. A prova de custo favorável sob viés
limitado não tornou essas instâncias baratas no programa.

| Caso neural | Preparação FFT | Circuito contextual completo | Total FFT certificado | Condicionamento inteiro + amostra |
| --- | ---: | ---: | ---: | ---: |
| instrução 0, N=33 | 6,758 ms | 0,264 ms | 6,867 ms | 0,090 ms |
| instrução 0, N=129 | 10,487 ms | 1,008 ms | 13,109 ms | 2,422 ms |
| instrução 0, N=513 | 22,572 ms | 5,306 ms | 123,250 ms | 101,882 ms |
| instrução 1, N=33 | recusa | 0,266 ms | recusa | 0,088 ms |
| instrução 1, N=129 | recusa | 1,359 ms | recusa | 2,180 ms |
| instrução 1, N=513 | 15,955 ms | 4,388 ms | 114,831 ms | 104,384 ms |

Tempos são medianas em CPU. “Total certificado” soma as medianas de
preparação, auditoria e amostra, conforme os campos brutos; não é uma
medição única da trajetória completa. O circuito completo nessa tabela
é o componente numérico vetorizado; seus próprios totais com auditoria
também estão no arquivo. A proposta FFT perdeu para esse componente em
todos os quatro casos neurais aceitos, antes de cobrar certificação.
Não há dúvida de decisão decorrente de como amortizar a auditoria.

Houve um efeito sintético real, mas insuficiente: em N=2049 e viés 0,25,
a mediana entre as três seeds foi 12,171 ms para a proposta FFT contra
17,102 ms para o circuito vetorizado. Ao cobrar a certificação, o total
FFT foi 523,813 ms, contra 487,982 ms só para preparar massas inteiras.
Apenas 5/29 propostas venceram o componente vetorizado; nenhuma venceu
o controle inteiro no total certificado. O algoritmo da auditoria
recalcula o alvo completo: essa implementação acrescenta trabalho ao
controle exato. Esse custo foi declarado antes da medição, não removido
depois para fabricar uma vitória.

O controle que ignora tipos foi barato, mas sua TV nos seis casos
neurais ficou entre 0,03972 e 0,38100, acima de 0,01 em todos eles.
Logo não explica um resultado positivo por uma aproximação ainda mais
simples. A biblioteca LL(1) confirmou massa e marginais do marcador em
todos os 11 casos N=33 (nove sintéticos e dois neurais); seu custo não
foi usado como único comparador. Todos os 22 testemunhos neurais
armazenados passaram reconhecimento independente da gramática.

### Escopo dos dados e auditoria de antecedente da operação

Os IDs originais são `7,8,58,60,2` para `(`,`)`,`[`,`]`,`#`.
São somente cinco IDs declarados: a massa conjunta por posição desses
IDs variou de `1,70649e-6` a `0,27461`. O restante do vocabulário está
fora desta operação e não foi renormalizado silenciosamente como se
fosse exatidão no vocabulário inteiro. A lei auditada é a dos pesos
binários64 congelados nesse suporte. As condicionais usam inteiros e
o marcador proposto é convertido explicitamente a uma lei racional.
Não foi demonstrada qualidade semântica nem vantagem de geração inteira.

O novo componente também tem antecedentes próximos que limitam qualquer
alegação de originalidade:

- [Baba et al., *A Generalization of FFT Algorithms for String Matching*
  (2003)](https://www.researchgate.net/publication/31910345_A_Generalization_of_FFT_Algorithms_for_String_Matching),
  Lema 1: decompor o score em características separáveis para usar
  convoluções é clássico. O texto primário foi conferido; não se
  apresenta FFT ou a fatoração do kernel como invenção nossa.
- [Christodoulakis et al., *Pattern Matching on Weighted Sequences*,
  manuscrito de 17/09/2004](https://www.researchgate.net/publication/228981923_Pattern_Matching_on_Weighted_Sequences),
  seção 3.2: transformar produtos em somas de log-probabilidades e
  aplicar FFT já é explícito. O texto distingue padrão sólido de dois
  lados ponderados; essa distinção não comprova novidade da nossa
  aproximação restrita, muito menos benefício para dLLMs.

Portanto a posição final é concreta: manter os teoremas e suas provas
escritas como resultado teórico delimitado; **encerrar a aplicação V2
e retirar A72 da posição de contribuição central selecionada**. A prova
não foi refutada por esses dados. O que falhou foi transformar essa
fronteira de representação, ou a hipótese adjacente por convoluções,
na contribuição própria, geral e útil que o projeto procura.

### Reprodução V2

Auditar as capturas e medições preservadas, sem GPU:

```bash
python3 attempts/72-recursive-syntax-factor-width/audit_v2.py
```

O auditor confirma 42 casos, 113 TVs conjuntas exatas, 13 recusas
independentes, 22 testemunhos e gate neural 0/6. Para repetir uma
captura ou timing, use a fonte `208b22b9` e NOVOS caminhos de saída:

```bash
.venv-live/bin/python attempts/72-recursive-syntax-factor-width/operational_v2.py \
  capture --output /tmp/a72-new-capture.jsonl
.venv/bin/python attempts/72-recursive-syntax-factor-width/operational_v2.py \
  measure --capture /tmp/a72-new-capture.jsonl --output /tmp/a72-new-results.jsonl
```

O produtor recusa sobrescrever saídas. Não atribuir novos timings à
rodada congelada nem alterar casos, tolerância ou limite de grau para
resgatar o gate. Os resultados desta V2 não alteram fontes/dados da V1.
