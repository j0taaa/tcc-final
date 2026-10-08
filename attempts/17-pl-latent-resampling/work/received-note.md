# Reamostragem condicional exata de propostas descartadas em dLLMs sob GLCs

**Data:** 8 de outubro de 2026.  
**Natureza:** construção e demonstração matemática produzidas nesta análise; acompanhadas de verificações finitas independentes. Não é uma publicação, um resultado de treinamento, uma prova mecanizada ou uma certificação de prioridade histórica.

## Resumo

Uma dLLM restrita pode sortear uma proposta completa gramaticalmente válida e escolher, por Plackett–Luce, apenas parte das posições para fixar. A proposta nas demais posições é uma variável latente descartada. O gradiente de política calculado com essa variável pode conter variância que não afeta a trajetória executada.

Construímos um amostrador **exato** da proposta latente condicionada aos tokens fixados e à ordem de seleção registrada. O mecanismo não exige calcular a normalização desse posterior nem integrar numericamente sua derivada. Uma mistura finita de distribuições gramaticais com pesos locais modificados domina o posterior, e uma correção de aceitação/rejeição restaura exatamente a distribuição-alvo.

Com k posições selecionadas e razão de taxas κ, a mistura usa J = O(1 + sqrt(k) log κ) componentes. No modelo aritmético real, bastam J avaliações de uma floresta compilada, com número esperado de propostas no máximo 2J. Uma versão inteiramente racional usa enclosures certificados de exponenciais na **proposta**, não no alvo, e tem número esperado de propostas no máximo 2J+1. A exatidão não depende de uma tolerância de quadratura nem da probabilidade do evento observado.

Amostras independentes desse posterior permitem um estimador de gradiente não enviesado com identidade exata de covariância:

Cov(G_r) = V_observável + V_latente/(r+1).

O resultado é eficiência estatística por trajetória neural. Menor tempo total só decorre sob uma condição explícita entre custo adicional e variância removida.

## 1. Contrato e hipóteses

Fixamos um estado de geração, o pedido e os parâmetros θ.

- Há n posições atualmente mascaradas, cada uma com suporte finito de tokens originais. Posições previamente fixadas entram como evidência e não são candidatas a seleção.
- F é o conjunto não vazio de propostas completas que respeitam a gramática, os tokens já fixados, os slots e a política de término declarada.
- Os pesos locais q_i(v) são positivos no suporte considerado. Z = sum_{y in F} product_i q_i(y_i) é positivo.
- A gramática/tokenização é representada por um circuito de soma/produto determinístico e decomponível: as somas unem alternativas disjuntas; os produtos combinam conjuntos disjuntos de escolhas de tokens. Cada proposta original tem exatamente uma representação na raiz. Uma floresta apropriada de gramática não ambígua é suficiente.
- Custo F_c denota o número de operações/arcos necessários para uma avaliação escalar do circuito. Não denota número de textos representados. A construção do circuito é contabilizada separadamente.
- Cada posição i recebe uma taxa λ_i(v)>0, dependente apenas do estado fixo, de i e do token v nessa posição. Pode depender de θ. Taxas com dependências globais arbitrárias não são admitidas por esta redução.
- Selecionamos 1 <= k < n posições por amostragem sequencial sem reposição Plackett–Luce. Guardamos a ordem efetivamente sorteada σ=(i_1,...,i_k), além dos valores a_{i_r} efetivamente fixados. Essa ordem não precisa ser usada pela continuação da dLLM.
- A trajetória posterior depende somente do novo canvas e de novas fontes de aleatoriedade, não dos tokens descartados. A política não usa remasking ou caches ocultos que dependam dessas propostas sem registrá-los no estado observado.
- Para a complexidade em bits, q e λ são entradas racionais positivas em representação binária. Para as identidades diferenciais, a política ideal é diferenciável em θ, com suporte e restrição fixos na região analisada.

Não se afirma exatidão no vocabulário completo quando se usa top-K. Não se afirma exatidão do texto final como posterior do primeiro passo. Uma gramática ambígua não pode ser usada para somar massas de derivações como se fossem massas de palavras.

