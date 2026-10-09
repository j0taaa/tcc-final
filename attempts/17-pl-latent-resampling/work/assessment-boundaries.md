# Fronteiras da confirmação

A operação confirmável é reamostrar propostas descartadas de **uma política
específica**: conclusão produto condicionada à gramática, seguida de seleção
PL de posições com taxas locais positivas. Não é operação requerida por toda
dLLM. Usá-la em treinamento exige implementar/registrar essa política, seu
normalizador, suporte localmente fixo e score da seleção. Nenhum modelo foi
treinado nesta auditoria; a referência não altera os decoders mantidos.

O evento condicionado inclui ordem e tokens observados. Ignorar a ordem ou
somente condicionar aos tokens muda a lei. Não há promessa de geração mais
rápida que EPIC: EPIC não resolve essa operação de gradiente. Circuitos de
fatores podem substituir o backend CFG, sem negar o algoritmo do kernel.

A confirmação de correção consiste em prova escrita sob hipóteses explícitas
e oráculos exatos pequenos. Não abrange implementação inteira, hipóteses
científicas sobre um modelo real, semântica do JSON ou prioridade na literatura.
A prova do ganho em tentativas é comparativa contra uma família precisa, não
contra todos os métodos. O contador binomial resolve o objeto de prova também.

Os nove replays cobrem todas as capturas previamente arquivadas, inclusive
recusa de compilação. São probabilidades de modelo sobre suporte declarado,
com derivação racional arquivada. Os logits completos originais continuam
locais; não foram inventados, reexecutados ou publicados nesta auditoria.
Os mesmos estados foram usados para desenvolver refinamentos; isso deve ser
assumido ao interpretar desempenho e não chamado de teste externo novo.

A exatidão computacional é relativa às probabilidades racionais recebidas.
Os oráculos de gradiente diferenciam uma política suave especificada e avaliada
nesses pontos; não diferenciam o arredondamento da captura ou um programa de
softmax em produção. Não converter isso em uma afirmação de gradiente neural
exatamente sem viés para probabilidades reais diferentes dos inputs publicados.

Os timers medem compilação comum e consultas CPU, com preparação condicional
incluída. Não medem consumo de memória residente por método, forward, backward,
recompensa, treinamento ou acerto final. Bits do inside e tamanho da floresta
são diagnósticos de representação, não medidas de memória física. Tempos são
três repetições descritivas, sem certeza estatística universal.

Os deadlines são cooperativos, consultados em limites de operações. Uma
operação atômica já iniciada pode ultrapassar o prazo; a síntese registra
prefixos concluídos depois dos 10 s, se houver, em vez de esconder excedentes.

A lei exata corresponde ao sampler sem interrupção dependente dos sorteios.
Uma amostra observada antes de um prazo de parede não conserva necessariamente
a distribuição condicionada a sucesso nesse prazo. Os registros de timeout
são evidências de custo, não certificados de uma política de treinamento.
Não reutilizar esses prefixos como evidência de ausência de viés operacional.

A redução de variância `V_o+V_h/(r+1)` é conhecida e estrita apenas quando
`V_h>0`. Replicar propostas sem novos forwards pode ainda exigir preparação
mais cara que a economia. Para uma réplica, a condição de benefício por custo
é `beta>2d/(1+d)`. Nem uma razão exata melhor de tentativas nem uma família
matemática resolve por si só essa condição num treinamento real.
