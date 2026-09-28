# Comparação com o EPIC: resultado e correção da conclusão

A comparação agora usa o gerador LLaDA original do EPIC e também a recuperação
oficial do seu wrapper. **O MWPC não demonstrou superioridade geral de precisão.**
Há um benefício de tempo frente a determinadas configurações, com uma relação
entre custo e qualidade que precisa ser apresentada integralmente.

O [relatório principal, com recuperação](generated/m23-recovery-results.md),
contém todos os resultados. Os relatórios dos geradores
[por bytes](generated/m23-byte-results.md) e
[com lexemas naturais](generated/m23-lexical-results.md) preservam o resultado
antes da recuperação. O protocolo e suas correções estão
[registrados](m23-epic-protocol.md), incluindo o piloto malsucedido como comparação
funcional por texto literal.

## O que foi medido

São os mesmos 100 pedidos sintéticos M22, duas execuções por configuração,
ordem inicial invertida e rotação por pedido, LLaDA-8B-Instruct NF4, mesma revisão,
mesma GPU, prompts, catálogo permitido e 24 posições. Houve 2.425 gerações reais
incluindo o piloto. Não são 2.425 tarefas independentes nem um novo holdout.

O EPIC usa o checkout fixado `5b1b31098f34ed3691d2a9f4aae14fdf5839d072`, sem
alterações no código vendorizado. Regular cover e verificação DFA-free foram
ativados. Os rastros confirmam commits de várias posições nos schedules paralelos.
O schedule de 24 etapas transfere um token por etapa e não aciona o lote mínimo
de dois; é um controle de orçamento, não evidência de paralelismo nessa condição.

Foram avaliados vocabulário nativo e uma variante com os domínios posicionais
M22, gramática por bytes e lexemas naturais, etapas 1/2/4/24 conforme cada config.
A variante lexical evita depender exclusivamente de uma representação potencialmente
ruim para o EPIC. Nas configurações nativas comparáveis, trocar a representação
preservou os acertos observados dos geradores.

## A recuperação muda a interpretação

O gerador isolado retorna algumas sequências incompletas; o wrapper EPIC oferece
`autocomplete_valid` para completá-las. Tratar todas como derrotas definitivas
exageraria a vantagem do MWPC. Foram reexecutadas **496 recuperações**, usando os
estados finais exatos arquivados, a função upstream e a mesma gramática, sem modelo
nem gabarito. Todas retornaram uma conclusão e preservaram os fragmentos fixos.
Todos os 2.000 resultados EPIC avaliados após essa etapa são chamadas válidas no
catálogo, incluindo os 1.504 que já estavam completos.

Com lexemas naturais, o MWPC acerta 65/100 nas duas rodadas; EPIC + recuperação
acerta 65 e 63 com uma etapa, 74 com duas, 81 com quatro e 92 com 24. Portanto,
a comparação anterior com um guloso próprio não autorizava afirmar vantagem
sobre EPIC. A recuperação variou algumas respostas entre repetições de estados
iguais; os dois resultados foram mantidos, sem selecionar o mais favorável.

A mediana do MWPC nessa coorte foi 280,9 ms por pedido. Os tempos reconstruídos
do EPIC lexical foram 442,5 ms (uma etapa), 369,0 ms (duas), 631,4 ms (quatro)
e 2.427,8 ms (24). **Reconstruído** significa tempo de geração medido somado ao
replay CPU da recuperação; não é uma medição conjunta do pipeline. A recuperação
custou cerca de 4–6 ms medianos quando necessária. Setup recriado apenas para o
replay foi excluído, pois o wrapper já possui gramática e lexer.

O EPIC de duas etapas usa 200 forwards contra 205 do MWPC e ainda acerta mais
após recuperação. Assim, a diferença de qualidade não pode ser explicada apenas
por mais avaliações do modelo. Domínios, seleção, confiança e conclusão também
diferem. O resultado numérico é uma métrica secundária: MWPC e EPIC lexical de
duas etapas chegam ao valor esperado em 81/100; isso não transforma seus 65 e
74 acertos de chamada em empate na métrica principal.

