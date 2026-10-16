# AGENTS.md

A52 começa ESCRITA antes de protótipo: probabilidade da ação realmente
selecionada por confiança (limiar/fallback ou top-k) como partição gramatical
com evidência unária dos descartes. Contagem, score condicional e redução de
variância são clássicos; DUEL seleciona posições antes dos tokens, MAPG usa
PL, e os contratos não são confundidos. Gradiente exige comparação localmente
estável em TODO suporte; não declarar política globalmente suave nem suporte
PPO automaticamente compatível. Família checksum conectada separa apenas o
score completo, inclusive seu melhor baseline escalar; enumeração/média
condicional clássica continuam controles. Após freeze238a356, seis oráculos
racionais passam108 leis1372 ações15092 componentes de score;211 testes
PASS72.391s e make check/Ruff PASS. Há contraexemplo ao score só dos retidos
(-21/100 real versus0), mas o score COMPLETO continua correto. Nenhum novo
head/treino/timing, novidade suficiente ou benefício real A52 foi confirmado.
V2 escreve antes de código uma política DIFERENTE: proposta gramatical e gates
Bernoulli dependentes do token, condicionados conjuntamente a máscara não vazia.
Compiler OR positivo de dois estados e likelihood marginal suave são aplicações
clássicas, não novidade assumida. Muda a marginal da proposta; reamostrar só os
bits de uma palavra fixa dá outra lei. dUltra/Learning Unmasking Policies já
usam Bernoulli e a versão por posição é controle competente mais barato.
Somente oráculo pequeno é justificado; nenhum novo head/treino/timing ou ganho.
Após freeze651b8dd, cinco oráculos V2 passam8 leis conjuntas256 ações4096
componentes de score e31 estados FALSOS/52 trajetórias observadas/88 auxiliares.
Full216 testes PASS73.155s e make check/Ruff PASS. MD4§6 já fornece schedules
dependentes do valor do token; não reivindicar isso. Nenhum peso/modelo/head
novo foi carregado: apenas metadados públicos de Tiny-A2D foram lidos.
V3 escreve antes de código a âncora auxiliar independente de X, forçada a
liberar: preserva P da proposta ATUAL e permite integrar âncora/descartes por
um escalar só dos retidos e partição unária. Forçar âncora, mistura/WMC/RB são
clássicos; novidade/uso não confirmados. Âncora fixa e gates por posição são
controles mais baratos e obrigatórios. Não atribuir oráculos V1/V2 a V3.
Após da3bd39, quatro oráculos V3 passam8 leis256 ações4864 componentes e
5 estados FALSOS/12 trajetórias observadas/24 completas, com chain rule e
controles analíticos. Full220 PASS73.333s; make check/Ruff PASS. Ainda sem
head real/update/timing novo. Cabeça Tiny-A2D V151936 excede tokenizer0..151669;
qualquer consumidor futuro deve declarar os IDs extras, não truncá-los calado.
V4 é SOMENTE contrato de recursos, antes de código/heads:8 perguntas GSM8K
de desenvolvimento JÁ conhecidas,32 slots, Tiny-A2D pinado, no máximo9 forwards
incluindo warmup/quatro amostras por head. Sem gabaritos/update/timing competitivo.
Declara todos151936 IDs, inclusive os266 sem token caso TODOS decodifiquem vazio,
JSON numérico irrestrito/EOT/PAD, controles, tolerâncias e recusas. Seis casos
corretos só permitem considerar protocolo de custo/variância separado; não são
vantagem útil/novidade. Runner/runtime precisam congelar antes do primeiro head.
Fundação V4 inicial:18 oráculos focados PASS1.532s,22608 palavras pequenas,
tokenizer oficial151936 IDs/4096 triplas sem erro,266 vazios preservados.
Compiler clássico tem38 classes/22 estados/92 arcos;48 checks NumPy/Torch
CPU/CUDA contra Fraction têm erro máximo de log~1.78e-15 nos brinquedos.
Não é bound global, lei GPU exata ou benefício neural. Runtime isolado importa
fonte pinada, sem instância de modelo; runner/captura ainda pendentes.
Preflight final V4:19 oráculos focados/full224 PASS74.209s, make check/Ruff
PASS. Três ações sintéticas full-V/32 slots usam421728768 bytes;48 checks
refinados incluem descartes. Cinco forwards de arquitetura ALEATÓRIA verificam
recorte/bidirecionalidade/padding e loading BF16 explícito. Pesos pré-treinados
baixados/hash conferido, mas ZERO forwards deles. Runner/protocolo congelam
antes da captura limitada; não há ganho/treino ou novidade confirmada.
Captura V4 após854a733 concluída8/8:9 forwards NOVOS incluindo warmup,
32 JSONs válidos, zero recusa/erro; logits/IDs/scores/dados completos preservados.
Erro máximo log CPU/GPU3.553e-14; sampler<=422932672B. É só recurso/correção,
sem gabaritos/update/variância/ganho competitivo. O gate6/8 só permite
reavaliar protocolo separado de custo/variância; meta científica ainda aberta.
V5 escreve antes de código/heads o controle que integra APENAS a âncora:
O(n+|B|), sem consulta, mesmo score de âncora da candidata. Não ganhar só
contra o full triple. Derivadas compactas por classes são clássicas. Protocolo
de necessidade usa duas etapas reais,8 estados conhecidos,16pilot+64eval,
máximo641 forwards novos, gabaritos após captura, controles fitted/zero/RLOO;
passar20% de variância ainda não é custo completo/treino/publicação. Só
oráculos mínimos antes de congelar runner. PUMBA/x-Prediction já são
alternativas de treino/planejamento; novidade/benefício A52 seguem abertos.
Preflight V5 depois de4b2fb1f passa full229 testes74.834s/make check/Ruff,
incluindo controle reverso/compacto, IDs fixos/números enormes e lei RLOO de
grupo. Dois forwards ALEATÓRIOS BF16 validam head por índices. Runner/analyzer
congelam antes de novo head; ainda sem medições de variância/treino V5.
V5 após e01739d completa640/640 trajetórias/629 forwards NOVOS incluindo
warmup, todos IDs/JSONs válidos, zero recusa/erro. Gabaritos após captura dão
ZERO acertos, confirmados independentemente por Decimal; variação0/8, nenhuma
razão/ganho de variância é creditada. Aplicação encerrada NEGATIVA; não
acionar custo/treino/novos seeds nem relaxar gate. Todos heads/scores/labels
preservados. PAD no sufixo versus parada/marginalização é hipótese diagnóstica
separada a escrever ANTES de código; sem novidade assumida ou relabeling.
V6 escreve essa auditoria antes de código: parada no primeiro EOT integra
todo sufixo, lei distinta do alvo FULL-WORD anterior JSON EOT PAD*. Fonte
nativa sample_trim foi lida pinada; não se afirma histórico exato de treino.
Mistura/TV por comprimento/tilt monotônico são clássicos. Só oráculos pequenos
e depois TODOS8 heads VELHOS sem forward/gabarito/update novo. MASK pode ser
ID latente após EOT, exigindo bits ativos explícitos em consumidor futuro.
Não chamar a correção de semântica de nova teoria ou conquista científica.
Dois oráculos V6 após6335f52 passam leis originais/TV/ordem de comprimento,
IDs fixos/EOT/MASK no sufixo e massa PAD zero; full231 PASS74.457s, make
check/Ruff PASS. Auditoria TODOS8 heads velhos congela fonte/protocolo antes
de cálculos, sem novos forwards/amostras/labels/updates.
V6 produtor d38b843 conclui8/8 heads VELHOS: TV de comprimento0.869119--
0.999971, E_padT-E_stopT6.475331--18.191402 slots;8/8 condição diagnóstica.
Checks independentes/arquivo max1.422e-13 log. ZERO forward/amostra/label/
update novo. É diferença de contrato/lei, não causa ou ganho semântico,
novidade ou treino. V5 continua encerrada negativa; só novo contrato escrito
de consumidor parado antes de qualquer campanha. Meta científica aberta.
V7 escreve ANTES de código a âncora elegível só dentro do prefixo parado,
mantendo TODOS IDs fixos no retorno. Normalizador dependente de T vira
potencial terminal; scores usam ocupância e posterior de comprimento.
Inferência/médias condicionais são clássicas. Controles baratos integram A,
T, IDs dentro de classes e combinações; não vencer só full triple. Somente
oráculo racional mínimo, sem novos heads/labels/updates/timings. Benefício
próprio/novidade e meta seguem abertos; V5 não é reaberta.
V7 após1ecf413/e686287 tem cinco oráculos PASS5.089s:5 leis2701 triplas484
ações31790 coordenadas, duals exatos de cabeça/gates/normalizador, redução
ao V3 com T fixo e35 estados FAKE. O objeto de prova tem traço alpha/âncora
estritamente menor inclusive contra controle combinado, não benchmark neural.
Full236 PASS84.581s/make check/Ruff PASS. Nenhum head/update/sampler nativo
ou ganho útil/novidade confirmados. Só novo consumidor escrito antes de código.
V8 escreve antes de implementação/heads a calibração SIGMOID clássica da
contagem só no ROOT, fixando o feature depois (sem implicit gradient omitido
em parâmetros novos). Contrato usa TODOS8 roots conhecidos/duas trajetórias,
parada correta/IDs fixos/bits explícitos, máximo497 forwards novos, baseline
one-shot pareado. Sem updates/timing/qualidade comparativa; gate de recurso/
sinal só permite considerar protocolo de custo/variância com controles fortes.
Oráculos e congelamento real de runner/runtime antecedem novos heads.
V8 preflight passa cinco novos oráculos CPU,111 comparações racionais NumPy/
Torch CPU/CUDA e três ações sintéticas full-V, pico340684288B. IDs fixos,
ocupância variável, calibração e TODOS controles parciais conferem. Full241
PASS79.352s/make check/Ruff PASS. Fontes iniciais e finais separadas; protocolo/
runner/runtime congelam ANTES do primeiro novo head. ZERO update/head real V8
até esse freeze; não é benefício neural, novidade ou meta cumprida.
V8 captura b6c7bb8 termina16/16 trajetórias válidas/113 transições,98 forwards
NOVOS (um warmup), zero erro de score/ID. Mas sinal0/8: candidato0/16 acertos
e one-shot0/16, confirmado por tokenizer/json/Decimal. Inicialização encerrada
NEGATIVA; sem treino/novos seeds/custo-variância/independente. Monitor NVML
registra seis polls de outro processo DURANTE preparação CPU, nenhum durante
novos forwards: isolamento da captura inteira NÃO cumprido. Relatório original
de recurso8/8 fica intacto, mas não é pass integral/tempo competitivo. Draft de
assertion do auditor e desvio estão preservados; não repetir para resgatar a
aplicação. TODOS heads/contextos/scores/gates/statuses/golds e checks arquivados.
V9 escreve ANTES de código um objetivo supervisionado por likelihood visível
e caminho de referência independente. PAPL já fornece ELBO/marginalização;
Jensen e amostragem de tempo são clássicos. Gradiente é do BOUND, não da
likelihood final ou recompensa. Só oráculo racional mínimo é justificado,
sem head/update/Tiny rescue; política CE supervisionada/grammatical e SFT
são controles obrigatórios. Diferença própria útil/publicação ainda abertas.
V9 após43f99f4/2112613/42f5972 passa cinco oráculos0.668s:7 leis247 ações,
30 alvos330 caminhos,30 gaps variacionais estritos/identidades de gradiente,
32 estados de ocupância. Doze contraexemplos de política só por posição com
EOS fixo têm gradiente do bound0 e likelihood final não zero (9/112 num caso).
Não refuta o caso dependente do token, mas impede promover o bound como
aprendizado útil automático. Full246 PASS81.280s/make check/Ruff PASS; zero
head/update novo. V9 é controle supervisionado, não protagonista/campanha.
V10 escreve antes de código novo consumidor LLaDA NF4/BF16 pinado, V126464,
115 IDs indefinidos a auditar, EOS=PAD126081 e prefixo JSON dado/64 posições.
Todos8 casos conhecidos/duas trajetórias, máximo1017 novos forwards; só
recurso/sinal, nenhum update. Projeção nativa inclui prompt/IDs fixos e custa;
não inventar API indexada. Oráculos/auditoria lexical/preflight/congelamento
antecedem heads. Native20/32 é outro decoder, não ganho desta política.
Preflight V10 passa126464 IDs oficiais/4096 triplas,115 vazios, seis shards
originais com hashes conferidos. Cinco oráculos CPU incluem EOS=PAD, prefixo,
IDs fixos e latch de processo externo durante preparação. Sessenta checks
racionais NumPy/CPU/CUDA e três full-V/64slots passam, pico546382336B,
log máximo1.706e-13. Full251 PASS80.108s/make check/Ruff PASS. Prompts89--127
tokens/prefixo3 IDs conferem; runner/runtime/protocolo congelam antes de
instância/head pré-treinado. Ainda zero head/update V10/benefício confirmado.
V10 após e6ef83b completa16/16 trajetórias válidas/70 transições,63 forwards
NOVOS (um warmup/oito roots/54 seguintes), zero erro de score/ID. Recurso8/8,
sinal4/8 (6/16 acertos, one-shot2/16) passam o gate de VIABILIDADE conhecido;
não é superioridade semântica/variância/velocidade. Auditoria posterior confere
63 heads/32 respostas Decimal/536 polls sem processo externo. Modelo todo
congelado, zero updates. Só considerar NOVO protocolo de custo-variância
com controles fortes, inclusive baselines condicionadas à proposta quando
legítimas. Nenhum treino/confirmação independente/publicação acionados.
V11 escreve ANTES de código baseline condicionada à proposta e correção
grad J_proxy(a)/K(a) após marginalizar. Princípios de baseline/RB são clássicos;
sem backbone congelado/proposta independente a identidade não vale assim.
Todos controles parciais recebem o mesmo proxy exato, com baselines fortes
de estado/horizonte/greedy/proposta/RLOO e ajuste independente. Só oráculo
racional pequeno é próximo; nenhum novo head/treino/ganho confirmado.
Após17a689a cinco oráculos V11 passam4 leis821 triplas193 ações/122 eventos
proxy zero,39 estados FAKE/168 caminhos. Projeção/zero mean/PSD/derivada real
conferem; atalhos têm viés359/18080 e1/50. Draft falho do DFA preservado.
Full256 PASS83.064s/make check/Ruff; zero head/update novo. É correção, não
benefício útil/novidade. Replay funcional ALL70 heads velhos exige novo freeze.
V12 escreve subconjunto regular de grafias de inteiro correto antes de código.
1260 casos regex/Decimal,137 queries racionais/35 zeros e12 checks autodiff
CPU passam. Full259 PASS83.760s/make check/Ruff; guards novos de underflow
têm rerun focado posterior. Replay ALL70 transições VELHAS deve congelar
runner/runtime/inputs antes de cálculos, sem novo head/sample/update/label.
É funcionalidade, não variância/custo competitivo, novidade ou treino.
V12 GPU foi recusada no startup por processo externo, antes de queries:70
NOT_RUN preservados. V13 escreve variante CPU separada antes de adaptar;
após0381620 TODOS70 estados reais VELHOS passam (33 positivos/37 zeros), erro
máximo1.043e-14, RSS1,692,696,576B. Auditoria posterior70 tokenizer/Decimal
confere24 propostas corretas/nenhuma perdida pelo proxy NESTAS amostras.
Zero novo head/sample/update/label; não atribuir isolamento/tempo GPU ao CPU.
V14 escreve controles semânticos brutos de média zero para TODOS métodos,
nove parâmetros comuns e ajuste independente. Ainda sem vantagem útil,
novidade suficiente, treino ou confirmação; meta permanece aberta.
V15 escreve diagnóstico exploratório de TODAS16 trajetórias VELHAS antes
de calcular variâncias: ator9 fixo, sete scores/quatro baselines/27 controles,
756 configurações preservadas. Três oráculos passam243 derivadas racionais
e contraexemplo RLOO(1/6 real versus1/9 atalho). Full262 PASS88.756s/check/Ruff.
Fonte/runtime/inputs congelam antes do diagnóstico. Duas trajetórias por
questão NÃO confirmam ranking; RLOO tem variância não estimável/null. Zero
novo head/sample/update/label; custo completo/novidade/benefício abertos.
V15 apósf106532 completa756 configurações/TODAS16 trajetórias70 estados:
mínimos escolhidos NESTAS amostras favorecem class0.00369058 versus visible
0.00485158, cerca31.46% maior; todos mínimos têm coeficiente0 no proxy regular
da grade fixa. É exploratório de duas trajetórias por questão, não superioridade
populacional/refutação ou gate. RLOO tem variância null. Auditoria posterior
159706 coordenadas/1512 grupos passa2.132e-14. Dados completos preservados;
sem nova geração/treino. Não iniciar campanha grande baseada só nesse colapso.
V16 escreve reuso condicional COM baseline semântico completo antes de código:
posteriorq_B/(H_TQ_B), âncora condicional independente dos descartes e identidade
clássica V_visible+V_hidden/M. Quatro oráculos passam4 leis821 triplas193 ações,
momentos1/2/4 réplicas e192 checks de estratos correlacionados. Enumeração exata
permanece controle superior nos brinquedos. Full266 PASS90.701s/check/Ruff;
zero head/amostra auxiliar real/update. Novidade/benefício/meta abertos; replay
full-V exige contrato escrito separado e não recebe crédito de V15.
V17 escreve sampler full-V antes de código: integerCDF exato por categoria
com mensagens externas FP64, portanto NÃO certificado do posterior nativo.
83 leis pequenas têm L1<=6.317e-16;18 estratos retêm subnormal mínimo e três
kernels de par/20 folhas passam PSD para todo score. Verificador396 Decimal/
expoentes5000 dígitos passa. Full273 PASS109.220s/check/Ruff; synthetic24
full-V/FAKE560 (256 além de Decimal) passam sem mudar RNG, zero amostra auxiliar
real/head/update até freeze. Replay ALL70*8=560 exige produtor/inputs pinados;
é funcionalidade, não variância/custo útil, treino, prioridade ou meta cumprida.

