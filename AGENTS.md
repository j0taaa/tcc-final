# AGENTS.md

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
  A suíte atual tem152 testes, incluindo as duas regressões reais de timer,
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

## Perguntas obrigatórias para cada ideia ou implementação

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
