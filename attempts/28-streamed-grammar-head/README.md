# Tentativa 28 — Cabeça de modelo com estatísticas gramaticais em fluxo

Início2026-10-11, base `303cff72d6e49e8b1dab29ea3ea84c79f4780646`.
Direção isolada. **Novidade suficiente e desempenho ainda não confirmados.**

## Oito perguntas antes da implementação

1. **Uso:** amostrar um preenchimento JSON conjunto da predição de uma dLLM,
   condicionado à gramática, sem guardar todos os pesos por posição/token.
   A saída continua sendo IDs originais, com strings/números escolhidos pelo
   modelo. O novo objeto é a fronteira entre a cabeça neural e o parser;
   não outro modelo de regras nem uma alteração semântica de JSON.
2. **Significância:** FlashSampling já funde projeção/amostragem e fatoriza
   categorias por grupos; GSP/STATIC já evitam projeções desnecessárias.
   Portanto, nenhum desses princípios é nosso. A diferença candidata é um
   resumo amostrável consumido por inferência CONJUNTA sob CFG, incluindo os
   IDs originais, sem usar rejeição independente da sequência. Só a composição
   algébrica não basta: precisa de uma execução útil e vantagem frente a um
   controle que também processe a cabeça em blocos. Publicação não garantida.
3. **Escolha:** buscar redução da memória temporária da cabeça de O(nV) para
   O(nC), quando C classes de efeitos gramaticais são muito menores que V.
   O lexer completo atual tem194 classes/50258 IDs, contagem anterior ao novo
   protótipo. Isto não prova tempo menor. Comparadores: cabeça densa + mesmo
   parser, cabeça em blocos + mesmo parser e FlashSampling + rejeição quando
   viável. EPIC também deve receber otimizações comuns da cabeça; não é
   derrotado por não retornar o nosso posterior.
4. **Matemática:** provar suficiência das massas por classe e sorteios
   internos independentes para uma ÚNICA amostra original, condicionada ao
   evento que depende das classes; mostrar lei completa e custo em bits.
   As classes devem preservar o comportamento em todos os estados relevantes,
   não apenas a grafia ou um token representativo. Disintegração e reservatório
   ponderado são conhecidos; localizar uma consequência operacional adicional.
5. **Experimentos:** começar por um oráculo pequeno da lei completa e pela
   invariância das classes com `json.loads`, incluindo aliases, macro-tokens,
   strings parciais, posições fixas e massa zero. Nenhuma escolha de corpus,
   timing ou forward novo nesta fase. Só depois congelar comparação GPU com
   controle em blocos e custos de ordenação, acumulação e parser incluídos.
6. **Custo:** pagar classificação/preparação, backbone, TODA a projeção que
   continuar necessária, agregação, RNG, transferências e parsing. Pesos
   inteiros/racionais são o contrato da referência; fusão flutuante precisa
   declarar sua lei numérica e não pode alegar identidade bit a bit por
   analogia com uma prova em reais. Marginais originais explícitas exigem
   saída O(nV); esta interface promete uma amostra, não essa saída.
7. **Objeção:** um simples streaming em blocos pode obter a mesma memória.
   FlashSampling agrupado já fornece parte do resumo; fusão por si só não é
   invenção. C pode se aproximar de V, o custo de RNG/acumulação exata pode
   dominar e o parser pode dominar o ciclo. Um resumo com sorteios internos
   NÃO pode ser reutilizado em amostras iid ou adaptado depois de observar
   esses sorteios. Rejeitar esse uso explicitamente.
8. **Artigo:** faltam diferença específica conferida, implementação neural
   real, custo competitivo contra streaming forte e reprodução independente.
   A prova de suficiência não resolve novidade. Preservar perdas e não mudar
   a lei, a tarefa ou o baseline para conseguir uma vitória.

## Escopo do primeiro protótipo

Interface de pesos não negativos inteiros entregues em fluxo; uma amostra
por resumo. A compilação estrutural usa cópias imutáveis do lexer/controle
clássico e não recebe o gabarito. EOS ausente, suporte original inteiro,
zeros e IDs fixos preservados. Sem kernel GPU, velocidade ou prioridade
confirmados nesta versão. Prova em `work/theory-v1.md`, antecedentes em
`work/antecedents-v1.md`.

Depois dos oráculos, o primeiro replay declarado usará o MESMO pacote público
completo de A24, com TODOS50258 IDs. Recalculará massa válida com a referência
completa, fará oito resumos novos/oito amostras independentes, verificará JSON
com `json.loads` e IDs fixos. Todos os resultados serão publicados. Não é
captura independente, timing competitivo ou medida de memória do ciclo neural:
o arquivo de entrada já contém probabilidades materializadas.

## Resultado v1, fonte congelada antes do replay

Fonte `5ebb2ec2eb07a395ac4f4a3ec61bcd2b8b55d5ae`; comando:

```bash
.venv/bin/python -m attempts.28-streamed-grammar-head.work.replay_v1 --packet attempts/24-certified-depth-approximation/work/evidence/first-full-head-v2/packet.zip --output attempts/28-streamed-grammar-head/work/evidence/public-head-v1.json
```

