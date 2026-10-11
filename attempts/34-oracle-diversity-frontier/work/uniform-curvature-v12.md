# Esperança uniforme também limita a curvatura: prova escrita

2026-10-11. Addendum analítico A34, antes de implementação/campanha. Não
reivindica prioridade, solução inédita de problema aberto ou novo uso neural.
As demonstrações V11 e os diagnósticos negativos permanecem preservados.

## 1. Enunciado e operação

Use o MESMO procedimento p-blind, output limitado |H|<=C e término a.s. de
`uniform-budget-score-v11.md`. Em cada compacto I interior ao domínio,
seja b_I=sup_{p em I}E_pN<infinito. A média g(p)=E_pH tem derivada localmente
Lipschitz: para x,y em I,

    |g'(y)-g'(x)| <= [2C b_I / min_{p em I}p(1-p)] |y-x|.

Assim g pertence localmente a C^{1,1}, não apenas C1. A afirmação NÃO exige
cauda uniforme do primeiro momento. NÃO afirma g'' contínua ou existente em
todos os pontos. O enunciado segue de identidades clássicas de score/Wald
e aproximações finitas; a prioridade de sua especialização permanece aberta.

## 2. Prova sem diferenciar uma série infinita duas vezes

Defina g_m(p)=E_p[H 1_{N<=m}]. Esta é uma soma FINITA de monômios de folhas
a_u p^s q^(n-s), com q=1-p. Sua segunda derivada é

    g_m''(p)=E_p[H 1_{N<=m} L_{2,p}],
    L_{2,p}=W_N^2/(p q)^2 - S_N/p^2 - (N-S_N)/q^2,
    W_N=S_N-pN.

Não se aplicou essa identidade diretamente a g. Para m finito ela é só
diferenciação de um polinômio. A parada é previsível e E_pN finita, logo
Wald e a soma L2 de incrementos parados dão

    E_pS_N=p E_pN,
    E_p(N-S_N)=q E_pN,
    E_pW_N^2=p q E_pN.

Como W_N^2, S_N e N-S_N são não negativos, restringir a N<=m somente reduz
cada termo. Portanto, para TODO m,

    |g_m''(p)|
      <= C [E_pW_N^2/(p q)^2 + E_pS_N/p^2
                                  + E_p(N-S_N)/q^2]
      = C E_pN [1/(p q)+1/p+1/q]
      = 2C E_pN/(p q).

Não substituímos W_N por N: isso exigiria desnecessariamente E_pN^2. Em I,
o lado direito é no máximo L_I=2C b_I/min_I(p q). Pelo teorema do valor médio,
|g_m'(y)-g_m'(x)|<=L_I|y-x| para todos m,x,y. A prova V11 já estabeleceu
convergência uniforme g_m'->g' em I. Passar ao limite dá o bound do enunciado.
QED. Na verdade, convergência pontual das derivadas bastaria neste último
passo; a justificativa de g'=lim g_m' não foi omitida.

Para H que assume valores em [a,d], subtraia a constante (a+d)/2 do output
ANTES de construir as aproximações. A média muda só por constante e
C=(d-a)/2. Logo a constante do bound passa a

    L_I=(d-a) b_I / min_I(p q).

Em particular, para um output Bernoulli, L_I=b_I/min_I(p q). Não subtrair
uma constante de g_m sem considerar a massa do evento N<=m: a aproximação
centrada é E_p[(H-(a+d)/2)1_{N<=m}], que converge à média centrada.

## 3. Consequência necessária além de C1

Considere a função definida em (0,1)

    f(p)=1/2 + (1/4)|p-1/2|^(3/2).

Ela tem range estritamente dentro de (0,1) e primeira derivada contínua:

    f'(1/2)=0,
    f'(p)=(3/8)sign(p-1/2)sqrt(|p-1/2|),  p!=1/2.

Porém |f'(1/2+h)-f'(1/2)|/|h|=3/(8sqrt(|h|)) diverge. Sua derivada não é
Lipschitz em nenhum intervalo ao redor de1/2. Pelo enunciado, nenhum factory
desse contrato tem esperança UNIFORMEMENTE finita nesse intervalo.

Isto mostra que C1 SOZINHO não é uma condição suficiente para orçamento
uniforme do primeiro momento. A Questão3 de Nacu--Peres admite condições
técnicas adicionais: não se diz que toda formulação possível daquela questão
foi refutada, nem que este exemplo não era conhecido depois de2005. O
resultado não decide se E_{1/2}N pode ser finita enquanto os custos vizinhos
divergem; a hipótese desta nota é uniforme, não pontual.

## 4. Leitura e fronteiras

`primary-reading-v12.md` registra os ORIGINAIS Nacu--Peres22/23/Questão3 e
Holtz--Nazarov--Peres8/13/Seção7. HNP já associa momentos a escalas de
regularidade e sugere Besov; isso é antecedente central, não tema criado
aqui. A prova acima usa a escala do passeio compensado, cujo segundo
momento é proporcional a E N, em vez do bound grosseiro por N^2.
Esta comparação literal de enunciados NÃO estabelece prioridade histórica
ou importância suficiente para publicar. Não anexar falsamente revisão humana.

A esperança uniforme não necessariamente torna o segundo score uniformemente
integrável. Por isso NÃO se conclui que g'' seja contínua, que g pertença a C2,
ou que a fórmula da segunda derivada valha pontualmente para todo p. Tais
afirmações exigem demonstrações adicionais. Na presente nota somente
curvatura das aproximações finitas e Lipschitz de g' foram demonstradas.

## 5. Oito critérios reavaliados

1. **Uso:** delimitar transformações de probabilidades desconhecidas de eventos
   de um decoder dLLM+GLC por draws, sem trocar a lei nativa pela do posterior.
   A fronteira ótima A34 e seu uso barato ainda são obrigações separadas.
2. **Diferença:** necessidade quantitativa de regularidade sob budget, não
   score/Wald/curvatura como princípios novos. Pode ser um lema conhecido.
3. **Escolha:** impedir promessa de um orçamento uniforme impossível para
   uma transformação C1 sem derivada Lipschitz. Não é, sozinho, um decoder
   melhor ou a contribuição útil final pedida pelo usuário.
4. **Matemática:** somente diferenciações FINITAS, identidades de martingais
   e passagem ao limite já justificada. Não depende de teste de desempenho.
5. **Experimentos:** nenhum. O exemplo é objeto de prova; não benchmark que
   compara modelos, e não fornece vitória prática/qualidade.
6. **Custos:** número TOTAL de bits/draws e output limitado; hardware,
   side information, probabilidades conhecidas e forwards não são confundidos.
7. **Objeção:** antecedente pode conter o mesmo bound; C1,1 pode ser condição
   conhecida insuficiente. Uma restrição/impossibilidade não satisfaz a meta
   do usuário sem uma solução positiva comparativa útil.
8. **Artigo:** fechar prioridade da fronteira A34 e aplicação. Esta nota
   não autoriza iniciar implementação extensa ou declarar publicação digna
   confirmada. Não promover a consequência negativa a produto final.
