# M24 — O que compensa na prática

A recomendação é **manter o MWPC com políticas simples de compromisso e encerrar
as margens contrafactuais como aposta principal para este TCC**. A campanha
identificou vantagens mensuráveis em configurações específicas com uma dLLM real,
mas não um vencedor universal. Para catálogos externos pequenos, a enumeração MAP
foi melhor que o parser geral. Isso deve orientar o escopo, não ser omitido.

## Evidência produzida

Foram 3.856 gerações finais, 26 configurações e 138 pedidos distintos: 30 de
desenvolvimento, 100 novos pedidos de confirmação e oito casos externos. O smoke
reutiliza dois pedidos do desenvolvimento. As repetições de tempo não aumentam o
número de pedidos independentes. O controle de revisão abre um segundo canvas e
contabiliza suas inferências no mesmo orçamento: foram 48 canvases adicionais
e 24.404 avaliações do modelo no total. Todos os 3.856 registros finais têm
estado `complete`; isso não significa que todas as respostas sejam válidas ou
corretas, como mostram as tabelas.

Modelo: LLaDA-8B-Instruct, revisão `08b83a6feb34df1a6011b80c3c00c7563e963b07`,
NF4 com double quantization e cálculo bfloat16, RTX 3080 Ti, um thread de CPU.
Todas as configurações foram versionadas antes de suas execuções. A seleção
primária foi congelada após desenvolvimento; controles adicionais são análises
secundárias, explicitamente identificadas. O EPIC é o upstream fixado com sua
recuperação oficial dentro do tempo total. Não é o seletor guloso próprio.

Fontes regeneráveis:

- [Inventário, commits produtores e comandos](generated/m24-campaign-inventory.json);
- [Todos os métodos no desenvolvimento](generated/m24-development-results.md);
- [Confirmação pareada completa](generated/m24-confirmation-paired-results.md);
- [Piloto externo pareado completo](generated/m24-external-paired-results.md);
- [Sensibilidade à formatação](generated/m24-whitespace-sensitivity.json);
- [Protocolo histórico e fronteiras de novidade](m24-stable-commit-plan.md);
- [Reprodução e auditoria](m24-reproduction.md).

## Escolha para chamadas compostas

**MWPC com confiança 0,8 é a opção de equilíbrio mais interessante neste conjunto.**
Acertou 87/100 chamadas nas duas rodadas, com mediana total de aproximadamente
1,11 s. O EPIC de 24 etapas acertou 89/100 em aproximadamente 2,38 s. A razão
pareada mediana de velocidade foi 2,19, com intervalo bootstrap de 95% de
aproximadamente 2,11–2,24. Em resultado numérico, foram 98/100 contra 99/100.
O limiar 0,8 usa probabilidade de token no vocabulário completo; não significa
80% de probabilidade de atender corretamente ao usuário.

**O critério primário completo não foi atingido.** A redução de latência excedeu
20%, mas a amostra não demonstrou perda inferior a dois pontos percentuais de
acurácia. Houve duas vitórias e quatro derrotas pareadas contra EPIC 24;
o intervalo conservador de 95% para a diferença é aproximadamente
[-10,71; +6,99] pontos percentuais. Ausência de diferença estatisticamente
significativa não estabelece equivalência. O bootstrap da diferença também
permanece inconclusivo. Não chamar esse resultado de não inferioridade comprovada.

**Orçamento de quatro propostas é uma opção mais rápida quando a métrica principal
é seguir exatamente a estrutura da chamada.** Obteve 86/100, aproximadamente
0,93 s e 682 inferências por rodada, contra 74/100, aproximadamente 0,97 s e 772
inferências do EPIC de oito etapas. São custos semelhantes com mais acertos
observados; não confundir quatro propostas com quatro inferências. Entretanto,
o resultado numérico do orçamento quatro foi 90/100, abaixo dos 98/100 do filtro
0,8. Esse segundo indicador é uma razão para preferir 0,8 como opção equilibrada.

