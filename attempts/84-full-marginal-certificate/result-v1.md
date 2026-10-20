# V1 — Regra mais rápida, com perda de acurácia; candidata não selecionada

Produtor e protocolo congelados em `c6358537c6a15d1e4cc12616eefb627c41148201`
antes da execução. O [contrato original](README.md) permanece inalterado.
Comando executado uma vez:

```sh
.venv-live/bin/python attempts/84-full-marginal-certificate/pilot.py \
  --output attempts/84-full-marginal-certificate/pilot-v1.jsonl
```

Os [dados completos pequenos](pilot-v1.jsonl), SHA256
`401109066383e3b80384ae3ab605ca7b7e7ab5bb29d1e7501bbac8729e1896eb`,
preservam as perguntas, golds, versões, IDs originais finais, contagens de seleção,
forwards, tempos e avaliações. Os datasets integrais ficam no cache ignorado.
Não há pesos ou grandes heads versionados.

## Resultado do gate prospectivo

Foram concluídos 64/64 decodes pontuados, sem erro, recusa, interrupção ou
truncamento. Não foram observados outros processos CUDA nas inspeções
antes/depois de cada decode. Essas inspeções não excluem interferência transitória.

| Família | Fréchet: acertos únicos | Runner-up: acertos únicos | Tempos somados F / R, s | R/F | Forwards F / R |
| --- | --- | --- | --- | --- | --- |
| GSM8K, 8 perguntas | 5/8 | 4/8 | 148,980 / 135,990 | 0,912806 | 950 / 864 |
| BBH word_sorting, 8 perguntas | 1/8 | 0/8 | 49,266 / 43,287 | 0,878654 | 314 / 276 |

Tempos/forwards somam duas ordens de execução; **não são 16 exemplos
independentes por família**. Os 32 pares método/pergunta tiveram IDs finais,
NFEs, scores e traços de seleção registrados idênticos entre as repetições.
A queda de um acerto único
em cada família se repetiu. Mantém-se o avaliador original, sem reclassificar
respostas para salvar o gate. A baixa acurácia em word_sorting também impede
interpretar sua redução de tempo como uma solução útil para essa tarefa.

O gate exigia R/F<=0,90 e nenhuma perda líquida de acertos em **ambas** as
famílias. Falhou: matemática não atingiu o tempo exigido; ambas perderam
acurácia. A regra economizou 8,72% e 12,13% de parede nesta pequena aplicação,
mas isso não basta para o benefício solicitado. **Este piloto está encerrado;
não selecionar A84 como tema central nem trocar subset/margem para resgatá-lo.**

Carga/quantização levou 73,277 s, reportada separadamente de pedidos. Os
aquecimentos consumiram nove forwards; decodes pontuados, 2.404. Pico de
memória de tensores reportado pelo Torch: 5.836.982.272 bytes, aproximadamente
5,44 GiB; não é medição de todo o contexto CUDA ou do pico de RAM do sistema.
Todos os decodes ocorreram na RTX3080Ti12GB com o mesmo snapshot/NF4/BF16.
Os tempos por pedido incluem tokenização, modelo, softmax, seleção/top-2,
sincronização, finalização e detokenização. O monitor de processos e o arquivo
de instrumentação ficam fora desse tempo e não simulam custo de serving.

## O que permanece matematicamente válido

Os oráculos racionais passaram em 9.702 perfis marginais e 35 tabelas
conjuntas, além do contraexemplo explícito E>1. O certificado local e o teto
de um token extra continuam corretos sob as hipóteses declaradas. Não
estabelecem qualidade semântica, coerência das condicionais neurais ou ganho
global. O resultado negativo é precisamente uma razão para separar essas
afirmações.

Uma revisão independente por subagente revalidou hashes, seleção input-only,
16 golds, 64 detokenizações pelo tokenizer oficial em CPU, scores, repetições,
EOS/EOT/MASK, contagens e agregados. Não executou novo forward ou GPU e não
constitui revisão humana/acadêmica. Lint/formatação focalizados e a integridade
do baseline preservado também passaram; nenhuma API mantida foi alterada.

A auditoria por subagentes não encontrou a regra exata nos antecedentes
primários examinados, mas identificou uma origem **exata**, não apenas
análoga, para a lei extremal de erro único: [Dhaene–Denuit, 1999, definição 6
e teoremas 7–8](https://jandhaene.org/wp-content/uploads/2025/10/1999-dhaene-denuit.pdf).
Renomear o argmax como zero dá a distribuição mutuamente exclusiva
concentrada nos eixos sob sum e<=1. Assim, a prova de sharpness aplica um
acoplamento conhecido. O contexto dos limites de células é clássico em
[Dobra–Fienberg, 2000](https://sites.stat.washington.edu/adobra/Files/Papers/pnas.pdf).
Não se reivindica invenção dessas ferramentas, prioridade global, revisão
humana ou validação Lean. A especialização modal e o seletor são candidatos
estreitos; a evidência prática obtida não justifica promovê-los.
