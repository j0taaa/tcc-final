# Confidence commitments com decisões exatas e amostra certificada

Aplicação da consulta, não uma alegação de que threshold/commitments são novos.
Em um histórico h, ambos os decoders recebem o MESMO produto q_h e o canvas.
O comparador amostra mu_h=q_h(.|J_h) e testa mu_{h,p}(y_p)>=4/5 para cada
slot livre do seu testemunho y. Aceita posições em ordem de índice, até4;
se nenhuma passa, fixa o primeiro slot livre do testemunho. Ambas regras
progridem e preservam uma conclusão válida, não asseguram acerto semântico.

A versão certificada amostra nu_h=q_h(.|J_{h,d}), com TV<=epsilon_h. Seus
marginais têm numeradores N_{p,t} na mesma unidade de l,u, satisfazendo

    N_{p,t}/(l+u) <= mu_{h,p}(t) <= (N_{p,t}+u)/(l+u).

Se o limite inferior>=4/5, a decisão exata é aceitar. Se o superior<4/5,
é rejeitar. Intervalo ambíguo causa refinamento da consulta do MESMO q_h;
y não é reamostrado. Um fallback completo resolve inclusive igualdade.
Assim o commitment final K_h(y) coincide com a política de marginais exatos
para TODO testemunho admitido, não apenas nos exemplos que passam nos testes.
Recusar por recursos não resolve ambiguidades e permanece interrupção explícita.

Aplicar a mesma função K_h contrai TV. Os próximos forwards dependem do
canvas; enquanto os históricos são acoplados, modelo e q_h também coincidem.
Acoplamento por passo dá TV da lei final<=sum_h epsilon_h. Com inicialmente
m slots livres e epsilon_h=0.001/m, há no máximo m passos: o limite é0.001.
Todas as conclusões QUE FOREM RETORNADAS são JSON válido, pela preservação
dos testemunhos, independente de usar esta aproximação. O bound não cobre
timeouts/memória ou reconhecedores inconclusivos, e tampouco o viés entre
posteriors produto e a trajetória NATIVA condicionada apontado por Twister.

O protocolo conserva todos5×3 inputs nas duas implementações e novos forwards
após cada passo. Um seed é uma demonstração funcional, não confirmação
estatística de latência ou de equivalência de amostras pareadas: mesma seed
não é, em geral, o acoplamento matemático ótimo. Custos incluem cada consulta
e refinamento, nova predição e saída; tabelas lexicais são o único estado
compartilhado do serviço. CARS sem marginais e EPIC com outro objetivo não
são reimplementados por este controle de pilhas. Alterar o produto pelo
corolário amplification é outra operação e NÃO ocorre neste decoder.
