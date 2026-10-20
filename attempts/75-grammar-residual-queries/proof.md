# Prova escrita A75 e ataques ao contrato

Esta é uma derivação escrita, não prova Lean, revisão humana ou garantia de
todo o software. Parâmetros: c>0 fixo, 0<α≤α₀≤1, n par positivo, P e R
como no README. Normas são sob x~R; A é independente, uniforme por tamanho
r~Unif{0,…,n−1}, e l=n−r. Todos os logaritmos são naturais.

## 1. Gramática, suporte e identidade residual

S→0T1S | 1U0S | ε; T→0T1T | ε; U→1U0U | ε.
T reconhece excursões não negativas, U as não positivas. A primeira volta
ao equilíbrio fixa unicamente a primeira excursão de S e sua decomposição
recursiva. FIRST(S)={0,1}, FIRST(T)={0}, FIRST(U)={1};
FOLLOW(S)={EOF}, FOLLOW(T)={1}, FOLLOW(U)={0}. As predições são disjuntas:
é LL(1). A união dos comprimentos é não regular, pois sua interseção com
0*1* é {0^k1^k}; cada G_n isolada é finita e portanto regular.

Para cada x no suporte, a regra da cadeia em qualquer permutação π dá
Σ_j log[P_{π_j}(x_{π_j}|x_{π_{<j}})/R_{π_j}(x_{π_j}|x_{π_{<j}})]
=log[P(x)/R(x)]=h(x). Sortear j e depois tirar a média sobre a próxima
posição produz

W_A(x)=(n/l)Σ_{i∉A}δ_i(x_i), E_A W_A(x)=h(x).

R permanece a mesma lei, com condicionais k/l, em todas as consultas.
Pins forçados têm δ=0, pois P e R têm o mesmo suporte. Alterar R por máscara
ou usar heads inconsistentes invalida a identidade. F geral é permitida.

## 2. Oscilação e concentração sem reposição

Fixe A,x_A, e 0<k<l. Acople R(.|X_i=0) e R(.|X_i=1) escolhendo uma
configuração com k uns nas outras l−1 posições e trocando i com um desses
uns uniformemente. O resultado é uniforme na outra fibra; a distância é
exatamente dois. Logo as médias condicionais de F diferem por ≤2αc/√n.
Como ambas são ≥1, |log E[F|i=1]−log E[F|i=0]|≤L/√n, L=2αc.
Em δ_i=log E[F|A,i]−log E[F|A], o segundo termo é constante.
Além disso E_R exp δ_i=1. Hoeffding para variável num intervalo de largura
L/√n dá −L²/(8n)≤E_R δ_i=−KL(R_i||P_i)≤0.

Escreva g_i(X_i)=a_i+b_i X_i, |b_i|≤b. Revele sucessivamente os l bits
de uma fatia uniforme. Se restam m posições, a diferença entre os dois
valores possíveis da próxima expectativa de Doob é
b_i−(Σ_{j posterior}b_j)/(m−1), de módulo ≤2b (m=1 é determinístico).
Assim cada diferença tem amplitude ≤2b e
E exp(t(S−ES))≤exp(t²lb²/2). Integrar a cauda de Azuma dá, para p≥1,
||S−ES||_p≤2b√(pl). Isto inclui coeficientes de ambos os sinais;
não presume independência dos bits. Com b=L/√n,

||W_r||_p≤2L√(pn/l)+L²/8≤C√(pn/l), C=2L+L²/8.

O termo de média não cresce com n; omiti-lo mudaria a constante. Minkowski,
Jensen em A e Σ_{l=1}^n l^(−1/2)≤2√n implicam
||h||_p, ||h_B||_p≤2C√p, h_B=E_A clip_B W_A.

## 3. Cauda integrada, normalização e factory clássico

