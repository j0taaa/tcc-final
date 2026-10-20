# B1 — O que a utilidade matemática permite afirmar

20/10/2026. Continuação da triagem A82 a pedido do usuário. Esta nota separa
um benefício em uma operação definida de uma melhoria geral de dLLMs. As
fontes e o oráculo inicial de A82, congelados em `7a07e803`, permanecem intactos.
Não há nova execução neural, campanha de performance ou prioridade científica
estabelecida. Transporte mínimo e junção em árvores são antecedentes clássicos.

## Operação e hipóteses

Um head congelado fornece distribuições finitas `p_i` para posições escolhidas
antes dos sorteios. A primeira política amostra independentemente; B1 usa
transportes mínimos nas arestas de uma floresta, preservando cada marginal.
Para uma aresta, escreva suas marginais `p,q` e seu transporte `J`.

Os valores nesta nota são classes semânticas declaradas, como rótulos de uma
classificação. IDs que representam a mesma classe são agregados para o custo
e devolvidos pela condicional interna. A garantia de cobertura abaixo exige
penalizar a igualdade de todas as classes pertinentes; uma cauda livre não
recebe essa garantia. Valores de vários tokens precisam de uma distribuição
sobre valores completos: não são obtidos gratuitamente de um head por token.

Inicialmente, considerar duas posições de rótulos com comprimento fixo,
EOS ausente e combinações sintaticamente válidas. Não aplicar seleção,
truncamento ou rejeição posteriores sem analisar sua nova lei. O objetivo
verdadeiro é fixo e não depende dos sorteios do algoritmo.

## Teorema 1: qualidade aditiva com custo real de colisão

Suponha que a utilidade efetivamente consumida seja

`U(x) = Σ_i u_i(x_i) − Σ_(i,j) λ_ij 1[x_i=x_j∈S]`,

com `λ_ij ≥ 0`, funções fixas `u_i` e arestas formando uma floresta. Um uso
admissível é selecionar recursos/opções em paralelo: cada escolha tem valor
próprio e uma coincidência proibida gera uma penalidade conhecida, como uma
taxa fixa de contenção. Esse é um contrato de operação, não um modelo universal
de qualidade linguística. A necessidade de preservar marginais deve vir do
consumidor, por exemplo probabilidades de inclusão anunciadas.

**Prova.** Como as marginais são iguais, a esperança de `Σ_i u_i(x_i)` é
igual sob B1 e independência, quaisquer que sejam os valores desconhecidos
de `u_i`. A independência tem custo de colisão por aresta
`d_ij = Σ_(c∈S) p_i(c)p_j(c)`. O menor custo possível é
`δ_ij = max(0, max_(c∈S)(p_i(c)+p_j(c)−1))`, atingido pelo transporte de B1.
A junção em uma floresta atinge esses limites em todas as arestas. Portanto

`E_B1[U] − E_IID[U] = Σ_(i,j) λ_ij (d_ij−δ_ij) ≥ 0`.

Também é ótimo entre todos os acoplamentos dessas mesmas marginais para essa
utilidade. A melhoria é estrita quando alguma aresta tem `λ_ij>0` e
`d_ij>δ_ij`. Distribuições determinísticas ou uma única posição não oferecem
essa oportunidade. Penalizar uma repetição legítima viola a hipótese de que
ela representa um custo do consumidor.

**Custo completo.** Seja `h` o aumento esperado dos custos de preparação,
amostragem, RNG, transferência, memória e entrega, convertido nas mesmas
unidades de utilidade. A vantagem líquida exige
`Σ λ_ij(d_ij−δ_ij) > h`. O algoritmo não faz forwards adicionais quando o
head já foi calculado, mas `h` ainda não foi medido. Não decorre daqui uma
aceleração nem economia de chamadas frente a um baseline que também reutiliza
o head nos descartes.

## Teorema 2: cobertura ótima de duas alternativas de classificação

Agora há **um único rótulo correto** `c`, e o consumidor recebe duas
alternativas completas `X,Y`. O sucesso significa `c∈{X,Y}`. Essa é uma
medida de acerto, e não apenas a contagem de repetições. Não é acerto top-1.

Qualquer acoplamento com marginais `p,q` satisfaz

`Pr(c∈{X,Y}) = p_c+q_c−J_cc ≤ min(1,p_c+q_c)`.

O transporte mínimo tem `J_cc=(p_c+q_c−1)_+` simultaneamente para todos os
rótulos. Logo B1 atinge o limite superior para **cada possível rótulo correto**:

`Pr_B1(c∈{X,Y}) = min(1,p_c+q_c)`.

Dois sorteios independentes têm cobertura `p_c+q_c−p_c q_c`. A vantagem é

`G_c = p_c q_c−(p_c+q_c−1)_+`
`    = min(p_c q_c, (1−p_c)(1−q_c)) ≥ 0`.

**Prova.** Inclusão-exclusão fornece a primeira identidade. A massa da
diagonal é pelo menos `max(0,p_c+q_c−1)` por Fréchet. O transporte mínimo
atinge todos esses limites: no máximo um pode ser positivo e a soma de suas
diagonais já atinge o mínimo. Substituir essa massa na identidade de cobertura
prova a fórmula. As duas expressões de `G_c` resultam de separar os casos
`p_c+q_c≤1` e `p_c+q_c≥1`. Não é necessário conhecer o rótulo correto para
construir o transporte. Para qualquer distribuição real `r` de rótulos,
a vantagem média é `Σ_c r_c G_c ≥ 0`, sem pressupor calibração de `p,q`.

