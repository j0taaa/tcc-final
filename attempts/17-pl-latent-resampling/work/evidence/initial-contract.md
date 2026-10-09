# Reamostragem latente condicionada à seleção Plackett–Luce

Iniciada em 2026-10-08 a pedido do usuário. Estado: investigação, não conquista
confirmada. A nota recebida é preservada em `work/received-note.md`; os programas
citados nela não foram fornecidos. A implementação abaixo será independente.
O núcleo/contratos de produção permanecem como base de comparação.

## Oito critérios científicos

1. **Uso:** reduzir ruído em gradientes on-policy ao adaptar uma dLLM para
   JSON/DSL. Tokens propostos e descartados são latentes; os commitments e a
   ordem PL são observados. A saída é uma amostra condicional de IDs originais,
   usada no score da política original. Não é aceleração do decoder final.
2. **Significância:** candidato é o amostrador gramatical condicional com
   envelope fatorável, custo em `sqrt(k) log(kappa)` e correção racional exata.
   PL, Rao–Blackwellização, rejeição e aproximações exponenciais são conhecidos.
   A diferença para Beylkin–Monzón e envelopes clássicos ainda precisa ser
   delimitada; nem prioridade nem suficiência para publicação estão confirmadas.
3. **Adoção:** menos variância por trajetória neural, estritamente quando há
   variância latente. Comparar com o score completo, rejeição condicionada aos
   tokens com envelope `f(L)`, enumeração e Rao–Blackwellização exata onde cabem.
   Só há vantagem por tempo se custo vezes variância diminuir; não basta vencer
   um rejeitador que use desnecessariamente o limite 1.
4. **Matemática:** auditar redução PL, cobertura, moedas racionais, custos e
   identidade de covariância. A identidade isolada é antecedente. Uma prova
   comparativa contra amostradores competentes ainda está em investigação.
5. **Experimentos:** protocolo em `work/protocol.json`, congelado em Git antes
   das medições. Famílias construídas são oráculos de correção; os nove inputs
   JSON M34 completos são replays de modelo, não novos rollouts ou benchmark
   independente de treinamento. Todos os estados e recusas permanecem no relato.
6. **Custo:** incluir compilação, enclosures, componentes, amostragem, memória
   lógica e aritmética; separar primeira saída/lote. O replay exclui forward
   e backward, que não foram executados. Não converter redução de variância em
   melhor qualidade ou convergência sem uma ligação adicional.
7. **Objeções:** métodos gerais podem obter o mesmo envelope; enumeração pode
   vencer; taxas quase constantes favorecem rejeição simples; preparação pode
   dominar. Uma distribuição condicional exata não basta para PPO/GRPO com
   clipping. Suporte fixo e política original correta são hipóteses essenciais.
8. **Artigo:** ainda faltam revisão independente, anterioridade suficiente,
   vantagem de custo relevante e integração de treinamento. As verificações
   aqui não serão apresentadas como treinamento, prioridade ou prova de Lean.

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

Serão registrados após execução. O protocolo, os resultados desfavoráveis e a
nota original não serão substituídos para transformar uma perda em sucesso.
