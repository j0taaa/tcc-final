# A87 — Certificados mínimos com consultas de estrelas

Estado em 2026-10-21: **provas escritas candidatas, sem prioridade científica
confirmada, sem auditoria computacional destas provas e sem benefício neural
medido**. Esta nota acrescenta uma operação distinta à hipótese de posterior
apoiado no codebook do README. Não altera fontes, protocolo ou dados congelados.

## 1. Operação nativa e contrato de informação

Há `K >= 2` palavras distintas de `N` IDs originais, com uma convenção explícita
de EOS/PAD. Dois blocos não vazios de posições, `A,B`, particionam os slots.
Uma alternativa é uma aresta `e=(a,b)`: `a,b` são tuplas de IDs dos blocos.
Não há aliases nesta operação; códigos com MASK não são alternativas.

A raiz fornece distribuições normalizadas por posição. Defina

\[
 R(a)=\prod_{i\in A}p_i(a_i\mid\mathrm{MASK}),\quad
 C(b)=\prod_{i\in B}p_i(b_i\mid\mathrm{MASK}).
\]

Fixar todo `a` em um forward fornece
`Q_B(b|a)=prod_{i in B}p_i(b_i|a)` para todos os `b` candidatos. O simétrico
vale para `Q_A(a|b)`. O alvo declarado é

\[
 J(a,b)=u_{ab}+v_{ab},\quad
 u_{ab}=\tfrac12R(a)Q_B(b\mid a),\quad
 v_{ab}=\tfrac12C(b)Q_A(a\mid b).
\]

