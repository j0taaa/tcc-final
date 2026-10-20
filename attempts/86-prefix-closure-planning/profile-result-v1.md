# Sonda de custo V1: viável, sem ganho de decoder estabelecido

O gate de viabilidade passou. Não houve geração de respostas ou seleção de
tema central. O produtor e o protocolo foram congelados em
`220be2ff4137c628dec511e4a6ac5e1695fe0f2e` antes da execução.

| Tokens totais | Batch | Mediana por forward, s | Custo por canvas / isolado |
| --- | --- | --- | --- |
| 128 | 1 | 0,065488 | 1,0000 |
| 128 | 2 | 0,100242 | 0,7653 |
| 128 | 4 | 0,158782 | 0,6061 |
| 128 | 8 | 0,288340 | 0,5504 |
| 256 | 1 | 0,101481 | 1,0000 |
| 256 | 2 | 0,159586 | 0,7863 |
| 256 | 4 | 0,287513 | 0,7083 |
| 256 | 8 | 0,517790 | 0,6378 |

B4 e B8 satisfazem o limite prospectivo de 0,75 nos dois comprimentos.
B2 não satisfaz esse limite. Cada célula contém cinco medições, com dois
aquecimentos registrados separadamente. O teste usou somente dois inputs
distintos, com linhas idênticas em cada batch; as repetições não são novos inputs.

Foram 60 forwards: 40 medidos, 16 aquecimentos e quatro referências. As ações
(posição e ID) coincidiram nas 210 linhas dos batches e nas comparações de
projeção completa versus selecionada. Todos os top-1 por slot também
coincidiram nos batches. Logits e probabilidades registrados eram finitos antes
da proibição de MASK e após softmax. Não houve recusa ou interferência CUDA
observada nas inspeções. O prompt oficial foi reproduzido por auditor CPU.

Isso não demonstra igualdade dos forwards: houve diferença máxima de 0,5 nos
logits e de 0,0305539966 na confiança. Em outros estados isso pode alterar a
próxima posição escolhida. Verificar fidelidade em trajetórias reais é uma
pendência anterior à medição de vantagem do decoder.

Carga: 58,9257 s, separada dos tempos acima. Pico Torch alocado:
6.178.455.552 bytes; reserva: 6.272.581.632 bytes. Maior observação NVIDIA:
6699 MiB. Pico Torch não é consumo total do processo ou da máquina. Construção
dos inputs e auditoria das saídas ficam fora da janela do microbenchmark;
uma avaliação de decoder precisa cobrar também esses custos.

[Dados completos](profile-v1.jsonl), SHA-256
`4b588d2904b8d3b5e63779d58adde6945b620f412cee53830458a5017f4476bf`.
Uma auditoria independente por subagente conferiu hashes de commit/fontes,
prompt, contagens, tempos, gate e campos numéricos sem executar GPU.

## Verificação CPU do planejador

`planner.py` implementa o objetivo local por cortes com capacidades inteiras e
razões racionais. Sua auditoria passou em 240 famílias e 5.124 células/fronteiras
de preço. Um subagente executou adicionalmente um oráculo zeta independente em
400 casos, incluindo múltiplos obrigatórios, repetições, caminhos vazios,
outsiders, pesos de 180 bits e custos de 150 bits. Não encontrou defeito material.
São verificações finitas; não constituem prova formal nem prioridade científica.

```bash
.venv-live/bin/python attempts/86-prefix-closure-planning/planner.py --audit
```

Para uma nova execução da sonda, preserve os dados V1 e use outro caminho:

```bash
.venv-live/bin/python attempts/86-prefix-closure-planning/profile_v1.py \
  --output /tmp/a86-new-profile.jsonl
```

O resultado autoriza apenas preparar o próximo gate delimitado. Prioridade,
contribuição suficiente e utilidade de geração permanecem abertas.
