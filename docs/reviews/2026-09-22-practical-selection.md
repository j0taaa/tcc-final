# Vantagem prática e redução de código

**Registro histórico, revisto pela [auditoria posterior](2026-09-22-selection-audit.md).**
O comparador com reaproveitamento de testemunha reduz bastante o ganho de tempo;
o caso de maior pontuação não melhora o cumprimento do prompt. As afirmações
abaixo descrevem a comparação original, não uma vantagem prática geral.

O uso demonstrado é selecionar um lote de propostas com certificado de
compatibilidade no suporte finito. A seleção simultânea evita reconstruir e
consultar o parser para cada tentativa de aceitação do seletor sequencial.
Isso é útil quando essa verificação sequencial é o custo a substituir.

O experimento foi congelado no commit
`3d573b2c8ea2312b681f81108abaa11f8a497d3f`, com a configuração
[`m18_batch_selection_v1.toml`](../../configs/experiments/m18_batch_selection_v1.toml).
Foram usados todos os 24 estados já salvos dos 12 prompts de confirmação,
sem inserir respostas conhecidas. Cada posição livre propõe seu primeiro token
permitido, com a probabilidade original sobre o vocabulário completo.
Os orçamentos são de até 2, 8 e 32 propostas; K=2,4,8; três repetições em
processos novos, alternando a ordem dos métodos. Ambos recebem exatamente
o mesmo estado, suporte e propostas. O limite é de um segundo por seleção.

As medianas de ganho de tempo, variando K, foram 2,4–2,6 vezes para orçamento
2; 4,9–6,5 para orçamento 8; e 4,5–15,9 para orçamento 32. Primeiro se toma a
mediana das razões das repetições em cada estado, depois entre estados.
As razões incluem apenas pares concluídos: os casos difíceis que atingiram
o limite permanecem nos denominadores dos resultados de execução, mas não
recebem um tempo de conclusão inventado.

Das 648 execuções de cada método, o exato retornou 540 ótimos e 108 resultados
de inviabilidade no suporte, sem timeout. O sequencial retornou 464 soluções
viáveis, 108 inviabilidades e 76 timeouts. As 1.296 linhas estão no
[`arquivo bruto`](../artifacts/raw/m18_batch_selection_v1/), com configuração,
commit, metadados da máquina, certificados e hashes dos 24 estados de entrada.
O [resumo gerado](../../paper/generated/m18_batch_selection_v1/summary.json)
mostra separadamente as nove combinações de K e orçamento.

Houve uma condição com ganho de pontuação, repetida nas três execuções:
`confirm-brackets-3-170302-capture-forward0`, K=4, orçamento 32. O exato
reteve 31 propostas e obteve 14,318663361719748; o sequencial reteve 30 e
obteve 14,203307921409227. O solver Python independente confirmou o ótimo
encontrado pelo Rust, e o caso entrou na suíte de testes. Os demais pares
concluídos empataram. Isso demonstra um caso real de perda da escolha gulosa;
não estima a frequência dessa perda em novos prompts.

O comparador é `greedy_exact_feasibility`, que reconstrói o problema em cada
consulta; não usa parsing incremental. Os tempos incluem lattice, parser e
validação do certificado, mas excluem inferência do modelo, extração top-K
e construção do suporte comum. Esta não é uma medição de aceleração sobre
o EPIC na geração completa. Os resultados negativos da avaliação ao vivo
continuam no artigo. São medições descritivas em uma máquina, com 12 prompts;
estados, larguras e repetições não constituem novas amostras independentes.

A manutenção ficou menor: comparado ao início desta alteração (`a309b1c`),
`src/`, `scripts/`, `tests/` e `crates/` tiveram 261 linhas adicionadas e 966
removidas, saldo de **705 linhas a menos**. Foram retirados três executores
experimentais e geradores de coortes sem uso. A versão `v0.2.0` preserva o
código histórico para reproduzi-los; as evidências, os oráculos e os testes
das baselines permanecem. Os testes de separação de coortes agora verificam
os registros realmente arquivados. A validação de IDs também deixou de
chamar uma função por token, e a consulta de posições fixas usa um conjunto
em vez de percorrer repetidamente o vocabulário.

Validação: `python -m pytest -q` passou 839 testes; `make test-rust-parser`
passou 24 testes, formatação e Clippy; Ruff e MyPy passaram. Os testes
originais do EPIC passaram 19 casos, com quatro skips preexistentes.
`build_review_results.py --check` reproduziu os resultados históricos.
As 1.296 linhas, os hashes de entrada, a configuração no commit produtor e
o resumo foram verificados. `make paper` gerou 18 páginas, sem referências
indefinidas ou caixas excedendo as margens; as páginas alteradas e seu entorno
foram inspecionados visualmente. LAVE permaneceu fora das alterações.
