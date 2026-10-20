# A74 V2 — Decisão operacional, antes dos novos dados

O usuário pediu explicitamente continuar até uma decisão sustentada por testes,
após esclarecer que V1 só testou correção/envelopes e NÃO mediu velocidade.
Esta autorização substitui a parada da V1; seus casos, dados e conclusão não
serão sobrescritos. Base desta rodada: `2978222c88479046a60c772a0eee19c9f94f6f23`.

## Pergunta, hipóteses e consumidor

Em estados de MDLM reais, um proxy barato COM limites certificados, proposta
CFG e squeeze custa menos que preparar/amostrar diretamente o mesmo alvo?
Medir aceitação real, fallback e custos integrais; R grande sozinho não decide.
Método continua sendo OS* + squeeze + inside clássicos (fontes da V1).
Uma vitória operacional não provaria novidade matemática. Uma derrota desta
rodada decide o investimento de TCC nesta formulação, não todas as variantes
matematicamente imagináveis. Não alterar proxies/casos depois dos dados.

Consumidor favorável à A74: o mesmo evento de modo constante e contagens A/B
iguais, agora sobre IDs GPT-2 0..50255, classe `id % 4`; modo=classe//2,
tipo=classe%2. Todos os 50.256 IDs são elegíveis em qualquer slot. A CFG
de excursões da V1 é não ambígua e se aplica às quatro classes. Emitir os
IDs e seus bytes GPT-2 originais, sem deduplicar aliases. É uma linguagem
construída sobre o alfabeto de IDs, NÃO uma gramática JSON sobre bytes.
Nenhuma alegação de utilidade semântica/decoder nativo. Usar esse consumidor
evita derrotar artificialmente a proposta com somente quatro linhas legais.
O controle competente soma quatro massas e usa DP de contagem O(n²), CDFs
inteiras por classe e busca binária de IDs. EOS/mask excluídos, PAD ausente.

## Referência numérica operacional explícita

V1 tinha referência conceitual idealexp e não implementou um sampler de
modelo. V2 implementa OUTRA referência finita, declarada antes da captura;
baseline, consultas e propostas serão verificados contra a mesma lei V2.
Não alegar identidade com V1 idealexp, torch.softmax ou trajetória nativa.

W12=round_even(4096 W_fp32), H10=round_even(1024 h_fp32), bias22=
round_even(2^22 bias_fp32). Dot de referência **inteiro exato**:
S_iv=sum_d W12_vd H10_id + bias22_v. Admitir somente W12/H10 em
[-16384,16383], com guards de overflow; recusa é preservada, sem mudar bits.
Índice k=clip(floor(S/2^14), -8192,8192). Peso inteiro T[k], tabela universal
`ceil(65536 * Decimal80.exp(k/256))`. A tabela literal gerada, positiva,
monótona e <2^63, é a definição numérica; guardar seu hash. Clipping e
racionalização são parte declarada desta lei, não poda de IDs/cauda.
O posterior produto condicionado usa esses inteiros e RNG inteiro exato.

Dot denso competente: (a) decomposição exata base 128 em quatro GEMMs INT8
com acumulação INT32 e recomposição INT64; (b) GEMM FP64 sobre esses inteiros,
cujo limite de soma absoluta <2^53 torna produtos/somas exatos. Comparar ambos.
Consultas de pares slot/ID usam multiplicação/redução INT64 exata. Todos os
dots e pesos densos dos dois caminhos devem coincidir, e uma seleção fixa
de pares será conferida por somas Python int independentes. Tabela não usa
exp CUDA. Não comparar discretizações diferentes como se fossem a mesma lei.

## Proxies sem treinamento e limites

INT8 por linha: quantizar W12 com menor escala inteira potência de dois
que caiba em [-127,127]; H10 mantido. Dois GEMMs INT8 produzem q exato.
SVD rank 8,32,128: autovetores principais de W12^T W12, em FP64 CPU;
coeficientes/fatores arredondados para grade 2^-10, sem treinamento ou
calibração nos h. Q=A10 B10 /2^20. Sua execução usa GEMMs FP64 de inteiros,
com guard de soma absoluta <2^53, certificando q=A10(B10 H10) exato.
Não tratar a SVD computada como uma prova espectral: limites usam o resíduo
EXATO dos fatores inteiros produzidos, comparado com W12 escalado por 256.

Para ambos, rho=ceil(sqrt(sum E_vd²)), eta=ceil(sqrt(sum H10_id²)),
com somas inteiras e isqrt, denominadores comuns 2^22 ou 2^30. Limite
inteiro B_iv=rho_v eta_i >= |Sref-q| na mesma escala. Aplicar a tabela
monótona aos índices de q-B e q+B produz L<=w<=U racionais exatos.
Conferir esse enclosure contra TODOS os pesos densos no diagnóstico,
sem fornecer a tabela alvo ao sampler candidato. O custo do diagnóstico
fica separado; a preparação de resíduos, fatores e limites entra no método.

Cap J=4 fixo e fallback denso independente preservam a lei, conforme V1.
Testar cada proxy com ambos os fallbacks densos: oito variantes, sem escolher
depois uma implementação favorável. Baselines diretos também usam os dois
heads. Cache entre repetições só de W/fatores/tabela; cada chamada representa
um head fresco e paga preparação das massas/CDF/chart. Repetir draws do mesmo
head preparado é outro consumidor e não é usado para amortizar injustamente.

## Casos, fontes e sequência congelados

MDLM-OWT/cache/revision/hashes/tokenizer da V1, somente leitura. Mesmo port
auditado em memória. FP32, quatro threads, TF32 desabilitado, seed 740301.
Prefixos literais V1, cada um com n=8,32,128 MASKs, timestep=0: seis estados.
Um warmup e três capturas de backbone por caso; guardar h da primeira captura
e hashes/IDs. Nenhum treinamento, alteração de vendor ou novo modelo baixado.

