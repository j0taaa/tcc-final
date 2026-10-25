# Limites definidos antes de julgar utilidade downstream

Este piloto tem uma única amostra por célula. Ordem fixa pseudoaleatória reduz
confusão com ordem de método, mas não estima dispersão da latência, consumo
energético, throughput ou concorrência de serving. Exclui outros processos CUDA
por lock; aplicações gráficas normais do desktop permanecem. Contadores de pico
PyTorch não incluem todo o overhead do driver e não são pico NVML de processo.
CPU peak RSS inclui o processo, não todo o sistema. A liberação efetiva da GPU
é garantida pela vida do processo sob o lock, inclusive buffers persistentes de
bitsandbytes que podem permanecer após `empty_cache`.

Sintéticos cabem no orçamento mesmo sem compressão: são sanidade factual, não
uma carga que necessite compactação. O piloto chama os editores a cada evento
para testar atualização/contradição/dependências. Uma política que mantivesse
histórico bruto até encher o orçamento evitaria chamadas desnecessárias aqui.
Portanto tempos sintéticos não refutam esse agendador mais competente; relatamos
custos externos separadamente e não apresentaremos a heurística como política
ótima de custo. `full_history` e `raw_tail` expõem o custo dessa escolha.

Histórias externas completas têm 1.017–6.168 tokens Qwen; cabem no consumidor de
32k. Assim o controle de histórico completo é especialmente adequado e forte.
Não extrapolar para sessões de 115k, pressão de capacidade, milhares de próximas
consultas ou arquiteturas/modelos diferentes. Não multiplicar economia por uma
quantidade imaginada de interações para obter amortização favorável.

Eventos grandes abrem todos os blocos pela regra fixada: avalia-se um fallback
global conservador; isso reduz a oportunidade de edição local no subconjunto
externo. Falha do gate não demonstra impossibilidade de um localizador semântico
melhor, de infill nativo multi-span ou de outro orçamento. Tampouco a existência
de alternativas ainda não medidas autoriza pós-treino grande ou reivindicação
de contribuição substancial.

O AR 3B e a dLLM 8B não têm pré-treino, capacidade ou formato de geração pareados.
A restrição local de disco motivou o AR compacto. Se a dLLM vencer, ainda falta
um AR maior/mais forte e mais de um par de modelos para alegar vantagem da
arquitetura. Se o AR menor alcançar igual qualidade a menor custo, esse fato já
invalida vantagem sobre este controle, sem provar dominância universal de AR.

Revisão semântica externa oculta os nomes dos métodos, mas o estilo pode sugerir
a família do modelo. O mesmo agente conduziu implementação e julgamento. Não é
avaliação humana independente nem substituto do judge oficial LongMemEval.
As respostas/referências e a chave ficam públicas na entrega local para revisão.
Menções lexicais de fatos na memória e de valores superados são diagnósticos:
implicitamente reter uma relação não exige escrever sua resposta literal, e citar
um valor antigo negado/histórico não é usá-lo incorretamente como atual. Os casos
sinalizados precisam ser auditados, não convertidos automaticamente em erro.
