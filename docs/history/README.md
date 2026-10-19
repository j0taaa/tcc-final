# Histórico e recuperação

A reorganização retirou da árvore atual documentos de entrada redundantes,
três módulos sem consumidores e os snapshots sem consumidores. As fontes,
os dados científicos, os testes e os resultados negativos continuam nos caminhos
usados pela reprodução. O Git mantém as versões retiradas.

Guias de fases encerradas, cópias antigas de tarefas, notas de releases/reviews
e PDFs compilados também saíram da árvore versionada. Não são requisitos para
os verificadores atuais. Os PDFs locais ficam ignorados em `output/`.

## Checkout anterior à simplificação

Commit: `9b097865ec300ed853a584238a3040b98714a8d5`.

```bash
git worktree add --detach /tmp/tcc-history 9b097865ec300ed853a584238a3040b98714a8d5
```

Esse checkout contém os antigos `AGENTS.md`, `TASKS.md`, `REPRODUCING.md`,
`START_HERE.md`, `IMPLEMENTATION_PLAN.md` e o mecanismo de snapshots.
Os ZIPs e manifests ocupavam 905 arquivos e 5.060.638.460 bytes. Foram retirados
903 arquivos (5.056.499.141 bytes). Permanecem somente o `source.zip` e o manifesto
de `attempts/23-canonical-epsilon-posterior/v2/`: os testes A24/A25 usam essa
fixture como controle independente com hashes fixados.

A redução é da árvore de trabalho; não reescreve nem reduz o histórico `.git`
existente.

No checkout antigo, `make attempts-check` ainda valida os 70 diretórios
catalogados e suas 279 versões. O catálogo completo de commits produtores está
em `attempts/catalog.json` naquele commit; o [índice atual](../../attempts/README.md)
resume as conclusões por direção. Não se exige uma nova cópia ZIP por alteração.

Para recuperar um arquivo isolado sem alterar a árvore atual:

```bash
git show 9b097865ec300ed853a584238a3040b98714a8d5:REPRODUCING.md
git show 9b097865ec300ed853a584238a3040b98714a8d5:attempts/catalog.json
```

Os módulos retirados por ausência de consumidores eram `mwpc_exact.mass_solver`,
`mwpc_exact.proof_reuse` e `mwpc_exact.probabilistic_update`. Suas versões
permanecem nesse commit. As CLIs e os solvers utilizados continuam mantidos.

## Interpretação

Registros antigos conservam datas, contagens e comandos da sua versão. Eles não
substituem o [estado atual](../status.md). Medições antigas pertencem ao código
produtor; reproduzir um certificado não equivale a repetir um experimento.
Não recrie filas de trabalho a partir de marcos encerrados.