## O que é defensável no TCC

O resultado positivo é **menor tempo neste conjunto frente a configurações
específicas do EPIC**, com os custos de qualidade explicitados. Frente ao EPIC
lexical de uma etapa, os acertos observados são próximos e o MWPC é mais rápido;
isso não estabelece estatisticamente não inferioridade de precisão nem uma
vantagem geral sobre a melhor configuração do concorrente.

A garantia MWPC continua sendo maximizar os pesos das propostas dentro do suporte
finito de cada etapa. Ela não garante a operação correta, o melhor programa ou a
melhor trajetória. M22 isola melhor a seleção contra o guloso com mesmo parser e
suporte; M23 mede o confronto entre pipelines e não atribui toda diferença ao
objetivo MWPC. A novidade deve continuar delimitada à adaptação e avaliação,
com referência aos algoritmos e decodificadores anteriores.

Para a próxima investigação, o teste prioritário é controlar o número de propostas
aceitas por etapa e comparar curvas de custo/qualidade com EPIC **incluindo sua
recuperação**, em novos pedidos e depois em um benchmark de APIs. Essa direção
está planejada; nenhuma nova vantagem desse ajuste foi medida aqui.

## Limitações de contrato e metadados

EPIC usa lacunas abstratas e admite EOS ou EOT; MWPC preserva domínios por posição
e EOS finito. Mesmo `domains` não transforma o checker EPIC em um solver de slots
finitos, e sua máscara renormaliza a confiança. A recuperação pode completar além
dos slots ou usar sequências fora dos domínios posicionais. O catálogo canônico é
compartilhado, mas o lexer EPIC tolera whitespace; a avaliação usa AST, sem reparar
ou executar código Python arbitrário. Não se contam MASKs ocultados como respostas.

Nos registros antigos deste M23, `support_policy` foi herdado da configuração
base do MWPC. Para EPIC, os campos explícitos `proposal_support`,
`confidence_policy` e `exactness_scope` descrevem a política realmente usada;
esse nome herdado não significa que EPIC otimize o suporte MWPC. Os registros
brutos não foram reescritos. `batch_selected` conta propostas retornadas pelo
seletor; eventos de canvas verificam commits reais, pois um lote pequeno pode
ser descartado pelo wrapper.

As medições cobrem uma linguagem pequena, um modelo quantizado e uma GPU.
O PDF anterior ao M22 não foi atualizado nesta comparação. Este relatório,
os arquivos gerados e os dados versionados são a evidência nova.

## Reprodução sem modelo

```bash
.venv/bin/python scripts/exact_commit/summarize_epic_tools.py \
  docs/artifacts/raw/m23_epic_tools_v1/confirmation \
  docs/artifacts/raw/m23_epic_tools_v1/repeat \
  --output docs/research/generated/m23-byte-summary.json \
  --report docs/research/generated/m23-byte-results.md --check
.venv/bin/python scripts/exact_commit/summarize_epic_tools.py \
  docs/artifacts/raw/m23_epic_tools_v1/lexical_confirmation \
  docs/artifacts/raw/m23_epic_tools_v1/lexical_repeat \
  --output docs/research/generated/m23-lexical-summary.json \
  --report docs/research/generated/m23-lexical-results.md --check
.venv/bin/python scripts/exact_commit/summarize_epic_recovery.py \
  docs/artifacts/raw/m23_epic_tools_v1/recovery \
  --output docs/research/generated/m23-recovery-summary.json \
  --report docs/research/generated/m23-recovery-results.md --check
```

O replay real da recuperação usa `run_epic_recovery.py --config
configs/experiments/m23_epic_recovery_v1.json`, em árvore limpa e congelada.
Inferência é opt-in pelo `run_tool_screen.py` e cada config M23 correspondente.
