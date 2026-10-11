# Revisão direcionada — A29,2026-10-11

| Fonte primária conferida | Resultado conhecido e obrigação restante |
| --- | --- |
| [Neal, Modifying Gibbs Sampling to Avoid Self Transitions,2024, §5/equação19 e §6](https://glizen.com/radfordneal/ftp/gibbs-self.pdf) | Transferências de massa entre grupos preservam o alvo e melhoram a eficiência por matrizes de diferença semidefinidas. Logo PSD/anticorrelação e remover self-transitions não são novidades. A29 deve ser comparada como algoritmo implícito, não como invenção desse princípio. |
| [Dimitriev e Zhou, CARMS, NeurIPS2021, teoremas1–2/§3.2](https://proceedings.neurips.cc/paper/2021/file/6e16656a6ee1de7232164767ccfa7920-Paper.pdf) | Acoplamentos categóricos, importance correction e benefício quando toda probabilidade fora da diagonal aumenta já são conhecidos. A29 satisfaz essa condição na lei homogênea, mas não deve reivindicar o teorema de gradientes. CARMS não pode ser descartado sem comparar suas construções de copula. |
| [Ren, Zhao e Ermon, Adaptive Antithetic Sampling, ICML2019, teorema1](https://proceedings.mlr.press/v97/ren19b/ren19b.pdf) | Para uniforme, nenhum acoplamento garante grande redução de variância para todas as funções; sem reposição é minimax. A29 também tem melhora universal pequena nesse regime. O enunciado uniforme é o que usamos; amostragem ponderada sem reposição geralmente altera marginais posteriores. |
| [Vilnis et al., Arithmetic Sampling, ICML2023, §§4.2–4.4](https://proceedings.mlr.press/v202/vilnis23a/vilnis23a.pdf) | Código aritmético e fase comum preservam marginais; garantias de variância possuem hipóteses sobre os intervalos. Não presumir que uma fase comum é inferior na prática; pode diversificar mais que uma intervenção em colisões. |
| [Sato, DAST,2026, §2/teorema2.1](https://arxiv.org/html/2609.33038v1) | Ordenação semântica e pontos espaçados garantem atingir uma palavra quando K é suficientemente grande. A29 não possui essa cobertura determinística; seu contrato de qualquer evento com K=2 é distinto, ainda sem prioridade delimitada. |
| [Roohi et al., STMC,CAV2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7363213/) | Trajetórias estratificadas/antitéticas e verificação probabilística são antecedentes diretos da extensão adaptativa. A prova de históricos completos reutiliza a ideia de dominância local; mudar o contexto para dLLM não demonstra novidade. |
| [Ponty, Non-redundant Random Generation Algorithms for Weighted CFGs,2013](https://doi.org/10.1016/j.tcs.2013.01.006) | Gerar palavras ponderadas sem redundância por unranking é alternativa competente, com contrato marginal distinto em geral. Não esconder este comparador nem atribuir ranking ponderado a A29. |
| [EPIC,v2](https://arxiv.org/html/2606.00722v2), [FactorDLM,Proposição2](https://arxiv.org/html/2609.32900v1), [ODD](https://arxiv.org/html/2603.04893v1) | Geração paralela gramatical, posterior exato com classes e repulsão para pass@K já existem. A29 não substitui estes métodos: precisa demonstrar qual operação adiciona, custo e vantagem frente a controles igualmente fortes. |

Metropolis–Hastings e a forma de Dirichlet são usados como antecedentes, não
registrados como invenções. A pesquisa até aqui não localizou o mesmo
transformador normalização-independente de leis P/Q ativado só em colisões;
**isso não prova ausência na literatura**. Ainda falta conferir acoplamentos
de leis diferentes, antithetic kernels e construções por fluxos implícitos.

A via de hash/partições aleatórias foi examinada antes de código: embora
formas semidefinidas deem não deterioração, o teorema de2019 impede alegar
ganho universal grande em espaços uniformes amplos. Não criamos um benchmark
de duas respostas equiprováveis para converter a desigualdade em utilidade.
