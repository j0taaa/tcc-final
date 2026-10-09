# Reamostragem latente condicionada à seleção Plackett–Luce

Iniciada em 2026-10-08 a pedido do usuário. Estado: auditoria técnica e decisão
de uso concluídas; há vantagem delimitada em lote, descrita em
[usefulness-decision.md](work/usefulness-decision.md).
Conquista científica completa ainda não confirmada. A nota recebida é preservada
em `work/received-note.md`; os programas citados nela não foram fornecidos.
A implementação desta tentativa foi criada independentemente.
O núcleo/contratos de produção permanecem como base de comparação.

## Oito critérios científicos

1. **Uso:** obter muitas amostras condicionais para auditar a seleção PL de uma
   dLLM sob JSON/DSL; estudar também redução de ruído em gradientes on-policy.
   O benefício validado da mistura é a operação de lote, não melhor treinamento.
   Tokens propostos e descartados são latentes; os commitments e a
   ordem PL são observados. A saída é uma amostra condicional de IDs originais,
   usada no score da política original. Não é aceleração do decoder final.
2. **Significância:** candidato é o amostrador gramatical condicional com
   envelope fatorável, custo em `sqrt(k) log(kappa)` e correção racional exata.
   PL, Rao–Blackwellização, rejeição e aproximações exponenciais são conhecidos.
   A diferença para Beylkin–Monzón e envelopes clássicos ainda precisa ser
   delimitada; nem prioridade nem suficiência para publicação estão confirmadas.
3. **Adoção:** menos variância por trajetória neural, estritamente quando há
   variância latente. Comparar com o score completo, rejeição condicionada aos
   tokens com envelope `f(L)`, inclinação exponencial única com majorante secante
   ótimo, enumeração e Rao–Blackwellização exata onde cabem. A rodada final
   inclui perfis com três granulações e MH estacionário com moeda integrada.
   Só há vantagem por tempo se custo vezes variância diminuir; não basta vencer
   um rejeitador que use desnecessariamente o limite 1.
   A decisão final recomenda enumeração nos 12 casos neurais pequenos. Para
   lotes de 4096, a mistura passa o critério de 20% em 3/48 eventos com circuito
   disponível, 2/48 incluindo compilação; no prefixo 1024, nenhum. As medianas
   frias de um evento são 11,08 s versus 23,82 s do SingleTilt fortalecido.
4. **Matemática:** auditar redução PL, cobertura, moedas racionais, custos e
   identidade de covariância. A identidade isolada é antecedente. A prova escrita
   `work/product-proposal-separation.md` estabelece uma separação assintótica
   contra qualquer proposta produto única. Ela não abrange todas as soluções;
   um contador especializado também resolve sua família em tempo polinomial.
5. **Experimentos:** protocolo em `work/protocol.json`, congelado em Git antes
   das medições. Famílias construídas são oráculos de correção; os nove inputs
   JSON M34 completos são replays de modelo, não novos rollouts ou benchmark
   independente de treinamento. Seis documentos externos selecionados por hash
   antes dos forwards avaliam 12 configurações de gradiente da cabeça real.
   Planos [neural](work/neural-utility-protocol.json),
   [bulk](work/bulk-utility-protocol.json),
   [envelope/perfis](work/envelope-profile-refinement.md),
   [decisões forçadas](work/forced-decision-refinement.md) e
   [perfis grossos](work/coarse-profile-control-plan.md) e
   [representação por índices](work/indexed-profile-control-plan.md) registram cada mudança
   antes de medir; todos os estados e recusas permanecem no relato.
   A [verificação dos tetos de tabelas](work/profile-resource-budget-plan.md)
   amplia recursos do comparador para que suas recusas não fabriquem uma vitória.
6. **Custo:** incluir compilação, enclosures, componentes, amostragem, memória
   lógica e aritmética; separar primeira saída/lote. O replay exclui forward
   e backward; o estudo neural os executou, com backbone congelado, além do
   custo extra do sampler/score. Piso neural exclui trabalho gramatical comum
   para não fabricar ganho com preparação ineficiente. Não converter redução
   de variância em melhor qualidade ou convergência sem uma ligação adicional.
