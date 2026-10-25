# Complemento da busca durante a execução, sem alteração do piloto

23/10/2026. Fontes primárias adicionais, localizadas seguindo referências de CADOC.
Nenhum seletor, gate, caso, orçamento ou métrica mudou em resposta à busca.

[Self-GC](https://arxiv.org/html/2607.00692v1), seção The Self-GC Framework,
Reflective Planning/Rehearsal/Commit e Recoverability/Cache-Aware Commit:
objetos indexados, planner lateral propondo fold/mask/prune, ensaio local,
recuperação por sidecars, dependências futuras e atraso de commit quando a quebra
do cache supera a economia esperada. Há framework implementado e avaliações
reportadas, não somente sugestão. Essa fonte primária reforça que a decisão
semântica de edição e a penalidade de cache já convivem em trabalhos anteriores.
Não é um editor dLLM com a interface e fidelidade A90; isso não basta para tornar
original a troca do backbone por difusão.

[TokenPilot](https://arxiv.org/html/2606.17016v1), §§2–3 e §4: objetivo de utilidade
por custo com tokens hit/miss, estabilização do prefixo na ingestão e evicção local
conservadora por estimativa de utilidade residual. Declara integração em LightMem2
e avalia modos isolado/contínuo; não é só oportunidade futura. Seu modelo de custo
é monetário e o mecanismo principal não é atualização factual por difusão, mas a
colisão com a motivação/política de granularidade e preservação de cache é direta.
Não adotamos seus percentuais como evidência local.

[TimeROME-DLM](https://arxiv.org/abs/2606.12841), título/resumo consultados:
intervenção residual de baixo rank em coordenadas internas de MDLMs, com tracing
temporal. Apesar do nome knowledge editing e memória de edições, não é memória
textual compacta repassada a um consumidor AR. Não classificamos como subsunção
completa da hipótese nem alegamos ter auditado seus resultados experimentais.

A primeira busca não ter retornado um artigo idêntico continuaria insuficiente
para reivindicar novidade. Após estes antecedentes, a fronteira de originalidade
fica ainda mais estreita: seria necessário formular uma operação/política própria
e demonstrar necessidade ou vantagem específica além da interface AR equivalente.
A V1 não fornece tal operação nova por construção.
