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
| [19-growing-support-decoding](19-growing-support-decoding/README.md) | Suportes crescentes e controles de reserva |
| [20-lexical-support-quotient](20-lexical-support-quotient/README.md) | Congruência lexical completa |
| [21-contextual-token-groups](21-contextual-token-groups/README.md) | Grupos conforme estado lexical |
| [22-full-vocabulary-posterior](22-full-vocabulary-posterior/README.md) | Posterior sobre todos os IDs originais |
| [23-canonical-epsilon-posterior](23-canonical-epsilon-posterior/README.md) | Circuito epsilon com proveniência de slots |
| [24-certified-depth-approximation](24-certified-depth-approximation/README.md) | Fechamento com certificado de erro e uso iterativo |
| [25-exact-envelope-sampling](25-exact-envelope-sampling/README.md) | Rejeição exata sobre envelope certificado |
| [26-stratified-decoder-batches](26-stratified-decoder-batches/README.md) | Lotes com lei individual preservada e dominância sobre iid |
| [27-finite-closure-certificates](27-finite-closure-certificates/README.md) | Limites finitos de fechamento; protótipo, novidade não confirmada |
| [28-streamed-grammar-head](28-streamed-grammar-head/README.md) | Resumo amostrável da cabeça para inferência conjunta; protótipo, novidade não confirmada |
| [29-collision-stationary-coupling](29-collision-stationary-coupling/README.md) | Reparo de colisões; errata do comparador raro preservada, utilidade/novidade abertas |
| [30-lazy-native-stratification](30-lazy-native-stratification/README.md) | Estratificação assíncrona do ruído nativo; correção pequena validada, utilidade/novidade abertas |

| [31-sufficient-state-coupling](31-sufficient-state-coupling/README.md) | Reunião de estados suficientes; prova comparativa e correção pequena, utilidade/novidade abertas |
| [32-native-oracle-antithetics](32-native-oracle-antithetics/README.md) | Orçamento ótimo de classes e custo minimax; antecedentes próximos, uso/novidade ainda abertos |
| [33-categorical-oracle-repair](33-categorical-oracle-repair/README.md) | Corrida categórica; redução exata a A29/Barker, recusada antes de implementar |
| [34-oracle-diversity-frontier](34-oracle-diversity-frontier/README.md) | Fronteira esperada com refinamento inteiro; candidata escrita, prioridade/uso abertos |
| [35-commitment-law-counting](35-commitment-law-counting/README.md) | Lei do commitment versus posterior LL(1); ponte escrita de contagem, antecedente de união explícito |
| [36-grammar-sparse-output-head](36-grammar-sparse-output-head/README.md) | Cabeça esparsa pela gramática; mecanismo anterior encontrado, versão simples recusada antes de código |
| [37-canonical-outcome-coupling](37-canonical-outcome-coupling/README.md) | Hash de resultados completos; garantias provadas, controle empírico mais forte encontrado depois |
| [38-empirical-pool-coupling](38-empirical-pool-coupling/README.md) | Ótimos categóricos simultâneos e custo pontual; teoria escrita antes de código, prioridade/uso abertos |
| [39-known-source-coupling](39-known-source-coupling/README.md) | Fronteira de fontes conhecidas; piloto nativo negativo e auditoria corrigida sem classes úteis |
| [40-anchor-trace-coupling](40-anchor-trace-coupling/README.md) | Âncora independente/cache exato pago; corolário escrito, novidade/uso abertos |
| [41-structured-noising-covariance](41-structured-noising-covariance/README.md) | Noising/score estruturado e ordem de covariância; matemática/redução escrita antes de código |
| [42-safe-empirical-resampling](42-safe-empirical-resampling/README.md) | Cobertura ótima de átomos e segurança para todos os scores; passo global ainda conjectural |

A primeira pasta inclui também o commit inicial do repositório (README apenas)
e o primeiro protótipo completo, da etapa M2, em versões próprias. A cópia `v1`
é a consolidação posterior da mesma abordagem; ela não foi apresentada como
o estado literal do primeiro commit.