## 2. Redução da seleção a uma função de uma soma

Seja U o conjunto das m=n-k posições não escolhidas. Para cada posição escolhida defina

b_r = λ_{i_r}(a_{i_r}),
c_r = sum_{j=r}^k b_j.

Para uma proposta y que coincide com os valores fixados, defina

S(y) = sum_{i in U} λ_i(y_i).

A probabilidade da ordem observada, dada essa proposta, é

f(S(y)) = product_{r=1}^k b_r/(S(y)+c_r).

**Prova.** Na r-ésima seleção, todas as posições de U ainda estão disponíveis, assim como as posições escolhidas nos passos r,...,k. O denominador Plackett–Luce é, portanto, S+c_r. O numerador é b_r. Multiplicar essas probabilidades prova a fórmula.

Se F_A = {y in F: y_i=a_i para i selecionado}, o posterior desejado é

μ_A(y) = w(y) f(S(y)) / Z_A,
w(y) = product_i q_i(y_i),
Z_A = sum_{y in F_A} w(y) f(S(y)).

O fator 1/Z da proposta gramatical original cancela nessa distribuição condicionada.

**Importante:** simplesmente sortear de w condicionado aos valores escolhidos está errado em geral. Os tokens descartados também influenciaram os denominadores da seleção. f corrige exatamente essa informação.

Se k=n, todos os tokens estão observados, sem latentes a reamostrar. Se k=0, não há seleção a condicionar e usa-se o sampler gramatical original.

## 3. Envelope de tangentes: teorema principal

Escolha limites seguros 0 < L <= S(y) <= H para todo y em F_A. Um cálculo suficiente é

L = sum_{i in U} min_v λ_i(v),
H = sum_{i in U} max_v λ_i(v).

Otimização min-plus/max-plus na mesma floresta pode apertar esses limites, mas não é necessária.

Se L=H, f é constante sobre o suporte, e μ_A é apenas a distribuição gramatical condicionada aos valores observados. Trate esse caso sem mistura.

Defina c_min=c_k>0, d=ceil(sqrt(k)) e r=1+1/d. Use pontos

s_j+c_min = (L+c_min) r^j,

começando em j=0, enquanto s_j <= H. Seja J o número de pontos. Então

J <= 1 + log((H+c_min)/(L+c_min))/log(1+1/d).

Em particular, se todas as taxas das posições ocultas estão entre λ_min e λ_max e κ=λ_max/λ_min,

J = O(1 + sqrt(k) log κ).

### Lema 1: cada tangente é uma distribuição fatorável não normalizada

Se h(s)=log f(s), então

h'(s) = -sum_r 1/(s+c_r),
h''(s) = sum_r 1/(s+c_r)^2 > 0.

Defina t_j=-h'(s_j) e

M_j(s) = f(s_j) exp(t_j s_j) exp(-t_j s).

Pela convexidade, M_j(s) <= f(s) para todo s>=0. Substituindo s=S(y), temos

M_j(S(y)) = α_j product_{i in U} exp(-t_j λ_i(y_i)),
α_j = f(s_j) exp(t_j s_j).

Logo, w(y) M_j(S(y)) usa a gramática original e apenas troca pesos locais por q_i(v) exp(-t_j λ_i(v)) nas posições ocultas.

### Lema 2: cobertura multiplicativa

Para cada S em [L,H], tome o último ponto s_j<=S. A construção assegura

0 <= S-s_j <= (s_j+c_min)/d.

Como h''(u) <= k/(s_j+c_min)^2 para u>=s_j, o resto de Taylor integral dá

0 <= h(S)-h(s_j)-h'(s_j)(S-s_j)
   <= k(S-s_j)^2/[2(s_j+c_min)^2]
   <= k/(2d^2) <= 1/2.

Portanto M_j(S) >= exp(-1/2) f(S). Somando todas as tangentes e usando M_j<=f,

exp(-1/2) f(S) <= R(S) := sum_j M_j(S) <= J f(S).

Em particular,

