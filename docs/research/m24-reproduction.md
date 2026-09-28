# Reproduzir a campanha M24

A campanha compara políticas durante geração real com LLaDA-8B-Instruct NF4.
Não é uma execução de reparo JSON sem modelo. A análise e os testes de CPU não
baixam pesos nem acessam APIs externas.

## Verificar os resultados preservados

Com o ambiente de CPU e o parser Rust instalados conforme `REPRODUCING.md`:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/exact_commit/build_policy_campaign.py --check
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q
PYTHONDONTWRITEBYTECODE=1 make test-upstream
make test-rust-parser
```

O primeiro comando verifica hashes, configurações, células completas, suporte
construído sem gabarito, escores, preservação de tokens fixos, certificados e
avaliação das saídas; depois reproduz todas as tabelas e intervalos. Remover
`--check` regenera os produtos em `docs/research/generated/m24-*`.
A verificação dos certificados estabelece validade e consistência dos escores;
a garantia de ótimo depende do algoritmo e dos testes diferenciais contra
oráculos, não apenas de observar um certificado viável.

Os arquivos brutos estão em `docs/artifacts/raw/m24_policy_v1/`, com gzip
sem perda e manifests SHA-256. O inventário gerado registra os commits produtores
e o comando exato de cada coorte. São 12 coortes; os nomes de políticas repetidos
entre desenvolvimento e confirmação não representam métodos novos.

## Executar inferência novamente

Usar o ambiente CUDA fixado e o snapshot local configurado. Rodar uma campanha
por vez, sem testes pesados concorrentes, a partir de uma árvore Git limpa:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-live/bin/python scripts/exact_commit/run_policy_screen.py \
  --config configs/experiments/m24_policy_development_v1.json
```

Substituir a configuração pelas demais listadas no inventário gerado. Cada
execução cria uma pasta nova em `results/raw/`; nunca sobrescreve a evidência
arquivada. Para reproduzir historicamente um resultado, usar seu commit produtor
em outro checkout e o respectivo ambiente fixado. O driver atual pode conter
correções de metadados posteriores, documentadas no relatório.

O mesmo modelo, tokenizer, quantização e semente são usados entre comparadores.
As ordens rodam por pedido e a segunda execução inverte a lista inicial.
Carregamento do modelo fica fora dos tempos por pedido; preparação, seleção,
inferências e recuperação oficial do EPIC ficam dentro. Há dois warmups.
O EPIC pode escolher outra recuperação válida entre processos: repetir a semente
não garante identidade dessas escolhas. Guardar todas as saídas de cada rodada.

Não somar as duas repetições como se fossem 200 pedidos distintos. O relatório
pareado usa uma observação de acurácia por pedido na primeira rodada, reporta
ambas as rodadas e agrega dois tempos por pedido antes do bootstrap. A comparação
primária foi congelada antes da confirmação; ablações e schedules adicionais são
secundários e não recebem ajuste por multiplicidade.

## Reconstruir a auditoria externa

Os oito exemplos de esquemas finitos e suas respostas públicas estão nas
configurações. A auditoria completa usa arquivos públicos da revisão
`6ea57973c7a6097fd7c5915698c54c17c5b1b6c8` de `ShishirPatil/gorilla`:

- `berkeley-function-call-leaderboard/bfcl_eval/data/BFCL_v4_simple_python.json`;
- `berkeley-function-call-leaderboard/bfcl_eval/data/BFCL_v4_live_simple.json`;
- `berkeley-function-call-leaderboard/bfcl_eval/data/possible_answer/BFCL_v4_live_simple.json`,
  salvo localmente como `possible_answer.json`.

Colocar os três arquivos em `results/raw/m24_external/bfcl/`, com a revisão em
`revision.txt`, e executar:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/exact_commit/prepare_bfcl_enum_pilot.py --check
```

O comando reproduz a seleção de oito entre 658 casos a partir dos esquemas e
verifica os hashes publicados em `docs/evidence/m24-bfcl-coverage.json`.
O gabarito é associado depois da elegibilidade; não fornece domínios de geração.
Licença e atribuição: `LICENSES.md`. O avaliador é próprio e estrito, não o score
oficial BFCL. Nenhuma função/API externa é executada pelo experimento.
