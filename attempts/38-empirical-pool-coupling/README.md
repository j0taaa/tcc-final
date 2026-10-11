# A38 — Acoplamento por pool empírico: ótimo simultâneo com quatro draws

2026-10-11. DIREÇÃO ESCRITA antes de implementação. A37 preservada separada;
este controle mais forte foi encontrado por revisão adversarial, não por
seleção de benchmark. Não houve novo forward, treinamento ou timing.

## Oito perguntas antes de implementar

1. **Uso real.** Entregar duas propostas JSON/DSL de uma dLLM com menor
   repetição do mesmo resultado canônico, sem distorcer a distribuição de
   nenhum payload individual. Pode envolver EPIC completo com suas falhas e
   recuperação, ou uma transição realmente aceita com head congelado e
   estado suficiente. Esta segunda operação cobra seleção/parsing, mas pode
   compartilhar o forward; probabilidades de logits não são automaticamente
   as probabilidades dos estados aceitos. A GLC restringe cada geração. A aplicação
   precisa de duas propostas para um consumidor caro ou de avaliação imparcial;
   não é uma aceleração de gerar/verificar todos os candidatos baratos.
2. **Relevância.** Pool empírico e acoplamento por quantis são conhecidos.
   A candidata científica é a caracterização quantitativa: ótimo simultâneo
   por evento canônico com cap4, covariância nunca positiva para qualquer
   score, e custo esperado PONTUAL mínimo `4-2c+s3` entre TODOS os
   maximizadores universais com três ou mais chaves permitidas. O pior custo
   mínimo é4. Um alfabeto binário conhecido permite controles mais baratos.
   O princípio Bernstein binário também é conhecido. É necessário verificar
   se o contrato categórico/custo e as fórmulas já estão publicados. Não afirmar
   que combinar técnicas conhecidas ou provar correção basta para publicação.
3. **Escolha/controles.** Sem conhecer probabilidades, cada evento recebe
   ganho `p²(1-p)²`, o máximo admitido pelo contrato cap4; diversidade ganha
   pelo menos1/4 do máximo entre pares de mesmas marginais. Misturar metade
   com iid2 custa no máximo3 draws em média e garante1/8, contra1/13 de A37.
   Isso não é dominância pontual. Comparar iid2/iid3/iid4 e misturas, A37,
   RSS/sampling sistemático, probabilidades conhecidas, pool sem reposição,
   calibração/PPI quando disponíveis e custos de todos os payloads descartados.
4. **Prova sem código.** `work/theory-v1.md` dá algoritmo, lei, covariância,
   ganho de colisões, bound binário reduzido, attainment categórico e um
   argumento de custo pior-caso; `optimal-cost-v2.md` refina o custo de forma
   pontual, antes de implementar. Objetos construídos são provas, não medições
   de modelo. O menor custo de4 refere-se a atingir TODOS os ótimos sob cap4;
   não a qualquer ganho de diversidade ou todos os decoders informados.
5. **Experimentos.** Primeiro verificar a álgebra e o kernel por enumeração
   independente, procurando contraexemplos. Não existe protocolo neural ainda.
   Se a prioridade/aplicação passar, congelar novos casos externos, controles,
   custos completos e critério antes de medir. Perdas de A32/A34 não somem.
6. **Custo completo.** São chamadas INTEIRAS da operação escolhida, geração
   ou transição nativa. A primeira adaptação custa `4-c`; a versão escrita v2
   mantém a mesma lei e atinge o custo mínimo `4-2c+s3` sob o contrato.
   Quatro payloads no máximo, além da memória do gerador; canonicalização custa.
   A mistura iid2 custa `3-c+s3/2`. Inclua forwards, preparação, cópias, falhas e
   consumidor; não vender contagem como velocidade física. Se verificar é
   barato, mais candidatos/sem reposição podem ser melhores. Reutilize labels
   canônicos já obtidos; não invente atrasos caros para ganhar.
7. **Objeção.** A construção é uma aplicação de acoplamento empírico; a
   novidade pode reduzir-se a um corolário pequeno de Bernstein/exchangeability.
   Campos semanticamente equivalentes precisam de chave correta sem gabarito.
   Preservar marginais precisa ser útil ao consumidor, não requisito imposto
   para excluir outros métodos. O método não aumenta pass@1 nem supera a
   latência de EPIC. Side information/probabilidades conhecidas estão fora
   do lower bound, mas continuam controles práticos legítimos.
8. **Artigo.** Faltam comparação primária específica, auditoria matemática
   completa, oráculo mínimo e uso de custo demonstrado. Ler especialmente
   antithetic bootstrap, systematic/RSS, coupling2024, CARMS e Bernoulli
   factories. Leituras efetivas de Neal1995, Andrieu2020, Craiu/bootstrap,
   Casarin2021/2024 e STMC2020 estão em `primary-comparison-v1.md`; não
   excluir métodos conhecidos com base em títulos/abstracts. Não inventar
   revisão humana ou confirmação de prioridade.
   O artigo principal permanece A24; esta direção não foi promovida.

