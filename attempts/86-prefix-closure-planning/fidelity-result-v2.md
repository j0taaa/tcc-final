# Fidelidade V2: gate prospectivo aprovado nos estados capturados

**PASS** no [protocolo V2](fidelity-protocol-v2.md), sem seleção como tema
central ou medição de aceleração de decoder. O batch B8 foi escolhido pelo
perfil V1 antes destes dados. O produtor e o protocolo V2 foram congelados em
`3cb983701d8e6176950d229adec894d4c99fa165`.

## Proveniência e auditoria independente

[Dados completos](fidelity-v2.jsonl): 666.840 bytes, 1.149 registros; SHA-256
`78de01d3bbecd1f61d896a08476728d0ff59c4306fb859df949037ee16b86daa`.
Hashes das fontes congeladas:

- [fidelity_v2.py](fidelity_v2.py):
  `89572c69bc1920b26b932c122f34e3eb0de1ee0742c4565bcf9e9d2e8a242ec5`.
- [fidelity-protocol-v2.md](fidelity-protocol-v2.md):
  `1b1833b47b53b0f0514fa6f88b410375290871806f191d0ea2cbec1d5202a8e7`.

Auditoria independente por subagente, somente em CPU, conferiu o SHA dos dados,
os cinco hashes do manifesto contra o commit e os arquivos atuais, JSON sem
NaN/Inf, a ordem de todos os registros e as entradas com o tokenizer oficial
local. Os quatro prompts reproduziram exatamente seus IDs; comprimentos
28, 33, 32 e 30, sem truncamento.

Os 256 estados pré-evento foram reconstruídos a partir das entradas e ações.
Cada evento revelou um MASK elegível no primeiro bloco incompleto de 32;
ordenação estável, posição global, ID original, prefixo do prompt, região
inelegível e canvas final conferiram. São quatro capturas de 64 eventos,
totalizando 256 estados dessas trajetórias.

## Resultado do gate

Os 256 pares B1/B8 coincidem exatamente nos valores registrados de ação,
32 top-1, 32 confianças e ordem dos slots. A diferença máxima de confiança foi
zero. Os quatro diagnósticos de projeção completa/selecionada também coincidem
nesses campos. Foram 32 lotes completos de oito canvases distintos, sem padding.
Nenhum lote usou previsões B8 para conduzir a captura serial.

Não houve erro, recusa, OOM ou falha numérica registrada. As 585 inspeções CUDA
registraram zero processos externos. Isso descreve as inspeções realizadas,
sem assegurar ausência de interferência entre elas.

Todos os casos pararam por `event_limit`. Nenhum EOS/EOT foi efetivamente
revelado; portanto o ramo de parada terminal não teve cobertura neural nesta
execução. O início de bloco era comum às oito linhas de cada lote: a reunião
de índices diferentes por linha existe no driver, mas lotes com inícios de
bloco distintos também não receberam cobertura aqui.

## Custos observados

Configuração registrada: RTX 3080 Ti, snapshot local LLaDA-8B-Instruct
`08b83a6feb34df1a6011b80c3c00c7563e963b07`, NF4/double quantization/BF16,
sem KV cache; seed 86002, quatro threads, Python 3.11.16, Torch 2.8.0+cu128,
Transformers 4.52.2, bitsandbytes 0.50.1 e Accelerate 1.10.1.

| Caso | Eventos B1 | Soma das consultas B1, s | Mediana B1, s |
| --- | --- | --- | --- |
| 0 | 64 | 6,487121 | 0,101177 |
| 1 | 64 | 6,509229 | 0,101563 |
| 2 | 64 | 6,538451 | 0,102072 |
| 3 | 64 | 6,553508 | 0,102169 |

Foram **292 forwards**: 256 consultas seriais, 32 verificações B8 e quatro
referências completas; 516 consultas de canvas ao contar as linhas dos lotes.
As janelas registradas somam 26,088309 s para B1, 16,947585 s para B8 e
0,997757 s para as referências, totalizando 44,033650 s. A mediana por lote B8
foi 0,529630 s. A primeira referência custou 0,683070 s e permanece contabilizada;
não foram retirados aquecimentos depois da execução. Carga separada: 56,627353 s.

Essas janelas incluem transferências, forward, projeção, finitude, softmax,
argmax, ordenação e leitura das saídas. Não são o tempo integral de um decoder:
inspeções de processos, escrita dos registros e trabalho fora de `query` ficam
fora delas. Não se infere speedup de geração comparando essas somas.

Pico Torch alocado: 6.172.797.952 bytes em B8; máximo serial e de referência:
5.826.620.928 bytes. Pico Torch não mede consumo total. O V2 não registrou um
pico NVIDIA total comparável ao perfil V1.

## Alcance da conclusão

O gate pré-fixado passou integralmente e permite formular um protocolo pequeno
de benefício em replay. A evidência é fidelidade finita das ações e cabeçalhos
gravados nesses estados e composições de lote; os logits completos não foram
armazenados. Não é prova de igualdade do oráculo para lotes arbitrários, nem
avaliação de respostas completas: todas as capturas foram limitadas a 64 eventos.
O teorema condicional de preservação de trajetória continua exigindo o mesmo
oráculo numérico. Novidade, contribuição suficiente e ganho integral permanecem
abertos.
