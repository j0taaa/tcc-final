# Reprodução local e contabilidade

**A avaliação final usa a emenda V1a**: consumidor Qwen2.5-1.5B-Instruct FP32,
comum a todos os métodos. A V1 NF4 falhou na auditoria, sem responder tarefas;
veja `protocol-v1a-runtime-amendment.md`. O editor AR continua Qwen 3B NF4.
O consumidor NF4 original não foi validado e não é usado nos resultados finais.

Ambiente já existente, somente leitura na raiz do checkout:
`/home/jota/projects/tcc-final/.venv-live/bin/python`.
Torch 2.8.0+cu128, Transformers 4.52.2, bitsandbytes 0.50.1.
GPU confirmada: RTX 3080 Ti 12.288 MiB. `models.json` contém revisions, configs,
tokenizers, tamanho dos pesos e blobs do cache. Não se treinam pesos.
AR é um checkpoint NF4 derivado de Qwen2.5-3B-Instruct; LLaDA é quantizada NF4 no
carregamento. Ambos usam compute BF16, todas as camadas na GPU e zero offload.
O consumidor final é um checkpoint distinto: Qwen 1,5B FP32, comum a todos.
Ambos os sistemas neurais precisam de editor e leitor. Não se mediu sua
coexistência em VRAM ou swapping a cada interação; a soma residente é por fases.

Antes de qualquer execução nova, preserve os `evidence/*-v1.*` existentes (o logger
recusa sobrescrita). Use novos nomes de saída e ajuste as leituras correspondentes
se quiser repetir medições; não promova repetição posterior à V1 congelada.

```bash
A90_PYTHON=/home/jota/projects/tcc-final/.venv-live/bin/python
A90_DIR=attempts/90-cache-aware-text-memory
HF_HUB_DISABLE_XET=1 "$A90_PYTHON" "$A90_DIR/fetch.py"
"$A90_PYTHON" "$A90_DIR/prepare.py"
"$A90_DIR/reproduce.sh" audit
"$A90_DIR/reproduce.sh" cpu
"$A90_DIR/reproduce.sh" ar
"$A90_DIR/reproduce.sh" dllm
"$A90_DIR/reproduce-v1a.sh"
"$A90_PYTHON" "$A90_DIR/analyze.py" --blind
# Classificar blind-review.json com a rubrica pré-fixada; manter a chave separada.
"$A90_PYTHON" "$A90_DIR/analyze.py"
"$A90_PYTHON" "$A90_DIR/verify.py"
```

Cada comando GPU mantém `flock /tmp/tcc-final-gpu-pilot.lock` durante o processo
inteiro, inclusive import, carga, warmup e limpeza. Espera padrão de 1 segundo;
uma tentativa limitada de 45 s também foi usada, registrada na coordenação.
Se houver PID compute alheio após adquirir o lock, o programa recusa continuar.
Não remova/recrie o arquivo de lock enquanto qualquer trabalho puder usá-lo.
`nvidia-smi` somente leitura não é uma medição de kernels.

`freeze-v1.json` preserva contrato/entradas/fontes anteriores ao primeiro forward;
`freeze-v1-initial.json` preserva a redação prévia (corrigida antes do primeiro
forward para dizer que a revisão semântica é do agente, não humana independente).
`pre-dllm-stop-amendment.json` corrige EOS versus EOT após inspeção do template e
antes da primeira chamada dLLM; a fonte inicial usada na fase AR também foi salva.
O trabalho de denoising até o canvas completo permanece cobrado apesar do trim.
Nenhum caso, cap, métrica, seletor ou gate é alterado por essa correção.

## O que os tempos significam

`seconds` inclui tokenização, tensor/preparo imediato, execução sincronizada,
amostragem gulosa, transferências de logits e decodificação. Seleção e montagem
são cobradas adicionalmente nos editores. O tempo residente combinado soma essas
etapas medidas separadamente e o consumidor com KV persistente por história.
Isso **não** mede pipeline intercalado, throughput, swap por interação nem serviço
simultâneo. Full-history recebe exatamente o mesmo KV/prefix caching do leitor.

Carga, warmup, import e wall time de cada fase estão separados nos JSONL. Na V1a, o custo
frio precisa incluir carga do editor e do consumidor, ambos distintos; os
controles sem editor neural precisam apenas do consumidor. A parede das fases
já inclui cargas/warmups: não somar essas parcelas duas vezes. A comparação
principal usa soma residente e relata a ausência de pipeline intercalado.

Obtenção do snapshot AR novo: aproximadamente 45 s reportados pelo downloader,
~1,9 GB de novos pesos; download não é latência residente por interação. LLaDA e
ambiente já existiam. Fontes bibliográficas e corpus também foram baixados;
duração total desses preparos e trabalho humano/agente não foi instrumentada e
não será inventada. Tamanhos e hashes ficam nos manifests. Construção do corpus
sintético/seleção é código CPU; `prepare.py` não usa modelo gerador. Treinamento,
dados de treinamento, chamadas pagas e compute pago: zero. Não há custo de
pós-treino para amortizar; sem ganho marginal positivo não existe amortização
finita de um treinamento hipotético.

Snapshot adicional V1a: Qwen/Qwen2.5-1.5B-Instruct revision
`989aa7980e4cf806f80c7fef2b1adb7bc71aa306`, ~3,1 GB de novos pesos; downloader
reportou cerca de 71 s. Falha V1: 14,19 s de parede; diagnóstico separado
não instrumentou parede total e não tem latência de serving atribuível. Esses
custos de pesquisa/preparo não entram na soma residente bem-sucedida. V1a usa
o mesmo consumidor FP32 em todos os métodos, sem offload; carga e picos são
registrados na nova fase. Aumentar a precisão e trocar o checkpoint do consumidor não alterou os dados,
pesos dos editores ou memórias já produzidas. Não é a mesma avaliação V1.
