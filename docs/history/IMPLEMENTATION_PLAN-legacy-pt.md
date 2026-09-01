# Plano completo de implementação

## 1. Objetivo prático

A implementação deve transformar a formulação teórica do TCC em um decoder executável que, em uma etapa de denoising, receba:

- o canvas parcialmente mascarado;
- as posições já comprometidas;
- as distribuições ou logits produzidos pelo dLLM;
- um conjunto de propostas ponderadas;
- uma CFG;
- uma representação finita das alternativas de token disponíveis em cada slot;

E devolva:

- o subconjunto de propostas de maior peso compatível com alguma conclusão válida;
- uma sequência de tokens testemunha;
- o caminho lexical/gramatical que certifica a validade;
- o valor ótimo;
- o escopo exato da garantia;
- diagnósticos de tempo, memória, tamanho do lattice e eventual fallback.

O resultado não deve ser apenas “válido”. Quando o status for `OPTIMAL`, o programa deverá fornecer evidências suficientes para reconstruir e verificar independentemente que:

1. a testemunha respeita o canvas atual;
2. a testemunha cabe no número real de slots;
3. sua detokenização está de acordo com a interface escolhida;
4. a saída pertence à linguagem da CFG;
5. todas as propostas retornadas coincidem com a testemunha;
6. o score retornado é exatamente a soma dos pesos dessas propostas;
7. nenhuma outra conclusão representada possui score maior.

O último item é garantido pelo algoritmo e validado empiricamente, em instâncias pequenas, contra força bruta.

---

## 2. Decisões de escopo recomendadas

### 2.1 Base de código

A implementação deverá partir de um repositório com o EPIC fixado como submódulo somente-leitura. Isso evita recriar:

- wrappers de modelos;
- loop de denoising;
- gramáticas e tarefas;
- validação CFG já existente;
- infraestrutura Python/Rust e bindings;
- scripts de avaliação;
- baselines serial e heurístico.

O fork deve registrar o commit exato do upstream e preservar licenças e avisos de terceiros. O método novo deve ser adicionado como uma estratégia separada, e não substituir silenciosamente o EPIC.

### 2.2 Estratégias de compromisso

A interface de execução deverá admitir, no mínimo:

```text
serial   -> valida e compromete propostas uma por uma;
epic     -> usa a seleção heurística do EPIC;
exact    -> usa o novo otimizador MWPC.
```

Essa separação é necessária para testes de regressão e comparações justas.

### 2.3 Interface lexical obrigatória

A implementação obrigatória deve usar uma **CFG byte-level** como primeira interface tokenizer-aware completa. Cada token do modelo será convertido em sua emissão exata de bytes, e o caminho de bytes será reconhecido pela CFG.

Essa escolha mantém as propriedades importantes:

- tokens podem emitir vários bytes;
- fronteiras de tokens não precisam coincidir com fronteiras sintáticas;
- token IDs diferentes que geram os mesmos bytes continuam distinguíveis;
- cada caminho usa exatamente um token por slot;
- pesos e proveniência permanecem ligados ao token original.

Um lexer determinístico que produz categorias como `IDENTIFIER` ou `NUMBER` será tratado como extensão posterior. Começar diretamente por um lexer genérico aumenta muito o risco porque exige maximal munch, prioridades, lexemas atravessando fronteiras de tokens e transporte de estado lexical.

### 2.4 Suporte finito e significado de “exato”

Nos testes sintéticos pequenos, todas as alternativas do vocabulário reduzido serão representadas. Nesses casos, a solução é exata para todo o problema definido.

Em um modelo real, o lattice provavelmente utilizará top-`K` alternativas por posição. Nesse caso, a nomenclatura obrigatória será:

```text
exact_on_support(top_k=K)
```

Nunca se deve afirmar que o resultado é ótimo sobre todo o vocabulário quando alternativas foram removidas. O resultado precisa carregar metadados sobre:

- valor de `K`;
- tokens especiais adicionados ao suporte;
- posições consideradas;
- expansão adaptativa de suporte;
- qualquer poda aplicada.

### 2.5 Conjunto de propostas

A política inicial deverá reproduzir a semântica do schedule usado pelo decoder:

