# A80 — resultado offline V1 não positivo

**O gate operacional falhou nas duas famílias.** A grade não obteve a redução
de 20% no custo completo frente ao melhor controle executado aplicável. Esta
aplicação V1 está encerrada; não ampliar casos, mudar seeds ou reduzir controles
para resgatar o resultado. A prova escrita de calibração permanece preservada,
com prioridade suficiente e utilidade geral em dLLMs ainda abertas.

| Família | Configurações comparadas | Mediana tempo grade / melhor controle | Critério |
| --- | ---: | ---: | --- |
| Dyck com aliases | 12 | 1,12842 | Falhou; cerca de 13% mais lenta |
| Expressões prefixas com aliases | 12 | 1,21288 | Falhou; cerca de 21% mais lenta |

São razões pareadas por configuração, agregadas conforme o protocolo; não são
razões entre medianas isoladas nem estimativas universais de tempo esperado.
Os casos de precheck foram preservados. As duas seeds não estabelecem
significância estatística nem verificam a probabilidade de falha do teorema.

## Fontes e congelamento

- Protocolo e prova: commit `d356cfde101ee27e626909d9618f419769cd7af7`.
- Executável produtor: commit `d1a1922c9bec0d4a0b81417f8abfcdc89bf6e87f`.
- [Notas pré-dados](implementation.md): a revisão identificou a verificação
  enumerável fora do tempo comparado e subcontagem de bits. Ambas foram
  corrigidas antes de qualquer execução de produção, com regressões.
- [Metadados e hashes](work/evidence/offline-v1/metadata.json),
  [todas as linhas](work/evidence/offline-v1/rows.jsonl),
  [decisão por configuração](work/evidence/offline-v1/decision.json) e
  [conclusão da execução](work/evidence/offline-v1/completion.json).

O README da tentativa é o protocolo congelado, incluindo seu estado anterior à
execução. Este arquivo registra o resultado posterior sem sobrescrevê-lo. Não
houve execução neural, GPU, treinamento, alteração de baseline ou nova medição
seletiva. A operação é uma lei produto congelada condicionada por gramática,
sem transferência à trajetória nativa ou qualidade semântica de um modelo.

## Execução completa e correção

Foram registradas as 144 execuções previstas em aproximadamente 180,53 segundos,
dentro dos 900 segundos globais:

- 104 conclusões normais, incluindo calibração ou projeção exata;
- 24 emissões diretas de `P`, certificada pelo precheck, sem calibração;
- 16 recusas da enumeração exata acima do teto público de 65.536 palavras;
- zero erros, timeouts, recusas de memória ou interrupções.

As recusas são inconclusivas para esse controle, não inviabilidade. O comparador
exato só participa onde cabe no limite declarado; as 24 comparações de grade
têm controles aplicáveis concluídos, sem lacunas.

Foram geradas e avaliadas **3.090.188 palavras internas de calibração** e
validadas independentemente **2.048 palavras finais** de IDs originais, com
aliases preservados. Não ocorreu fallback nas emissões observadas; o caminho
de fallback permanece verificado por testes de lei finita. Não foram guardadas
todas as palavras, probabilidades ou traces.

Os certificados empíricos e seus orçamentos passaram nas execuções amostrais.
Nos 48 processos com suporte enumerável, os testemunhos exatos conferiram massa,
normalização e pertencimento a `C_R`; o maior excesso KL condicional observado
em binary64 foi aproximadamente `0,00029835`, abaixo de `xi=0,02`. Esse é um
diagnóstico numérico, sem intervalos de log certificados. Não valida por si
mesmo a confiança `beta=0,05`, a lei marginal final ou DP de um executável.

## O que os controles mostraram

Nos casos pequenos de `R=2`, o controle exato foi o mais rápido; a grade levou
aproximadamente 2,31–2,58 vezes seu tempo. Para `R=2` e comprimentos maiores,
a mediana foi o melhor controle. Para `R=16` nos casos que precisaram calibrar,
os índices compactados foram o melhor controle executado; diferenças de tempo
da grade frente a eles ficaram próximas de zero e não atingiram o gate.
Os casos `R=16,n=8` passaram pelo precheck, evitando calibração em todos os
métodos. O orçamento assintótico melhor da candidata não assegura uma vantagem
nesses parâmetros finitos.

O estado retido declarado da grade foi menor que o de ratios brutos: as medianas
de storage Python nos 20 casos calibrados por método foram 360.898 e 4.405.632
bytes, respectivamente. Isso verifica uma realização comprimida. Não estabelece
novidade, superioridade global de memória ou ganho de tempo. Os estados dos
controles têm escopos de workspace explicitamente diferentes; o RSS cobre o
processo inteiro, inclusive verificações. O pico RSS entre os processos variou
de 24.518.656 a 84.213.760 bytes. Não há medição de VRAM. As larguras racionais
registradas são majorantes conservadores nos escopos declarados.

MetaGrad e coeficientes de controle variável aprendidos continuam controles
teóricos não implementados. Uma vitória deste V1 tampouco provaria
superioridade sobre eles; o resultado observado já falhou contra os controles
implementados.

## Verificação e consequência científica

Antes da execução: `make check` passou, com 345 testes, tipos, lint, formatação
e integridade EPIC. A suíte própria passou em 37 testes independentes, incluindo
leis racionais, extremos e empates, CDF do GK, discretização U64, aliases, pins,
multibyte e ordenação dos diagnósticos antes da primeira saída. Após a execução,
a decisão foi reconstruída a partir das linhas; contagens, flags dos
certificados e componentes do custo foram conferidos. Testes não provam
prioridade ou benefício semântico.

O lema específico da [prova escrita](theory.md) continua uma candidata teórica
sob suas hipóteses. Este ensaio não estabeleceu um método com vantagem integral
nem um consumidor privado semanticamente útil. A80 não é selecionada como tema
central; a meta de três métodos distintos qualificados permanece aberta.
