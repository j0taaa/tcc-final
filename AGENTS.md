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
  nenhum ganho forte adicional sobre closed. A confirmação independente e o
  ciclo dLLM continuam pendentes. A25 investiga amostragem EXATA por envelope,
  sem excluir eventos profundos; tem prova escrita e seis oráculos pequenos
  da lei efetiva/CARS. Counter-only, counter+CARS e CFG compacta são controles
  necessários. Não atribuir os timings de24 à operação25. Nenhuma prioridade
  acadêmica ou geração completa de24/25 foi confirmada.
- Há garantias matemáticas delimitadas de amostragem, rejeições e reutilização.
  A comparação escrita com CARS trata sua atualização de prefixos visitados
  sob hipóteses explícitas; não demonstra superioridade geral de latência.
  A auditoria pequena preserva enumeração mais rápida e custos de preparação.
- Novidade, significância suficiente para publicação e vantagem prática ampla
  não estão confirmadas. Não apresentar esses objetivos como já atingidos.

Use [TASKS.md](TASKS.md) para tarefas/evidências atuais e
[attempts/README.md](attempts/README.md) e `attempts/catalog.json` para versões
preservadas. O [caderno científico](docs/research/contribution-plan.md) registra
antecedentes, provas, objeções e decisões. Histórico não é instrução para
restaurar código retirado ou insistir em uma hipótese refutada.

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
