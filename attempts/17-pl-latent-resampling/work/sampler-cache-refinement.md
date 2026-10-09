# Controle fortalecido antes de decidir utilidade

As perguntas científicas dos planos anteriores continuam válidas: esta é uma
correção de custo convencional, sem diferença de política ou alvo. A execução
bulk v1 foi interrompida explicitamente para fortalecer o comparador, antes de
concluir o conjunto; seus registros parciais permanecem acessíveis e não serão
apresentados como campanha completa nem removidos por perder ou ganhar.

Todos os WeightedForests passam a guardar as CDFs inteiras dos nós visitados,
sem caches globais ou reaproveitamento entre pesos distintos. Os pesos/inside
são imutáveis durante a consulta. A CDF guarda exatamente as massas dos termos;
bisect_right implementa as mesmas partições categóricas, incluindo massas zero,
sem reconstruir Fractions/cumulativos a cada visita. Nenhuma alternativa some.
No SingleTilt, produtos de unárias dyádicas recebem a mesma representação por
inteiros já utilizada pela mistura. Preserva exatamente o envelope anterior.

A memória adicional será registrada como nós/entradas/bits das CDFs criadas;
a primeira construção continua dentro do timing. Usar esse cache é conhecido,
não contribuição científica. Oráculos racionais devem passar antes do replay.

Refazer **todos** os casos bulk v2 e a campanha neural v2 após congelar o código;
não apenas o evento que parece ganhar. Mesmos inputs, ordens, seeds, suportes,
limites e métricas. A captura neural pode mudar somente por variabilidade
numérica de execução; documentar isso em vez de trocar casos. Timings v1 são
mantidos. A avaliação de novidade permanece separada dos ganhos de engenharia.
