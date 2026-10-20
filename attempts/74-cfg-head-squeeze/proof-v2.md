# A74 V2 — O que é prova e o que é medição

## Referência e certificados numéricos

A lei V2 usa a tabela inteira do [protocolo](protocol-v2.md), não a lei
idealexp V1 nem torch.softmax nativo. Clipping, rounding e exclusão explícita
de EOS/mask fazem parte da definição anterior aos dados. Todos os demais
50.256 IDs permanecem com peso positivo, sem renormalização de cauda oculta.

W12,H10 em [-16384,16383] e d=768 dão soma absoluta dos produtos <=768*2^28
<2^38. A leitura independente do bias do checkpoint fixado deu
max |bias22|=10.177.900<2^30. Assim dot+bias cabe em INT64. Os produtos e
todas as somas parciais também cabem exatamente nos 53 bits de FP64.
Consequentemente GEMM FP64 é uma implementação exata desse dot inteiro
(assumindo as operações IEEE declaradas, sem TF32).

Escreva x=x0+128*x1 com x0=x mod 128 em [0,127], x1=floor(x/128) em
[-128,127]. Expandir o produto dá os quatro GEMMs INT8 do controle split.
Cada acumulação tem soma absoluta <=768*128²<2^31; recompor em INT64 não
transborda. Padding por zeros altera o tamanho físico, não o dot. O oráculo
GPU compara 1.280 células com FP64; nos estados reais foram comparados todos
os pesos dos dois caminhos, mais 64 pares por estado com somas Python int.
Esses testes são distintos da derivação algébrica e não verificam todo CUDA.

No proxy INT8 o resíduo E=W12-Q é inteiro. No SVD, os fatores A10,B10 são
inteiros produzidos pela SVD arredondada; comparar E=256 W12-A10 B10 dispensa
qualquer garantia de exatidão da SVD em reais. Os produtos dos fatores em
FP64 são inteiros exatos pelos limites de somas parciais exportados, todos
<2^53 para qualquer H10 admitido. Bias é mantido na escala correspondente.

Se rho=ceil(sqrt(sum E²)) e eta=ceil(sqrt(sum H10²)), Cauchy dá
|sum E*H10|<=rho*eta. Quadrados/somas/isqrt são inteiros com guards de
overflow. A tabela T e clip/floor são monótonos, logo consultar T nos
extremos fornece L<=w<=U. Foram verificados TODOS os 67.544.064 enclosures
(quatro proxies vezes 16.886.016 pares slot/ID), não uma amostra de IDs.

## CDF, DP e lei do output

Cada CDF acumula pesos uint64 em dois limbs. Um wrap do limb baixo ocorre
exatamente quando novo_baixo<baixo_anterior; cada adição causa no máximo um
carry. O limb alto conta esses carries. O total é <50256*2^63<2^79, portanto
128 bits bastam. Buscar primeiro o limb alto e depois o baixo equivale a
buscar a CDF inteira, inclusive zeros e limites de carry testados no oráculo.

O controle agrega quatro massas por posição. A recorrência de contagens
calcula a massa de cada sufixo; escolher modo/classe proporcionalmente à
massa e depois ID pela CDF da classe faz os fatores telescoparem em
prod_i w_i,xi / Zw. Um auditor independente multiplica polinômios para a
frente e extrai o coeficiente n/2, reconstruindo os 54 certificados de massa.
A bijeção CFG/palavras é a da V1. Aliases mantêm IDs e massas separados.

A rejeição com MESMO ticket para L e w, e o fallback independente depois de
J=4, têm a prova de [proof.md](proof.md). Aritmética inteira não significa
igualdade com outra referência numérica. A prova usa bits uniformes ideais;
os seeds de PRNG fixam a execução reproduzível, não uma prova estatística.

## Por que mudar somente o cap não resolve o custo serial observado

Para um head fixo, p=Zw/ZU, q=1-ZL/ZU, F_J=(1-p)^J. Sem cache entre
tentativas, assuma custo médio C por tentativa (incluindo consultas quando
acionadas), preparação A e custo B do fallback denso independente. Renovação
linear, sem exigir independência entre custo e aceitação da MESMA tentativa:

    E[T_J] = A + C*(1-F_J)/p + F_J*B
           = A + C/p + F_J*(B-C/p).

Logo o custo esperado é monótono em F_J. Os extremos são fallback imediato
ou repetição ilimitada; um cap intermediário não cria um mínimo adicional.
Se C/p>=B, desligar a proposta é a melhor opção neste modelo de custo.

Essa identidade é prova. Substituir C pelo MENOR custo por tentativa
observado fornece somente um diagnóstico otimista, não um lower bound físico
de tempo nem uma execução sem cap. Nos 48 diagnósticos ele já excede o
controle. Nos dois casos INT8 n=8 dá 0,455s e 0,286s, versus 5,72ms e 5,63ms
diretos, mesmo sem preparação. Os demais INT8 exigiriam da ordem de 10^12 a
10^51 tentativas em média; SVD tem p<3*10^-88. Não executar isso até completar
um draw não transforma uma recusa de tempo em argumento científico: as
massas exatas já quantificam a dificuldade da repetição serial.

## Certificado de trabalho, separado de tempo GPU

No caminho split, o head denso faz quatro GEMMs com as mesmas dimensões.
O proxy INT8 faz dois e o fallback faz quatro com probabilidade F_4. Ignorando
queries, charts, RNG e saída, o número esperado relativo é

    (2+4 F_4)/4 >= 1,4966851279 > 1

nos seis estados (desigualdade conferida racionalmente). A proposta já faz
mais trabalho desse kernel que o controle, mesmo concedendo custo zero a
todas as demais etapas. Isso não é um teorema sobre wall time de qualquer
GPU/circuito, mas elimina a interpretação "menos linhas referência significa
menos trabalho integral" para esta implementação.

No caminho FP64 SVD de posto r, os dois produtos custam nr(d+V) MACs; o
fallback denso custa ndV com probabilidade F_4. O fator relativo mínimo é
F_4+r(d+V)/(dV)>1, também nos 18 pares estado/posto. Aqui o comparador
aritmético é o controle FP64, não a soma indevida de MACs de tipos diferentes.

O pós-teste que doa projeção, limites e transferências ao candidato também
continua negativo: melhor speedup hipotético 0,4883. Doar adicionalmente
TODAS as preparações da proposta chega no máximo a 1,0532, abaixo do gate,
mas é um cenário fictício que conserva efeitos favoráveis de cache. Nenhuma
dessas subtrações é uma nova medição de um algoritmo otimizado.

Nada aqui prova que todo futuro envelope, batching, hardware ou modelo seja
ruim. O regime construído positivo da V1 continua válido. O resultado que
decide esta aposta é a derrota operacional dos proxies/envelopes fixados,
confirmada pela aceitação real e pela contabilidade completa das etapas.
