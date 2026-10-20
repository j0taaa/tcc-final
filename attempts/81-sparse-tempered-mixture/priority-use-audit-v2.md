# A81 — Auditoria posterior de prioridade e uso

20/10/2026. Nota separada; a prova e a especificação V1 permanecem congeladas.
Leitura de fontes primárias e revisão por subagentes, sem execução, protótipo,
revisão humana ou demonstração de prioridade mundial. **Não selecionada.**

## Antecedente matemático adicional

[Erdős–Kővári, Teorema I e construção dos Lemas II–IX](https://www.renyi.hu/~p_erdos/1956-12.pdf)
já aproxima a função de módulo máximo de uma função inteira por uma soma de
monômios com coeficientes positivos, com cobertura e sobreposição limitadas.
Sua desigualdade `M/3<N<6M` dá `M<3N<18M`. Para inteiro n, a função
`M(r)=(1+r)^n` está no escopo. A auditoria não estabeleceu que a seleção de
expoentes daquele artigo tenha O(sqrt(n)) termos neste caso. Portanto não
foi demonstrada subsunção da complexidade A81, mas esse antecedente é mais
próximo que uma simples aproximação por máximo de tangentes.

Fracionalidade sozinha não fornece uma separação. Para n=ceil(beta) e
a=beta/n, a desigualdade entre normas dá

`(t1+t2)^beta <= (t1^a+t2^a)^n <= 2^(n-beta)*(t1+t2)^beta < 2*(t1+t2)^beta`.

Logo uma construção inteira anterior com O(sqrt(n)) termos se transportaria
para beta racional com, no máximo, o dobro da constante. A construção racional
explícita, o limite de termos, o inferior restrito e a compilação comum ainda
podem conter diferença própria; isso não foi confirmado como prioridade.

## Operação legítima, consumidor específico ausente

Temperar a distribuição conjunta é uma operação estatística legítima.
[LHTS, ICML 2023](https://proceedings.mlr.press/v202/shih23a.html) e
[Temperature Scaling in Discrete Sequence Models, ICML 2026](https://proceedings.mlr.press/v306/scheufele26a.html)
estudam temperatura de sequência. Não estabelecem um consumidor dLLM dentro
do contrato de dois produtos e derivação comum da A81.

[CoDD v3](https://arxiv.org/html/2603.00045v3), seção 5.1 e algoritmos,
usa um PC hierárquico fora desse contrato. Seus algoritmos escritos também
distinguem `p_theta^(1/tau)*p_omega` de temperar o produto inteiro. Nas
temperaturas exploradas 0,2 e 0,1, beta=5 e 10: o limite A81 usa 6 e 8 charts,
contra 6 e 11 na expansão binomial, antes de pagar rejeição e aritmética.
Não é uma integração equivalente nem ganho integral estabelecido.

[E-MoE](https://arxiv.org/html/2609.37533v1), seções 3.1–3.3, realmente usa
um latente global e mistura de produtos, mas soma muitas configurações de
roteamento. Sua temperatura atua no router. Não é uma mistura marginal de
dois componentes temperada como A81; truncá-la exigiria outra justificativa.

Há controles simples indispensáveis:

- Suportes disjuntos: `(t1+t2)^beta=t1^beta+t2^beta`; dois charts exatos.
- Componentes proporcionais: um chart basta.
- Se min(t1,t2)<=epsilon*max(t1,t2) uniformemente, dois charts têm envelope
  `(1+epsilon)^beta`, com correção exata por rejeição.
- Razão pouco variável favorece secante/âncora; poucas razões ou saídas
  relevantes favorecem histograma, enumeração ou MAP/TV certificados.

Para um conjunto C de respostas corretas, no domínio finito positivo,

`d Q_beta(C)/d beta = Cov_Q_beta(1_C, log(t1+t2))`.

O sinal não é determinado. Aumentar peso declarado não prova melhorar
correção semântica. Ainda falta um consumidor natural com sobreposição
substancial, responsabilidades variáveis e temperatura que torne relevante
a economia de charts, sem ser dominado pelos controles acima.

Nenhuma campanha foi selecionada por esta auditoria. A meta central permanece
aberta; não apresentar o limite de representação como benefício de decoder.