**Exemplo construído.** Três rótulos equiprováveis A/B/C em ambas as posições.
IID fornece cobertura `5/9` para qualquer rótulo correto. Escolher os pares
AB, BC e CA com probabilidade `1/3` mantém cada marginal uniforme e fornece
`2/3`. A diferença é `1/9`, aproximadamente 11,1 pontos percentuais. Esses
valores são deduções do exemplo, não resultados de uma dLLM.

**Uso delimitado.** Um classificador pode oferecer duas ações ou categorias
candidatas para revisão humana ou verificação automática. O recurso é geral
entre domínios, mas limitado a alternativas categóricas. Não demonstra melhora
de respostas longas, raciocínio, geração de código ou classificação top-1.

## Controles que limitam a relevância da prova

Preservar as duas marginais é uma restrição importante. Se o consumidor só
quer duas melhores hipóteses, a restrição pode ser desnecessária. Para
`p=q=r=(3/5,3/10,1/10)`, as coberturas são:

| Política | Rótulo A | Rótulo B | Rótulo C | Cobertura média sob verdade r=p |
| --- | --- | --- | --- | --- |
| IID | 21/25 | 51/100 | 19/100 | 169/250 = 0,676 |
| B1 | 1 | 3/5 | 1/5 | 4/5 = 0,8 |
| Sem reposição, primeiro sorteio p | 97/105 | 47/60 | 41/140 | 573/700 ≈ 0,8186 |
| Dois rótulos mais prováveis | 1 | 1 | 0 | 9/10 = 0,9 |

Os últimos controles não preservam ambas as marginais, mas são admissíveis
quando essa exigência não existe. Se `r=p`, selecionar os dois maiores `p_c`
é ótimo para cobertura média entre conjuntos de tamanho no máximo dois:
qualquer conjunto `A` tem sucesso `Σ_(c∈A) p_c`, maximizado pelos dois maiores.
Randomizar conjuntos não supera esse máximo. A vantagem de B1 contra IID
não prova vantagem contra esses controles.

Além disso, um LLM autorregressivo também pode aplicar o mesmo transporte a
distribuições de rótulos. Se ambas as marginais forem cópias do mesmo head,
uma única leitura de logits já basta nos dois tipos de modelo. O teorema não
estabelece uma vantagem específica de dLLMs ou um resultado matemático novo.

## Contraexemplos a ampliações indevidas

- **Decisão única:** a probabilidade de acertar com a primeira alternativa
  continua `p_c`. Preservar a marginal impede melhorar esse acerto top-1.
- **Texto com dependência conjunta:** se as únicas respostas corretas forem
  AA e BB, com marginais uniformes, IID acerta com probabilidade `1/2`.
  A anticorrelação AB/BA acerta zero. A redução de repetição pode piorar tudo.
- **Mais de um rótulo aceitável:** marginais uniformes em A/B/C/D e pares
  AB, BA, CD, DC equiprováveis têm colisão zero. Se A e B são ambos aceitáveis,
  B1 tem sucesso `1/2`, abaixo de `3/4` do IID. O teorema 2 exige um rótulo.
- **Mais de duas alternativas:** repetir o transporte anterior num caminho
  de quatro posições produz ABAB, BABA, CDCD ou DCDC. Para um rótulo correto
  fixo, a cobertura é `1/2`; quatro sorteios IID dão `175/256`. A soma de
  colisões adjacentes é ótima e a cobertura global é pior. Escolher outro
  transporte pode mudar isso; a garantia local não escolhe nem prova essa
  melhoria global.

## Evidência e decisão

A prova é escrita, não uma especificação Lean. Oráculos não estabelecem
prioridade ou benefício medido em modelos. Um único subagente independente
de revisão concluiu a auditoria e confirmou os dois teoremas, os controles
e as limitações. É revisão por IA, não revisão humana ou acadêmica.

Reprodução do oráculo adicional, sem alterar o oráculo congelado original:

```bash
python3 attempts/82-five-operator-screening/b1_utility_oracle.py
```

Resultado: 2.347 verificações exatas de cobertura por rótulo para marginais
em grades de dois a quatro valores, sem divergências; a enumeração direta de
uma floresta de três posições confirmou ganho aditivo de `177/100` no exemplo
construído. Os resultados de IID/B1/WOR/top-2 e os três contraexemplos foram
reproduzidos com racionais. Não são medições de um modelo.

O acesso a leituras categóricas é um consumidor tecnicamente plausível:
[dJev](https://github.com/mmastrac/djev) já oferece decisões por logits e
espaços de rótulos de um token. Isso demonstra uma interface disponível,
sem estabelecer necessidade de preservar as marginais nem novidade de B1.

O revisor fez uma enumeração independente de 495 tabelas inteiras, cobrindo
225 pares de marginais: 1.800 objetivos e 675 verificações de cobertura
passaram; 3.375 cadeias racionais confirmaram T1. Esses conjuntos se
sobrepõem aos outros e não devem ser somados como casos independentes.
Ele confirmou também que três alternativas podem perder cobertura mesmo
com todas as colisões adjacentes minimizadas: ABA, BCB e CAC equiprováveis
cobrem cada classe com `2/3`, abaixo de `19/27` do IID.

**Decisão após a auditoria:** há utilidade demonstrável sob contrato restrito
e potencial como operador probabilístico. A recomendação inicial de priorizar
B1 para uma campanha fica suspensa. A necessidade real de manter marginais
não foi estabelecida para um consumidor dLLM; controles simples podem vencer
quando ela não existe. O mesmo teorema aplica-se a logits de um modelo AR.
Não selecionar B1 como contribuição central do TCC nesta forma nem presumir
vantagem de decoder a partir desses teoremas. A meta científica segue aberta.
