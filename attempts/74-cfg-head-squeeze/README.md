# A74 — CFG antes do head: rejeição com squeeze

Base: `84b3496952243f2a5b3c5dd2d31191073be3a304`. Investigação delimitada,
sem treinamento. Protocolo escrito antes de executar os novos oráculos ou
capturar estados. A confirmação do coordenador liberou os três worktrees.

**Decisão:** não selecionar esta formulação como contribuição central.
O mecanismo é clássico; os dois envelopes fixados recusaram os quatro estados
CPU, e desempenho GPU ficou não medido por ocupação externa. Provas, oráculos,
falhas de software e limites dessa conclusão estão separados em [result.md](result.md).

## Operação e consumidor

Uma amostra **completa** de IDs originais do produto de um único head congelado,
condicionado por CFG não ambígua, n slots fixos, EOS/PAD ausentes. Commitments
devem ser escolhidos antes dos valores livres. Não é a trajetória nativa de
MDLM/EPIC e não fornece todas as confidências nem a massa válida no produto
normalizado original. Suporte restrito é `exact_on_support`; aliases continuam
IDs diferentes, mesmo quando emitem os mesmos bytes. Nenhuma cauda é escondida.

Dados limites racionais 0<=L<=w<=U, propor X de U|G e comparar o **mesmo**
uniforme primeiro com L(X)/U(X), depois com w(X)/U(X). Consultar somente as
linhas referência do candidato quando o primeiro teste falhar. O protótipo
offline usa inteiros/racionais; a triagem de modelo usa logits ideais de um dot
exato sobre W e h binários capturados, mais bias, seguido de exp ideal. Nenhum
deles promete identidade binária com GEMM/exp/softmax CUDA.

Consumidor concreto do protótipo: IDs (c,b,j), modo c constante, contagens A/B
iguais e lexemas j livres; todos os IDs são elegíveis em cada posição. É um
consumidor **construído**, não um workload neural natural demonstrado. A
triagem de envelopes vale para qualquer evento não vazio no vocabulário
declarado; não inventa um decoder de produção nem uma semântica para os IDs.
Nos oráculos de aliases, o ID v emite o byte `b"ABCD"[v//m]`; os m IDs de
cada classe emitem o mesmo byte, mas mantêm pesos/identidades próprios.

## Antecedentes e diferença possível

Fontes primárias consultadas em 2026-10-20 UTC:

