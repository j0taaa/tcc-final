# A82 — Cinco operadores para investigar em dLLMs

20/10/2026. Triagem solicitada pelo usuário após a busca concentrada em
inferência exata. Adaptações substanciais de métodos autorregressivos são
admitidas. Esta tentativa registra cinco propostas distintas, suas provas
delimitadas e objeções. Não declara prioridade mundial, vantagem neural ou
tema de TCC aprovado. Não reabre aplicações negativas anteriores.

Três subagentes fizeram a descoberta; cada proposta tem uma thread própria
com uma rodada de verificação e um revisor independente. As threads usam o
checkout compartilhado somente para leitura. Nenhuma campanha neural está
selecionada. Protocolos abaixo são desenhos preliminares, não protocolos
congelados de medição.

| Proposta | Operação | Thread |
| --- | --- | --- |
| B1 | Coordenar tokens vizinhos para reduzir repetições | [Verificação](t3-thread://v1/thread:mcp:0500190c-aab1-49b6-b9b0-4a249c29550e:reset-five-20261020-five-operator-verification-v1:0) |
| B2 | Produzir respostas completas sem reposição | [Verificação](t3-thread://v1/thread:mcp:0500190c-aab1-49b6-b9b0-4a249c29550e:reset-five-20261020-five-operator-verification-v1:1) |
| B3 | Entregar campos irrevogáveis antes do documento completo | [Verificação](t3-thread://v1/thread:mcp:0500190c-aab1-49b6-b9b0-4a249c29550e:reset-five-20261020-five-operator-verification-v1:2) |
| B4 | Construir decisões coerentes preservando marginais | [Verificação](t3-thread://v1/thread:mcp:0500190c-aab1-49b6-b9b0-4a249c29550e:reset-five-20261020-five-operator-verification-v1:3) |
| B5 | Responder ou pedir informação ausente com certificado | [Verificação](t3-thread://v1/thread:mcp:0500190c-aab1-49b6-b9b0-4a249c29550e:reset-five-20261020-five-operator-verification-v1:4) |

## B1: evitar escolhas repetidas no mesmo passo

**Uso e método.** Tokens amostrados independentemente no mesmo passo podem
repetir a mesma palavra. Escolher previamente um caminho ou floresta entre
posições simultâneas e coordenar seus sorteios. Uma versão usa a lei de Potts
`Q(x) ∝ ∏ p_i(x_i) r^C(x)`, com `r` racional. Uma alternativa mais forte
preserva as marginais: calcular um transporte ótimo por aresta e juntar os
transportes como uma cadeia/árvore de Markov.

**Hipóteses e prova da alternativa.** O head é congelado; as distribuições
finitas são declaradas. O custo por aresta é 1 quando ambas as posições têm
a mesma classe em um conjunto previamente escolhido `S`, e 0 caso contrário.
Para marginais `p,q`, a menor colisão possível é
`δ = max(0, max_{c∈S}(p(c)+q(c)-1))`. O limite inferior é de Fréchet. Sem
diagonal forçada, o fluxo que proíbe as diagonais de `S` é viável: as condições
de Hall ponderadas reduzem-se aos singletons, pois duas linhas distintas têm
todos os destinos como vizinhos. Se `δ>0`, somente uma classe pode exigi-lo;
reservar essa massa na diagonal deixa um problema residual viável.

Em uma árvore, amostrar a raiz por sua marginal e cada filho pela condicional
do transporte conserva todas as marginais e realiza todos os ótimos de
arestas simultaneamente. Portanto minimiza a soma esperada de colisões entre
todos os acoplamentos dessas marginais. O erro esperado de qualquer perda
aditiva por posição também fica igual ao da amostragem independente. Isso
não preserva a trajetória futura nem garante fluência ou acerto da resposta.

Classes agregam massas e depois devolvem IDs originais pela condicional
interna. Uma classe residual livre permite limitar `S` sem descartar massa:
o ótimo então cobre somente as colisões declaradas em `S`. Pins são pontos
de massa. EOS ausente nesta primeira operação. Grafos com ciclos não recebem
a garantia de juntar ótimos locais. Três bits uniformes em um ciclo ímpar
não podem discordar nas três arestas. Restrições gramaticais adicionais
também podem tornar o transporte inválido; um filtro posterior pode alterar
as marginais. A garantia é sobre o sorteio declarado antes desses filtros.

**Construção esparsa proposta, antes do protótipo.** Um transporte por
quantis tem no máximo `2K−1` átomos. Enquanto duas diagonais penalizadas forem
positivas, mover o mínimo das duas massas para as duas posições cruzadas.
Cada operação elimina uma diagonal; há no máximo `K−1` operações. Resta no
máximo uma diagonal penalizada `(d,d)`. Percorrer os átomos fora da linha e
coluna `d`, trocando massa de `(d,d),(j,k)` para `(d,k),(j,d)`. Os novos átomos
tocam `d`, portanto não entram nesse percurso. Se a diagonal não zerar,
esgotou-se a massa externa e ela vale `p(d)+q(d)−1`, o limite inferior.

Manter átomos repetidos como eventos com massas explícitas evita depender
de uma tabela hash: no máximo `4K−3` átomos antes do último percurso e
`12K−9` ao final, contando até os zerados. São `O(K)` operações aritméticas
e memória; o custo em bits dos racionais deve ser contabilizado separadamente.
Isso permite considerar o vocabulário inteiro, sem supor um transporte denso
`V²`. Transferência CPU/GPU e construção/amostragem eficiente ainda não foram
medidas. Cancelamento de ciclos em transportes é clássico; esta descrição
não estabelece prioridade para a construção.

**Antecedentes e diferença pretendida.** Acoplamentos, transportes, junção
em árvores e Potts são clássicos. [Mosaic](https://arxiv.org/html/2607.07026v1)
e [FactorDLM](https://arxiv.org/html/2609.32900v1) já coordenam posições por
restrições. [R²-dLLM](https://arxiv.org/html/2604.18995v1) já trata clusters
de repetição durante inferência; é controle obrigatório. A diferença candidata
é uma transição antirrepetição sem treino nem forward adicional que preserve
as marginais do head, com custo operacional delimitado. O problema aparece
em [On the Role of Discreteness](https://arxiv.org/html/2512.22630v1), §5.2.

**Benefício, controle e custo.** Medir repetição, acurácia e repetições
legítimas destruídas com o mesmo orçamento de forwards. Comparar com sorteio
independente, penalidade usual, reparo local e R²-dLLM. Cobrar agrupamento,
transporte, RNG, mensagens, sincronização e memória. Zero forward adicional
não significa custo zero. Se o reparo barato oferecer qualidade/custo melhores,
a garantia marginal pode ser insuficiente como contribuição prática.

O ganho por aresta sobre sorteios independentes é
`Σ_{c∈S} p_i(c)p_j(c) − δ_ij`. Distribuições determinísticas têm ganho zero;
marginais muito concentradas podem oferecer pouco benefício. A aplicação é
amostragem estocástica com temperatura declarada, não correção gratuita de
um decoder guloso. Oportunidade matemática não garante benefício semântico.

[SAC-Copula](https://arxiv.org/html/2608.20839v1) já correlaciona perturbações
Gumbel durante inferência de dLLMs para watermarking. Portanto correlacionar
ruído ou preservar marginais isoladamente não é a novidade candidata.
[CONDOR](https://arxiv.org/html/2609.06324v1) aprende dependências por treino;
é outro antecedente, com requisitos diferentes.

## B2: respostas completas sem duplicatas

**Uso e método.** Evitar gastar um orçamento de alternativas entregando a
mesma resposta. Adaptar [UniqueRandomizer](https://proceedings.mlr.press/v119/shi20a/shi20a.pdf)
a uma política dLLM monotônica: escolher posições deterministicamente antes
dos sorteios, sortear somente tokens retidos, nunca desfazer compromissos e
usar backbone e desempates determinísticos. Cachear estados da trajetória.
Manter a política-base fixa entre respostas, inclusive seu scheduler; escolher
posições a partir dos logits-base, sem usar as massas já alteradas por WOR.

**Prova e fronteira.** A resposta final em IDs determina a trajetória por
indução: o estado anterior determina as posições e a resposta determina os
tokens revelados. A árvore de escolhas é, assim, injetiva nas respostas.
Remover folhas já entregues produz
`P(next=y | anteriores) = Pπ(y)/(1−Σanteriores Pπ)`.
A probabilidade de atingir um conjunto de sucesso em `k` respostas é pelo
menos a de `k` sorteios independentes da mesma política: após falhas, só foi
removida massa de insucessos. Isso não compara políticas diferentes.

Remasking, ruído descartado e EOS/truncamento podem quebrar a injetividade.
IDs distintos podem produzir os mesmos bytes. A política proposta não é a
trajetória nativa. A lei racional ideal não certifica automaticamente floats.

**Diferença e controles.** O sampler é conhecido; a construção e avaliação
de uma política dLLM utilizável são o trabalho candidato. Comparar com IID
mais deduplicação, [Prism](https://arxiv.org/html/2602.01842v1),
[UnMaskFork](https://arxiv.org/html/2602.04344v1) e as temperaturas de posição
de [Tale of Two Temperatures](https://arxiv.org/html/2604.09921v1).
A37 investigou outro contrato, preservando marginais de geradores completos;
não se atribui novidade à ideia genérica de diversidade.

**Custo e refutação.** Contar todos os forwards de ramos divergentes, trie,
RNG, aritmética, memória e saída. Medir alternativas distintas em bytes e
sucesso por orçamento completo. Se a mudança de política perder qualidade
ou IID com deduplicação vencer, a adaptação não se justifica.
IID da mesma política com rejeição até obter o próximo resultado novo já
produz exatamente a mesma lei WOR. Dar a esse controle o mesmo cache de
canvases/logits é obrigatório; a candidata precisa justificar economia de
trabalho, e não uma vantagem de qualidade entre leis idênticas.

## B3: campos prontos antes do restante da resposta

**Uso e método.** Uma API pode receber `set(caminho, valor)` quando um campo
ficar pronto, mesmo que posições anteriores estejam mascaradas. O decoder
continua normalmente. Um certificado conservador verifica região, fronteiras,
identidade do caminho e existência de completação; começar com esquema JSON
delimitado, chaves únicas e posições finitas.

A unicidade das chaves precisa ser verificada após decodificar escapes. O
decoder deve manter viabilidade em todos os passos e informar falhas/abortos;
um testemunho válido no instante da emissão não garante que uma política
arbitrária terminará com sucesso. Latência até campos é uma métrica diferente
de latência até um documento completo e correto.

**Prova.** Se os conjuntos não vazios de completações válidas satisfazem
`F(t+1) ⊆ F(t)` e todo documento em `F(t)` tem o mesmo valor no mesmo caminho,
esse valor persiste nas finalizações. Um trecho visível isolado não certifica
o caminho: um prefixo ainda aberto pode mudar seu nível de aninhamento.
Compromissos reversíveis exigem outra política, não este observador.

**Antecedentes.** A53 já provou absorção de observáveis para parar geração;
sua aplicação negativa continua encerrada. Aqui a operação é publicar campos
durante uma geração que prossegue. [Longest Stable Prefix](https://arxiv.org/html/2603.05454v1),
[StreamingdLLM](https://arxiv.org/html/2601.17917v3) e
[SGLang](https://arxiv.org/html/2312.07104v2) são controles próximos.
O princípio de estabilidade não é novo; uma interface dLLM útil e sua
certificação barata ainda precisam justificar contribuição própria.
[Answer First, Reason Later](https://arxiv.org/html/2608.05687v1) também já
observa respostas que congelam antes do texto anterior. Resta demonstrar o
valor adicional da entrega certificada por campo ao consumidor.

**Benefício e custo.** Na mesma trajetória, um observador que oferece todos
os certificados do observador de prefixos pode entregar cada campo tão cedo
quanto ele, e antes quando há uma região pronta além do prefixo. Comparar
também AR com campos prioritários primeiro e consultas independentes. Cobrar
certificação, parsing, eventos e cliente. Ganho pode ser zero ou desaparecer
com uma ordem AR competente. Não há garantia de verdade semântica.

## B4: coerência sem alterar probabilidades anunciadas

**Uso e método.** Várias decisões com exclusões, hierarquias ou capacidades
devem formar configurações válidas sem alterar suas frequências declaradas.
Enumerar um conjunto pequeno `F` de configurações e resolver
`q ≥ 0`, `Σ q = 1`, `Σ_{x_i=a} q(x) = p_i(a)`.
Retornar testemunho racional ou certificado de incompatibilidade. Uma operação
separada pode minimizar o ajuste marginal quando o sistema for incompatível.

**Prova e exemplo.** Verificar essas igualdades certifica regras e marginais;
um separador linear certifica impossibilidade. Para exatamente um de dois
bits e marginais `(3/5,2/5)`, entregar `(10)` com massa `3/5` e `(01)` com
`2/5` preserva ambas. Condicionar o produto fornece `9/13,4/13`, alterando-as.
Marginais `(7/10,7/10)` são incompatíveis porque exigem soma esperada `7/5`.

**Antecedentes e diferença.** Isso é
[satisfatibilidade probabilística clássica](https://www.ijcai.org/Proceedings/11/Papers/096.pdf).
FactorDLM já condiciona o produto por relações; dJev já oferece dependências
entre perguntas. A diferença candidata é disponibilizar a operação marginal
com diagnóstico explícito sobre leituras paralelas, não inventar PSAT.

**Benefício, custo e objeção.** Validade e desvio marginal são verificáveis.
Enumerar suporta custo exponencial; cobrar LP, certificados e amostragem em
bits, além do modelo. Comparar com PSAT genérico, produto condicionado, reparo
e decisões por estágios. Logits não são probabilidades calibradas por decreto.
Sem consumidor que precise dessas marginais, a integração pode ser rasa.
Uma política randomizada com probabilidades de inclusão anunciadas é um
consumidor defensável; amostrar esse acoplamento e depois usar argmax não
preserva o contrato. Arredondamento dependente clássico também é controle
obrigatório para seleção com capacidades. Coerência de pares não certifica
compatibilidade global.

## B5: decidir ou esclarecer campos ausentes

**Uso e método.** Um sistema recebe um formulário incompleto e responde ou
pergunta o que falta. Enumerar todas as completações admissíveis de poucos
campos finitos e calcular a decisão determinística `f(v)` sob contrato fixo.
Responder somente se todas concordam; senão mostrar duas testemunhas que
discordam e compilar perguntas por minimax.

**Prova.** A unanimidade certifica estabilidade no domínio enumerado, não
correção no mundo. Para conjunto não vazio `V`, a recorrência clássica
`D(V)=0` se `f(V)` for constante; caso contrário,
`D(V)=1+min_j max_a D(V[j=a])` fornece a menor profundidade de perguntas,
por indução no número de atributos restantes. Domínio vazio é recusado.
Uma máscara não marginaliza magicamente todas as entradas possíveis.
As completações devem ser avaliadas em contextos independentes. A tabela
congelada é somente restringida após respostas; introduzir o histórico das
perguntas em novas consultas pode mudar `f`. Uma pergunta minimax ótima
pode deixar ambiguidade e exigir outras perguntas.

**Antecedentes e diferença candidata.** dJev tem `ask_if`/`depends_on`;
[Anchors](https://homes.cs.washington.edu/~marcotcr/aaai18.pdf) e
[Learning to Ask Good Questions](https://aclanthology.org/P18-1255/) são
antecedentes de estabilidade e esclarecimento. Enumeração e árvore ótima
são clássicas. O trabalho proposto seria o operador dLLM verificável com
contraexemplos e perguntas; sua vantagem específica ainda não foi demonstrada.
[Béjar et al. (2023)](https://arxiv.org/html/2306.15803v1), §§3–4, já tratam
classes alcançáveis sob entradas incompletas com restrições. A decisão entre
esclarecer e agir também aparece em
[Dong et al. (ACL 2026)](https://aclanthology.org/2026.acl-long.1987.pdf).
São antecedentes mais próximos; o núcleo do operador não é uma descoberta.

**Custo e refutação.** Comparar com defaults, perguntar tudo, ordens fixas,
heurísticas e a mesma enumeração com AR. Cobrar todas as completações, ainda
que em batch, memória e construção da árvore. A hipótese útil é reduzir
interações sem piorar a decisão pelo custo aceitável. Se AR ou uma regra
determinística entregar o mesmo contrato melhor, o uso de dLLM não se justifica.

## Verificação e próximos passos

O oráculo local é reproduzível sem dependências nem modelo:

```bash
python3 attempts/82-five-operator-screening/oracles.py
.venv/bin/ruff check attempts/82-five-operator-screening/oracles.py
.venv/bin/ruff format --check attempts/82-five-operator-screening/oracles.py
```

Ele confere 8.200 transportes por fluxo racional contra a construção esparsa,
incluindo todos os subconjuntos de diagonais penalizadas, e 125 palavras em
IDs originais para a junção de três posições com aliases. Nesse exemplo
construído, as colisões esperadas caem de `14/25` para `1/10`; isso não é
uma taxa medida de repetição em um modelo. Também verifica 16 canvases com
trajetória injetiva, nove desigualdades WOR, oito publicações de campos,
testemunho/separador marginal e uma árvore de duas perguntas para oito
completações. Inclui contraexemplos de ciclos, gramática adicional, ruído
descartado, caminho JSON móvel e preenchimento por defaults.

As cinco threads também executaram verificações próprias, sem arquivos,
modelos ou tempos. Seus conjuntos se sobrepõem; os totais não devem ser
somados como casos independentes.

| Proposta | Evidência da rodada | Decisão científica |
| --- | --- | --- |
| B1 | 9.928 casos racionais na thread; transporte mínimo, construção esparsa e junção em florestas confirmados, com revisor independente. | Melhor candidata desta triagem para investigar. Qualidade do texto, utilidade e ganho integral continuam em aberto. |
| B2 | 703 leis condicionais WOR e 33.456 triplas enumeradas; revisor confirmou injetividade, lei e limite contra IID da mesma política. | Adaptação correta; prioridade secundária. IID com rejeição e o mesmo cache produz a mesma lei e é controle eliminatório. |
| B3 | 3.072 estados parciais, 1.664 eventos e 3.456 verificações de finais; revisor confirmou contrato restrito e escapes. | Adaptar, baixa prioridade como tema isolado: disponibilidade de slots e invariância já são conhecidas. |
| B4 | 252 entradas racionais, 82 testemunhos e 170 separadores; revisor confirmou provas e incompatibilidade global apesar de coerência local. | Adaptar somente para consumidor que precise das marginais; PSAT e arredondamento dependente são controles da mesma operação. |
| B5 | 6.560 tabelas na thread e 6.903 casos parcialmente sobrepostos no revisor, sem divergências. | Adaptar, baixa prioridade como tema central: enumeração, estabilidade e perguntas ótimas já são clássicas; vantagem dLLM ausente. |

Os oráculos finitos não são medições de performance. Cada thread incorporou
um único subagente independente; são verificações por IA, não revisão humana
ou acadêmica. Nenhuma proposta tem prioridade mundial ou benefício neural
estabelecido. A recomendação B1/B2 é uma decisão de triagem, não aprovação
acadêmica ou declaração de resultado positivo no TCC.

Antes de uma campanha, selecionar com o usuário a candidata e congelar
modelo, implementação, entradas, seeds, métricas, controles e custos. Não
há autorização científica implícita para descartar perdas ou trocar casos.

Há uma RTX 3080 Ti de 12 GB. O checkpoint
[Qwen3 MDLM pequeno](https://huggingface.co/dllm-hub/Qwen3-0.6B-diffusion-mdlm-v0.1)
declara 0,8B parâmetros e o
[Fast-dLLM v2](https://github.com/NVlabs/Fast-dLLM/blob/main/v2/README.md)
oferece 1.5B. Tamanho dos pesos não verifica pico de memória, compatibilidade
ou qualidade. O segundo é causal entre blocos; não assume infilling global.
Nenhum modelo foi executado nesta triagem.
