# A37 — Acoplamento de respostas completas pelo resultado canônico

2026-10-11. Nova direção, independente dos prefixos negativos de A34 e da
campanha negativa de A32. V1 congelou contrato/prova/antecedentes antes de
código. V2 tem referência mínima e quatro oráculos racionais independentes;
não há campanha neural ou confirmação de publicação.

## Oito perguntas antes de implementar

1. **Uso real.** Entregar duas respostas JSON/DSL de uma dLLM com maior
   cobertura de respostas corretas, preservando a distribuição de cada
   geração individual. O gerador pode ser EPIC completo, com recuperação e
   falhas incluídas. Uma função canônica reúne representações do mesmo
   resultado, como `1`, `1.0` e um programa JSON que avalia exatamente para
   um. A classe é definida sem gabarito. A aplicação forte é uma tarefa com
   uma única resposta canônica correta e duas avaliações caras; a validade
   sintática vem da GLC original, não deste acoplamento. Custo alto de avaliação
   é uma condição de aplicação, ainda não uma medição deste projeto.
2. **Relevância.** A candidata é um limite quantitativo independente da lei
   do gerador e da concentração dos resultados errados: pelo menos `1/13`
   do ganho máximo possível de pass@2 entre pares de mesmas marginais, usando
   três gerações completas em média. A versão de no máximo doze gerações
   conserva pelo menos `1023/13312` desse máximo. Isso dispensa presumir sinal
   semântico de uma partição fixa. Hashes universais, ruína do jogador,
   antitéticos e canonicalização são conhecidos; o limite composto, suas
   condições e seu valor acadêmico precisam de revisão. Não há prioridade
   confirmada nem promessa de aceitação.
3. **Escolha e controles.** Compare com iid2, iid3, misturas iid de mesmo
   custo esperado, o controle clássico de quatro draws com parada antecipada,
   Barker por colisões, ranked-set sampling, tickets e acoplamentos com
   probabilidades conhecidas. O limite `1/13` supera o `1/16` da mesma partição
   aleatória com o controle clássico limitado a quatro draws; o controle
   consome MENOS trabalho em muitos parâmetros. Não é dominância de custo
   pontual. Amostragem sem reposição pode ter cobertura maior e deve aparecer,
   declarando que altera as marginais. Não exigir preservação de marginais
   artificialmente se o consumidor não precisar dela.
4. **Prova sem código.** `work/theory-v1.md` contém a operação, a lei conjunta,
   o bound por um minorante convexo, a constante e um objeto de prova que a
   torna sharp para ESTA construção. Não afirma minimax entre todos os
   algoritmos. A vantagem vale para toda lei admitida e todo resultado único
   escolhido somente na análise; o algoritmo não o recebe. A prova não usa
   um benchmark favorável. Relevância de custo completo continua separada.
5. **Experimentos honestos.** Antes de qualquer medição neural, conferir a
   distribuição com enumeração racional independente e atacar controles
   conhecidos. Não reutilizar os ganhos de A24 nem relabelar campanhas A32/34.
   Uma eventual campanha nova precisa de inputs externos completos, critérios
   prévios, custos integrais e todos os resultados. Nenhuma foi autorizada
   pelo gate científico desta tentativa ainda.
6. **Custo completo.** Cada draw termina UMA geração inteira original. O
   método não chama o modelo apenas uma vez nem reaproveita logits de um
   canvas diferente. Cobrar carregamento/preparação conforme protocolo comum,
   forwards, recuperação, canonicalização, hash, descartes, saída e avaliação.
   Há no máximo três payloads vivos; o hash linear usa bits proporcionais ao
   maior resultado canônico observado. Não é hashing criptográfico presumido
   exato. Se avaliar é barato, gerar/verificar mais respostas iid vence na
   operação de cobertura: a prova mostra que iid3 SEMPRE supera esta construção
   para o evento canônico único com o mesmo número esperado de gerações. Para
   avaliação imparcial, o bound ideal exige avaliação mais cara que cinco
   gerações quando a taxa de acerto é1/2, antes do custo de coordenação.
   Não cobrar repetidamente por um label canônico que já foi obtido.
7. **Objeções.** A relação com dLLMs/GLCs é de integração, não um princípio
   exclusivo desses modelos. Uma contribuição genérica pode ser pequena
   demais para o recorte pretendido. Mais de um resultado canônico correto
   recebe apenas não deterioração, não o bound `1/13`. Hash do texto bruto não
   substitui equivalência semântica. Uma lei conhecida permite controles mais
   fortes. Nenhuma superioridade de latência ou pass@1 sobre EPIC é alegada.
8. **Artigo defensável.** Faltam prioridade específica, revisão adversarial
   completa, validação mínima e demonstração de uma operação com vantagem no
   custo pertinente. Os antecedentes efetivamente lidos estão em
   `work/primary-comparison-v1.md`. Não inventar revisão humana. A prova escrita
   positiva não encerra o objetivo do usuário nem modifica o artigo principal.

## Contrato e decisão inicial

Investigar somente o protótipo mínimo após registrar esta versão. Os gates
negativos de prefixos baratos continuam fechados. Primeiro verificar se a
constante é correta e se a garantia tem um concorrente conhecido equivalente;
depois decidir se há uso suficiente para uma campanha completa. O método
entrega literalmente dois payloads do gerador original e preserva o primeiro.
Nada é treinado, reparado semanticamente ou consultado no gabarito.

## V2: ampliação e verificação pequena

`work/diversity-corollary-v2.md` estende a constante a TODA distribuição de
resultados canônicos: obtém pelo menos1/13 da maior redução possível de
colisões entre pares de mesmas marginais. O ótimo por quantis conhecidos é
um controle clássico explícito, com vantagem maior; o corolário não exclui
esse comparador. Diversidade não significa correção semântica.

`work/couple.py` não importa código mutável de outra tentativa. Quatro testes
PASS0.064s enumeram payloads originais, aliases/falhas, hashes dependentes
pairwise, truncação e quantis do controle competente. A suíte inteira147
PASS67.788s precedeu a última adição desse check de diversidade; os quatro
testes atuais foram repetidos depois dela. Ruff check/format passam. Tudo
é correção offline, não novidade, timing competitivo ou uso neural. Leituras
adicionais reais ficam em `work/primary-comparison-v2.md`. Gates de prioridade
e consumidor de custo útil permanecem abertos; nenhuma promoção ao artigo.
