# Protocolo A73 V1 — congelar fonte antes dos timings

Não alterar casos, ordem, seeds, métricas ou gates após observar dados.
Comando produtor e hash Git serão registrados no relatório, sem editar este
protocolo. Preparação offline já permitida não continha timings ou dados neurais.

## Entrada e operação

Modelo local absoluto `/home/jota/projects/tcc-final/.cache/a52-model-metadata`,
`dllm-hub/Qwen3-0.6B-diffusion-mdlm-v0.1`, revisão
`c8d24a3f4adaeef46881b450e1bf7d1005203bd7`. Pesos SHA256 esperado
`3485d18016ce6c302e8973809b47aa6369d6612ef9978d0690b4575d1193e932`;
tokenizer SHA256 `6d55810de1daf81d1d1259355b4b85810385022ab745be68029295935a4eacf0`.
Não baixar nem treinar. Ambiente em leitura `.venv-a52` do checkout principal;
`PYTHONDONTWRITEBYTECODE=1`, HF offline. Código do modelo importado diretamente
do arquivo local, sem mudar vendor ou pacotes instalados. Backend SDPA, modelo
BF16 eval, cache desligado, TF32 desligado, quatro threads Torch, seed 730019.

D contém TODOS os IDs BPE ordinários cujo byte string casa
`[A-Za-z_][A-Za-z0-9_]*`. Revalidar ausência de aliases e tokens especiais.
Sentinela `#`, separador `,` e máscara original 151669. Cada campo usa um slot
de token inteiro; o canvas tem campos mascarados intercalados por vírgulas
fixadas. Prompt é prefixo fixo e não é parte do MAP. EOS/PAD não são gerados.
As confidências originais são dispensadas porque todos os campos são
comprometidos ao retornar UMA proposta conjunta.

Seis casos, nesta ordem, sem seleção pelo score ou resultado:

1. `copy4-p0`: 4 campos iguais em ID, prompt 0.
2. `copy16-p0`: 16 campos iguais em ID, prompt 0.
3. `copy32-p1`: 32 campos iguais em ID, prompt 1.
4. `independent4-p0`: 4 campos independentes em D, prompt 0.
5. `independent16-p1`: 16 campos independentes em D, prompt 1.
6. `balance4-p1`: 4 campos em {#,v}, v∈D, indicador de v satisfaz
   x0+x1=x2+x3; todos os campos ativos têm o mesmo ID v. Inclui #### uma vez.
   São 1+5|D| palavras, seis padrões binários, nenhuma igualdade global de slots.

Prompt 0: `Fill the comma-separated fields with a valid identifier. Repeated fields must agree.\nFields: `

Prompt 1: `Complete this identifier record using short names. Respect the declared joint constraints.\nRecord: `

Os prompts são casos de desenvolvimento construídos, não benchmark externo ou
evidência de qualidade. Balance é um consumidor sintético de contagem de eventos,
não alegação de gramática natural frequente. Slots/bytes fixados são verificados
na saída. A tarefa fica restrita a tokens inteiros; não suporta identificadores
multi-token arbitrários. Não há alegação de ganho de geração iterativa.

## Métodos

- `dense`: H_livre @ W_completo^T FP32, selecionar D depois; resolver MAP com
  max/sum vetorizados adequados à família. Slots fixos não calculam head.
- `sparse`: gather de W_D FP32 no setup; GEMM H_livre @ W_D^T; mesmo solver.
- `manual`: copy usa sum(H) antes do head, equivalente a flattening antecipado;
  independent/balance não têm igualdade global de slots e usam sparse. É um
  controle especializado competente, não o runtime original de FactorDLM.
- `a73`: forest explícito sem enumerar palavras independentes, compilador
  racional, agrupamento B, GEMM (B H) @ W_grupo^T e solver sobre pivôs.

Todos usam o MESMO backbone BF16 e FP32 para o head; a prova ideal refere-se
aos valores representados de H/W, não a identidade binária de GEMMs. Aliases
não ocorrem em D; caso adversarial fora de D permanece nos oráculos.
Empates exatos recebem desempate por IDs lexicográficos; se a certificação
numérica não separar o vencedor, resultado é inconclusivo, nunca OPTIMAL.

## Validação numérica

Capturar uma H real por caso; salvar seus valores e hashes para replay offline.
Referência independente: projeção legal FP64 não contraída, solver vetorizado
de todas as palavras/padrões (independent por posição). Usar margem contra o
segundo melhor e limite conservador de erro de produto escalar/soma em FP64:
E=16 eps64 d n max_v|W_v| Σ_{i,j}|H_ij|. Sob o modelo padrão de arredondamento
FP64, cada escore representado fica a menos de E do ideal; exigir gap>2E.
Para independent, certificar cada argmax por posição. Se gap não separar,
registrar inconclusivo sem trocar dtype/tarefa/seeds para salvar o gate.
Esse certificado é condicional à aritmética FP64 padrão, não intervalo com
arredondamento dirigido nem validação formal de CUDA. Cada proposta FP32
deve coincidir com o MAP certificado; cada H repetida deve coincidir com a
captura. Se houver divergência, registrar erro e falhar o gate.

## Custos, execução e gates

Lock exclusivo obrigatório `/tmp/tcc-final-candidate-tests-gpu.lock` para
TODOS os timings e GPU. `nvidia-smi` antes de carregar: nenhum processo compute
alheio e utilização <=5%; caso contrário recusar recurso sem refutar o método.
Não matar processos. Lock não cooperativo externo implica interrupção.

Cronometrar startup/imports/hash/tokenizer/modelo separadamente, com RSS e pico
CUDA; preparação por método inclui gerar/admitir o forest, anchors, redução,
grouping, transferência B e gather/conversão W. Não oferecer plano A73 pronto
de graça. Medir uma primeira chamada por método, e depois cinco rotações
pareadas; ordem circular dos quatro métodos deslocada por índice do caso e
repetição. Cada chamada faz NOVO backbone, head, solve, D2H, validação dos IDs/
bytes/posições e serialização. Sincronização CUDA antes/depois. Relatar CPU e
wall integral e componentes backbone/fronteira; pico GPU absoluto e incremental,
RSS e tamanho tensor. RNG online=0, parser=solver especializado (sem custo CFG
escondido); output incluído. Custo do oráculo FP64 é separado e explicitado.

Gate por caso: todas as chamadas válidas/certificadas, e mediana A73 <=80%
da mediana de CADA controle, em wall **e CPU**, com setup por consulta Q=1 e
Q=32. Startup compartilhado é apresentado tanto à parte quanto amortizado
nesses totais. Não tratar 32 repetições do mesmo estado como trajetória real:
Q=32 é cenário de amortização, sem medir 32 forwards adicionais para isso.
Relatar também fronteira quente e sem startup; não substituem gate integral.
Conclusão útil/publicável precisa além disso de relevância e distinção própria;
um ganho sobre dense sem ganho sobre manual não passa.

Limites: seis casos, cinco rotações + uma primeira chamada por método/caso;
uma captura/certificação por caso. Máximo 150 novos backbones, 2 milhões de nós
por forest, 120 s de preparação por caso, 1200 s no processo, 12 GB GPU.
Limites cooperativos; não prometer teto de memória do SO. Cada registro é
gravado/flush em JSONL; preservar erro, recusa e interrupção. Não repetir a
campanha por ruído, não expandir casos após perdas e não disparar confirmação
independente se o gate falhar. Correção de bug exige addendum separado com a
causa; não sobrescrever registros existentes.
