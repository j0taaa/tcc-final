# Controle forte: counter+CARS e interrupção de prefixos impossíveis

O protocolo deve incluir `Cars(counter=True)`, não apenas rejeição bruta e
CARS sobre o produto original. A primeira proposta é q(.|C), onde C exige
lexer completo e balanço final sem tipos/sintaxe. C contém J e tem beta exato
por(slot,lexer,height). Cada nó novo da trie usa essa massa de continuação,
em vez de tratar todo futuro como permitido. Remover prefixos comprovadamente
inválidos continua preservando a lei q(.|J) das respostas aceitas.

O controle também para de desenhar uma proposta assim que o prefixo sorteado
não admite JSON válido. Os sorteios restantes não podem torná-lo válido;
são variáveis latentes desnecessárias. A trie é atualizada ENTRE propostas.
Os irmãos viáveis de um prefixo novo não são renormalizados durante a
proposta: isso seria outra distribuição e precisaria de correção.

Todos os grupos inválidos dos prefixos visitados são excluídos, incluindo
tokens lexicalmente inválidos. Classes do mesmo efeito preservam seus IDs
por amostragem proporcional aos pesos originais. A alternativa `perfect=True`
usa DFS memorizada de viabilidade com o comprimento/suporte originais; a
opção leve usa sintaxe e limites necessários seguros do contexto direito.
Fonte do controle é independente, não o código nativo dos autores de CARS.

Seis oráculos pequenos enumeram os sorteios reais; a lei aceita com orçamento
finito coincide com o reconhecedor JSON independente em todas quatro
configurações CARS: leve/perfeito sobre q/counter. Isso é correção, não
conquista experimental. O híbrido pode vencer nosso envelope; todas perdas
devem permanecer. A família escrita NÃO prova vantagem sobre esse híbrido.
