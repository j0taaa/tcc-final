# Exact CFG-Constrained Parallel Commitment for Diffusion Language Models

Repositório definitivo e privado do TCC **Exact Maximum-Weight Parallel Commitment for CFG-Constrained Diffusion Language Models**.

Este repositório contém um bootstrap verificado do workspace completo, o artigo SBC em LaTeX, `AGENTS.md`, o backlog científico `TASKS.md`, testes, CI e o EPIC fixado como baseline imutável.

## Preparar o workspace

```bash
git clone --recurse-submodules https://github.com/j0taaa/tcc-final.git
cd tcc-final
python scripts/materialize.py
git submodule update --init --recursive
make bootstrap
source .venv/bin/activate
make check
```

A materialização baixa o snapshot de origem por um commit imutável, verifica seu SHA-256 e expande o projeto neste repositório. Depois, revise `git status` e faça um commit da árvore expandida.

## Instrução inicial para o agente

```text
Leia START_HERE.md, AGENTS.md, UPSTREAM.md e TASKS.md. Comece na T000 e
continue em ordem de dependência. Não pule gates de correção. Atualize
checkboxes e campos Evidence somente depois de executar os testes exigidos.
Não invente benchmarks nem preencha placeholders dependentes da implementação.
Mantenha vendor/EPIC-Decoding somente leitura; implemente o método novo nos
módulos próprios e integre ao EPIC por adapters.
```

Nenhum resultado científico ou benchmark é reivindicado no bootstrap.
