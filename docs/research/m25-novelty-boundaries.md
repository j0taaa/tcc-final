# Delimitação da contribuição após a revisão de literatura

Revisão ampliada em 30 de setembro de 2026. Uma busca bibliográfica não prova
ausência de trabalhos equivalentes. O artigo deve apresentar a contribuição
incremental que o código e os resultados sustentam, sem reivindicar prioridade
geral para inferência exata, programação dinâmica ou compromisso por confiança.

## Antecedentes mais próximos

| Trabalho primário | Relação com este projeto | Limite da comparação |
|---|---|---|
| [Weighted CFG Constraint, 2008](https://gkatsi.github.io/papers/knwcpaior08.pdf) | Otimização gramatical ponderada e restrições suaves de distância já existem. | Não trata a integração de propostas de uma dLLM com proveniência de tokens e slots físicos deste projeto. |
| [Structured Prediction Cascades, 2010](https://proceedings.mlr.press/v9/weiss10a.html) | Filtragem estruturada por max-marginais é anterior às dLLMs. | Os testes de margens deste projeto não inventam essa ideia e não justificaram seu custo como extensão principal. |
| [DINGO](https://proceedings.neurips.cc/paper_files/paper/2025/hash/eb17a2030d1bd4a1bd29531bcd626705-Abstract-Conference.html) | Inferência restrita por linguagens regulares é um antecedente. | MAP enumerativo é um controle de catálogo, não uma reprodução completa do decoder. |
| [EPIC](https://arxiv.org/abs/2606.00722) | Seleção paralela heurística com verificação CFG; baseline executado a partir do código original. | Vocabulário nativo, espaços lexicais e recuperação diferem do suporte finito MWPC. Comparação do sistema não isola somente o algoritmo de seleção. |
| [Dang e Ermon](https://arxiv.org/abs/2607.07026) | Inferência exata da distribuição mean-field condicionada por autômatos. | Probabilidade conjunta e concordância ponderada com propostas são objetivos diferentes. |
| [CLAD](https://arxiv.org/abs/2605.29607) | Seleção ponderada exata em decodificação paralela já é estudada. | Conflitos derivados de clusters de atenção não equivalem a existência de conclusão CFG. |
| [Decodificação por confiança](https://arxiv.org/abs/2603.22248v1) | O controle de compromisso por confiança tem antecedentes teóricos. | Nosso limiar fixo não reproduz a análise de amostragem desse trabalho. |
| [TACG](https://arxiv.org/abs/2607.03236v1) | Separar identidade do token e momento de compromisso é anterior a este estudo. | Nosso gate simples não implementa o histórico de previsões do TACG. |
| [FactorDLM](https://arxiv.org/abs/2609.32900v1) | Preprint de 26/09/2026: inferência exata com grafos de fatores e restrições relacionais. | Não é um baseline implementado aqui. Não reivindicar novidade geral em inferência exata de dLLMs ou vantagem para restrições relacionais. |

## O que o TCC entrega

A implementação liga uma formulação de concordância ponderada por passo a um
parser CFG em Python e Rust, com implementações independentes, slots finitos,
bytes composicionais do tokenizer, EOS/PAD e certificados conferidos fora do
parser. A política que decide quanto comprometer fica separada do conjunto
ótimo: seu efeito sobre a trajetória é uma questão experimental.

O estudo mede essa integração com uma dLLM real, EPIC original com recuperação,
guloso sob suporte compartilhado e controles MAP enumerativos. Ele preserva
as falhas, estabelece um benefício limitado nas chamadas sintéticas e investiga
onde a estrutura certificada custa mais do que alternativas simples. Os
resultados externos devem ser reportados integralmente, sem trocar o comparador
primário após observar a confirmação.

Essa combinação sustenta uma contribuição de implementação verificável e
avaliação empírica. Não sustenta afirmar um novo algoritmo geral de parsing,
superioridade universal, novidade de confiança ou necessidade de uma dLLM para
uma consulta geográfica. A demonstração apenas torna concreto o fluxo de gerar,
validar e despachar uma chamada de leitura.

Referências completas e auditoria de metadados:
`paper/referencias.bib` e `docs/evidence/submission-bibliography-verification.md`.
