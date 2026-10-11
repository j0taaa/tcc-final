# Antecedentes conferidos e pergunta de novidade de A30

Consulta2026-10-11; fontes primárias. Ausência num conjunto de leituras não
prova ausência na literatura inteira. Não há revisão humana.

- Wang, Roohi, West, Viswanathan e Dullerud2019, *Statistical verification of
  PCTL using antithetic and stratified samples*, DOI10.1007/s10703-019-00339-8.
  [PDF dos autores](https://lagrange.mechse.illinois.edu/pubs/WaRoWeViDu2019/WaRoWeViDu2019.pdf),
  algoritmo1, seções3.1/3.2, hipótese2 e teorema1. Distribui m estratos a TODAS
  as cadeias por timestep; ordena estados conforme os conjuntos da propriedade.
  A afirmação conferida é correlação não positiva para a fração PCTL indicada,
  com V_psi2 contido em V_psi1, não dominância para todo verificador desconhecido.
  A30 mantém apenas histórias completas idênticas, até para mapas descontínuos;
  a consequência candidata é cobertura finita sob visitantes assíncronos.
  Estratificar ruído em Markov chains não é novidade deste TCC.
- El Haddad, Lécot e L'Ecuyer2024, *Simple stratified sampling for simulating
  multi-dimensional Markov chains*, DOI10.1007/978-3-031-59762-6_15.
  [Preprint dos autores](https://www.gerad.ca/papers/G-2023-68.pdf),
  introdução/seção2 conferidas no espelho GERAD após bloqueio do URL pessoal.
  Usa N=p^(2d)
  pontos em2d dimensões, metade para selecionar/ordenar estado e metade para
  transição; limites de variância O(N^-(1+1/(2d))) na classe declarada. Requer
  componentes avançados independentemente e condições de regularidade. É
  comparador relevante, não
  evidência de que toda estratificação adaptativa é inédita.
- Gerber, Chopin e Whiteley2019, *Negative association, ordering and convergence
  of resampling methods*, [preprint primário](https://arxiv.org/html/1707.01845).
  Resampling/associação negativa e preservação de estimadores são antecedentes.
  A30 não reivindica a desigualdade para subconjuntos nem Maclaurin. É preciso
  distinguir seleção de ancestrais de preservação da lei de cada path original.
- Vilnis et al.2023, *Arithmetic Sampling*,
  [artigo ICML](https://proceedings.mlr.press/v202/vilnis23a/vilnis23a.pdf),
  usa uma fase comum com espaçamento, e delimita condições de seus resultados
  de variância. Fase comum não é permutação independente por história.
- Sato2026, *DAST*, [artigo primário](https://arxiv.org/html/2609.33038v1).
  Ordenação semântica de tours/fase comum procura diversidade; cobertura de
  uma palavra não estabelece dominância de todo conjunto terminal. Verificar
  competitividade prática se a operação puder receber o mesmo modelo/política.
- Ren, Zhao e Ermon2019, *Adaptive Antithetic Sampling for Variance Reduction*,
  [artigo ICML](https://proceedings.mlr.press/v97/ren19b/ren19b.pdf), teorema1.
  Limite universal em uniforme: garantia fraca sobre iid pode ser mínima.
  A30 não recebe suficiência para publicação apenas por provar não piora.
- Gandhi, Khuller, Parthasarathy e Srinivasan2006, *Dependent Rounding and its
  Applications to Approximation Algorithms*, DOI10.1145/1147954.1147956,
  [PDF dos autores](https://www.cs.umd.edu/~srin/PDF/2005/depround-dec05.pdf),
  introdução/P1–P3 conferidas. Já oferece preservação de marginais e limites
  de produto para subconjuntos em arredondamento de vetores em grafos
  bipartidos. Não reivindicar essas propriedades como princípios novos. A
  pergunta que resta é o contrato de decoder implícito, visitantes adiados
  e mapa arbitrário sem calcular probabilidades de suas ações terminais.
- PyTorch2.8.0, [kernel CUDA](https://github.com/pytorch/pytorch/blob/v2.8.0/aten/src/ATen/native/cuda/DistributionTemplates.h),
  uniform_and_transform/uniform_kernel; [transformação CPU](https://github.com/pytorch/pytorch/blob/v2.8.0/aten/src/ATen/core/TransformationHelper.h),
  uniform_real. Também conferidos os headers NVIDIA curand_uniform.h locais,
  `_curand_uniform_double_hq` e curand_uniform2_double. Necessária a transformação
  numérica correta, não só o Gumbel ideal de um paper.
- EPIC pinado, `vendor/EPIC-Decoding/.../generate_constrained.py`, add_gumbel_noise
  e recuperação: no caminho auditado o mesmo tensor ruidoso serve aos rankings
  seguintes após recusa. Trocar somente a primeira proposta muda a distribuição.
  A30 só promete equivalência se preservar o tensor/transformação completos.

## Matriz de prioridade antes do protótipo

| Afirmação | Classificação atual |
|---|---|
| Estratificar RNG/Markov chains reduz variância em classes adequadas | conhecido |
| Subconjunto de estratos e desigualdade de Maclaurin | clássico |
| Igualdade de marginais sob permutação uniforme | consequência direta |
| Tabelas por histórico reveladas em qualquer ordem | construção probabilística conhecida |
| Dominância finita para TODO verificador sem sua ordenação, por história completa, visitantes desconhecidos | candidato a resultado/contrato delimitado; conferir antecedentes adicionais |
| Adaptador de um ruído bruto mantendo todo EPIC/fallback sem compiler posterior | candidato operacional, não nova teoria de parsing |
| Menos forwards únicos ou menor latência de qualquer lote | não sustentado |
| Ganho prático relevante/publicação suficiente | ainda não confirmado |

A26 é antecedente interno explícito. A30 não deve ser apresentado como sua
invenção independente; deve delimitar precisamente o acréscimo operacional.