## Objetivo e estado atual

Estas instruções valem para o repositório inteiro. O objetivo é desenvolver uma
contribuição científica útil para **geração de textos estruturados por GLCs
com modelos de linguagem por difusão (dLLMs)**, especialmente JSON e DSLs.
O usuário pretende publicar o artigo e usar esse trabalho na candidatura ao
mestrado. A meta exige uma vantagem relevante e bem sustentada sobre métodos
competentes; organizar tentativas ou documentar que uma ideia não funcionou
não satisfaz, por si só, esse objetivo.

O projeto não está limitado a encontrar uma aplicação para MWPC. Atualmente:

- `src/mwpc_exact/` mantém posterior gramatical exato no suporte declarado,
  commitment MWPC, certificados e integração. Serial, EPIC e exact continuam
  como estratégias separadas; suas garantias devem ser preservadas.
- `scripts/exact_commit/semantic_json.py` e `adaptive_semantics.py` são
  referências de pesquisa sobre regras Booleanas condicionadas por execução,
  refinamento adaptativo e núcleos semânticos certificados. Não são um novo
  decoder de produção nem um modelo dJev treinado.
- As tentativas 15/16 foram rejeitadas pelo usuário como protagonistas. A
  tentativa 17 audita reamostragem latente após seleção Plackett–Luce: há
  referência racional, oráculos e provas escritas delimitadas. Um estudo externo
  executou forwards e gradientes da cabeça real de MDLM, com backbone congelado;
  não houve atualização de parâmetros, treinamento completo ou prioridade
  confirmada. Réplicas correlacionadas por variáveis
  auxiliares também precisam ser consideradas na aplicação de redução de
  variância; réplicas independentes não são automaticamente necessárias. MH
  estacionário foi implementado e medido; a alternativa contínua de Gibbs
  permanece apenas derivada. Nos 12 casos neurais pequenos, enumeração com
  média condicional venceu inclusive o piso de sobrecusto zero dos samplers iid.
  A auditoria final de lote usa 13 métodos/configurações e todos os 48 eventos
  originais: a mistura tem ganho predeclarado de pelo menos 20% em três eventos
  com circuito disponível, dois incluindo compilação. O prefixo 1024 não tem
  esse ganho. A decisão delimitada está em `work/usefulness-decision.md` da
  tentativa 17; não é superioridade de geração sobre EPIC ou treinamento
  completo. Controles tiveram mais recursos para evitar vitória por teto de
  tabelas, e todos os resultados desfavoráveis foram preservados.
- A tentativa18 investigou preservação da política gulosa no suporte top16
  congelado. CPU/GPU e refinamentos com poda, Rust, prefixos compartilhados,
  atalhos e busca guiada pela raiz estão preservados; nenhum demonstrou o
  critério forte de vantagem total frente a todos os controles competentes.
  A propagação clássica continua uma alternativa importante. A tentativa19
  investiga união de suportes sugeridos por novos forwards, com controles que
  reservam32/64/128 tokens e bloqueiam explicitamente os ainda inativos.
  Os oráculos pequenos passam; 1.026 registros MDLM/CUDA e controles fortes
  não confirmaram o critério conjunto wall/CPU em nenhuma das18 configurações.
  Os resultados e recusas estão preservados; não relaxar o critério depois
  da medição.
  Não apresentar essas tentativas como nova teoria de parsing ou vitória EPIC.
  A tentativa20 investiga classes pelo efeito em todos os estados de um lexer
  JSON, preservando tokens originais e suportes crescentes. Inclui controles
  lexicais sem classes e métodos clássicos por classes. Princípios de lexer e
  quociente são antecedentes, não novidade; 864 registros e controles lexicais
  não confirmaram ganho adicional do quociente global. A tentativa21 investiga
  grupos locais possivelmente sobrepostos conforme o estado lexical explícito.
  Viabilidade original é união dos grupos; commit retém todos os grupos com
  o original, e crescimento com comportamento novo recompila. Os1.026 registros
  reais também não confirmaram ganho forte contra TODOS os controles de20.
  As três direções negativas estão preservadas, não satisfazem o objetivo.
  A tentativa22 investiga posterior JSON exato no vocabulário original inteiro,
  com classes globais e locais e rejeição exata como controles. Massa, marginais
  e lei do sampler passam em oráculos pequenos independentes. O protocolo foi
  definido antes dos novos forwards. Desenvolvimento original:6/18 ganhos fortes;
  refinamento original:7/36. Esses comparadores ainda precisavam de coacessibilidade
  lexical pelo contexto direito. A confirmação foi interrompida com50/810 registros,
  todos preservados; não é conquista confirmada. O refinamento v5 fornece trimming
  clássico às quatro representações e testa ambas as variantes locais contra seis
  controles de partições e um controle independente de pilhas preditivas. Todos
  recebem a equivalência sintática de valores atômicos; IDs/bytes são preservados. Seleção da candidata só no desenvolvimento; nova confirmação
  usará todos os cinco documentos elegíveis de outro corpus externo pinado.
  A medição v5 foi interrompida com171/540 registros, todos preservados: o controle
  de pilhas recalculava limites intrínsecos idênticos em muitos estados lexicais.
  V6 cacheia esses limites por camada antes de repetir todo o desenvolvimento.
  V6 foi encerrada inteira com411/540 registros (331 completos,80 recusas):
  auditoria negativa das condições necessárias prova que ambas as candidatas
  falham nas18 configurações, mesmo sem os129 timings restantes. Nenhum
  forward independente novo. A23 preserva cópias independentes e investiga
  scanner epsilon ponderado com circuito de proveniência de slots, fornecido
  a três representações como ablações do mesmo compiler. Remoção epsilon é
  clássica. A23 v1 também falhou:262/702 registros e dois pares individuais
  reordenados para uma auditoria apenas negativa, todos preservados. As três
  variantes são rejeitadas nas18 configurações; sem captura independente nova.
  A24 investiga certificado de aproximação por profundidade: identidade TV
  condicionada, bound de counter lexical e acoplamento da trajetória sob
  política comum estão escritos. Nove oráculos pequenos e168 comparações full-V
  passam; duas campanhas108+108 de viabilidade nos dados existentes estão
  preservadas. Handoff permite menor profundidade que grammar-hit em7/18
  quadros, mas isto não é timing competitivo. Há separação escrita de força
  de certificado com tokenizer fixo: depth constante versus linear, com
  consequência exponencial SOMENTE para pilhas explícitas. Não é lower bound
  de toda inferência CFG. A comparação completa inclui9 métodos e fontes
  imutáveis dos controles compactos, regra conjunta wall/CPU, custos completos
  e rejeição. Todos486 registros foram preservados:445 completos,41 recusas,
  ambas variantes3/18 ganhos fortes de consulta, também a frio,216 checks
  contra massa exata. Handoff é selecionado pela regra congelada de empate;
  nenhum ganho forte adicional sobre closed. A confirmação independente está
  completa:1215/1215 registros,1071 completos144 recusas,540 checks de massa,
 3/15 ganhos fortes de consulta para ambas variantes,2/15 de primeira amostra
  aproximada. O ganho20% é na mediana pareada wall E CPU frente a TODOS seis
  controles, com sinal favorável em todas repetições, não20% em cada repetição.
  Os15 estados vêm de TODOS cinco documentos externos elegíveis, sem seleção
  por resultado. O ciclo dLLM real está completo:30/30 execuções válidas,
 184 forwards novos, IDs fixos preservados, uma seed/sem erros. É demonstração
  funcional, não gate estatístico de latência inteira. A auditoria33/33 oferece
  amplificação estrita certificada e confere contra marginais completos;
  muda explicitamente q, não é qualidade semântica ou velocidade total.
  A25 investiga amostragem EXATA por envelope, sem excluir eventos profundos;
  tem prova escrita, sete oráculos pequenos e controle counter+CARS reforçado.
  OS*2012 já fornece o princípio geral de proposta superior/refinamento:
  não reivindicar esse princípio. A trajetória com orçamento finito tem FAIL
  e bound sum(delta_t^k), não igualdade incondicional. Protocolo13 métodos primeira amostra/lote32 teve702/702 registros
  de desenvolvimento:648 completos53 recusas1 erro de timer, todos preservados.
  Ambas variantes0/18 gates primários e1/18 secundário de lote; este NÃO é
  confirmação independente. Cada um dos36 pares candidato/estado falha
  contra outro controle totalmente concluído sem erro; a conclusão primária
  independe da falha do timer, que não recebe crédito. A fronteira de timer
  foi corrigida e verificada em dois novos checks; não relabelar medições
  anteriores nem atribuí-las à fonte corrigida. A fase independente
  condicionada não é acionada. O refinamento estático v2 que
  pula cauda inútil com massa rasa zero foi feito DEPOIS dos heads A24 e ANTES
  de timings A25; v1 e addendum preservados. Não atribuir os timings24 a25.
  Lean verifica nove enunciados novos de contagem/amplificação, não o sampler
  Python nem o decoder inteiro. A aplicação24 foi executada; a amostragem25
  foi medida, falhou no gate primário e não tem uso neural iterativo validado. Nenhuma prioridade
  acadêmica ou superioridade de geração geral foi confirmada.
