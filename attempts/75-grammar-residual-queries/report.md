# A75 — Resultado da investigação delimitada

**Decisão: resultado matemático condicional sustentado; gate finito 12/12;
ponte neural não estabelecida.** Não selecionar como avanço prático de dLLM
nesta rodada. Prioridade específica e consumidor real continuam pendentes.
Não houve treinamento, forwards, modificação do vendor ou de dados anteriores.

## Prova e prioridade

[A prova escrita](proof.md) reconstitui a identidade residual, o acoplamento
por troca, o martingal sem reposição, a cauda integrada e a normalização.
Sob o oráculo coerente e a classe Lipschitz declarados, dá TV≤κα com
O(α) consultas, uniforme em n, e o witness dá Ω(α) para κ suficientemente
pequeno e n suficientemente grande. O custo da saída continua Ω(n).
Cada G_n finita é regular; a linguagem de todos os comprimentos é não regular.

Ataque independente adicional ao passo assintótico: T tem massa
binom(n/2,t)²/binom(n,n/2) e variância n²/[16(n−1)]. Stirling em
t=n/4+z√n dá, uniformemente em janelas limitadas de z, massa
√[8/(πn)] exp(−8z²)(1+o(1)); Chebyshev dá tightness. Logo o limite é
N(0,1/16). A função limitada g não é constante nesse limite e sua
desviação absoluta média tem limite positivo. Isto justifica o passo do
witness sem inferir uma prova universal dos casos finitos.

FORS já fornece a proposta arbitrária e o factory; SIRS já fornece o
incremento aleatório, clipping e Rao–Blackwell. **FORS com este mesmo
estimador é idêntico, inclusive em custo.** Os primários e as diferenças
estão no [README](README.md). A busca delimitada não certifica prioridade.
O teorema é uma especialização quantitativa candidata, não uma nova primitiva.

O limite estacionário exige que o protocolo completo preserve P e mantenha
o estado no ramo sem consulta. Inclui pair heat bath, mas exclui refresh de R.
Uma fórmula conhecida de F pode permitir zero consultas, fora da interface.
Uma consulta raiz não distingue o par witness BALANCE; não se afirma que
uma consulta arbitrária tampouco o distingue.

## Protocolo, falha preservada e auditoria

- `0070c2ba`: operação, prova e protocolo antes dos casos e dos timings.
- `2a1e7de7`: implementação congelada antes de executar.
- `2f5a8885`: primeira falha preservada e correção explícita de marginais
  já fixadas. [O registro original](results-v1.jsonl) permanece FAIL.
- `788f04d5`: dados corrigidos preservados; verificador de operandos congelado
  antes de seu replay, sem mudar casos, seeds, decisões ou gates.

Foram conferidos 2.047 reconhecimentos de palavras até n=10; 36.164 pinnings;
68.904 desigualdades de oscilação/média; 1.022 cadeias racionais em duas ordens;
29.616 pares para Lipschitz; momentos p=1,2,4,8 em todos os níveis dos casos
BALANCE; 3.405 logs por séries racionais independentes. A conferência escalar
Decimal de 90 dígitos é separada dos certificados intervalares.
Os endpoints inteiros a escala 10^100 são os certificados, os campos float
são somente apresentação. Massas são racionais; o sampler completo limitado
pode recusar decisões, portanto não recebe a exatidão ilimitada do factory ideal.

Os **12/12** casos BALANCE, sem mudar B=α, tiveram TV(P,Q_B)≤TV(P,R)/2 e
E NFE<1. A maior razão de erros foi 0,194734; consultas esperadas ficaram
entre 0,02020016 e 0,10514807. Resultados representativos de n=8, α=0,01:

