# Operação adaptativa e fronteiras da vantagem

G é a GLC JSON publicada; token->bytes é composicional, slots finitos, EOS
ausente. D_i^0 contém o top16 inicial sem gabarito. Antes da seleção no passo t,
se i está livre, D_i^t=D_i^{t-1} união Top16(q_i^t); se fixado, D_i^t={x_i}.
Uma conclusão y pertence a F_t quando seus tokens estão em D^t, preservam o
canvas e seus bytes pertencem a L(G). q é o softmax congelado daquele forward,
com MASK excluído; a exatidão se restringe ao suporte declarado.

## Invariantes (prova escrita)

1. Se y era uma conclusão viável após os commits anteriores, continua viável
   após expandir os domínios livres. Expansão por união nunca remove seu token.
2. Fixar tokens de um testemunho preserva ao menos esse testemunho. Portanto,
   após admissão inicial conclusiva, suporte expandido e commits certificados
   conservam possibilidade de progresso. Timeout/recusa não provam inexistência.
3. Top16 e união dependem apenas do canvas, previsões e domínios anteriores.
   Se dois seletores executam o mesmo forward determinístico e produzem o
   mesmo lote a cada passo, seus domínios e próximos canvases coincidem por
   indução. Aleatoriedade compartilhada admite a mesma afirmação distribucional.
4. O guloso completo e a maximização lexicográfica produzem o mesmo vetor
   de propostas aceitas: o peso de uma prioridade supera a soma das posteriores.
   Filtro, orçamento e fallback comuns produzem o mesmo lote observável.
5. Se o prefixo elegível até o orçamento é conjuntamente viável, cada prefixo
   também é viável, e o guloso o aceita. Se não é viável, nada se deduz sobre
   os tokens isolados: o híbrido executa a consulta lexicográfica completa.
   Sem propostas elegíveis, uma primeira proposta livre viável é o fallback.
6. Reservatório R pode ser maior que D, sem mudar F_t, se todas as escolhas
   R_i\D_i forem explicitamente proibidas nas consultas. A floresta completa
   preserva todas as conclusões sobre R; exatamente-um token por slot e a
   codificação AND/OR certificam existência. Assumptions negativos que proíbem
   R\D tornam o SAT equivalente à existência em F_t. Ativações futuras mudam
   assumptions, não a gramática. Candidatos fora de R exigem nova preparação.

Estes são resultados de monotonicidade, lexicografia e Tseitin clássicos. Não
inventar novidade apenas por definir a aplicação dLLM. A reserva usa somente
softmax disponível e tokens já conhecidos, sem informações dos futuros forwards.
No reparo, amplia R com D atual e topM atual, M em32/64/128. Tokens futuros
continuam proibidos até entrarem na união top16. Não há liberação de commits.

## Algoritmos e custos

A busca guiada pela raiz usa deduções Earley de previsão, escaneamento e
completação em DAG acíclico. O max-plus guarda a melhor derivação, a compilação
de floresta guarda TODAS as alternativas. CNF sem consumo epsilon permite
processar finais crescentes e inícios decrescentes: filhos direitos sempre
acabam antes de pais de maior span, e prefixos esquerdos já estão estáveis.
Proveniência é preservada no fechamento privado de cada token; aliases e
tokens prefixo são escolhas diferentes. Inteiros exatos transportam prioridades
e desempate do token mínimo no primeiro slot livre. Prioridades m+b<=1075
usam díades representáveis sem arredondar a comparação; recusar outros casos.

Se V/E são vértices/arestas do DAG, um limite conservador de deduções é
O(|G|V³+|G|E), com O(|G|V²+E) células/prefixos para melhor derivação, além dos
bits dos scores/backpointers. A floresta acrescenta todas as alternativas A,
potencialmente cúbicas, mas pode amortizar queries futuras. Esse antecedente é
[Opedal et al.2023](https://aclanthology.org/2023.acl-long.204.pdf), §§5/6 e
notas7/10. A estrutura gramatical incremental segue
[Quimper–Walsh2009](https://arxiv.org/pdf/0903.0470). Não são novos limites.

A união pode acrescentar até16 tokens por slot livre por passo. Novos IDs
não pertencem necessariamente ao circuito preparado. Compare custo total:
preparação inicial + todas as expansões/reconstruções + todos os forwards +
suporte/softmax/propostas + consultas/commits + validação/saída/cleanup.
Reservas ampliam a preparação para diminuir reconstruções; conferir todos os
M predeclarados. Os controles recebem maior limite de células/alternativas e
tempo de compilação, não um teto que force a candidata a vencer.

## O que constitui benefício

Igualdade da trajetória preserva qualquer avaliação aplicada somente à saída
entre os decoders deste MESMO regime. Não prova semântica correta, equivalência
com M24/EPIC ou ganho contra suporte congelado: alterar os domínios pode alterar
as saídas. Velocidade precisa sobreviver ao custo completo e aos controles
com reservas/reutilização. O protocolo de dados externos é evidência empírica
complementar; não transforma os lemas clássicos em uma descoberta original.
Revisão humana, novidade suficiente e publicação ainda não estão confirmadas.
