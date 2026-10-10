# Envelope exato, garantia de aceitação e vantagem delimitada

## 1. Contrato e lei da proposta

q é uma predição produto congelada sobre IDs originais de n slots, com pesos
racionais, trechos fixos, emissões em bytes e EOS ausente. J é JSON completo
estritamente UTF8. J_d é o subconjunto cuja profundidade máxima de containers,
inclusive dentro de cada token, não excede d. B_d conserva a sintaxe através
do token da PRIMEIRA ultrapassagem, e depois exige lexer completo, contador
não negativo e zero ao final, esquecendo os tipos e outras regras.

Todo JSON profundo pertence a B_d. J_d e B_d são disjuntos. A partição por
primeira ultrapassagem é única sobre IDs originais; aliases não se confundem
com várias derivações. Assim L=q(J_d) e U=q(B_d) são massas exatas de eventos.
L não precisa ser a massa completa Z=q(J).

Se L+U>0, propor ν=q(.|J_d união B_d) por uma mistura com pesos L e U:
amostra exata em J_d ou amostra exata em B_d. Testar se a conclusão está em J.
Para qualquer y∈J, a probabilidade de propô-la é q(y)/(L+U). Logo,

    P(aceitar)=Z/(L+U),
    P(resultado=y)=q(y)/Z.

A segunda identidade vem de somar a série geométrica das rejeições, ou de
condicionar uma proposta à aceitação. Todos os eventos profundos permanecem.
Não é uma mistura arbitrária de duas distribuições: disjunção e os pesos
EXATOS L,U são indispensáveis.

Se L>0 e delta=U/(L+U), então Z>=L e

    P(rejeitar)<=delta,
    E[propostas]<=(L+U)/L=1/(1-delta),
    P(refusa após k propostas)<=delta^k.

Com k finito, a lei CONDICIONAL ao sucesso continua q(.|J), pois cada y válido
tem a mesma multiplicação pela soma geométrica finita. Refusa não é uma amostra
nem prova de massa zero. As tentativas não treinam nem mudam q.

J_d usa DP gramatical bounded-depth. B_d usa um backward DAG de prefixos
gramaticais NÃO trimmed por conclusão rasa, conectado no overflow a β de
counter por (slot,lexer,height). Cada transição escolhe peso original vezes
β de continuação; probabilidades telescopam à lei ν. Escolher um ID dentro
de seu grupo proporcionalmente ao peso recupera a lei original, não só bytes.

## 2. Família JSON de prova, com tokenizer FIXO

São3m+4 slots, m>=2, e tokenizer fixo:
`{"payload":`, quote, `[`, `[ `, `{"k":`, whitespace, `0`, `]`, `}`.
O prefixo e o último `}` são fixos. Nos demais slots:

- primeiro valor: quote3/4 ou `[`1/4;
- m slots: `[`1/4, `[ `1/4, `{"k":`1/2;
- um slot: quote1/2 ou `0`1/2;
- 2m slots: `]`φ_j/(4m), `}`(1-φ_j)/(4m), whitespace1-1/(4m),
  com φ_j∈[1/4,3/4], podendo variar arbitrariamente por posição.

A gramática é JSON ordinário, não uma lista de respostas. O ramo quote admite
2^m textos diferentes de payload (`[` versus `[ `); o ramo array admite
2^m sequências de tipos aninhados e diversas posições de whitespace/fechamento.
É um objeto de prova, não uma observação de modelo ou evidência estatística.

No ramo quote, os tokens `{"k":` invalidam a sequência lexical; todos os m
slots devem ser uma das duas versões de `[`. Encerrar com quote e escolher
whitespace nos slots finais dá massa rasa

    L_1 >= (3/4) 2^(-m) (1/2) (1/2) = 3/[16 2^m].

A última1/2 é união: 2m posições têm probabilidade1/(4m) de não-whitespace.
Toda sequência profunda lexicalmente completa pertence ao ramo array e usa0
no slot central. Há m+1 aberturas internas além do objeto raiz. O contador
final requer exatamente m+1 fechamentos no bloco de2m slots, cuja contagem C
é uma soma de Bernoulli independentes de esperança1/2. Pela união sobre
subconjuntos de m+1 sucessos e expansão multinomial,

    P(C>=m+1) <= (1/2)^(m+1)/(m+1)!,
    U_1 <= 1/[8 2^(m+1) (m+1)!],
    delta <= 1/[3(m+1)!].

