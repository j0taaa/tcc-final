# Protocolo prospectivo V1

Coordenação operacional adicionada antes dos forwards: toda execução CUDA nova
usa `flock /tmp/tcc-final-gpu-pilot.lock`, cobrindo preparo, carga, warmup,
medições e término do processo/liberação de VRAM. As verificações de correção
iniciadas antes dessa instrução terminaram sem interrupção. Não executar em
paralelo com a campanha de cache/memória da outra worktree.

Congelar hash deste arquivo e dos produtores antes da primeira geração neural.
Correções de implementação anteriores à avaliação são registradas; dados
anteriores nunca são sobrescritos. Não escolher tarefas por desempenho.

## Hipótese e decisão

Permitir propostas que precisam de posições adicionais, com alocação mínima
exata, pode melhorar acerto sob um orçamento de forwards, sem penalidade integral
relevante. Uma GPU só justifica desenvolvimento adicional se o verificador CPU
competente consumir pelo menos 10% da mediana do decode adaptativo em validação
e houver consultas suficientes para amortizar lançamentos. Sem esse sinal, não
escrever kernel próprio. Uma implementação mínima com operações Torch permite
medir o fatorial mesmo se perder; não é um sistema GPU otimizado.

Gate de continuidade: em TEST, candidata adaptativa não pode perder nenhum
acerto único frente ao melhor controle de cada família, deve economizar >=10%
na mediana pareada do tempo preparado em ambas as famílias e ambos os orçamentos,
e não perder validade. Alternativamente, ganho de >=2 itens únicos por família
com tempo mediano <=110% do controle aciona apenas confirmação independente.
São quatro itens por família em TEST. Nenhum desses gates prova publicação/originalidade.
Repetições de tempo não contam como novos exemplos de qualidade. Intervalos
bootstrap por item, descritivos com apenas quatro itens por família.

## Tarefas e separação

BBH word_sorting, revisão `9ee07bd481feebf959a6b59d61ea57bdcf30964d`.
Ordenar todos os índices por SHA256(`A89-v1:<índice>`). Os primeiros dois são
VAL, os quatro seguintes TEST, sem filtro de tamanho/dificuldade/gabarito.
Cada entrada origina duas tarefas: (a) lista JSON compacta de palavras ordenadas;
(b) lista de listas JSON, agrupadas pela primeira letra, palavras e grupos
ordenados. A segunda é uma transformação própria da tarefa externa, não um
benchmark publicado. Gabarito só no avaliador. A gramática não recebe palavras,
número de itens, letras iniciais ou resposta. Não há afirmação de generalização
de utilidade a partir deste pequeno piloto. Controle sem modelo: lista vazia,
e ordenação determinística (resolve a tarefa sem dLLM; reportar esse teto).

Modelo local LLaDA-8B-Instruct, snapshot
`08b83a6feb34df1a6011b80c3c00c7563e963b07`, NF4/double-quant/BF16,
RTX 3080 Ti 12 GiB. Reutilizar somente pesos/ambiente instalados, arquivos locais.
Quatro threads Torch/Rayon. Sem treinamento, compra ou outros modelos.

## Linguagem e políticas

CFG: raiz array, valores strings de letras ASCII ou arrays recursivos, strings
possivelmente vazias, sem espaços/escapes. Isso é um subconjunto explícito de
JSON, suficiente para as respostas destas tarefas, não toda GLC/JSON. A tradução
token->texto usa todos os IDs originais cujo texto ASCII está nesse alfabeto,
incluindo aliases e tokens com múltiplos lexemas. EOS/EOT só depois da raiz
fechada; PAD usa o mesmo ID EOS do tokenizer e só é permitido nesse sufixo.
Não apagar posições comprometidas, não retirar tokens dentro de strings. Uma
saída deve conter EOS, nenhuma MASK, e passar json.loads; comparar valor JSON
com o gabarito. Estados parciais/incompletos não são válidos funcionais.

