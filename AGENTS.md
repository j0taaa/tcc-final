# Instruções de trabalho

## Orientação

- Leia `README.md`, `docs/status.md` e a pendência pertinente em `TASKS.md`.
- Use `docs/architecture.md` para os contratos e `docs/reproducing.md` para comandos.
- O histórico anterior à simplificação está em `docs/history/README.md`.
  Documentos históricos explicam evidências antigas; não são uma fila de trabalho.
- A meta científica positiva continua aberta. A71 é uma candidata em investigação;
  não reabra aplicações encerradas para tentar obter um resultado favorável.
- O usuário quer um TCC de impacto que fortaleça sua candidatura ao mestrado:
  contribuição própria, teoria matemática e utilidade geral com melhoria
  demonstrável, viável sem treinamento em uma RTX 3080 Ti de 12 GB.
  Correções de implementação e integrações conhecidas servem como controles;
  não bastam para selecionar o tema central. Só ampliar uma direção quando
  houver justificativa científica específica para esse objetivo.

## Mudanças

- Prefira uma solução pequena. Não crie camadas, documentos, comandos ou
  infraestrutura sem um consumidor concreto. Remova código sem uso quando seguro.
- Preserve APIs utilizadas, a independência das referências Python/Rust e os
  caminhos dos dados necessários à reprodução. Código específico de modelo fica
  na integração, não no solver genérico.
- Não edite o baseline em `vendor/EPIC-Decoding` para favorecer comparações.
  Preserve licenças, fontes externas e seu manifesto.
- Não versione modelos, caches, credenciais nem grandes traces novos. Não altere
  arquivos locais não relacionados à tarefa.
- O Git preserva versões: use commits para congelar fontes, protocolos e dados.
  Não volte a duplicar o repositório em ZIPs por tentativa ou a acumular recibos
  de verificações rotineiras. Registre comandos e resultados no commit/PR.
- Execute as verificações pertinentes. Commit e push normal para o upstream
  configurado fazem parte da conclusão de alterações; confirme a sincronização.
  Não mude de branch, reescreva histórico ou force-push sem pedido explícito.

## Contratos científicos

- Declare a operação e suas hipóteses. Conjectura, prova escrita, especificação
  Lean, teste de correção, observação de modelo e medição são evidências distintas.
  Lean não verifica todo o software nem estabelece prioridade científica.
- Preserve tokens originais, aliases, bytes, posições fixadas e política EOS/PAD.
  Suporte podado é `exact_on_support`, não exatidão no vocabulário completo.
- `OPTIMAL`, inviabilidade no suporte, timeout, entrada não suportada e erro são
  resultados diferentes. Recusa por recursos é inconclusiva.
- MWPC maximiza o peso declarado por passo. Exige testemunho reconstruível e
  validação independente dos IDs, multiplicidades e objetivo. Não implica
  otimização da trajetória inteira.
- O posterior mantido usa gramáticas LL(1) verificadas, slots finitos e EOS ausente.
  Reponderação, contração de suporte e novos commitments compatíveis permitem
  reutilização; expansão, liberação de posições ou mudança de semântica exigem
  nova preparação. Nunca renormalize silenciosamente uma cauda omitida.
- Amostragem/massa exatas usam inteiros ou racionais. Separe a lei produto
  congelada de um passo da trajetória nativa do modelo e sintaxe de semântica.
- Não sobrescreva fontes/dados científicos congelados para corrigir ou melhorar
  um resultado. Correções ficam separadas, com a origem e o erro explícitos.

## Pesquisa nova

Antes de um protótipo extenso, escreva na própria tentativa: operação real,
diferença para o antecedente mais próximo, benefício verificável, hipóteses e
prova, comparador competente, custo completo, objeções e o que ainda falta.
Uma implementação correta de um método conhecido não estabelece avanço próprio.

Congele protocolos antes de medir; preserve perdas, recusas e interrupções.
Não mude casos, seeds, métricas ou controles depois dos dados para salvar um gate.
Contabilize preparação, modelo, RNG, consultas, saída, memória e custo em bits.
Não invente revisão humana, resultados, prioridade ou aprovação acadêmica.
Não contate pessoas nem submeta trabalhos sem instrução explícita.
