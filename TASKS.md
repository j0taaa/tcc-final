# Pendências

Este arquivo contém apenas trabalho atual. Evidências e tarefas encerradas são
consultáveis no [histórico](docs/history/README.md); o panorama científico está
em [docs/status.md](docs/status.md).

## Pesquisa

A contribuição própria útil continua aberta. A71 permanece uma candidata
de acoplamento. A72 não foi selecionada como contribuição central após
o [gate V2 negativo](attempts/72-recursive-syntax-factor-width/README.md):
seis capturas neurais reais, nenhuma vantagem integral. Suas provas
teóricas ficam preservadas; não ampliar essa aplicação para salvar o gate.

A aplicação offline A80 também foi encerrada sem vantagem integral no
[gate V1](attempts/80-private-clipping-calibration/result.md). O lema de
calibração permanece preservado; não alterar casos ou controles para resgatar
essa execução. A busca por métodos distintos com contribuição própria e
utilidade demonstrável continua aberta.

- [ ] Auditar a prioridade específica e justificar um consumidor com vantagem
  integral para [A81](attempts/81-sparse-tempered-mixture/README.md), antes
  de selecionar protocolo ou campanha.
- [ ] Para [A87](attempts/87-conditional-choice-readout/matching-probe-analysis.md),
  concluir prioridade específica e adequação do método de auditoria por
  alvos não casados: prova escrita de esperança `2OPT` arbitrária e
  `OPT+1` perfeita; 83.679 execuções do oráculo exaustivo passaram.
  Revisões independentes não localizaram o mesmo passo nos antecedentes
  ESA/IJCAI, mas isso não certifica novidade mundial. A qualificação nativa
  [V1](attempts/87-conditional-choice-readout/native-result-v1.md) não justificou
  implementar a auditoria: seis propostas corretas já certificadas antes dela,
  duas falsas fora da garantia de custo. Não ampliar V1 para resgatá-la.
  A nova prova e a auditoria CPU sustentam uma candidata teórica em FTC;
  não demonstram ganho próprio de dLLM nem selecionam sozinhas esse tema.
  A aplicação distinta de conjuntos por limiar também foi examinada: nos
  320 cenários exploratórios, advice-first e capped-lazy foram ótimos em
  todos e a candidata não venceu nenhum. Não ajustar esse replay para resgate.
  A aceitação do núcleo teórico como centro do TCC foi perguntada ao usuário;
  o requisito original permanece vigente sem resposta.
- [ ] Antes de selecionar outra campanha, justificar uma contribuição própria
  com teoria, utilidade geral e benefício demonstrável para o TCC de impacto
  solicitado. A leitura de LAVE/Saber/DecoCal e a avaliação independente não
  justificaram desenvolver atualização durante rejeições como tema central
  de [A83](attempts/83-epic-operational-diagnosis/README.md). Seus controles de
  engenharia ficam preservados; A82 também não está selecionada para campanha.
  O piloto prospectivo [A84](attempts/84-full-marginal-certificate/result-v1.md)
  também falhou: reduziu tempo, mas perdeu acurácia nas duas famílias. Não
  alterar margem/subset para resgatar essa aplicação nem promover sua prova
  local a garantia de qualidade do modelo. O replay prospectivo
  [A86 V3](attempts/86-prefix-closure-planning/result-v3.md) também falhou nas
  duas famílias: custos previstos com preparo 18,18%/22,68% maiores que o
  serial. Aplicação encerrada; não ajustar custos, margens ou casos para
  salvar esse gate, nem implementar o decoder acelerado por esse resultado.
- [ ] Auditar a prioridade específica e a relevância da interface A71 frente
  às construções clássicas já reconhecidas na própria tentativa.
- [ ] Antes de qualquer campanha neural, justificar variabilidade útil de EOS,
  contrato numérico do consumidor e custo integral contra controles fortes.
- [ ] Reconciliar qualquer nova versão científica do artigo com os resultados
  operacionais posteriores. O ganho histórico A24 de 3/15 não é superioridade atual.

Não reiniciar aplicações encerradas de A65, A68 ou A70, nem ampliar campanhas
apenas porque um oráculo finito passou. Nenhuma execução neural está selecionada
por esta reorganização.
