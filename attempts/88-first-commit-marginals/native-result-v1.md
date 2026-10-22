# A88 V1 — resultado do qualificador delimitado

2026-10-22. **Captura concluída; sinal de desenvolvimento positivo no replay;
qualificação operacional INCONCLUSIVA. Tema central ainda não validado.**

As duas regras adaptativas pré-registradas atingiram o gate pontual modelado:
>=10% de redução de variância × custo previsto frente aos DOIS controles em
6/8 itens. O requisito de massa A–D foi atendido em 8/8 itens. Dois itens têm
variância empírica numericamente degenerada: são inconclusivos, não vitórias
nem ganhos infinitos. O protocolo exige seis itens; nenhum foi substituído.

A regra **integrar até a primeira W<=0,01 e então usar o readout exato de
primeiro compromisso na cauda** fica selecionada e congelada apenas como
escolha de desenvolvimento para um futuro protocolo independente. Ela teve
menor produto previsto que W<=0,0001 em todos os seis itens não degenerados.
A seleção usa estes mesmos dados e não é validação independente. Nenhum novo
teste neural, ajuste de casos ou nova versão do sampler foi executado.

O custo não foi qualificado ponta a ponta. O executor mede a trajetória
auxiliar; os custos dos demais métodos são previstos por replay condicional,
com cache global otimista e kernels por visita. O intervalo pareado contra o
controle mais forte ainda inclui perda no caso 150. Preparação/carregamento
representam grande parte do orçamento fixo N=8; não há conclusão de ganho em
regime contínuo, acurácia semântica, prioridade mundial ou candidatura acadêmica.

## Proveniência e execução única

- Fonte produtora congelada ANTES do primeiro forward:
  `aa8ec805c81f40247536da55d7480882f270c8f6`.
- Prova/oráculo/protocolo anteriores preservados: `6452120e`, `6985bf05`,
  `ab8f2921`; nenhuma dessas fontes ou notas foi reescrita.
- MMLU `cais/mmlu`, revisão `c30699e8356da336a370243923dbaf21066bb9fe`,
  arquivo `all/dev-00000-of-00001.parquet`, 285 linhas. Casos selecionados por
  SHA: 150, 209, 47, 12, 85, 279, 183, 224. Texto, alternativas e gold preservados.
- Checkpoint local GSAI-ML/LLaDA-8B-Instruct
  `08b83a6feb34df1a6011b80c3c00c7563e963b07`: 14 arquivos,
  16.037.448.436 bytes, todos com SHA256 no manifesto de entradas; sem treino.
- NF4 double/BF16, batch 1, quatro threads, sem KV, crop da cabeça de saída.
  O canvas tem 31 MASKs de raciocínio, delimitador fixo, um MASK observado e
  EOT fixo; 32 posições elegíveis, k=2, 16 passos. EOS/PAD são tokens comuns.
- Oito réplicas independentes por item, seeds `880001+1000*caso+replica`.
  Stream independente do slot observado: seed+1000000000. Seu registro é só
  o primeiro hit acoplado; a continuação auxiliar não é uma saída nativa completa.
- T=1, supressão compartilhada de MASK, softmax float64 dos logits BF16,
  todos os 126.464 IDs. A partição preserva 12 aliases A–D, inclusive NBSP,
  e OUTSIDE. Não houve renormalização para opções. Esta política difere do
  MASK handling upstream e não reproduz o experimento publicado 280+1/T≈0.
- **968 forwards novos, 1.024 passos lógicos, 64 réplicas, oito itens**.
  Status `COMPLETE`; zero recusas, erros, interrupções, retries ou trocas de linha.
  Limites pré-registrados: 968 chamadas e 30 minutos cooperativos.


Captura: 264.299984 s; análise offline: 93.075382 s. O cache físico guardou apenas raízes, em GPU, uma por item. Foram observados 825 estados distintos, 817 não-raiz: o controle de cache global é material para esta comparação.


## Todos os métodos e itens

Produto: estimativa do traço de covariância × custo médio previsto para N=8,
com preparação/carga amortizadas, raiz uma vez por item e cache global
condicional otimista. As células seguintes são a vantagem percentual contra
o readout selection-aware d=0, o controle mais forte neste conjunto. A
análise JSON também preserva a comparação com contagens MC para todos os
métodos e os cinco bins completos. “inc.” = momento degenerado/inconclusivo.


| Linha MMLU | d=1 | d=2 | d=4 | d=8 | full | W≤.01 | W≤.0001 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 150 | 15.31% | 14.52% | 20.89% | 7.22% | -14.66% | 15.39% | 12.04% |
| 209 | -0.01% | -0.01% | 46.33% | 43.21% | 34.22% | 45.63% | 44.99% |
| 47 | 86.60% | 86.40% | 87.20% | 98.02% | 97.71% | 98.09% | 98.05% |
| 12 | 22.01% | 37.29% | 61.72% | 63.19% | 68.02% | 72.60% | 71.68% |
| 85 | 11.57% | 30.57% | 30.56% | 29.72% | 20.50% | 24.70% | 23.53% |
| 279 | -0.01% | 7.24% | 7.22% | 33.81% | 23.17% | 32.06% | 31.05% |
| 183 | inc. | inc. | inc. | inc. | inc. | inc. | inc. |
| 224 | inc. | inc. | inc. | inc. | inc. | inc. | inc. |
| Itens ≥10% contra ambos | 4/8 | 4/8 | 5/8 | 5/8 | 5/8 | 6/8 | 6/8 |