- Há garantias matemáticas delimitadas de amostragem, rejeições e reutilização.
  A comparação escrita com CARS trata sua atualização de prefixos visitados
  sob hipóteses explícitas; não demonstra superioridade geral de latência.
  A auditoria pequena preserva enumeração mais rápida e custos de preparação.
- A vantagem delimitada de consulta24 está confirmada pela prova escrita e
  pelo gate independente3/15; não confundir com superioridade geral. Novidade
  específica na literatura, significância suficiente para publicação e
  vantagem prática ampla não estão confirmadas. Não inventar revisão humana.
  O artigo principal apresenta24;25 é extensão separada/resultado delimitado.
  A suíte atual tem164 testes, incluindo as duas regressões reais de timer,
  seis oráculos da fronteira amostrável A28 e cinco do reparo de colisões A29.
- A26 responde ao pedido de vantagem geral por uma operação distinta: lotes
  estratificados somente dentro de históricos completos idênticos, preservando
  cada trajetória individual. Há prova escrita de pass@K nunca inferior a K
  execuções iid do MESMO decoder para qualquer verificador, dominância da
  melhor pontuação e variância da média nunca maior.
  Eventos que ocupam um prefixo de tickets atingem min(1,Kp), ótimo entre todos
  os lotes de mesmas marginais; a hipótese não vale para qualquer semântica.
  Isso não exige estabilidade dos próximos logits, mas exige kernel independente das outras
  trajetórias, horizonte finito e não reunir históricos divergentes. Sete
  oráculos passam, inclusive recomputação independente do head público. Cinco
  especificações Lean verificam tickets e a desigualdade de dois estratos,
  não a prova adaptativa inteira ou o software. O primeiro replay top16 tem
  massa zero; o full-V do mesmo head gera64 JSONs válidos, sem novos forwards.
  A auditoria exata do evento de IDs de origem é estrita em K=2/8/32, mas
  pequena no caso (cerca de0,0104 ponto percentual em K=2). Não é melhoria
  semântica medida. Mais históricos distintos podem aumentar forwards únicos
  com caching, e a coordenação tem custo. Princípios de estratificação,
  arithmetic sampling e unranking são antecedentes conhecidos; novidade
  suficiente para publicação permanece não confirmada. Não tratar isto como
  superioridade sobre EPIC/ODD/sampling sem reposição, ganho de pass@1 ou
  demonstração neural iterativa de A26. O artigo inclui a extensão no apêndice,
  mantendo24 como protagonista confirmado de consulta.
- A27 investiga o custo de preparação do fechamento depois do primeiro
  overflow, usando resíduos ou potenciais em lugar de todas as alturas.
  Há quatro oráculos pequenos, uma formulação escrita e40 limites corretos
  no mesmo head público. Neste head a fronteira já é vazia para d>=1; todos
  os métodos certificam zero, sem ganho demonstrado. Não há novo sampler,
  timing competitivo ou forward independente. V2 completou1080/1080 registros
  nos18 estados anteriores:730 completos,320 massa rasa zero,30 recusas,
  1050 checks de massa arquivada. Resíduo16 empata as profundidades do handoff
  em18/18; potenciais empatam17/perdem1. Nenhum dos73 pares comuns tem limite
  mais apertado. Não promover a novidade; dimensão menor não é timing medido.
  Separabilidade one-counter2019
  já usa resíduos e Chernoff/OS* são antecedentes centrais. A hipótese deve
  ser descartada se não houver consequência própria relevante. A meta de
  novidade suficiente para publicação permanece aberta; não confundir a
  continuação da investigação com cumprimento dessa meta.
- A28 investiga estatísticas amostráveis na fronteira da cabeça neural/CFG,
  preservando IDs originais sem guardar pesos por token na referência de uso
  único. Há prova escrita de suficiência, custo em bits e três oráculos
  pequenos de lei conjunta/JSON independente. FlashSampling já fornece
  agrupamento e fusão; STATIC/GSP são antecedentes de projeção restrita.
  Não chamar esses princípios de novidade. V1:8/8 JSONs no mesmo head
  público e29488 checks exatos, sem forwards novos. V2 implementa redução
  inteira binary64 opt-in em GPU e controles NumPy/PyTorch vetorizados.
  Auditoria GPU52/52 passa, com39924 checks de blocos contra Fraction,
  incluindo subnormais/extremos e recusas. Não há timing, benefício sobre
  streaming competente ou prioridade publicável confirmada.
  Mantém head denso na GPU; não reivindicar economia de memória neural.
  Replay v2 dos mesmos pesos:24/24 JSONs e2328 checks de classe/massa;
  IDs pareados iguais em NumPy/Triton/PyTorch. Contagem de comunicação não
  substitui custo integral ou vitória sobre o controle GPU igualmente exato.
  V3 completo tem486 registros,351 completos135 recusas comuns0 erros,
  53 forwards novos (um warmup), todas as saídas medidas válidas. As três
  variantes0/18 gates primários;1024 tem13/18 ganhos de fronteira e4/18 de
  consulta preparada. Não há ganho20% integral contra todos os controles,
  trajetória iterativa ou confirmação independente. FactorDLM Proposição2
  já enuncia a lei de quociente; nova teoria/publicabilidade não confirmadas.

Use [TASKS.md](TASKS.md) para tarefas/evidências atuais e
[attempts/README.md](attempts/README.md) e `attempts/catalog.json` para versões
preservadas. O [caderno científico](docs/research/contribution-plan.md) registra
antecedentes, provas, objeções e decisões. Histórico não é instrução para
restaurar código retirado ou insistir em uma hipótese refutada.

- A29 preserva uma referência racional de reparo estacionário de colisões
  para leis P/Q distintas. Cinco oráculos passam; há prova escrita de
  não deterioração de pass@2/toda pontuação, via MH/Dirichlet clássicos.
  Correção posterior2026-10-11: a antiga comparação com ganho linear de um
  controle direto era INCORRETA. Fréchet limita TODO par de mesmas marginais
  a ganho epsilon² para um evento raro; A29 MH chega a1-epsilon do máximo
  binário. Errata separada em29/work/erratum-2026-10-11.md, sem sobrescrever
  a prova histórica. Não promover como protagonista, nem iniciar campanha
  só por vencer iid. Nenhum forward/timing ou prioridade confirmados.
- A30 investiga tabelas de K estratos por histórico, reveladas preguiçosamente,
  permitindo execuções seriais/assíncronas do MESMO decoder. Prova escrita usa
  Maclaurin e indução: marginais, pass@K para todo verificador e variância; são
  princípios clássicos, novidade suficiente ainda aberta. Cinco oráculos
  racionais passam;72 replays do EPIC pinado com logits FALSOS preservam
  trajetórias/rejeições/EOS/aliases CPU/CUDA. Nenhum forward neural novo ou
  ganho competitivo foi medido. Inputs do modelo sozinhos eram insuficientes:
  rejeições cumulativas influenciam max_resamples; o adaptador registra também
  snapshots de controle completos e não reúne histórias divergentes. A lei
  do uniforme CUDA tem arredondamento diferente da CPU e é preservada.
  Coordenação estratifica apenas UMA coordenada, não o tensor inteiro; há
  contraexemplo de paridade ao atalho. Custo/cache/latência e ganho semântico
  relevante ainda precisam de protocolo independente. Não declarar vitória
  sobre EPIC ou publicação a partir dos oráculos/replay de correção.

- A31 reúne históricos divergentes SOMENTE em estados realmente suficientes,
  incluindo ordinal de consulta por trajetória, fase, canvas, agenda, EOS e
  budget de rejeições. Há prova escrita de dominância sobre iid e identidade
  de variância contra o histórico A30; pass@2>=A30, não pass@K>=A30 geral.
  Quatro oráculos racionais e216 replays FAKE-head passam; nenhuma execução
  neural nova ou vitória prática. V2 ancora o primeiro visitante no ruído
  nativo observado, com posterior exato de estrato e dos aliases CUDA; três
  oráculos e216 preservações literais da primeira trajetória K=2 passam.
  São978 chamadas FALSAS, não evidência de ganho neural. V3 congelou inputs/
  protocolo4038857 e runner0a27a24 antes dos novos heads. O piloto de uma seed
  concluiu272 registros,528 trajetórias válidas e11.615 novos forwards LLaDA.
 192 primeiras trajetórias conferem integralmente;20 reencontros extras não
  melhoram cobertura: as quatro configurações empatam iid/root/history.
  Quatro seeds de desenvolvimento e confirmação independente NÃO executadas;
  não chamar o piloto de refutação completa ou conquista. Timings diagnósticos
  têm breve sobreposição de make check, sem confirmação de velocidade.
  Canvas sozinho tem contraexemplo de perda
  de cobertura. A diferença teórica específica, magnitude útil e suficiência
  para publicação permanecem abertas. Não alterar A30 retroativamente.

- A32 investiga reparo de colisão de CLASSES de ruídos/ordens nativas, não
  de palavras inteiras. Referência p-blind requer no máximo dois draws
  auxiliares do head congelado e esperado1-p(1-p)<=1; não novos forwards para
  coordenar. Há prova escrita de marginais e cobertura pass@2>=iid para todo
  verificador, incluindo trajetória adaptativa sob estado suficiente. O limite
  sharp por Bernstein vale SOMENTE sem acesso a p/densidade/side information:
  n<=3 draws não melhora a classe, n=4 é atingido pelo algoritmo. Não é lower
  bound de parsing/EPIC/forwards nem superioridade sobre CDF que conhece p.
  Quatro oráculos passam, incluindo729 kernels adaptativos;216 replays com
  heads FALSOS preservam primeira trajetória e RNG CPU/CUDA,978 calls falsas.
  O draft que falhou por índice CUDA implícito foi preservado. Sem novos heads
  neurais, vantagem prática ou novidade/publicabilidade confirmadas para32.
  Benchmark completo/controles fortes/protocolo independente ainda pendentes;
  estratificação/Barker/Bernstein/Dirichlet são antecedentes conhecidos.
  V2 generaliza o walk para orçamento n; seis novos oráculos e432 replays
  FALSOS passam, com controle pool compacto de mesma lei/memória. Mais energia
  local pode PIORAR cobertura final: contraexemplo preservado. Antecedente
  Nacu–Peres2005 Section6/Proposition24 foi encontrado DEPOIS: B_n=Q_n-p é
  redução exata, portanto walk/Bernstein não são invenção. Refinamento escrito
  v3 prova custo esperado minimax floor(n/2)+1 contra TODOS os factories
  p-blind adaptativos que atinjam B_n para todo p. Não abrange known-p/side
  information, nem prova prioridade ou velocidade do decoder. LP de54 árvores
  finitas tem36 certificados duais exatos/18 reconstruções inconclusivas, sem
  contraexemplo numérico; não prova otimalidade pontual geral. Nenhum head
  neural novo para32 até aqui. Novidade/benefício real continuam pendentes.
  V4 congela aplicação externa de JSON numérico:32 train/64 test do GSM8K
  pinado escolhidos somente por hash das perguntas, número irrestrito na
  gramática.16 métodos/configurações por temperatura incluem iid4, misto,
  raw tickets, pool compacto/vetorizado de MESMA lei e known-p aproximado
  (PL contínuo, não lei nativa finita exata).864 replays de heads FALSOS e
 32 checks do wrapper com68 respostas passam;135 testes68.297s. Protocolo
  antes de heads/gabaritos de avaliação; branch independente condicionada.
  Nenhum ganho real, prioridade ou publicabilidade A32 confirmado ainda.
  O piloto real está COMPLETO1056/1056 no produtor8fc0999/archiveabdf242:
  2208 JSONs válidos,32.716 forwards novos, nenhum erro/recusa/divergência
  da primeira trajetória. As8 candidatas empatam20/32 com iid2 e custam mais;
  controle misto21/32 é mais barato. Gate negativo predefinido encerra essa
  aplicação, sem outros seeds/labels independentes. Uma seed não é refutação
  estatística; todos os dados/custos I/O estão preservados. V5 é nota separada,
  sem atribuir o produtor posterior aos dados congelados de v4.
- A33, sem implementação ou novos forwards, reduz EXATAMENTE ao transformador
  de A29 com Barker e corrida clássica. Preservar a direção e não expandir
  como protagonista. R=1 truncado não é o MH implementado em29.
