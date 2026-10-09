# Certificado global de envelope e controle por perfis

Refinamento da tentativa 17, não mudança de distribuição/política. Os oito
critérios são reavaliados antes de implementar:

1. Uso: consultas condicionais iid para diagnóstico/gradiente da política PL
   da dLLM sob JSON/GLC. Reduzir rejeições sem trocar os logits ou commitments.
2. Significância: o fator 2 da nota é conservador. Certificar o melhor fator
   obtido por limites de intervalos é uma otimização matemática delimitada;
   não reivindicar novidade de rejection sampling/interval arithmetic.
3. Adoção: menos propostas **da mesma distribuição**, contra a mistura original;
   medir também Base, SingleTilt fortalecido, enumeração e perfis arredondados
   da própria nota. Não usar um produto único como único adversário.
4. Prova: seja r_j(S)=f(s_j)exp(t_j(s_j-S))/f(S). A segunda derivada de log r_j
   é -sum_r 1/(S+c_r)^2 <0. Logo r_j tem mínimo nos extremos de cada intervalo.
   Somar limites inferiores certificados dos extremos fornece B<=inf_S sum_j r_j.
   Arredondar B para baixo numa potência de 2 preserva o certificado. Use
   B=max(1/2,B_calculado), porque a cobertura original prova >=1/2. Como as
   unárias/coeficientes são superiores, Rbar>=sum_j tangentes>=B f. Portanto
   f/(Rbar/B)<=1. A lei aceita continua mu_A e a esperança de propostas é
   (1/B)/2 vezes a da mistura antiga, nunca maior. O custo adicional é O(J^2)
   enclosures racionais, contabilizado; não implica menor primeira latência.
   Argumentos exponenciais negativos enormes podem receber lower bound 0,
   com corte certificado e erro absoluto. Argumentos positivos são <=k.
5. Protocolo: mesmas nove entradas/48 eventos, todos os cinco métodos,
   três repetições e lotes 1024/4096. Nenhum caso novo eleito por vitória.
   Primeiro completar/preservar as versões anteriores; depois avaliar essa.
   Repetir a campanha neural externa de seis inputs com mesmos casos/seeds.
6. Custo: prep do certificado/perfis, bits, CPU/wall, first draw e lote,
   tabelas/memória e recusas. Aplicar ao SingleTilt uma tolerância mais fina
   (f(H)/1024), para evitar favorecimento por um envelope numericamente frouxo.
   O novo controle por perfis tem limite de 1M células/3M transições e mesmo
   deadline, declarado antes de observar seu desempenho; recusas inconclusivas.
7. Objeções: O(J^2) pode custar mais que as rejeições poupadas; perfis podem
   vencer; o certificado pode permanecer B=1/2. O controle por perfis deve
   usar CDFs inteiras e majorantes dyádicos dos pesos na raiz, evitando um
   MMC desnecessário. Sua curva é polinomial mas potencialmente grande.
8. Artigo: provar/auditar a cobertura e a lei efetiva; não converter otimização
   de envelope em prioridade científica ou vitória geral contra EPIC. Se os
   controles melhores continuam ganhando, reportar isso e não esconder o código.

## Perfis como comparador competente

A referência já monta profiles[node][rho], mas só integrava sua lei em exemplos
pequenos. Tornar essa mesma representação amostravel é um controle, não nossa
inovação. rho é soma arredondada numa árvore fixa, não semiring associativo.
Cada caminho com m folhas ocultas positivas tem erro relativo <=gamma^m;
merges com zero não introduzem erro. Com gamma=1+1/(2km),
f(rho)<=f(S)<=2 f(rho). Root weights podem ser arredondados para cima com
erro <=f(max rho)/1024; isso preserva a moeda f(S)/(2 root_upper[rho]) e dá
esperança <=2(1+1/1024). O majorante dyádico comum mantém o denominador da
raiz pequeno. Todos os backpointers/combinações e seus recursos entram no custo.

## Correção do harness neural anterior

A campanha neural v2 do commit 090f734 preserva 369 recusas por TypeError: um
argumento posicional `decision_cache_statistics` entrou indevidamente no
`partial(TangentMixture, ...)`. As 63 consultas com recompensa zero tiveram
bypass; não são medições do amostrador. Isso invalida qualquer leitura de v2
como campanha completa da mistura. A campanha v1 não tem esse defeito.
Remover esse argumento é uma correção do harness, não melhoria do método nem
nova distribuição. O gerador de relatório exige todos os status completos e
recusa v2. Reexecutar as seis entradas selecionadas, sem substituir casos.

## Fortalecimento do controle antes de medir

O DP de perfis calcula também a menor soma **exata** S de cada célula, além da
massa. Nas folhas usa a taxa original e nos merges soma os mínimos dos filhos;
a decomponibilidade torna esses mínimos alcançáveis conjuntamente. Alternativas
usam mínimo. Assim, na raiz, f(S_min[rho]) é um envelope competente por perfil,
mais justo que aplicar o fator global 2 a f(rho). Seu majorante dyádico usa erro
f(max S_min)/1024. Peso da raiz = massa[rho] * upper[rho]; aceitação = f(S)/upper.
Isso preserva exatamente o alvo e não usa taxas do gabarito. Como todas as
somas no perfil estão entre rho/gamma^m e rho, a esperança é no máximo
2(1+1/1024), com os mesmos limites de recursos e custos contabilizados.
Esse controle mais forte não é rebatizado como nossa contribuição. O estado
antigo, incluindo o primeiro protótipo executável, fica preservado no commit
b9a809d antes de qualquer medição dessa nova fase.
