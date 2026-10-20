# A73 — evidência adicional após a retomada

Este resultado acrescenta evidência ao [relatório V1](result.md), que permanece
preservado. Não altera casos/gates do [protocolo neural](protocol.md) nem apaga
a recusa de recurso. A decisão agora tem um limite matemático de utilidade,
além dos oráculos de correção e da auditoria de antecedentes.

**Decisão: não selecionar a contração A73 como contribuição central nesta
formulação.** Para o consumidor natural de sintaxe JSON irrestrita, a classe
inteira dos 32.804 identificadores tem rank máximo nas posições viáveis: não
há consultas de head adicionais a eliminar em relação ao sparse competente.
Nos casos de cópia, a redução já é obtida pelo pooling manual. O ganho algébrico
restante no exemplo balanceado é de uma relação construída e não estabelece
um consumidor natural, novidade ou benefício integral. Isso não prova que toda
GLC, todo schema ou toda implementação de head seja incapaz de ganhar tempo.

## Sintaxe mantida: nove casos, nenhuma redução adicional

O addendum [rank-probe.md](rank-probe.md) e o produtor `rank_probe.py` foram
congelados em `145060ee` antes dos dados. A ponte consome o forest do parser
mantido, preserva os IDs de um byte do tokenizer e verifica os contratos A73.
Todos os nove casos concluíram; nenhuma recusa, nenhum modelo/GPU/timing.
Resultados completos em [rank-probe-results.json](rank-probe-results.json).

| Caso | Consultas sparse variáveis | Σq_v A73 |
| --- | ---: | ---: |
| JSON 8 | 84 | 84 |
| JSON 16 | 180 | 180 |
| JSON 32 | 372 | 372 |
| Dyck 4 | 12 | 12 |
| Dyck 8 | 28 | 28 |
| Dyck 16 | 60 | 60 |
| Dyck 32 | 124 | 124 |
| JSON `[x,x]`, dois valores independentes | 4 | 4 |
| JSON `{"a":x,"b":x}`, dois valores independentes | 4 | 4 |

O denominador omite pares inviáveis e posições forçadas, como GPIO/GSP
competentes. Logo a redução de 13 posições de objeto para dois valores livres
não é um ganho da candidata. A comparação é estrutural, não latência.

Validação independente adicional: as 12 dimensões por ID do JSON foram
reproduzidas sem o parser/compilador, por eliminação inteira sobre 76, 164 e
340 palavras JSON explícitas, respectivamente. Os dois casos fixados têm suas
quatro palavras verificadas por `json.loads`; Dyck 4/8 teve 8/224 palavras
verificadas por pilha e seus ranks por eliminação inteira. O tokenizador de um
byte limita esta sondagem; ela não é um benchmark BPE de vocabulário completo.

## Obstrução para TODOS os identificadores Qwen selecionados

A [prova escrita](json-obstruction.md), congelada em `315cb6e0` antes da
auditoria dos testemunhos, trata também identificadores de muitos bytes e
admite outros tokens no suporte. Para n>=6, sem commitments e com os tokens
auxiliares declarados disponíveis, ela estabelece

    q_v = n-2 + 1[v é prefixo de true/false/null]
                + 1[v é sufixo desses literais ou expoente e/E seguido de dígitos].

Esse valor é exatamente o número de posições viáveis do ID. A razão é local
e concreta: dentro de uma string JSON, substituir isoladamente um token pelo
identificador v produz cada vetor e_i interno como diferença de palavras
válidas. Testemunhos de fronteira geram os pivôs restantes quando a sintaxe
os permite. Não se impõe retokenização canônica: a saída são IDs originais,
como no contrato do solver. Novas fixações ou suporte contraído podem remover
esses testemunhos; o teorema não é transferido para essa operação diferente.

A [auditoria finita](json_witnesses.py) cobriu TODOS os 32.804 IDs em quatro
comprimentos, totalizando **1.771.504 testemunhos válidos sem falhas**:

