# Antecedentes conferidos em 2026-10-10

| Fonte primária | O que já é conhecido; diferença e objeção para A26 |
| --- | --- |
| [Kondratovich e Zhigljavsky, *Comparison of independent and stratified sampling schemes in problems of global optimization*, §2, teorema1](https://ssa.cf.ac.uk/zhigljavsky/pdfs/GO/GO%20comparison%20of%20samples.pdf) | Dominância do máximo sob estratificação proporcional já foi demonstrada; a desigualdade local de A26 é uma especialização, não um novo princípio estatístico. |
| [Vilnis et al., Arithmetic Sampling, ICML2023, §§4.2–4.4, proposições7–8](https://proceedings.mlr.press/v202/vilnis23a/vilnis23a.pdf) | Código aritmético para geração paralela e marginais preservadas; análise de variância exige condições sobre intervalos. A26 usa jitter independente, evitando a fase comum que pode piorar um verificador periódico. Isso reutiliza estratificação clássica. |
| [Sato, DAST,2026, §2, teorema2.1](https://arxiv.org/html/2609.33038v1) | Reordenação semântica dos tokens e fase comum; garantia de atingir uma sequência quando K≥1/P(y). A26 não possui essa garantia de cobertura determinística e não reivindica vencer DAST. Propõe dominância para qualquer conjunto aceitável, outra propriedade. |
| [Roohi et al., STMC, CAV2020, §2, teoremas1–2](https://pmc.ncbi.nlm.nih.gov/articles/PMC7363213/) | Estratificação de trajetórias Markov e verificação probabilística já existem. A não correlação de certas propriedades requer forma específica de fórmula. Conferimos o texto primário disponibilizado pelo editor/PMC; o primeiro open encontrou proteção de acesso, mas a pesquisa retornou o texto completo. Não concluir prioridade apenas porque um enunciado usa dLLMs. |
| [Li et al., Stratification and Optimal Resampling for Sequential Monte Carlo,2020](https://arxiv.org/abs/2004.01975) | Crescimento com múltiplos descendentes e resampling estratificado são antecedentes próximos. A26 conserva K rótulos sem seleção por peso/recompensa e separa históricos; não reivindica introduzir crescimento estratificado ou inferência por partículas. |
| [Fakhereddine et al., Stratified Monte Carlo simulation of Markov chains,2017](https://arxiv.org/abs/1603.06386) | Simulação paralela de cadeias estratificadas é conhecida. O texto discute as dificuldades de independência e deixa a análise geral de cadeias como investigação. A prova por histórico completo de A26 evita juntar estados com leis futuras diferentes. |
| [Lamont et al., ODD,2026, §§2.2–2.3](https://arxiv.org/html/2603.04893v1) | Já trata pass@K em dLLMs com repulsão nos logits. Não preserva a mesma lei individual por construção; o ganho é experimental. A26 preserva o kernel e demonstra dominância sobre iid desse kernel, sem comparar a pontuação empírica com ODD. |
| [Ponty, Non-redundant random generation algorithms for weighted CFGs,2013](https://doi.org/10.1016/j.tcs.2013.01.006) | Geração ponderada por unranking e sem redundância em GLCs é conhecida. O adapter de A26 não é uma nova teoria de ranking gramatical. Sampling sem reposição continua alternativa competente com outro contrato marginal. |

## Decisão de novidade

A superioridade sobre iid tem uma prova geral, porém seus fundamentos são
clássicos. A26 NÃO deve ser apresentada como descoberta de estratificação,
de programação dinâmica, de unranking ou de diversidade em dLLMs. O algoritmo
de tokens originais, a auditoria inteira dos estratos e a garantia para
históricos adaptativos constituem um recorte operacional a examinar. Não há
prioridade, suficiência de publicação ou revisão humana confirmada.

Uma contribuição útil e comprovada em resultado pode existir sem ser um
princípio matemático novo. Isso precisa permanecer separado da avaliação de
significância científica, em vez de chamar uma adaptação de invenção.
