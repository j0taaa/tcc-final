# Reprodução

Execute os comandos na raiz do checkout. Use Python 3.11; os pins estão em
`pyproject.toml`, `requirements/` e nos lockfiles Rust. Modelos e GPU são opcionais.

## Uso cotidiano

```bash
make setup
make check
make demo
```

`setup` cria `.venv` e instala as dependências de desenvolvimento pinadas.
`check` verifica o snapshot EPIC, lint/formatação, tipos e os testes independentes.
`test` executa somente a suíte. Os testes usam fontes de `attempts/` e dados
versionados: rode-os no checkout completo, não a partir de um wheel isolado.
Não há download de modelo nem execução neural nesses comandos.

`demo` lê o pacote público em
`attempts/24-certified-depth-approximation/work/evidence/first-full-head-v2/packet.zip`.
Ele audita probabilidades/bytes e retorna JSON, tokens originais e certificado.
Reproduz inferência sobre uma captura, não um novo forward do backbone.

## Verificações opcionais

| Comando | O que verifica |
| --- | --- |
| `make rust` | Formatação e Clippy do parser e dos bindings Rust |
| `make formal` | Especificações Lean, auditoria de axiomas e exemplo canônico |
| `make evidence` | Integridade dos artefatos preservados e derivados do artigo |
| `make paper` | Evidências e compilação LaTeX do artigo, com checagem do PDF |
| `make format` | Formatação e correções automáticas de lint no código mantido |
| `make clean` | Produtos de build e caches das ferramentas de desenvolvimento |

Para instalar os bindings Rust na `.venv`, use `make setup-rust`.
`make setup-epic` instala o ambiente CPU opcional do baseline.
O snapshot e sua verificação estão descritos em [upstream.md](upstream.md).
As integrações de modelos têm perfis separados em `requirements/`; sua instalação
não transforma uma campanha antiga em uma nova medição.

Rust usa `rust-toolchain.toml`. Lean usa `formal/lean-toolchain`; instale esse
toolchain via Elan antes de `make formal`. Se necessário:

```bash
make formal LAKE="$HOME/.elan/bin/lake"
```

O artigo requer `pdflatex`, `bibtex` e `pdfinfo`. O PDF sai em `paper/main.pdf`.
O suplemento semântico histórico pode ser compilado diretamente com
`make -C paper research-note`.

## Alcance das evidências

`make evidence` confere o inventário histórico de artefatos, os certificados M31,
os resultados M34, os dados do certificado de profundidade e a tabela semântica.
Esses verificadores não reexecutam todas as campanhas, modelos ou timings e não
estabelecem novidade. A fronteira formal está em [formal/README.md](../formal/README.md).
Dados brutos e resultados negativos continuam nos caminhos originais.

Os grandes logits e modelos permanecem em caches locais ignorados. O pacote
público permite verificar uma captura completa; os demais hashes não substituem
arquivos indisponíveis. A checagem opcional dos logits locais continua disponível:

```bash
.venv/bin/python -m scripts.exact_commit.check_cfg_model_capture \
  --capture results/raw/m34_cfg_posterior_v1/json-model
.venv/bin/python -m scripts.exact_commit.build_probability_audit_results \
  --check --capture results/raw/m31_probability_v1/capture
```

Para reconstruir campanhas antigas, use o commit produtor e um novo diretório
de saída. Não use o código atual para atribuir novos timings a um resultado antigo.
Protocolos e comandos específicos estão na tentativa correspondente; as versões
anteriores da documentação podem ser recuperadas pelo [Git](history/README.md).

## Distribuição

```bash
.venv/bin/python -m build --no-isolation
```

O wheel contém a biblioteca. Dados brutos de campanhas e diretórios de tentativas
não fazem parte dele. As demonstrações e a reprodução do artigo exigem o checkout.