Para m>=5, delta<0.001, antes de qualquer amostra. Preparação bounded-depth1
mais counter tem O(m²) operações aritméticas e custo polinomial em bits
(denominadores O(m log m) se φ_j tem O(log m) bits). O custo esperado de uma
amostra após preparar é polinomial e o número esperado de propostas<1.002.
Essa não é uma promessa de tempo físico independente da precisão.

Também Z<= (3/8)2^(-m)+U_1 <= (1/2)2^(-m), m>=2.
Logo rejeição bruta requer em média pelo menos2^(m+1) propostas.
Grammar-hit registra pelo menos1/4 de massa de overflow para todo d<=m+1:
todo ramo array atravessa m aberturas e atinge depthm+2. Todas as2^m pilhas
de tipos possuem uma conclusão no suporte, com0 e os fechamentos necessários.
Um certificado hit-only não autoriza erro<0.001 em profundidade constante.

## 3. CARS publicado: uma separação no custo da PRIMEIRA saída

Comparador: algoritmo1 de CARS v2, inicial W vazio, q produto acima e até
oracle PERFEITO de viabilidade no suporte e length fixos. O update de §3
adiciona todos os filhos INVÁLIDOS dos prefixos de cada candidato visitado.
Dar oracle perfeito só fortalece o comparador. Nenhum forward extra é cobrado
ao controle: q inteiro já está disponível para ambos.

Cada uma das2^m classes por tipos no bloco de m aberturas, no ramo array,
tem massa1/[4 2^m]. Todos seus prefixos até o fim do bloco são completáveis;
portanto não podem ser removidos por um oracle correto. Um candidato visitado
consegue eliminar massa futura de no máximo uma dessas classes. Siblings
antes do fim do bloco também são viáveis e não podem ser eliminados. Isso
permanece mesmo agregando aliases e memorizando o estado lexical/pilha igual;
as2^m pilhas de tipos são distintas.

Após t candidatos, massa ainda permitida é pelo menos

    A_t >= (1/4)(1-t/2^m).

Enquanto t<=2^(m-1), A_t>=1/8. Como a lei proposta CARS é q/A_t nos eventos
não eliminados e nenhum evento válido pode ser eliminado, sua probabilidade
de sucesso no próximo candidato é Z/A_t<=4 2^(-m).

Para M=floor(2^m/8), união condicional dá P(N<=M)<=4 M/2^m<=1/2.
Logo E[N]>=M P(N>M)>=M/2=Omega(2^m). Para m>=3,

    E[N] >= 2^(m-4).

Não precisa supor independência dos candidatos adaptativos para essa união.
Trata-se de primeira saída, não de superioridade universal em lotes longos.
Se a implementação testa filhos durante o desenho em vez de terminar um
candidato, contar as classes completas de prefixos de abertura processadas;
a garantia não autoriza chamar todos os checks de uma única tentativa grátis.

**Fronteiras cruciais.** CARS permite outros updates: precomputar massas CFG,
remover conjuntos não prefixais por um circuito ou começar com o envelope
deste método muda o comparador. A separação NÃO cobre essas variantes, toda
codificação FactorDLM nem parsing compacto. Counter-only também pode conseguir
amostras rápidas nesta família e é baseline obrigatório. O ganho do envelope
específico contra esse baseline depende de custos/aceitação reais, não segue
deste teorema. Aplicação de uma técnica conhecida não demonstra prioridade.

## 4. dLLM e limites da integração

O produto é um forward de dLLM, disponível em paralelo; não é o modelo conjunto
aprendido nem a lei nativa condicionada de todo processo. Substituir a amostra
de posterior completo por este sampler exato preserva o kernel sob a MESMA
política de commits e, com rejeição ilimitada/recursos suficientes, por
indução a trajetória desse decoder com novos forwards. Com orçamento FIXO
k, o kernel inclui FAIL: TV da trajetória<=sum_t delta_t^k, nas hipóteses de
`finite-budget-trajectory.md`. Condicionar a trajetória inteira à conclusão
não demonstra igualdade. Intervalos de marginais não podem alterar a política: decisões
precisam ser robustas aos intervalos ou usar fallback exato. Twister2026
documenta que o decoder de posteriors congelados já pode diferir da trajetória
nativa condicionada. Não confundir equivalência com eliminar esse viés.

Recursos suficientes são hipótese das leis. Refusas por memória/deadline
permanecem explícitas em experimentos e não recebem garantia de acerto.
Semântica não decorre de JSON válido. Probabilidades zero fora do suporte da
família são hipótese explícita, não exclusão silenciosa de cauda full-V real.
