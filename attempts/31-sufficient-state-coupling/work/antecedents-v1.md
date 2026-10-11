# Revisão direcionada antes da implementação de A31

2026-10-11. Não estabelece ausência global nem revisão humana.

- Craiu e Meng2005, *Multiprocess parallel antithetic coupling for backward
  and forward Markov chain Monte Carlo*, Annals of Statistics33(2),661–697,
  DOI10.1214/009053604000001075,
  [PDF dos autores](https://statistics.fas.harvard.edu/file_url/1056).
  Seções1,2 e teorema1: antithetic MCMC/LHS e ligação estratificação são
  antigos. O resultado conferido de não deterioração restringe funções
  monótonas; discute perdas para funções não monótonas. Não reivindicar
  acoplar várias cadeias como novidade. A31 condiciona coordenação à
  igualdade de estados suficientes, sem requerer monotonicidade do kernel/f.
- Wang et al.2019, [STMC/PCTL](https://lagrange.mechse.illinois.edu/pubs/WaRoWeViDu2019/WaRoWeViDu2019.pdf),
  algoritmo1, hipótese2/teorema1: ordenação conforme propriedade e classes
  PCTL declaradas. Não trata o mapa native-noise sem ordenar pelo verificador.
- El Haddad, Lécot e L'Ecuyer2024,
  [SSS/Array-RQMC](https://www.gerad.ca/papers/G-2023-68.pdf), introdução/seção2.
  Compara variância sob regularidade/ordenação e componentes independentes.
  A31 não alega taxas assintóticas melhores, somente uma desigualdade finita
  e identidade de energia sob a igualdade de estados suficientes.
- Gandhi et al.2006,
  [dependent rounding](https://www.cs.umd.edu/~srin/PDF/2005/depround-dec05.pdf),
  P1–P3: marginais e desigualdades de produtos já conhecidas. Maclaurin e
  preservação de marginais não constituem novidade própria.
- Ren et al.2019,
  [No-Free-Lunch](https://proceedings.mlr.press/v97/ren19b/ren19b.pdf), teorema1:
  uma garantia universal fraca pode ter ganho minúsculo; energia precisa
  representar uso real. Não prometer benefício substancial de toda reunião.
- A30v1 é referência interna explícita para tabelas de K fixo e adaptador
  nativo. A26 com partições de m variável é outro método: (4)-(6) NÃO são
  automaticamente comparação com ele. A29 já expõe princípios de Dirichlet
  clássicos e o limite de reparar apenas duplicatas terminais.
- Neufeld, Bowling e Schuurmans2015, *Variance Reduction via Antithetic
  Markov Chains*, [PDF AISTATS dos autores](https://webdocs.cs.ualberta.ca/~daes/papers/aistats15.pdf).
  Teorema1/seção3.2: simetria de kernel, importance sampling e análise de
  variância sob proposta localmente uniforme. Não reivindicar variance
  reduction geral por Markov chains. O comparador de A31 mantém o MESMO
  kernel individual por camada e contabiliza reencontros de duas execuções;
  falta ainda excluir uma equivalência mais direta à literatura próxima.

## O que ainda precisa ser conferido

Prioridade de acoplamento somente na diagonal para kernels não monótonos,
quantificação por energia de encontros e comparação com um método que
coordena somente antes da primeira divergência. A ausência nas leituras
acima não basta. Provas e oráculos testarão a diferença antes de qualquer
campanha, incluindo o risco de falsa suficiência do resumo do decoder.
