# M24 — Compromisso por estabilidade estrutural em dLLMs

Estado: plano e referência enumerativa; **sem integração de produção ou novo
resultado com modelo**. Data: 2026-09-28. Depende de M22/M23 e preserva M19.

## Ampliação autorizada: triagem prática de políticas

Após o pedido de testar amplamente, a triagem usa 20 configurações congeladas em
`configs/experiments/m24_policy_development_v1.json`, sobre os primeiros 30
pedidos do desenvolvimento M22 v4: orçamentos 1/2/4/8/12/24; confiança
0,2/0,5/0,8; margens relativas 0/0,02/0,10; duas/três propostas por posição;
guloso com orçamento 8; revisão em outra chamada da mesma dLLM; MAP enumerativo
no catálogo; EPIC lexical 2/4/24 com recuperação oficial medida na mesma execução.
O smoke de dois pedidos testa a integração antes da triagem. Todos são dados de
desenvolvimento; nenhum ganho neles será chamado de confirmação.

Escolha antes do teste novo: manter MWPC b24 e EPIC 2/4/24; acrescentar até três
políticas de produção não dominadas em acurácia e mediana de tempo total no
desenvolvimento. Desempatar por maior acurácia e depois menor tempo. MAP sobre
catálogo é controle com suporte mais estreito, não elegível como substituto do
parser. Congelar cem pedidos novos antes de escolher políticas; depois executar
a confirmação e repetir com ordem inicial invertida. Guardar todos os resultados,
incluindo se nenhuma extensão superar o EPIC.

A revisão gera um novo canvas a partir do pedido e do rascunho, sem gabarito;
nunca modifica posições fixas dentro de um canvas. Conta os forwards e o tempo
das duas fases, com orçamento total comum de 24 forwards/120 segundos. Não é
remasking dentro da mesma trajetória, nem reprodução de TACG. Nenhuma posição
externamente protegida existe nessa tarefa.

A redução contrafactual de produção usa bônus B maior que a soma W dos pesos
originais para cada token alternativo na posição consultada. Um caminho recebe
no máximo um bônus; se existe alternativa, seu score aumentado é pelo menos B,
enquanto um caminho que mantém o token tem score no máximo W. Portanto o ótimo
da consulta discorda sempre que isso é viável. Recalcular seu score **sem** o
bônus fornece A_i. Se o ótimo mantém o token, ele é obrigatório no suporte.
Essa redução preserva todos os domínios e as regras EOS/PAD; não há poda nem
remoção implícita de tokens especiais. Propostas artificiais têm IDs próprios e
nunca entram no score ou selected IDs do problema original. Cada consulta passa
pelo validador independente existente. Um prazo cobre todas as consultas e
resultados tardios não geram commits. O guard numérico relativo é 1e-10.

O tempo total inclui a preparação por pedido e eventuais duas fases; carregamento
único do modelo é excluído. Componentes e latência sem preparação são reportados
separadamente. A auditoria BFCL mede primeiro cobertura dos tipos/esquemas; não
converter um catálogo de calculadora em benchmark real apenas renomeando funções.

## Decisão e utilidade

Investigar uma política que usa o MWPC existente para decidir **o que pode ser
fixado agora e o que deve esperar outra avaliação da dLLM**. O produto pretendido
é um decodificador de chamadas de ferramentas curtas: transformar um pedido em
uma chamada com nome, argumentos e tipos corretos, com menor tempo para uma
qualidade previamente definida. Exemplo de aplicação: consultar pedidos por
status e limite em uma API de leitura. Um formato válido que consulta o status
errado continua sendo erro; demonstrações usam um serviço local, sem ações reais.

A calculadora M22 é um diagnóstico do mecanismo, não comprovação de uso real.
A etapa externa deve usar chamadas públicas do BFCL, com avaliador oficial e
recorte documentado. Não iniciar treinamento, outro modelo, agentes multietapas,
SQL completo ou reparo geral de JSON neste mês.

M23 mostrou 65/100 chamadas corretas do MWPC contra 74/100 do EPIC lexical de
duas etapas com recuperação, com 205 contra 200 avaliações do modelo. Portanto,
"basta dar mais passos" não explica o resultado. Suporte, objetivo e política
também podem causar a diferença. A nova política é uma hipótese causal a testar,
não um diagnóstico já demonstrado. Fonte: [resultados M23](m23-findings.md).

## Mecanismo proposto

Seja F(y) a soma dos pesos das propostas atuais compatíveis com a conclusão y,
no suporte finito corrente. O MWPC calcula F* e uma testemunha y*. Para cada
proposta positiva selecionada na posição i, calcular:

```text
A_i = max F(y), sujeito a y_i != y*_i e às restrições originais
delta_i = F* - A_i
```

