# Correção explícita do oráculo V1

Origem: implementação congelada em `2a1e7de7`, `Oracle.marginal` em
`oracle.py`. A primeira execução de `audit.py` parou no primeiro caso
(BALANCE n=4, α=1/100, witness_plus), antes das métricas, porque uma
posição fixada em zero buscava a massa da **outra** fibra, fixada em um,
em vez de retornar zero. A referência independente por filtragem de tuplas
detectou a discrepância das condicionais.

`results-v1.jsonl` preserva o registro FAIL original. O commit de correção
mantém a fonte original recuperável no Git e adiciona o tratamento explícito
de posições já fixadas. Não muda operação, casos, seeds, precisão,
comparadores ou gates do protocolo `0070c2ba`. A execução corrigida usa
`results-v1-corrected.jsonl`, sem sobrescrever a falha.

O erro afeta a interface que retorna **todas** as marginais, embora o
incremento residual só leia posições livres. Corrigir o contrato completo
é necessário antes de avaliar os resultados. Nenhum resultado favorável
é inferido desta correção.