Ponto a ponto |W−clip_B W|≤min(|W|,|W|³/B²), logo sua norma Lp é
≤min(C√(pn/l), C³(3p)^(3/2)(n/l)^(3/2)/B²). A função de l/n é
decrescente; a soma direita dividida por n é ≤a integral em (0,1).
Estender a segunda parte até infinito, com cruzamento t₀=d/a, dá
∫₀^∞ min(a t^(−1/2),d t^(−3/2))dt=4√(ad). Portanto

||h−h_B||_p≤K₀ C²p/B, K₀=4·3^(3/4).

Defina M_C=Σ_{j≥0}(4C)^j j^(j/2)/j!, com termo j=0 igual a 1.
O quociente de termos é ≤4C√e/√(j+1), portanto a série converge.
Os momentos acima dão E exp(2|h|), E exp(2|h_B|)≤M_C, de modo que
||e^h||₂,||e^h_B||₂≤√M_C. Pela desigualdade
|e^u−e^v|≤|u−v|(e^u+e^v), Cauchy–Schwarz e normalização,

TV(P,R e^h_B/Z_B)≤E_R|e^h−e^h_B|≤4K₀C²√M_C/B.

A primeira desigualdade usa E_R e^h=1: a diferença de normalizadores é
≤E|e^h−e^h_B|, inclusive quando Z_B<1. Jensen fornece
Z_B≥exp(E h_B)≥e^(−2C).

FORS: sorteie x~R, J~Poisson(2B), e J incrementos independentes dado x.
A aceitação média é exp(h_B(x)−B). Repetir dá Q_B=R e^h_B/Z_B.
Sem interromper cedo, custo esperado de queries por amostra é
2B e^B/Z_B; propostas esperadas são e^B/Z_B. A identidade vale apesar da
dependência entre custo J e aceitação: resolva a recorrência da renovação.
O mecanismo inteiro é antecedente FORS/SIRS, não contribuição A75.

Para c,α₀ fixos, D=4c+α₀c²/2 dá C≤Dα e M_C≤M_{Dα₀}.
Escolher K≥4K₀D²√M_{Dα₀}/κ e B=Kα garante TV≤κα e
E NFE≤2Kα exp((K+2D)α)=O(α), uniforme em n.
É um resultado assintótico; K pode ser enorme. Testar B=α não é testar
essa constante universal. α=0 usa R diretamente, sem dividir por B=0.

## 4. Witness e limite de consultas

Para 4|n, T é o número de uns na primeira metade e
g=1/[1+c²((T−n/4)/√n)²]. Sua derivada em T tem módulo
≤9c/(8√(3n))<c/√n, e |ΔT|≤d_H. F_+=1+αg,
F_−=1+α(1−g) pertencem à classe. O complemento global preserva g,
logo todas as marginais raiz de ambos os alvos são exatamente 1/2.
Isso impede identificação pela **consulta raiz**, sem alegar o mesmo de
uma consulta arbitrária com pins.

O CLT hipergeométrico padrão dá (T−n/4)/√n⇒N(0,1/16).
A função limitada g converge em lei e em seus primeiros momentos;
E|g−Eg| converge a uma constante positiva para c>0. Diretamente,

TV(P_+,P_−)=α(2+α)E|g−Eg|/(2Z_+Z_−)=Θ(α).

Até a primeira consulta os dois algoritmos têm o mesmo transcript.
Acoplando seus bits, os outputs só podem diferir se houver consulta;
TV(Q_+,Q_−)≤Pr(NFE≥1)≤E NFE (em cada alvo).
A desigualdade triangular exige E NFE≥TV(P_+,P_−)−2κα.
Para κ menor que metade da constante assintótica, é Ω(α).
Portanto Θ(α) é ótimo nessa classe e interface, com tolerância adequada,
para n suficientemente grande. Não é superioridade sobre FORS, algoritmos
com a fórmula F, todas as tolerâncias ou todos os MCMCs.

## 5. Controle estacionário e referência gratuita

