# A89 — Capacidade em tokens e expansão gramatical

Investigação prospectiva iniciada em 23/10/2026 nesta worktree. Não reabre A19,
A28 ou A36. Não afirma novidade da combinação CFG + expansão + GPU.

**Piloto concluído, não selecionada como contribuição central.** 48 decodes
VAL + 336 TEST reais; zero acerto funcional em todos os métodos. Verificador
CPU: 1,44% do decode adaptativo VAL, sem justificativa para kernel próprio.
Fatorial CPU/Torch CUDA concluído; 96 pares com IDs/decisões/expansões idênticos,
sem vantagem integral e com menor validade adaptativa. Leia a
[conclusão e limites](result.md). O zero neural geral não refuta toda abordagem
de expansão; este decoder não foi qualificado para utilidade.

Leia `protocol-v1.md`, `mechanism.md`, `sources.md` e, depois da execução,
`result.md`. Os dados novos ficam em `evidence/`; modelo e ambiente existentes
são reutilizados explicitamente. Nenhuma captura neural antiga é avaliação nova.

Entrega local revisável; sem publicação ou PR. Comandos em `reproduce.sh`.