| Alvo | TV(P,R) | TV(P,Q_B) | E NFE residual |
| --- | ---: | ---: | ---: |
| Witness + | 0,001354927114 | 0,000262315795 | 0,020200163186 |
| Witness − | 0,001361267782 | 0,000265083871 | 0,020201861028 |
| F por pares adjacentes iguais | 0,000639658849 | 0,000031193696 | 0,020201035746 |
| Hard-core anterior, separado de BALANCE | 0,001389668409 | 0,000249759907 | 0,020196832890 |

Todos os 13 casos e endpoints estão em [results-v1-corrected.jsonl](results-v1-corrected.jsonl).
No caso hard-core, o limite estacionário reproduzido é 0,1263790847592863.
O sistema das marginais raiz tem posto 5; o controle de reconstrução e mistura
residual é **exato, TV=0, E NFE=1/101**, mais forte que o factory nesse caso.
Não se usa esse caso para alegar separação. Em BALANCE as raízes do witness
são exatamente iguais, impedindo aquela reconstrução específica.

Sequential+closure é exato e custa aproximadamente 2,66–2,68 consultas
em n=4 e 6,39–6,41 em n=8. Pair heat bath faz n atualizações válidas,
com detailed balance racional verificado, e custa 8/3 ou 32/7 consultas.
Ele alcança erro menor que o residual nos witnesses, pagando mais consultas;
não foi omitido para favorecer a candidata. Single-site congelado não foi usado.

SIRS original com proposta produto mantém a massa inválida: com B=α,
a saída ficou com aproximadamente 61%–72,5% fora da gramática. O controle
declara a extensão das condicionais em pinnings de massa zero, e cobra o
root head. Na raiz uniforme a massa válida inicial é 6/16 ou 70/256,
assintoticamente Θ(n^(−1/2)), sem alegação de decaimento exponencial.
O produto raiz projetado pela gramática coincide com R nos casos desta rodada;
paga um head e tem outro alvo. Sua exatidão de passo não valida P conjunta.

O bound universal de TV em B=α é **vacuoso** nestes parâmetros. Com cotas
racionais conservadoras para M_C e K₀<10, um B suficiente para certificar
metade do erro varia de cerca de 1.512 a 667.215. Não foi executado esse
parâmetro nem se confundiu esse bound frouxo com custo real. O ganho finito
observado não fornece uma constante universal prática.

## Execução, bits e custo completo

O teste congelado executou 64 chamadas por caso e controle: 3.072 saídas,
nenhuma recusa. Não se usa frequência empírica para provar a lei conjunta.
Os contadores agregados, sem timings, foram:

| Controle | Saídas | Consultas | Propostas de R | Bits RNG |
| --- | ---: | ---: | ---: | ---: |
| R | 768 | 0 | 768 | 11.108 |
| Residual | 768 | 35 | 783 | 13.240 |
| Sequential+closure | 768 | 3.510 | 0 | 40.531 |
| Pair heat bath | 768 | 2.833 | 768 | 91.933 |

O custo de 35 consultas é uma realização aleatória, não a esperança nem
estimativa de ganho de tempo. A saída total contém 18.432 slots binários.
O residual pagou 10.948 bits da referência, 1.565 do Poisson, 674 de máscaras
e 53 de aceitação. Não existe um root head necessário à R uniforme.
Se uma referência neural exigir esse head, somá-lo: não haverá NFE total<1.

O oráculo sintético prepara tabelas exponenciais; em n=8 foram 5.407
cilindros por tabela e até 21 bits nos inteiros do oráculo. A construção
prepara também a tabela de referência para auditoria, embora o consumidor
BALANCE use k/l diretamente. Não se considera esse setup gratuito nem um
substituto de transformer/head/normalização. O high-water RSS registrado foi
444.468 KiB, cumulativo do processo e ambiente, sem atribuição incremental
por algoritmo ou pesos de modelo. Não houve alocação de modelo na GPU.