Uma alternativa inviável no suporte torna o token estruturalmente obrigatório.
Um TIMEOUT torna sua estabilidade desconhecida, nunca obrigatória. O limiar
epsilon é não negativo e tem unidades de pontuação, não de probabilidade.
Fixar apenas propostas selecionadas com `delta_i > epsilon`, ou obrigatórias.
Manter as outras posições mascaradas para outra avaliação da mesma dLLM.

**Propriedade:** todas as conclusões com `F(y) >= F* - epsilon` concordam nesses
tokens. Prova: uma conclusão que discordasse teria pontuação no máximo A_i,
estritamente menor que F* - epsilon. Assim, o lote inteiro preserva todas essas
conclusões, e é compatível com y*. A desigualdade é estrita: um empate no limiar
deve permanecer entre as alternativas. Essa propriedade elementar não será
apresentada como novo teorema de otimização.

Se nenhum token passar, fixar uma proposta selecionada pelo maior peso, com
desempate por posição; sem propostas positivas selecionadas, usar uma posição
livre da testemunha. Registrar esse progresso separadamente: ele **não** tem a
garantia de estabilidade. Não reescrever o conjunto selecionado pelo otimizador;
`selected_proposal_ids` e `committed_positions` têm significados diferentes.

Exemplo didático: duas conclusões têm pontuações 9 e 8; divergem numa operação,
mas concordam num delimitador. Com epsilon=1, a operação espera e o delimitador
pode ser fixado. Isso não demonstra que a primeira operação estava errada.

A referência em `src/mwpc_research/commit_stability.py` enumera caminhos completos
explícitos. Os testes comparam o filtro contra a interseção de todas as conclusões
quase ótimas, incluindo empates, posições fixas e fallback. **Não é o parser de
produção, não inclui a dLLM e não permite inferir o custo do método final.**

Na implementação de produção inicial, reutilizar o parser para cada consulta
contrafactual, removendo o token de um único domínio. Preservar bytes, slots,
EOS/PAD, propostas e suporte nas consultas restantes. Orçamento total inclui
todas as consultas. Inviabilidade e timeout continuam distintos. A comparação
de margens próximas do limiar deve ser conservadora quanto ao arredondamento
numérico, com tolerância registrada e testes específicos. Uma otimização por
inside/outside só entra se esse protótipo mostrar utilidade e custo justificável.

Riscos concretos: uma chamada errada pode vencer com margem alta; o suporte pode
excluir a resposta correta; vários tokens estáveis podem ser apenas EOS/PAD; e
as consultas adicionais podem custar mais que os forwards economizados. Medir
separadamente tokens ordinários e EOS/PAD. A propriedade não limita a mudança
das previsões na rodada seguinte e não certifica confiança semântica.

## Novidade: fronteira realista após pesquisa

