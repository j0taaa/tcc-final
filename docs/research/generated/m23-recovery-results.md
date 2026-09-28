# M23 — EPIC com a recuperação oficial

100 pedidos sintéticos por método, duas execuções. Acerto principal: AST da chamada.
A recuperação usa a função original do wrapper, sem modelo ou gabarito.

| Representação | Método | Chamadas corretas (1 / 2) | Valor correto (1 / 2) | Tempo reconstruído (ms) |
|---|---|---:|---:|---:|
| bytes | exact | 65 / 65 | 81 / 81 | 276.2 |
| bytes | epic_native_1 | 64 / 63 | 77 / 76 | 439.3 |
| bytes | epic_domains_1 | 40 / 40 | 64 / 68 | 159.9 |
| bytes | epic_native_4 | 81 / 81 | 84 / 84 | 620.8 |
| bytes | epic_domains_4 | 58 / 58 | 80 / 80 | 258.3 |
| bytes | epic_native_24 | 92 / 92 | 100 / 100 | 2314.0 |
| bytes | epic_domains_24 | 63 / 60 | 77 / 73 | 1117.3 |
| lexical | exact | 65 / 65 | 81 / 81 | 280.9 |
| lexical | epic_lexical_1 | 65 / 63 | 78 / 77 | 442.5 |
| lexical | epic_lexical_2 | 74 / 74 | 81 / 81 | 369.0 |
| lexical | epic_lexical_4 | 81 / 81 | 84 / 84 | 631.4 |
| lexical | epic_lexical_24 | 92 / 92 | 100 / 100 | 2427.8 |

Tempo reconstruído = geração previamente medida + recuperação CPU reexecutada
sobre o estado final salvo. Não é uma medição conjunta do pipeline. O setup
recriado no replay fica excluído, pois o wrapper já possui gramática e lexer.
A recuperação não faz forwards e pode ultrapassar os slots/domínios do MWPC.
A métrica numérica é secundária; coincidência do valor não garante a chamada pedida.
Os resultados sem recuperação permanecem nos relatórios dos geradores.

| Representação | Método | Status de recuperação (rodada 1) | Mediana da recuperação quando necessária (ms) | Saídas estáveis |
|---|---|---|---:|---|
| bytes | exact | {'not_needed': 100} | 0.000 | True |
| bytes | epic_native_1 | {'not_needed': 66, 'recovered': 34} | 5.027 | False |
| bytes | epic_domains_1 | {'recovered': 64, 'not_needed': 36} | 5.619 | False |
| bytes | epic_native_4 | {'recovered': 12, 'not_needed': 88} | 5.913 | True |
| bytes | epic_domains_4 | {'recovered': 52, 'not_needed': 48} | 5.222 | True |
| bytes | epic_native_24 | {'not_needed': 100} | 0.000 | True |
| bytes | epic_domains_24 | {'not_needed': 76, 'recovered': 24} | 4.263 | False |
| lexical | exact | {'not_needed': 100} | 0.000 | True |
| lexical | epic_lexical_1 | {'not_needed': 66, 'recovered': 34} | 3.956 | False |
| lexical | epic_lexical_2 | {'not_needed': 84, 'recovered': 16} | 4.995 | True |
| lexical | epic_lexical_4 | {'recovered': 12, 'not_needed': 88} | 4.885 | True |
| lexical | epic_lexical_24 | {'not_needed': 100} | 0.000 | True |
