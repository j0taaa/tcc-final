# M23 — gerador EPIC, antes da recuperação

Gerado dos arquivos validados; 100 pedidos sintéticos já usados no M22, duas
execuções por método. Repetições não são tarefas independentes.

A conclusão sobre o fluxo completo deve usar também o relatório
[EPIC com recuperação oficial](m23-recovery-results.md).

| Método | Chamadas corretas (1 / 2) | Resultado numérico correto (1 / 2) | Forwards (1 / 2) | Mediana total (ms) |
|---|---:|---:|---:|---:|
| exact | 65 / 65 | 81 / 81 | 205 / 205 | 276.2 |
| epic_native_1 | 46 / 46 | 54 / 54 | 100 / 100 | 439.3 |
| epic_domains_1 | 18 / 18 | 30 / 30 | 100 / 100 | 157.3 |
| epic_native_4 | 76 / 76 | 77 / 77 | 394 / 394 | 620.8 |
| epic_domains_4 | 32 / 32 | 40 / 40 | 200 / 200 | 256.9 |
| epic_native_24 | 92 / 92 | 100 / 100 | 2272 / 2272 | 2314.0 |
| epic_domains_24 | 49 / 49 | 57 / 57 | 1037 / 1037 | 1117.3 |

Mediana calculada após agregar as duas medições de cada pedido. Inclui
inferência, decodificação e setup da gramática/lexemas/domínios; exclui
carregamento, warmup e diagnóstico contrafactual MWPC.

| Comparador | Só MWPC acerta | Só EPIC acerta | Ambos acertam | Tempo EPIC / MWPC* |
|---|---:|---:|---:|---:|
| epic_native_1 | 24 | 5 | 41 | 1.14 |
| epic_domains_1 | 48 | 1 | 17 | 0.59 |
| epic_native_4 | 7 | 18 | 58 | 2.18 |
| epic_domains_4 | 41 | 8 | 24 | 0.91 |
| epic_native_24 | 6 | 33 | 59 | 7.89 |
| epic_domains_24 | 35 | 19 | 30 | 4.01 |

*Mediana dos quocientes pareados somente onde ambos acertam; >1 favorece MWPC.

Saídas, status e forwards idênticos nas repetições: **True**.

## Limites da comparação

Chamadas corretas: AST idêntico ao pedido, ignorando whitespace legal. Resultado
numérico é métrica secundária: aceita equivalências aritméticas, mas não prova
preservação das operações pedidas. Nenhuma métrica aceita geração incompleta.

EPIC original usa vocabulário nativo, rejeições no mesmo forward e lacunas
abstratas. A variante `domains` recebe os domínios do MWPC, mas a máscara
renormaliza a confiança; não torna os seletores isoladamente equivalentes.
Etapas EPIC 1/2/4/24 são orçamentos distintos, não 24 forwards garantidos.
MWPC usa até 24 forwards e otimiza propostas dentro de suporte finito por etapa.
Métodos native/domains usam lexemas por byte; lexical usa nomes de funções,
dígitos e pontuação. Ambos representam o mesmo catálogo canônico, mas o
lexer EPIC admite whitespace. O controle lexical testa a sensibilidade a isso.
Um modelo quantizado, uma GPU e uma linguagem pequena e finita. Não há
evidência aqui de superioridade geral em APIs reais ou sobre outras configurações.
