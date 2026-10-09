# Tentativa 21 — Grupos de tokens dependentes do estado lexical

**Resultado negativo preservado:** 1026 registros MDLM/CUDA, 948 completos,
897 comparações exatas e nenhuma divergência; 0/18 ganhos fortes tanto
para GAC quanto para root frente a TODOS os controles não contextuais,
incluindo globais. Menos recompilações não bastou para o custo completo.
Nenhuma expansão à confirmação fresca neste protocolo. Dados em work/evidence. Fontes independentes
copiados de20 (`7b33f6d`), sem import mutável de outra tentativa. Não alterar
núcleo ou EPIC. Todos os resultados negativos anteriores permanecem congelados.

1. **Uso:** preencher JSON recursivo usando novos top16 da dLLM. Preservar
   EXATAMENTE os IDs, compromissos, probabilidades, suporte e fallback originais,
   mas agrupar palavras conforme seu efeito NO ESTADO lexical do caminho.
   Cada caminho tem estado explícito: não assumir contexto conhecido da lacuna.
2. **Relevância:** lexer/semirings/GAC são clássicos; partição global já está em
   FactorDLM Proposição2. Aqui os grupos podem se sobrepor: o mesmo token está
   em grupos diferentes conforme o estado. O circuito preserva esse estado,
   viabilidade de propostas originais usa união dos grupos que contêm o token,
   e fixação mantém todos esses grupos, não apenas um representante escolhido.
   Construção/atualização automáticas e equivalência da política são recorte
   candidato, não prioridade confirmada ou promessa de publicação.
3. **Escolha:** menos alternativas e recompilações que a partição global,
   mantendo a mesma trajetória. TODOS os dezesseis controles de20 entram,
   incluindo lexer simples, propagação/SAT e classes globais/reservas64/128.
   GAC/root/SAT contextuais são implementações fortes da MESMA contribuição.
   Ganho da representação não implica vencer outros solvers que a adotem.
4. **Matemática:** cada caminho do transdutor é determinístico; substituir o
   token por outro do grupo do estado atual preserva todo caminho lexical.
   Viabilidade original é união dos grupos suportados; commit retém grupos que
   contêm t. Crescimento cuja imagem nos estados preparados não muda conserva
   topologia/GAC. Cada partição global refina a local, portanto não há mais
   grupos contextuais que classes globais no mesmo estado. Custo/prova escritos.
5. **Experimentos:** protocolo antes dos novos forwards. Mesmos casos externos,
   máscaras4/8/16, ALL19 configurações, três repetições; zero gabarito injetado.
   >=20% wall E CPU frente a TODO controle não contextual concluído, incluindo
   classes globais; sinal em cada repetição. Se desenvolvimento passar,
   confirmação seis casos nunca-model-testados, nove repetições; todos os casos,
   inclusive perdas/inviáveis. Nenhum limiar será reduzido depois de medir.
6. **Custo:** cache (token,estado), teste de crescimento, agrupamento/membership,
   construção/gramática/GAC/SAT, consultas, reconstrução original, leitura de
   probabilidades, todos os forwards, memória e limpeza são contabilizados.
   Expansão que cria comportamento novo recompila; não declarar reutilização
   universal. EOS ausente, domínio finito, sintaxe e não qualidade semântica.
7. **Objeção:** grupo local pode crescer sempre, exigir tantas recompilações
   quanto o controle; materializar todos os caminhos pode custar mais que uma
   consulta; pré-compilação lexical clássica/eliminação de variáveis pode obter
   a mesma representação. Não transformar ganho de implementação em novo
   princípio matemático. Controlar consultas condicionais SEM apagar estados
   possíveis, e não somar recompensas de originais incompatíveis de um grupo.
8. **Artigo:** falta vantagem completa confirmada, antecedente mais próximo e
   avaliação humana. Se não superar lexer/classificação global competente,
   rejeitar como protagonista. Quantidade de código e testes não provam avanço.

Fontes: [FactorDLM Proposição2](https://arxiv.org/html/2609.32900v1),
[SynCode](https://arxiv.org/html/2403.01632v3),
[DOMINO](https://arxiv.org/abs/2403.06988),
[XGrammar](https://arxiv.org/abs/2411.15100),
[Quimper–Walsh](https://arxiv.org/pdf/0903.0470).
