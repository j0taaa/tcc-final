# Decisão — vantagem geral de resultado sobre lotes iid

## O que está demonstrado

Para um decoder de horizonte finito com kernels exatos especificados, agrupar
somente históricos completos idênticos e usar estratos independentes preserva
a lei de cada execução. Para TODO verificador de saída, a chance de encontrar
uma saída aceitável no lote é no mínimo a de K execuções independentes do mesmo
decoder. A melhor pontuação domina estocasticamente para qualquer pontuação;
a variância da média é no máximo a referência iid. Não se escolhe o verificador
depois de observar resultados para obter essas desigualdades: elas são universais.

Há desigualdade estrita em uma classe matemática admitida: duas classes de
JSON equiprováveis, uma por estrato, e K=2. Qualquer software que aceite uma
das classes recebe um candidato aceitável com probabilidade1, contra3/4 iid.
A operação útil é buscar entre múltiplas configurações/chamadas que um programa
consegue testar, ou avaliar expectativas do decoder com menor variância.
O sampler não conhece o resultado do teste. Isso não demonstra que o modelo
produz semanticamente bons candidatos ou que dLLMs sejam melhores que outros
modelos para a tarefa.

Mais geralmente, qualquer evento que ocupe um prefixo dos tickets atinge
min(1,Kp), o máximo possível pela desigualdade da união entre TODOS os lotes
de mesmas marginais. Há ganho estrito sobre iid para K>1 e0<p<1, incluindo
cobertura determinística quando p≥1/K. Ramos disjuntos iniciais de uma gramática
podem satisfazer a hipótese; ela não é presumida para semântica ou replay fonte.
É um corolário clássico, não uma nova reivindicação de prioridade.

## Evidência e limites

- Sete oráculos passam: todos os pequenos mapas/binárias admitidos,36 árvores
  adaptativas, todos os verificadores finais dos espaços enumerados e todas
  as menores principais da diferença de covariância, unranking de IDs originais,
  ponte full-V e recomputação de uma captura completa publicada.
- Cinco identidades/comparações selecionadas passam em Lean. A indução inteira
  continua prova escrita; não é refinamento universal do software.
- V1 top16 tem massa zero. V2 fonte6a69638 usa o mesmo head e todos50258 IDs,
  obtém64 candidatos JSON válidos e preserva os IDs fixos, sem novos forwards.
  Fonte/IDs não guiam o sampler. Para o evento de reconstrução dos IDs da fonte,
  K=2 passa de0.9789632926416021 para0.9790673626937444, diferença de apenas
  0.01040700521423 ponto percentual. Frações e todos os estratos estão no JSON.
  K=8/32 também têm desigualdade estrita exata; floats arredondam K=32 para1.
  Este evento não é avaliação de acerto semântico de pedidos reais.
- Preparação e coordenação têm custo, e mais diversidade pode fazer um cache
  de forwards visitar mais históricos. Não foi demonstrada redução da latência
  total ou de custo por resposta útil. Um único timing não recebe esse crédito.
- O algoritmo adaptativo foi testado em kernels pequenos, não executado num
  novo ciclo neural de A26. As184 chamadas de A24 não pertencem a A26.

## Comparador e novidade

O comparador que recebe a garantia geral é iid do MESMO kernel, com a mesma
preparação/ranking e política. Não é uma vitória sobre outra política EPIC,
sampling sem reposição ou ODD. Arithmetic Sampling e STMC já mostram que
diversidade/estratificação probabilística não são novas; o teorema local é
clássico. A adaptação de circuito original e o cuidado com históricos têm um
benefício operacional demonstrável, mas NÃO confirmam uma nova contribuição
teórica significativa ou suficiência para publicação. Não inventar revisão
humana. O apêndice expõe o resultado e os limites sem substituir silenciosamente
o protagonista24 ou prometer que todos os requisitos acadêmicos foram resolvidos.

Decisão: vantagem matemática de resultado sobre iid **confirmada sob o contrato**;
superioridade de tempo, relevância industrial medida e novidade acadêmica forte
**não confirmadas**. A documentação das perdas é evidência, não o benefício.
