# Start here — AI agent handoff

Antes de qualquer implementação, execute:

```bash
python scripts/materialize.py
git submodule update --init --recursive
make bootstrap
source .venv/bin/activate
make check
```

Depois da materialização, leia integralmente `AGENTS.md` e `UPSTREAM.md`. Em `TASKS.md`, comece por `T000` e avance estritamente em ordem de dependência.

Não marque tarefas como concluídas apenas porque arquivos existem: execute os critérios de aceitação e registre evidências. Não altere `vendor/EPIC-Decoding` diretamente, não chame top-K de ótimo global, não confunda timeout com inviabilidade e não preencha resultados do artigo sem artefatos reproduzíveis.
