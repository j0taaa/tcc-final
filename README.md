# Inferência gramatical para modelos de linguagem

Biblioteca de inferência exata sobre tokens finitos: posterior condicionado por
uma gramática, seleção de compromissos e validação de certificados. O repositório
também contém o artigo e as fontes das investigações realizadas durante o TCC.

## Começar

Use Python 3.11. Na raiz do repositório:

```bash
make setup
make check
```

`make check` verifica o baseline preservado, lint, tipos e a suíte de testes
independentes. Funciona sem modelo, GPU ou acesso à rede depois da instalação.
`make` mostra os demais comandos.

Para executar um exemplo com probabilidades reais já capturadas:

```bash
make demo
```

O exemplo usa um pacote público local; não baixa nem executa um modelo.

## Estrutura

| Diretório | Responsabilidade |
| --- | --- |
| `src/mwpc_exact/` | Biblioteca Python e referência independente |
| `tests/` | Testes e oráculos offline |
| `crates/` | Parser Rust e bindings Python opcionais |
| `paper/` e `formal/` | Artigo LaTeX e especificações Lean |
| `scripts/` | Verificação e reprodução |
| `attempts/` | Fontes e resultados das investigações, fora da biblioteca |
| `docs/` | Estado atual, arquitetura, reprodução e evidências |
| `vendor/` | Baseline EPIC com origem e hashes preservados |

Os caminhos dos dados científicos continuam estáveis porque são usados por
testes, manifests e verificadores. Snapshots ZIP duplicados foram retirados da
árvore atual, exceto uma fixture usada pelos controles independentes. O
[histórico](docs/history/README.md) explica a recuperação pelo Git.

## Situação da pesquisa

A contribuição científica própria e útil ainda está em aberto. O artigo A24
registra um ganho histórico de consulta em 3/15 estados sob seus comparadores
originais; uma comparação operacional posterior falhou em todos os 15 estados
contra controles mais fortes. A investigação mais recente, A72, tem uma prova
escrita de limite de representação sob aproximação para uma GLC fixa. Sua
prioridade e relevância científica continuam em avaliação; não há ganho neural
estabelecido.

Veja o [estado atual](docs/status.md) e as [pendências](TASKS.md). Testes de
correção e integridade de arquivos não comprovam novidade nem benefício prático.

## Referências do projeto

- [Reprodução e comandos](docs/reproducing.md)
- [Arquitetura e contratos](docs/architecture.md)
- [Índice das investigações](attempts/README.md)
- [Artigo](paper/README.md) e [fronteira da verificação formal](formal/README.md)
- [Instruções para alterações](AGENTS.md)

O software original usa a [licença MIT](LICENSE). As condições do manuscrito e
as atribuições de terceiros estão em [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).