1. o modelo produz uma proposta principal para cada posição mascarada;
2. as posições são ordenadas pela confiança usada pelo schedule;
3. as primeiras `k_s` posições da etapa formam o conjunto candidato `C`;
4. cada posição candidata contribui com uma proposta `(posição, token, peso)`;
5. o lattice também contém alternativas de peso zero para permitir que o parser encontre uma testemunha sem aceitar aquela proposta;
6. o solver escolhe o melhor subconjunto de `C`.

Assim, o tamanho do lote retornado nunca supera `k_s` e a comparação com o EPIC utiliza o mesmo conjunto de candidatos.

A implementação deve aceitar pelo menos dois esquemas de peso:

- `unit`: todas as propostas têm peso 1, maximizando cardinalidade;
- `confidence`: o peso é uma utilidade não negativa derivada da confiança do modelo.

Uma soma de probabilidades deve ser descrita como utilidade de preservação, não como probabilidade conjunta da sequência.

### 2.6 Garantia por etapa

A garantia de otimalidade é local à etapa atual. Comprometer um lote muda os logits futuros; portanto, a implementação e a redação não devem alegar que o decoder otimiza toda a trajetória de denoising.

---

## 3. Arquitetura recomendada

A implementação deverá separar cinco níveis.

### 3.1 Orquestração em Python

Responsável por:

- receber logits;
- gerar propostas;
- escolher o suporte top-`K`;
- construir o lattice;
- chamar o solver;
- validar o resultado;
- comprometer tokens;
- registrar métricas;
- aplicar fallback explícito.

Estrutura sugerida:

```text
constrained_diffusion/
  exact_commit/
    __init__.py
    types.py
    proposal_policy.py
    support.py
    token_lattice.py
    byte_lattice.py
    solver.py
    validator.py
    decoder.py
    profiling.py
    reference/
      token_aligned.py
      graph_parser.py
      brute_force.py
```

### 3.2 Implementação de referência em Python

Deverá ser pequena, legível e independente do dLLM. Ela existe para:

- tornar a semântica executável cedo;
- facilitar depuração;
- servir de oráculo diferencial para Rust;
- comprovar que os casos pequenos coincidem com força bruta.

Ela não precisa ser rápida e não deve usar GPU.

### 3.3 Solver de produção em Rust

Responsável por:

- parsing max-plus sobre um DAG terminal ponderado;
- armazenamento de backpointers;
- reconstrução do caminho e da derivação;
- timeout explícito;
- validação estrutural do grafo;
- retorno de um certificado estável.

Módulo sugerido:

```text
rustformlang/src/cfg/weighted_graph.rs
```

### 3.4 Bindings Python/Rust

Os bindings deverão ser finos. Eles convertem:

- nós, arcos, labels e pesos Python para structs Rust;
- resultado Rust para um objeto Python estruturado.

Não devem conter uma segunda implementação do algoritmo.

### 3.5 Integração com o EPIC

O ponto de integração inicial é o trecho do loop em que o EPIC:

- calcula o token argmax por posição;
- calcula confiança;
- seleciona as posições que a etapa pretende transferir;
- chama a seleção paralela heurística;
- recorre ao fallback serial.

O novo fluxo deverá chamar `solve_exact_commit(...)` nesse ponto quando `commit_strategy=exact`.

---

## 4. Contratos de dados

Antes de implementar algoritmos, devem ser criados tipos explícitos.

### 4.1 Proposta

```text
Proposal
  proposal_id: inteiro único
  position: índice absoluto no canvas
  token_id: token do vocabulário
  weight: número finito não negativo
  model_confidence: valor opcional para análise
```

IDs são necessários porque duas propostas podem coincidir em posição e token, mas ainda serem objetos distintos.

### 4.2 Escopo de suporte

```text
ExactnessScope
  kind: full | top_k | explicit
  top_k: inteiro opcional
  vocabulary_size: inteiro
  included_special_tokens: lista
  adaptive_expansions: lista
  pruning_description: texto opcional
```

### 4.3 Arco de token

```text
TokenArc
  token_edge_id
  slot
  token_id
  source_boundary
  target_boundary
  emitted_bytes
  weight
  matched_proposal_ids
```

### 4.4 Arco terminal expandido

Depois da expansão byte-level:

```text
TerminalEdge
  edge_id
  source_state
  target_state
  terminal_byte
  weight
  provenance_token_edge_id opcional
  matched_proposal_ids
```

O peso e a proveniência devem aparecer uma única vez no caminho correspondente ao token, para evitar dupla contagem quando um token contém vários bytes.

