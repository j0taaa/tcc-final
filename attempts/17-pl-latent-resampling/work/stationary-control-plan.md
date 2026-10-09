# Controle estacionário e critério de utilidade (congelar antes de medir)

Os oito critérios do README continuam válidos. Este refinamento investiga a
aplicação de treinamento, não reivindica novidade em Metropolis–Hastings.

1. Uso: média de scores de propostas descartadas, mantendo os commitments e
   o retorno observado de um rollout on-policy dLLM/GLC. Não mudar sua saída.
2. Significância: identificar quando o kernel iid da nota é necessário e quando
   uma operação conhecida mais simples obtém benefício suficiente. O controle
   não será vendido como descoberta teórica independente.
3. Comparadores: original sem réplica; iid por enumeração/Base/SingleTilt/mistura;
   um passo de independência-Metropolis com proposta Base e SingleTilt. Eles
   recebem a proposta descartada original. Não exigir burn-in nesse contexto.
4. Matemática: se Y0|A tem lei mu_A e P preserva mu_A, Y1 também a tem.
   A média dos scores mantém o valor esperado. Cov(média|A) = Cov(G|A) -
   Cov(G0-G1|A)/4, portanto não aumenta em ordem PSD. No IMH a aceitação é
   min(1, a(Y')/a(Y0)), onde a é a moeda do rejeitador; pesos normalizadores
   cancelam. Detalhamento balanceado deve ser verificado por oráculo racional.
5. Protocolo: mesmas fixtures finitas e casos nativos já congelados; sem escolher
   estados por conflito/ganho. Reproduzir Y0 com a semente original. Três
   repetições, lotes 1/4/16, tempo completo e limites existentes. Uma sequência
   IMH tem dependência; nunca aplicar a identidade iid a ela. Oráculos não são
   benchmark de treino. Os nove casos existentes permanecem desenvolvimento.
6. Custo: preparo e todas as transições; forward/backward e score neural precisam
   ser medidos separadamente para fechar a condição de custo vezes variância.
   Verificar de modo independente o score em parâmetros reais (ao menos uma
   cabeça neural, explicitando essa fronteira). Custo marginal > custo original
   impede compensação com uma única réplica iid mesmo no melhor caso possível,
   pois sua variância total só pode cair até metade. Não confundir esse limite
   necessário com comprovação de benefício se o custo for menor.
7. Objeções: IMH pode quase nunca mover e não reduzir variância suficiente;
   iid pode valer em estados difíceis; enumeração/Rao–Blackwellização podem
   dominar todos. Provar correção sem medir ou limitar o custo não fecha utilidade.
8. Falta: obter redução e custo na mesma operação, delimitar relevância versus
   novidade, preservar todos os resultados. Não alegar treinamento completo,
   acerto semântico, revisão humana ou superioridade geral de publicação.

Integraremos também a moeda MH: H=(1-a/2)G0+(a/2)Gproposto.
E[H] é o mesmo; Var(H)<=Var((G0+G1)/2) por condicionamento.
Esse controle exige somente uma proposta e dois scores, sem simular a moeda,
e será apresentado como Rao–Blackwellização clássica.
