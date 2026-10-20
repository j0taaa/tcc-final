# A73 V1 — resultado da investigação delimitada

**Não selecionada como contribuição central com a evidência desta rodada.**
A contração é correta no contrato ideal, e o compilador finito funciona nos
oráculos. Ainda não há distinção matemática própria suficiente estabelecida,
consumidor natural validado nem ganho neural integral. O gate operacional é
**inconclusivo por recurso**, não negativo por latência: nenhum modelo foi
carregado e nenhum timing neural foi realizado. Não ampliar a campanha para
resgatar um gate, nem transformar a recusa em refutação do método.

## Prova, prioridade e benefício

A [prova escrita](proof.md) demonstra geração exata de U_v por anchors do
forest e preservação de todos os contrastes pela mudança de base. Corrige
explicitamente bias e constante do normalizador. Ambiguidade conserva MAP e
hull, mas não permite contar árvores como palavras para o posterior. O limite
de consultas refere-se a todos os contrastes sob consultas separadas por linha,
não a MAP arbitrário, preprocessamento de W ou ótimo de GPU.

Um antecedente adicional conferido durante a espera pelo recurso é
[Wainwright–Jordan (2008), §3.2, p.40; Proposição 3.2, p.64](https://www.cs.columbia.edu/~blei/fogm/2020F/readings/WainwrightJordan2008.pdf).
Eles descrevem redundância de estatísticas suficientes por relações afins e
equivalência dos parâmetros da família exponencial. Minha inferência: remover
direções que só adicionam constantes e transportar unárias para uma base é
uma instância desse princípio clássico. Não atribuo ao texto a implementação
de um LM-head contraído. Junto com análise afim e semirings, isso reduz a
distinção candidata à integração/compilação anterior ao head e à sua utilidade
operacional, que continuam sem validação competitiva.

O exemplo de cópia é inteiramente coberto por pooling manual/flattening
antecipado: A73 e esse controle têm as mesmas consultas de head. Campos
independentes não permitem redução. A contagem balanceada fornece relações
além de igualdades e reduz quatro para três consultas por ID, mas é uma tarefa
construída com dois tipos de campo, não evidência de relevância geral para
sintaxe natural. O protótipo recebe um forest explícito; não implementa um
frontend genérico de CFG de bytes nem torna esse custo gratuito.

## Evidências offline

Fonte e protocolo congelados antes do preflight:
`9f8641009d1a6eabdbf41923ebb3b28950036f30`.
Os números inline do briefing não foram tratados como dados congelados.
O novo [auditor](audit.py), com enumeração de palavras e eliminação inteira
independentes da redução racional do compilador, registra em [oracles.json](oracles.json):

- 345 linguagens, incluindo TODAS as linguagens binárias não vazias com
  comprimento 1–3 e 64 linguagens maiores com seed 730019;
- 41.128 contrastes de indicadores reconstruídos, 1.035 ensaios de score/MAP
  e de uma lei Gibbs racional centrada, sem divergência;
- seis forests malformados rejeitados; DAG fatorado/compartilhado, epsilon,
  nó inalcançável, ambiguidade, fixações, aliases, bias e pivôs fracionários;
- tokenizer pinado reproduzido: 151.643 IDs ordinários, 32.804 identificadores,
  zero aliases nessa classe, 183.834 bytes. Não juntar aliases em outras classes.

Os três builders efetivamente usados pelo runner também foram conferidos
contra enumeração racional em versão pequena. A compilação de TODOS os seis
forests na dimensão real foi concluída sem GPU e **sem timings**, em
[structure.json](structure.json). São contagens estruturais, não aceleração:

| Caso | Nós | Consultas sparse | Consultas A73 | Observação |
| --- | ---: | ---: | ---: | --- |
| copy4-p0 | 164.021 | 131.216 | 32.804 | manual também 32.804 |
| copy16-p0 | 557.669 | 524.864 | 32.804 | manual também 32.804 |
| copy32-p1 | 1.082.533 | 1.049.728 | 32.804 | manual também 32.804 |
| independent4-p0 | 131.221 | 131.216 | 131.216 | nenhuma economia |
| independent16-p1 | 524.881 | 524.864 | 524.864 | nenhuma economia |
| balance4-p1 | 820.106 | 131.220 | 98.415 | inclui o ID sentinela |

Cada caso tem um único grupo B. Seus ranks são respectivamente 1,1,1,4,16,3;
nnz(B) são 4,16,32,4,16,6. Nos casos reais os coeficientes são 0/±1; o oráculo
fracionário verifica também denominador 2. `stored_rational_bits` conta somente
numeradores/denominadores/signs de B, incluindo zeros; não é RSS, serialização
total ou custo dos intermediários. Os masks dos geradores ocupam n bits e
anchors/grafos/IDs continuam tendo custo. As contagens mostram tanto a pequena
representação online compartilhada quanto o preço do forest explícito.

## Recusa operacional e reprodução

O [protocolo](protocol.md) manteve casos, controles, seed, métricas e gate de
20% integral contra **todos** os controles, incluindo pooling, em Q=1 e Q=32.
O [registro bruto](run-v1/records.jsonl) preserva a única tentativa de preflight:
GPU RTX 3080 Ti 12 GB, 4.470 MiB ocupados, utilização 74%; processo alheio
PID 2603454, `pratofolio/.../llama-server`, 4.054 MiB. O runner adquiriu
`flock` exclusivo, verificou `nvidia-smi` e retornou código 76 ANTES de importar
Torch/carregar pesos. Uma consulta posterior sob o mesmo lock encontrou o
mesmo processo. Nenhum processo foi encerrado. Não há tempos, gaps ou MAPs
neurais a reportar, e o gate não deve ser contado como 0/6 medições negativas.

Comandos executados da raiz:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/jota/projects/tcc-final/.venv/bin/python \
  attempts/73-grammar-head-contraction/audit.py \
  --tokenizer /home/jota/projects/tcc-final/.cache/a52-model-metadata/tokenizer.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/src" \
  make check VENV=/home/jota/projects/tcc-final/.venv
PYTHONDONTWRITEBYTECODE=1 /home/jota/projects/tcc-final/.venv/bin/python \
  -m ruff check attempts/73-grammar-head-contraction
PYTHONDONTWRITEBYTECODE=1 /home/jota/projects/tcc-final/.venv/bin/python \
  -m ruff format --check attempts/73-grammar-head-contraction
PYTHONDONTWRITEBYTECODE=1 /home/jota/projects/tcc-final/.venv-a52/bin/python -u \
  attempts/73-grammar-head-contraction/operational.py \
  --output attempts/73-grammar-head-contraction/run-v1
```

`make check`: baseline preservado, lint/formatação, tipos e **345 testes
passaram**. O auditor A73 é adicional à suíte mantida. O runner recusa
sobrescrever `records.jsonl`; eventual execução quando houver recurso precisa
de um diretório NOVO e deve manter a recusa anterior. Não foi feita uma nova
campanha ou captura em CPU para substituir o endpoint GPU congelado.

Para reproduzir as contagens estruturais, importar `make_forest`, `CASES` e
`MODEL` de `operational.py`, obter D pela regex pinada no tokenizer, e aplicar
`compile_forest(nodes,root,n)` para cada caso; conferir `Plan.stats` contra
`structure.json`. Nenhum peso neural é necessário para essa verificação.

O limite entregue é concreto: prova e software finito corretos nos checks
executados; novidade suficiente, prevalência de ranks baixos em gramáticas
naturais, certificação numérica CUDA e benefício completo continuam abertos.
Só a indisponibilidade do endpoint impede medir o protocolo autorizado; ela
não estabelece se A73 seria mais rápida ou lenta. Esta tentativa não sustenta
uma nova recomendação de TCC nem uma alegação de método publicável.
