# Triagem por operação após A88

2026-10-22. Leituras e provas escritas, sem novos modelos, medições ou
protótipos. A meta positiva continua aberta. A qualificação A88 foi encerrada
como inconclusiva; esta triagem não a reabre nem altera seus dados.

## Rotas examinadas e não selecionadas

**Localização de edições coordenadas.** A revisão delegada
`source-led-real-gap-20261022-after-a88-r1` encontrou um consumidor real em
[How Should Diffusion Language Models Edit Code?, §§3–6 e H](https://arxiv.org/html/2609.38257v1).
O resultado com regiões-oráculo não se transfere à localização prevista;
abrir regiões maiores também prejudica a reconstrução. Isso documenta uma
necessidade, não um método próprio. [CORE, §4](https://arxiv.org/html/2602.04096#S4)
já mascara grupos para avaliar e revisar tokens. [WINO, §3.2](https://arxiv.org/html/2606.12232#S3.SS2),
[T2M](https://arxiv.org/html/2604.18738) e
[NAVIRA](https://arxiv.org/html/2606.06031) são controles adicionais.
Não foi identificado componente próprio com vantagem integral defensável;
nenhum protótipo ou campanha foi selecionado.

**Likelihood da sequência completa sob top-k dependente dos tokens amostrados.**
A revisão `native-density-rank-pivot-20261022-r1` validou a construção
seguinte, mas recomendou descartá-la como tema central por composição
insuficiente. O alvo é uma sequência de IDs de comprimento fixo, sem trim
por EOS, com propostas independentes por posição e estado suficiente que
não conserva propostas descartadas. A confiança de seleção pode diferir
da distribuição de geração.

Para uma ação S de tamanho k que compromete somente IDs-alvo, seja j seu
menor rank-alvo, com desempate por posição. Escreva `a_i=q_i(x_i)` e
`B_i(r)=P(rank_i(V_i)<r)`. A massa da ação é

    K_x(s,S) = produto_{i em S} a_i * produto_{i fora S} B_i(r_j).

Somar por pivôs evita enumerar todos os conjuntos:

    A_j = a_j [z^(k-1)] produto_{i != j}
          (B_i(r_j) + 1[rank_i(x_i)>r_j] a_i z),
    Z(s,x) = soma_j A_j.

Amostrando a ação proporcional a K e multiplicando Z a cada passo,
`E[W]=P_nativa(X_final=x)`. A prova soma as trajetórias compatíveis; é SIS
clássico com adaptação ao próximo evento. Não implica log-likelihood sem
viés ou dominância terminal de variância. Um controle uniforme pode ter
variância terminal zero enquanto essa adaptação tem variância positiva.

A operação difere de [DUEL, §§3–5](https://arxiv.org/html/2603.01367v1):
seu seletor escolhe posições antes dos novos valores. Porém,
[PAPL v3, §§3.1, A.4–A.5](https://arxiv.org/html/2509.23405v3) já define a
política e marginaliza propostas descartadas; [A52 V1](../../attempts/52-collapsed-commit-likelihood/work/theory-v1.md)
já calcula a massa de uma ação. Cada A_j reduz, após preservar a massa da
evidência, a uma contagem Poisson-binomial de grau k-1, coberta por
[Li–Saha–Deshpande, VLDB 2009, §4](https://www.vldb.org/pvldb/vol2/vldb09-769.pdf).
A proposta proporcional ao kernel e o peso normalizador também são
antecedentes de [SMC adaptado](https://www.cs.ubc.ca/~arnaud/doucet_johansen_tutorialPF.pdf)
e [guidance para difusão discreta, §3.2.2](https://arxiv.org/html/2310.15817).

Controles competentes da MESMA likelihood incluem SIS uniforme e SIS
proporcional ao produto dos a_i, com avaliação exata da ação e memoização
igual. Não basta vencer ocorrência bruta ou ELBO de outra política. O custo
de todos os limiares e DPs é `O(n V log n + n^2 k)` operações aritméticas por
estado, além do modelo, RNG e custo em bits. Não foi identificada contribuição
própria substancial; não abrir oráculo para contornar essa objeção.

## Em revisão: não interferência durante a seleção paralela

Esta seção registra uma hipótese distinta e suas provas escritas iniciais.
Não seleciona um tema, código ou campanha. A revisão independente
`dlm-flow-selection-gap-20261022-r1` examina o primeiro caso e os antecedentes.
O segundo caso abaixo é uma derivação adicional do agente principal.

Operação real: gerar, em um canvas, campos de níveis de confidencialidade
diferentes. O campo público deve ter a mesma lei sob substituição dos dados
privados por outros de mesmo tamanho, enquanto os campos privados ainda
podem usar esses dados. Labels, fronteiras e comprimentos são públicos e
fornecidos por uma política confiável; não se promete ocultar sua existência.

[What the Model Cannot See, §III](https://arxiv.org/html/2610.15883) já fornece
um veto de atenção em todas as camadas com não interferência das ativações
externas. [CoDA, Apêndice E](https://arxiv.org/html/2610.15177#A5) restringe
conteúdo e substrings; isso não é uma prova de não interferência.
[LLMbda](https://arxiv.org/html/2602.20064) e
[secure multi-execution para LMs](https://zenodo.org/records/22097472)
são antecedentes obrigatórios. Atenção segura, escalonadores não
interferentes e indução de acoplamento não são reivindicados como novos.

**Caso com amostragem.** Duas posições, L pública e H privada, top-1 por
confiança do token amostrado, dois passos, sem revisão. A cabeça L é sempre
`(.6,.4)`, inclusive após H ser preenchida. O segredo escolhe a cabeça H
`(.9,.1)` ou `(.5,.5)`, constantes ao longo da trajetória. No primeiro caso,
H vence com probabilidade .9 independentemente da proposta de L, de modo
que `P(L=A)=.6`. No segundo, L vence precisamente quando propõe A; quando
propõe B, fica para o passo seguinte. Logo `P(L=A)=.6+.4*.6=.84`.
O resultado público final depende do segredo apesar da cabeça pública
invariante; esconder os tempos intermediários não elimina esse canal.

**Caso guloso, sem RNG.** Três posições, L1/L2 públicas e H privada, top-2
no primeiro passo e a última posição no segundo. A confiança inicial de
L1 é .9 para A; a de L2 é .8 para B. Se L1=A já estiver visível e L2 ainda
mascarada, L2 passa a preferir A com .95. Essas cabeças dependem somente
do estado público. O segredo faz H preferir um token com confiança .99
ou .6. No primeiro caso, H e L1 são preenchidas juntas e L2 depois produz A.
No segundo, L1 e L2 são preenchidas juntas e L2 produz B. As saídas públicas
finais são determinísticas e distintas: distância de variação total 1.
Não há dependência explícita de tempo nem leitura privada nas cabeças L.

A correção candidata combina o veto em todas as camadas com escolhas,
quotas, relógios, RNG e parada públicos dependentes apenas do estado
público. Decisões privadas não alteram a trajetória pública. Sob kernels
públicos iguais e streams públicos acoplados, indução dá trajetórias públicas
iguais. Isso ainda precisa ser comparado a filas locais, execução pública
primeiro e multi-execução isolada; combinar mecanismos conhecidos sem
avanço próprio não seleciona o tema.

Gramáticas conjuntas exigem outro cuidado: condicionar o produto público /
privado em G dá marginal pública proporcional a `q_L(u) Z_h(u)`. Essa
partição pode depender do segredo. A versão inicial teria somente campos
gramaticais independentes e wrapper público fixo, sem tokens cruzando labels.
Não se transfere a garantia a relações arbitrárias entre campos, padding,
stops privados, self-conditioning ou kernels cujo estado não foi isolado.

Benefício a verificar: não interferência da geração completa, conservando
uso privado e paralelismo, sem treinamento. Ainda faltam prioridade específica,
componente próprio suficiente, consumidor e avaliação de qualidade/custo
contra controles com a mesma visibilidade. A prova abstrata não demonstra
bit-identidade de um executor GPU, ocultação de latência física, melhoria
neural ou viabilidade integral na GPU. Nenhuma captura foi autorizada por
esta triagem.

### Revisão independente R1 e fronteira ainda aberta

A revisão `dlm-flow-selection-gap-20261022-r1` confirmou o caso amostrado,
com distância de variação total .24 nas saídas finais. Conferiu a regra de
propostas, `gather` da confiança do token proposto e `topk` no
[controlador oficial LLaDA](https://raw.githubusercontent.com/ML-GSAI/LLaDA/main/generate.py).
Isso identifica um controlador pertinente, não estados observados em um
checkpoint. A revisão também confirmou a prova construtiva e a ressalva
das fibras, com hipóteses explícitas sobre todo o estado observável.

Acrescentou dois antecedentes importantes: [CIV, §§4.3 e 6.2](https://arxiv.org/html/2508.09288)
para labels e máscaras de atenção em modelos congelados, sem importar sua
prova cujo sentido da desigualdade de confiança diverge entre essas seções;
e [Popescu–Hölzl–Nipkow](https://www.andreipopescu.uk/pdf/CALCO2013.pdf)
para o canal clássico em que escalonamento altera a distribuição do valor
público final. [Faceted SME](https://users.soe.ucsc.edu/~cormac/papers/18ccs.pdf)
também é antecedente de compartilhamento de execução seguro. Nenhum desses
ingredientes é reivindicado como próprio.

O parecer R1 recomenda não selecionar o método central: a correção proposta
é operacionalmente igual a barreira + filas locais + RNG endereçado + saída
segura. A análise pode fornecer um diagnóstico específico, mas ainda não
mostra contribuição própria suficiente ou vantagem neural. Nenhum oráculo
foi executado por esse parecer. O caso guloso escrito acima não fez parte
do brief inicial e ainda não recebe validação independente por R1.

A nova revisão `dlm-flow-contribution-greedy-20261022-r2` recebeu o brief
original, os achados R1, o caso guloso e a objeção de composição. Examina a
fronteira entre um método já conhecido para a mesma operação e uma capacidade
nova obtida por mecanismos clássicos, além de procurar uma diferença
construtiva verificável em relação às filas locais. Não autoriza código ou
campanha; selecionar pela ausência de publicação idêntica continuaria errado.

A inspeção estática do checkpoint LLaDA local encontrou outra fronteira:
`attention_bias` é aceito, mas máscaras booleanas usam o menor valor finito
do dtype, e `_cast_attn_bias` pode substituir infinito negativo por esse
valor. A prova para uma barreira ideal não certifica esse caminho numérico.
Não houve alteração dos pesos, cache ou implementação externa, nem execução.