- A34 é uma candidata ESCRITA de fronteira de diversidade/custo para TODOS
  acopladores regulares sem p conhecido, com orçamento esperado total.
  Aritmética inteira reforça o score-bound; ruína clássica fornece attainment.
  O benefício normalizado é minimax sobre todo p, não apenas benchmark justo.
  Não prova latência total, prioridade ou utilidade neural. DeGroot ORIGINAL
  Sections1--8/formulas84/91 já foram lidos; score/variância são antecedentes.
  Wasan1964 ORIGINAL13 páginas foi lido: a expressão de mistura s_b já
  aparece em2.1, NÃO reivindicar sua invenção. Sharpness para outputs de
  par restrito é a diferença candidata. Wu/Wasan1991 e a revisão autoral
  Ghosh/Purkayastha2010 foram lidos; o original Ghosh1987 ainda falta.
  Aparente falha de estrita desigualdade em Wasan é auditoria separada,
  não conquista dLLM. Referência mínima com cap determinístico e certificado
  espectral passou4 oráculos independentes/139 testes no freezeV2, antes
  dos heads posteriores. Probabilidades conhecidas, mais saídas, custo completo
  e sinal da classe são objeções obrigatórias. Novidade/publicação abertas.
  V3 escreve custo completo e comparação com TODOS planos iid de contagem
  não adaptativa no mesmo orçamento esperado. Se cada draw já gera/verifica
  toda resposta, iid3 vence; retry sequencial com verificador disponível
  também pode vencer. A fronteira de transição barata e sinal semântico
  permanecem requisitos REAIS, não propriedades presumidas do modelo.
  V6 escreve lei/custo cap12 com341/1024 do ganho binário máximo, não qualidade.
  V7 preserva deadlock de cache normal-form no Rust externo; preparação dupla
  pela mesma API para TODOS caminhos evita-o, sem editar vendor.144/144 replays
  FAKE CPU/CUDA preservam primeira decisão/streams,132 batches reais do helper
  e198 forwards FALSOS. Screen oito inputs hash-ranked/32 prefixos nativos
  está congelado ANTES de heads, sem gabaritos; programa JSON aritmético
  recursivo, raiz mul/div versus add/sub/falha. A fronteira pode exigir vários
  forwards, todos custam. Só testa viabilidade de recursos, não vantagem ou
  novidade. Suíte142 PASS68.228s; não expor como ganho EPIC/publicação.
  O screen raiz está completo:8/8 casos,256 prefixos,1.845 forwards NOVOS,
 6/8 primeiras continuações executáveis,0/8 gates; sem gabaritos. Classe
  barata degenerada e classe variável tardia recusam esta aplicação, não
  o teorema. Nenhuma campanha de qualidade raiz deve ser iniciada.
  V8 testa o primeiro token numérico realmente novo/aceito (classe por
  paridade, sem sinal semântico presumido) nos MESMOS oito problemas:
 256 prefixos,2.330 forwards novos,5/8 primeiras caudas executáveis, zero
  erros do producer.1/8 screens, abaixo de2 exigidos; campanha de qualidade
  NÃO acionada. Fonte f7114ac, dados integrais preservados. Jafari Jozani/
  Perron2011 original Sections1--4 confirma que ranking barato/medição cara
  já é antecedente; seu pool4 e controles adaptativos competentes são
  obrigatórios. Fonte/evidência raiz anteriores ficam independentes emv9.
  V11 prova o score para outputs limitados e budget esperado localmente
  uniforme, sem cauda exponencial. Assim o bound cobre TODOS os factories
  p-blind com aquele budget, incluindo caudas lentas. Igualdade com primeiro
  bit retido e budget inteiro r>=3 força a parada de ruína, com suporte não
  limitado; cap finito não atinge exatamente a mesma fronteira. São provas
  ESCRITAS, não Lean/software/revisão humana. Regularidade pode já ser
  consequência conhecida; nenhuma prioridade ou aplicação prática nova.
  Os dois screens negativos e suas recusas de campanha continuam válidos.
  V12 dá uma prova escrita pontual por KL/Hellinger: basta E_p0N finita e
  output limitado para diferenciação EM p0, desde que termine em todos os
  parâmetros vizinhos. Lower bound A34 exige só budget no ponto justo, não
  uniforme. Não concluir C1 por finitude pontual. Leituras originais de
  Nacu--Peres/Holtz--Nazarov--Peres e tutorial autoral2022 estão registradas;
  contraste com uma questão antiga não confirma descoberta/priority hoje.
  Não houve código/head/timing novo; prioridade e uso continuam abertos.
  Addendum de curvatura V12 demonstra C^{1,1} sob budget uniforme, por
  bound das segundas derivadas das aproximações finitas. Não afirma C2,
  prioridade ou uso positivo novo; uma impossibilidade não cumpre a meta.
- A35 é uma ponte ESCRITA antes de código: lei de tag realmente aceita por
  greedy/MWPC pode contar #DNF, mesmo com sintaxe LL(1) e posterior produto
  polinomial de palavras com testemunho. Miklos4.2.2 já constrói união de
  termos em gramática regular; não reivindicar contagem/projeção como nova.
  Hazan/Jaakkola já distingue leis de argmax e Gibbs. A família é objeto de
  prova, não benchmark/modelo de regras Booleanas nem EPIC/CUDA exato.
  Não prova que todo acoplador precisa calcular p. Novidade própria e
  aplicação nativa útil continuam abertas; não ampliar este companion.
  V2 tem um oráculo independente pequeno: cinco gramáticas LL(1),528
  rankings,440 verificações de TODOS ótimos e cinco recomputações do núcleo.
  PASS0.086s; suíte inteira140 testes PASS70.001s. É correção da redução,
  não evidência de prioridade ou benefício neural.
- A36 preserva a ideia de cabeça esparsa pela viabilidade gramatical antes
  de implementar. GPIO-LLM fonte pinado2026-09-19 já projeta somente IDs
  admitidos; o mecanismo simples não é uma novidade central. Normalizadores
  cancelam na amostragem condicionada de slots fixos, mas são necessários
  para massa válida original/confidências nativas. Não omitir esses custos
  ou alegar preservar EPIC ao renormalizar sobre suporte diferente. Nenhum
  teste neural/timing/resultado próprio; a versão simples foi recusada.
- A37 investiga hash aleatório do resultado canônico de GERAÇÕES COMPLETAS,
  sem gabarito e sem presumir sinal de uma classe fixa. Prova escrita dá1/13
  do ganho máximo de pass@2 entre pares de mesmas marginais para qualquer
  resultado canônico correto único; cap12 dá1023/13312. Não é ótimo entre
  todos acopladores nem ganho de velocidade. iid3 SEMPRE vence sua cobertura
  com mesmo orçamento esperado de gerações; avaliar somente duas respostas
  exige consumidor real, não restrição para favorecer a proposta. Bound de
  avaliação imparcial exige v>5c em a=1/2 antes da coordenação; ratio não foi
  medido, e labels canônicos reutilizáveis devem ser cobrados corretamente.
  Antecedentes de antitéticos categóricos/difusão, RSS e PPI foram lidos.
  V1 congelou a teoria antes de código. V2 tem referência independente e
  quatro oráculos racionais passando;147 testes67.788s antes do último check
  de diversidade, depois quatro focados0.064s. Corolário escrito estende1/13
  à maior redução de colisões para TODA distribuição canônica. Controle por
  quantis conhecidos atinge o ótimo e continua explícito. Diversidade não é
  semântica nem latência. Novas leituras primárias estão registradas emv2;
  prioridade, aplicação útil e publicação abertas, sem novos forwards.

- A38 é um controle mais forte encontrado DEPOIS de37, em pasta independente.
  Antes de código, lei escrita do pool cap4 atinge os ótimos de TODOS eventos
  canônicos simultaneamente e covariância<=0 para qualquer score L2. A
  adaptação v2 escrita preserva essa lei com custo pontual mínimo4-2c+s3
  entre todos maximizadores universais p-blind cap4, com pelo menos três
  chaves PERMITIDAS. Não excluir controles binários quando o alfabeto é
  conhecido, nem métodos informados por logits. Mistura iid2 dá D_opt/8,
  contra1/13 de37, no mesmo teto de custo esperado3; não é dominância
  pontual de leis. Rank/pool exchangeability, clipping Bernstein e evitar
  auxiliares inúteis são antecedentes conhecidos. Neal/Andrieu/bootstrap/
  Casarin/STMC foram lidos nos trechos/hashes registrados. Prioridade,
  relevância prática e publicação ainda abertos; nenhum novo
  head/timing ou promoção. Auxiliares de um head congelado não exigem por
  si só novos forwards, mas todo parsing/rejeição/status continua custando.
  Não transformar isto em superioridade EPIC por contar somente draws.
  V2 tem referência29 linhas e cinco oráculos independentes0.056s, full152
  testes68.353s e make check PASS. O controle clássico de ranks confirma
  a MESMA lei, logo a construção básica é conhecida. Derangement uniforme
  informado vence em todos verificadores e sem auxiliares; é controle
  obrigatório quando suas hipóteses valem. Dice Enterprise já desenvolve
  factories categóricos e analisa custo/Peskun sob contratos próprios.
  Corolário de continuação adaptativa é ESCRITO, não adaptação EPIC medida.
  A candidata é o bound pontual sharp, com prioridade/efeito útil abertos.
  V3 escreve ANTES de nova implementação uma fronteira minimax mais forte:
  fração garantida ótima(b-2)/8 sob cap4 e orçamento médio uniforme b em[2,4],
  contra TODOS samplers desconhecendo P, inclusive clones do primeiro e
  paradas adaptativas. Chaves possíveis arbitrariamente numerosas; bound
  finito explícito, não minimax exato para vocabulário/comprimento fixo.
  Mistura meia-iid atinge1/8 no teto médio3. Prioridade, auditoria do novo
  lower bound e aplicação prática permanecem abertas. Não confundir este
  contrato de oracle com vitória sobre decoders que usam logits/tickets.
  V4 materializa só11 linhas adicionais (40 total); sete oráculos0.091s e
  suíte154 PASS69.932s, make check/Ruff PASS. Duas moedas independentes e
  coeficientes de cada multiset verificados. Análise de trabalho completo
  usa Wald PADRÃO e lei conjunta igual para cobrar continuação; economia
  versus pool full/early não é timing nem vitória sobre iid3. Novas leituras
  Huber/Dice têm hashes/escopos; sem novos forwards ou promoção do artigo.
  V5 limita o gap minimax finito por11/(8M) e congela pequeno piloto real:
  quatro perguntas input-only hash de TODO SVAMP pinado, duas seeds/sete
  métodos=56 registros. Golds só após captura, controles baratos mantidos.
  V6 prepara driver nativo completo/copias imutáveis, nove oráculos0.121s,
  suíte156 PASS68.012s e streams CPU/CUDA/Python/NumPy restaurados. Sem novo
  forward até esse preflight. Cobrar head/preparação/auxiliares/overhead;
  piloto não é confirmação estatística, novidade ou vitória geral EPIC.
  V7 preserva a captura posterior COMPLETA:56/56 registros,169 chamadas
  nativas reais,1885 novos forwards,134 COMPLETE/35 INCOMPLETE/0 ERROR,
  IDs originais do primeiro preservados. Adaptive usa28 chamadas contra
  pool32/early30 nos oito pares; iid2 é mais barato e todos esses têm
  pass2 observado2/8, seed_half3/8. Piloto pequeno NÃO confirma vantagem
  semântica/latência geral. Golds só após captura, fontes/dados auditáveis.
  Nova prova v7 de coarsening SEM implementação/timing: agrupar por um
  observável suficiente reduz chamadas completas em esperança e nunca
  piora pass2 de qualquer verificador desse observável ou o melhor score.
  Não vale monotonicidade da variância de TODO score real (contraexemplo).
  Deve haver fatoração exata, incluindo budgets de texto/AST/interpreter.
  Prioridade/aplicação competitiva/publicabilidade continuam abertas.
  V8 tem observadores21 linhas e três oráculos novos (15 partições e todos
  verificadores, budgets, aliases/falhas e contraexemplo).12 checks focados
  PASS0.279s;159 totais PASS68.211s, check/Ruff PASS. Slides Luo2025 lidos
  integralmente, mas NÃO o manuscrito2026: preservar essa distinção.
  Nenhum novo forward/timing, promoção ou novidade confirmada nesta versão.

## Atualização de trabalho em 2026-10-13 — A50

A49 V29 foi rebaixada a especialização após reconstruir a mesma cota com
Chan+Fu. V30 acrescenta apenas uma otimização clássica opt-in de range sums:
74.593 consultas exatas e300 casos/108 recusas passam; sem timing ou novidade.
A nova pasta independente50 investiga amostragem residual EXATA (P-Q)_+/TV
entre dois posteriores gramaticais congelados. Prova/critério antecedem código.
V1 mantém normalizadores originais; bug inicial de densidade de draft inválido
foi corrigido antes de oráculos. Falha de fixture fixa V2 foi preservada;
V3 passa482.657 checks de caudas/700 palavras/15 leis completas.
V4 tem51.340 intervalos de marginais originais e11 recusas reais de massa zero.
V5 escreve primeiro a preparação única por perfil superior e proveniência,
com singularidades exatas; referência175 linhas passa475.041 caudas/1.780
palavras/18 leis completas/6 leis singulares/432 samples e12 recusas.
A prova ESCRITA dá menos de duas tentativas condicionais esperadas sem1/TV,
mas cobra preparação e O(H*M^2) proveniência; não é deadline ou timing.
Dyer2003 e Gawrychowski/Markin/Weimann2018 já dão os princípios centrais;
prioridade/suficiência científica e benefício integral com dLLMs continuam
ABERTOS. Não inventar revisão humana/Lean ou vitória sobre EPIC. O artigo
mantido continua A24, sem transferir suas vitórias para A50. As menções
históricas a 'sem tentativa50' descrevem somente aquelas versões anteriores.

