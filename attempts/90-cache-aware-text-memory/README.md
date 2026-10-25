# A90 — Memória textual incremental com custo de cache

Investigação independente, iniciada em 2026-10-23 na worktree
`research/cache-aware-memory-20261023`. Não altera campanhas antigas nem A89.
A hipótese é prospectiva; memória incremental dLLM → AR, compressão por difusão,
seleção de regiões e preservação de prefix cache não são novidades presumidas.

- `novelty.md`: fontes primárias, colisões e fronteira da contribuição.
- `protocol-v1.md`: contrato congelado antes do primeiro forward desta tentativa.
- `pilot.py`, `prepare.py`, `reproduce.sh`: execução local sem treinamento.
- `data/`: entradas sem perguntas futuras para o compressor e avaliação separada.
- `evidence/`: manifests, saídas brutas, custos e verificações.
- `result.md`: conclusão depois da execução, inclusive negativos.

Modelo dLLM existente: LLaDA-8B-Instruct, NF4; AR disponível sob restrição de disco:
Qwen2.5-3B-Instruct, checkpoint NF4 publicado por Unsloth. Pesos congelados.
Comparações são destes sistemas concretos, não uma comparação controlada apenas
pela arquitetura. Nenhum compute pago, pós-treino, publicação ou PR.