A família inteira era pré-registrada; o endpoint full não precisa vencer suas
parciais. Não selecionar um subconjunto de itens para converter o gate de
uma variante em outro. d=0 permanece controle, não contribuição própria.

Para a escolha de desenvolvimento W≤.01, os intervalos de 95% são percentis
exploratórios de 2.000 reamostragens pareadas de RÉPLICAS INTEIRAS, seed
888801. Não são intervalos corrigidos por multiplicidade nem evidência
confirmatória. O caso 209 tem 61 reamostras degeneradas excluídas do cálculo
do quociente (1.939 válidas), explicitamente registradas; os dois casos
com variância empírica degenerada têm zero quocientes válidos.


| Linha | Vantagem MC | Vantagem d=0 | IC exploratório d=0 | Massa A–D |
|---|---:|---:|---|---:|
| 150 | 72.09% | 15.39% | [-2.18%, 71.95%] | 1.000000000000 |
| 209 | 53.29% | 45.63% | [24.94%, 65.80%] | 1.000000000000 |
| 47 | 99.61% | 98.09% | [97.99%, 99.64%] | 0.999999999968 |
| 12 | 89.00% | 72.60% | [57.50%, 87.78%] | 0.999999999997 |
| 85 | 67.19% | 24.70% | [9.38%, 59.16%] | 0.999999997075 |
| 279 | 78.20% | 32.06% | [13.57%, 66.09%] | 1.000000000000 |
| 183 | inc. | inc. | inc. | 1.000000000000 |
| 224 | inc. | inc. | inc. | 1.000000000000 |

O estimador de variância soma variância amostral de Y e média das variâncias
condicionais não negativas. Não usa variância empírica de oito hits raros.
Os momentos condicionais incluem todos os tempos de compromisso. O produto
não linear com cache global é exploratório. O comparador com cache só na
raiz também registra o U-estatístico com terceira réplica distinta, evitando
multiplicar ingenuamente estimativas correlacionadas; ambas as regras
adaptativas tiveram vantagem pontual material em 6/8 nesse comparador.
Nenhuma garantia por segundo decorre apenas do teorema de covariância.

## Auditoria de custo, memória e números


| Parcela real da execução | Segundos |
|---|---:|
| Preparação de entradas/tokenizer/hashes, antes da captura | 49.607845 |
| Reconfirmação de hashes na captura | 52.895168 |
| Carregamento do modelo | 97.019532 |
| Forwards, novas chamadas apenas | 89.423446 |
| Preparação categórica/CDF, novas chamadas apenas | 2.392178 |
| Demais perfis, incluindo diagnósticos e serializações de sonda | 1.231464 |
| Escrita da captura JSONL | 0.309492 |
| Residual não atribuído a métodos pelo replay congelado | 21.028703 |
| Captura total, sem a preparação prévia | 264.299984 |

Preparação + reconfirmação + carga = 199.522546 s, ou
3.117540 s por réplica no orçamento de 8×8. Cada método
paga a raiz uma vez, não oito vezes. Os controles pagam decisões por proposta
e só reduzem a5 no hit; MC não paga a5. A candidata paga reduções durante a
integração. qf5 diagnóstico, stream observado durante integração, bootstrap
e saída do trace são sobrecarga da pesquisa, não latência de produto.

**O residual de 21.03 s contém trabalho fora dos cronômetros de
kernel, como inicialização/imports, guardas de recurso, despacho e
bookkeeping. Ele não foi distribuído por método pelo analisador congelado.**
Não atribuo retroativamente esse tempo para salvar ou ampliar o resultado.
As políticas de cache e a serialização final são modelos de custo, não
execuções completas dos controles. Portanto o gate de CUSTO INTEGRAL permanece
**INCONCLUSIVO**; o resultado positivo é do screen modelado de desenvolvimento.
O tempo real de 264,30 s é da captura auxiliar, não uma aceleração de decoder.

Picos: GPU alocada 5907240448 bytes
(5.502 GiB), reservada
5949620224 bytes (5.541 GiB),
RSS host 3868991488 bytes
(3.603 GiB). Compatível com a 3080 Ti de
12 GB nesta execução. Nenhuma cabeça completa foi acumulada em RAM.
q/CDF de uma raiz de 32 posições usam 64.749.568 bytes em float64. IDs
originais precisam de 17 bits nominais e são transportados em tensores int64;
cada vetor de cinco probabilidades tem 320 bits de valores float64, além
do formato JSON. Logits são BF16, probabilidades/CDF são float64 e pesos
usam NF4 double; isso não é aritmética racional exata de custo ilimitado.