As direções 15/16 foram rejeitadas pelo usuário como protagonistas: a aplicação
não justificou usar uma dLLM. Seus resultados continuam preservados. A direção
17 encerrou uma decisão delimitada: há ganho em alguns lotes grandes do
posterior PL, mas não em treinamento completo ou geração final. Seus 16
snapshots mantêm controles mais rápidos, erros de harness e todas as perdas.
A tentativa18 investigou lexicográfico e propagação incremental competente
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
    as variantes e um controle independente de pilhas.216 comparações exatas
    com oráculo completo passam. Cache dos limites do controle reforçado antes
    de repetir desenvolvimento;171 registros v5 preservados. Todos
    os dados, inclusive50 registros frescos interrompidos, estão preservados.
    Confirmação com controles fortalecidos/novidade ainda pendentes.

V6 de22 é negativa:411 registros, condições necessárias rejeitam ambas as
candidatas em todas18 configurações;129 timings restantes não foram executados.

23. [Circuito epsilon com escolhas originais](23-canonical-epsilon-posterior/README.md):
    cópias independentes, prova escrita delimitada e seis oráculos pequenos
    em12 kernels. Remoção epsilon clássica, benefício não confirmado. Comparação
    completa antes de qualquer novo forward independente. A22 permanece acessível.

A23 v1 negativa:262 registros e dois probes apenas negativos reordenados,
condições necessárias rejeitam três variantes em todos18 quadros. Sem captura nova.

24. [Aproximação de profundidade certificada](24-certified-depth-approximation/README.md):
    especificação/provas escritas iniciais, regularização e conditioning antigos
    creditados. Counter lexical limita massa profunda e erro condicionado;
    política comum permite bound da trajetória. Nove oráculos pequenos e168
    comparações full-V passam. Duas campanhas de viabilidade108+108 preservadas;
    handoff permite depth menor que grammar-hit em7/18 quadros. Separação
    escrita com tokenizer fixo, custo/limites explícitos. Consulta confirma3/18
    ganhos em desenvolvimento e3/15 independentes contra TODOS seis controles;
    todos1.215 registros independentes preservados. Aplicação MDLM conclui30/30
    casos com184 novos forwards. Prioridade/publicação não estão confirmadas.

### 25 — envelope exato (isolado)

[25-exact-envelope-sampling](25-exact-envelope-sampling/README.md) reutiliza
apenas cópias imutáveis de24/v3 para propor no envelope e aceitar somente
JSON completo. A lei aceita é exata; sete oráculos independentes verificam
os sorteios efetivos, inclusive CARS adaptativo. Há separações escritas
delimitadas, não prioridade/velocidade confirmada. Counter+CARS e inferência
compacta são controles obrigatórios. Nenhum timing de24 é vitória de25.

A comparação completa24 selecionou handoff por empate ANTES da captura dos
cinco documentos externos. A confirmação completa conserva1.071 resultados
conclusivos,144 recusas e540 checks contra massa exata, com3/15 ganhos de
consulta e2/15 de primeira amostra aproximada. A geração30/30 válida é uma
demonstração funcional de uma seed; não superioridade estatística geral.
V6 preserva fontes/protocolo antes da aplicação; v7 acrescenta os resultados
reais e a auditoria33/33 de amplificação. V1 e refinamentos de25 permanecem
independentes. V2 executou702 registros/13 controles:0/18 gates primários
de primeira amostra para ambas variantes e1/18 secundário de lote32, sem
confirmação independente. Um erro de timer é preservado;36 bloqueadores
concluídos/sem erro mostram que a rejeição primária não depende dele.
V8/24 consolida artigo e reprodução; v3/25 conserva a decisão negativa e
a correção de fronteira, sem modificar resultados antigos.

V1/26 conserva a primeira prova/implementação e o replay top16 de massa zero.
V2/26 acrescenta a prova de optimalidade para eventos prefixos, sete oráculos,
cinco especificações Lean selecionadas, a recomputação full-V do MESMO head,
os64 candidatos válidos e a melhoria exata pequena do evento de IDs da fonte.
A garantia geral é sobre iid do mesmo decoder, com distribuição individual
preservada. Estratificação/unranking são clássicos; não há ganho universal de
latência, nova aplicação neural iterativa26 ou prioridade acadêmica confirmada.

