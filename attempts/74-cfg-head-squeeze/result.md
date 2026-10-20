# A74 — Resultado da investigação delimitada

**Não selecionar esta formulação como contribuição central de TCC.**
A operação é correta sob o contrato, mas é uma composição de rejeição com
envelope dominante, squeeze clássico e DP gramatical. Não se estabeleceu
novidade relevante. O regime aritmético favorável é construído e depende de
um head quase posto 1; isso não foi verificado num modelo aprendido.

A triagem CPU preservou quatro capturas reais MDLM e oito recusas de
envelope, sem mudar casos/gates. **Não há comparação de velocidade neural**:
a GPU estava ocupada por um processo externo e não foi usada. Recusa de
recursos é inconclusiva. A recusa do envelope CPU também não demonstra
aceitação real baixa nem impossibilidade de proxies melhores.

## Prova escrita, oráculos e implementação

[proof.md](proof.md) deriva a lei aceita, E[propostas], E[consultas],
probabilidade de acionar a referência, cap fixo com fallback exato, bijeção
CFG/palavras, kernel racional e regime construído. Inclui o ataque por
censura de outputs e a ressalva de que gauge antes de racionalizar muda
a lei. Não é prova Lean, revisão humana nem prova de todo o software.
O lower bound de consultas usa indistinguibilidade/TV clássica, não tempo.

[oracle-v1.json](oracle-v1.json), produzido a partir do protocolo congelado:

- 1.296 leis completas, com enumeração de todos os tickets de aceitação;
  fórmulas de consultas e fallback J=0,1,2,4 conferidas racionalmente.
- 4.368 strings sobre quatro terminais; parser independente de spans
  confirmou uma derivação por palavra válida e zero por inválida.
- 4.096 strings com aliases em n=4, das quais 192 válidas; DP versus
  enumeração em 48 tabelas ponderadas. Fixed positions e massa vazia testados.
- 768 amostras válidas, incluindo 73 fallbacks, 6.446 linhas consultadas
  antes do fallback e 178.855 bits RNG no protótipo. O contador de linhas
  não inclui um head denso: o alvo já é uma tabela inteira nesse oráculo.
  O maior inteiro de chart observado tinha 28 bits.
- 387 pontos de E_b comparados com Decimal de 90 dígitos. É crosscheck
  numérico finito, separado do argumento universal de Taylor/monotonicidade.

As contagens anteriores de 298 leis/340 strings não foram promovidas a dados:
não havia vetores/programa congelados para reproduzir exatamente aquela rodada.
Os novos casos estão declarados na V1. Não somar essas contagens como se
fossem a mesma experiência. A amostragem não prova a lei por frequências.

Depois da triagem, `check.py --audit-screen` foi adicionado para consumir
os certificados arquivados: reconstrói os oito expoentes e polinômios com
Fraction, sem Torch/modelo/GPU. Também confere seis construções racionais
quase posto 1 contra R<exp(2,4 delta), nove leis TV construídas explicitamente
e um contraexemplo à invariância de gauge antes de E_b. São verificações
suplementares da prova, não novos casos neurais nem mudança do gate.

## Triagem de limites no modelo

Modelo MDLM-OWT, revision/hashes, tokenizer, IDs de entrada e hashes de h
estão em [screen-cpu-v1c.jsonl](screen-cpu-v1c.jsonl). São **quatro** estados,
cada um avaliado por dois proxies; não oito forwards. Port FP32 CPU auditado,
sem treinamento, head interceptado antes da projeção. Alvo conceitual:
dot exato sobre W/h binários capturados, bias e exp ideal, condicionado em
suporte 0..50255. EOS/mask excluídos, PAD ausente. Não é softmax binário CUDA
nem uma nova amostra gramatical de trajetória nativa.

O envelope Cauchy escolhido tem rho mínimo 510497/16777216 no INT8 e
33343937/8388608 no posto 1 da primeira coluna. Para qualquer CFG não vazia
nesse suporte, R>=exp(a), a=2 min(rho) sum(eta). O certificado usa
sum_{k=0}^{16}a^k/k! como limite inferior racional de exp(a).

| Prefixo | n | a no INT8 (aprox.) | R maior que o inteiro certificado |
| --- | ---: | ---: | ---: |
| `Return a balanced sequence of A and B:` | 8 | 5,191915 | 179 |
| mesmo prefixo | 32 | 21,243039 | 253.391.951 |
| `Complete the structured payload:` | 8 | 5,163758 | 174 |
| mesmo prefixo | 32 | 20,680110 | 172.532.115 |

