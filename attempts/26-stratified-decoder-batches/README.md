# A26 — Lotes de decodificação com dominância sobre gerações independentes

Base preservada: `99e965ea27e0588f189221d8b61de88633dec340`.
Investigação iniciada em 2026-10-10 por pedido de uma vantagem **geral**.
Não modifica o posterior, o EPIC, os resultados24/25 ou a política de um decoder.

## Contrato científico e oito perguntas

1. **Uso real.** Gerar K configurações, preenchimentos JSON ou chamadas sob
   uma GLC para um programa testar e escolher. O consumidor pode executar um
   dry-run, conferir um schema ou pontuar candidatos. A dLLM continua propondo
   conteúdo; o verificador não fornece respostas ao sampler. Melhorar a chance
   de encontrar um candidato útil com K tentativas é diferente de apenas garantir
   JSON válido. O resultado também se aplica à geração iterativa inteira.
2. **Significância e antecedente.** Estratificação proporcional, unranking de
   gramáticas ponderadas e a desigualdade média geométrica/aritmética são
   conhecidos. Arithmetic Sampling (Vilnis2023), DAST (Sato2026), STMC
   (Roohi2020), SMG (Li2020) e ODD (Lamont2026) são comparadores intelectuais
   obrigatórios. Não reivindicamos inventar estratificação. A contribuição
   candidata é uma construção exata sobre o circuito de tokens originais e
   estratificação **somente dentro de históricos idênticos**, com dominância
   finita para qualquer verificador final, sem alterar a distribuição individual
   nem supor monotonicidade do verificador. A prioridade desse recorte e sua
   suficiência para publicação permanecem abertas; provar o resultado não
   transforma automaticamente princípios conhecidos em nova teoria.
3. **Por que escolher.** Frente a K execuções iid do MESMO decoder, provar
   simultaneamente: mesma lei de cada candidato; chance de algum passar em
   qualquer verificador nunca menor; melhor pontuação do lote domina
   estocasticamente; variância da média nunca maior. A desigualdade pode ser
   igualdade. Não é superioridade geral sobre beam search, sampling sem
   reposição, EPIC com outra política ou todos os algoritmos possíveis.
4. **Prova sem código.** `work/theory.md` define o kernel e prova as propriedades
   por indução numa árvore de históricos. O passo local usa estratos de igual
   massa com sorteios independentes, permutados uniformemente. Inteiros evitam
   arredondamento, inclusive quando K não divide a massa. Um corolário relaciona
   a construção a um posterior CFG e às transições reais de uma dLLM.
5. **Experimentos honestos.** A garantia vem da prova, não de um benchmark.
   Oráculos devem enumerar TODAS as propriedades binárias de espaços pequenos,
   leis conjuntas e matrizes de covariância; incluir perdas frente a outros
   métodos e erros de uma implementação superficial. Demonstração com captura
   real é replay declarado, não novos forwards ou ganho semântico medido.
6. **Custo inteiro.** Ambos os métodos recebem a mesma preparação e kernel.
   O unranking paga a avaliação inside, CDFs e divisões em inteiros de B bits;
   estratificação acrescenta O(K) operações em B+log K bits e permutação.
   O custo esperado SOMADO por candidato é preservado, mas esse argumento
   não inclui coordenação e não prova wall-time menor. Compartilhar forwards
   repetidos pode favorecer iid: mais diversidade pode visitar mais históricos
   distintos. Comparações devem pagar esse efeito; não alegar igualdade do
   custo de forwards únicos ou da latência paralela.
7. **Objeções.** Se o decoder é determinístico, não há ganho. Se a decisão
   final não varia entre estratos, pode haver igualdade. Um verificador que
   pontua sequências distintas como equivalentes pode apagar diversidade.
   Estratificar tokens/tempos independentemente ou juntar históricos diferentes
   NÃO tem automaticamente estas garantias. Uma aplicação que só quer um
   candidato não ganha. Técnicas clássicas capazes de gerar os mesmos lotes
   compartilham o benefício; não esconder isso.
8. **Artigo defensável.** Ainda exige delimitar a diferença específica para
   os antecedentes, revisão humana (ausente), aplicação e avaliação de custos
   se houver alegação de velocidade. Manter prova escrita, verificação
   mecanizada selecionada, oráculo e replay separados. Não substituir o
   protagonista24 por esta direção antes dessa auditoria.

## Critério de decisão

Falha de preservação marginal ou algum verificador com pass@K inferior ao iid
derruba a construção admitida. Falha de novidade derruba uma reivindicação de
nova teoria, mas não a validade da vantagem operacional. Sem vantagem estrita
em uma operação admitida, a proposta não atende ao pedido. Sem custo físico
medido, não escrever que gerações ficaram mais rápidas. Não reduzir o conjunto
de verificadores para ocultar contraexemplos.

## Refinamento v2 — protocolo antes da execução

O primeiro replay (`work/evidence/replay-v1.json`) tem massa válida zero no
top16. Ele permanece preservado e não recebe crédito funcional. V2 usa o
MESMO documento/canvas/head público escolhido antes dos resultados24, todos
os50258 IDs do vocabulário original e os denominadores completos. IDs sem
emissão ordinária não podem completar JSON, mas sua probabilidade permanece
no denominador; EOS continua ausente. Não inserir IDs do texto de origem.

`work/replay_full.py` usa cópias independentes e hashadas de cinco arquivos
clássicos de A24/v8. A ponte `layer_bridge.py` apenas representa a mesma soma
de caminhos como circuito de ranks. Um sexto oráculo compara todos os tickets
em exemplos pequenos com `json.loads`, incluindo IDs aliases, tokens prefixos,
posições fixas, pesos zero e emissões não suportadas.

Regra congelada: seed2026101026;32 candidatos iid e32 estratificados; ambos
recebem o MESMO circuito. Todos os candidatos devem preservar IDs fixos e
passar UTF8/JSON. Depois de congelar o circuito, o auditor calcula exatamente
a probabilidade de reconstruir os IDs da fonte para K=2,8,32, sem orientar o
sampler. A fonte é evidência de um evento, não um gabarito semântico de geração.
Guardar todos os resultados, inclusive igualdade, massa zero e recusa. Limites
intrínsecos:1M arestas,200k estados,50M termos,120s de preparação de pilhas.
Não há campanha de velocidade, seleção de casos ou novos forwards. Timings
de uma execução são descritivos, com preparação e emissão registradas.

Comando de reprodução (usar outro caminho para não sobrescrever evidências):

```bash
.venv/bin/python -m attempts.26-stratified-decoder-batches.work.replay_full \
  --packet attempts/24-certified-depth-approximation/work/evidence/first-full-head-v2/packet.zip \
  --output /tmp/a26-full-replay.json
```