Antes de timings: oráculos pequenos do sampler/CDF e kernel inteiro, incluindo
overflow de CDF uint64 com carry explícito, aliases, fixed positions e cap.
Congelar em commit protocolo e fontes. Depois, na ordem declarada: setup
modelo/tabela/proxies; capturas; igualdade/enclosure e taxa real por massa;
warmup de cada variante; 11 repetições completas, ordem rotativa por caso e
repetição. RNG seed 740302 + 10000*caso + 100*repetição + índice_variante.
Não regenerar seeds/perdas/rejeições para melhorar um resultado.

Taxa de aceitação **real** p=Zw/ZU, probabilidade de fallback (1-p)^4 e
probabilidade de consulta q=1-ZL/ZU serão reconstruídas de massas inteiras.
Além dos dados por draw, guardar custos determinísticos previstos por essas
massas. Nenhum estimador Monte Carlo substitui essas identidades.

## Recursos, custos e decisão

TODO uso de GPU e timings sob flock exclusivo
`/tmp/tcc-final-candidate-tests-gpu.lock`. nvidia-smi antes de iniciar;
exigir >=2 GiB livres e três observações de GPU ociosa. V1 recusou pela
presença de um processo residente; presença com VRAM alocada não demonstra
execução concorrente. V2 permite processo residente ocioso, sem pausá-lo ou
matá-lo. Monitor pmon durante a campanha; atividade compute alheia observada
invalida timings e interrompe a campanha, preservando dados. Registrar
telemetria indisponível e processo residente: ausência observada de atividade
não é prova de isolamento físico. Não publicar vantagem se interferência
ficar demonstrada. Limite externo 900s, teto 2 GiB de novas alocações CUDA.

Contar carga/hashes, SVD e demais preparações, pack/transfers, backbone,
proxy, limites, D2H, inside/CDF, proposta, consultas e gathers, fallback,
RNG, bytes de saída e memória. Inteiros de chart e bits RNG registrados.
Baseline e candidato têm mesmo backbone; reportar head+sampler e total com
backbone, separadamente. Preparação por modelo: uma vez e amortização
EXPLÍCITA em T=1 e T=32 heads frescos (hipótese, não 32 novas capturas).
Fonte e dados finais <=2 MiB, tensores ficam em cache local ignorado.

Gate prévio para manter esta versão como aposta operacional: alguma das
oito variantes, em algum dos seis estados, precisa ser correta, vencer
AMBOS os controles em todas as 11 repetições pareadas, ter ganho mediano
>=10% em head+sampler e também >=10% no total com backbone e setup amortizado
em T=32. Guardar todos os casos, inclusive os demais fracassos. Gate é regra
de seleção de engenharia desta rodada, não prova de novidade nem garantia
estatística universal. Se nenhuma passar, descartar esta formulação como
aposta principal para o TCC no hardware/contrato testados; não inventar nova
variante para resgatar. Se recurso/correção impedir a comparação, diagnosticar
e corrigir separadamente antes de concluir; não usar recusa como derrota.

## Correção V2b antes da primeira comparação

V2 carregou/preparou o modelo e capturou o estado 0, mas recusou a primeira
chamada `_int_mm`: `self.size(0) needs to be greater than 16, but got 16`.
PyTorch 2.8 exige padding M>=32 nesse caminho, não somente múltiplo de 16.
Corrigir padding por zeros para 32 preserva TODOS os dots/pesos. Incluir
um smoke test GPU de 1.280 células, com n=8 e n=32, antes de carregar o
modelo novamente; seu custo entra no setup comum. Também aquece conversão
de h para não atribuir sua primeira inicialização a cada head fresco.
`measurements-v2` preserva a falha e os tempos parciais, sem nenhum draw
comparativo. A nova execução irá a `measurements-v2b`, com casos, sementes,
proxies, referência, número de repetições e gate inalterados.

## Emenda de recursos V2c, ainda antes de qualquer draw comparativo

V2b recusou antes do oráculo/kernel: GPU estava ociosa em duas observações,
mas chegou a 75% na terceira. O servidor externo está intermitentemente ativo.
V2 inicial também registrou atividade alheia durante setup no pmon: seus tempos
parciais NÃO são medições isoladas. Preservar ambos os diretórios.

Para obter comparação sem concorrência, manter um modelo preparado e esperar
três observações ociosas antes de cada bloco das mesmas dez variantes. Monitorar
entre variantes e por mais 1,1s após cada bloco para cobrir a janela pmon.
Se houver atividade alheia, marcar e preservar todos os draws do bloco como
`timing_valid=false`; interromper o bloco e tentar novamente, com EXATAMENTE
as mesmas seeds, no máximo três vezes. Usar o primeiro bloco válido, nunca
selecionar por velocidade. Continuam onze blocos válidos por caso, mesmas
ordem rotativa e métricas. Um draw lento, uma rejeição ou um fallback NÃO
autoriza repetição. Espera ociosa tem limite de 180 observações de 1s por
bloco; teto externo passa a 1800s para essas esperas, sem ampliar casos.

Capturas e setup também recebem flags de validade do monitor. Tempos de setup
com interferência são diagnósticos, não usados para alegar vantagem; uma
derrota já no custo quente, concedendo setup gratuito ao candidato, continua
decisiva independentemente desse setup. Exportar ambos, sem ocultar o limite.
Dados completos terão caminho novo `measurements-v2c`; não sobrescrever dados
anteriores. Essa alteração é exclusivamente de isolamento/recuperação de
recursos, não muda a lei, os proxies nem o gate científico.