A50 V6 leu o original2019 completo na seção de amostragem; back-pointers e
preparação única são antecedentes. V7 delimita consumidor iterativo com
posições de commit escolhidas antes dos valores amostrados, não política
nativa EPIC. V8 implementa controle escalar mais forte; Feng/Guo/Jerrum/Wang
2023 Section3 já contém proposta/aceitação no caso produto. O simples ganho
contra rejeição1/TV não fecha a novidade. V9 escreve CDFs inteiras de precisão
controlada; V10 corrige contrato de canal comum com massa zero e preserva
falha V9. Os quatro oráculos completos passam90 leis de canais/18 residuais
cada: adaptativo432 saídas válidas; grids2/4/256 perdem o bound de custo em
seis fixtures, com292/237/185 FAILs no orçamento de uma tentativa. Nada disso
é timing, confirmação prática ou prioridade. A extensão recursiva e o custo
real do consumidor ainda precisam de avaliação contra controles competentes.

A50 V11 lê também Bhattacharyya et al. ICML2024 Section4 e provas completas:
proposta/aceitação e bound2n já explicam o princípio escalar. É especialização
compacta clássica; não promover sua exatidão como teorema próprio substancial.
O estimador produto aleatório linear de Anand/Benford/Guo2026 também foi lido,
sem confundir estimativa TV com amostra residual exata. V12 remove marginais
da precisão; oráculo completo passa30 queries de igualdade/range/90 leis de
canais/18 residuais/432 saídas, com131 passes de precisão cobrados. V13
congela screen de consumidor REAL com todos15 heads antigos, full/top16,
posições fixadas antes do sample, novos heads do canvas e quatro variantes.
É desenvolvimento funcional/de recursos, não confirmação de velocidade,
qualidade, originalidade ou publicação. Todas recusas permanecem no screen.

A50 V13 screen está COMPLETO:30 iniciais,15 full recusas de preprocessing,
nove top16 massa zero/seis admitidos. Sete forwards NOVOS (um warmup), seis
replays literais de softmax;24 correções,23 JSONs válidos/um timeout do perfil,
quatro estados retidos/dois ramos residuais. Packet opcional completo inclui
todos15 heads antigos/seis novos/logits/bytes, com hashes e quatro partes.
V14 audita que censura por tempo pode enviesar os sucessos: não apresentar
essas23 execuções como prova de distribuição P exata com recursos limitados.
Kernel ilimitado/FAIL e subprobabilidade são contratos diferentes. Não há
ganho competitivo, cobertura full-V, nova teoria ou publicação confirmados.

## Perguntas obrigatórias para cada ideia ou implementação

