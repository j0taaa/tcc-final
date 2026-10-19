# Verificação Lean

O toolchain está fixado em `lean-toolchain`; o projeto usa somente a biblioteca
padrão de Lean. Instale esse toolchain via Elan e execute, na raiz:

```bash
make formal LAKE="$HOME/.elan/bin/lake"
```

O comando falha se o toolchain não estiver disponível. Compila as especificações,
audita as dependências dos teoremas e verifica o exemplo canônico de certificado.
Não instala ferramentas silenciosamente nem executa modelos.

## O que é mecanizado

| Módulos | Escopo |
| --- | --- |
| `Certificates`, `Bounds`, `Selection`, `Prefixes` | Limites de recompensa, certificados de ótimo/inviabilidade e propriedades das representações declaradas |
| `Conflicts` | Coberturas de busca e transporte de conflitos sob hipóteses explícitas |
| `Probability`, `CfgSampling` | Identidades de massa, limites de erro, suporte e especificações selecionadas do posterior |
| `SemanticProfiles`, `AdaptiveSemantics` | Resultados algébricos e de contagem para as classes de planos/refinamentos declaradas |
| `ExactEnvelope`, `CertifiedAmplification` | Especificações de contagem, rejeição finita e reponderação |
| `StratifiedBatches` | Aritmética de tickets e desigualdades selecionadas de dois estratos |

Os arquivos `Audit*.lean` imprimem dependências. O verificador em
`scripts/exact_commit/check_formal_project.py` enumera os enunciados exigidos.
Não se usam admissions nem axiomas próprios para substituir demonstrações.

## Fronteira de confiança

Os teoremas têm premissas explícitas sobre gramáticas, grafos, potenciais,
cobertura e contagens. O exportador emite construções rechecadas pelo kernel.
O verificador Python liga um certificado aos tokens originais, bytes, propostas,
posições fixadas, suporte e EOS/PAD. Essa correspondência não foi universalmente
provada como refinamento do código Python/Rust.

Lean não verifica a implementação completa do lexer, normalizador, compilador,
inside/outside, RNG, FFI, tokenizer ou modelo. Também não comprova timings,
prioridade científica, qualidade semântica nem a trajetória nativa do modelo.

A cobertura da fronteira de fechamento, a família de separação do artigo e as
leis gerais de trajetória/amostragem indicadas nas tentativas continuam provas
escritas. Aritmética mecanizada de um limite de erro não mecaniza o argumento
probabilístico inteiro. Testes independentes são evidência complementar.

Um certificado pequeno de conflitos foi verificado em Lean; a tentativa de
exportar um replay de 75 nós excedeu o prazo de 180 segundos. O registro em
`docs/evidence/m29-concrete-conflicts-lean.json` preserva essa limitação. Não se
atribui verificação Lean a todos os certificados grandes.

## Exemplo portátil

```bash
.venv/bin/python scripts/exact_commit/budget_math_example.py \
  --verify docs/artifacts/math/m27-budget-proof.json --lean
```

O JSON contém a entrada e os testemunhos. `examples/BudgetExample.lean` é a
exportação versionada. Consulte o [histórico](../docs/history/README.md) para
os comandos e resultados de versões anteriores, incluindo a suíte retirada.
