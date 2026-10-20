# A86 — Resultado V3: aplicação encerrada com FAIL

Data: 20/10/2026. A candidata perdeu o gate prospectivo nas duas famílias TEST:
o custo previsto, incluindo preparação amortizada, foi **18,18% maior em código**
e **22,68% maior em explicações** que o melhor controle selecionado na validação.
O protocolo exigia redução de pelo menos 10% em ambas. **0/2 famílias aprovadas.**
Esta aplicação V3 está encerrada; não alterar casos, custos, classes, margens ou
controles para resgatá-la. Não implementar o decoder acelerado por este resultado.
A86 não foi selecionada como tema central.

## Protocolo, fontes e dados

O commit prospectivo foi `d317e2505e20a07bd29984b8449267f170f77356`, anterior à
captura e à avaliação. O [protocolo V3](protocol-v3.md), os produtores e os dados
foram preservados. SHA-256 conferidos contra o produtor e, para as fontes e
dependências congeladas, contra `git show` desse commit:

| Arquivo | SHA-256 |
| --- | --- |
| [capture-v3.jsonl](capture-v3.jsonl) | `7a19cebf14677a586a552c7c7e1d7cd715163c06e588b58ad326d81f8c8e2d12` |
| [replay-v3.jsonl](replay-v3.jsonl) | `7bd0897ecd7e7098b11de25c7fdda583ea63a5073174ff8ec3f89e05bb367a7f` |
| [protocol-v3.md](protocol-v3.md) | `925b8a42b82cd98531e0161696c15d87039b432951e8212c683e25e63cb1c826` |
| [capture_v3.py](capture_v3.py) | `6f23dcfc863b8a3de3c5da773044405392d771005baf8ad929a427e19a47e095` |
| [policies_v3.py](policies_v3.py) | `d31981c12957e0a2c7a83307637be99dcbe5f9524af6f546fcf748fcd2d94410` |
| [planner.py](planner.py) | `3b223f68da1fbb3af9ac54ef1bc476031039fad08978456ecafc9b9891f58012` |
| [profile-v1.jsonl](profile-v1.jsonl) | `4b588d2904b8d3b5e63779d58adde6945b620f412cee53830458a5017f4476bf` |
| [fidelity-v2.jsonl](fidelity-v2.jsonl) | `78de01d3bbecd1f61d896a08476728d0ff59c4306fb859df949037ee16b86daa` |

Captura: RTX 3080 Ti, LLaDA-8B-Instruct no snapshot
`08b83a6feb34df1a6011b80c3c00c7563e963b07`, NF4/double/BF16, sem KV,
softmax FP32, quatro threads e seed 86003. Python 3.11.16, Torch 2.8.0+cu128,
Transformers 4.52.2, bitsandbytes 0.50.1 e accelerate 1.10.1. Replay CPU:
SciPy 1.17.1, NumPy 2.4.6 e NetworkX 3.6.1.

Os 16 casos terminaram sem erro, recusa ou processo CUDA concorrente registrado.
Foram capturados 1.760 eventos: TRAIN 256, VALIDATION 480 e TEST 1.024.
Os quatro TRAIN atingiram o limite de 64 eventos; na validação, três casos
completaram a região e `validation-3` terminou por terminal seguro aos 96 eventos.
Os oito TEST completaram a região aos 128 eventos. Nenhum caso foi removido.
A carga do modelo, registrada separadamente, durou 58,275732594 s; o pico de
alocação da captura B1 foi 5.826.620.928 bytes. Isso não mede a memória de um
decoder acelerado.

## Ajuste e seleção sem usar TEST

Excluídas as últimas oito origens de cada TRAIN, restaram 224 origens para ajuste.
As tabelas globais foram:

| k | Origens TRAIN | Nós observados | Consultas escolhidas pelo flow global |
| --- | ---: | ---: | ---: |
| 1 | 4 | 1 | 1 |
| 2 | 4 | 2 | 2 |
| 3 | 4 | 4 | 3 |
| 4 | 4 | 6 | 5 |
| 5 | 4 | 9 | 2 |
| 6 | 4 | 9 | 1 |
| 7 | 4 | 10 | 1 |
| 8 | 196 | 56 | 2 |

Há 544 registros de ajuste: 357 `OPTIMAL` e 187 `FALLBACK_GLOBAL` por classe
sem observações. Entre os ótimos, 146 são MILPs HiGHS, todos com gap zero;
190 têm solução direta e 21 são ajustes flow. Não houve timeout ou inviabilidade.
O status HiGHS é evidência numérica do solver; não é certificado formal independente.

Foram avaliadas 3.123 configurações somente em VALIDATION: 520 por família SSD
ou Spiffy, duas flow e uma serial. Cada uma percorreu suas próprias origens
induzidas na trajetória completa. As configurações congeladas foram:

| Família | Escolha em VALIDATION |
| --- | --- |
| Serial | `{1}` |
| SSD-chain | contextual, N=(1,1,1) |
| SSD-mix | global, N=1 |
| Spiffy J0 | global, D=1 |
| Spiffy J1 | global, D=1 |
| Spiffy J0-GM | contextual, D*=(1,1,1), grafo base D=12 |
| Spiffy J1-GM | contextual, D*=(1,1,1), grafo base D=12 |
| Flow | global |

Todos os controles selecionados consultam efetivamente apenas `{1}`; as variantes
GM ainda pagam seu cálculo online. Expandir as consultas não compensou no replay
de validação. As pequenas diferenças entre configurações com as mesmas consultas
vêm dos tempos CPU registrados, sem evidência de ganho pelo contexto.
O serial foi o melhor controle na validação. Flow global custou 60,381426276 s
previstos, contra 63,162951275 s contextual e 48,711098702 s serial.
Nenhuma configuração foi escolhida por métrica TEST.

## Custo e gate TEST

As medianas V1 congeladas, em ns, são `c1=101481173` e `c8=517789811`.
Foi aplicado exatamente
`C(m)=floor(m/8)*c8+min((m mod 8)*c1,c8)`.
O envelope usou `a=42008511`, `b=59472662` e
`kappa=507405865/339371821` (aproximadamente 1,49513).

A preparação cobrada à candidata soma **78,828404300 s**:
78,631092468 s de captura integral TRAIN+VALIDATION e 0,197311832 s de CPU
flow/compartilhada. O segundo intervalo resulta dos 21,972001545 s offline totais,
descontando os intervalos exclusivos de ajuste/busca dos controles, registrados
separadamente. Os cabeçalhos TRAIN+VALIDATION consumiram 77,473026668 s, já
contidos na captura integral. A carga do modelo fica separada conforme o protocolo.
Os controles recebem custo zero de preparação no gate.

O horizonte é de 1.000 respostas. Os valores abaixo somam quatro casos por
família; incluem seleção CPU online e, para flow, quatro parcelas da preparação
amortizada. O critério conservador compara com **cada** família de controle cuja
configuração foi congelada em VALIDATION; o serial é o menor em ambos os grupos.

| Família TEST | Consultas flow / serial | Flow com preparo (s) | Melhor controle (s) | Razão | Gate |
| --- | ---: | ---: | ---: | ---: | --- |
| Código | 602 / 512 | 61,4071078292 | 51,958500647 | 1,181849112 | FAIL |
| Explicações | 625 / 512 | 63,7411766842 | 51,958500252 | 1,226770911 | FAIL |

Razões exatas: código `307035539146/259792503235`; explicações
`318705883421/259792501260`. Ambas excedem 1 e o limite prospectivo de 0,9.
Flow já perde antes da preparação; não existe ponto de amortização favorável
frente aos controles selecionados nestes dados.

O flow executou 609 macros, contra 1.016 seriais, mas consultou 1.227 cabeçalhos
contra 1.024: 203 consultas futuras não foram aproveitadas. Das macros flow,
52 consultaram um estado, 524 dois, 23 três e dez cinco. Houve 24 macros
que alcançaram um cabeçalho no próximo bloco, sem perder a fronteira.

O menor número de macros não representa menor custo. Todos os tamanhos escolhidos
pelo flow global são no máximo cinco; como `5*c1<c8`, nessa faixa **C(m)=m*c1**.
Logo nenhuma dessas macros recebe economia por B8, e consultas rejeitadas apenas
aumentam o custo. A otimização exata do envelope afim não otimizou a tabela de
custo real deste executor. Sua garantia de aproximação permanece compatível
com esta perda; não estabelece aceleração.

## Auditoria independente e limites

Uma auditoria CPU independente reconstruiu os 1.760 eventos e canvases finais,
ranks, classes, caminhos e exclusões de treino. Conferiu frequências, objetivos
inteiros, conectividade e cardinalidades dos ajustes; nos MILPs conferiu também
o status, gap e limite dual registrados. Recalculou os custos neurais de todas
as 3.123 configurações de validação e confirmou os mínimos dos scores registrados,
a separação dos splits e a ordem dos registros de seleção antes de TEST.

Os 72 replays TEST foram conferidos macro a macro: conjuntos escolhidos,
prefixos completos, consultas cobradas, seleção CPU registrada, primeira consulta,
evento final direto, totais e gate por `Fraction`. O serial cobrou exatamente
L consultas para L eventos em todos os casos. Hashes, preparação e todas as
razões acima passaram na conferência. A auditoria não repetiu forwards nem
recronometrou ajuste ou seleção para substituir os tempos congelados.

**Medido:** geração serial B1, captura, preparação e seleção CPU; o perfil B1/B8
é a medição V1 reutilizada. **Estimado:** custo de geração acelerada por replay
e pela tabela V1. Não foi executado um decoder acelerado V3, nem comprovada
igualdade numérica de todas as suas consultas hipotéticas. Os oito TEST não
fundamentam afirmações gerais sobre modelos ou tarefas. O resultado negativo
encerra esta aplicação; preserva as provas delimitadas e os dados sem promover
A86 a contribuição central.
