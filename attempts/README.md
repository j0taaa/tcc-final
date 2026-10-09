# Tentativas de pesquisa preservadas

Cada direção tem sua própria pasta. Cada versão contém **cópias reais e
imutáveis** do código, das provas, das configurações e das evidências. Os
arquivos estão compactados para preservar versões sem ampliar o código mantido.
Não são links para arquivos atuais; nenhuma tentativa foi apagada por ter perdido
uma comparação. As fases e repetições de cada campanha mantêm suas subpastas.

## Índice

| Pasta | Direção |
| --- | --- |
| [01-mwpc-original](01-mwpc-original/README.md) | MWPC original e validação inicial |
| [02-parallel-batch-selection](02-parallel-batch-selection/README.md) | Seleção paralela em estados reais — M18 |
| [03-witness-reuse-audit](03-witness-reuse-audit/README.md) | Controle com reutilização de testemunho — M19/M20 |
| [04-minimal-json-repair](04-minimal-json-repair/README.md) | Reparo mínimo de JSON — M21 |
| [05-dllm-tool-infilling](05-dllm-tool-infilling/README.md) | Preenchimento de chamadas com dLLM — M22 |
| [06-epic-tool-comparison](06-epic-tool-comparison/README.md) | Comparação com o decoder EPIC — M23 |
| [07-stable-commitment-policies](07-stable-commitment-policies/README.md) | Políticas de commitment e confirmação externa — M24 |
| [08-grounded-json-generation](08-grounded-json-generation/README.md) | Geração de consultas com dados externos — M25 |
| [09-budgeted-commitment](09-budgeted-commitment/README.md) | Commitment com orçamento e certificados — M26–M28 |
| [10-conflict-guided-commitment](10-conflict-guided-commitment/README.md) | Aprendizagem de conflitos certificada — M29 |
| [11-probability-certificates](11-probability-certificates/README.md) | Certificados de massa e auditoria de relevância — M30/M31 |
| [12-exact-cfg-posterior](12-exact-cfg-posterior/README.md) | Posterior gramatical exato — M34/M35 |
| [13-commitment-event-reduction](13-commitment-event-reduction/README.md) | Probabilidade de eventos de commitment — M36 |
| [14-boolean-execution-profiles](14-boolean-execution-profiles/README.md) | Condicionamento de regras Booleanas por execução — M36 |
| [15-adaptive-semantic-cores](15-adaptive-semantic-cores/README.md) | Refinamento adaptativo e núcleos semânticos — M36 |
| [16-cars-rejection-bound](16-cars-rejection-bound/README.md) | Limite de rejeições contra a atualização publicada do CARS — M36 |
| [17-pl-latent-resampling](17-pl-latent-resampling/README.md) | Auditoria de reamostragem latente após seleção PL |
| [18-monotone-grammatical-decoding](18-monotone-grammatical-decoding/README.md) | Preservar a trajetória gulosa e reduzir trabalho gramatical |

A primeira pasta inclui também o commit inicial do repositório (README apenas)
e o primeiro protótipo completo, da etapa M2, em versões próprias. A cópia `v1`
é a consolidação posterior da mesma abordagem; ela não foi apresentada como
o estado literal do primeiro commit.

As direções 15/16 foram rejeitadas pelo usuário como protagonistas: a aplicação
não justificou usar uma dLLM. Seus resultados continuam preservados. A direção
17 encerrou uma decisão delimitada: há ganho em alguns lotes grandes do
posterior PL, mas não em treinamento completo ou geração final. Seus 16
snapshots mantêm controles mais rápidos, erros de harness e todas as perdas.
A investigação atual é a 18: lexicográfico e propagação incremental competente
para conservar os commits do guloso e avaliar custo na geração inteira.
Organização, testes e provas selecionadas não substituem avaliação humana de
prioridade/significância.

## Abrir uma versão

Por exemplo, a partir da raiz do repositório:

```bash
make attempts-check
python3 -m zipfile -e attempts/16-cars-rejection-bound/v1/source.zip .cache/attempt-16
python3 -m zipfile -e attempts/16-cars-rejection-bound/v1/evidence.zip .cache/attempt-16
```

