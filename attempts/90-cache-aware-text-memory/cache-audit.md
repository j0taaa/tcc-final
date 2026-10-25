# Auditoria de cache: falha V1 e validação delimitada V1a

Todos os casos usam o template e tokenizer do consumidor efetivo. O executor
retokeniza o prompt completo e recorta um DynamicCache real no LCP de IDs. Nenhum
KV depois da primeira diferença é reutilizado. Validade causal de prefixos não
implica bit-identidade de cálculos de ponto flutuante em formatos distintos.

A primeira execução V1, consumidor Qwen 3B NF4/BF16, parou antes de avaliar tarefas:
append teve erro máximo 0,875 frente ao limite congelado de 0,25. A saída em ambos
foi `OK`. O diagnóstico posterior, preservado, cobriu as cinco fixtures e repetiu
execuções frescas: NF4 chegou a 1,015625; os mesmos pesos desquantizados em BF16
chegaram a 1,3125. Houve `OK` versus `OK.` no caso late. Execuções frescas repetidas
tiveram diferença máxima zero. Essa investigação não identificou a causa completa;
não atribuímos o efeito exclusivamente à quantização nem proclamamos um bug do
Transformers. Não usamos esses tempos para concluir ganho operacional da A90.

Antes da primeira resposta de tarefa, a V1a fixou consumidor comum
Qwen2.5-1.5B-Instruct em FP32, sem mudar entradas, memórias, perguntas ou critérios.
Os cinco casos passaram, saídas gulosas iguais e máximo de logits:

| Caso | Tokens reutilizados | Tokens de prefill executados | max abs Δlogits |
| --- | ---: | ---: | ---: |
| append | 71 | 16 | 0,000070572 |
| early | 52 | 28 | 0,000143051 |
| middle | 58 | 23 | 0,000100493 |
| late | 69 | 12 | 0,000027657 |
| boundary | 45 | 12 | 0,000075817 |

Essa auditoria é um smoke test numérico delimitado, junto ao invariante causal
inspecionado no código. Não prova bit-identidade universal, invariância de toda
resposta sob chunking, exatidão de KV esparso ou reutilização de sufixos editados.
A checagem CPU também encontrou `foo` → `[7975]`, `foobar` → `[50267]`:
mesmo prefixo de caracteres não é prefixo de tokens. Nas 245 memórias prontas,
os tokenizers 3B/1,5B produziram IDs idênticos; o orçamento foi verificado novamente.

Evidências: `reader-v1.jsonl`, `cache-diagnostic.jsonl`, `reader-v1a.jsonl`,
`tokenizer-v1a-check.json`, em `evidence/`. A emenda é explícita; V1 continua falha,
V1a é uma avaliação com outro consumidor. Nenhuma tolerância foi relaxada.