A39 começa em pasta independente, somente ESCRITA antes de protótipo/modelo:
fonte uniforme FINITA com índices conhecidos, labels do decoder opacos.
O bound robusto cap4 inclui escolhas adaptativas de índices/clones do primeiro;
cap3 não melhora atomicamente derangement de seeds em pior placement. Custo
sharp é minimax de placement por contagens, não pointwise de TODO mapa.
Covariância de scores completos tem correção WITHOUT replacement dentro das
classes; C4 não domina derangement para todos scores (contraexemplo mantido).
Corolário de primeiro yield nativo/head comum exige auditar zero forwards
auxiliares; igual esperança de forwards não é igualdade de wall/CPU/memória.
V2 tem kernel/source61 linhas e cinco oráculos exatos independentes:270
partições finitas, todos verificadores brutos e60 coarsenings, incluindo
contraexemplos a derangement/custo Wald/variância real.164 testes PASS70.995s,
check/Ruff PASS. Ren2019 Theorem1 e suplemento8.1 são antecedentes explícitos
de no-free-lunch finito; novidade query-cost e uso competitivo seguem abertos.
V3/v4 protocolo e producer foram congelados antes de modelos: v5 fecha72/72
registros originais,1595 forwards novos,117 completos35 incompletos selecionados,
0 erros. Cada prefixo usa zero forwards auxiliares; primeiros IDs completos e
reruns por seed coincidem.74 rewrites EOS-to-PAD após terminador vêm do upstream,
não de mudança do adapter: não alegar imutabilidade de TODO commit intermediário.
Adaptive25 queries contra32 full, mediana5.155s/3 acertos em8; iid2 tem16 queries,
5.041s/4 em8, menos memória. Piloto descritivo NÃO confirma benefício competitivo.
Primeira observação é frequentemente EOS ou concentrada; três keys globais não
provam classes informativas em cada input. Evidência e decisão39/work/*v5
preservadas; investigar o PRIMEIRO passo neural inteiro antes de outro forward
é nova fronteira/key a congelar, não relabelling da captura v4. Prioridade,
publicabilidade e utilidade ampla continuam abertas.
Primeiro passo v6/7 FAIL real no primeiro seed: observer leu j, mas upstream
o reassocia a batch-row0; um forward extra foi consumido e registrado.
V8 preserva erro/metadados/erratum. V9 proposto/corrigido conta yields de
fallback por seis sites AST pinados, sem escrever locals; toy CPU/CUDA com
j clobbered e batch parcial PASS. V10 fecha51/51 fontes antigas, zero forwards
auxiliares, oito regressões full-ID/status,88 forwards novos com heads iniciais.
Key constante em TODAS quatro entradas; auditoria funcional, informação útil
não confirmada. v7 FAIL e v9 corrigido permanecem separados. Não é gate
independente de benefício nem motivo para promover39 ao artigo.

A40 começa SOMENTE escrita antes de protótipo/outputs: âncora original
INDEPENDENTE é retida como terceira saída, heads exatos pagos/cacheCPU são
congelados antes de auxiliares. Corolário condicional dá pass3/best-score e
variância nunca piores que iid3, com igual ESPERANÇA de forwards ao mesmo
cache congelado. Cache dinâmico/3 seeds sem reposição são controles obrigatórios.
A39 lower bound sem labels grátis NÃO se aplica à informação da âncora.
Condicionamento/cache são conhecidos; novidade e benefício útil NÃO confirmados.
Classificador root/left-choice fixo, todos inputs/seeds antigos, auditoria
funcional/informacional apenas. V2 prototype CPU/CUDA PASS de IDs/status/RNG,
clones próprios e cache-miss recusado antes do forward. Captura32 requests/8
âncoras antigas tem16 regressões full-ID; primeiro helper repete a âncora,
NÃO é experimento da lei pass3. V3 fecha32/32,16 full-ID/status matches,
120 forwards novos; helpers zero. Excluindo replay da âncora, só uma de quatro
entradas tem key diversa; cacheCPU642--894MiB, prefixos0.103--3.128s. Nenhum
gate competitivo/semântico ou publicação; não chamar helper sem forward de
trabalho grátis. Novidade/benefício continuam abertos, sem artigo promovido.

A41 investiga OUTRA operação, escrita ANTES de implementar/modelos: estimar
ELBO/score de um JSON/DSL fixo ou gradientes com noising barato e duas avaliações
neurais. Matrix-covariance/Loewner/fixed-preconditioner e um passo quadrático
são corolários explícitos de39, não novas descobertas de álgebra linear.
MIRROR/P-POTS v2(2026-05-21) é antecedente DIRETO, já lido nas seções relevantes.
A garantia é versus iid2 da MESMA operação/fonte; dados repetidos NÃO dominam
duas amostras de dados independentes. Massas/inversos analíticos, mask/time
antithetics e importância são comparadores legítimos. Novidade, proxy CFG útil,
benefício completo e publicação NÃO confirmados. V2 tem referência própria,
três oráculos pequenos/67 partições de matriz, protocolo de apenas duas
avaliações caras e gradiente ReLU/softmax CPU/CUDA construído. O contraexemplo
MIRROR NÃO é benchmark favorável: registra controle analítico mais barato e
exato. Nenhum treino/head real novo. Ranked-set sampling já fornece a garantia
genérica com ranking imperfeito. V3 confirma equivalência da lei completa a
um design pivotal clássico. Novo modelo separa preparo bruto de consultas ao
classificador e admite saída não classificada: bound escrito4-4c2+2c3 é somente
para o design condicional FOUR-POOL declarado, não todo sampler ou mapas/massas
conhecidos. Seis oráculos próprios passam; Lean verifica a obstrução local
finita, não custo/probabilidade inteira ou software. Preservar comparador RSS
com boa ordem fixa, que pode vencer, e atalhos pivotal iguais. Prioridade,
significância e benefício neural real permanecem abertos.
V4 escreve a fronteira de átomos para qualquer orçamento SOURCE-cap e seu
incremento Catalan;5556 triplas passam. Oito oráculos próprios no total, sem
novos testes ativos/modelos. Pool8(1,1,3,3) tem covariance positiva para união
de classes: não transferir a garantia de todo score/gradiente para pools maiores.
LLaDA1.5/VRPO v2 já otimiza avaliação de ELBO; preservar seus controles e a
forma por contagem quando o denoiser for independente do tempo.
V5 congela uma sondagem de informação mínima: seis JSONs externos antigos,
32 corrupções para ajustar proxy e64 novas por documento;32 forwards de
preparação são cobrados. Conta-NELBO é conhecido, gradiente é somente BIAS
de saída full-V. Banco64 conhecido oferece massas/inversos gratuitos; seu
ganho de covariância não é vitória prática de oracle opaco. Nenhum novo
head/treinamento/resultado neural nesta versão prospectiva.
V6 substitui o mapa finito de seeds por tickets/unranking EXATOS para a lei
conhecida conta-NELBO, ANTES de qualquer head real. Aliases originais e custo
em bits são preservados; embedding não é novidade. Oráculos enumeram todos
os masks pequenos e casos limite64. Informação analítica de contagem/aliases
é permitida aos controles; bound opaco não limita todos os algoritmos de masks.
V7 completa TODOS os seis documentos,576 forwards reais de MDLM;32 ajuste+64
corrupções novas iid por documento. Não houve atualização. Dados integrais,
Gram do bias full-V e auditoria pivotal independente estão preservados.
RSS clássico PODE reter o primeiro score pago, com pilot barato e mais UM
forward: alegar descarte obrigatório enfraqueceria o adversário. Nos bancos
conhecidos RSS vence C4 no score em6/6; CV do mesmo proxy vence5/perde1.
Bias C4 reduz só2,00--4,33% versus iid2, com32 forwards de preparo cobrados.
Torch4 threads não limita BLAS NumPy; custos integrais registrados. Não é
gate populacional, treino, ganho EPIC ou confirmação de publicação. Não ampliar
a campanha neural desta aplicação sem nova diferença/justificativa concreta.

Antes de propor, implementar ou ampliar uma solução, responda às perguntas
abaixo no README da tentativa. Reavalie as respostas a cada versão. Uma
correção pode referenciar respostas existentes e explicar o que muda ou
permanece válido; não pode ignorar esses critérios.

1. **Qual uso real será melhorado?** Identifique a operação, quem a usaria,
   entradas disponíveis e saídas consumidas por software. Explique a ligação
   com uma dLLM e uma GLC. Produzir JSON válido, isoladamente, já é possível;
   explicite o que este trabalho acrescenta.
2. **A contribuição é relevante ou pequena demais?** Qual é a diferença
   precisa para o antecedente mais próximo? A solução é uma aplicação direta
   de algo conhecido, um ajuste trivial ou um avanço com consequência útil?
   Explique por que o resultado sustenta um TCC e uma proposta de artigo.
   Incrementos são aceitáveis; quantidade de código, esforço gasto e uso de
   Lean não medem novidade. Não prometer aceitação acadêmica.
3. **Por que alguém a escolheria?** Declare uma vantagem verificável em
   velocidade, custo, memória, resultado, capacidade ou garantia relevante.
   Nomeie um comparador competente que resolva a mesma operação, com informações
   e restrições equivalentes. Quantifique a vantagem e suas condições. Não é
   necessário vencer sempre, mas a condição favorável precisa ter utilidade.
4. **A vantagem pode ser provada sem executar código?** Priorize um resultado
   matemático: definições, algoritmo, hipóteses, teorema, prova e análise de
   custo independentes da implementação. Provar correção de um método conhecido
   não basta para demonstrar avanço; localize também o benefício comparativo.
   Inclua um corolário que conecte a vantagem à aplicação proposta.
5. **Se depender de experimentos, qual hipótese será testada honestamente?**
   Essa alternativa é autorizada, mas tem prioridade menor que uma contribuição
   matemática adequada. Declare previamente métricas, casos, comparadores,
   orçamento e critérios de sucesso/falha. Use evidência independente e
   relevante; não crie ou selecione benchmarks para fabricar uma vitória.
6. **O ganho sobrevive ao custo completo e ao uso com dLLMs?** Contabilize
   preparação, normalização, tokenização, forward do modelo, consultas,
   atualizações, saída, memória e aritmética em bits. Distinga primeira saída,
   lote e consultas repetidas. Separe exatidão de um passo de garantias para
   a trajetória inteira, e validade sintática de acerto semântico.
7. **Qual objeção pode derrubar a proposta?** Procure reduções a técnicas
   conhecidas, contraexemplos, um comparador melhor e condições nas quais a
   vantagem desaparece. Explique quando a solução não seria escolhida. Se uma
   codificação clássica compacta obtém o mesmo benefício, reconheça isso.
8. **O que ainda falta para um artigo defensável?** Identifique a afirmação
   própria, antecedentes conferidos, prova/validação, aplicação e limites.
   Separe conjectura, prova escrita, resultado mecanizado, teste de correção
   e medição. Revisão humana e publicação nunca podem ser inventadas.

As respostas são critérios de decisão, não um formulário para justificar toda
ideia. Antes de uma implementação extensa, estabeleça a diferença científica
e um argumento plausível para a vantagem. Use protótipos mínimos para encontrar
contraexemplos quando necessário; um protótipo que funciona não resolve a
questão de novidade ou utilidade.

Se a direção não atender aos critérios, diga isso claramente, preserve-a e
investigue outra. O usuário autoriza mudar o recorte ou começar outro TCC;
não force utilidade no tema atual por causa do trabalho acumulado. Proponha e
fundamente a alternativa antes de desenvolver outra implementação grande.
Resultados negativos devem permanecer acessíveis, mas não são o produto final
pretendido. Se uma direção atender aos critérios, consolide-a; não reinicie a
busca ou expanda funcionalidades sem uma razão concreta.

## Motivação Jev e direção dJev

A consulta às fontes oficiais em 2026-10-08 confirma que Jev recebe estado e
perguntas tipadas e retorna decisões/probabilidades em paralelo, abrindo mão
da geração livre de strings. A API oferece tipos como Choice, Score e Noul.
As alegações de velocidade são resultados reportados pelo fornecedor, não
medições deste TCC. Fontes: [apresentação oficial](https://typesafe.ai/blog/introducing-system-one-models-and-jev)
e [referência da API](https://api.typesafe.ai/redoc).

Use Jev como motivação para decisões estruturadas consumidas por software.
**dJev é uma direção de pesquisa**, não o nome de um modelo já implementado:
usar dLLMs para gerar estruturas/textos sob GLCs com uma melhoria útil sobre
uma solução competente já existente. Só combinar uma dLLM com um validador
JSON ou reproduzir uma interface de decisões tipadas não constitui o avanço.

Escolha uma aplicação concreta: por exemplo, preenchimento de configurações,
chamadas estruturadas ou regras JSON recursivas com dependências entre campos.
Mostre por que a operação se beneficia do resultado e admite várias respostas
válidas. Não presuma que Jev resolve geração textual recursiva geral ou que o
projeto o supera. Para comparar desempenho, alinhe tarefa, qualidade, estrutura,
probabilidades exigidas e custos; não compare um serviço com uma única etapa
de parsing. Não deduza acerto semântico ou calibração apenas de type safety.

## Fluxo de trabalho e preservação

- Antes de alterar código, leia este arquivo, o marco atual e suas dependências
  em `TASKS.md`, e os fontes/provas/evidências pertinentes. Declare a operação
  e o contrato que a alteração deve preservar.
- Cada nova direção começa em `attempts/<id>/`, com README, as respostas
  obrigatórias e um protótipo isolado em `work/`. Cada refinamento conserva
  as versões anteriores. Não dependa de código mutável de outra tentativa.
- Congele código, provas, configuração e evidências com commits completos e
  hashes. `scripts/archive_attempts.py` inclui o `work/` da tentativa e recusa
  sobrescrever versões. Modelos/caches ficam fora dos snapshots. Os testes
  históricos dentro dos ZIPs são dados arquivados, não testes ativos restaurados.
- Preserve os arquivos científicos congelados nos inventários existentes,
  incluindo `formal/MWPC.lean`. Novas evidências/provas ficam em arquivos novos;
  correções não devem sobrescrever resultados históricos.
- Preserve o núcleo e baselines mantidos enquanto investiga alternativas.
  Promova código experimental quando a contribuição/contrato estiverem claros
  e a implementação tiver validação apropriada. Evite refatorações amplas,
  infraestrutura desnecessária e otimização anterior à correção.
- Execute trabalho concreto em grupos coerentes. Atualize `TASKS.md` com
  comandos, resultados e caminhos. Não declare conclusão quando apenas criou
  tarefas. Não marque conjecturas, revisão ausente ou medições pendentes como
  concluídas; registre o impedimento e o menor próximo passo útil.
- A ausência de comentários do orientador não impede continuar a investigação
  autorizada. Ela não autoriza alegar revisão independente. Não contate pessoas
  nem submeta trabalhos externamente sem instrução explícita.
- Commit e push normal para o upstream configurado são obrigatórios antes de
  reportar conclusão. Confirme sincronização e informe falhas. Não mude de
  branch, reescreva histórico ou force-push sem pedido explícito.

## Contratos dos componentes mantidos

Não imponha o objetivo de MWPC a métodos que calculam um posterior ou executam
outra operação. Defina o contrato próprio de cada proposta e preserve os
contratos existentes ao reutilizar seus componentes.

### MWPC e certificados de commitment

1. Para propostas `(position, token_id, weight)` com pesos não negativos,
   maximize a soma dos pesos casados por uma conclusão gramaticalmente válida
   no suporte finito atual. A garantia é por passo, não da trajetória futura.
2. Suporte podado/top-K é `exact_on_support`, nunca exatidão no vocabulário
   inteiro. Todo resultado deve identificar o suporte.
3. `OPTIMAL`, `INFEASIBLE_ON_SUPPORT`, `TIMEOUT`, `UNSUPPORTED` e `ERROR` são
   distintos. Timeout não prova inviabilidade.
4. `OPTIMAL` exige caminho e tokens reconstruíveis, IDs das propostas
   selecionadas e objetivo recomputável independentemente.
5. O conjunto selecionado contém todas as propostas de peso positivo casadas
   pelo testemunho, preservando IDs e multiplicidades de propostas duplicadas
   quando aplicável.
6. Preserve posições fixadas e consuma exatamente os slots permitidos pela
   política EOS/PAD. Lacunas abstratas `Sigma*` não são certificados finitos.
7. Poda que possa remover um ótimo invalida `OPTIMAL`; poda segura exige prova,
   documentação e teste independente.
8. Fallback de progresso não vira proposta casada retroativamente. Rejeite
   pesos negativos, NaN e infinito. Produção usa float/f64 conforme a API;
   prefira pesos inteiros nos oráculos do objetivo.
9. Desempate estável pode ser determinístico. Somente o objetivo primário é
   garantia matemática, salvo objetivo lexicográfico implementado e validado.

### Posterior gramatical e pesquisa semântica

- A distribuição condicionada é a predição produto congelada de um passo
  sobre tokens originais. Preserve aliases, bytes, posições fixadas e slots.
  Conte eventos de tokens, sem multiplicidade artificial de derivações.
- O posterior CFG atual admite gramáticas LL(1) verificadas e EOS ausente.
  Não amplie essas hipóteses no artigo sem implementar/provar a ampliação.
- Massa e amostragem exatas usam aritmética racional/inteira. Distinga massa
  válida zero, ausência de soluções estruturais, suporte omitido e recusa
  por recursos. Não renormalize uma cauda descartada silenciosamente.
- Reutilização de plano/núcleo admite os pesos, contrações de suporte e novos
  commitments compatíveis previstos na API. Expansão de suporte, liberação de
  posições fixadas ou mudanças de gramática/tokenizer/EOS exigem nova preparação.
- Um núcleo semântico deve certificar implicações sobre todo o suporte
  estrutural original com pesos auxiliares positivos; zero probabilidade do
  modelo não justifica descartar um requisito para consultas futuras.
- A referência semântica atual trata campos Booleanos e seus operadores
  admitidos, com limites de trabalho/perfis. Não cobre JsonLogic geral ou
  correção em exemplos não declarados. Recusa de recursos permanece inconclusiva.
- O limite de rejeições do fluxo adaptativo pressupõe pesos/requisitos fixos
  e recursos suficientes. Não transforme-o em garantia de velocidade geral,
  inferência da dLLM inteira ou benefício exclusivo sobre todo solver.

## Arquitetura, código e dependências

- `src/mwpc_exact/reference/`: referência Python legível, sem dependências de
  modelo, caches globais ou estado mutável oculto. Referência e solver Rust
  permanecem independentes para que comparações sejam informativas.
- `crates/mwpc_parser/`: parsing e reconstrução Rust; `crates/mwpc_parser_py/`:
  bindings finos. Valide grafos, use IDs estáveis para backpointers e retorne
  erros/status explícitos para entradas controladas pelo usuário; não use panic.
  Produções permanecem neutras, salvo extensão ponderada explicitamente definida.
- A conversão tensor/CPU e o código específico de modelo ficam na integração,
  não nos solvers genéricos. Use tipos públicos explícitos e resultados com
  status/escopo/certificado identificáveis.
- Preserve `LICENSE`, `THIRD_PARTY_LICENSES.md`, o EPIC pinado em `UPSTREAM.md`
  e seu manifesto. Não altere o snapshot externo para favorecer a comparação.
- Python segue versões declaradas, com 3.11 como base de reprodução. Adicione
  dependências apenas quando necessárias, com pins/locks e justificativa.
- Não versione pesos, caches, dados privados, credenciais, grandes traces novos
  ou caminhos absolutos específicos da máquina. Novas execuções de modelos são
  opt-in; testes automáticos devem funcionar offline.

## Provas, testes, experimentos e conclusão

Prefira demonstrar a contribuição matematicamente sem depender de benchmarks.
Uma prova precisa de hipóteses e custo completo, inclusive custo em bits; não
prova prioridade na literatura ou velocidade física em qualquer hardware.
Lean verifica os enunciados/specs mecanizados: não o Python/Rust inteiro, o
tokenizer, o modelo ou toda a lei escrita de amostragem. Declare essa fronteira.

A suíte histórica foi retirada por pedido do usuário. A suíte atual em
`tests/` contém oráculos independentes focados no posterior, nas extensões
semânticas e na referência PL da tentativa 17. Preserve-a; não restaure a antiga
indiscriminadamente. Crie novos
testes apenas necessários, pequenos e capazes de encontrar erros reais.
Enumeração e famílias construídas são verificações de correção ou objetos de
prova, não observações de modelo nem superioridade prática demonstrada.

Quando houver experimentos, congele o protocolo antes de medir, separe
desenvolvimento de avaliação independente e publique todos os resultados,
incluindo perdas, massa zero, recusas, timeouts e tentativas interrompidas.
Não selecione apenas saídas favoráveis nem altere o adversário para piorá-lo.
Use os mesmos logits/canvas quando comparar operações de seleção equivalentes;
controles próprios não são execuções nativas de EPIC, CARS ou FactorDLM.
Registre commit, configuração, seed, revisões de modelo/tokenizer, hash de
gramática, política/escopo do suporte, hardware/software e contagens de status.
Separe timings, sincronize CUDA e exclua carregamento único apenas quando isso
estiver declarado. Gere tabelas/figuras dos dados; não edite números à mão.

Os comandos disponíveis têm alcances diferentes; rode os pertinentes à mudança:

```bash
make check                 # upstream, lint, tipos e integridade das tentativas
make attempts-check        # preservação dos snapshots; não correção científica
make test                  # suíte independente focada atual
make build-rust            # formatação/build/clippy dos componentes Rust
make check-formal LAKE="$HOME/.elan/bin/lake"  # provas selecionadas
make article-results-check # arquivos e derivados; não toda recomputação do solver
make paper                 # artigo principal
make research-note         # nota da pesquisa semântica
```

CI deve executar testes, build, provas e verificações de artefatos; CI verde
não estabelece novidade ou utilidade. Não escreva resultados no artigo sem
comando, configuração, dados e código produtor registrados. Declare quais
inputs são reproduzíveis offline e quais traces completos permanecem locais.

A conclusão científica deve explicar **o que melhorou, para quem, contra qual
alternativa, sob quais hipóteses e por que importa**. Se isso ainda não estiver
sustentado, diga exatamente o que falta e continue o trabalho autorizado que
possa resolver a lacuna. Não chame organização, compilação ou um exemplo que
funcionou de cumprimento dos requisitos científicos do usuário.

A42 separa a lei empírica rejective/max-entropy conhecida da conjectura de
covariância global após pool uniforme.16824 casos numéricos M<=20/até5 classes
não têm obstrução, mas NÃO são prova, sampler exato ou uso neural. V1 e
explorações preservadas. A garantia condicional não elimina a flutuação da
média do pool. Nenhuma campanha neural é justificada; custos de calibração
irracional continuam pendentes. Não confundir com prioridade/publicação.
A42 v2 tem prova escrita de segurança CONDICIONAL para todos os tamanhos
pares de pool conhecido, via operadores estáveis clássicos.38 enumerações
independentes e2213 checks finitos passam; pesos inteiros não exigem raízes
irracionais. Não transferir o lema ao pool sorteado: esse passo segue aberto.
Contagem/orçamento em bits, uso, novidade/publicação ainda não confirmados.
A42 v4 fecha a segurança de covariância INCONDICIONAL somente para pool6,
com prova analítica e fronteira explicitamente assistida por computador:
104 menores polinomiais/38 famílias infinitas e289 certificados racionais,
com cobertura de14.723 partições pequenas e verificador separado. Não é
formalização Lean integral, teorema para todo orçamento, ganho neural ou
novidade/publicação confirmados. As15 matchings eliminam calibração irracional
nessa versão; custos de fonte, classificação e proxy continuam cobrados.
Prioridade frente a pivotal/rejective/RSS e utilidade CFG seguem abertas;
preservar as perdas de41 e não iniciar grande campanha apenas pela prova.
A42 v5 compara40 partições exatas com pivotal clássico: mesma fronteira de
átomos, uma diferença de lei em pool6. Nos TODOS seis bancos antigos, pivotal6
é quase igual e vence5/6 gradientes do bias; RSS vence todos os scores. Não
usar esses dados como ganho populacional/treino, nem promover esse proxy.
Nenhum novo forward. Prioridade e uso CFG específico permanecem abertos.
A42 v6 usa seis propostas originais IID COM reposição, preservando estados
repetidos e aliases. A prova escrita puramente analítica fecha a segurança
incondicional para toda massa de classes, sem certificados finitos. Dois
checks simbólicos e8.256 tapes racionais passam. A fronteira balanceada de
pior direção é ótima no contrato de coupling independente do score e fonte
IID opaca universal; pivotal6 a compartilha. Não aplicá-la a métodos com
massas/inversas gratuitos, CV ou políticas adaptadas a cada score. Os controles
fortes negativos de v5 continuam válidos; nenhuma novidade/publicação,
superioridade neural/EPIC ou utilidade CFG de custo completo foi confirmada.
A42 v7/v8 preservam duas refutações EXATAS: blend1/L não domina C4, e
ótimo por classe individual não garante pass@2 de uma união de classes.
O reparo local H6 tem ganho pequeno e isso não justifica promoção. V9 tem
37.200 checks numéricos sem obstrução no intervalo necessário0/4/45, mas a
suficiência continua conjectural; há redução algébrica escrita, não prova.
Nenhum novo forward ou campanha neural. Não apagar/refavorecer esses casos.

A42 v10 muda a construção: refino de C4 por capacidades diagonais e
Laplaciano não negativo. Prova escrita pura cobre dominação de covariância
de C4 para todoB>=4 e monotonicidade emB, com limite balanceado ótimo entre
couplings de duas saídas.145 leis de pools,1053 tapes racionais, cinco leis
do sampler e28 somas balanceadas passam. L declarado fixo é obrigatório.
Dirichlet/U-statistics e monotonicidade RSS são antecedentes, não novidade.
O limite ideal de quatro classes melhora C4 só7/39 na variância ENTRE classes;
não é gate20% integral, vitória contra pivotal/RSS/CV, modelo treinado ou
vantagem EPIC. Prioridade e uso CFG/dLLM de custo completo continuam abertos.

A42 v11 auditou o EPIC NATIVO sem alterar seu gerador:32 fontes/8 continuações
em todos quatro inputs públicos antigos,343 forwards novos LLaDA/NF4. Todos
os32 primeiros yields têm raiz pendente; obter o operador exige7--12 forwards
adicionais.6/8 continuações são JSONs executáveis, duas incompletas preservadas.
Preparação de oito fontes versus duas continuações custa2,73--3,84 vezes em
wall e2,87--3,84 emCPU nesse diagnóstico serial; não é benchmark competitivo,
pool vivo, medição semântica ou avaliação independente. A proposta de fonte
barata pela raiz falha; não cancelar work/model forwards e chamá-los de grátis.
Provas6/10 permanecem, mas uso/publicação continuam abertos. Não ampliar esse
proxy por mais casos favoráveis; próxima aplicação deve ter fontes baratas.

A43 inicialmente investigou paradas adaptativas IID de fontes originais:
primeira/última fonte de uma excursão com duas classes, duas avaliações caras.
Prova escrita preserva P e toda covariância vetorial, dá E[N]=M para TODO p
e fronteira sharp de repetição/custo em p=1/2 por KL do experimento parado.
423 leis racionais,3952 tapes e15 momentos balanceados PASS, producer6dcd88e.
Ruin/factories/inequações sequenciais são clássicos; prioridade/uso/publicação
continuam abertos. Teto finito v2 retém a última fonte subsequente da MESMA
classe:1.540 leis racionais e10.220 tapes passam sob producer d0b6936.
Não confundir teto de draws com fallback iid arbitrário, latência garantida,
nova geração EPIC ou treinamento. Nenhum novo forward.
A auditoria interna V4 encontrou a mesma lei completa e uma fronteira MAIS
forte já preservadas na A34. A43 está encerrada como candidata de novidade;
seus oráculos são revalidação, não avanço. Consultar as provas existentes
antes de apresentar uma formulação novamente; o erro de duplicação está
registrado em43/work/internal-reduction-v4.md.

A44 investiga uma lei empírica de três classes com orçamento finito arbitrário.
Há prova escrita analítica de segurança vetorial incondicional via concavidade
da raiz do déficit binomial, fronteira de átomos e minimax balanceado no
contrato de fontes opacas. Producer090c357 passa12.844 leis racionais, oito
famílias de produtos originais,360 árvores RNG e14 identidades polinomiais.
Transporte empírico, RSS, Bernstein e Fréchet são antecedentes. O contraexemplo
não uniforme contra C4 foi preservado; não existe dominação geral de C4/RSS/CV.
Nas V1/V2 não houve forwards ou treinamento; ganho neural e prioridade/
publicação não foram confirmados. A associação a alvos JSON/GLC é candidata, não
prova de que o benefício prático depende de GLCs. Auditoria primária e custo
completo devem anteceder implementação neural extensa.
A44 V3 agora tem192 novos forwards/backwards de TODOS169.627.218 parâmetros,
nos seis documentos públicos antigos, zero updates. Oráculos/derivada do bias
passam; a tela prospectiva falha0/6 mesmo com sobrecusto zero contra RSS
contínuo e CV-oráculo. A aplicação deste classificador está encerrada, não
acionar treino/heldout/timings. As provas3classes/RSS balanceado permanecem,
mas não há uso neural competitivo ou novidade/publicação confirmados.


A45's6.230-case random-label-order tower screen found no finite obstruction;
unconditional arbitrary-class safety remains a CONJECTURE. Its B6 law is the
lambda2 member of A42's OPEN family, not the proved minimum matching. ALL rows
are retained; A44's failed full-gradient classifier is not reopened. No neural
execution. A46 closes generic reciprocal-ambiguity correction and weighted
FPRAS lifting after primary2001/2015/2024/SODA2026 readings. A47 closes generic
exact-interval forest sampling/logarithmic refinement as novelty after original
Duchon2011 and Brassard/Devroye/Gravel2019 readings; complete arbitrary-logit
bit costs are still unwritten. No numerical solver was implemented. A48 closes
generic grammar versus wide-factor claims: CFD UAI2004 already covers context-
specific parsing, and constant gated alternatives require a conditioning
control. These are audits, not new publication/EPIC wins. The goal stays OPEN.

A49 investiga certificados racionais de TV entre DOIS posteriores do mesmo
suporte/GLC, não aceleração do decoder EPIC. Fu2609.24235 já dá o princípio
geral de composição de zonótopos; não reivindicar isso. V1 passa3.100 casos/
57.769 consultas exatas e V2 passa75 casos de IDs originais. V3 usa geometria
clássica de projeção e endpoints inteiros para escrever uma melhoria do bound
de núcleo: O(sqrt(d/epsilon)) contra O((d/epsilon)^2) no Lemma3.5 de Fu
para dimensão2, com custo completo em bits na floresta ADMITIDA. Não é lower
bound do algoritmo concorrente, invenção de aproximação convexa ou prova do
normalizador Python. Producer2e3b4a7 passa2.480 casos/40.035 consultas e os75
casos originais sob AMBOS núcleos (150 checks). Especificidade/prioridade do
resultado de TV, aplicação real e suficiência para publicação permanecem
abertas; não converter oráculos de correção em vitória de desempenho.

A49 V8 acrescenta consultas geométricas exatas logarítmicas, provadas ANTES
do código: limite produto O(nq sqrt(n/epsilon) log(qn/epsilon+2)), núcleo
floresta O(H(d/epsilon) log(d/epsilon+2)), com custo inteiro em bits completo.
Melhora os UPPER BOUNDS determinísticos publicados inspecionados, não é
lower bound contra todas implementações. Geometria/projeção são clássicas;
Fu já remove a dependência numérica de TV. Oráculos:1.860 casos/30.846 queries,
117.376 projeções por scan racional independente,75 florestas originais.
A admissão LL(1) polinomial é um algoritmo matemático escrito; exige trimming
e não verifica o normalizador mantido. A auditoria pública V9 encerra6/6 casos
predefinidos, todos50.258 IDs: FP16 tem bound4,095e-5 contra Hellinger2,784e-3.
Isto é um uso real de PRECISÃO DE CERTIFICADO para tabelas de probabilidades;
os controles são mais baratos. Não houve modelo quantizado, nova captura,
vitória neural/EPIC ou benchmark independente. Ambas falhas de setup e o
V6 lento interrompido1/6 estão preservados. A redução ICML2024 inteira§4
foi lida e admite um controle gramatical competente; possibilidade genérica
de aproximar TV não é descoberta. V10 passa1.167 casos do algoritmo produto
direto e tem rascunho matemático separado de sete páginas, com tabelas geradas.
Antecedentes e distinção quantitativa estão em primary-comparison-v10.md;
prioridade exaustiva/revisão humana/aceitação permanecem não confirmadas.
Consolidar esta diferença antes de nova implementação ampla; não reiniciar
decoders negativos ou prometer certeza absoluta de publicação.

A49 V11 conserva todos snapshots e o PDF V10. O atalho exato m<=k é rotina,
com prova antes de código: custo de compressão O(m log(m+2)), garantia igual.
Todos1.860 casos/30.741 queries/117.376 projeções e75 florestas passam,
assim como1.167 produtos e389 casos epsilon2^-1024, exatos. Três regressões
independentes pequenas entram no CI; suíte completa passa167 testes em70,530s.
Matoušek1996/Reis-Rothvoss2026 reforçam que geometria/bit computability
são antecedentes. A distinção é o bound quantitativo de TV, não nova geometria.

A49 V12 reforça o controle angular clássico, iguala budgets e conserva18
resultados, inclusive seis recusas por materialização. Essas recusas não
recebem crédito. V13 faz streaming de produtos no controle, sem esse teto:
ALL18/18 concluem, com custos completos wall/CPU, sem novas capturas. São
medições de desenvolvimento no MESMO pacote, não confirmação independente.
V14 prova separação de armazenamento de núcleos numa família positiva;
TV escalar de uma posição continua melhor por soma exata O(M)/memória O(1).
Não converter a separação de representação em lower bound de toda inferência
ou em velocidade geral. Novidade específica/suficiência editorial permanecem
sob auditoria; não fingir revisão humana ou garantia de aceitação.

A49 V15 dá ao controle angular auto-certificação exata em todas direções e
passthrough estrutural comum:18/18 concluem; o controle vence AMBAS candidatas
no core BF16/0.5. Preservar a perda. V16 falha no primeiro oráculo por presumir
IDs topológicos; V17 corrige somente o helper novo, passa75 oráculos e18/18
casos. V18 fortalece a precisão relativa de ambas direções chi-square:75
oráculos/18 casos passam. O melhor bound barato FP16 é0,0007602748 contra
endpoint0,0000409460 emepsilon0,1 (cerca18,57x, não67,98x contra esses novos
controles). Não houve forward novo, corpus independente, modelo quantizado,
gate de latência geral ou vitória EPIC. V10/PDF e todos erros/custos ficam
preservados; próximo rascunho deve incorporar estes controles mais fortes.

A49 V19 falha no primeiro oráculo não vazio por inverter a comparação do
menor ângulo; fonte/erro foram preservados. V20 passa1.860 geometrias/33.747
queries,117.376 projeções exaustivas,1.860 imagens,1.167 produtos/389 extremos
e75 florestas. V21 conclui TODOS24 casos funcionais com os controles mais
fortes; mantém perdas FP32 da versão ordenada e vitória angular BF16/0,5.
V22 conserva um NOVO rascunho matemático separado de dez páginas, com bound
produto O(nq sqrt(n/epsilon) log(q+2)) e tabela integral gerada. O corolário
de orçamento da trajetória é acoplamento clássico escrito, não decoder
iterativo implementado/medido. Quatro regressões focadas cobrem ambos núcleos
e o erro realV19. Geometria, parsing, acoplamento e computabilidade em bits
são antecedentes; a diferença candidata é quantitativa. Não declarar
prioridade absoluta, revisão humana, aceitação ou superioridade EPIC.
Na fonte2f406e3 a suíte mantida passa168 testes em70,403s; check de upstream,
lint/tipos/formatação e preservação também passa. Isto não prova novidade.

A49 V24 acrescenta um controle clássico mais forte por acoplamento dos samplers
na floresta, com limites dyadicos certificados em suporte total e comum. Passa
105 oráculos originais e TODOS24 casos públicos, sem erros/recusas/forwards.
O ganho FP16 antigo18,57x cai para1,05476x; o controle FP32 é mais preciso que
o upper da candidata. Preservar essa perda: V22/PDF é rascunho histórico com
seus comparadores declarados, não vitória contra V24. A teoria quantitativa
não foi refutada, mas a aplicação precisa de evidência melhor. V25 conserva
todos casos/tolerâncias/budgets e o mesmo critério2x, incorporando AMBOS
acoplamentos ANTES de novas observações. TODOS15 heads dos cinco documentos
pinados foram capturados (mais UM warmup); replay confirma softmax completo
bit-exato e bytes originais. Quatro documentos são não vistos pela pesquisa
TV deA49, não porA24 ou pelo treinamento. Auditoria360 está completa:256
certificados e104 recusas, nenhum registro ausente. O gate independente2x
falha em TODOS36 pares primários; não reduzir o limiar ou contar1,9885x como
sucesso. A análise adicional de precisão ideal também tem zero ganhos robustos.
Os75 oráculos dessa análise passam; isto é correção, não vantagem prática.
Todos45 pares e360 registros ficam em49/work/evidence/external-v25;
recusas compartilhadas não recebem crédito. Fontee6cef06 passa169 testes em
71,697s. Arrays novos completos ficam locais; hashes não são reprodução
offline integral. Novidade/suficiência editorial/ganho independente continuam
abertos; não inferir vitória EPIC ou da geração inteira.

A49 V26 passa300 oráculos antes de completarALL360 registros de replay:
256 certificados104 recusas, nenhum ausente/forward novo. Um de45 pares de
DESENVOLVIMENTO excede2x (2,02282896x), inclusive precisão ideal do controle;
não é confirmação independente, gate de latência ou vitória EPIC. V25 continua
FAILED0/36. Os controles inferiores clássicosV27 passam105 oráculos de tokens
originais (33 massas zero indefinidas), sem aplicação medida. Provas escritas
fecham custos de scaling/grid/saída, Markov com denominador GLOBAL por camada,
chart CNF d<=3B-2 e fonte LL(1) d<=2(h+1)(2B-1) sem pressupor normalizador CNF
verificado. A família matemática positiva de JSON separa TODOS os upper baratos
nomeados por Omega(sqrt(n)); possui contador binomial EXATO O(n), explicitamente
creditado, e seis checks aritméticos, não benchmark de desempenho. Não inferir
exclusividade contra todos algoritmos TV ou salvar o gate negativo. A suíte
mantida passa170 testes em70,627s. Prioridade suficiente, revisão humana e
suficiência editorial permanecem abertas.

A49 V27 tem um NOVO rascunho matemático de11 páginas e PDF congelado em
work/generated-v27. Inclui bound Markov, custo completo/bit/source chains,
prova da separação dos upper baratos e AMBAS campanhas360. Todos45 pares por
campanha/macros são derivados de hashes; regeneração byte-idêntica, sem warnings,
11 páginas finais visualmente conferidas. V25 continua FAILED0/36 e V26 é só
DESENVOLVIMENTO1/45. Rascunho, correção e QA não fecham a meta científica ou
inventam revisão humana; originalidade/suficiência editorial permanecem abertas.

A49 V28 consolida esta candidata após o feedback, sem tentativa50 ou novos
forwards. Protocolo escrito antes de código; controles inferiores clássicos
com range gramatical passam105 oráculos (33 massas zero indefinidas).
Auditoria completa de decisões conserva45 pares antigos,33 intervalos/12
recusas compartilhadas históricas. Há22 regiões adicionais ACCEPT e31 REJECT;
grade ilustrativa completa tem1 ACCEPT/8 REJECT adicionais, mas ZERO escolhas
de menor word-width nas120 políticas. Somente lowers/range custam108,784s wall,
além de preparação/posteriors e controles/cores históricos, distinguidos por
producer. Não promover isto como economia de memória neural, dJev mais rápido,
confirmação independente ou publicação. V25 continua0/36. Mapa das obrigações
de prova e antecedentes preserva lacunas: chart polinomial e Markov escritos
ainda não implementados; prioridade/revisão humana/utilidade suficiente abertas.

A49 V29 encerra auditorias de arredondamento e fecha a objeção de composição
direta: Chan2006 Theorem2.6 já fornece kernel planar por SUBSET de pontos
originais, tamanho/construção O(eta^-1/2); os envelopes de2.1/2.2 fornecem
consultas batched. A reconstrução escrita simetriza os vértices, usa paridade
para inteiros, ordem das cadeias para envelopes racionais exatos e indução
de Fu: recupera o MESMO bound produto/Markov/forest e estabilidade em bits.
Não usar uma geometria clássica mais fraca como adversário. Isto NÃO refuta
o bound nem prova que um artigo TV anterior imprimiu aquela fórmula; reduz
a justificativa técnica atual a especialização de técnicas conhecidas.
Não anunciar prioridade/publicação ou contribuição própria substancial por
aquele expoente ou pelos inteiros. Nenhum código/teste/forward/timing novo,
tentativa50 ou vitória operacional. A24 e todas evidências antigas preservadas;
a meta de novidade/utilidade suficiente permanece aberta. Fonte, derivação
completa e escopos lidos estão em49/work/direct-composition-v29.md.

M71/A24 consumer V2 é refinamento de sistemas, sem nova teoria de quociente,
sumário numérico, marginais ou pilha limitada. Desenvolvimento540/540 completo
tem4/15 ganhos contra interfaces igualmente esparsas; suplemento compacto180/180
preserva144 conclusões/36 recusas,99 checks de massa e os mesmos quatro estados
com vantagem delimitada de tempo/capacidade. O piloto neural posterior451de419
concluiu270/270:246 completos24 recusas0 erros,1345 forwards novos mais um
warmup. Candidata30/30,30 trajetórias cursor/full-sparse literalmente iguais,
1321 checks de amostras/IDs e735 checks contra massas exatas. Só2/15 passam
o critério integral quente contra TODOS controles concluídos; nesses dois,
três controles compactos recusam sob3GiB. Zero estados têm vitória temporal
com todos seis controles concluídos. Duas seeds e os mesmos cinco documentos
antigos não são confirmação independente ou ganho semântico. Modelo/carregamento
ficam fora do custo quente; frio é reconstruído, não executado separadamente.
Dados/custos/recusas publicados em24/work/evidence/consumer-v2-neural-v1;
3,43GB de heads permanecem locais, explicitamente sem reprodução offline
integral. A suíte180 testes passou no preflight, sem checks concorrentes aos
timings. Originalidade específica de24, consumidor externo justificado e
publicação seguem abertos. Não promover reparo de API, piloto ou capacidade
a vitória geral sobre EPIC/controles GPU, nem garantia de mestrado.

M72/A24 V3 identifica o consumidor publicado Mosaic, commit36945e4b3c64.
Seus kernels sequencial/paralelo GPU e minimização são controles obrigatórios,
com igual compilação/cache. A ponte inicial SEM EOS mantém fonte externa
intacta e passa5576 checks de linguagem,21220 marginais e8640 amostras,
CPU/CUDA; máximo erro observado4.76837158203125e-7. Não é garantia global da
lei arredondada, novo head, vantagem temporal ou novidade. Ambiente Torch2.8
difere do serving completo Torch2.13. Dois drafts de fixture falharam e foram
preservados. Prova EOT/PAD variável antecede implementação: massa rasa deve
vir da linguagem terminada VERDADEIRA, nunca do surrogate de whitespace.
Consumidor real é identificado; efeito útil/originalidade/publicação seguem
abertos. Não promover adaptação de API ou profundidade3 como descoberta.
O contrato EOT/PAD posterior passa8284 checks de linguagem minimizada,28
checks exatos de massa/cauda,3720 marginais e1200 amostras CPU/CUDA. Massa
verdadeira e surrogate são explicitamente separados. Três oráculos racionais
novos incluem a lei conjunta com boundary variável e não usam Torch no CI.
Ainda sem novo head ou timing/benefício integral desta versão.
O screen full-V45/45 de4c80a59 termina42 massas positivas/3 rasas zero;
190 configurações nativas completas/corretas,20 guards CONSERVADORES de
alocação,0 erros/warnings. Trinta bounds conferem com massa terminada exata.
Gate apenas de recursos14/15; zero forwards novos. Não tratar guards como
OOM medido, prefixos antigos como corpus novo ou diagnóstico como velocidade.
V4 escreve antes de código a obrigação de CPU simbólico competente e cache
compatível; não atribuir o custo de minimizar DFA a toda inferência CPU.
V4 materializa esses controles e uma CFG EOT/PAD DIRETA, com scanner DONE e
gramática próprios, fontes do compiler/posterior de23 intactas em namespace
separado; hook de finalização é explícito. Três controles CFG, CPU simbólico,
novos heads sintéticos/aliases fixos, cache de prefixo e ranking passam11
oráculos focados e191 testes totais73.521s. O draft de ranking que comparava
ordem de tuplas em vez do conjunto foi preservado. Torch2.13/CUDA13 isolado
também passa ambos preflights nativos; não é serving HF completo. Sem novo
head neural ou gate temporal. Controles por quociente/sparse FA continuam
obrigatórios quando aplicáveis; não atribuir buffers densos a toda inferência.
M73 acrescenta controles clássicos GPU por classes: FA esparso e DAG por
camada, cada um com2184 marginais/88 amostras CPU/CUDA. O DAG não repete
estados inacessíveis em todas posições. Não são nova teoria ou Mosaic nativo.
Operação completa CUDA passa14 checks/60 palavras enumeradas;2 oráculos de
decisão e193 testes totais75.536s. Draft de sintaxe incorreta no auditor foi
preservado antes de qualquer timing. Protocolo ainda pré-medição:17 métodos,
765 registros;315 iniciais só podem provar decisão NEGATIVA, nunca vitória.
Não usar o limite refinado de confiança para reduzir a cobrança da amostra
anterior. No Mosaic lido, LLaDA1 usa ranking por marginal, mas LLaDA2/SGLang
default usa confiança do MODELO; não atribuir o custo de marginais a esse
default nem inventar superioridade semântica ou serving completo.

M73/A24 V4 gate operacional está NEGATIVO no produtor0c75b91:315/315 registros,
630 operações frio/quente corretas,135 rankings exatos135 matches de cache.
Ambas candidatas0/15 contra controles obrigatórios concluídos;450 registros
restantes não executados não podem reverter as falhas necessárias. Nenhum
forward novo ou confirmação independente acionada. Sparse FA/DAG por camadas
GPU são controles clássicos e vencem esta aplicação; não promovê-los como
nova teoria. A vantagem antiga3/15 vale sob os comparadores originais, não
sob estes controles mais fortes. Dados/decisão completos em24/work/evidence/
consumer-v4-development-first-v1. A meta científica permanece aberta.

A51 começa apenas com contrato/prova escrita antes de protótipo. Candidata de
sistemas audita a lei FINITA realmente executada por tickets inteiros GPU e
corrige palavra original por rejeição escalar exata. Max-product, rejeição,
intervalos, multiply-high e EBUS são antecedentes; não reivindicar princípios
ou teoria própria substancial. Consumidor LLaDA2 usa confiança do MODELO; não
prometer marginais condicionadas desta operação. Controles intervalares lazy
podem evitar correções CPU e são obrigatórios. Exatidão de pesos binary64 não
é ideal-softmax, lei RNG nativa, qualidade ou benefício prático/publicação.
Antes de código extenso, precisa de diferença útil concreta e controles fortes.

A51 V1 referencia racional passa cinco oráculos:2910 categorias279068 palavras
finitas9986 probabilidades; lei conjunta JSON/EOT/PAD/aliases/budget corretos.
Primitivas opt-in PTX .rm/.rp e mul.hi passam18734 checks Fraction/inteiros,
inclusive subnormais/overflow. Suíte198 PASS77.017s e make check PASS. Nenhum
forward ou timing/benefício/originalidade novo. V2 exige controle intervalar
com MESMO uniforme após ambiguidade e corrige escopo de leitura primária;
não chamar estas construções clássicas de descoberta ou a meta de cumprida.

A51 controle intervalar completo passa768 replays JSON e4096 prefixos de uma
lei conjunta dyádica; draft com erro de compilação preservado. ScreenV5 fonte
3e6b84c usaTODOS15 heads antigos:240 palavras GPU/240 replays literais,30 massas
exatas,zero fallback/recusa/erro. Não é timing, corpus/head novo, ganho próprio,
novidade ou meta cumprida. V6 escreve envelope por telescopagem de potenciais/
fatores de totais inteiros, evitando segundo max-DP; princípio CLÁSSICO, não
promover como teorema próprio antes da auditoria e vantagem prática.

A51 candidata GPU tickets/correção V8 passa980 condições de contagem,181 razões
completas W/Q,832 propostas/packets literais CPU-GPU e192 JSONs aceitos. Guards
142 casos/1088 condições/seis recusas passam. Suíte203 PASS75.441s. Primeira
recusa por clipping de potencial zero e draft do checker0/0 ficam preservados;
V8 mantém somente zeros CERTIFICADOS. Potenciais aproximados arbitrários zero
não recebem essa licença. Caso positivo subnormal recusa candidata, mas controle
intervalar exato conclui; não ocultar. Sem tempo/head novo ou vitória própria.
Próximo gate precisa comparar custo completo com o controle intervalar competente,
sem herdar resultados de viabilidade ou promover princípios clássicos a novidade.

A51 V9 congela ANTES de timings protocolo/runner/auditor first90 somente
NEGATIVO:15 heads antigos3 repetições2 métodos, operação CUDA completa e
política comum por confiança do MODELO. Gate necessário20% mediana pareada
wallECPU incluindo clock antigo do modelo, sinal favorável em todas repetições.
Não permite positivo antes de TODOS controles e nova aplicação neural completa.
Compilação compartilhada cobrada em primeiro-query decomposto, JIT/setup
registrados, logs fora dos timers e todo trabalho numérico dentro. Oito checks
full-V e205 testes PASS71.777s. Otimização anterior aos timings reutiliza upper
já pronto e bound de FAIL admitido; oráculos completos iguais. Nenhum tempo
competitivo/head novo foi creditado a esse preflight.

A51 V9 aplicação está NEGATIVA: produtorb18c5b4 completa90/90 registros,180
operações corretas sem erro/recusa, candidata tickets/correção0/15 frente ao
controle intervalar exato. Custos de tabelas+correção vencem especialmente nos
grafos grandes. Nenhum controle restante ou head independente acionado. Piso
aritmético de CPU do decoderZERO já impede o gate total20% em14/15 sob os
clocks antigos comuns; não alterar o critério nem usar isso como vitória.
Dados/protocolo/fontes completos preservados. Controle intervalar é clássico,
não promover sua mera implementação a nova teoria/conquista editorial. A meta
científica do usuário permanece aberta; não insistir nesta aplicação só por
correção numérica ou derrotar um baseline CPU mais fraco.
