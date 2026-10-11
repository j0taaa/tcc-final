# Revisão dirigida, antes de ampliar o protótipo

Consulta a fontes primárias em 2026-10-10/11. Ausência em buscas não prova
prioridade. Fontes e objeções são preservadas mesmo quando descartam uma ideia.

| Antecedente | Conteúdo relevante | Consequência para esta pesquisa |
| --- | --- | --- |
| [EPIC, v2, §§4.1–4.4](https://arxiv.org/html/2606.00722v2) | Memoização lexical, regular cover, validação exata sobre ENFA e recuperação por testemunho. | Não chamar cache, Earley sem DFA ou dividir lotes de novidade. A18 já estudou seletores equivalentes no suporte finito. O texto que menciona busca exponencial não prova que toda otimização ponderada exige esse custo. |
| [FactorDLM, §§3–5 e apêndice E](https://arxiv.org/html/2609.32900v1) | Eliminação exata em fatores, plano reutilizável, sintaxe e relações; custos governados pela largura. | Circuito, reponderação, relações e reutilização não são novidades genéricas. Não comparar com uma codificação ruim por fatores. |
| [Twister, §3 e §6](https://arxiv.org/html/2609.35609v1) | Condicionamento local do produto não preserva a lei da trajetória nativa; correção SMC por razões de massas. | Este diagnóstico só trata o produto de um passo. Não reivindicar trajetória nativa exata por aplicar o solver repetidamente. |
| [Future Validity, §3–4](https://arxiv.org/html/2605.07698v1) | Doob transform, limitações da projeção local e correção aproximada da massa futura em geração AR/especulativa. | Futura massa e controle TV já são antecedentes; trocar o modelo por dLLM não os inventa. |
| [Amarilli et al., STACS 2026, introdução e §2](https://drops.dagstuhl.de/storage/00lipics/lipics-vol364-stacs2026/html/LIPIcs.STACS.2026.5/LIPIcs.STACS.2026.5.html) | Massa de palavras probabilísticas é tratável para GLCs não ambíguas; sampling/ranking por auto-redução; ambiguidade pode tornar contagem difícil. | Posterior CFG e unranking não são a nova contribuição. |
| [Bertoni, Goldwurm, Santini, 2001](https://www.numdam.org/item/ITA_2001__35_6_499_0/) | Geração de palavras em linguagens de ambiguidade limitada, com técnica de correção da multiplicidade. | Rejeição inversa pelo número de parses não é um caminho novo. Descartado como protagonista antes de implementá-lo. |
| [Czerwiński e Lasota, LMCS 2019, §3](https://lmcs.episciences.org/5563/pdf) | Aproximação regular de one-counter: altura exata abaixo de n e resíduo módulo n acima, com mudanças de modo. | Antecedente muito próximo da proposta modular. A nova aplicação ponderada e a passagem determinística depois de primeiro overflow precisam ter consequência própria; não basta rebatizar essa abstração. |
| [OS*, 2012, §§2–3](https://aclanthology.org/W12-6106.pdf) | Propostas superiores, rejeição e refinamento, inclusive gramáticas probabilísticas. | Envelope exato é princípio conhecido; A25 já aplicou e perdeu o gate de primeira amostra. |
| [Moulos e Anantharam, 2019](https://arxiv.org/abs/1907.04467) | Limites Chernoff para funcionais de cadeias finitas. | Potenciais e transformadas de soma de incrementos não são uma nova desigualdade. A recorrência aqui permite pesos por slot e bytes de tokenizer; essa especialização, sozinha, pode ser pequena demais. |

## Decisão provisória

Não implementar outro decoder amplo agora. Um protótipo de limites finitos
serve para rejeitar cedo uma redução inviável ou frouxa. Só uma combinação de
diferença específica, resultado de custo relevante e aplicação competitiva
permitirá promovê-lo. Nada desta revisão confirma aceitação ou revisão humana.