### 4.5 Resultado

```text
ExactCommitResult
  status
  objective_value
  selected_proposal_ids
  witness_token_ids
  witness_terminal_labels
  witness_graph_edge_ids
  exactness_scope
  diagnostics
```

Statuses mínimos:

```text
OPTIMAL
INFEASIBLE_ON_SUPPORT
TIMEOUT
UNSUPPORTED
ERROR
```

O código não deve usar `None` para representar indistintamente todos esses casos.

---

## 5. Etapa 0 — congelar e reproduzir o baseline

Antes de adicionar o algoritmo:

1. criar o fork;
2. registrar URL e commit do EPIC upstream;
3. criar um ambiente limpo;
4. compilar os bindings Rust;
5. executar os testes existentes;
6. executar ao menos um smoke test sem restrição e um restrito, se os artefatos estiverem disponíveis;
7. registrar falhas preexistentes antes de qualquer alteração;
8. criar uma tag ou commit de baseline.

Esse passo impede que um problema já existente seja atribuído ao método novo.

Também devem ser registrados:

- Python;
- Rust;
- compilador;
- CUDA;
- PyTorch;
- CPU;
- RAM;
- GPU e VRAM;
- sistema operacional.

---

## 6. Etapa 1 — versão token-aligned

### 6.1 Objetivo

Construir o caso mínimo em que cada token já é um terminal da CFG.

### 6.2 Gramática

A implementação deverá receber uma CFG e convertê-la para uma forma adequada:

- produções terminais `A -> a`;
- produções binárias `A -> B C`;
- tratamento documentado de `epsilon`;
- eliminação ou fecho de produções unitárias;
- preservação do símbolo inicial.

A conversão deve possuir testes independentes. Não se deve assumir que uma função existente preserva exatamente a semântica necessária sem verificar.

### 6.3 Score lexical

Para cada posição `i` e token `a`:

```text
score(i, a) = -infinito, se a posição estiver fixada em outro token;
score(i, a) = soma dos pesos das propostas em i que propõem a;
score(i, a) = 0, se a for permitida e não satisfizer proposta alguma.
```

### 6.4 CKY max-plus

Implementar uma tabela:

```text
D[A, i, j]
```

Ela guarda o melhor score derivável por `A` no intervalo `[i, j)`.

Cada atualização deve guardar um backpointer:

- terminal escolhido; ou
- produção binária e ponto de divisão.

### 6.5 Saída

O backtracking deve reconstruir:

- a sequência testemunha;
- as propostas satisfeitas;
- o score reconstruído.

### 6.6 Validações obrigatórias

- posições fixadas permanecem iguais;
- a CFG aceita a testemunha;
- cada proposta selecionada coincide com a testemunha;
- o score é a soma dos pesos selecionados;
- inviabilidade é reportada explicitamente;
- empates não causam não determinismo acidental nos testes.

Essa etapa deve funcionar sem modelo, tokenizer, GPU ou EPIC.

---

## 7. Etapa 2 — oráculos de força bruta

Devem existir dois oráculos independentes.

### 7.1 Oráculo por conclusões

Para vocabulários e canvases pequenos:

1. enumerar todas as sequências permitidas;
2. filtrar as que respeitam posições fixadas;
3. testar pertencimento à CFG;
4. calcular a recompensa;
5. obter o máximo.

### 7.2 Oráculo por subconjuntos

1. enumerar todos os subconjuntos de propostas;
2. verificar se cada subconjunto possui alguma conclusão testemunha;
3. encontrar o subconjunto compatível de maior peso.

Os três valores devem coincidir:

```text
ótimo CKY = ótimo por conclusões = ótimo por subconjuntos.
```

### 7.3 Testes aleatórios

Gerar milhares de casos pequenos com:

- gramáticas simples aleatórias;
- pesos inteiros;
- posições fixadas;
- propostas conflitantes;
- propostas duplicadas;
- gramáticas ambíguas;
- instâncias inviáveis;
- empates.

O seed de qualquer falha deve ser impresso e transformado em teste de regressão.

A integração com o modelo não deve começar enquanto essa etapa não apresentar concordância total.

---

## 8. Etapa 3 — parser ponderado genérico sobre DAG

### 8.1 Motivo

O CKY sobre uma string não basta para representar alternativas de tokenização. O próximo componente deve receber um grafo acíclico terminal genérico, sem conhecer dLLMs.

