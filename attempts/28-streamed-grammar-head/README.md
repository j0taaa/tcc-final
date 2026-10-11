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