O [replay de operandos](runtime-bits-v1.json) confirmou igualdade de todas as
48 linhas, incluindo outputs, consultas, propostas e bits, descontando apenas
RSS. Detectou operandos racionais de até **2.101 bits**, produtos intervalares
de 665 bits, 207.489 multiplicações intervalares e 341.077 chamadas dos helpers
de arredondamento (ceil chama floor). São contadores de implementação,
não instruções CPU nem um teorema de bit-complexidade. A precisão custa trabalho.
O verificador confere ainda 9 pontos de exp por séries racionais, 25 pares
aritméticos, 1.692 transcripts uniformes de subconjuntos e duas recusas
deliberadas no teto de 256 bits. As recusas aleatórias não foram substituídas.

Fisher–Yates paga O(n) operações de palavra e O(n log n) bits esperados,
além da saída; a rejeição no randbelow não tem teto determinístico. Em CFG
geral cobrar inside/outside por máscara consultada. Sob a interface ideal,
o custo é da forma C_R+O(α)(C_model+C_mask), com logs/precisão/RNG/saída e
preparação incluídos; não é um speedup quando o oráculo é uma tabela barata.

## Gate neural e timings

**NOT_APPLICABLE_ORACLE_CONTRACT; zero forwards.** A inspeção em leitura do
snapshot local LLaDA `08b83a6feb34df1a6011b80c3c00c7563e963b07` e seus hashes
estão nos dados. Ele expõe logits posicionais de vocabulário completo;
não fornece P(.|G,pins) coerente nem o certificado Lipschitz exigido.
Os IDs originais dos caracteres são registrados, sem projetar/renormalizar
uma cauda e chamá-la de vocabulário completo. EOS/PAD não entram no teorema.

O contraexemplo racional de projeções por máscara dá probabilidade 9/19
para um mesmo par numa ordem e 1/3 na outra: não há uma conjunta coerente.
Se P_all sair de G, log P_all(G) prejudica a aceitação e os bounds; posições
forçadas por R não são automaticamente forçadas pelo modelo. Preparar uma
única lei produto com parser poderia fornecer condicionais coerentes, mas
muda a operação e cobra root+parser; isso não foi medido como validação neural.

Uma tentativa de timing adquiriu flock exclusivo no caminho contratado e
consultou nvidia-smi. Encontrou o processo alheio `llama-server`, PID 2603454,
com 4.054 MiB, e retornou TIMING_DEFERRED_GPU_PROCESS_PRESENT antes de ler
relógios. Não encerrou processos nem mediu sob concorrência. A execução CPU
contada e seu replay não mediram wall time. Recursos ocupados não refutam
o método; a ausência de ponte é um limite de contrato independente disso.

## Reprodução e checks

Python 3.11.16 em `.venv` deste worktree, sem modificar o ambiente principal.
Instalação usada: `uv pip install --python .venv/bin/python -e '.[dev]'` e
`uv pip install --python .venv/bin/python --index-url https://download.pytorch.org/whl/cpu 'torch==2.8.0+cpu'`.
O primeiro make check encontrou quatro erros pela ausência de Torch; após
instalar a variante CPU local, **make check passou, 345 testes**, além de
baseline, lint, formato e tipos. Nenhum resultado científico foi alterado.

```bash
a75_out=$(mktemp -d /tmp/a75-repro.XXXXXX)
.venv/bin/python attempts/75-grammar-residual-queries/audit.py --output "$a75_out/audit.jsonl"
.venv/bin/python attempts/75-grammar-residual-queries/runtime.py --output "$a75_out/runtime.jsonl"
.venv/bin/python attempts/75-grammar-residual-queries/verify_runtime.py --recorded "$a75_out/runtime.jsonl" --output "$a75_out/bits.json"
.venv/bin/python -m ruff check attempts/75-grammar-residual-queries
.venv/bin/python -m ruff format --check attempts/75-grammar-residual-queries
make check
```

Para o timing opcional, adicionar `--timing` ao runtime com uma saída nova;
o próprio programa exige lock exclusivo e recusa GPU ocupada. Não há
timing/resultado neural autorizado que se possa substituir por outro posterior.
