# A31 — Reunir estados suficientes, preservando a lei nativa

Iniciada em2026-10-11. **Candidata teórica, não publicação confirmada.**
Nova pasta porque o contrato permite reunir históricos diferentes, algo
explicitamente proibido em A26/A30. Essas tentativas não serão alteradas.

## Oito critérios antes do protótipo

1. **Uso.** Lotes de JSONs/chamadas/DSLs de uma dLLM sob GLC, avaliados por
   um verificador/dry-run. Ordens diferentes de commitment podem chegar ao
   mesmo estado de decodificação e compartilhar novamente a coordenação,
   sem substituir parser, modelo ou distribuição individual do EPIC.
2. **Diferença.** Acoplamento de Markov chains, estratificação, potenciais de
   martingale e estado suficiente são antecedentes. A diferença candidata
   é a identidade finita de ganho ao REUNIR estados suficientes, comparada
   à referência competente que só coordena históricos completos iguais.
   Vale para toda pontuação da saída final, sem monotonicidade/ordenar pelo
   verificador. Não reivindicar as ferramentas clássicas ou parsing novo.
   Novidade e tamanho suficiente para artigo permanecem em investigação.
3. **Escolha.** Provar marginais originais, cobertura pass@K>=iid e variância
   da média <=baseline A30 de K estratos fixos. Para K=2, cobertura de todo
   verificador >=A30, com identidade explícita de ganho nas reuniões úteis.
   Comparadores: EPIC iid completo, estratificação só da raiz, A30, STMC,
   Array-RQMC, arithmetic/DAST e métodos de diversidade quando aplicáveis.
   Não alegar cobertura>=A30 para K>2 ou dominância sobre a A26 com m estratos.
4. **Prova.** Cadeia não homogênea de horizonte finito, kernel F_t(s,I,Z),
   tickets de K estratos, estado suficiente para kernel E saída terminal.
   Prova global por configuração, sem exigir árvore de históricos disjuntos.
   A identidade de covariância é soma de energias de encontros. Comparação
   A30 usa projetividade de K fixo e o primeiro histórico divergente.
5. **Testes.** Antes de modelo, enumerar toda aleatoriedade de cadeias pequenas,
   TODAS as propriedades terminais e scores, comparar iid, histórico e estado.
   Incluir contraexemplo quando o resumo omite informação de parada/verificador.
   Famílias construídas são oráculos/corolários, não medições práticas.
6. **Custo.** O mapa suficiente precisa ser auditado, não presumido. EPIC exige
   canvas, fase/bloco, agenda, palavras/EOS, rejeições cumulativas, política
   e namespace imutável; modelo stateless/frozen. Hashes não provam suficiência.
   Não criar forwards adicionais para coordenar; custo de chave, CPU/GPU,
   tabelas/cache, memória e recuperação entra inteiro em avaliação. Mais
   diversidade pode aumentar forwards únicos com caching; não ocultar isso.
7. **Objeções.** Canvas igual não basta; fases distintas ou budgets diferentes
   não se unem. Verificadores que dependem de detalhes históricos omitidos
   ficam fora do teorema; JSON/dry-run depende da saída final admitida. Sem
   encontros posteriores informativos, A31 iguala A30 em resultado e pode
   custar mais. Outro método clássico equivalente/mais barato pode refutar
   prioridade/utilidade. Não iniciar campanha para resgatar ganho inexistente.
8. **Artigo.** Falta conferir a diferença contra antithetic MCMC/STMC/rounding,
   terminar prova/oráculos, validar o resumo nativo e medir aplicação externa
   antes da confirmação independente. Não há revisão humana/aceitação nem
   conquista de geração geral. A prova tem comparação, não só correção.

## Preservação e contrato

A30v1:75d626c0acc1611909a788cf102abb2cc48ea17b, snapshot independente.
A31 poderá copiar referências pequenas dessa fonte CONGELADA, com hashes e
atribuição; não importará arquivos mutáveis de outra tentativa. EPIC permanece
o snapshot externo mantido. `work/theory-v1.md` é a primeira obrigação.

## Gate v1 executado

Quatro oráculos racionais independentes passam, incluindo todas as propriedades
terminais das cadeias pequenas, identidades de energia, ganhos estritos e um
contraexemplo ao resumo apenas por canvas. A suíte inteira passa118 testes
em65.916s (`make test`). Não são benchmarks de utilidade.

216/216 replays do EPIC pinado preservam literalmente IDs, EOS, rejeições e
saída completa/incompleta: três modos state/history/root, CPU/CUDA, coordenadas
first/entropy, temperaturas0/0.5/1 e orçamentos1/8. São logits FALSOS, não
execuções neurais:60 completos156 incompletos,648 chamadas falsas. O produtor
e hook têm hashes no JSON; drafts antes do ordinal estão preservados em
`work/evidence/query-ordinal-refinement/`, sem reatribuir as medições.

A prova escrita permite reunificação de estados realmente suficientes. Para
K=2, oferece identidade comparativa de pass@2 versus histórico e um corolário
de número esperado de verificações em retries. Não demonstra acerto semântico,
latência geral, priority ou suficiência para publicação. O próximo refinamento
pretende preservar literalmente a primeira resposta nativa antes de medir.

## V2: ancoragem e primeira trajetória

O lema de ancoragem em `work/anchoring-v2.md` retém o ticket nativo do primeiro
visitante e completa seu posterior de estrato. Três oráculos independentes
passam, incluindo todos os K<=3/W<=4 e ordens de chegada, preimages CPU/CUDA
por Fractions e refusas. A suíte121 passa64.878s.

`work/probe_anchor.py` valida216/216 primeiras trajetórias literais em pares
K=2 do EPIC real com heads FALSOS;978 chamadas falsas incluindo controles,
168 saídas completas nos432 candidatos,156 nós compartilhados. Todos os
hashes de produção conferem. O hook v1 e seus resultados não foram alterados;
o refinamento fica em `native_noise_v2.py`/`anchored_ledger.py`.
Não há ganho neural medido nem confirmação de publicação.

## V3: piloto neural externo concluído, sem vitória

Protocolo e inputs4038857, runner0a27a24, antes dos heads. Os16 pedidos BFCL
foram selecionados por hash do input, não pela resposta. EPIC público mais
recente continua no commit pinado; execução nativa completa, regular cover
batch/exact/DFA-free e recuperação habilitados para todos os controles.

Todos272 registros estão em `work/evidence/external-pilot-v3/`:528 trajetórias,
11.615 novos forwards LLaDA8B NF4,528 JSONs válidos,192 comparações integrais
da primeira trajetória sem divergência. As20 reuniões posteriores não
produziram vantagem de acerto nesta seed. Iid/root/history/state têm15/16
pass@2 em ambas configurações de temperatura0.5 e16/16 em ambas de1.
Controle determinístico15/16.

Não são os quatro seeds de desenvolvimento; o gate completo permanece
incompleto e a confirmação não foi acionada. A decisão de investigar outra
operação é registrada sem alegar impossibilidade nas seeds não executadas.
Nenhum caso foi removido/trocado, nenhuma perda foi apagada. O piloto teve
breve sobreposição de make check e pequeno screen NumPy; os timings são
diagnósticos, não confirmação competitiva. O audit é gerado dos dados,
inclusive status/IDs/output/rejeições/recovery/queries/forwards.
Suíte offline completa123 passa66.444s. Novidade/publicação continuam abertas;
este resultado não satisfaz o objetivo científico do usuário.
