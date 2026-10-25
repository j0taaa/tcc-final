# Fontes primárias e investigação dirigida — 23/10/2026

- Beyond Fixed / DAEDAL, Li et al., v2 18/08/2025:
  https://arxiv.org/html/2508.00819v2, §3.2. Expansão inicial por EOS e inserção
  iterativa em baixa confiança já implementadas. Não atribuir isso a A89.
- Mündler, Dekoninck, Vechev: https://arxiv.org/pdf/2508.10111,
  apêndice E, páginas impressas 24–25 (índices PDF 23–24), conferidas.
  Modelar tokens restantes aumenta construção/interseção; expansão já sugerida.
  Contar posições do modelo e inserir MASKs não são, isoladamente, novidade.
- EPIC v2 04/10/2026: https://arxiv.org/html/2606.00722v2,
  §3–4 e apêndices C/E. Lexing reutilizado, cover regular, teste CFG exato e
  compromisso paralelo implementados; lacunas usam abstração lexical.
  Código preservado em vendor/EPIC-Decoding, sem editar, ver hash no manifesto.
- DreamOn: https://hkunlp.github.io/blog/2025/dreamon/ . Estados treinados de
  expansão/remoção implementados; não é o mesmo contrato training-free de A89.
- Gram2Token, ICML 2026: https://proceedings.mlr.press/v306/hua26b.html .
  Compila execução gramatical sobre bytes em categorias/tabelas de tokens na GPU,
  com overhead de preparo/TTFT. Precedente direto de sistemas; não é evidência
  de que o mesmo sistema resolva inserção conjunta em lacunas fora de ordem.
- FactorDLM: https://arxiv.org/html/2609.32900v1, §3–5 e apêndice B.
  Inferência exata CPU/CUDA em fatores finitos e variabilidade via EOS implementadas.
  O próprio artigo relata crossover CPU/GPU e limites de largura. A representação
  finita A89 pode ser codificada como fatores em cadeia: não alegar nova inferência
  finita. Não inferir que isso resolve GLC recursiva geral com baixo custo.
- XGrammar: https://arxiv.org/abs/2411.15100 . Compilação lexical, pilhas
  persistentes e sobreposição são precedentes, não novidade de portar à GPU.
- Dados BBH: https://github.com/suzgunmirac/BIG-Bench-Hard/tree/9ee07bd481feebf959a6b59d61ea57bdcf30964d .
  Cópia identificada e licença preservadas em evidence/.

Busca web dirigida: `diffusion grammar length expansion decoding 2026`,
`diffusion length Earley grammar mask`, `length-aware grammar diffusion`,
`site:arxiv.org grammar diffusion adaptive length masks tokens feasibility`,
`site:arxiv.org context free grammar length constrained completion GPU insertion diffusion`.
Não foi estabelecida prioridade da formulação específica. Busca negativa não
certifica originalidade mundial. Fontes adjacentes de adaptação de comprimento
(p.ex. https://arxiv.org/abs/2608.22274) reforçam que adaptar canvas é conhecido;
não são comparações de alocação exata conjunta sob CFG.

Contexto local lido: AGENTS.md, README.md, docs/status.md, A19, A28, A36 e A83.
A19 cresce suporte de IDs, não o canvas; A28 não passou o gate integral; A36
identificou GPIO-LLM antes de implementar. Nenhum resultado antigo é resgatado.
