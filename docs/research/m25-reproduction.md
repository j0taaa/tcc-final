# Reproduzir as consultas externas M25

O protocolo está em `m25-external-protocol.md`. Os esquemas e pedidos públicos
determinam elegibilidade, famílias e suporte; os valores aceitos entram somente
na auditoria e na avaliação. O experimento não executa as funções do BFCL nem
produz um score oficial do benchmark.

## Verificar os arquivos sem GPU ou rede

Usar o checkout Git completo e o ambiente de CPU de `REPRODUCING.md`:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/exact_commit/build_grounded_campaign.py --check
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/exact_commit/freeze_grounded_confirmation.py --check
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/exact_commit/build_live_article_results.py --grounded --check
```

O verificador reconstrói o suporte a partir de cada esquema/pedido e confere
hashes, grade completa, metadados, bytes, slots, tokens fixos, propostas
selecionadas, valores objetivos e avaliações. A reconstrução de um certificado
viável não prova sozinha que ele é ótimo: essa garantia depende do algoritmo e
dos testes independentes contra oráculos.

Sem `--check`, os scripts regeneram produtos derivados, preservando os brutos.
`build_grounded_campaign.py --partial` serve apenas para acompanhamento durante
desenvolvimento; não substitui a verificação final de todas as coortes. Os
manifests ficam em `docs/artifacts/raw/m25_grounded_v1/`. O prefixo interrompido
de desenvolvimento é uma cópia dos mesmos registros retomados, nunca uma segunda
amostra. As quatro gerações do primeiro smoke e seus motivos de interrupção
continuam registrados separadamente.

Os JSONs de componentes separam passos comprometidos de seleções finais que
falharam. Os contadores antigos omitiam seleções falhas; os novos as incluem.
Não somar esses contadores com a coluna de falhas terminais. Somas de etapas
não cobrem automaticamente todo forward tentado; o tempo total inclui todos.

## Inferência com o modelo real

Instalar o ambiente CUDA fixado e manter o snapshot local. Não executar testes,
compilação ou outra campanha pesada durante as medições. Cada campanha exige
código testado e commitado, cria uma pasta nova e registra todos os resultados:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-live/bin/python scripts/exact_commit/run_policy_screen.py \
  --config configs/experiments/m25_grounded_development_v1.json
PYTHONDONTWRITEBYTECODE=1 .venv-live/bin/python scripts/exact_commit/run_policy_screen.py \
  --config configs/experiments/m25_grounded_confirmation_v2.json
PYTHONDONTWRITEBYTECODE=1 .venv-live/bin/python scripts/exact_commit/run_policy_screen.py \
  --config configs/experiments/m25_grounded_confirmation_repeat_v2.json
```

A política secundária de orçamento é escolhida apenas no desenvolvimento:
maior número de chamadas corretas, depois menor mediana de tempo total. A
comparação primária confiança 0,8 versus EPIC 32 permanece a original. MAP,
guloso e os três schedules EPIC continuam como controles. A segunda confirmação
inverte a ordem inicial; tempos são agregados dentro de cada pedido, sem tratar
as repetições como tarefas independentes. A recuperação do EPIC pode variar
entre processos mesmo com semente fixa.

Se um processo terminar entre registros, `--resume PASTA` aceita somente um
prefixo íntegro da ordem original, configuração e suporte idênticos, mesmas
revisões/versões/hardware. Registra o commit e a reinicialização da semente por
sessão. Nunca usar retomada para repetir somente falhas ou selecionar saídas.

## Reproduzir a auditoria de dados

Os casos selecionados já estão nas configurações versionadas. Para conferir
também a regra sobre os 658 registros originais, obter os três arquivos e a
revisão descritos em `m24-reproduction.md`. Adicionar da mesma revisão de Gorilla:

`berkeley-function-call-leaderboard/bfcl_eval/data/possible_answer/BFCL_v4_simple_python.json`

Salvar como `results/raw/m25_external/simple_python_answers.json`, depois rodar:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/exact_commit/prepare_grounded_bfcl.py --check
```

Os hashes publicados em `docs/evidence/m25-grounding-coverage.json` fixam os
arquivos. A seleção conserva 68 casos, divididos em 26 de desenvolvimento e 42
de confirmação sem nomes de função compartilhados. O suporte inclui resposta
aceitável em 56/68; os doze casos ausentes não são removidos. Licença e atribuição
do conjunto público ficam em `LICENSES.md`.

## Consulta executável

[Uso da demonstração](m25-query-demo.md) descreve inferência ao vivo e replay
sem rede. Somente a demonstração despacha um GET de geocodificação após validação.
Ela registra a fonte e data da resposta; o benchmark nunca consulta APIs externas.
