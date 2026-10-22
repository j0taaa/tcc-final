# A88 V1 — auditoria posterior da interpretação de custo

2026-10-22, após o resultado congelado `f1721bbb`. Nenhuma captura,
cabeça, caso, seed, variante ou medição nova. Esta nota preserva o resultado
original e delimita o que sua métrica permite concluir. Não substitui o gate
pré-registrado por outro retrospectivo nem seleciona uma nova variante.

## Resultado original preservado

O qualificador reportou vantagem pontual prevista de pelo menos 10% em
6/8 itens para `W<=.01`, com dois momentos degenerados inconclusivos.
O produto era variância por custo médio, incluindo preparação, verificação
das fontes e carregamento amortizados em 64 réplicas. O replay não executou
todos os métodos ponta a ponta e deixou 21,028703 s sem atribuição. Logo
o relatório original já classificou o custo operacional como inconclusivo.

## Sensibilidade ao preparo comum

O JSON congelado atribui 199,52254562207963 s a preparo comum, ou
3,1175397753449943 s por réplica. Uma análise do modelo já carregado pode
ser obtida dos MESMOS valores salvos:

    score_residente(m) = V_m * (custo_medio_m - preparo_comum/64)
    vantagem(m) = 1 - score_residente(m)/score_residente(d0).

O custo residente ainda contém a raiz uma vez por item, kernels por visita,
saída e o modelo otimista de cache global do replay. Portanto continua
sendo uma previsão, não latência ponta a ponta medida. Só se retira o
mesmo preparo comum de todos os métodos; não se alteram variâncias,
trajetórias, cache, intervalos ou a escolha de desenvolvimento.

| Linha MMLU | Vantagem prevista de W<=.01 frente a d0, modelo residente |
| --- | ---: |
| 150 | -119,21% |
| 209 | -2,26% |
| 47 | +84,04% |
| 12 | -6,42% |
| 85 | -35,53% |
| 279 | -32,00% |
| 183 | Inconclusivo: momento degenerado |
| 224 | Inconclusivo: momento degenerado |

A regra escolhida tem vantagem material residente em **1/8 itens** neste
replay. Cinco previsões são desfavoráveis e duas inconclusivas. Isso não
comprova uma perda real de latência em cinco checkpoints; todos os itens
usam o mesmo checkpoint e os custos são modelados. Também não justifica
ignorar a redução de variância observada ou o item favorável.

A mesma conferência sobre TODA a família pré-registrada não fornece uma
variante com seis vitórias residentes: d=1 atinge 10% em dois itens; cada
outra variante atinge no máximo um. Não se escolhe agora o melhor orçamento
para cada item, nem se substituem os dois itens degenerados.

## Por que o preparo muda a interpretação

Para N fixo, `V*(A/N+c)` é uma métrica declarada de erro versus custo
daquele orçamento. Contudo, quando o preparo comum A cresce, a ordenação
passa a depender principalmente de V, mesmo se o método exigir muito
mais trabalho de inferência. Isso não demonstra menor custo para atingir
uma precisão fixada.

Se uma réplica tem variância V e custo médio residente c, para uma meta de
erro quadrático e^2 o modelo simplificado de custo é

    C(e) = A + ceil(V/e^2)*c.

O mesmo A é pago uma vez por cada alternativa. Ele não favorece um método
ao se comparar a quantidade de inferência necessária para a mesma meta.
Para muitas réplicas, a comparação relevante nesse modelo é V*c, com A
reportado separadamente. Reutilização entre réplicas, custos aleatórios e
parada adaptativa exigem análise adicional; a fórmula não os apaga nem é
um teorema de tempo do executor real.

Assim, o sinal original de seis itens é verdadeiro para a métrica fria
de N=8 usada no qualificador, mas não sustenta uma alegação geral de
eficiência de inferência ou certificação de resposta. A incerteza de custo
não se resume aos 21 s sem atribuição.

## Decisão científica limitada

A prova e a redução de ruído continuam preservadas. A evidência atual não
justifica selecionar A88 como tema central, nem lançar uma campanha maior
apenas para confirmar o sinal de 6/8. Uma auditoria independente da
interpretação e dos controles foi solicitada antes de decidir qualquer
nova campanha. A seleção de desenvolvimento `W<=.01` não é modificada.
Nenhuma mudança de temperatura, scaffold, casos ou objetivo está autorizada
por esta nota para resgatar o qualificador.

## Reprodução sem modelo, GPU ou novas medições

O comando lê somente o JSON científico já congelado:

```bash
.venv-live/bin/python - <<'PY'
import json
from pathlib import Path

p = Path('attempts/88-first-commit-marginals/native-analysis-v1.json')
d = json.loads(p.read_text())
a = sum(d['setup_seconds'].values()) / 64
print('preparo comum por replica:', a)
for case in d['cases']:
    methods = case['methods']
    base = methods['d0']
    base_score = base['variance_trace'] * (base['mean_cost_seconds'] - a)
    advantages = {}
    for name in ('d1', 'd2', 'd4', 'd8', 'full', 'eta.01', 'eta.0001'):
        value = methods[name]
        score = value['variance_trace'] * (value['mean_cost_seconds'] - a)
        advantages[name] = 1 - score / base_score if base_score > 1e-15 else None
    print(json.dumps({'row': case['row'], 'resident_advantage': advantages}))
PY
```
