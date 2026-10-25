# Registro de implementação e limitações

Antes de qualquer forward neural:

1. `correctness-v1.console.txt`: Torch CUDA não oferece scatter-reduce booleano
   nesta instalação. Corrigido usando estados 0/1 int32, sem alterar a semântica.
2. `correctness-v1b.console.txt`: o primeiro teste de paridade estava errado:
   uma MASK imediatamente antes de EOS pode ser preenchida por EOS/padding.
   O teste foi corrigido adicionando um delimitador fixo ANTES de EOS; a lacuna
   interior só aceita comprimentos pares. O verificador não foi alterado para
   fazer esse teste passar. `correctness-v1c.console.txt` e JSON: PASS.
3. O script de reprodução continha erro de quebra de linha ao definir a variável
   Python. Corrigido depois do freeze, antes da avaliação TEST; não muda
   produtores, protocolo, políticas ou dados. O hash antigo permanece no freeze.

O perfil é de implementação serial instrumentada; sincronizações por categoria
e listas de decisões têm custo pago no decode. Não mede serving concorrente,
overlap ou um limite inferior de CUDA. O protótipo GPU usa operadores Torch,
incluindo transferência da testemunha para CPU. Não é Gram2Token nem kernel
especializado. CPU usa C++ otimizado, propagação incremental e fechamento por
Dijkstra, em vez de parsing Python deliberadamente lento.

Strings restritas a letras ASCII e arrays recursivos permitem uma pilha
caracterizada apenas pela profundidade. Isso é muito mais simples que uma CFG
geral, JSON completo ou C++. A profundidade 192 decorre do orçamento de 96 IDs
e do máximo de dois colchetes de abertura por ID admitido. A adaptação de
orçamento é exata neste domínio, mas não resolve a barreira geral do apêndice E.

BBH fornece entradas de ordenação; agrupamento JSON é uma transformação própria.
Essas tarefas são resolvíveis por ordenação determinística sem modelo, que recebe
o mesmo texto e atinge 100% por construção. O piloto mede comportamento neural
e custo, não demonstra necessidade social de dLLM nem superioridade a um
programa especializado. Não é benchmark de código funcional ou uso geral.

As oito alternativas por posição são uma política finita explícita; uma
recusa nessa shortlist não prova inviabilidade sob todo o vocabulário. O
verificador, ao completar MASKs, usa TODOS os IDs lexicalmente admissíveis.
Proposta impossível significa que aquela proposta específica não admite
conclusão dentro do orçamento; não implica que o estado atual inviabilizou.

Novos forwards em um estado estagnado continuam no orçamento V1, conforme o
protocolo. Um cache determinístico de logits por contexto poderia evitá-los em
todos os métodos. Relatar estagnação e esse controle adicional antes de promover
qualquer vitória; não implementar uma campanha posterior para resgatar perdas.