f(S) <= 2 R(S) <= 2J f(S).

### Teorema 1: amostragem exata no modelo aritmético real

Para cada componente j, avalie a floresta com os pesos locais modificados e a evidência escolhida. Seja Z_j essa massa. Sorteie j proporcionalmente a α_j Z_j e depois y segundo esse componente. A proposta resultante tem distribuição

ν(y) = w(y) R(S(y)) / Z_R,
Z_R = sum_{y in F_A} w(y) R(S(y)).

Aceite y com probabilidade

p_acc(y) = f(S(y))/(2R(S(y))).

A probabilidade não normalizada de retornar y numa tentativa é

ν(y) p_acc(y) = w(y) f(S(y))/(2Z_R).

Condicionando ao sucesso, isso é μ_A(y). Repetir com novas variáveis aleatórias produz amostras independentes de μ_A.

O número esperado de tentativas por amostra é

2 Z_R / Z_A <= 2J.

A probabilidade de precisar de mais de t tentativas é no máximo (1-1/(2J))^t. O limite não contém 1/P(A).

## 4. Versão racional: exatidão sem aritmética exponencial ideal

O sampler anterior pode ser implementado sem aceitar/rejeitar com floats. As exponenciais servem apenas para construir uma proposta dominadora; podemos substituí-las por limites racionais superiores controlados e corrigir usando o alvo racional exato.

Seja f_min=f(H)>0. Note que t_j s_j <= k e f(s_j)<=1, portanto

α_j <= exp(k) < 3^k.

Calcule números racionais satisfazendo

α_j <= αbar_j <= α_j + δ_a,
exp(-t_j λ_i(v)) <= ubar_{ji}(v) <= 1,
ubar_{ji}(v)-exp(-t_j λ_i(v)) <= δ_u,

onde

δ_a = f_min/(4J),
δ_u = f_min/(4J 3^k m).

Como fatores estão em [0,1], a diferença entre os produtos de m fatores é no máximo a soma das diferenças. Assim,

0 <= αbar_j product_i ubar_{ji}(y_i) - M_j(S(y))
   <= δ_a + 3^k m δ_u = f_min/(2J).

Defina

Rbar(y) = sum_j αbar_j product_{i in U} ubar_{ji}(y_i).

Então

f(S(y)) <= 2Rbar(y) <= (2J+1) f(S(y)).

Use a mistura gramatical racional com coeficientes αbar e pesos q_i(v)ubar_{ji}(v). A aceitação é a fração racional

f(S(y))/(2Rbar(y)).

**Corolário.** As amostras continuam exatamente distribuídas segundo μ_A, com no máximo 2J+1 tentativas em esperança. Não há erro de aproximação na distribuição final. O arredondamento alterou a eficiência da proposta, não o alvo.

### Como obter os limites superiores racionais

Para x>=0, a série positiva de exp(x) fornece limites. Após grau N, se N+2>=2x, a cauda é no máximo duas vezes o primeiro termo omitido. Uma soma parcial e esse limite fornecem um intervalo racional certificado.

Para exp(-x), inverta o intervalo certificado de exp(x). Se x>=p e 2^(-p)<=δ, pode-se usar δ como limite superior: exp(-x)<=exp(-p)<=2^(-p)<=δ. Esse caso impede gastar espaço representando uma exponencial astronomicamente pequena.

Todas as operações de aceitação são Bernoulli racionais: para a/b, sorteie um inteiro uniforme em {0,...,b-1} e aceite se ele for menor que a. A seleção categórica pode usar denominadores comuns ou Bernoullis sequenciais exatos.

### Complexidade em bits

A afirmação O(F_c J) abaixo é uma contagem aritmética, não tempo binário unitário. Ainda assim, a versão racional tem custo binário polinomial na representação de entrada e do circuito:

1. log κ é limitado polinomialmente pelo número de bits das taxas racionais.
2. Cada ponto da grade usa uma potência racional de expoente J, que possui tamanho binário polinomial.
3. -log f_min é soma de k logaritmos de razões racionais de tamanho polinomial. Assim log(1/δ_a) e log(1/δ_u) são polinomiais.
4. As séries anteriores precisam de precisão absoluta com número polinomial de bits. Os argumentos negativos grandes são truncados por um limite superior certificado; os argumentos positivos t_j s_j são menores que k.
5. O circuito é decomponível: uma derivação usa no máximo uma escolha por posição. Produtos e somas de pesos racionais podem ser colocados em denominadores comuns por posição, com tamanho polinomial no total de entradas e em seus bits. O número de atribuições é exponencial, mas o número de bits necessário para contar essas atribuições é polinomial.
6. As moedas/categorias racionais têm algoritmos exatos de custo esperado polinomial. O número esperado de tentativas externas é <=2J+1.

Não se reivindica uma cota linear de bit complexity nem que Fraction seja uma implementação rápida.

## 5. Custo completo de uma consulta

Se B_c é o custo de compilação, E o total de escolhas de tokens e L_s o custo de uma amostra em um componente já preparado, a mistura requer:

- construção de pesos/enclosures: custo adicional polinomial em E,J e nos bits;
- preparação dos componentes: O(F_c J) operações aritméticas;
- memória para todos os valores internos: O(V_c J), onde V_c é o número de nós;
- cada proposta: O(L_s + mJ + k + J) operações para escolher o componente, amostrar, somar taxas e avaliar a mistura;
- cada amostra condicional aceita: até 2J+1 propostas em esperança.

Para r reamostragens, a preparação é paga uma vez. A compilação pode ser reutilizada quando o contrato permite; se não puder, B_c entra novamente. O bound é em relação a uma representação já fornecida, não uma promessa de que toda GLC ambígua tenha um circuito determinístico pequeno.

Uma seleção por tabela categórica pré-computada pode reduzir parte do custo de amostragem. Seu custo de preparação também precisa ser contado. Um caso de taxas totais constantes não precisa de mistura.

## 6. Gradiente de política e identidade de redução de variância

Considere uma trajetória de geração inteira. C registra todos os canvases efetivamente executados, os valores fixados e as ordens PL. Y registra as propostas completas latentes de todos os passos. A recompensa R depende de C, não de Y fora dos valores observados.

O estimador completo on-policy é

G(Y,C) = R(C) grad_θ log p_θ(Y,C).

Ele deve incluir tanto a normalização gramatical dos tokens quanto a probabilidade da seleção. Ignorar a seleção ou a derivada da normalização invalida esse contrato.

Pela hipótese de estado Markoviano, condicionado à trajetória C, as propostas latentes de diferentes passos se fatoram nos posteriors locais μ_{A_t}. Logo, aplicar o sampler a cada passo produz uma nova trajetória latente completa da distribuição p(Y|C), sem novas avaliações do modelo ou da recompensa.

Gere r réplicas independentes condicionadas a C. A proposta originalmente observada é uma amostra adicional da mesma lei condicional. Defina

G_r = [G(Y^(0),C)+...+G(Y^(r),C)]/(r+1).

As réplicas usam os mesmos logits dos estados observados. Para calcular os scores, diferencie a **probabilidade original** da trajetória, tratando os tokens amostrados como fixos. Não diferencie o algoritmo auxiliar de rejeição, as tangentes ou os enclosures. Gradientes em relação aos logits podem ser acumulados antes de uma retropropagação pela rede, sem r forwards neurais adicionais.

Defina

V_o = Cov(E[G|C]),
V_h = E[Cov(G|C)].

**Teorema 2.**

E[G_r] = grad_θ E[R],
Cov(G_r) = V_o + V_h/(r+1).

**Prova.** Condicionado a C, os r+1 termos são independentes e têm a mesma distribuição. Sua média condicional é E[G|C]; sua covariância condicional é Cov(G|C)/(r+1). Aplicar esperança e a lei da covariância total fornece as identidades.

Consequentemente, para todo vetor a,

Var(a^T G_r) <= Var(a^T G),

com desigualdade estrita quando a^T V_h a>0 e r>=1. Isso vale para cada instância admitida, sem precisar escolher um benchmark onde a desigualdade apareça.

