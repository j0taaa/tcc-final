# Emenda de execução V1a — antes de qualquer resposta de avaliação

A V1 preservada em `evidence/reader-v1.jsonl` parou na primeira auditoria de cache:
max |Δlogits| 0,875 > 0,25. Não há nenhuma resposta de tarefa nesse arquivo.
`cache-diagnostic.jsonl` confirmou diferença entre cache e execução fresca em
NF4 e nos mesmos pesos desquantizados BF16, inclusive diferença de pontuação
na saída gulosa. Repetição fresca foi idêntica a si mesma. Não se estabeleceu a
causa completa e não se declara válida a versão NF4 pelo fato de o argmax inicial
coincidir. Não aumentamos tolerância depois da falha.

A V1a troca somente o consumidor por Qwen2.5-1.5B-Instruct, revision registrada
em `pre-qa-fp32-amendment.json`, pesos originais em FP32, sem offload, igual para
os sete métodos. Os editores, memórias já produzidas, dados, perguntas, rubric,
orçamento de memória e gate continuam fixos. O leitor precisa passar os mesmos
cinco casos e limite de 0,25, com saídas gulosas iguais, antes de avaliar tarefas.
Isso é uma correção operacional da avaliação, não resultado positivo V1.
Custos de falha/diagnóstico/download/preparo adicionais serão relatados.

A mudança deixa de compartilhar o mesmo objeto/modelo entre editor AR e leitor:
AR editor 3B NF4, leitor comum 1,5B FP32; a dLLM permanece 8B NF4. Assim todos os
sistemas produtivos agora precisam do leitor e de seu editor, ou de fases com
swapping. O piloto continua replay de fases, sem medir residência simultânea.
A qualidade de um leitor menor e o custo FP32 limitam generalização, mas valem
igualmente para candidata e controles. Não comparar tempos da V1 falha com os
resultados de utilidade V1a nem chamar isso de réplica sem alterações.
