# A36 — Cabeça esparsa guiada por gramática: antecedente encontrado antes de código

2026-10-11. Direção explorada separadamente, SEM implementação, teste de
modelo ou medição. Recusada como novidade central na formulação simples.
Não recupera as perdas de A28 nem modifica EPIC ou o artigo principal.

## Oito perguntas antes de implementar

1. **Uso real:** geração/preenchimento paralelo de JSON por dLLM, evitando
   calcular linhas da cabeça neural para tokens que não podem aparecer em
   nenhuma conclusão válida. O consumidor receberia os mesmos IDs originais
   do posterior condicionado, com menos produtos escalares na projeção.
2. **Contribuição relevante:** a ideia simples não passou pelo gate de
   novidade. GPIO-LLM já implementa cabeça esparsa determinada pela gramática,
   inclusive pular a cabeça em decisões forçadas. Transferir isto a uma dLLM
   ou citar CFG não constitui por si só uma nova contribuição matemática.
   Uma implementação eficiente pode ser útil, mas isso não cumpre a exigência
   científica atual sem uma diferença adicional demonstrada.
3. **Escolha/comparador:** compare com cabeça densa igualmente otimizada,
   com cálculo apenas nos slots necessários, e com cabeça esparsa competente.
   O potencial de MACs é proporcional a |A_i|/|V| na posição i. Não confundir
   essa razão com aceleração total; o backbone e a obtenção de A_i custam.
4. **Prova sem código:** fatores de normalização por posição cancelam no
   posterior condicionado; escores de tokens que NÃO ocorrem em nenhuma
   conclusão válida não são necessários para AMOSTRÁ-LO. É uma identidade
   clássica, insuficiente para novidade. Ela não dispensa calcular a massa
   válida no produto original, nem preserva confidências usadas pelo EPIC.
5. **Experimentos:** nenhum foi iniciado. Antes de uma eventual hipótese
   distinta, seria preciso congelar casos externos, controles, geração inteira
   e critério de sucesso. Não medir só a cabeça e alegar ganho integral.
6. **Custos completos:** suporte viável por posição exige admissão, tokenizer,
   preparação/atualização gramatical e memória. Depois vêm backbone, projeção,
   amostragem e saída. Slots em strings podem admitir quase o vocabulário
   inteiro; o benefício pode desaparecer. EOS/falhas continuam no contrato.
7. **Objeção decisiva:** há antecedente público com o mesmo mecanismo. Além
   disso, remover logits e renormalizar altera a confiança da política nativa;
   essa alteração não pode ser vendida como preservação da trajetória EPIC.
8. **Artigo:** não há resultado próprio delimitado, vantagem total ou prova
   distintiva. Não expandir esta versão para outra grande implementação. Fonte
   primária e raciocínio ficam em `work/primary-comparison-v1.md` para não
   perder a investigação ou repetir uma ideia já conhecida.

## Decisão

Rejeitar a alegação "cabeça esparsa guiada por CFG é a contribuição nova".
Isto NÃO prova impossibilidade de qualquer avanço relacionado, nem que o
antecedente já implemente inferência conjunta de uma dLLM. Nenhum pedido de
review humano/publicação foi feito e nenhuma aceitação é alegada.