**Limites.** A variância observável V_o não desaparece. Não há promessa de melhor mínimo da rede, melhor acurácia ou menor tempo total. O resultado é para o gradiente on-policy especificado; não justifica substituir likelihoods dentro de clipping PPO/GRPO ou de razões não lineares sem nova análise.

Uma negativa por orçamento não pode descartar seletivamente trajetórias de treinamento. Um fallback decidido pelo estado observado antes das reamostragens pode usar o estimador completo original. Interrupções adaptativas baseadas nos próprios scores precisam de análise adicional.

## 7. Condição exata de benefício por custo

Para um estimador não enviesado e M trajetórias independentes,

E[||mean(G)-grad J||^2] = tr(Cov(G))/M.

Se c_0 é o custo médio do estimador original por trajetória e c_r o custo completo da versão reamostrada, a eficiência MSE por orçamento assintótico é melhor exatamente quando

c_r [tr(V_o)+tr(V_h)/(r+1)] < c_0 [tr(V_o)+tr(V_h)].

O uso de custos médios descreve o regime de muitas trajetórias; não é uma garantia de deadline rígido. Para afirmações com orçamento rígido, acrescente as caudas dos tempos aleatórios.

Com uma réplica extra, escreva c_1=(1+d)c_0 e β=tr(V_h)/tr(V_o+V_h). A condição vira

β > 2d/(1+d).

Isso localiza precisamente o que a matemática garante e o que a aplicação precisa verificar. Não há benefício universal por tempo quando V_h=0 ou quando a preparação domina.

## 8. Variante alternativa inteiramente racional com rejeição esperada <=2

Uma segunda construção usa perfis de soma arredondada, em vez de mistura de inclinações. Ela tem preparação mais cara, mas limite constante de rejeição.

Escolha 0<ε<=1 e γ=1+ε/(2km). Arredonde cada taxa oculta para cima na grade λ_min γ^j. Nos produtos do circuito, some os valores arredondados e arredonde novamente para cima, exceto quando um filho tem soma zero. Fixe a estrutura do circuito: essa operação arredondada não é associativa e não deve ser chamada de semiring genérico.

Cada caminho acumula no máximo m arredondamentos ao longo de uma cadeia de somas positivas. Por indução,

S(y) <= Shat(y) <= γ^m S(y).

Como c_r>0,

f(Shat(y)) <= f(S(y)) <= γ^(km) f(Shat(y)) <= (1+ε) f(Shat(y)).

A última desigualdade usa γ^(km)<=exp(ε/2)<=1+ε.

Guarde, em cada nó, a massa exata de cada valor de soma arredondada. Somas de alternativas somam massas; produtos convolvem perfis com a regra arredondada. O peso na raiz é massa_do_perfil vezes f(Shat).

Sortear uma derivação dessa distribuição e aceitar com

f(S(y))/[(1+ε)f(Shat(y))]

produz exatamente μ_A. O número esperado de propostas é <=1+ε, em particular <=2 para ε=1.

A quantidade de buckets é O((km/ε) log(mκ)+m). A avaliação direta custa O(F_c K^2), com K buckets, e a amostragem por busca de pares pode custar O(L_s K^2). Todas as contas são racionais. Esse backend prova uma alternativa de tempo esperado polinomial e rejeição constante, mas não deve ser anunciado como o mais rápido.

## 9. Comparadores e anterioridade

Os componentes básicos não são invenções deste texto:

1. Raajesh, Shah, Klivans e Krähenbühl, *Mask-Aware Policy Gradients for Diffusion Language Models* (2026): inclui a decisão de máscara e usa PL. https://arxiv.org/html/2607.15200v1
2. Eisenach et al., *Marginal Policy Gradients* (2018/2019): variância desnecessária quando uma ação interna é transformada antes da execução. https://arxiv.org/abs/1806.05134
3. Liu et al., *Rao-Blackwellized Stochastic Gradients for Discrete Distributions* (2019): antecedentes de redução de variância por marginalização. https://proceedings.mlr.press/v97/liu19c.html
4. Ma et al., *Learning-to-Rank with Partitioned Preference* (2021): integrais eficientes para PL com preferências particionadas. https://proceedings.mlr.press/v130/ma21a.html
5. Gadetsky et al., *Low-variance Black-box Gradient Estimates for the Plackett-Luce Distribution* (2019/2020): variáveis de controle e amostragem condicional Gumbel, um comparador relevante para treinamento. https://arxiv.org/abs/1911.10036
6. Woeginger, *When Does a Dynamic Programming Formulation Guarantee the Existence of an FPTAS?* (2000): antecedentes gerais para arredondamento em DP. https://pubsonline.informs.org/doi/10.1287/ijoc.12.1.57.11901
7. Gawrychowski, Markin e Weimann, *A Faster FPTAS for #Knapsack* (2018): antecedentes de contagem aproximada de somas. https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ICALP.2018.64
8. Su e Zhang, *Constraints Are Graphs, Not Chains* (2026): inferência estruturada compilada para dLLMs; a operação proposta aqui pode usar esse tipo de backend e não estabelece que ele seja inferior. https://arxiv.org/abs/2609.32900

A contribuição candidata específica é a redução da inferência sobre propostas latentes PL à mistura corrigida de consultas gramaticais, com o bound explícito em sqrt(k) log κ, sua implementação racional exata e o uso para reamostragem de gradientes sem novos rollouts neurais.

A busca realizada foi direcionada, não exaustiva. Não foi identificada a mesma construção completa nas fontes examinadas. Isso não prova prioridade mundial nem estabelece aceitação editorial. O argumento deve ser revisto especialmente contra técnicas gerais de envelopes de rejeição, amostragem perfeita, probabilistic circuits e variáveis de controle PL.

Comparações honestas: estimador completo que inclui a seleção; métodos de variância reduzida aplicáveis ao mesmo objetivo; reamostragem por rejeição sem inclinações; DP por somas quando as taxas têm estrutura simples; inferência de fatores que incorpore técnicas equivalentes. Não comparar latência de treinamento a uma etapa isolada de EPIC nem chamar esse sampler de acelerador de inferência final.

## 10. Verificações e limite da implementação

Os programas anexos não acessam o repositório original nem o alteram. São implementações de referência independentes da construção:

- `verify_resampling.py`: variante de perfis arredondados, gramática JSON unambígua em tokens de um caractere, sampler racional e enumeração independente para checar identidades. Nove instâncias; 42 caminhos condicionados examinados. Um segundo oráculo enumera 120 desfechos de uma política e verifica exatamente a identidade de covariância para uma réplica extra.
- `tilt_resampling.py`: mistura com limites racionais de exponenciais. Doze instâncias; 87 caminhos condicionados examinados. Verifica ponto a ponto o envelope, a massa da mistura e a distribuição após aceitação.
- `verification.json` e `tilt_verification.json`: resultados completos, incluindo as esperanças de tentativas nos pequenos casos. Não são tempos de geração nem medidas de treinamento.

O exemplo escalar de variância reduz apenas cerca de 1,83% da variância total com uma réplica: foi mantido como verificação, não selecionado para parecer uma grande vitória. A identidade geral é a evidência matemática principal.

A referência não integra tokenizer BPE, GPU, treinamento, qualquer modelo Jev ou uma política PPO. Não há claim de verificação formal total. A integração produtiva ainda precisa preservar tokens originais, memória, término, suporte e diferenciação do objetivo correto.

## Conclusão operacional

O resultado matemático especifica uma operação exata que a análise anterior não fechava: obter novas propostas latentes condicionadas à mesma ação sem quadratura e com custo controlado. Isso permite reduzir exatamente o componente latente da variância do gradiente sem alterar a geração ou pedir novas respostas ao modelo.

A vantagem provada é estatística e condicional ao contrato, com custo lógico explícito. Melhor latência real, maior qualidade final e prioridade científica não são consequências automáticas. Esses limites não anulam o teorema e também não podem ser removidos da apresentação.