### 8.2 Estrutura do grafo

```text
WeightedTerminalDAG
  number_of_states
  start_state
  final_states
  terminal_edges
  topological_order
```

Cada arco possui:

- origem;
- destino;
- terminal;
- peso;
- ID;
- proveniência opcional.

### 8.3 DP

A tabela passa a ser:

```text
D[A, p, q]
```

Ela representa o melhor caminho de `p` a `q` derivável por `A`.

A inicialização usa arcos terminais. A combinação binária considera estados intermediários `r`.

### 8.4 Epsilon

O solver principal deve operar sobre um DAG terminal sem epsilon, sempre que possível. Caso a construção produza arcos epsilon, deve haver uma fase explícita de normalização:

- calcular fechos epsilon ponderados no DAG;
- transportar peso e proveniência;
- saturar os arcos terminais;
- preservar backpointers para reconstruir o caminho original;
- tratar separadamente o caso de palavra vazia.

Timeouts e ciclos devem ser detectados. Não se deve executar relaxamento indefinidamente.

### 8.5 Implementações

Primeiro, implementar uma versão Python de referência. Depois, implementar a versão Rust de produção. Por fim, executar testes diferenciais:

```text
Python reference == Rust production == brute force de caminhos
```

A igualdade obrigatória é de score e validade do certificado. Testemunhas diferentes são permitidas em empates.

---

## 9. Etapa 4 — lattice finito de tokens

### 9.1 Camadas

Para um canvas com `n` slots, criar fronteiras:

```text
q_0, q_1, ..., q_n
```

Cada alternativa no slot `i` cria um caminho de `q_i` a `q_(i+1)` correspondente a exatamente um token.

### 9.2 Posições fixadas

Uma posição já comprometida contém somente o token atual. Qualquer tentativa de oferecer outro token deve falhar na validação de entrada.

### 9.3 Posições mascaradas

O suporte é obtido dos logits:

- top-`K` tokens da posição;
- token da proposta, obrigatoriamente incluído;
- tokens especiais necessários pela semântica de fim;
- alternativas adicionais inseridas por expansão adaptativa.

### 9.4 Peso

Somente o arco do token que coincide com uma proposta recebe o peso correspondente. As demais alternativas recebem zero.

Se existirem múltiplas propostas com a mesma posição e token, seus pesos e IDs são agregados naquele arco.

### 9.5 Proveniência

Dois token IDs que emitem os mesmos bytes não podem ser colapsados sem preservar qual token foi escolhido. Na primeira implementação, use caminhos distintos mesmo que isso aumente o lattice. Compartilhamento por trie só deve ser adicionado depois de testes que comprovem a preservação da proveniência.

---

## 10. Etapa 5 — detokenização exata e expansão para bytes

### 10.1 Auditoria do tokenizer

Antes de escolher o modelo final, verificar se o tokenizer permite mapear cada token para bytes de forma composicional.

A propriedade desejada é:

```text
bytes(token_1) + ... + bytes(token_n)
=
bytes(detokenização([token_1, ..., token_n])).
```

Isso deve ser testado sobre:

- sequências aleatórias;
- whitespace;
- Unicode;
- tokens byte-fallback;
- tokens adicionados;
- tokens especiais.

Se a propriedade não valer, há duas opções:

1. implementar um transdutor de detokenização com estado;
2. escolher um tokenizer/modelo cuja semântica seja adequada ao escopo.

A escolha deve ser documentada; usar `tokenizer.decode([id])` cegamente não é suficiente.

### 10.2 Expansão

Um token que emite `b_1 ... b_m` é convertido em um caminho de `m` arcos terminais. O peso e os IDs de propostas devem ser anexados somente uma vez, por exemplo, ao primeiro arco.

Tokens de emissão vazia exigem tratamento explícito e testes; eles não podem simplesmente desaparecer e perder a contagem de slots.

### 10.3 Grammar byte-level

As primeiras tarefas devem usar gramáticas de:

- expressões aritméticas;
- uma pequena DSL;
- um subconjunto de JSON.

A linguagem aceita deve ser documentada exatamente. “JSON” não deve ser usado se a gramática implementar apenas um subconjunto.

---

## 11. Etapa 6 — EOS, PAD e finite-slot exactness

A semântica deve ser escolhida e congelada antes do código final. Uma opção recomendada é:

```text
antes de EOS: tokens normais ou EOS;
depois de EOS: somente PAD;
PAD não emite conteúdo gramatical;
o caminho continua consumindo todos os slots físicos.
```

Isso exige compor o token lattice com um pequeno autômato de dois estados:

```text
BEFORE_EOS
AFTER_EOS
```

A saída testemunha deve registrar todos os token IDs físicos, embora o conteúdo reconhecido pela CFG termine no EOS.

Testes obrigatórios:

- EOS no primeiro slot;
- EOS no meio;
- ausência de EOS quando permitida;
- token normal depois de EOS deve ser rejeitado;
- PAD antes de EOS deve seguir a política declarada;
- exatamente `n` slots físicos são consumidos;
- uma continuação que exigiria `n+1` tokens deve ser rejeitada;
- um validador abstrato com `Sigma*` pode aceitar o mesmo caso, produzindo o contraexemplo de finite-slot exactness.

---

## 12. Etapa 7 — API do otimizador exato

A API Python recomendada é conceitualmente:

```python
solve_exact_commit(
    grammar,
    canvas,
    proposals,
    per_position_support,
    tokenizer_adapter,
    eos_policy,
    timeout,
) -> ExactCommitResult
```

Ela deve executar:

1. validação dos argumentos;
2. construção do token lattice;
3. expansão/composição para o grafo terminal;
4. chamada ao parser;
5. reconstrução da testemunha;
6. recuperação das propostas;
7. validação independente;
8. geração de diagnósticos.

A API deve ser utilizável com logits salvos, sem carregar modelo.

### 12.1 Expansão adaptativa de suporte

Se o top-`K` não produzir conclusão:

1. retornar `INFEASIBLE_ON_SUPPORT` internamente;
2. aumentar `K` conforme configuração;
3. reconstruir e tentar novamente;
4. parar em `K_max` ou timeout total;
5. registrar todas as expansões;
6. executar um fallback explícito se ainda necessário.

Nunca transformar silenciosamente `INFEASIBLE_ON_SUPPORT` em “a CFG é inviável”.

### 12.2 Fallback de progresso

Se o resultado for ótimo, mas nenhuma proposta positiva coincidir com a melhor testemunha:

- selecionar uma posição ainda mascarada;
- comprometer o token da testemunha nessa posição;
- registrar `progress_fallback=true`;
- não contar esse token como proposta aceita, salvo coincidência real.

Uma regra determinística recomendada é escolher, entre posições mascaradas, a de maior probabilidade atribuída pelo modelo ao token da testemunha.

Em timeout ou erro, o sistema pode usar o fallback serial do EPIC, mas precisa registrar que a etapa não recebeu garantia ótima.

---

## 13. Etapa 8 — integração no loop do dLLM

### 13.1 Feature flag

Adicionar configuração explícita:

```text
--commit-strategy serial|epic|exact
```

E configurações do exato:

```text
--exact-support-top-k
--exact-support-k-max
--exact-weight-mode unit|confidence
--exact-timeout-seconds
--exact-eos-policy
--exact-backend python|rust
```

### 13.2 Fluxo de uma etapa

1. executar o forward do modelo;
2. obter o token principal e a confiança de cada máscara;
3. calcular `k_s` pelo schedule existente;
4. criar `C` com as `k_s` posições candidatas;
5. construir suporte para todas as posições mascaradas do canvas relevante;
6. chamar o solver;
7. se `OPTIMAL` e lote não vazio, comprometer o lote;
8. se `OPTIMAL` e lote vazio, usar o token testemunha para progresso;
9. se timeout/erro, usar fallback configurado;
10. atualizar o canvas;
11. registrar um evento JSON da etapa;
12. continuar até conclusão.

### 13.3 Invariante

Depois de cada compromisso, o validador deve confirmar, durante testes e modo de debug, que a testemunha retornada ainda completa o novo canvas.

### 13.4 Compatibilidade

Quando `commit_strategy` não for `exact`, o comportamento existente deve permanecer inalterado. Isso será verificado por testes e, quando possível, por comparação de outputs com seeds fixos.

---

## 14. Etapa 9 — validador independente

O resultado do parser não pode validar a si próprio. Criar um componente separado que:

1. verifica comprimento físico da sequência;
2. verifica posições fixadas;
3. verifica EOS/PAD;
4. recalcula a detokenização;
5. reconstrói a sequência terminal;
6. executa o reconhecedor CFG booleano existente;
7. recalcula as propostas satisfeitas;
8. recalcula o score;
9. compara score e conjunto com o resultado;
10. confirma que todos os IDs e arcos existem.

Em modo de teste, qualquer divergência deve gerar falha imediata com um caso serializável.

---

## 15. Etapa 10 — baselines comuns

Todos os seletores devem receber o mesmo objeto de entrada e produzir uma estrutura comparável:

```text
SelectionResult
  selected_proposal_ids
  score
  witness, se disponível
  runtime
  status
  diagnostics
```

Baselines mínimos:

- força bruta, somente em casos pequenos;
- serial exato;
- EPIC heurístico;
- novo método exato;
- decoder sem restrição para avaliação end-to-end.

A comparação de gap deve usar o mesmo canvas, propostas, pesos e suporte. O ideal é salvar os logits/canvases uma vez e executar vários seletores offline.

---

## 16. Etapa 11 — testes

### 16.1 Unidade

Cobrir:

- validação de pesos;
- agregação de propostas;
- posições fixadas;
- CNF;
- backtracking;
- score;
- múltiplos estados finais;
- topological order;
- epsilon;
- tokens multi-byte;
- token IDs distintos com bytes iguais;
- EOS/PAD;
- timeout.

### 16.2 Diferenciais

- CKY versus força bruta;
- parser de grafo Python versus força bruta de caminhos;
- Rust versus Python;
- solver ponderado com todos os pesos zero versus oracle booleano de não vacuidade;
- witness validator versus parser.

### 16.3 Propriedades

Em instâncias geradas aleatoriamente:

- o score ótimo nunca diminui quando uma alternativa de peso não negativo é adicionada;
- fixar uma posição pode manter ou diminuir o ótimo, nunca aumentá-lo por si só;
- remover uma proposta não pode aumentar o score ótimo;
- toda solução retornada é compatível;
- o score do lote é igual ao score da testemunha;
- expansão de suporte não pode reduzir o ótimo anterior;
- se o lote inteiro é compatível, o ótimo inclui todas as propostas positivas do lote.

### 16.4 Regressão

Cada bug descoberto deve gerar:

- uma entrada mínima serializada;
- o resultado incorreto anterior;
- o resultado esperado;
- um teste permanente.

### 16.5 Integração

Primeiro com logits artificiais fixos; depois com logits gravados; por fim com um modelo real. Testes comuns não devem depender da rede nem da GPU.

---

## 17. Etapa 12 — experimentos

### 17.1 Q1: a implementação é exata?

Executar casos exaustivos e aleatórios pequenos. Reportar:

- quantidade de instâncias;
- tamanhos;
- seeds;
- concordância;
- falhas;
- tempo do DP e da força bruta.

O resultado aceitável para concordância é 100%. Qualquer divergência é um erro, não ruído estatístico.

### 17.2 Q2: quanto a heurística perde?

Para cada estado real ou sintético:

- score exato;
- score EPIC;
- score serial;
- cardinalidade;
- gap absoluto;
- gap relativo;
- tempo.

Também criar casos adversariais pequenos em que a escolha heurística é subótima.

### 17.3 Q3: o canvas finito elimina falsos positivos?

Construir casos em que uma máscara abstrata `Sigma*` admite uma continuação, mas nenhum caminho com os slots reais consegue produzi-la. Reportar:

- número de slots;
- testemunha abstrata mínima;
- número de tokens necessário;
- decisão do baseline abstrato;
- decisão do lattice finito.

### 17.4 Q4: escalabilidade

Variar independentemente:

- número de slots;
- top-`K`;
- tamanho do vocabulário reduzido;
- comprimento médio em bytes dos tokens;
- número de nós e arcos;
- tamanho da gramática;
- ambiguidade;
- número de propostas.

Medir:

- construção do suporte;
- construção/expansão do lattice;
- parsing;
- backtracking;
- validação;
- pico de RAM;
- tamanho do chart.

### 17.5 Q5: funcionamento end-to-end

Com `[MODEL_ID]`, `[TASKS]` e `[GRAMMARS]`, reportar:

- validade sintática;
- funcionalidade, quando houver checker;
- número de etapas;
- tamanho médio e distribuição dos lotes;
- frequência de lote ótimo vazio;
- expansões de suporte;
- fallbacks;
- timeouts;
- tempo total;
- overhead sobre serial, EPIC e sem restrição.

