# A31v3 protocolo externo antes de novos forwards

JSON de argumentos de uma chamada, com valores livres de strings, números,
arrays e objetos recursivos. Prefixo só fixa nome conhecido da API e a primeira
chave obrigatória; não fixa nenhum valor correto. A gramática não usa respostas
nem catálogos de valores. É um preenchimento real de configuração/API, não
um benchmark sintético inventado. A gramática clássica comum beneficia todos.

`external-inputs-v3.json` registra TODOS658 inputs auditados, critérios e
hashes,16 desenvolvimento Python e64 confirmação live. Oito live casos usados
na M24 antiga são excluídos previamente; os demais são ordenados por hash
input-only. Nenhum gabarito foi obtido antes deste congelamento. Fonte oficial
pinada BFCL/Gorilla Apache2.0; corpus inteiro SHA no manifesto.

A operação primária é gerar dois candidatos do mesmo kernel EPIC e verificar
se ao menos um é correto, conservando literalmente o primeiro. Controles:
native iid completo com recuperação; estratificação apenas da raiz; histórico
completo; estado suficiente. Todos mesmos budgets/logits suportados, parser,
cache e recuperação. Controle determinístico também expõe a fronteira
qualidade/custo, sem supor queτ>0 será escolhido em toda aplicação.

Configuração e gates exatos em `protocol-v3.json`. Este estágio é pesquisa,
não resultado. Apenas candidata que passa desenvolvimento aciona confirmação.
Métricas incluem TODAS as falhas; nenhuma troca de casos após ver gabarito.
A cobertura matemática não se estende a interrupções por relógio ou mudança
do kernel por caching/batch global. Nenhuma alegação de qualidade para
verificadores ou corpus diferentes deriva do experimento.

O verificador executará o ASTchecker original pinado, com imports de linguagem
Python/registry mínimos (nomes de funções mantidos, sem conversão de pontos).
Não será uma comparação de igualdade inventada que facilite respostas.
Mapeamento do JSON para {function_name:arguments} é comum e auditável.

Custo completo por resposta correta é obrigatório para a decisão prática.
Ganho pequeno sem superar root/history, ou custo maior sem operação que o
justifique, não satisfaz o objetivo do usuário. Nenhuma promessa de aceitação
em revista/conferência ou prioridade mundial pode vir deste protocolo.
