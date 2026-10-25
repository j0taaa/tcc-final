# Ambiente e reprodução

Python e dependências já instalados em
`/home/jota/projects/tcc-final/.venv-live/bin/python`, Python 3.11.16,
Torch 2.8.0+cu128, Transformers 4.52.2, NumPy 2.4.6. Lista integral em
`evidence/pip-freeze.txt`. `g++ -O3 -std=c++17 -shared -fPIC` compila o controle
CPU; cache regenerável em `.cache/a89`, SHA256 do C++ nos manifests.

Modelo NF4/double quantization, compute BF16, sem offload intencional ou treino:
`~/.cache/huggingface/hub/models--GSAI-ML--LLaDA-8B-Instruct/snapshots/08b83a6feb34df1a6011b80c3c00c7563e963b07`.
`evidence/reused-assets.json` identifica os seis shards e o binário Rust
instalado; sete fontes Python dos bindings conferem com o vendor desta worktree.
Metadados/tokenizer/código do modelo têm hashes nos registros. Os shards não
foram baixados novamente nem auditados integralmente por novo hash de conteúdo.

GPU: RTX 3080 Ti, 12 GiB, driver 595.99.02. Há também consumidores gráficos
do desktop, listados no início de cada fase. Ambas as fases neurais foram
executadas sob `flock /tmp/tcc-final-gpu-pilot.lock`; o processo inteiro, não só
o trecho cronometrado, segura o lock. A checagem inicial começou antes da
instrução do lock e terminou normalmente. A thread de memória usa tentativa A90
em outra worktree, sem colisão de pasta. Ao terminar TEST, o processo A89 saiu;
o lock e a VRAM puderam ser usados pela outra thread.

Na raiz desta worktree, `bash attempts/89-adaptive-mask-budget/reproduce.sh`
reproduz oráculos, VAL, seleção e TEST em arquivos com sufixo `rerun`; os comandos
recusam sobrescrever evidência existente. O lock espera no máximo 30 segundos
por chamada; se estiver ocupado, aguardar sem lançar cópia paralela. É necessário
ter pesos/ambiente equivalentes disponíveis localmente. Não há dependência de
capturas neurais antigas.

Outros comandos CPU:

```bash
P=/home/jota/projects/tcc-final/.venv-live/bin/python
A=attempts/89-adaptive-mask-budget
$P $A/prepare_inputs.py --output .cache/a89/inputs-reproduced.json
$P $A/audit_cpu.py --output $A/evidence/incremental-audit-rerun.json
uv run --no-project --with matplotlib==3.10.7 python $A/plot.py
```

Os inputs reproduzem byte a byte a seleção congelada. O script de plots não
carrega modelo nem usa CUDA. A fonte completa BBH e sua licença MIT estão
preservadas em `evidence/`. `freeze-v1.json` registra fontes pré-forward;
notas/análise/auditoria posteriores têm escopo explicitado. Não houve commit,
push, publicação, PR ou alteração de `vendor/`.
