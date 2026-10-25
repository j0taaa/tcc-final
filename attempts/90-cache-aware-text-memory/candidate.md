# Mecanismo realmente implementado e reivindicação permitida

O piloto implementa uma política compartilhada, simples e sem treino: identificar
blocos lexicalmente afetados, fechar dependências lexicais, emitir um patch
conjunto, copiar os outros blocos e reescrever globalmente quando a alteração é
ampla. Novos fatos sem relação usam slot vazio ou o último slot. Esse último
critério tende a conservar um prefixo longo, mas não é um otimizador calibrado
de latência. A abertura global em eventos grandes favorece fidelidade/capacidade
em detrimento do cache; suas consequências aparecem nos resultados sem alteração
de limiar depois da medição.

A interface é idêntica para AR e dLLM; não se concede à candidata uma estrutura,
seleção-oráculo, dependências anotadas, perguntas futuras ou acesso a histórico
que o comparador AR não tenha. As memórias passam a divergir por conta das saídas
dos próprios modelos, portanto o seletor pode escolher conjuntos distintos ao
longo das trajetórias. Isso compara sistemas online com a mesma política e não
isola o efeito da arquitetura com entradas internas idênticas em cada passo.

LLaDA denoiseia um canvas de patch em paralelo; a reconstrução externa aplica
seu texto somente aos blocos abertos. Não foi implementado infill simultâneo nas
posições originais de um canvas de memória inteira, nem política treinada,
planejador semântico de dependências ou pós-treino orientado a cache. Não tratar
um resultado negativo desse piloto como impossibilidade desses mecanismos.

Mesmo sem alterar blocos estáveis, uma edição no B0 invalida KV dos blocos B1–B3
no consumidor causal. O protocolo mede esse efeito retokenizando todo o template,
comparando IDs e descartando o sufixo após divergência. Padding, semelhança textual
e cópia de um sufixo não autorizam reutilização de KV desse sufixo.

A contribuição candidata desejada seria um seletor/treinamento novo que resolvesse
fidelidade de dependências e custo integral com vantagem específica verificável
sobre AR. Essa contribuição não é a implementação heurística acima, nem o objetivo
qualidade + ruptura de cache isoladamente. CADOC, ACON, DiffuAgent e edição por
difusão restringem fortemente essa reivindicação. O gate V1 serve para decidir se
há justificativa experimental mínima para investir; não prova originalidade.