Oito resumos novos produziram oito JSONs válidos, com IDs fixos preservados.
Todas29.488 probabilidades de classes conferem exatamente com a referência
completa; a massa válida também confere, aproximadamente3,14645e-6. Todos os
IDs/probabilidades originais foram considerados, incluindo aliases e zeros.
Nenhum forward novo, medição neural de memória/tempo ou confirmação de
novidade. Os101 testes passam; os controles conhecidos ainda precisam receber
a mesma fronteira eficiente antes de qualquer conclusão competitiva.

## V2 em validação: comunicação de massas binary64 exatas

O addendum `work/gpu-boundary-v2.md` responde aos oito critérios novamente
antes da implementação. Preserva o head denso na GPU e a lei de seus pesos
representados; a hipótese é economia de comunicação/conversão, não de pico
de memória GPU. Controles NumPy e PyTorch somam dígitos inteiros de forma
vetorizada e recebem o mesmo parser e recuperação por blocos. Neal/ExBLAS
são antecedentes da soma; o princípio não é reivindicado como novo.

Dois oráculos CPU de soma e a lei completa de recuperação por blocos passam.
Antes de timing, o comando GPU abaixo executará todos os40 pares positivos
predefinidos e12 recusas de números inválidos/massa zero, comparando cada
bloco com `Fraction` independente. O produtor será congelado antes da execução;
falhas também terão arquivo próprio preservado.

```bash
.venv-live/bin/python -m attempts.28-streamed-grammar-head.work.check_gpu_v2 --output attempts/28-streamed-grammar-head/work/evidence/gpu-correctness-v2.json
```

Resultado: produtor564e68b,52/52 verificações concluídas (40 positivas/12
recusas),39924 somas de blocos conferidas com Fraction. A suíte inteira tem104
testes e passou39,501s. Não há velocidade ou prioridade de publicação obtida.

Próximo replay declarado: os MESMOS pesos públicos serão copiados à GPU,
sem mudar seus bits. NumPy/Triton/PyTorch terão oito amostras por método,
com todas as probabilidades por classe e massa válida conferidas novamente:

```bash
.venv-live/bin/python -m attempts.28-streamed-grammar-head.work.replay_blocks_v2 --packet attempts/24-certified-depth-approximation/work/evidence/first-full-head-v2/packet.zip --output attempts/28-streamed-grammar-head/work/evidence/public-head-blocks-v2.json
```

Resultado: produtor32b46b2, todos os três métodos passaram;24/24 JSONs válidos,
2328 probabilidades por classe e massa completa conferidas. As oito sequências
de IDs com mesma seed são idênticas entre os três métodos. Head materializado
na GPU a partir do pacote antigo, sem forward novo. São286 blocos e quatro
palavras por peso;53.040 bytes D2H de sumários/recuperação na versão GPU contra
1.608.256 de pesos completos. Essa contagem não é medição de PCIe/latência nem
economia adicional sobre o controle PyTorch, que envia os mesmos sumários.

## V3: custo completo da fronteira, protocolo antes da medição

`work/antecedents-v3.md` registra que FactorDLM Proposição2 também já enuncia
a lei conjunta por classes. Não há nova teoria de quociente nesta tentativa.
A hipótese de sistemas permanece aberta. Protocolo `work/protocol-v3.json`:
todos18 estados antigos, NumPy/Torch/Triton com blocos256/512/1024, três rotações,
486 registros. Custos de frame, saída, RNG e transferências incluídos; setup
estático e primeiras chamadas JIT registrados. Gate primário exige ganho20%
wall E CPU contra TODOS seis controles, incluindo preparação do frame e o
custo de NOVOS forwards CUDA/softmax GPU compartilhados. Os mesmos números
novos são usados por todas as interfaces; não são os bits do softmax CPU
antigo. Setup estático completo também será reportado, sem ocultar JIT.

```bash
.venv-live/bin/python -m attempts.28-streamed-grammar-head.work.benchmark_v3 --input .cache/a22-development-cuda-v1 --output attempts/28-streamed-grammar-head/work/evidence/development-boundary-v3 --weights-cache .cache/a28-live-development-v3
.venv/bin/python -m attempts.28-streamed-grammar-head.work.analyze_v3 --input attempts/28-streamed-grammar-head/work/evidence/development-boundary-v3
```

O contrato das perguntas2/3/5/6 fica mais restrito: possível ganho de sistemas,
sem nova lei matemática, somente uma mesma operação/mesmo parser nesta fase,
controles numéricos fortes e custos reais de um passo. As
demais respostas continuam válidas. Resultados ainda não medidos; ganhos de
componentes não substituem o gate integral. É desenvolvimento novo nos frames
antigos, sem nova avaliação independente ou trajetória inteira. As matrizes
novas completas ficam no cache local, com hashes publicados por repetição;
nunca são fornecidas ao baseline CPU para evitar a transferência obrigatória.
