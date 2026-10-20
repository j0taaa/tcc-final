# A74 V2 — Decisão após comparação operacional

**Descartar esta formulação como aposta principal de TCC.** Agora há derrota
medida, além da anterioridade clássica: seis estados MDLM reais, quatro
proxies sem treinamento, dois controles densos e **0/48** comparações aprovadas.
Em head + sampler, a melhor variante por estado foi **2,6–3,0 vezes mais lenta**.
Todos os 528 draws válidos dos candidatos usaram fallback denso; as taxas
exatas de aceitação explicam isso, sem inferir taxa zero de uma amostra finita.

V1 havia testado somente correção/envelopes. Essa limitação fica preservada
em [result.md](result.md). V2 foi expressamente autorizada pelo usuário e
congelada antes dos dados em [protocol-v2.md](protocol-v2.md), produtor inicial
`355b95d3`; produtor completo `d47f000c`. Provas estão em [proof-v2.md](proof-v2.md).

## Medições válidas

Medianas em ms, 11 repetições pareadas/rotativas. P0/P1 são os dois prefixos
literais do protocolo. Comparação mais favorável à proposta entre oito
variantes em cada estado; o melhor denso foi sempre o split INT8 exato.

| Caso | n | Melhor proposta | Denso | Proposta | Proposta/denso |
| --- | ---: | --- | ---: | ---: | ---: |
| P0 | 8 | INT8 | 5,72 | 15,04 | 2,63 |
| P0 | 32 | INT8 | 19,18 | 53,56 | 2,79 |
| P0 | 128 | INT8 | 81,61 | 241,19 | 2,96 |
| P1 | 8 | INT8 | 5,63 | 15,25 | 2,71 |
| P1 | 32 | SVD-8 | 20,89 | 54,16 | 2,59 |
| P1 | 128 | INT8 | 79,45 | 235,02 | 2,96 |

Houve **zero vitórias pareadas** dos 528 draws de candidatos contra ambos os
controles. Incluindo o backbone medido e concedendo setup gratuito, a melhor
proposta ainda fica 1,75–2,80 vezes mais lenta por estado. Não é medição de
uma trajetória nativa inteira ou de qualidade semântica.

O caminho medido cobra proxy, limites, transferências, inside/CDF, RNG,
consultas/gathers, fallback e materialização dos bytes. Logs e espera por GPU
ociosa ficam fora do tempo do operador. A referência é o kernel inteiro
Q12/Q10 + lookup congelado, **igual entre todos os caminhos**; não é identidade
binária com torch.softmax nem com o idealexp V1. O consumidor é a CFG
construída de contagens sobre todos os 50.256 IDs elegíveis, com bytes
originais preservados; não alegar que ela é um consumidor JSON natural.

## Aceitação real e custo

Taxas reconstruídas de massas inteiras, não estimadas por frequência:

| Caso | n | p INT8 | Probabilidade exata de fallback após quatro propostas (aprox.) |
| --- | ---: | ---: | ---: |
| P0 | 8 | 0,000511997 | 99,7954% |
| P0 | 32 | 1,0823e-13 | quase 100% |
| P0 | 128 | 4,5821e-52 | quase 100% |
| P1 | 8 | 0,000829750 | 99,6685% |
| P1 | 32 | 3,0382e-13 | quase 100% |
| P1 | 128 | 2,8972e-51 | quase 100% |

Todos os SVD de postos 8,32,128 têm p<3e-88. A proposta geralmente paga
proxy/charts/propostas e depois o mesmo head/inside denso. Só contar as
linhas consultadas antes do fallback esconderia o custo decisivo.

O teste não depende apenas do cap escolhido: a prova de renovação em
proof-v2.md analisa qualquer cap sob custo médio serial constante. Usando
até o MENOR custo por tentativa observado, a extrapolação sem cap dá
0,286–0,455s nos dois INT8 n=8, contra ~0,006s diretos; não é uma execução
sem cap nem prova de tempo físico. No caminho INT8, a contagem exata dos
GEMMs já é >=1,4966 vezes o denso em expectativa, antes de parser/RNG.
Mesmo doar projeção, limites e D2H deixa melhor speedup hipotético <0,489.
Esses diagnósticos foram acrescentados após os dados, sem alterar o gate,
os casos ou qualquer resultado congelado.

## Isolamento, integridade e limites

O servidor externo estava residente e intermitentemente ativo. O lock
exclusivo foi respeitado; aguardaram-se três observações ociosas antes de
cada bloco. **116 draws em 13 blocos contaminados** ficam preservados e
explicitamente inválidos; mesmas seeds foram repetidas somente por recurso.
Os **66 blocos válidos / 660 draws** passaram por rechecagem independente
do pmon, sem atividade compute alheia observada nos respectivos intervalos.
Isso não estabelece isolamento físico nem monitoração contínua de nanossegundos.

Setup (8,51s comum; 2,55–3,22s por proxy) teve interferência: flags de validade
são false. Esses valores e razões T=1/T=32 exportadas são **diagnósticos**,
não benchmarks frios certificados. A decisão não usa esses tempos: a proposta
já perde com TODOS os custos de setup zerados, e setup adicional não negativo
não pode converter essa perda em ganho. Os seis tempos de backbone são válidos.

O auditor stdlib reconstruiu 54 massas por convolução de polinômios,
conferiu os 660 outputs/bytes e o gate. Pesos dos dois heads coincidiram em
16.886.016 pares; todos os 67.544.064 enclosures foram verificados. Oráculo
pequeno: 244 leis completas, carry uint64, posições fixas e fallback; oráculo
GPU: 1.280 células. Maior inteiro de chart: 9.825 bits; RNG: 764.587.991 bits
nos draws válidos. Não confundir isso com prova de todo o software.

Pico observado do processo: 1.601.680.384 bytes CUDA (~1,49 GiB) e 3.060.488
KiB RSS. O protótipo mantém todos os proxies/controles juntos; armazenamento
por variante e preparação estão nos registros. Modelos/tensores não entram
no Git. A falha inicial de padding e a recusa de recurso anterior ficam em
`measurements-v2`/`measurements-v2b`; não contam como derrotas científicas.

Não há teorema contra toda variante futura. Há evidência suficiente para
parar **esta aposta**, com limites Cauchy e proxies baratos fixados, no
modelo/hardware/consumidor declarados. Um novo envelope ou batching seria
outra investigação; não ampliar esta campanha para resgatar o gate.

## Reprodução

Dados: [measurements-v2c/rows.jsonl](measurements-v2c/rows.jsonl),
[pmon](measurements-v2c/pmon.txt), [auditoria](audit-v2.json).

```bash
PYTHONPATH=src:. /home/jota/projects/tcc-final/.venv/bin/python -B \
  attempts/74-cfg-head-squeeze/operational_v2.py --oracle
python3 -B attempts/74-cfg-head-squeeze/audit_v2.py \
  attempts/74-cfg-head-squeeze/measurements-v2c \
  --vocab /home/jota/projects/tcc-final/.cache/mdlm/models--openai-community--gpt2/snapshots/607a30d783dfa663caf39e06633721c8d4cfcd7e/vocab.json
```

Uma reprodução neural exige ambiente CUDA local, cache pinado e saída NOVA:
usar o comando do protocolo com `--run .cache/a74-reproduction-new`, flags
offline, quatro threads e limite externo 1800s. O script gerencia lock/ociosidade.
Não sobrescrever capturas. Verificações: Ruff da tentativa, auditor e
`make check` (345 testes, tipos/lint/integridade EPIC): PASS. A conferência
do gate original versus o auditor estendido preservou TODOS os valores.
