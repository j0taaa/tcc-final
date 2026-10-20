# Sonda V1 de custo e separabilidade, antes do decoder

Congele este arquivo e `profile_v1.py` em commit antes de executar. Esta sonda
não seleciona o tema, não mede qualidade e não autoriza uma campanha ampla.
Seu consumidor é o planejador descrito no README da tentativa: uma consulta
de canvas precisa custar menos quando agrupada, sem depender de cache KV
aproximado. A política de revelar um token por passo permanece a referência.

## Configuração fixa

- GPU RTX 3080 Ti de 12 GB; recusar com menos de 7 GiB livres antes da carga
  ou com outro processo CUDA de computação. Não encerrar processos externos.
- LLaDA-8B-Instruct local, snapshot
  `08b83a6feb34df1a6011b80c3c00c7563e963b07`, NF4, double quantization, BF16.
  Não baixar nem treinar modelos. `use_cache=False`, quatro threads CPU,
  `eval` e `inference_mode`, seed Torch 86001.
- Prompt fixo: `Write a Python function that returns the running sum of a list.`
  Template de chat oficial, sem truncar o prompt. Complete com MASK até
  comprimentos totais de 128 e 256 tokens, nesta ordem. Não são gerações.
- Ler os primeiros 32 slots após o prompt. Um pre-hook na projeção final
  recebe somente esses estados ocultos. Todas as posições passam normalmente
  pelo transformer; não se alteram pesos, atenção, cache, posições ou vendor.
  Essa integração conhecida é um controle de custo, não contribuição própria.
- Batch de canvases idênticos com tamanhos 1, 2, 4 e 8, nesta ordem.
  Dois forwards de aquecimento e cinco medidos por par comprimento/batch;
  sincronizar CUDA antes/depois. Incluir softmax FP32, proibição de MASK,
  argmax de token, ordenação estável das posições por confiança e checagens
  de finitude dos logits antes da proibição e das probabilidades após softmax.
- Antes do pre-hook, obter um forward completo isolado por comprimento;
  comparar logits e ações com a projeção selecionada. Comparar também cada
  linha dos batches com a referência isolada selecionada. Relatar diferenças;
  igualdade matemática de linhas não implica igualdade numérica na GPU.
- OOM interrompe somente aquele tamanho e os maiores naquele comprimento;
  preservar a recusa, sem diminuir comprimentos ou repetições para salvar gate.

## Registro e decisão

Escrever JSONL novo, sem sobrescrever. Registrar commit, SHA-256 de fontes e
protocolo, versões, carga, processo, memória alocada/reservada e inspeções
CUDA. Relatar todos os tempos e seu resumo mediano, incluindo aquecimento
separado; carga do modelo fica separada. Pico Torch não é memória total.

O avanço é apenas para um protocolo pequeno de calibração e holdout se:

1. Ao menos um batch maior que um cabe em ambos os comprimentos e tem
   custo mediano por canvas <= 75% do batch 1 em ambos.
2. Todas as ações (posição e ID do token escolhido) comparadas são iguais
   à referência, incluindo projeção completa versus selecionada.
3. Não há interferência CUDA observada nem erro não explicado.

Falhar não prova impossibilidade geral, mas encerra esta configuração de
decoder. Passar não comprova novidade, aceleração de geração completa,
igualdade em outros inputs ou aprovação acadêmica. O próximo protocolo deve
congelar splits, comparadores competentes, fidelidade e custo completo antes
de capturar suas trajetórias.