Há uma diferença de formatação relevante: EPIC permite espaços/quebras entre
lexemas que o avaliador Python pode rejeitar. Uma análise posterior que preserva
os tokens e strings, mas normaliza espaços, eleva EPIC 8 para 78/100, ainda abaixo
de 86/100. EPIC 6 sobe de 77 para 79; EPIC 12, de 72 para 77. As pontuações
primárias não foram reescritas. Não apresentar toda a diferença bruta como erro
de escolha semântica do EPIC, nem essa normalização posterior como parte do
protocolo primário. Ela não faz nova inferência, mas seu custo não foi cronometrado
no pipeline original.

Para latência menor, confiança 0,2 obteve 74/100 e aproximadamente 0,43 s, enquanto
EPIC 4 obteve 74/100 e 75/100 em aproximadamente 0,63 s. A variação do EPIC vem de
recuperações que podem diferir entre processos. O MWPC sem controle adicional
(`exact_b24`) fez 54/100 em aproximadamente 0,28 s: comprometer mais posições cedo
produz uma saída rápida, mas a qualidade caiu bastante neste conjunto.

## O que as ablações mostram

O guloso com o mesmo suporte e filtro 0,8 teve a maior acurácia observada:
91/100, resultado numérico 100/100 e aproximadamente 2,28 s. O exato com esse
filtro foi muito mais rápido, mas perdeu quatro acertos. Com limiar 0,2, o exato
fez 74/100 em aproximadamente 0,43 s, e o guloso 73/100 em aproximadamente 0,79 s.
Logo, exatidão do objetivo de seleção não implica maior acurácia final. O ganho
prático do seletor exato é principalmente de custo nessas comparações.

As margens não compensaram a complexidade medida: no desenvolvimento, margem
relativa 0,1 obteve 27/30 em aproximadamente 0,98 s; confiança 0,8 obteve 28/30 em
aproximadamente 0,94 s. As margens fizeram menos inferências, mas pagaram por
muitas consultas adicionais ao parser, inclusive em posições EOS/PAD. No piloto
externo, ficaram entre cinco e seis acertos de oito e foram mais lentas que
alternativas simples. Isso rejeita priorizar **esta implementação e estas
políticas testadas**, não prova impossibilidade de uma implementação conjunta
de max-marginais mais eficiente.

Revisar o rascunho com a mesma dLLM, aceitar duas/três propostas por posição e
MAP de compromisso amplo também não foram vencedores gerais. MAP com 24 commits
foi extremamente rápido nas calculadoras, mas acertou apenas 58/100; três
propostas fizeram 59/100. A tabela de desenvolvimento preserva todos os resultados,
incluindo margens, revisão, orçamentos e variantes não selecionadas.

O diagnóstico independente dos 11 erros do MWPC original no desenvolvimento
mostrou que o gabarito estava no suporte inicial em todos eles. No primeiro passo
que o excluiu, o objetivo MWPC favorecia uma conclusão errada. O parser pode
resolver exatamente um objetivo que não representa toda a intenção do usuário.
Isso motiva separar otimização e decisão de compromisso; o diagnóstico sozinho
não prova que adiar um token particular causará uma resposta correta.

## Uso externo: catálogo pequeno favorece a solução simples

A auditoria congelada encontrou oito casos elegíveis entre 658 exemplos BFCL
(aproximadamente 1,2%). Eles envolvem quatro nomes de função, quatro pedidos da
mesma função de comida e uma chamada sem argumentos. O suporte vem somente dos
esquemas, sem preencher campos com valores do gabarito. Não são oito famílias
independentes nem uma avaliação geral de chamadas de API.

