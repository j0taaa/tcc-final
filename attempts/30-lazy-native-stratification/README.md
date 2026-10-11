# A30 — Estratificação preguiçosa da aleatoriedade do decoder nativo

Iniciada em2026-10-11. **Hipótese científica, não conquista confirmada.**
Mantém o EPIC pinado intacto. Não herda timings nem evidência neural de A26.

## Oito critérios antes da implementação

1. **Uso real.** Produzir um lote de JSONs/DSLs com uma dLLM e um decoder
   gramatical já existente; um verificador/dry-run seleciona uma saída útil.
   A operação pretende aumentar cobertura com K candidatos, mantendo a lei
   de cada execução original, inclusive recuperação, EOS e decisões futuras.
   O verificador não é consultado para coordenar as amostras.
2. **Diferença/relevância.** Estratificação, Maclaurin e redução de variância
   são clássicas. A26 já formula dominância em históricos completos, mas
   necessita conhecer o tamanho do grupo no momento da transição e seu
   protótipo depende de unranking gramatical. A30 pergunta se tabelas locais
   de K estratos permitem execuções seriais/assíncronas, visitantes em número
   desconhecido e uma única coordenada do ruído NATIVO, sem posterior novo.
   A diferença candidata é esse contrato operacional com dominância finita
   para todo verificador. Prioridade/suficiência acadêmica ainda em aberto.
3. **Por que escolher.** Comparador principal: K execuções iid do MESMO EPIC
   completo, com os mesmos recursos, caching e política. A prova pretendida
   é pass@K nunca inferior e variância nunca maior, sem mais candidatos ou
   chamadas de modelo para a coordenação. A26 síncrona, STMC/Array-RQMC,
   arithmetic sampling, DAST e samplers sem reposição são alternativas fortes;
   não alegar dominância sobre todos eles ou aceleração física universal.
4. **Matemática sem código.** Provar primeiro o lema para qualquer subconjunto
   de m dos K rótulos, inclusive W não divisível por K. Depois, indução em
   árvore de históricos completos, com kernel arbitrário dependente de h.
   O corolário preserva o decoder CFG nativo; não pressupõe logits estáveis,
   gramática não ambígua ou exatidão de seu posterior, pois não troca a política.
5. **Experimentos honestos.** Primeiro oráculos racionais de TODAS as decisões
   aleatórias e verificadores em pequenas árvores; não benchmarks favoráveis.
   Um protocolo externo de utilidade/latência/qualidade deverá ser congelado
   antes de novos forwards. Preservar recusas, erros e ganhos nulos/negativos.
6. **Custo completo.** Coordenação tem permutação esparsa/tabela por histórico, sorteio,
   cálculo inteiro, escolha da coordenada, transferência e escrita no tensor.
   Esperança da soma de custos individuais é preservada; forwards únicos com
   cache podem AUMENTAR. Não ocultar essa diferença, memória ou serialização.
   A estratificação de uma só coordenada pode ter ganho ínfimo. CPU/GPU devem
   receber exatamente sua transformação original do ticket aleatório.
7. **Objeções.** Históricos divergentes nunca são reunidos. Não estratificar
   coordenadas independentes simultaneamente: paridade dá contraexemplo.
   Não usar fase comum, estrato fixo por rótulo ou verificador/gabarito para
   escolher coordenadas. Wall time afetado pelo lote não preserva o kernel.
   Uma redução a Array-RQMC/STMC ou ganho irrelevante derruba o protagonismo.
   Uma vantagem fraca sobre iid, isoladamente, não satisfaz o objetivo.
8. **Artigo.** Faltam oráculos, integração nativa, magnitude/custo em aplicação
   independente e revisão delimitada da novidade. Prova escrita não é prova
   de software, fonte do RNG ou revisão humana. Nenhum resultado de publicação
   é prometido. A30 não altera o artigo principal antes de passar esses gates.

## Contrato e arquivos

`work/theory-v1.md` define o contrato e a prova candidata. `work/antecedents-v1.md`
registra antecedentes e fronteiras. `work/ledger.py` é a referência inteira;
`work/native_noise.py` é um adaptador opt-in e serial do decoder pinado. A
permutação usa decisões adiadas, sem O(K) itens em históricos com um visitante.
`tests/test_lazy_stratification.py` enumera decisões aleatórias independentemente.
`work/probe_native.py` reproduz trajetórias do EPIC com cabeças pequenas falsas,
incluindo rejeições, EOS, aliases e CPU/CUDA; não é experimento neural. Tudo
fica isolado aqui;
nenhum código mutável de outra tentativa ou alteração de vendor é permitida.

Para um lote, K é fixado ANTES da primeira execução. Uma tabela independente
é criada por histórico completo. Ela atende cada rótulo uma única vez e não
precisa saber quem mais chegará. A mesma tabela não pode ser usada em outro
lote ou em históricos que apenas terminem no mesmo canvas.

A auditoria da integração encontrou estado oculto relevante: rejeições
cumulativas mudam o orçamento de recuperação mesmo com canvases iguais.
O adaptador registra esses checkpoints, além dos inputs completos. Não
interpretar o proxy de inputs, isoladamente, como chave suficiente.

## Evidência inicial e limites

Cinco oráculos racionais passam em15.980s; toda a suíte offline passa114
testes em56.494s (`make test`). A prova local cobre qualquer subconjunto de
rótulos com K fixo; a execução serial/intercalada tem a mesma lei pequena.

`PYTHONPATH=vendor/EPIC-Decoding:. .venv-live/bin/python -m
attempts.30-lazy-native-stratification.work.probe_native --output
attempts/30-lazy-native-stratification/work/evidence/native-correctness-v1.json`
passa72/72 replays literais nativos:20 completos,52 com `complete=False`,
todos com rejeição,216 chamadas a cabeças FALSAS (referência+candidata).
Há chaves com duas rejeições prévias; IDs0/3 emitem o mesmo texto e os IDs
originais ainda coincidem na reprodução. É replay determinístico injetando
o mesmo valor escalar nativo, não estimação da lei por frequências. Fonte,
CPU/CUDA, configurações e hashes do produtor estão no JSON.

Não houve forward neural, campanha de velocidade ou acerto semântico externo.
Um controle importante será estratificar APENAS o primeiro ruído: já fornece
dominância fraca sobre iid por estratificação clássica e pode obter a maior
parte do ganho com menos infraestrutura. Também é necessário investigar se
um resumo Markoviano SUFICIENTE do estado permite coalescer históricos sem
perder a garantia para verificadores da saída final. O contrato conservador
de A30 permanece intacto; nenhum teorema autoriza juntar canvases apenas.