Se um protocolo completo K preserva P e mantém x quando não consulta,
escreva K(x,.)−δ_x=q(x)[K₁(x,.)−δ_x]. Usando PK=P,
RK−R=(R−P)(K−I), logo
TV(RK,R)≤Σ_x|R(x)−P(x)|q(x)≤κ_F E_R NFE,
κ_F=||P/R−1||∞≤α. Reduzir TV(R,P)=d à metade exige
E_R NFE≥d/(2κ_F)=Ω(1) para o witness.
Pair heat bath satisfaz o contrato e move o estado; single-site fica
congelado. Refresh/movimentos gratuitos de R violam o ramo identidade e
ficam **fora** desse limite. Rejeição residual também fica fora.

Na antiga instância hard-core com tilt só do total S, as marginais raiz
reconstroem o histograma por um sistema combinatório. Há
C_s=binom(n−s+1,s) palavras de contagem s; A_{i,s} conta as que têm bit i=1
e é obtido contando independent sets à esquerda e à direita dos vizinhos
excluídos. Então P(X_i=1)=Σ_s(A_{i,s}/C_s)P(S=s). Junto à normalização,
essas equações permitem inversão quando a matriz tem posto completo.
A auditoria verificará o posto para n=8, sem presumir fórmula geral aqui.
Uma vez reconstruída P, decompor P=mR+(1−m)H, m=min P/R, permite
consultar só no ramo de probabilidade O(α) e amostrar exatamente.
Esse controle especializado empata O(α); não se transfere à F geral nem
ao par BALANCE com raízes idênticas. A auditoria finita verificará o posto
e a decomposição, sem reivindicar que construiu uma nova primitiva.

## 6. Ataque à ponte neural e custo em bits

Heads projetados por máscara não precisam ser condicionais coerentes.
Exemplo n=4: head raiz uniforme dá R; após fixar X₀=0, aumente só o peso
de X₁=1 por fator 9 antes de projetar o produto na contagem restante 2.
A projeção dá P₁(1|X₀=0)=18/19, mas a condicional da raiz é 2/3.
Se após fixar X₁=1 o head ficar uniforme, o produto da cadeia para
(X₀=0,X₁=1) é 9/19 em uma ordem e 1/3 na outra. Cada projeção é
válida; inexiste a conjunta postulada. A auditoria usa frações exatas.

Se um modelo coerente P_all tem massa fora de G, a regra da cadeia em G
gera h=log(P_all(.|G)/R)+log P_all(G). Essa constante cancela sem clipping
na lei normalizada, mas prejudica a aceitação e invalida os limites usados;
o clipping tampouco comuta com sua remoção. Pinos forçados por R podem
continuar probabilísticos em P_all. Nem podar o vocabulário nem renormalizar
cada head resolve a coerência. Um posterior produto congelado pode ser
coerente se preparado uma vez e depois condicionado pelo parser, mas então
as novas consultas não são forwards: a operação mudou, pagando root+parser.

Um softmax finito do LLaDA local dá probabilidade positiva também a IDs
fora dos dois símbolos. Seu código fornece logits por posição, não um
oráculo certificado de P(.|G). A inspeção desse contrato precede qualquer
carregamento; sem ponte, a campanha neural deve ser registrada como
NOT_APPLICABLE_ORACLE_CONTRACT, não como refutação matemática ou speedup.

R usa subconjunto uniforme de n/2 índices por Fisher–Yates parcial. Cada
randbelow usa rejeição de bits e custo esperado O(log n); não se materializa
binomial de n bits. O(n) palavras/O(n log n) bits de índices e RNG, além
dos n símbolos da saída. Por máscara, o denominador da soma é
k log(k/l)+(l−k)log(1−k/l), omitindo termos 0 log 0, não infinitos.
Os condicionais sintéticos P têm denominadores de muitos bits: contar seu
custo e preparação exponencial. Um simulador intervalar de precisão finita
pode recusar comparações indecididas; não equivale ao Bernoulli ideal de
precisão adaptativa ilimitada nem estabelece exatidão binária neural.