Máximo 96 posições de resposta incluindo EOS/padding; início adaptativo 32.
Forwards máximos 8 ou 16. Sem KV cache. Cada forward produz candidatos reais;
considerar até oito alternativas por posição, ordenar por logit decrescente,
empate por posição e ID. No máximo 256 consultas por forward e quota
ceil(MASKs / forwards_restantes) compromissos. Se nenhuma alternativa passa,
continuar com novo forward até o orçamento, registrando estagnação.
O mesmo filtro lexical, shortlist e política de compromisso valem para os quatro
braços do fatorial e expansão simples. Não renormalizar confiança no vocabulário
filtrado: a confiança é a probabilidade no head completo.

- fixo CPU e fixo GPU: mesma viabilidade exata nas posições atuais; selecionar
  capacidade em VAL entre 32/64/96, por acertos somados nos dois orçamentos,
  desempate por mediana de tempo, depois menor capacidade.
- adaptativo CPU e adaptativo GPU: tentar a mesma proposta; se não cabe,
  procurar inserção mínima em quaisquer fronteiras entre posições, inclusive
  início/fim, sem deslocar a ordem dos compromissos. Só aceitar se cabe em 96.
  Empates da alocação têm uma regra comum determinística. Não expandir por baixa
  confiança nem afirmar que uma invariável exata entra em impasse espontâneo.
- simples CPU: mesmo verificador incremental, iniciar em 32; antes de cada
  forward após o primeiro, se a menor confiança dos MASKs do forward anterior
  for <0,1, inserir quatro MASKs junto à posição menos confiante até 96. Esta
  é uma ablação inspirada na inserção DAEDAL, não reprodução integral DAEDAL.
  Inserção só se preservar viabilidade atual. Não recebe alocação gramatical.
- reserva generosa CPU: fixo 96, mesmo decoder e verificador; reportar mesmo
  quando a seleção em VAL escolher outra capacidade.
- EPIC: implementação preservada, mesma linguagem, prompts/modelo, 96 posições,
  8/16 passos, bloco único, seleção paralela/exata/lexing ligados. Dar preparação
  reutilizável, omissão de forwards sem MASK e softmax reutilizado por forward
  quando possível; não enfraquecer o vendor nem mudar seus arquivos. Seu oráculo
  de lacunas arbitrárias tem funcionalidade diferente do exato em tokens; medir
  validade final e não fingir equivalência de trajetória. Sem recuperação que
  esconda falhas. Informar exceções/fallbacks/timeout.

VAL: fixos CPU 32/64/96, adaptativo CPU, simples CPU, reserva96 (=fixo96),
EPIC; ambos orçamentos, uma execução. TEST: sete modos (fatorial quatro,
simples CPU, reserva96 CPU, EPIC), ambos orçamentos, três repetições pareadas,
ordem rotacionada por item/orçamento/repetição. Repetição de fixo96 é preservada
se coincidir com o selecionado. Seed 89001; greedy, sem significância sobre seeds.

## Correção, custo, recursos

Antes do modelo: oracle independente de strings/json.loads e enumeração finita,
multigaps, macros, EOS prematuro, padding, orçamento esgotado, proposta impossível,
alocação inicial inviável, lacunas com comprimentos não contíguos. Comparar
distâncias/alocações CPU/GPU em entradas idênticas; em TEST comparar todos os IDs,
decisões e expansões pareadas. Divergência impede alegar equivalência.

Medir decode inteiro com synchronize CUDA nas fronteiras, incluindo tokenização
do prompt, tensorização, head, ranking, CPU/GPU, inserções e avaliação; categorias
internas disjuntas ou explicitamente aninhadas. Reportar carga, compilação C++,
lexer, gramática, transferência/tabelas GPU e primeira chamada separadamente;
serviço preparado exclui esses custos comuns, uso frio os adiciona sem amortizar
de forma arbitrária. Registrar forwards, somatório de comprimentos de entrada,
comprimento final/efetivo, expansões/inseridos, consultas/caches, memória GPU
alocada/reservada, RSS cumulativo e outros consumidores GPU. Sem sobreposição
assumida: esta implementação é serial entre parser e modelo.

Timeout cooperativo 60 s por decode; checks nativos mantêm timeout do upstream.
Recusar carga com <6,5 GiB livres. Limite de preparo do protótipo GPU 10 minutos;
registrar bloqueios e não substituir por medições inventadas. Preservar todos
os erros/negativos. Arquivos grandes regeneráveis ficam no cache A89 identificado.
