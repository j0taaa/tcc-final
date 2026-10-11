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
