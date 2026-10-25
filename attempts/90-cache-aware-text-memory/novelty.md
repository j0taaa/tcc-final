# Triagem de novidade — A90, 23/10/2026

Busca dirigida, sem certificação de prioridade mundial. Fontes primárias lidas;
`source/manifest` (em `sources/manifest.json`) registra hashes dos downloads.
Os números de autores abaixo não são reproduções locais nem evidência da A90.

## Antecedentes obrigatórios

- [DiffuMask](https://arxiv.org/html/2604.06627v1), §3 e avaliações: poda hierárquica
  por shot/token, previsão de máscaras paralela com dLLM ajustada, transferência
  entre consumidores. Implementa compressão por difusão; não presume consumidor
  exclusivo nem reivindica edição de memória online nesta leitura.
- [DiffuAgent](https://aclanthology.org/2026.acl-long.2036.pdf), §5.1, eqs. (3–4):
  memória textual anterior + eventos recentes + tarefa → memória nova; atualiza
  periodicamente e retém interações recentes. §6.1/Tabela 3 já mede dLLMs como
  memória para agentes AR. Portanto **memória incremental dLLM → AR já existe**.
  Essa comparação não é uma avaliação da política A90 com custo local de KV.
- [billion-context](https://github.com/ranxianglei/billion-context), README e
  [paper §3.3–3.7](https://github.com/ranxianglei/billion-context/blob/fdbddd05ad485c88b745cc421dcd8a3b55f57b50/paper/model-driven-incremental-hierarchical-compression-training-free-multi-generational-context-management-for-long-lived-coding-agents.md):
  blocos, proteção de zonas recentes, compressão de incrementos consumidos,
  hierarquia e recuperação de originais. Evita reescrever prefixos estabelecidos,
  compactando ranges e promovendo summaries. Inspeção de `kernel/src/compress.ts`,
  `refold.ts`, `decompress.ts`, `compression-rules.ts` no commit
  `fdbddd05ad485c88b745cc421dcd8a3b55f57b50`: validação de patches/ranges, refold
  in-place e tratamento de modificações que quebram prefixos. Existe mecanismo
  implementado; a alegação geral de prefixo sempre intacto depende do range e da
  serialização concreta. Não adotamos publicidade de bilhões de tokens, economia
  nem cache-hit como medição independente ou garantia tokenizer/KV.
- [LLMLingua-2](https://aclanthology.org/2024.findings-acl.57/), §3: distilação de
  dados de compressão e classificador bidirecional de tokens para compressão
  extrativa agnóstica de tarefa. Extração e preservação de informação são controles
  conhecidos. Piloto usa seleção extrativa própria simples, não reproduz LLMLingua-2.
- [LongMemEval](https://arxiv.org/html/2410.10813v2), §§3–5, e
  [repositório oficial](https://github.com/xiaowu0162/LongMemEval): atualização de
  conhecimento, tempo, múltiplas sessões e abstenção. Arquivo oracle contém sessões
  de evidência, não recuperação real de todo o histórico. Usamos versão cleaned
  recomendada pelo README (2025/09), sete IDs por hash sem filtro de resultados,
  histórias completas em ordem cronológica; perguntas e metadados de resposta
  removidos das entradas dos compressores. Amostra permite diagnóstico delimitado,
  sem acurácia oficial nem conclusão de cobertura ampla.
- [Elastic-dLLM](https://arxiv.org/html/2605.18165v1), §§3–4: comprime computação
  redundante de MASK preservando posições e protege MASK terminal em variantes
  block diffusion. Seu objeto é o custo interno da dLLM; não equivale a compactar
  memória textual para consumidor AR. Pode ser otimização ortogonal, não evidência
  favorável à A90.

## Colisões dirigidas adicionais

- [CADOC](https://arxiv.org/html/2609.37012v1), §§2–5, Apêndices A–C: substitui
  objetos por cards recuperáveis e agenda commits por custo acumulado de espera
  versus reconstrução compartilhada de cache; trata explicitamente edição precoce
  invalidando o sufixo. Há algoritmo, replay e avaliação de sistema reportados;
  não é apenas sugestão. Seu custo principal é economia de tokens tarifados
  `N+wR`, não latência GPU local sincronizada de compressor dLLM. **Impede alegar
  que decidir quando compactar usando cache é contribuição nova.** Seus controles
  citam Self-GC e TokenPilot; prioridade desses métodos não foi auditada integralmente.
- [ACON](https://arxiv.org/html/2510.00615v3), §§3.2–3.4: objetivo de recompensa
  downstream e custo de contexto, atualização de guidelines por falhas contrastivas,
  destilação em compressor menor. Implementa otimização e distilação; não somente
  intenção futura. Objetivo conjunto qualidade/custo e supervisão downstream não
  são novos por si. Não é a mesma política de edição tokenizer-aware proposta.
- [How Should Diffusion Language Models Edit Code?](https://arxiv.org/html/2609.38257v1),
  §§3–5 e apêndices: implementa rewrite, search-and-replace e localizar+infill;
  controles com regiões-oráculo expõem falhas de localização. Edição de múltiplas
  regiões por difusão não é novidade; código difere de memória factual, mas a
  dificuldade de seleção/dependências é antecedente obrigatório para esse mecanismo.
- [Decision-Aware Memory Cards](https://arxiv.org/html/2606.08151), §3:
  seleção/compressão de unidades, expansão de vizinhos de grafo e rankers treinados
  por sinais de utilidade. Não reivindicar seleção de dependências ou treinamento
  por utilidade como ideia ausente da literatura. Avaliação tem escopos distintos
  (incluindo recuperação de arquivos, não execução de patches).
- [Don't Break the Cache](https://arxiv.org/html/2601.06007v1): avalia fronteiras de
  caching em workflows longos. Motivação para medir custo real, não prova de ganho A90.
- [Cache Engineering for Agents](https://arxiv.org/html/2610.28577), §§2–4,
  Apêndice A: estado de KV pode depender das operações, além de tokens/posições.
  Implementa operações e serving que acompanham esse histórico. A90 usa somente
  prefixos causais normais, mesma configuração, sem drop/reposition de KV de sufixo;
  assim LCP de IDs mais cache crop é válido no escopo declarado. Não generalizamos
  para KV esparso/relocalizado, nem prometemos identidade bit a bit de kernels.
- [distil](https://github.com/dshakes/distil): implementação pública afirma
  compressão do tail, estabilidade de prefixos e custo por tarefa. Consultado como
  colisão adicional de engenharia; publicidade/qualificações não auditadas e não
  usadas como evidência de efeito. Evidência primária mais direta já é CADOC/BC.

## Busca e fronteira própria

Consultas em 23/10: `diffusion language model editable memory incremental cache
aware compression dependent updates`; `LLM memory compression prefix cache
preserving incremental consolidation training downstream utility`; `diffusion
text editing dependent factual updates memory summarization DiffuAgent`;
`cache-aware context compression`; `diffusion memory consolidation language`.
A ausência de um resultado idêntico nessas buscas **não prova originalidade**.

O diferencial desejado ainda seria um algoritmo ou pós-treino específico que
escolha e realize edições factuais dependentes minimizando **custo integral real**,
com validade de tokenizer/template/cache e vantagem sobre AR com a mesma interface.
A política heurística implementada na V1 é instrumento experimental: sobreposição,
fechamento, blocos estáveis e patch conjunto. Não há teorema, seletor aprendido,
perda nova nem evidência de mecanismo exclusivo da difusão. Adicionar penalidade
por ruptura de cache à fidelidade é proposta de objetivo, não contribuição
substancial estabelecida. Não selecionamos pós-treino por lacuna nominal.
