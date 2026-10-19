# Arquitetura e contratos

## Biblioteca

O pacote instalado é `mwpc_exact`. Não depende de Torch nem de pesos de modelo.

- `cfg_posterior.py`: compila gramáticas LL(1) de bytes e calcula massa válida,
  marginais e amostras com aritmética inteira/racional sobre tokens originais.
- `solver.py`, `budgeted_commit.py` e `conflict_commit.py`: resolvem variantes
  explícitas de seleção MWPC; certificados são conferidos independentemente.
- `reference/`: gramáticas, reconhecimento e parsers de referência Python.
- `crates/mwpc_parser/` e `crates/mwpc_parser_py/`: parser Rust independente e
  bindings finos. São opcionais para a suíte offline do posterior.
- `epic_adapter/`: integração com o baseline, fora dos solvers genéricos.

As CLIs instaladas são `mwpc-commit-config`, `mwpc-commit` e `mwpc-sample`.
Os experimentos em `attempts/` não integram o wheel da biblioteca.

## Fluxo

```text
probabilidades/propostas + canvas + suporte + gramática + semântica dos tokens
                              |
                    inferência / seleção
                              |
                 resultado + escopo + certificado
                              |
                     validação independente
```

MWPC otimiza o peso das propostas casadas em um passo. O posterior calcula
probabilidades e amostras da predição produto congelada condicionada pela
gramática. São operações diferentes; não transfira a garantia de uma para outra.

## Fronteiras

- Preserve IDs, aliases, bytes e posições fixadas. A política EOS/PAD é explícita;
  o posterior LL(1) atual admite somente EOS ausente.
- Suporte podado só recebe `exact_on_support`. A massa omitida permanece explícita.
- Timeout e recusa por recursos não provam inviabilidade. Os limites Python são
  cooperativos; não equivalem a preempção ou teto físico de memória.
- A reutilização de planos admite mudanças compatíveis de pesos, contração do
  suporte e novos commitments. Mudanças na gramática, tokenizer, EOS, expansão
  de suporte ou liberação de posições exigem nova preparação.
- Exatidão de um passo não prova exatidão da trajetória nativa, qualidade
  semântica, velocidade ou novidade. A [verificação Lean](../formal/README.md)
  cobre apenas especificações declaradas.

## Pesquisa e dados

`attempts/` contém código e resultados por direção. `docs/artifacts/` contém
entradas e saídas científicas preservadas; `docs/evidence/` contém registros
antigos. Seus caminhos continuam estáveis para reprodução e validação de hashes.
`paper/generated/` contém derivados que não devem ser editados manualmente.
`docs/research/` guarda protocolos e leituras históricos, sem outra fila de tarefas.

O Git é o arquivo de versões. Não é necessário manter ZIPs de todo o projeto
para cada refinamento. Consulte [histórico](history/README.md) para recuperar
código retirado, protocolos antigos e snapshots anteriores.