7. **Objeções:** métodos gerais podem obter o mesmo envelope; enumeração pode
   vencer; taxas quase constantes favorecem rejeição simples; preparação pode
   dominar. Uma distribuição condicional exata não basta para PPO/GRPO com
   clipping. Suporte fixo e política original correta são hipóteses essenciais.
   `work/auxiliary-variable-objection.md` mostra como uma réplica correlacionada
   de Gibbs, iniciada na proposta original, também reduz variância sem viés.
   Gibbs contínuo não foi medido. O controle racional MH estacionário foi
   implementado, testado por balanço detalhado e medido no estudo neural.
   Os [antecedentes adicionais](work/utility-antecedents.md) incluem Dyer:
   arredondamento com correção exata por rejeição é técnica estabelecida.
8. **Artigo:** há uma vantagem medida de lote, com limites explícitos. Ainda
   faltam revisão independente, anterioridade suficiente e avaliação de
   treinamento completo. As verificações
   aqui não serão apresentadas como treinamento, prioridade ou prova de Lean.
   A [obstrução em bits](work/normalizer-bit-obstruction.md) e o
   [corolário de auditoria](work/conditional-audit-corollary.md) delimitam um
   benefício matemático de amostragem sem normalizador, compartilhado por
   alternativas adequadas; não são prova de exclusividade da mistura.

## Contrato de referência

Circuito finito determinístico/decomponível de tokens, gramática LL(1), slots
fixos e EOS ausente no backend mantido; pesos e taxas racionais positivos.
Evidência contém tokens fixados e ordem PL de posições inicialmente livres.
Preservar aliases e bytes. Não contar derivações como eventos diferentes.
Preparação recusada é inconclusiva, não inviabilidade. Nenhuma cauda é
renormalizada silenciosamente. Uma interrupção dependente do sorteio não
certifica a lei das amostras condicionada a ter concluído antes do prazo.

`work/` contém código e evidência independentes. O backend mantido será
identificado pelo commit-base e incluído no snapshot desta tentativa; não há
importações das referências mutáveis das tentativas 15/16.

## Comandos e resultado

O [relatório final de utilidade](work/evidence/utility/final-utility-decision.md),
seu [prefixo 1024](work/evidence/utility/final-prefix-decision.md), o
[relatório histórico](work/final-report.md), a
[auditoria matemática](work/mathematical-review.md) e as
[fronteiras da confirmação](work/assessment-boundaries.md) separam correção,
tentativas esperadas, tempo de consulta, novidade e benefício neural.
Todos os registros, incluindo o erro inicial do harness e as versões mais
lentas, ficam em `work/evidence/`. O protocolo foi congelado antes de medir;
refinamentos posteriores têm planos próprios e não são avaliação externa nova.

```bash
PYTHONPATH=src:. .venv/bin/python attempts/17-pl-latent-resampling/work/audit.py \
  --dyadic --tight-bounds --single-tilt --output .cache/pl-correctness-new.json
PYTHONPATH=src:. .venv/bin/python attempts/17-pl-latent-resampling/work/replay.py \
  --numeric-variant tight-dyadic --extra-control --output .cache/pl-replay-new
PYTHONPATH=src:. .venv/bin/python attempts/17-pl-latent-resampling/work/report.py \
  --evidence attempts/17-pl-latent-resampling/work/evidence \
  --json .cache/pl-assessment-new.json --markdown .cache/pl-report-new.md
make test
```

Os caminhos de saída devem ser novos: os scripts recusam sobrescrever resultados.
O replay exige árvore Git limpa e registra o commit produtor. Os snapshots
conservam 16 versões independentes do código/evidência; extraia `source.zip`
e `evidence.zip` numa pasta isolada. Nenhum resultado antigo foi substituído.

As versões v1–v5 conservam a auditoria inicial; v6–v10 conservam os primeiros
estudos dyádicos, neurais e caches, incluindo erros/execução interrompida.
v11 é o primeiro protótipo executável de envelope/perfis; v12 conserva a rodada
fortalecida completa; v13 conserva o protótipo de decisões forçadas **sem uma
nova campanha de tempos atribuída a ele**. v14 conserva o estudo neural final
e sete controles; v15 os três perfis compactos; v16 a avaliação final com mais
recursos e todos os relatórios/provas. Os produtores de cada fase estão nos
metadados, pois um snapshot pode conservar evidências anteriores adicionais.

O relatório novo é reproduzido offline com `utility_report.py`, capturas
`work/evidence/utility/neural-utility-v4`, `bulk-final-combined` e
`neural-v4-independent-geometry.json`. Os comandos exatos usados e os hashes
dos produtores estão em `work/evidence/utility/final-analysis-provenance.json`.