### 32 — oráculo nativo e classes (candidata, não confirmação)

[32-native-oracle-antithetics](32-native-oracle-antithetics/README.md) investiga
acoplamento de pares preservando a lei finita nativa e recuperação completa,
sem probabilidade de classe calculada. Há prova candidata de orçamento mínimo
quatro/limite ótimo no acesso p-blind delimitado e expected auxiliary<=1.
Quatro oráculos e216 replays de heads FALSOS passam; nenhuma medição neural
ou novidade/publicabilidade confirmada.32 não herda o piloto31:272 registros,
11.615 novos forwards e cobertura EMPATADA preservados em31/v3.

### 29 — reparo estacionário de colisões

[29-collision-stationary-coupling](29-collision-stationary-coupling/README.md)
preserva P/Q distintos e deriva não deterioração de pass@2 para qualquer
verificador, usando MH clássico e uma proposta adicional só em colisões.
Cinco oráculos independentes passam. Errata2026-10-11: o teto quadrático de
eventos raros vale para TODO par de mesmas marginais; a comparação histórica
com ganho linear era impossível e está corrigida separadamente. Não promover
como protagonista sem novidade/custo/aplicação; nenhuma
medição/execução neural ou novidade suficiente para publicação confirmada.

### 33/34 — gates matemáticos antes de implementação

A33 reduz exatamente a A29+Barker; recusada como protagonista ANTES de
implementar ou gerar novas medições. A34 escreve uma candidata de fronteira
minimax para todos os orçamentos esperados reais, por score e aritmética
inteira. Ruína do jogador é clássica; prioridade e aplicação útil continuam
abertas. As notas têm pastas próprias; primeiros snapshots serão congelados
após o piloto A32 para não competir com seus timings na compactação.

A32/v4 concluiu1056 registros/2208 JSONs válidos/32.716 forwards novos com
resultado negativo:8 candidatas20/32 empatam iid2 e custam mais, misto21/32
é mais barato. Screen predefinido encerrou o piloto, sem labels test/outros
seeds. Todos os resultados/IO/metadata estão preservados. A34 acrescenta
referência mínima e4 oráculos, sem nova execução neural ou utilidade confirmada;
DeGroot original foi lido, Wasan/Ghosh e novidade específica ainda pendentes.

### 37 — resultado canônico de gerações completas

[37-canonical-outcome-coupling](37-canonical-outcome-coupling/README.md) começa
com prova e oito critérios ANTES de código. Hash aleatório e ruína dão1/13
do ganho máximo de cobertura de pares de mesmas marginais para qualquer
resultado canônico correto único. Custo integral: iid3 SEMPRE vence cobertura
com mesmo número esperado de gerações. Avaliação cara é uma condição ainda
não validada, não um atraso artificial de benchmark. Prioridade/publicação
continuam abertas; v1 preserva exatamente o contrato escrito inicial.

V2 preserva referência independente/quatro oráculos e o corolário de1/13
da maior redução de colisões para TODA distribuição canônica. O controle
clássico por quantis conhecidos atinge o ótimo; geração/avaliação completa
continua requisito de custo. Sem novos forwards ou vitória prática/publicação.


### 38 — empirical coupling and complete native pilot

[38-empirical-pool-coupling](38-empirical-pool-coupling/README.md) preserves
all56 native pilot rows,169 actual calls/1885 forwards and35 incomplete
outcomes. Adaptive saves calls against the same-law pools, but iid2 is
cheaper with equal observed pass2. No general EPIC or publication win.
Sharp candidate frontier/cost proofs and semantic-coarsening laws have
12 focused independent checks;159 full tests pass. All versions are kept.

### 39 — known finite source and opaque decoder decisions

[39-known-source-coupling](39-known-source-coupling/README.md) starts with
proofs and eight criteria BEFORE code. Known source addresses, adaptive
queries and cloning are admitted; robust cap4 atom/query-cost optima are
finite, with a strong cheap seed-derangement control. Native first-yield
coordination could preserve every marginal/terminal-verifier guarantee
with equal expected neural forwards; full physical cost remains mandatory.
No prototype, neural output, timing or publication claim yet.
