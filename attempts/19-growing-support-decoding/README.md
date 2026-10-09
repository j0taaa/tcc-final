# Tentativa 19 — Seleção exata quando a dLLM propõe tokens novos

Iniciada em 2026-10-09 após a tentativa18 não encontrar ganho completo no
suporte congelado. Fontes independentes copiados de `15767f3`; nenhum import
depende do work mutável de18. Não substituir código/provas/resultados antigos.
Candidata primária predeclarada: `root_lex`; híbrido `root_speculative`
secundário. Confirmação nos seis casos frescos usa nove repetições, TODOS
os dezenove métodos; nenhum caso será escolhido por resultado.

Status: **rejeitada como vantagem principal neste protocolo**.

Foram executados 1.026 registros reais com MDLM/CUDA: 939 completos,
888 comparações exatas de suporte/decisões/saída, nenhuma divergência e
**0/18 configurações** com o ganho predeclarado de 20% em wall E CPU
frente a todos os controles concluídos. O melhor caso reduziu wall, mas
não cumpriu o custo de CPU. O critério não foi relaxado.
As reservas128 recusaram nove execuções por recursos, preservadas.
O desenvolvimento não autoriza ampliar esta candidata à confirmação fresca.
Dados, comandos, hashes e análise estão em
[work/evidence/development-decision.md](work/evidence/development-decision.md).

## Oito critérios e decisão anterior à implementação extensa

1. **Uso real:** preencher lacunas de JSON existente com dLLM. A cada novo
   contexto, ela pode preferir tokens ausentes do top16 inicial; restringir
   para sempre aquele conjunto perde essas propostas. Use união dos top16
   atuais com os anteriores nos slots ainda livres. Entrega o mesmo lote
   da política gulosa a cada forward, permitindo novas propostas do modelo.
2. **Relevância:** lexicografia/Earley/GAC/circuitos compilados são conhecidos.
   A candidata é uma integração enxuta com equivalência da política no domínio
   adaptativo e eventual custo menor que manter/reconstruir representação de
   todas as conclusões. Não é uma nova teoria geral, nem prioridade confirmada.
   O ganho precisa sobreviver a controles preparados para ativar tokens.
   Se for apenas mais um cache ou ajuste sem ganho completo, rejeitar.
3. **Escolha:** economia no decoder inteiro, mesma trajetória no mesmo regime.
   Comparar com todos os dezesseis métodos de18 adaptados às expansões, mais
   SAT com reservas32/64/128 (informações disponíveis igualmente no softmax).
   Reservas incluem tokens ainda inativos, mas NÃO os permitem nas consultas.
   Só reconstruir quando um candidato atual sai da reserva; dar maior orçamento
   aos controles. Não confundir vantagem com limitação artificial de tabelas.
4. **Matemática:** união é determinada pelo mesmo canvas/softmax e independente
   do seletor. Expansão não invalida um completamento já viável; um commit
   certificado conserva existência no passo seguinte. Por indução, métodos
   equivalentes por passo produzem a mesma trajetória. Lex resolve o lote em
   uma otimização por passo; não há garantia de que isso seja fisicamente mais
   barato que circuitos reutilizáveis. Provar esse benefício requer custo
   comparativo delimitado, não apenas correção de Earley conhecido.
5. **Experimentos honestos:** protocolo antes dos novos forwards. Mesmos seis
   documentos de desenvolvimento e doze de avaliação-refinamento, todas as
   máscaras4/8/16, três ordens rotacionadas, CPU/GPU. Nenhum documento escolhido
   por vitória. Se o desenvolvimento passar, confirmar também nos seis últimos
   documentos por hash, nunca executados em18. Todos os fracassos permanecem.
   Critério original: >=20% de redução mediana wall E CPU contra todo controle
   concluído, sinal favorável nas três repetições. Ausência de confiança
   estatística ou publicação/revisão humana não pode virar certeza mundial.
6. **Custo completo:** novos suportes, reservas, normalização preparada,
   construção, gramática/índices, ativação, queries, commits, output, memória,
   inteiros e TODOS os forwards. Carregamento/aquecimento fixo comum permanece
   registrado fora do decoder do serviço preparado. Sem esconder compilação
   numa consulta amortizada. Suporte finito declarado, EOS ausente e nenhum
   acerto semântico geral. O regime adaptativo não é replay do estático.
7. **Objeção:** reservas/circuitos com potenciais zero podem tornar a otimização
   repetida desnecessária; FactorDLM já explora compilação/reavaliação. Uma
   implementação gramatical incremental mais competente pode ganhar. Não
   alegar superioridade sobre toda codificação por fatores ou EPIC. Crescimento
   de suporte pode aumentar memória e inviabilizar TODOS os métodos.
8. **Artigo:** novidade teórica/publicabilidade/revisão ausentes. Precisamos
   demonstrar ganho real no mesmo contrato, conservar todos os resultados e
   delimitar por que expansão é necessária. Apenas funcionamento/testes não
   cumprem o objetivo. Se houver ganho, consolidar antes de ampliar o projeto.

A tentativa18 mostrou por que NÃO assumir ganho de uma consulta em suporte
congelado: propagação clássica reutilizável ganhou após fortalecer controles.
Esta hipótese muda a operação para candidatos atuais do modelo, e declara isso
antes de medir. Não muda documentos nem remove os casos fáceis/desfavoráveis.

Antecedentes: [Opedal et al.2023](https://aclanthology.org/2023.acl-long.204.pdf),
[Quimper–Walsh2009](https://arxiv.org/pdf/0903.0470),
[FactorDLM](https://arxiv.org/abs/2609.32900),
[EPICv2](https://arxiv.org/html/2606.00722v2).