É uma mistura de duas políticas próprias de geração em dois passos, cada uma
com produto paralelo dentro do bloco. Portanto `J` é normalizado no universo
completo de palavras, mesmo se as condicionais nativas forem incompatíveis.
Comparar o MAP em `G` não exige renormalizar a massa fora de `G`. `J` não é
afirmado como posterior verdadeiro das classes nem como lei de outro decoder.
Misturas de ordens agrupadas já aparecem em
[TUBE, §2.3](https://arxiv.org/html/2605.24292v1) e
[DUEL, Proposição D.2](https://arxiv.org/abs/2603.01367); essa definição não é
a reivindicação de novidade.

Consultar um vértice `a` revela todo o vetor `u_{ab}` incidente; consultar `b`
revela `v_{ab}`. Os caps conhecidos na raiz são
`alpha_a=R(a)/2`, `beta_b=C(b)/2`, aqui estritamente positivos. Custos de consultas `c_z>0` são dados e
aditivos. A raiz e consultas anteriores são custos já pagos.

**Classe de informação da prova.** Respostas de contextos ainda não consultados
podem ser quaisquer distribuições produto sobre o vocabulário completo. Não se
pressupõe uma distribuição global compatível, suavidade entre contextos ou acesso
a parâmetros internos. Cada bloco admite pelo menos duas palavras. Vértices de
partes diferentes correspondem a contextos distintos. Há duas versões separadas:

- **fechada:** zeros e deltas são permitidos; contribuições estão em `[0,cap]`;
- **interior:** todas as cabeças têm suporte completo estritamente positivo;
  contribuições estão em `(0,cap)`.

Uma rede fixa pode permitir informação adicional; não se afirma ótimo diante
de acesso aos seus pesos. Floats com underflow não satisfazem automaticamente a
versão interior. A política numérica deve declarar qual versão está certificada.

## 2. Sharpness do certificado de comparação

Depois de consultar `Q`, sejam

\[
 L_e=\mathbf1_{a\in Q}u_e+\mathbf1_{b\in Q}v_e,\qquad
 U_e=L_e+\mathbf1_{a\notin Q}\alpha_a+
                  \mathbf1_{b\notin Q}\beta_b.
\]

**Lema 1.** Para duas alternativas distintas `w,e`, o supremo de
`J(e)-J(w)` entre respostas consistentes com o transcript é `U_e-L_w`.
Na versão fechada esse supremo é atingido. Na interior é atingido se e somente
se todos os vértices de `w union e` já foram consultados.

**Prova.** A desigualdade superior segue dos limites de cada contribuição.
Em estrela desconhecida compartilhada, escolha uma delta na palavra de `e`;
ela dá cap a `e` e zero a `w`, pois as palavras restantes são distintas.
Em estrela exclusiva de `e`, concentre a massa na sua palavra. Em estrela
exclusiva de `w`, concentre-a em qualquer outra palavra. As deltas são produtos
de deltas nas posições e contextos diferentes são livres no contrato. Isso
atinge simultaneamente todos os extremos relevantes. No interior, aproximar
essas deltas por cabeças positivas aproxima o mesmo supremo; qualquer estrela
relevante ainda desconhecida mantém uma desigualdade estrita. Fim.

Fixe uma prioridade total para desempates. Logo `Q` certifica exatamente `w` se
as condições seguintes valem para cada rival `e`:

- fechada: `U_e < L_w`, ou igualdade e prioridade de `w` sobre `e`;
- interior: `U_e <= L_w`; na igualdade, se ambos os scores estão totalmente
  conhecidos, é necessária também prioridade de `w` sobre `e`.

Na segunda regra, igualdade com algum vértice desconhecido significa
`J(e)<J(w)` em toda realização permitida. Se a condição falha, o lema fornece
uma realização, ou uma aproximação interior suficientemente próxima dela, em
que `e` derrota `w`. Esta necessidade vale par a par; basta um rival possível
para invalidar um certificado. Não se exige realizar simultaneamente os caps de
todos os rivais. Assim, normalização e produto das cabeças não tornam estes
certificados apenas suficientes.

## 3. Certificado offline mínimo: quatro cortes ponderados

**Teorema 2.** Dadas todas as respostas reais e o vencedor `w`, um certificado
de custo aditivo mínimo, incluindo desempates, pode ser calculado com no máximo
quatro problemas de corte mínimo em grafos de `O(V+K)` arcos e vértices, onde
`V=|A|+|B|` conta as tuplas distintas. É um ótimo *offline*, calculado com
respostas já conhecidas; não é um algoritmo que obtém essas respostas de graça.

**Prova construtiva.** Enumere `S=Q intersect endpoints(w)`, quatro casos.
Fixe as decisões desses dois vértices e `tau=L_w(S)`. Para um rival `(a,b)`,
as quatro possibilidades de upper bound são

\[
 U_{00}=\alpha_a+\beta_b,\quad
 U_{10}=u_e+\beta_b,\quad
 U_{01}=\alpha_a+v_e,\quad U_{11}=u_e+v_e.
\]

Use o Lema 1 e o desempate para obter quatro booleanos `C_ij`: a comparação
está certificada quando esses endpoints são consultados? O conjunto de padrões
aceitos é monotônico, pois consultar informação real só restringe realizações.

| Condição | Restrição sobre consultas |
| --- | --- |
| `C_11` falso | Caso `S` inviável |
| `C_00` verdadeiro | Nenhuma |
| Só `00` falha | Consultar `a` ou `b` |
| `C_10` verdadeiro, `C_01` falso | Consultar `a` |
| `C_10` falso, `C_01` verdadeiro | Consultar `b` |
| `C_10,C_01` falsos e `C_11` verdadeiro | Consultar ambos |

Propague vértices obrigatórios, proibidos por `S`, e os já consultados. Uma
contradição descarta o caso. As cláusulas restantes são `x_a or x_b` e formam
vertex cover bipartido ponderado. Construa arcos `source -> a` de capacidade
`c_a`, `b -> sink` de capacidade `c_b` e `a -> b` de capacidade
`M=1+sum_z c_z` para cada cláusula. O ótimo tem capacidade menor que `M`,
portanto não corta arco de capacidade `M` e escolhe precisamente uma cobertura;
some o custo dos vértices obrigatórios. Minimize entre os quatro
casos. Toda consulta admissível pertence a um dos casos, e todas as restrições
são necessárias e suficientes pelo lema. Fim.

Para um transcript com consultas anteriores, elas ficam fixadas com custo
adicional zero. O mesmo algoritmo calcula o mínimo restante *se* as demais
respostas forem fornecidas offline. Um timeout de max-flow não é inviabilidade.

**A família completa não é sempre um único vertex cover nas queries originais.**
Tome duas arestas disjuntas `w=(a0,b0)`, `e=(a1,b1)`, com caps de `w`
`(.25,.42)` e contribuições `(.22,.40)`, e caps de `e` `(.20,.05)` com
contribuições `(.01,.01)`. No interior, seus certificados satisfazem exatamente

\[
 b0\ \lor\ [a0\land(a1\lor b1)].
\]

Os certificados minimais por inclusão são `{b0}`, `{a0,a1}`, `{a0,b1}`.
`{a0}` não certifica, mas adicionar qualquer um de `{b0,a1,b1}` certifica.
Se a família fosse um único vertex cover nessas quatro queries, uma aresta
descoberta por `{a0}` teria de ser coberta por qualquer uma dessas três adições,
portanto teria os três como endpoints, impossível em grafo. Isso distingue a
união dos quatro casos da representação direta por VC; não exclui reduções com
vértices auxiliares nem estabelece prioridade frente a outros problemas.

## 4. Fronteira natural: três blocos tornam o ótimo NP-difícil

Considere três blocos e a mistura de três políticas que geram um bloco primeiro
e os outros dois em paralelo:

\[
 J_3(x)=\tfrac13\sum_{j=1}^3
 R_j(x_j)\prod_{i\ne j}q_i(x_i\mid x_j).
\]

Cada alternativa é uma hiperaresta 3-partida; consultar um vértice revela sua
contribuição em todas as hiperarestas incidentes. O Lema 1 estende-se: uma delta
no par de blocos restantes é produto e separa alternativas distintas.

**Teorema 3.** Decidir se existe certificado de no máximo `b` consultas é
NP-completo para essa operação com três blocos, mesmo com um token por bloco,
custos unitários, cabeças racionais estritamente positivas e vencedor único.
O vocabulário é parte variável da entrada; a afirmação com três tokens não é
uma redução em vocabulário de tamanho constante.

**Redução.** Parta de vertex cover em hipergrafo 3-partido 3-uniforme `H`, com
partição fornecida. Essa restrição já é NP-difícil; ver
[Meliou et al., Lema B.1](https://www.vldb.org/pvldb/vol4/p34-meliou.pdf).
Seja `m>=1` o maior tamanho de uma parte e `C=1/[3(m+3)]`. Cada vértice comum
tem cap `C` e contribuição real `g=C/(4m^2)` em toda aresta incidente.
Acrescente duas alternativas com vértices exclusivos em cada parte:

| Alternativa | Cada um dos três caps | Cada contribuição real | Score |
| --- | --- | --- | --- |
| Vencedor `w` | `C` | `17C/20` | `51C/20=2.55C` |
| Rival `d` | `71C/100` | `7C/10` | `21C/10=2.10C` |

As probabilidades de raiz são três vezes os caps. Em cada posição sua soma
nos símbolos usados é `(n_j+1+.71)/(m+3)<1`; distribua a sobra positivamente
nos demais símbolos. Em contexto comum, dê a cada símbolo comum de cada outra
parte probabilidade `1/(2m)`, com a sobra distribuída positivamente. Isso produz
`g`. Em contexto de `w`, dê aos seus dois símbolos restantes probabilidades
`17/18` e `9/10`, produto `17/20`. Em contexto de `d`, use `140/141` e
`141/142`, produto `70/71`; multiplicado pelo cap `71C/100` dá `7C/10`.
Assim, a instância usa distribuições produto normalizadas e racionais; os
contextos são diferentes, portanto não precisam satisfazer compatibilidade.

Qualquer certificado deve consultar os três vértices de `w`: omitir um deixa
seu lower bound em no máximo `1.70C`, abaixo do score real `2.10C` de `d`.
Depois dessas três consultas, `d` está eliminado pelo seu upper bound `2.13C`.
Uma hiperaresta comum não consultada tem upper bound `3C>2.55C`. Consultar
qualquer um de seus vértices reduz esse upper bound a
`2C+g<=2.25C<2.55C`. Portanto as demais consultas devem e bastam cobrir `H`:

\[
 \mathrm{OPT}_{\rm cert}=3+\tau(H).
\]

A construção tem tamanho e números de bits polinomiais, e um certificado pode
ser verificado por comparações racionais em tempo polinomial. Isso prova
NP-completude e a fronteira de tratabilidade 2/3 nesta família. Não é uma
garantia de que três blocos sejam lentos em todos os casos, nem impede FPT,
aproximações ou soluções fáceis para suportes particulares.

## 5. Controle online: best-first tem limite preciso, mas é conhecido

No contrato interior e com vencedor único, considere: enquanto nenhum vencedor
estiver certificado, escolha uma aresta de maior upper bound e consulte todos
os seus endpoints ainda desconhecidos. Cada rodada custa no máximo duas
consultas. Para custos unitários,

\[
 \mathrm{ALG}\le 2\mathrm{OPT}+1.
\]

**Prova.** Se a aresta escolhida não é o vencedor real, seu upper bound é
estritamente maior que o score vencedor: se o vencedor está incompleto seu
upper bound é maior; se está completo, igualdade já permitiria parar pelo
contrato interior. Deixar desconhecidos todos os novos endpoints dessa aresta
permite aproximar uma delta que a faça derrotar o vencedor. Logo cada
certificado consulta pelo menos um desses endpoints. Rodadas diferentes usam
vértices novos disjuntos e custam no máximo dois, permitindo a cobrança a OPT.
O vencedor só pode ser escolhido uma vez. Se nessa rodada faltam dois endpoints,
OPT precisa de pelo menos um deles, pois sem ambos o lower bound vencedor é
zero e há um rival de score positivo; essa rodada também é cobrada. Se falta
um só endpoint, ele pode ser dispensável para OPT e custa no máximo `+1`. Fim.

**Sharpness.** Para cada `k>=1`, tome arestas `w=(r0,c0)`, `e=(r0,c1)` e
`k` arestas disjuntas `(ri,ci)`. Multiplique todos os números abaixo por
`lambda=1/(k+2)`; massas de raiz restantes ficam fora das alternativas.

| Aresta | Cap da linha | Cap da coluna | Contribuição linha | Contribuição coluna |
| --- | --- | --- | --- | --- |
| `w` | `.30` | `.20` | `.23` | `.01` |
| `e` | `.30` | `.21` | `.01` | `.001` |
| Cada `(ri,ci)` | `.20` | `.09` | `.01` | `.001` |

Os caps de cada parte somam menos de `1/2` e todas as contribuições são
realizáveis por condicionais positivas; na linha compartilhada as duas
probabilidades somam `.8`. O algoritmo consulta `r0,c1`, depois `c0`, depois
ambos os endpoints de cada aresta disjunta: `2k+3` consultas. O certificado
`{r0,r1,...,rk}` custa `k+1` e é mínimo: cada aresta disjunta exige um endpoint
e algum endpoint vencedor é necessário. Portanto `ALG=2OPT+1`. Em particular,
`k=1` dá cinco consultas contra duas e refuta a alegação `ALG<=2OPT`.

Esse controle adapta uma técnica antiga, não é apresentado como método novo.
[Erlebach e Hoffmann, §§3,7](https://bulletin.eatcs.org/index.php/beatcs/article/download/335/317)
expõem witness sets e a cobrança `d*OPT+d` para cheapest-set de tamanho `d`.
A prova acima trata revelação vetorial e refina a constante aditiva; isso não
basta para estabelecer uma contribuição central de inferência.

## 6. Custos completos, antecedentes e decisão ainda aberta

Se probabilidades de cabeças são racionais com no máximo `B` bits por numerador
e denominador, produtos de até `N` fatores e somas de duas contribuições usam
`O(NB)` bits. Construir todos os scores exige `O(KN)` operações de produto,
além de obter as respostas. Após scores prontos, os quatro casos usam `O(K)`
comparações racionais e quatro cortes. Para custos racionais de `D` bits,
limpar denominadores dá capacidades inteiras de `O(VD+log V)` bits.
Edmonds–Karp fornece o limite conservador de
`O(V*(V+K)^2*(VD+log V))` operações de bits nos cortes, além de multiplicações
e comparações de scores com `O(NB)` bits e da preparação dos denominadores dos
custos, limitada por `O(V*M(VD))`, onde `M(t)` é o custo de multiplicar inteiros
de `t` bits. Algoritmos de fluxo melhores podem reduzir esse limite; não se
pressupõe aritmética real de custo unitário. Uma realização com floats deverá
declarar racionalização/normalização das cabeças ou intervalos certificados;
comparar floats arredondados não estabelece automaticamente esse alvo racional.

Obter o transcript offline inteiro custa uma raiz mais `V` canvases condicionais,
projeção/normalização do vocabulário e produtos das arestas incidentes. Manter
apenas contribuições incidentes custa `O(KNB)` bits; os logits temporários,
modelo, máscaras e ativações são custos adicionais. Se o modelo for batched,
`V` canvases não significam `V` chamadas seriais: tempo por batch e memória
devem ser medidos. O teorema ponderado pressupõe custos aditivos declarados;
não otimiza automaticamente uma latência não aditiva de batches.

Antecedentes próximos, sem alegar subsunção completa onde ela não foi provada:

- [Megow e Schlöter, §4.2](https://arxiv.org/html/2211.01097v2#S4.SS2)
  já têm MinCover com coeficientes vetoriais revelados juntos. Fixados `S,tau`,
  nossa suboperação é exatamente uma restrição desse modelo: requisito
  `alpha_a+beta_b-tau`, com coeficientes `alpha_a-u_e`, `beta_b-v_e`.
  A parte candidata é o ótimo exato bipartido com quatro escolhas do vencedor,
  a comparação sharp sob produtos normalizados e a fronteira de três blocos.
  Sua garantia estocástica não se transfere sem as hipóteses de distribuição.
- [Diwan et al., Corolário 28](https://drops.dagstuhl.de/storage/00lipics/lipics-vol364-stacs2026/LIPIcs.STACS.2026.32/LIPIcs.STACS.2026.32.pdf)
  já obtêm certificados mínimos por vertex cover bipartido para bases de
  matroides incertos, consultando um peso escalar por elemento. A ideia geral
  certificado/corte não é nova. Aqui uma estrela revela contribuições diferentes
  para várias alternativas. A família não é sempre um único vertex cover nas
  variáveis de consulta: tome `w` com caps `(.25,.42)` e contribuições
  `(.22,.40)`, e um rival disjunto com caps `(.20,.05)` e contribuições
  `(.01,.01)`. Seus certificados mínimos são `{b0}`, `{a0,a1}`, `{a0,b1}`.
  A maioria coordenada desses três conjuntos é `{a0}`, que não certifica.
  Soluções de 2-CNF, incluindo vertex covers e projeções existenciais de
  auxiliares, são fechadas por maioria: aplique maioria às três atribuições
  completas testemunhas; cada cláusula de duas literais continua satisfeita.
  Isso impede um único gadget de VC que preserve a viabilidade das variáveis
  originais. Não exclui outras reduções, representações ou uniões por bases.
- [CAS, §7.2 e Apêndice C.6](https://arxiv.org/html/2610.14996v1)
  trata decisão top-k por intervalos e aquisição por previsões, mas delimita
  explicitamente a não transferência de seu ótimo aos experimentos com
  primitivas compartilhadas. Seu framework de witnesses é controle obrigatório.
- [IO-Top-k](https://www.vldb.org/conf/2006/p475-bast.pdf)
  já usa upper/lower bounds e agendamento de acessos em blocos para top-k.
  Branch-and-bound, previsão apenas para aquisição e cache de componentes não
  serão tratados como novidade.

**Utilidade comprovada aqui:** o menor transcript suficiente pode ser calculado
offline em dois blocos; três blocos já incluem uma otimização NP-difícil. Isso
permite medir o espaço possível de economia antes de projetar uma política.
Não prova que o alvo classifica melhor, que há compartilhamento útil em dados
naturais, ou que qualquer algoritmo online melhora custo integral.

**Próximo gate necessário:** diagnóstico prospectivo do ótimo em famílias
naturais que compartilham metades, com target/IDs/split/custos congelados, antes
de uma campanha de políticas. Rótulos de intents compostos podem ser candidatos
a examinar; não se afirma que BANKING77 já passe o gate. MCQs sem reutilização
de metades não demonstram benefício da parte compartilhada. Produtos em blocos
longos podem produzir caps exponencialmente frouxos, impedindo poda útil.
Controles precisam incluir os dois blocos completos batched, best-first acima,
avaliação lazy que compra uma ponta por vez e reavalia a parada, CAS/Upper e
scoring em uma ordem/trie; qualidade também exige dJev com índice
de um token e readouts conhecidos. Uma política que use planos de certificado
previstos poderia ser investigada, mas ainda não foi definida nem provada
melhor que esses controles. **Nenhuma campanha ou seleção central decorre
apenas desta nota.**

Consultar as duas pontas de uma vez não é o controle prático mais forte: na
família apertada da seção 5, revelar primeiro a linha e reavaliar já elimina
cada rival disjunto com uma consulta. Além disso,
[Erlebach et al., ESA 2022](https://drops.dagstuhl.de/storage/00lipics/lipics-vol244-esa2022/LIPIcs.ESA.2022.49/LIPIcs.ESA.2022.49.pdf)
já combinam previsões, consultas obrigatórias, vertex cover bipartido,
parceiros-testemunha e fallback em matroides. Um plano previsto por mincut com
fallback seguro não estabelece, sozinho, método próprio nem melhoria frente
a esses controles. A parte online específica desta operação permanece aberta.

## Protocolo executável CPU V1 — produtor a congelar antes da execução

Fonte nova: [star_certificates.py](star_certificates.py), independente de
`oracles.py` e dos dados anteriores. Executar apenas após o commit produtor:

```bash
.venv-live/bin/python attempts/87-conditional-choice-readout/star_certificates.py --audit
```

O script usa stdlib e NetworkX, `Fraction` em scores/caps/custos e capacidades
inteiras após limpar denominadores. Enumera os 511 subgrafos não vazios dentre
os 512 grafos bipartidos `3 x 3`; o suporte vazio é excluído explicitamente.
Em cada grafo há três padrões fixos, custos unitários ou `1+i%3`, caps iguais
a um e contrato interior. Para a aresta `(a,3+j)`, os padrões são:

1. `u=v=1/8`;
2. `u=(1+(3a+2j)%7)/32`, `v=(1+(a+5j)%9)/40`;
3. `u=(1+(a+2j)%3)/8`, `v=1/2-u`, com prioridade inversa nos empates.

São 3.066 instâncias principais. Os caps unitários são uma escala algébrica
comum; não são afirmados como massas de raiz nativas normalizadas. As massas
incidentes deixam sobra em toda estrela e admitem realização por um símbolo
fora do codebook. Para cada instância, comparar o custo do mincut com todos os
64 conjuntos de consultas, usando um segundo predicado que constrói os extremos
das diferenças por respostas delta, sem chamar o cálculo de bounds/mincut.
Conferir também o vencedor devolvido por best-first, inclusive seu desempate.

Há ainda 256 casos com todos os priors no grafo completo, contratos fechado e
interior, e custos unitários ou `(i+1)/(i+2)`. Casos nomeados cobrem igualdade de
bounds com prioridade contrária nas duas versões, zeros/deltas na fronteira
fechada, a família de certificados que não é um único VC, e a família apertada
de best-first para `k=1,2,3,4`, com até 11 vértices e 2.048 subconjuntos.
Nenhum sorteio, modelo, medição de latência ou gate de performance integra o
protocolo. O script imprime somente JSON com contagens e resultado; não grava
resultados automaticamente. Uma falha ou interrupção deve ser preservada pelo
executor; não é autorização para trocar padrões depois dos dados.