O diretório extraído preserva os caminhos originais (`src/`, `scripts/`,
`formal/`, `paper/`, `configs/`, `docs/`, etc.). A lista completa e os hashes
estão em `v1/manifest.json`. Não extraia sobre o projeto mantido.

O código é congelado no commit de cada tentativa. As evidências foram copiadas
da versão indicada pelo `evidence_commit`, que pode ser posterior: correções de
proveniência e resultados finais foram arquivados depois da execução. O commit
de preservação **não é** o commit produtor de uma medição. Metadados, perdas,
casos impossíveis, timeouts e relatórios originais são mantidos sem alterações.

Nos casos sem campanha própria, `evidence.zip` está vazio; os argumentos,
diagnósticos e oráculos ficam no snapshot de código. A última direção reutiliza
as capturas anteriores explicitamente, sem apresentá-las como nova medição.

## Integridade e novas tentativas

`make attempts-check` verifica todos os ZIPs e os arquivos internos offline,
sem modelos, rede ou histórico Git. Para comparar também com as árvores Git
originais disponíveis localmente:

```bash
python3 scripts/archive_attempts.py --check --git
```

Antes de investigar outra abordagem, crie `attempts/<id>/README.md` com a
hipótese, contrato e critério de descarte, e guarde seu protótipo em `work/`.
Preserve resultados negativos e anote cada revisão em vez de sobrescrever a
tentativa anterior. Não duplique EPIC, pesos de modelo ou caches nesse protótipo.

Para congelar uma versão concluída, registre em `catalog.json` os hashes completos
de código/evidência e as raízes de evidência pertinentes. A partir de commits
já existentes e sincronizados, execute (o snapshot inclui o `work/` desta
tentativa; outros snapshots são excluídos para evitar cópias recursivas):

```bash
python3 scripts/archive_attempts.py --create <id> --git
```

O comando recusa substituir uma versão existente; use `v2`, `v3`, etc. Para
acrescentar uma versão a uma pasta existente, registre-a e use
`--create <id> --version v2 --git`. Cada fonte já congelada continua acessível
dentro da sua versão.
Snapshots não entram nos imports, lint, suíte ativa ou distribuição da biblioteca.
A verificação de integridade integra o CI; ela verifica preservação, não a
correção científica do método.

Arquivos originais permanecem nos seus caminhos de reprodução. Modelos, caches
e logits completos que nunca foram publicados continuam fora do Git. Submódulos
históricos são pinados nos manifestos; o código externo e as dependências não
são invenções deste trabalho.

A tentativa19 começa em `19-growing-support-decoding/`, com suporte expandido
pelas previsões atuais e controles de reserva inativa. É pesquisa independente
ainda não confirmada, não continuação de um resultado positivo de18. A versão
inicial será congelada após o commit do código/protocolo, antes dos timings.

20. [Suporte por congruência lexical completa](20-lexical-support-quotient/README.md):
    hipótese e protótipo isolados; classificação em todos os estados, crescimento
    por classe e controles lexicais fortes. Princípios conhecidos, benefício
    não confirmado. Dados negativos de19 preservados em v2.

21. [Grupos dependentes de estado lexical](21-contextual-token-groups/README.md):
    protótipo e prova escrita delimitada, sobreposição de membros e crescimento
    seguro. Todos os controles byte/lexer/classes globais preservados.
    1.026 registros e897 comparações iguais, nenhum ganho forte contra controles
    lexicais/globais. Resultado negativo preservado; fundamentos conhecidos.

22. [Posterior no vocabulário inteiro](22-full-vocabulary-posterior/README.md):
    representação lexical de massa, marginais e amostras exatas sobre TODOS os
    originais; classes globais/locais e rejeição como controles. Provas escritas
    delimitadas e quatro oráculos passam. Comparadores originais davam6/18 e7/36
    ganhos preliminares; acrescentamos trimming lexical pelo sufixo a todas
    as variantes.192 comparações exatas com oráculo completo passam. Todos
    os dados, inclusive50 registros frescos interrompidos, estão preservados.
    Confirmação com controles fortalecidos/novidade ainda pendentes.