Posto 1 da primeira coluna: a entre 674,56 e 2.775,05. Todas as oito
variantes deram `ENVELOPE_GATE_REFUSAL` no gate prévio R<=4. O teste é forte
contra **esses envelopes**: nem escolher depois outra CFG nesse suporte
reduziria sua cota abaixo do gate. Não testa um proxy SVD ótimo nem todas
as técnicas de intervalo. R é cota suficiente de custo esperado, e sua
largura não é medição de rejeições reais. Não há vitória de baseline por
tempo nem inferência de speedup a partir dessa tabela.

Custos preservados: ler/hash-verificar checkpoint, percorrer 38.596.608
coordenadas por proxy, preparar resíduos/normas e executar quatro backbones
até o head. RSS máximo do processo: 3.123.392 KiB (~3.050 MiB). Head FP32
original: 154.392.576 bytes; formato compacto INT8+escalas: 38.998.656 bytes,
além da referência. O protótipo de certificação usa arrays FP64/Fraction,
não um kernel INT8 compacto; os tamanhos compactos não são memória medida
de um decoder. O RSS inclui o custo real desse protótipo.

Nenhuma projeção proxy/referência, chart neural, consulta de dot, RNG de
amostragem ou saída foi executada depois da recusa. Seus contadores são
zero porque não houve amostra. Não interpretar como decoder de custo zero.
Todos os campos de tempo/GPU da execução CPU são null; não existe custo
integral medido para comparar com head denso, head legal esparso ou DP.
O consumidor construído continua sendo o único sampler completo desta A74.

## Recursos, falhas preservadas e produtores

- `63d5c1ed`: V1 congelou contrato, fontes primárias, casos, seeds, controles
  e gate antes dos outputs. [screen-v1.jsonl](screen-v1.jsonl) obteve flock
  exclusivo e consultou nvidia-smi: 7.443 MiB livres, mas um `llama-server`
  externo estava ativo. Recusa antes de carregar modelo, sem concorrência
  de medição e sem interromper o processo. Não é falha científica.
- `78738aba`: congelou os mesmos casos CPU sem relógio/GPU, preservando
  resultado offline e recusa CUDA. [V1a](screen-cpu-v1a.jsonl) falhou no
  TorchScript: `RuntimeError: Expected a single top-level function`.
  Erro do loader em memória, sem captura h.
- `4a31e54e`: forneceu ao linecache o fonte transformado. [V1b](screen-cpu-v1b.jsonl)
  verificou hashes do modelo, mas a checagem Fraction das normas detectou
  `OverflowError: Python int too large to convert to C long`: um booleano
  NumPy propagava int64 ao numerador racional. Sem captura h.
- `cccc8136`: incremento de isqrt convertido para int Python. A fórmula de
  intervalo não mudou. V1c concluiu quatro capturas/oito certificados.
  Casos, pesos, proxies e gate nunca foram trocados para obter aprovação.

Nenhum arquivo do checkout principal, `.venv`, cache de modelo, biblioteca,
vendor, status global ou dado anterior foi editado. O loader lê os checkpoints
absolutos e registra o fonte adaptado somente no linecache do próprio processo.
Saídas parciais ficam separadas; nenhuma foi sobrescrita por uma correção.

## Reprodução e verificações

Na raiz do worktree, stdlib para todos os oráculos e o auditor:

```bash
python3 -B attempts/74-cfg-head-squeeze/check.py
python3 -B attempts/74-cfg-head-squeeze/check.py --audit-screen
```

Captura CPU (escolher saída NOVA; requer cache local pinado, não há download):

```bash
PYTHONPATH=src:. HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  timeout --signal=TERM --kill-after=10s 180s \
  /home/jota/projects/tcc-final/.venv/bin/python -B \
  attempts/74-cfg-head-squeeze/screen.py --device cpu \
  --output .cache/a74-reproduction-new.jsonl
```

O mesmo script com `--device cuda` usa internamente o lock exclusivo,
verifica nvidia-smi e recusa concorrência. Isso não é uma recomendação de
nova campanha para resgatar o resultado.

Ruff dos dois fontes e o teste independente dos intervalos dyádicos com
Fraction: PASS. `make check`: PASS, incluindo integridade EPIC, lint/formato,
tipos de 55 fontes e os 345 testes offline. O auditor dos oito certificados,
a reprodução idêntica do JSON offline e `git diff --check`: PASS.
Commit/push da branch preservam os produtores;
nenhum PR, merge, publicação ou contato externo é necessário nesta rodada.

A conclusão positiva é somente a validade matemática condicionada e os
oráculos finitos. Novidade e utilidade integral exigidas para o TCC não
foram demonstradas. Encerrar esta rodada sem ampliar a campanha.