Nesse recorte, o controle MAP com orçamento 24 acertou os oito casos em ambas as
rodadas e levou aproximadamente 0,26 s; MWPC b24 também acertou oito, em cerca de
0,35 s. O EPIC 4 fez sete sob avaliação estrita, ou oito após normalizar espaços,
em cerca de 0,82 s. O EPIC 24 fez sete, em cerca de 2,39 s. O limiar 0,8 não ajudou
aqui: manteve oito acertos, mas exigiu muito mais inferências.

**Para esse caso de uso, escolheria MAP enumerativo.** Não há justificativa
experimental para exigir o solver geral quando todas as alternativas já cabem
num catálogo pequeno. `catalog_map24` usa 24 commits por passo: no canvas externo
de 32 slots ele faz duas inferências, não uma. Não medimos MAP com 32 commits.
Seu suporte é mais estreito, restrito às tokenizações canônicas enumeradas;
não é uma reprodução do parser nem de um artigo sobre posterior condicionado.

O avaliador externo é próprio, baseado em AST escalar e nas respostas aceitáveis
públicas; não é o score oficial BFCL. Nenhuma API externa foi executada. Todos os
casos, erros e recuperações foram preservados, inclusive a queda de EPIC 2 entre
repetições. O piloto demonstra integração com esquemas externos e ajuda a escolher
uma ferramenta para esse recorte; não estabelece superioridade populacional.

## Contribuição defensável e prioridade para o mês restante

A contribuição que os resultados sustentam é a **integração certificada de seleção
paralela exata em dLLMs, com avaliação de como a política de compromisso altera
custo e qualidade**, incluindo comparação real com EPIC e controles fortes.
Há vantagens observadas em configurações delimitadas; não há garantia de
melhora semântica global. Pesos, suporte, slots e estados do solver continuam
explícitos. Não chamar filtros de confiança ou max-marginais de invenções novas:
os antecedentes estão no protocolo. Esta campanha não estabelece prioridade
mundial da combinação nem reproduz todos os decodificadores recentes.

Eu priorizaria, nesta ordem:

1. Consolidar confiança 0,8, orçamento quatro e as opções EPIC/gulosa como escolhas
   configuráveis. Manter MAP para catálogos pequenos. Não adicionar mais margens
   nem ajustar limiares ao conjunto de confirmação já visto.
2. Dedicar o próximo experimento a chamadas com argumentos que não sejam apenas
   enums, preservando construção de suporte sem gabarito e medindo sua cobertura.
   Separar novas famílias de ferramentas antes de testar. A principal lacuna
   prática agora é cobertura externa; não mais a falta de variantes na calculadora.
3. Usar o restante do prazo para uma demonstração de consulta somente de leitura,
   resultados reproduzíveis e artigo/apresentação que incluam as comparações
   positivas, negativas e inconclusivas. Não condicionar a conclusão a derrotar
   todos os concorrentes nem prometer um ganho que ainda não foi medido.

O artigo/PDF preservado continua sendo a versão histórica M21; esta campanha
atualiza código, evidências e relatório científico. A confirmação externa ampla,
a demonstração e a atualização do manuscrito de T2404 permanecem pendentes.

## Limites de medição e verificação

Os cem pedidos novos ainda usam as mesmas famílias sintéticas do desenvolvimento.
Não há segundo modelo, segunda GPU, ferramentas com campos livres ou aplicações
remotas nesta campanha. Os intervalos secundários não têm ajuste de multiplicidade.
Tempos incluem preparação e recuperação, excluindo carregar o modelo; CUDA foi
sincronizada e os experimentos rodaram sem testes pesados concorrentes. O pico
de memória é alocação GPU incluindo o modelo; pico de RAM da CPU não foi medido.

Nos primeiros artefatos, o rótulo geral de suporte do guloso mencionava o parser
exato. Os estados internos sempre registraram `feasible_on_support`, sem garantia
de seleção ótima. O driver agora explicita essa diferença também no rótulo geral;
os registros históricos permanecem intactos. O validador confere o estado correto.

A verificação completa, com comandos e resultados, fica em
[`m24-policy-verification.json`](../evidence/m24-policy-verification.json).