| Fonte primária | O que já existe | Consequência para o TCC |
| --- | --- | --- |
| [Weighted CFG, Katsirelos et al.](https://gkatsi.github.io/papers/knwcpaior08.pdf) | Otimização sob CFG com pesos e domínios | Não reivindicar invenção do núcleo de otimização |
| [Structured Prediction Cascades](https://proceedings.mlr.press/v9/weiss10a.html) | Filtragem estruturada usando max-marginais | Margens estruturadas não são novas por si só |
| [EPIC](https://arxiv.org/html/2606.00722v1) | Decodificação restrita paralela | Comparação obrigatória com recuperação e configurações fortes |
| [Confidence-Based Decoding](https://arxiv.org/abs/2603.22248) | Orçamento adaptativo por entropia com análise teórica | Ajustar quantidade de tokens não basta como novidade |
| [TACG](https://arxiv.org/html/2607.03236v1) | Prontidão de compromisso usando histórico das previsões | Adiar compromisso também não basta |
| [Plan, Verify and Fill](https://arxiv.org/abs/2601.12247v3) | Âncoras estruturais e verificação para controlar geração | Não reivindicar primeira geração guiada pela estrutura |
| [Dang e Ermon](https://arxiv.org/html/2607.07026v1) | Posterior restrito por autômatos e marginais para selecionar posições | Concorrente conceitual próximo, além do EPIC |

O candidato a contribuição incremental é **usar margens contrafactuais do
objetivo MWPC, com CFG e certificado de slots/tokens, como política de compromisso
na dLLM, e demonstrar uma relação custo/qualidade melhor em tarefa útil**.
Não foi estabelecida exclusividade dessa combinação. Ausência de resultado de
busca não prova novidade. Dang e Ermon já usam confiança condicionada às
restrições; a distinção proposta é estabilidade do objetivo MWPC sob CFG, não
"usar gramática para obter confiança". Nosso catálogo finito também é regular;
não alegar vantagem de expressividade sobre autômatos apenas por escrevê-lo como CFG.

Consultas desta revisão: adaptive unmasking/confidence/grammar; constrained
diffusion max-marginal; grammar margin commitment; near-optimal structured
prediction. Foram conferidos os textos/arXiv oficiais de TACG e Dang/Ermon,
os resumos oficiais dos demais artigos recentes e a página PMLR. Esta revisão
é direcionada, não uma revisão sistemática exaustiva.

## Experimento que pode justificar utilidade

1. **Desenvolvimento:** apenas coortes já exploradas M22; usar um subconjunto
   fixado antes da nova execução. Limitar a busca a três tolerâncias relativas
   à soma dos pesos das propostas: 0, 0,02 e 0,10. O oráculo recebe epsilon
   absoluto; a conversão deverá ser registrada no driver. Escolher uma política
   antes da confirmação. Não escolher exemplos pelos ganhos observados.
2. **Ablações obrigatórias:** MWPC atual; MWPC com orçamento fixo pequeno;
   filtro por confiança local com mesmo máximo de commits; filtro por margem
   estrutural. Mesma formação de suporte e mesmas propostas entre essas variantes.
   Comparar seletores no mesmo estado/logits; trajetórias completas exigem novas
   inferências, não reaproveitamento fictício de logits de outra trajetória.
3. **EPIC completo:** lexical nativo em schedules 2, 4 e 24, incluindo recuperação
   oficial dentro do cronômetro da execução. Preservar seus defaults, saídas e
   falhas. Comparar a fronteira de configurações, não só a mais fraca. Acrescentar
   marginal restrita por autômato no catálogo pequeno como controle conceitual;
   chamar implementação própria de controle, não reprodução do artigo.
4. **Teste externo:** auditar BFCL single-turn antes de qualquer execução do modelo.
   Fixar revisão/licença, IDs, orçamento e regras de elegibilidade baseadas nos
   esquemas (uma chamada, argumentos escalares, sem execução externa). Separar
   desenvolvimento/teste por família de ferramenta. Publicar quantos casos são
   excluídos e por quê; não escolher pelo desempenho ou por conhecer o gabarito.
   Não reduzir campos livres aos valores corretos. Suporte construído somente
   de esquema, pedido e previsões; ausência da resposta no suporte conta como
   falha e deve ser diagnosticada depois. Não chamar recorte de score BFCL geral.
5. **Métricas:** correção de chamada/argumentos pelo avaliador, validade separada,
   latência total p50/p95, forwards, memória, custo das consultas adicionais,
   quantidade de commits estáveis e de progresso, estados do solver. Arquivar
   configs, revisões, sementes, hashes e saídas antes de gerar tabelas.

O [BFCL oficial](https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard)
oferece o caminho para avaliação externa; sua cobertura no suporte deste projeto
ainda precisa ser auditada. Não há subconjunto externo já preparado neste plano.

**Meta de engenharia, não resultado previsto:** reduzir latência em pelo menos
20% preservando qualidade, ou melhorar qualidade sob um mesmo limite de tempo.
Antes de abrir o teste, fixar a comparação primária, o limite de tempo, a margem
de não inferioridade e o tamanho amostral conforme o piloto. Uma amostra de cem
pedidos não estabelece automaticamente não inferioridade de dois pontos
percentuais. Usar diferenças pareadas e intervalos; repetições de tempo não
contam como novos pedidos. Resultados inconclusivos continuam inconclusivos.

## Um mês, com decisão na primeira semana

| Prazo | Entrega e critério |
| --- | --- |
| Dias 1–3 | Referência, contrato, integração contrafactual e testes contra oráculo; nenhum benchmark de desempenho antes de passar |
| Dias 4–7 | Piloto LLaDA + EPIC completo + controles; auditoria de cobertura BFCL; medir se o custo das margens compensa |
| Dias 8–14 | Se houver sinal, congelar política e protocolo externo, implementar avaliador e executar confirmação |
| Dias 15–21 | Repetir tempos, ablações, intervalos e análise de erros; demonstração local de consulta de API |
| Dias 22–30 | Artigo, gráficos reproduzíveis, limitações e apresentação; nenhum novo mecanismo nesta fase |

**Regra de parada:** se até o dia 7 o método não mostrar melhora frente ao
controle simples de confiança/orçamento, não gastar a semana 2 otimizando-o em
Rust nem prometer superioridade. Fechar essa hipótese e entregar a integração
útil com a melhor política validada, delimitando a contribuição experimental.
O plano maximiza a chance de um resultado útil; não torna um resultado positivo
garantido nem autoriza trocar o teste depois de vê-lo.
