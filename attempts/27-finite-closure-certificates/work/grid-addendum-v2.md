# Refinamento de diagnóstico v2, antes de executar

V1 é mantida: no primeiro head público, todos os bounds eram zero quando a
fronteira já era vazia. Isso não mostrou utilidade. Não trocar esse resultado
por um exemplo escolhido por conter uma cauda favorável.

V2 toma TODOS os18 estados já usados no desenvolvimento A22/A24 e os mesmos
seis limites de profundidade do diagnóstico A24. Cada caso/profundidade recebe
os cinco módulos e cinco conjuntos de potenciais:1080 resultados previstos.
Não há divisão independente nova nem timings; são dados já vistos. O protocolo
e código são commitados antes do comando de execução. Hashes de cada quadro,
probabilidades originais, vocabulário e massas exatas arquivadas são registrados.
Massa rasa zero e recusas permanecem no denominador do diagnóstico.

O gate é somente necessário: um certificado finito que nunca evita uma
profundidade maior que o controle sem fechamento não justifica implementar
outro sampler. Uma melhora de profundidade também não prova velocidade,
novidade ou utilidade global. O custo dos módulos/potenciais e um controle
clássico usando a mesma abstração terão de entrar em qualquer fase competitiva.
As respostas1–8 do README e as objeções de prioridade continuam aplicáveis.

Comando previsto:

```bash
.venv/bin/python -m attempts.27-finite-closure-certificates.work.diagnostic_grid_v2 --output attempts/27-finite-closure-certificates/work/evidence/development-feasibility-v2
```
