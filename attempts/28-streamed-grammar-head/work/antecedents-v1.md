# Fontes primárias e eliminação de falsas novidades —2026-10-11

| Fonte | Alcance e objeção para esta direção |
| --- | --- |
| [FlashSampling,2026, §4.1–4.4](https://arxiv.org/html/2603.15854v1) | Projeção/amostragem sem logits materializados, massas e sorteios internos de grupos, inclusive online/distribuído. O princípio do resumo e o ganho sobre uma tabela densa são antecedentes. A28 troca a seleção independente de grupos por inferência conjunta de uma CFG; a suficiência dessa troca é consequência direta, não um novo princípio estatístico. |
| [STATIC, versão3 de07/10/2026](https://arxiv.org/abs/2602.22647v3), [RecTokens](https://pypi.org/project/rectokens/) | Restrição vetorizada para retrieval, CSR e fusão da projeção com masking/amostragem. Não reivindicar fusão ou transições esparsas como novidade. A aplicação deles tem trie de itens, diferente de uma distribuição conjunta recursiva, mas a diferença de domínio sozinha é insuficiente. |
| [Grammar-sparse-projection, descrição do autor](https://github.com/StealthEyeLLC/grammar-sparse-projection) | Antecedente descoberto na busca: skip de projeção com máscara gramatical, controle denso/adaptativo e batching. A página primária não foi recuperada nesta sessão; o índice de busca retornou a descrição. Não usar seu desempenho ou detalhes não conferidos como evidência. A ideia simples de projeção esparsa foi retirada antes de implementação. |
| [FactorDLM, §3–5](https://arxiv.org/html/2609.32900v1) | Inferência compilada com pesos/fatores atualizados já existe. Precisa de uma boa representação e a mesma cabeça em fluxo como controle, quando a tarefa for compatível. Não atribuir uma vantagem ao parser só porque o comparador guarda logits. |

## Direção de gradientes examinada antes desta implementação

[Diffinity, §3.3](https://arxiv.org/html/2602.12468v1) calcula a probabilidade
de aceitação regular e sua orientação analítica; o uso dessa probabilidade
como h da trajetória é uma aproximação explícita. A ideia de usar inside/
outside para CFG é um candidato de extensão, não prioridade confirmada.
[Dierckx/Dubray/Nijssen, IJCAI2025](https://www.ijcai.org/proceedings/2025/0558.pdf)
já limita erros de gradientes usando circuitos inferiores/superiores, e
[Guo/Tang/Xu,2026](https://arxiv.org/html/2602.05533v1) já relaciona erros de
orientação a distâncias da distribuição final. Além disso, passar um limite
de logits para o espaço latente precisa de um Jacobiano certificado: uma
estimativa barata de norma pode ser somente um limite inferior. Sem resolver
esse custo, não implementar uma grande orientação neural nem alegar um novo
teorema genérico de certificação de difusão.

## Gate científico

Há uma consequência de memória bem definida e uma operação conjunta distinta
da amostragem independente. Ainda não há novidade suficiente ou superioridade
sobre o melhor streaming. O próximo protótipo deve materializar a lei sem
guardar pesos originais; qualquer GPU posterior depende de uma justificativa
de benefício frente a esses antecedentes e de um protocolo congelado.