| Slots | Testemunhos / rank somado | Sparse variável |
| --- | ---: | ---: |
| 6 | 131.238 | 131.238 |
| 8 | 196.846 | 196.846 |
| 16 | 459.278 | 459.278 |
| 32 | 984.142 | 984.142 |

Há 11 IDs da classe viáveis na primeira posição e 11 na última no tokenizer
pinado. Ataques diretos aos endpoints em sete exemplos disponíveis também
concordaram; `e1` não é um ID dessa classe no tokenizer, portanto não foi
inventado como fixture neural. A decodificação dos bytes de TODOS os IDs foi
conferida independentemente com o decoder original. Contagens e hash dos
testemunhos estão em [json-witness-results.json](json-witness-results.json).

Isso é uma prova escrita acompanhada de verificações finitas; não é Lean,
prioridade científica ou validação de CUDA. Em particular, q_v é o rank
estrutural preparado antes de H. Não se alega lower bound universal de GPU:
dependências de H, mistura/preprocessamento das linhas W e fusão de kernels
são outras operações e podem ter outros custos.

## Dyck: a ausência de economia vale para todo comprimento par

Há também uma prova escrita curta independente dos números da tabela.
Para Dyck com dois tipos de pares e n par >=2, cada ID de abertura tem
q=n-1 e pode ocorrer exatamente nas posições 0,...,n-2. Para um i par,
use pares rasos antes/depois de um par que abre em i. Para i ímpar, use
pares rasos antes e um par externo que contém o par que abre em i.
Trocar somente o tipo do par escolhido preserva validade e muda o indicador
de cada ID de abertura somente em i. Logo e_i é uma diferença válida.
O mesmo argumento com reversão e troca abertura/fechamento cobre cada
posição 1,...,n-1 de cada ID de fechamento. A posição restante é impossível
por sintaxe; isso prova o rank exato. Assim Σq_v=4(n-1), exatamente sparse.
Comprimentos ímpares são inviáveis, não casos de rank zero favorável.

## Endpoint operacional e reprodução

Na retomada, a GPU passou a 0% instantâneo, mas o processo alheio PID 2603454
continuou residente com 4.054 MiB. O usuário não sabia a previsão de liberação.
As verificações foram feitas sob lock exclusivo; não se interrompeu o serviço,
não se relaxou a condição congelada de zero processo compute alheio e não se
mediu sob concorrência. A disponibilidade continuou sem mudar durante estas
verificações offline. O gate neural permanece **não executado/inconclusivo por
recurso**; não atribuir a ele zero ganhos em seis medições inexistentes.

Os novos resultados sustentam encerrar a seleção científica desta formulação
sem esperar um número de latência para o JSON: sua redução adicional de
consultas nessa classe é matematicamente zero. Não sustentam uma afirmação de
speedup, slowdown ou impossibilidade operacional de toda candidata relacionada.

Comandos, sem sobrescrever os resultados já existentes:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/src" \
  /home/jota/projects/tcc-final/.venv-a52/bin/python -u \
  attempts/73-grammar-head-contraction/rank_probe.py \
  --output /tmp/a73-rank-probe-replay.json
PYTHONDONTWRITEBYTECODE=1 /home/jota/projects/tcc-final/.venv-a52/bin/python -u \
  attempts/73-grammar-head-contraction/json_witnesses.py \
  --output /tmp/a73-json-witness-replay.json
PYTHONDONTWRITEBYTECODE=1 /home/jota/projects/tcc-final/.venv/bin/python \
  -m ruff check attempts/73-grammar-head-contraction
PYTHONDONTWRITEBYTECODE=1 /home/jota/projects/tcc-final/.venv/bin/python \
  -m ruff format --check attempts/73-grammar-head-contraction
```

Ruff passou nos novos produtores. A biblioteca e o vendor não foram alterados;
o `make check` anterior já passou em 345 testes. Cada produtor adicional tem
seus próprios checks científicos; nenhum resultado foi escolhido para substituir
um fracasso anterior nem foi iniciada nova campanha para resgatar A73.