O TCC continua válido mesmo se o exato for mais lento; a análise deve caracterizar o custo da garantia.

---

## 18. Protocolo de medição

Cada execução deverá produzir JSONL contendo:

```text
run_id
commit_sha
config_hash
seed
model_id e revision
tokenizer_id e revision
grammar_hash
dataset e example_id
commit_strategy
weight_mode
support_scope
solver_backend
solver_statuses
hardware
software_versions
timings por componente
memory peaks
selected batches
witness validation
output final
```

Para tempos:

- aquecer modelo e kernels;
- sincronizar CUDA antes/depois do trecho medido;
- separar carregamento do modelo;
- repetir configurações;
- reportar mediana e intervalo interquartil;
- executar métodos no mesmo hardware;
- também reportar razão de overhead.

Tabelas e figuras devem ser geradas por scripts a partir dos dados brutos.

---

## 19. Informações que deverão entrar no TCC

A seção de implementação não pode conter apenas “modelo, GPU e tempo”. Ela deverá registrar:

- fork e commit do EPIC;
- arquivos/módulos alterados;
- linguagem e versões;
- tipos de dados;
- algoritmo usado no backend;
- conversão da gramática;
- tratamento de epsilon/unitárias;
- política de propostas;
- fórmula dos pesos;
- top-`K` e significado de exatidão;
- mapeamento exato token-para-bytes;
- tratamento de tokens especiais;
- EOS/PAD;
- fallback;
- timeout;
- desempate;
- modelo e revisão;
- tokenizer e revisão;
- tarefas, datasets e gramáticas;
- hardware e software;
- seeds e protocolo de repetição;
- verificações contra força bruta;
- métricas;
- limitações observadas;
- comandos de reprodução.

O regulamento exige que o produto final seja descrito em detalhes suficientes para reprodução e que os resultados sejam apresentados e analisados. Por isso, cada decisão acima deve ser registrada durante o desenvolvimento, e não reconstruída de memória no final.

---

## 20. Critérios de conclusão

A implementação obrigatória estará concluída quando:

1. o CKY token-aligned estiver correto;
2. os dois oráculos de força bruta existirem;
3. testes aleatórios apresentarem concordância total;
4. o parser de DAG Python e o Rust concordarem;
5. o lattice preservar slots, tokens, bytes, pesos e proveniência;
6. EOS/PAD estiverem formalmente definidos e testados;
7. cada resultado ótimo vier com testemunha verificável;
8. top-`K` estiver identificado como exatidão sobre suporte;
9. o método estiver integrado a um dLLM real;
10. serial e EPIC continuarem disponíveis;
11. os cinco grupos de experimentos forem reproduzíveis;
12. tabelas e figuras forem geradas automaticamente;
13. o artigo for atualizado somente com resultados reais;
14. a declaração de uso de IA estiver preenchida de acordo com o regulamento.

---

## 21. O que não fazer

- Não começar tentando rodar um modelo de 8B e depurar tudo ao mesmo tempo.
- Não implementar primeiro uma otimização incremental.
- Não tratar timeout como ausência de conclusão.
- Não chamar top-`K` de exatidão global.
- Não usar uma detokenização potencialmente não composicional sem teste.
- Não apagar token IDs depois de converter para texto.
- Não permitir que o peso seja contado uma vez por byte.
- Não confiar apenas no parser novo para validar o próprio resultado.
- Não comparar métodos com propostas ou suportes diferentes.
- Não editar manualmente números de tabelas.
- Não inventar resultados preliminares para preencher o artigo.
- Não modificar o baseline de forma que deixe de representar o EPIC original.

---

## 22. Primeiro ciclo de trabalho

O primeiro ciclo deve terminar com um artefato pequeno, mas cientificamente completo:

1. ambiente reproduzido;
2. tipos `Proposal`, `ExactCommitResult` e statuses;
3. uma CFG pequena em CNF;
4. CKY max-plus;
5. backtracking;
6. oráculo por conclusões;
7. oráculo por subconjuntos;
8. testes de concordância;
9. um exemplo documentado em que o lote ótimo não é o prefixo greedy das propostas.

Somente depois desse gate devem ser iniciados Rust, tokenizer e modelo. Essa ordem é a principal medida de redução de risco do projeto.