## Decisão inicial

Atacar os resultados escritos e sua redução a métodos antigos ANTES de
implementar. A38 não depende de implementação mutável de outra tentativa.
Se os resultados relevantes forem conhecidos, registrar isso e procurar uma
diferença útil; não iniciar outra grande campanha para justificar a ideia.

## V2 — referência mínima e objeções confirmadas

`work/couple.py` tem29 linhas. Cinco oráculos independentes PASS0.056s no
registro com hashes `work/evidence/law-v2.json`: lei de payloads/aliases/falhas,
custo4-2c+s3, todos32 verificadores de cinco payloads, scores não monótonos,
redução EXATA ao controle clássico de ranks, e controles informados mais fortes.
Suite inteira152 testes PASS68.353s; `make check` e Ruff explícito passam.
São testes de correção; nenhum input é um benchmark de modelo favorável.

A redução por ranks confirma que a construção básica é conhecida. O custo
pontual ótimo entre TODOS os maximizadores universais é a afirmação candidata,
com prioridade ainda aberta. `primary-comparison-v2.md` acrescenta Dice
Enterprise e mostra que métodos informados também combinam diversidade máxima
com covariância não positiva para TODOS scores; não enfraquecê-los.

`decoder-corollary-v2.md` escreve a ligação com a continuação adaptativa de
uma transição nativa inteira. Não implementa/revalida um adaptador EPIC,
não mede efeito semântico e não confirma velocidade, revisão humana ou
publicabilidade. O artigo principal não foi promovido por esses oráculos.

## V3 — fronteira minimax, antes de novo código ou campanha

As oito respostas acima permanecem, com estas mudanças explícitas:

1. **Uso:** duas propostas originais de uma transição aceita ou geração
   completa, com diversidade canônica garantida e avaliação sem viés. Uma
   continuação não precisa manter os mesmos próximos logits. O adaptador e
   o benefício depois do custo completo ainda precisam ser demonstrados.
2. **Diferença candidata:** `work/minimax-frontier-v3.md` demonstra uma
   fronteira exata de benefício/orçamento para TODOS os algoritmos universais
   adaptativos de cap4, incluindo retornar/clonar o primeiro payload. Isto é
   mais forte que o mínimo de custo entre maximizadores de v2. Ainda verificar
   prioridade e consequência útil; uma prova genérica pequena pode ser
   insuficiente como protagonista de um artigo sobre dLLMs/GLCs.
3. **Escolha:** com orçamento esperado máximo `b` entre2 e4, a maior fração
   garantida do ótimo informado de diversidade é `(b-2)/8`. Em `b=3`, mistura
   meia-iid2/meia-v2 atinge1/8, ótimo no contrato. Controles iid3 e informados
   NÃO são excluídos da avaliação prática por esta definição.
4. **Matemática:** prova por coeficientes multivariados, simetrização finita,
   ocupação de chamadas e dois limites de leis construídas, SEM benchmarks.
   Domínio admite arbitrariamente muitas chaves; há bound explícito finito.
   Não afirmar que um comprimento/vocabulário fixo tem o mesmo minimax exato.
5. **Teste:** auditar esse lower bound antes de implementar a pequena mistura.
   Depois verificar por enumeração a lei exata, custo e todas as propriedades
   anteriores. Nenhum protocolo neural congelado ainda; não medir e depois
   escolher métrica/classe para proclamar sucesso.
6. **Custo:** `3-c+s3/2` chamadas inteiras para a mistura meia-iid. Teto4,
   duas saídas, sem garantia de menor wall time. O comparador inferior admite
   paradas precoces e clones, eliminando uma restrição artificial de índice.
7. **Objeção:** informações de logits, ordenação de tickets, probabilidades
   conhecidas e cap maior podem vencer. A conexão nativa deve preservar
   estado/RNG e contabilizar rejeição/falha; vantagem de diversidade não
   garante ganho semântico grande nem supera gerar/verificar iid3 baratos.
8. **Artigo:** falta prioridade específica do novo lower bound, validação
   independente da álgebra, implementação/oráculo da mistura e aplicação com
   consumidor/custo plausíveis. Nenhuma revisão humana ou conquista EPIC.

Este addendum foi escrito ANTES de código da mistura e de novos forwards.
V1/v2 e seus registros continuam preservados, com as afirmações originais.

## V4 — mistura validada e análise de custo completo

Depois do freeze v3 `a760d16`/archive `d6a6d84`, a referência acrescenta
somente11 linhas para a mistura de orçamento3:40 linhas no total. Sete
oráculos racionais PASS0.091s incluem duas moedas INDEPENDENTES, todos32
verificadores raw, aliases/falhas e marginais condicionadas a CADA multiset
virtual. Essas verificações não provam o lower bound genérico nem prioridade.
`work/evidence/law-v4.json` registra comandos/hashes; suíte154 PASS69.932s,
`make check`/Ruff passam (`work/evidence/checks-v4.json`).

