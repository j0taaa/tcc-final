# A86 — Gate V2 de fidelidade numérica em trajetórias reais

Congelar este protocolo e `fidelity_v2.py` em commit antes da execução.
O perfil V1 produzido pelo commit `220be2ff` escolheu B8 antes destes dados.
Este gate mede fidelidade dessa configuração, sem avaliar qualidade ou aceleração.
Não alterar B, comprimentos, prompts, desempates ou paradas depois dos resultados.

## Configuração e entradas fixas

- RTX 3080 Ti de 12 GB; recusar antes da carga com menos de 7 GiB livres ou
  outro processo CUDA de computação. Inspecionar processos antes/depois de cada
  forward; interferência observada interrompe com recusa inconclusiva.
- Mesmo snapshot local LLaDA-8B-Instruct do perfil V1:
  `08b83a6feb34df1a6011b80c3c00c7563e963b07`; NF4, double quantization, BF16,
  quatro threads, seed Torch 86002, `eval`, `inference_mode`, `use_cache=False`.
  Nenhum download, treinamento ou cache KV. Registrar versões e hardware.
- Template de chat oficial, sem truncamento. Canvas total fixo de 256 tokens;
  após os `P` tokens do prompt, 128 posições elegíveis à geração, em blocos de
  32. Exigir `P+128≤256`. O restante permanece MASK e é visto pelo transformer.
- Prompts, nesta ordem, sem seleção posterior:
  1. `Write a Python function that merges two sorted lists. Include a short explanation.`
  2. `Write a Python function that returns the longest common prefix of a list of strings. Explain its complexity.`
  3. `Explain why hash tables can have collisions and how chaining resolves them. Give a concrete example.`
  4. `Explain the difference between a stack and a queue, with one practical example for each.`

## Captura serial B1

Executar os quatro casos, até 64 eventos por caso. O bloco ativo é o primeiro
bloco de 32 ainda incompleto. Projetar seus 32 estados ocultos, mantendo todas
as 256 posições no transformer. Converter logits para FP32, verificar finitude,
proibir MASK 126336 e aplicar softmax FP32. Para cada posição, usar token argmax;
ordenar posições por confiança decrescente, estável em posição crescente,
excluindo posições já reveladas. O evento é posição global e ID original.

Após cada evento, parar na primeira ocorrência segura de EOS 126081 ou EOT
126348: todo o prefixo gerado anterior a esse terminal deve estar sem MASK.
Não continuar além dessa parada. O limite de 64 eventos é uma parada distinta.
Salvar na CPU o canvas anterior a cada evento, sem mantê-lo na GPU.

Por caso, um forward B1 completo extra no primeiro estado compara sua ação com
a projeção selecionada. Esse forward é somente diagnóstico, tem tempo separado
e não conduz nenhum evento. Todos os eventos usam os cabeçalhos selecionados B1.

## Verificação B8

Depois das quatro capturas, agrupar todos os estados pré-evento em ordem
cronológica, oito por forward. Preencher o último grupo repetindo sua última
linha real; padding não entra nas comparações. O hook reúne índices `B×32`
distintos por linha sobre os estados ocultos `B×256×4096`, segundo seu bloco.
Liberar logits/probabilidades completos a cada consulta, retendo apenas top-1,
confiança e ordem de 32 posições. Não usar previsões B8 para gerar novos estados.

Comparar posição global e ID da ação B8 com o registro B1 de cada linha real.
Relatar também todos os top-1, ordens e confianças, sua igualdade e maior diferença
de confiança. Divergência diagnóstica fora da ação não é, sozinha, falha do gate.
Qualquer divergência de ação falha esta configuração; continuar os quatro casos
e todos os batches, se não houver erro numérico, OOM ou interferência externa.

## Registro, decisão e limites

JSONL novo, aberto exclusivamente e com flush após cada registro. Registrar
commit e hashes das fontes/protocolo, entradas tokenizadas, cada cabeça B1/ação,
paradas, canvases finais, verificações B8, tempos, picos Torch e inspeções CUDA.
Entradas, eventos e canvas final permitem reconstrução independente dos estados.
Não salvar logits de vocabulário completo. Alvo de saída: no máximo 1 MiB.
Cobrar transferências, forwards, projeção, softmax, argmax, ordenação e finitude;
estes tempos são diagnósticos, sem conclusão de desempenho de decoder.

Gate passa somente com quatro capturas e todos os batches completos, zero
divergências de ação B1/B8 e completa/selecionada, sem interferência nem falha
numérica. OOM ou interferência: interromper, registrar recusa inconclusiva e
preservar o parcial. Outros erros ficam registrados; execução incompleta não passa.
Passar permite formular depois um protocolo de benefício em replay; não prova
igualdade em outros inputs, aceleração integral, novidade ou seleção do tema.
