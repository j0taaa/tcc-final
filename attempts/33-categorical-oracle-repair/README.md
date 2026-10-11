# A33 — Reparo categórico sem avaliar probabilidades

Iniciada em 2026-10-11, DURANTE a avaliação congelada de A32/v4. Esta é uma
tentativa independente, ainda sem implementação, execução neural ou novidade
confirmada. A32 não herdará este algoritmo, suas provas ou um novo comparador.
Não modificar seu produtor enquanto seus timings estão em andamento.

## Oito critérios antes do protótipo

1. **Uso.** Dois candidatos de um decoder dLLM+GLC, conservando literalmente
   o primeiro e a distribuição individual de ambos. A operação pretendida
   coordena transições completas de um head congelado, incluindo recuperação
   gramatical. A classe é um próximo estado suficiente, não uma regra criada
   pela dLLM nem uma resposta obtida do gabarito. JSON/DSL continua consumido por
   um verificador externo. O contrato abstrato também permite outros samplers.
2. **Diferença.** Barker, Bernoulli races, kernels reversíveis e comparação de
   Peskun são conhecidos. Reparo de colisões já aparece em A29. A candidata
   específica é um reparo por corrida sobre duas categorias, com lei conjunta
   explícita, custo esperado de oráculo independente do número de categorias
   e consequência estrita para toda propriedade terminal não degenerada,
   quando as classes distinguem estados completos. A prioridade e a dimensão
   desse incremento ainda precisam ser examinadas; não basta renomear Barker.
3. **Escolha.** Não exige densidades nem probabilidades das classes. A prova
   candidata oferece pass@2 maior que duas execuções iid do MESMO decoder,
   conservando pass@1, com até um draw extra esperado em cada encontro.
   Esta afirmação não é menor latência, ganho grande ou vitória contra iid3,
   iid4, temperatura mista, determinístico ou amostragem sem reposição.
   Esses controles e Barker com probabilidades conhecidas são obrigatórios.
4. **Matemática.** Um oráculo iid arbitrário P e uma classificação categórica
   fixada antes dos draws. Resolver uma colisão por uma corrida que termina
   ao observar uma das duas categorias. Demonstrar marginais completas,
   covariância de qualquer score, custo esperado <=3 draws totais e minimax3
   para sua lei-alvo. Depois demonstrar a consequência adaptativa com históricos
   completos. O princípio de corrida e o argumento de prefixos não são novos.
5. **Validação.** Primeiro oráculos racionais independentes, abrangendo todas
   as propriedades de leis pequenas, aliases e limites de recursos. Depois
   integração literal com o EPIC original, sem cortar rankings, recuperação,
   EOS, budgets ou classes pouco frequentes. Nenhum novo benchmark favorável
   deve ser inventado. A avaliação A32 continua sendo outra operação.
6. **Custos.** A corrida tem parada aleatória. Esperança limitada não fornece
   cauda uniforme rápida, memória pequena ou custo físico baixo. A classificação
   de um próximo estado pode exigir parsing e, se não houver head reutilizável,
   forwards; contabilizar ambos. Uma versão truncada pode conservar marginais
   por fallback simétrico, mas calcula outra lei, explicitamente delimitada.
7. **Objeções.** Este reparo pode ser apenas uma combinação direta de Barker
   com A29. A melhoria máxima de pass@2 de um evento raro é da ordem do quadrado
   de sua probabilidade, mesmo com antitético perfeito. Um comparator com mais
   saídas pode vencer. Usar uma classe incompleta mantém dominância fraca, mas
   perde a alegação de melhoria estrita de toda propriedade terminal. Não
   reintroduzir 15/16 nem alegar que rótulos de tokens predizem semântica.
8. **Artigo.** Faltam prova revisada, antecedentes específicos, oráculos,
   realização barata de transições completas e avaliação competente. Se a
   redução a um método conhecido eliminar a diferença, preservar e recusar
   a direção. Nenhuma revisão humana, prioridade ou publicação foi confirmada.

## Contrato inicial

Apenas investigação matemática em `work/theory-v1.md` e revisão em
`work/antecedents-v1.md`. Não importa fontes mutáveis de A29/A32. Nenhum
resultado do núcleo posterior ou de A24 prova novidade desta direção.

## Gate de redução, antes de implementar

O algoritmo reduz diretamente ao transformador estacionário de A29, usando
Barker para o alvo de colisões proporcional a p_i². A corrida é uma construção
clássica. O cálculo de custo esperado <=3 não fecha uma diferença relevante
suficiente por si só. Não ampliar como protagonista nem iniciar campanha
neural. Preservar a prova escrita e o controle; o objetivo continua aberto.