`full-cost-corollary-v4.md` aplica a identidade Wald finita PADRÃO ao trabalho
completo, inclusive custos correlacionados com o payload. Mesma lei conjunta
permite cobrar também a mesma continuação do par. Economia versus pool4:
`(2c-s3)*w`, e versus early-pool: `(c-s3)*w`, antes da diferença explícita
de overhead. Não declarar que isto é wall time medido ou vantagem contra iid3.

`primary-comparison-v3.md` registra leituras originais Huber2013/2015 dos
lower bounds e Dice Enterprise3.3--3.5.2. A fronteira é a candidata, não o
princípio de contagem/exchangeability/Wald. Prioridade/aplicação permanecem
abertas, sem novo forward ou promoção do artigo.

## V5 — contrato nativo pequeno, congelado antes de implementação

Os oito critérios são reavaliados antes do adaptador:

1. **Uso:** traduções de enunciados externos em árvores JSON recursivas
   executáveis; pares com a lei original de EPIC. Não criar regras Booleanas
   ou recuperar as direções15/16. A escolha por pares imparciais precisa ter
   valor para o consumidor; busca de melhor resposta é operação diferente.
2. **Contribuição:** fronteira e mínimo pontual continuam candidatos. O novo
   corolário `finite-domain-v5.md` limita a distância minimax finita por
   `11/(8M)`, sem fingir que tokenizer finito tem domínio infinito. Integração
   nativa sozinha NÃO cria novidade nem garante publicação.
3. **Escolha:** mesma lei dos pools clássicos, menos chamadas completas em
   esperança; incluir também iid2, novelty3 enviesado e seed-half barato,
   permitindo que vençam na aplicação. Nenhuma superioridade EPIC geral.
4. **Matemática:** todos os argumentos independem do modelo/código; o piloto
   verifica o vínculo ao native completo, não substitui prova de vantagem.
5. **Honestidade:** `native-protocol-v5.md/json` escolhe quatro registros
   input-only hash de TODOS1000 SVAMP, novo corpus pinado, antes de outputs.
   Duas seeds/sete métodos =56 registros, incluindo perdas e recusas. É
   PILOTO funcional/custo, explicitamente insuficiente para gate estatístico.
6. **Custo:** reruns nativos completos para cada chamada pedida; cobrar
   helpers, forwards, cache/head comum, parsing/cópias/reconstrução/overhead.
   Nenhum replay é creditado como execução evitada. Mesma preparação comum.
7. **Objeção:** independentes ou novelty3 podem ser melhores para busca;
   preservar marginais não pode ser desculpa artificial. O domínio neural
   restrito e logits acessíveis não herdam o lower bound universal desconhecido.
8. **Artigo:** precisa completar a auditoria de prioridade e evidência de
   uso relevante. Golds separados só após captura completa; não selecionar
   classes/métricas a partir dos resultados. Sem revisão humana inventada.

Nenhum forward ou adaptador novo foi executado ao escrever esta versão.
Fontes/helper próprios serão copiados por commit/hash, não importados de
trabalho mutável de outra tentativa. Licença SVAMP acompanha os inputs.

## V6 — adaptador preparado, ainda sem novos forwards

`work/native-preflight-v6.md` registra referência/controles próprios e nove
oráculos0.121s; suíte156 PASS68.012s, make check/Ruff PASS. O driver importa
dependências live, preserva streams privados CPU/CUDA/Python/NumPy e cobra
chamadas inteiras. Helpers são cópias por commit/hash, não imports mutáveis.
O controle pool4 pequeno tem a MESMA lei raw e não foi implementado com
sort caro. Novelty3 enviesado permanece concorrente barato.

Classificação inútil para iid2/seed-half fica só no diagnóstico posterior ao
timer; custos obrigatórios/coordenação permanecem incluídos. Nenhum output
ou timing neural novo foi visto nesta validação. Protocolo56 registros e
limitações do piloto permanecem os de v5, sem gate criado depois dos dados.

## V7 — captura completa preservada e novo teorema antes de código

`work/native-audit-v7.md` e seu JSON são gerados da captura original v6:
56 registros,169 chamadas nativas REAIS,1885 novos forwards. Todos35 calls
INCOMPLETE são preservados; não houve ERROR. Os primeiros IDs coincidem.
Adaptive usa28 calls contra32 pool/30 early nos oito pares, mas iid2 é
mais barato e todos esses acertaram2/8 pares; seed_half3/8. Isso não é
superioridade prática confirmada ou uma avaliação estatística independente.
Golds só foram lidos APÓS a conclusão; producer76f4bc1 e hashes preservados.

`work/semantic-coarsening-v7.md` escreve uma NOVA consequência comparativa
ANTES de implementar: classes pelo resultado observado do software melhoram
ou preservam pass2 de TODOS seus verificadores e o melhor score, enquanto
reduzem chamadas completas em esperança. Não precisa conhecer a resposta
correta. As oito perguntas estão respondidas nesse arquivo; prioridade e
utilidade de custo completo ainda precisam de auditoria. Um contraexemplo
impede alegar monotonicidade para variância de todo score real. Nenhum timing
v6 mede essa nova direção, e o artigo principal não foi promovido.
