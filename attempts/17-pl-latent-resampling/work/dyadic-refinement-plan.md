# Refinamento numérico declarado antes da segunda campanha

Durante a campanha de referência, a mistura perdeu para a rejeição em vários
inputs e encontrou recusas. A referência usa `1/lower(exp(x))` para limitar
`exp(-x)`; o denominador varia por token. O MMC por slot pode, por isso,
somar os tamanhos binários de muitos denominadores coprimos.

Será investigado um refinamento de representação, sem mudar alvo, estados,
taxas, eventos, orçamento ou comparadores. Essa escolha usa os primeiros
resultados como desenvolvimento: a repetição no mesmo conjunto não passa a
ser validação externa independente. Todas as perdas da primeira execução ficam.

## Contrato e prova antes de implementar

Para tolerância `delta>0`, obtenha `u<=v<=u+delta/2`, com `u=exp(-x)` e
`v<=1`, pelo método já auditado. Escolha `p` com `2^(-p)<=delta/2`, e devolva

\[
 \bar u=\min(1,2^{-p}\lceil 2^p v\rceil).
\]

Então `u<=ubar<=1` e `ubar-u<=delta`. A prova do envelope e o bound
`2J+1` não mudam. Uma tolerância comum produz uma potência de dois comum;
o MMC desses fatores deixa de acumular denominadores coprimos. Isso não elimina
os denominadores próprios de `q`, das taxas nem dos coeficientes da mistura.

Também serão preparados uma vez os pesos categóricos dos componentes e os
coeficientes inteiros do envelope. São valores invariantes da consulta; isso
evita repetir MMCs em cada tentativa. A enumeração já recebe a mesma otimização
de tabela categórica. Não é uma nova regra de aceitação ou contribuição teórica.

Os oito critérios da tentativa continuam valendo: uso de treinamento e operação
condicional iguais; mudança numérica conhecida, sem novidade reivindicada;
vantagem de custo ainda a medir; prova acima independente de execução;
protocolo inteiro permanece; custos de preparação/reconstrução continuam;
objeção é permanecer mais lento que rejeição/enumeração; anterioridade e
treinamento real continuam pendentes para artigo.

Antes da campanha: testar novamente as leis racionais e o erro do enclosure,
fazer commit/push e guardar hashes. Executar os mesmos nove casos, três
repetições, lotes 1/4/16 e comparadores do protocolo original. A execução anterior
deve terminar antes da nova medição, para não competir pela CPU.
