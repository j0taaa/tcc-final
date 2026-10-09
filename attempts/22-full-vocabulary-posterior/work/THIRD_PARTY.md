# Dependências do experimento

- MDLM OWT e os kernels oficiais pinados permanecem Apache-2.0, conforme a
  atribuição de `scripts/exact_commit/mdlm_cpu.py` e do inventário existente.
  O port PyTorch usa rearrangement/rotary/SDPA e não afirma igualdade bit a bit
  com FlashAttention. Pesos não são versionados.
- JSON-Schema-Test-Suite, revisão
  `5b0ee1613e45fcc2bddac00e07c19cd49b00d8a8`, MIT. Os arquivos fonte selecionados
  e a licença original ficam em `evidence/external-source/`; não foram escolhidos
  pelos resultados dos métodos. São documentos externos de teste JSON, não
  requisições de produção nem uma avaliação oficial de JSON Schema.

As dependências anteriores do repositório mantêm seus pins e atribuições.