- [OS*, Dymetman/Bouchard/Carter, 2012](https://arxiv.org/html/1207.0742),
  seções 2.1–2.2: envelope dominante, amostragem por DP e rejeição exata;
  taxa de aceitação é razão de massas. A74 com envelope fixo é uma
  especialização desse princípio, sem o refinamento adaptativo do OS*.
- [Owen, Monte Carlo, cap. 4](https://artowen.su.domains/mc/Ch-nonunifrng.pdf),
  algoritmo 4.6, p. 26: aceitação pelo limite inferior evita avaliar a densidade.
  Logo o squeeze e sua economia de consultas também são clássicos.
- [Mussmann/Levy/Ermon, UAI 2017](https://proceedings.mlr.press/r15/mussmann17a.html):
  LazyGumbel/MIPS amortiza amostragem de log-lineares. Top-k correto e custos
  de busca/preparação são hipóteses; amostrar posições independentemente e
  rejeitar gramática é apenas um controle, não o melhor controle CFG.
- [AdaptiveSoftmax, NeurIPS 2024](https://papers.nips.cc/paper_files/paper/2024/file/d52dbd66219dc4e432e0bd4f9c25c4c3-Paper-Conference.pdf):
  aproxima top-k/normalizador com garantias probabilísticas, não o contrato
  racional exato A74. Não tratar intervalos de alta probabilidade como certos.
- [Block Verification, 2024](https://arxiv.org/html/2403.10444): verificação
  conjunta de blocos especulativos é antecedente para aceitação conjunta;
  sua operação autoregressiva não é automaticamente o produto CFG congelado.
- [SlimSpec, 2026](https://arxiv.org/html/2605.10453): head do draft de posto
  baixo com vocabulário completo e treinamento. Não fornece gratuitamente
  limites certificados do head referência sem treinamento.
- [Quasar, 2026](https://arxiv.org/html/2603.01399), seção 3.3: verificador
  quantizado. Dequantizar não prova igualdade com logits referência originais;
  a A74 exige limites e correção contra uma referência declarada.
- [FlashSampling, 2026](https://arxiv.org/html/2603.15854): Gumbel online/fusão
  reduz materialização e comunicação; não elimina por si só o dot do head.
  É controle competente para amostragem categórica, não um parser CFG geral.
- [GPIO, fonte pinada](https://github.com/AwaleSagar/gpio-llm/blob/6b0846503592c9bd2fc8e0f36bc5fac24f57ddf9/engine/src/forward.c)
  e [GSP](https://github.com/StealthEyeLLC/grammar-sparse-projection): projetar
  só linhas gramaticalmente legais precede A74. GSP também declara diferenças
  de redução floating point. Seus tempos não são medições nossas.

A36 já documentou head esparso; A50 já pagava o head inteiro. A74 tenta evitar
até linhas **elegíveis** usando envelope barato. Isso distingue a interface,
mas não estabelece método matemático novo: OS* + squeeze + inside já a obtém.
Nenhuma prioridade mundial, aprovação ou benefício neural é alegado. CAVeS
não entra como prioridade estabelecida (origem primária não verificada).

## Hipóteses, prova e custos

[proof.md](proof.md) deriva lei, fallback, limites, gramática, kernel racional,
regime construído e objeções independentemente do briefing. O benefício
verificável pretendido é custo integral menor para a mesma lei. Contar:
preparação/leitura de W, proxy e resíduos, backbone, limites, dois insides,
amostras propostas, referência/gathers, RNG/bits, saída e memória.

Comparadores: head denso otimizado só nos n slots + quatro massas por slot +
DP de contagem O(n²), head apenas nas linhas elegíveis quando reduzidas,
amostragem direta racional do alvo, rejeição independente (controle fraco
explicitamente identificado), e rejeição com o mesmo envelope sem squeeze.
Não usar um parser cúbico artificial para a gramática de contagens.

Um proxy INT8 ainda custa O(nVd) operações, com menor precisão; não supor
FP8 ou velocidade INT8 da 3080 Ti sem kernel implementado. Proxy de posto r
custa O(ndr+nVr); sua preparação e erro residual não são gratuitos. Guardar
W, proxy, resíduos, chart e backpointers. O regime assintótico construído não
é lower bound contra todos os circuitos nem hipótese verificada num modelo.

## Protocolo congelado V1

**Offline, sem timings:** `check.py`, stdlib Python 3.11. Não reproduzir a
mesma contagem de 298 leis/340 strings: o briefing não trouxe seus vetores
nem seu programa. São alegações anteriores, não dados congelados. Novos
casos fixos: todas as 6^4 tabelas locais (L,w,U) com L em {0,1}, w em {1,2,3},
U=3, sobre G={01,10}; todos os 4^n strings n=2,4,6 para a CFG de dois modos;
aliases m=2 em n=4; pesos 1..9 com seed 740201, n=2,4,6 e m=1,2, oito casos
por par. Verificar massas contra enumeração independente, todas as leis
aceitas, fórmulas de consultas, fallback J=0,1,2,4 e lei condicional do timeout.
Sampler mínimo com J=4 e fallback denso, 16 draws por caso, seed 740202.
Kernel E_b na grade t=k/64, k=-64..64, b=8,12,16, e intervalos de resíduo
delta=1/8,1/4, n=2,4,8. Incluir L=0, massa vazia, fixed positions, alias,
gauge e dois modos adversariais r=1,2,3 e n=2,4,8.

**Triagem neural, antes de implementar sampler GPU:** MDLM-OWT revision
`d0958fa851335ece6c15260ce0025f030673c0fb`, hashes da configuração M31
versionada. Cache absoluto `/home/jota/projects/tcc-final/.cache/mdlm`, somente
leitura. Adaptar em memória o mesmo port auditado de atenção do repositório;
não usar o loader que escreve no cache principal. Torch FP32, quatro threads,
seed 740203; dois prefixos literais `Return a balanced sequence of A and B:`
e `Complete the structured payload:` (tokenizer GPT-2 pinado na M31), cada
um seguido por n=8,32 masks; timestep=0. Capturar o input do linear final
com pre-hook e interromper antes do head, sem logits referência completos.
Vocabulário de triagem: IDs 0..50256 exceto EOS=50256; mask=50257 excluído,
PAD ausente. Bias mantido exatamente no proxy. Não são saídas gramaticais.

Dois proxies sem ajuste por dados: (1) cada linha INT8 com escala potência
de dois mínima que cabe em [-127,127], nearest ties-even; (2) posto 1 retendo
a primeira coluna de W. Limite de logits por Cauchy: eps_iv=rho_v*eta_i,
rho>=||Wv-Qv||2 e eta>=||hi||2. Normas certificadas por inteiros em grades
2^-24 (resíduo) e 2^-16 (h); floor/ceil e isqrt, sem soma floating point.
Para cada estado registrar a cota inferior racional
`a=2 min_v rho_v sum_i eta_i`; então `R>=exp(a)` para QUALQUER evento não
vazio nesse suporte. A prova consta de proof.md. É uma cota do envelope,
não lower bound de rejeições reais nem de todo proxy possível.

Gate: se o polinômio positivo sum_{k=0}^{16} a^k/k! exceder 4, recusar essa
variante (`ENVELOPE_GATE_REFUSAL`). Se alguma variante não for recusada,
registrar `NEEDS_EXACT_MASS_AND_CONSUMER`; só R<=4 certificado por massas e
um consumidor de bytes admissível justificariam protocolo posterior de custo
integral. Não improvisar um benchmark novo após ver os dados. Nenhum resultado
de triagem é speedup nem refutação de todo método. Gate de novidade continua
separado e pode rejeitar a candidatura mesmo com um envelope útil.

Todo uso de GPU **e timings** sob flock exclusivo
`/tmp/tcc-final-candidate-tests-gpu.lock`, nvidia-smi antes de iniciar, sem
concorrência compute, sem matar processos. Priorizar CUDA já instalada em
`.venv-live` do checkout principal, só leitura. Recusar GPU se indisponível
ou ocupada, sem interpretar recurso como resultado científico. Limite externo
180 s para triagem, memória livre mínima 2 GiB. Uma captura por estado,
sem warmup/repetições: custos são diagnósticos até a recusa, nunca benchmark.
Registrar setup, captura, normas, memória, ausência de chart/RNG/saída e de
head/proxy projetados; não comparar esse tempo incompleto com decoder completo.

## Reprodução e decisão

Comandos e resultados finais ficam em `result.md` e JSONs pequenos. Não alterar
os casos/gates desta V1 após executar. Modelos, tensores e caches não entram
no Git. Biblioteca, vendor e status globais permanecem fora do escopo.

### Emenda V1a anterior aos dados de modelo

A execução CUDA V1 recusou ANTES de carregar o modelo: um `llama-server`
de outro projeto ocupava a GPU. `screen-v1.jsonl` preserva a recusa de
recursos, que não é um resultado negativo do método. Não matar esse processo
nem medir sob concorrência. Autoriza-se a MESMA triagem, quatro estados e
dois proxies/gates inalterados, com `--device cpu` e o mesmo port FP32.
Nessa opção não se consulta a GPU, não se lê relógio e todos os campos de
timing/GPU são null; não há lock necessário para trabalho CPU sem timings.
O h capturado é o da execução CPU declarada: não alegar identidade com h
CUDA. Sem novo prompt, seed, proxy, treinamento ou campanha de desempenho.
Os dados CPU terão caminho novo `screen-cpu-v1a.jsonl`. A falta da medição
GPU permanece uma limitação, mesmo que os envelopes CPU sejam recusados.

Correção de implementação V1b, ainda antes de qualquer captura: V1a falhou
no TorchScript, `RuntimeError: Expected a single top-level function`, porque
o loader em memória atribuía ao fonte transformado o caminho/linhas do
original. O JSON inicial fica preservado e a falha não conta como recusa do
envelope. A correção fornece o fonte transformado ao `linecache` em memória,
sem gravar no cache compartilhado. Nenhum peso, caso ou gate muda. Dados
do produtor corrigido vão para `screen-cpu-v1b.jsonl`.

Correção numérica V1c: V1b carregou/hash-verificou o modelo, mas a primeira
checagem independente Fraction recusou a norma: o booleano NumPy do arredondamento
de isqrt propagava `np.int64` ao numerador de Fraction e causava `OverflowError`.
Converter explicitamente esse incremento para int Python corrige o tipo sem
mudar a fórmula do intervalo. Nenhuma captura h ocorreu. Saída parcial V1b
preservada; execução corrigida usa `screen-cpu-v1c.jsonl`. O erro é de software,
não recusa do proxy nem evidência de impossibilidade científica.
