# Reprodução do piloto neural V2

Os fontes de captura e seu protocolo foram congelados no commit
`451de4199be5f9884d4c84e886862f314880b571`, depois da conclusão dos controles
compactos e antes dos novos forwards. O produtor usa as probabilidades
binary64 representadas após backbone FP32/sigma0 e softmax CPU, normalizadas
exatamente pelo solver. Não é a distribuição nativa condicionada da MDLM.

Com os caches originais e o ambiente pinado, o comando realmente executado foi:

```bash
HF_HUB_OFFLINE=1 OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 .venv-live/bin/python -m attempts.24-certified-depth-approximation.work.consumer_v2.neural --input .cache/a24-independent-cuda-v1 --development-decision attempts/24-certified-depth-approximation/work/evidence/consumer-v2-development/decision.json --compact-decision attempts/24-certified-depth-approximation/work/evidence/consumer-v2-compact/decision.json --output .cache/a24-consumer-v2-neural-v1
.venv/bin/python -m attempts.24-certified-depth-approximation.work.consumer_v2.analyze_neural --input .cache/a24-consumer-v2-neural-v1 --original .cache/a24-independent-cuda-v1
.venv/bin/python -m attempts.24-certified-depth-approximation.work.consumer_v2.report_neural --input attempts/24-certified-depth-approximation/work/evidence/consumer-v2-neural-v1
```

O runner recusa sobrescrever a pasta de saída; uma repetição precisa de outro
nome. Não atribuir a uma nova execução os hashes ou tempos originais.

Uma nova captura não precisa dos heads antigos: os inputs usados pelo runner
estão publicados integralmente em
`attempts/24-certified-depth-approximation/work/evidence/consumer-v2-neural-v1/initial-inputs`.
Esse caminho pode substituir `--input` no runner e `--original` no auditor,
usando outra pasta em `--output`. Ainda exige o checkpoint pinado, o ambiente
Torch/CUDA declarado e novos forwards; uma nova captura não é reprodução
offline das matrizes históricas.

`work/evidence/consumer-v2-neural-v1/` contém o journal completo de custos,
probabilidades/certificados declarados, amostras e transições, metadados,
inventário de hashes das matrizes, inputs iniciais/tokenizer, logs de execução,
auditoria e preflight, ambiente e decisão gerada. `report_neural.py` foi criado
DEPOIS da captura para apresentar o JSON da decisão, sem modificar seu gate.
`preservation.json` identifica o alcance adicional das verificações locais.

Os1.345 arquivos completos de probabilidades (3.430.582.208 bytes) permanecem
em `.cache/a24-consumer-v2-neural-v1/heads`. Os bytes dessas matrizes não estão
publicados neste suplemento. O journal permite auditar a decisão, os tokens
e as desigualdades com as massas registradas; conferir os próprios pesos ou
recalcular os solvers exige esses arrays ou novos forwards pinados. Não se
alega reprodução numérica offline integral a partir de hashes.

A demonstração mínima já usa o pacote público anterior, sem modelo/Torch/GPU:

```bash
.venv/bin/python -m attempts.24-certified-depth-approximation.work.consumer_v2.demo --packet attempts/24-certified-depth-approximation/work/evidence/first-full-head-v2/packet.zip
```

Seu resultado está em `public-demo.json`: é demonstração funcional em UM
head antigo e não integra o gate nem as contagens de novos forwards.

O custo quente inclui cada forward/softmax, captura da matriz e hash, IPC,
consulta, amostra, confiança, reconhecimento e construção da saída. Exclui
preparação única de modelo/serviço, reportada separadamente. Os totais a frio
reconstroem essa preparação medida; não foram executadas sessões frias
independentes. Escrita do journal e encerramento/reset do serviço seguem a
fronteira do pedido medido, portanto os custos de recusa são custos medidos
do pedido, não uma medição completa do ciclo de vida do processo.

Sob recursos conclusivos, a prova escrita do kernel continua aplicável.
Timeouts/recusas gerenciados produzem FAIL e podem selecionar saídas por custo;
validade ou bounds nos sucessos não certificam sua lei incondicional. O piloto
não mede qualidade semântica, independência de corpus ou superioridade geral.
