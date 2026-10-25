# Busca adicional durante a execução, sem mudar políticas ou tarefas

23/10/2026, depois de congelar V1. Novas fontes primárias próximas:

| Trabalho | Implementado/publicado | Diferença ainda necessária |
| --- | --- | --- |
| [SWYB, 28/08/2026](https://arxiv.org/html/2608.28229), §§3–4 | Configurações de PDA conscientes do tokenizer, resumos limitados de pilha, alcance e distâncias em tokens até aceitação, poda por orçamento e beam search; código público. Distâncias podem ser limites superiores conservadores. | Opera sobre prefixos AR. Não foi localizado ali um alocador exato de múltiplas lacunas com compromissos fora de ordem e inserção no canvas dLLM. Só trocar AR por dLLM não comprova contribuição. |
| [TruncProof, v3 24/06/2026](https://arxiv.org/html/2605.13076), §IV | Lexer/parser LL(1) incremental e custos futuros em tokens com cache para concluir JSON sob limite; código público. Não garante semântica. | Contagem aproximada para prefixos, não decisões exatas conjuntas entre lacunas. Não reivindicar “tokens reais + comprimento + gramática” como invenção. |
| [Quimper–Walsh, 2009](https://arxiv.org/html/0903.0470), §§4–6 | Propagação incremental de Regular/Grammar constraints; estados em cadeia e extensões soft por distância de edição, com antecedentes ainda anteriores. | O grafo de inserção de A89 é uma especialização clássica desse tipo de otimização, não um novo algoritmo de inferência finita. |
| [Opedal et al., 2023](https://aclanthology.org/2023.acl-long.204/) | Parsing Earley em semirings e melhorias de custo. | Mudar pesos para custos min-plus não cria sozinho uma contribuição nova. |

Consultas adicionais: `grammar constrained decoding minimum token completion length tokenizer`,
`diffusion grammar length budget masks expansion`,
`Quimper Walsh 2009 grammar constraints lengths incremental`,
`context free grammar edit distance insertion error correcting parser Aho Peterson`.

A proposta específica exigiria uma representação de capacidade conjunta de
lacunas tokenizadas que evite o custo da construção explícita e supere controles
incrementais fortes. Nenhuma prova de complexidade nova ou algoritmo geral desse
tipo foi obtido nesta tentativa. A redução especializada de arrays a profundidade
tem baixo custo justamente porque uma pilha de um único tipo não exige guardar
sequências de símbolos diferentes. Isso não transfere automaticamente a SQL/C++.

Mündler et al. já sugerem expansão e documentam o custo de token counts; DAEDAL e
DreamOn já modificam canvas; Gram2Token já faz gramática na GPU; FactorDLM cobre
a codificação finita em cadeia e a inferência CPU/CUDA equivalente. A contribuição
não pode ser vendida como a soma desses elementos. A busca não prova prioridade
nem subsunção total por um único artigo; estabelece colisões suficientes para
rejeitar a alegação ampla de originalidade.