Maior erro observado de soma de q: 2,665e-15; endpoint CDF: 5,552e-15.
Zero probabilidades clean zeradas, zero empates de cutoff e zero clamps de b.
RNG/CDF/comparações/reduções flutuantes não estabelecem lei CUDA bit-exact.
Não houve cauda descartada ou renormalização das opções. O oráculo racional
anterior é a evidência exata separada: 11 casos, 904 folhas nativas,
53 auxiliares e duas recusas de contrato, já registrados antes desta execução.

O auditor reconstruiu todos os canvases por IDs originais, conferiu hashes,
slots fixados, seeds, simplex, mass/W, primeiro hit e sandwich das variâncias.
Uma conferência independente por segundos momentos E||Z||²−||Y||² diferiu
no máximo 6,662e-16 nos 64 caminhos e todas as parciais. Isso é teste
numérico, não prova de prioridade científica ou verificação Lean do software.


## Arquivos e reprodução

- [Entradas e todos os hashes de checkpoint/tokenizer](native-inputs-v1.json).
- [Captura científica completa, 326.333 bytes comprimidos](native-capture-v1.jsonl.gz).
- [Análise de todos os casos/variantes e intervalos](native-analysis-v1.json).
- [Console original da única captura](native-capture-v1.console.txt).
- [Detalhes do executor congelado](implementation-v1.md).

SHA256:


- entradas: `fe163cb34d5def117011bfb415e3a8fd42374fc199c1768f94ff50722006a68a`.

- dataset parquet: `2b19bde1ed8ca6b482fb283abc90e8e0d9d228947029c0b91795d64b28b3bc3f`.

- captura JSONL original: `25f6c71aa6ee69b39f3de4d9ba208cf1af09ce3bfb1958989b3032526b8e3ec2`.

- captura gzip: `7ae3e6440deb3f3193cddc511bc3ce0d3ea290514267d792a3315b1ec4851a26`.

- análise JSON: `46bced5b4aa3ce6e93e25426370e9dee313abceec8ffabda46e679ff1cf9eb0b`.


Comandos exatos executados na raiz, em ordem. O commit aa8ec805 foi feito
entre os testes e a captura; nenhuma outra captura A88 foi executada.

```bash
.venv-live/bin/python attempts/88-first-commit-marginals/native_v1.py --prepare
.venv-live/bin/python attempts/88-first-commit-marginals/test_native_v1.py
.venv-live/bin/python attempts/88-first-commit-marginals/test_native_v1.py Checks.test_cdf_zero_plateaus_and_boundaries Checks.test_ties_both_physical_orders Checks.test_partial_moments_independent_hit_enumeration Checks.test_cost_product_distinct_replicas Checks.test_global_cache_independent_visits
.venv/bin/ruff check attempts/88-first-commit-marginals/native_v1.py attempts/88-first-commit-marginals/analyze_v1.py attempts/88-first-commit-marginals/test_native_v1.py
.venv-live/bin/python -u attempts/88-first-commit-marginals/native_v1.py --capture --output artifacts/a88-native-v1.jsonl > artifacts/a88-native-v1.console.log 2>&1
.venv-live/bin/python attempts/88-first-commit-marginals/analyze_v1.py artifacts/a88-native-v1.jsonl --output artifacts/a88-analysis-v1.json > artifacts/a88-analysis-v1.console.log 2>&1
```

Para reproduzir apenas a análise, sem GPU/modelo e sem repetir a captura:

```bash
.venv-live/bin/python attempts/88-first-commit-marginals/analyze_v1.py attempts/88-first-commit-marginals/native-capture-v1.jsonl.gz --output artifacts/a88-analysis-reproduced-v1.json
```

O arquivo de saída é exclusivo: use um novo nome se já existir. A análise
salva foi produzida do JSONL original; a reprodução do gzip terá o hash do
gzip em capture_sha256 e o mesmo hash original em uncompressed_capture_sha256.
O tempo de análise também varia. Esses campos de proveniência não alteram
os momentos/intervalos científicos. A preparação completa verifica novamente
16 GB de fontes; não executá-la só para reproduzir os resultados offline.

## Decisão e limite da próxima etapa

Esta V1 está encerrada como execução delimitada. A88 ganhou evidência neural
concreta para a capacidade de estimar a marginal do sampler, com redução de
variância contra o readout correto. O gate pontual modelado passou, mas custo
operacional integral, generalidade e novidade específica seguem abertos.
Implicit capture/CMC, sobrevivência, marginalização de propostas e soft votes
são antecedentes conhecidos; a hipótese própria continua sendo a exploração
da coalescência pós-seleção top-k com cabeças que mudam ao longo do canvas.

O próximo trabalho justificável é um protocolo INDEPENDENTE que congele a
regra W≤.01, casos novos e um consumidor que necessite essa marginal, com
latência ponta a ponta e amortização de preparo especificada. Isso ainda
precisa da auditoria de prioridade adequada. Não é autorizado inferir deste
qualificador um tema central validado, melhoria de acurácia, teste independente
já realizado ou promessa de aprovação. A65/A87 e as aplicações negativas
encerradas não foram reabertas; dados locais A71 e documentos alheios ficaram
intactos. Nenhum contato, submissão ou publicação foi realizado.
