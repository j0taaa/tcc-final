# Sondagem offline de rank em sintaxe — addendum anterior aos dados

Esta sondagem responde à pendência de utilidade do compilador em gramáticas
de sintaxe. Não substitui nem altera os seis casos, métricas, controles ou
gates do protocolo operacional V1. Não inclui modelo, GPU ou timings.

Usar os fontes atuais das gramáticas JSON e Dyck mantidas no repositório e
o compilador de posterior existente para obter um forest finito. Converter
apenas escolhas de token em folhas com os IDs originais, produtos em AND e
alternativas em OR. O compilador A73 verifica seus contratos. Não modificar
a biblioteca; essa ponte tem como único consumidor esta sondagem.

Tokenização de um byte por slot, usando IDs originais do tokenizer Qwen pinado.
Alphabetos declarados: JSON `[]{}\":,01ab `, Dyck `()[]`. Não usar aliases
inventados, EOS/PAD nem tokens de vários bytes nesta sondagem. Portanto ela
não representa a distribuição de tokenizações BPE do vocabulário completo.

Casos: JSON totalmente livre com n=8,16,32; Dyck totalmente livre com
n=4,8,16,32; JSON `[x,x]` com cinco slots, delimitadores fixados e cada x
independentemente em {0,1}; JSON `{"a":x,"b":x}` com 13 slots, estrutura
fixada e os dois x independentes em {0,1} (o nome x é apenas um marcador,
não igualdade). Nove casos, sem seleção por resultado.

Medir somente contagens: nós/arestas do forest, por ID q_v, número de posições
onde seu indicador varia e Σq_v. A referência sparse competente omite slots
forçados e consulta somente pares posição/ID viáveis variáveis. Em uma base
correta, uma coluna é não nula se e somente se o indicador daquela posição
varia; isto dá a contagem exata desse controle. Não usar nV como denominador
primário. Ranks e sparsity não são latência, utilidade geral ou prioridade.

Limites por caso: 100 mil células e 500 mil alternativas no parser, deadline
cooperativo 120 s. Recusas são inconclusivas e preservadas. Para entradas
pequenas fixadas, verificar todas as palavras com `json.loads` e rank inteiro
independente. Para Dyck n<=8, verificar por enumeração de palavras e uma pilha
independente. Não enumerar línguas exponenciais dos casos maiores. Não aumentar
limites nem casos depois dos resultados para obter redução favorável.
