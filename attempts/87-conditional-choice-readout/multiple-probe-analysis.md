# A87 — múltiplas auditorias: análise separada da V1

Prova escrita nova; **não altera fontes, protocolos ou dados congelados da V1**.
Nenhum oráculo CPU desta extensão, forward, campanha ou ganho de modelo foi
executado/estabelecido por esta nota. A operação abaixo é de fundamentos de
algoritmos; sua utilidade neural e prioridade específica são questões distintas.

## 1. Contrato estático, custos e algoritmo

Seja H=(V,E) finito, com consultas de custo unitário. Uma instância real fixa
antes dos sorteios define M⊆V e respostas determinísticas. Exigimos exatamente:

1. Q é certificado se, e somente se, M⊆Q e Q é vertex cover de H.
2. Para cada alvo previsto p há uma testemunha selecionada u(p). Uma consulta
   de u(p) decide um teste; **aprovação implica p∈M**, no problema original.
3. Depois de consultar qualquer cover C, a conclusão requer somente um conjunto
   F⊆M de consultas ainda ausentes. A resposta final é validada com dados reais.

Isto implica OPT=|M|+vc(H−M). MVC é exato; se H é bipartido, usa-se mincut
polinomial, mas o teorema de contagem não presume tempo unitário para o solver.
Forecaster fornece o conjunto fixo Mhat de alvos e suas testemunhas. Não se
recalculam Mhat nem a distribuição dos alvos durante os sorteios.

Fixe inteiro k≥1. Prepare Cpred=MVC(H−Mhat), P=Mhat∪Cpred e C0=MVC(H).
Se Mhat=∅, consulte C0 e as pendências F. Caso contrário, sorteie k alvos iid
uniformes de Mhat **com reposição**. Consulte/cacheie u(p), parando na primeira
rejeição. Aprove P somente se os k testes aprovarem; caso contrário use C0.
Consulte o cover escolhido e depois F. Toda consulta duplicada é deduplicada.
Não há parada probabilística sem certificado real. Os sorteios repetidos não
se transformam em amostragem sem reposição por haver cache de respostas.

No oráculo A87 de dois blocos com limiar τ conhecido, uma realização CLOSED
deste contrato usa E={ab:α_a+β_b>τ}, componentes reais u_e,v_e com u_e+v_e<τ,
e certificado U_e(Q)≤τ. O incumbente tem preferência em empates hipotéticos;
isso certifica sua vitória, não unicidade em todas as completações adversárias.
M são os alvos dos arcos reais u_e+β_b>τ ou v_e+α_a>τ. Cada consulta revela uma
estrela. Obter o incumbente/τ e preparar posições já conhecidas tem custo próprio,
fora deste problema residual. Outra regra de empate exige outro contrato.

## 2. Garantia com k auditorias

Escreva m=|Mhat|, t=|Mhat∩M|, f=m−t, u=|M\Mhat| e g=|M|=t+u.
Para um certificado ótimo Q*, Q*\Mhat cobre H−Mhat. Portanto

\[
|Cpred|\le OPT-t,\quad |P|\le OPT+f,\quad
|F\setminus P|\le u\le OPT-t.
\]

Seja A o evento de aprovar os k testes. Cada alvo aprovado é realmente
mandatory, logo Pr(A)≤(t/m)^k. Isso continua válido com respostas cacheadas:
o evento A está contido em “todos os k alvos sorteados pertencem a M”.
Há no máximo k consultas de auditoria. No ramo aprovado,

\[
ALG\le k+|P|+|F\setminus P|\le k+2OPT+m-2t.
\]

No ramo rejeitado, |C0|≤OPT e |F\setminus C0|≤g≤OPT, logo ALG≤k+2OPT.
Se m≤2t, ambos os ramos custam no máximo k+2OPT. Caso m>2t, ponha x=t/m<1/2:

\[
\mathbb E ALG\le k+2OPT+(m-2t)x^k
=k+2OPT+t\,x^{k-1}(1-2x).
\]

Para k≥2, a derivada é x^(k−2)[(k−1)−2kx]; o máximo ocorre em
x_k=(k−1)/(2k). Para k=1, o supremo é 1 quando x tende a zero. Assim,

\[
\boxed{\mathbb E ALG\le(2+c_k)OPT+k},\qquad
c_1=1,\qquad c_k={1\over k}\left({k-1\over2k}\right)^{k-1}\ (k\ge2).
\]

Em particular c2=1/8 e c3=1/27. Como c_k≤2^(1−k),
k≥1+ceil(log2(1/ε)) basta para o limite (2+ε)OPT+k. Este é um limite de
**consultas esperadas com termo aditivo**; não é robustez multiplicativa estrita
2+ε para instâncias pequenas. Para OPT≥1, implica o limite multiplicativo mais
fraco 2+c_k+k. Com H vazio, m=0 e ALG=OPT=0.

Previsão perfeita significa Mhat=M **e todas as testemunhas selecionadas
aprovam**. Então P é ótimo, F é vazio e ALG≤OPT+k. Apenas acertar Mhat=M não
garante que as testemunhas escolhidas estejam corretas. O adversário precisa
ser oblivious: respostas/M fixos antes dos sorteios; não escolher valores depois
de observar os alvos. Esta análise não cobre custos arbitrários por vértice.

## 3. Degradação aditiva por erros

Fixadas as testemunhas, seja b o número de alvos previstos cujo teste real
rejeita. Pela aprovação unilateral, b≥f. Para m>0,
q=Pr(A)=(1−b/m)^k, mesmo parando na primeira rejeição. Usando o limite mais
preciso dos dois ramos,

\[
\mathbb E ALG\le k+OPT+q(f+u)+(1-q)g
=k+OPT+f+u+(1-q)(t-f).
\]

Como t−f≤m e m[1−(1−b/m)^k]≤kb, resulta

\[
\boxed{\mathbb E ALG\le OPT+k+f+u+kb}.
\]

Pode-se tomar o mínimo desse limite com (2+c_k)OPT+k. Para m=0, não há
auditorias e ALG≤OPT+u; não dividir por m. A parcela f+u mede erro do conjunto
mandatory; b mede erros das testemunhas selecionadas e não todo erro neural.

## 4. O fator 2+c_k é sharp para este algoritmo

Construção de oráculos finitos variáveis, sem alegar realização por pesos de um
modelo treinado. Tome n≥2 componentes: uma estrela de centro c em A e r folhas
ℓ_j em B; n−1 arestas isoladas x_i∈A,y_i∈B. Use MVC que escolhe x_i nos
empates das arestas isoladas, como o mincut unitário com essa orientação.
Escolha n≥2, r≥n e s=n+r+1, e defina

\[
τ={1\over8s},\qquad ε={τ^2\over16s^2},\qquad δ={ε\over4}.
\]

Caps: α_c=τ−δ, β_ℓ=τ−ε, α_x=τ/4, β_y=τ−δ. **Todas são estritamente
menores que τ**: o pré-processamento que consulta caps≥τ não revela nenhuma
dessas posições. Componentes reais da estrela são
u_cℓ=v_cℓ=ε/2; das arestas isoladas, u_xy=v_xy=τ/8. Todas as respostas são
positivas, somas de estrela estritamente menores que sua cap, e scores menores
que τ. As somas das caps em cada lado são menores que 1/2. Todas as arestas
continuam ameaçadoras: 2τ−δ−ε>τ e 5τ/4−δ>τ.

O centro é mandatory porque ε/2>δ; as folhas não são porque ε/2<ε.
Nas arestas isoladas, somente y_i é mandatory: τ/8>δ, mas τ/8+τ/4<τ.
Assim M={c,y_1,…,y_(n−1)}, |M|=OPT=n, e o MVC base é
{c,x_1,…,x_(n−1)}.
A previsão produto-raiz tem componente hat_u=hat_v=2αβ. Ela prevê c, todas
as r folhas e todos os y_i: 2(τ−δ)(τ−ε)>ε>δ na estrela e
τ(τ−δ)/2>δ nas arestas isoladas; o arco reverso não passa porque
τ/4+τ(τ−δ)/2<τ. Assim Mhat=M∪{ℓ_j}, Cpred=∅ e |P|=n+r.

Selecione testemunha ℓ_1 para c, c para cada folha, e x_i para y_i. Exatamente
os n alvos reais aprovam. Aprovação tem probabilidade [n/(n+r)]^k. Rejeição
custa 2n−1 mais O(k) auditorias; aprovação custa n+r mais O(k), com cache.
Para k≥2, tome n múltiplo de k−1, r=(k+1)n/(k−1) e n tendendo a infinito:

\[
{\mathbb E ALG\over OPT}\longrightarrow
2+x_k^{k-1}(1-2x_k)=2+c_k.
\]

Para k=1, escolha r=n³ e n tendendo a infinito, obtendo razão 3. O k é fixo
nesses limites; isso não demonstra tightness do termo aditivo k.

A realização pode ter marginais/condicionais de uma única joint positiva.
Defina R(a)=2α_a,C(b)=2β_b e P(a,b)=2u_ab=2v_ab nas arestas candidatas.
Essas massas deixam resíduos positivos em toda linha/coluna. Além disso,
sum R+sum C<1 sobre símbolos candidatos. Coloque η>0 suficientemente pequeno
nas outras células candidatas, complete resíduos numa linha/coluna outside,
e use P(out,out)=1−sum R−sum C+sum P(células candidatas)>0. Todas as
condicionais e roots são então normalizados e positivos. A previsão acima é
precisamente usar C(b) e R(a) como condicionais independentes da outra ponta.

Pode-se acrescentar vencedor exclusivo com ambas as caps τ−δ/2<τ e
componentes τ/2,τ/2. Seu produto-raiz 4(τ−δ/2)² supera os rivais, pois
(τ−δ/2)²−(τ−δ)(τ−ε)=τε−δε+δ²/4>0. Suas duas consultas fornecem τ por
custo constante; as massas continuam admitindo a extensão positiva acima.
Isso não dispensa contar tais consultas num decoder completo. O
certificado continua usando a classe adversária de respostas do contrato; não
presume que o solver conheça coerência Bayesiana de todas as completações.
Sharpness de pior caso não demonstra ganho frente ao controle lazy com caps.

## 5. Barreira determinística e controles conhecidos

Há uma barreira direta no contrato abstrato. Suponha um determinístico com
ALG≤OPT+a sob previsão perfeita, a constante, e robustez ALG≤βOPT+B com
β,B finitos. Tome d estrelas disjuntas com r folhas, τ suficientemente pequeno,
cap central τ/4 e caps das folhas τ−δ, δ=τ/(16r). Na previsão perfeita,
componentes de ambos os lados são 2δ em toda aresta. Só as folhas são mandatory,
OPT=dr, logo a execução perfeita consulta no máximo a centros. Seja h≤a o
número de centros consultados. Mantenha seus valores e todos os valores das
folhas; nos outros centros troque os componentes por δ/2. O transcript inteiro
do determinístico permanece idêntico. O novo OPT é hr+(d−h), pois cada estrela
alterada é resolvida só pelo centro. ALG≥dr. Escolha d>βa e depois r grande:
dr>β[ar+d]+B, contradição. Escolher τ<1/[8d(r+1)] permite roots e respostas
normalizadas/positivas. O adversário é fixado simulando offline a execução
perfeita; não reage a aleatoriedade durante a execução.

Este argumento não vale para sorting pleno por intervalos: ali o grafo exige
todas as comparações entre intervalos sobrepostos, não estrelas de comparações
arbitrárias. [Erlebach et al., IJCAI 2023](https://arxiv.org/abs/2305.09245),
Teorema 4.2, já fornecem sorting determinístico 1-consistente/2-robusto. O
Teorema 2.1 dá outro tradeoff determinístico para orientação; suas hipóteses e
ausência de termo aditivo não devem ser trocadas pelas desta nota sem prova.
Uma transferência específica para orientação bipartida, com suas próprias
hipóteses e antecedentes, está na seção 7. Ela não se transfere a sorting como
uma melhoria sobre o resultado já conhecido.

Mandatory sets, witnesses, MVC e seus usos em aquisição são controles conhecidos
em [ESA 2022](https://arxiv.org/abs/2206.15201) e no artigo IJCAI citado. A
probabilidade x^k de todos os testes aprovarem é elementar; não reivindicamos
inventar verificação aleatória ou confiança/fallback. O candidato específico é
o tradeoff aditivo, sua degradação por erros e a sharpness neste oráculo. Esta
nota não estabelece prioridade mundial, aceleração, acurácia ou tema central.

## 6. Protocolo CPU proposto, ainda não executado

Antes de rodar, congelar esta nota e a fonte separada `multiple_probe.py`.
Auditar k=1,2,3,4 nos mesmos 15 grafos não vazios 2×2, três tabelas racionais
reais e seis previsões de `online_probe.py`, incluindo sua tabela de igualdade
e previsão sem alvos. Enumerar todas as m^k tuplas uniformes com reposição,
executar cache/parada precoce e somar custos com Fractions. Validar cada
certificado independentemente; comparar OPT pelos quatro cortes e todos os
16 subconjuntos. Conferir ambos os limites esperados, q, consistência por
execução quando os arcos previstos são exatos, e equivalência com V1 para k=1.

Acrescentar duas tabelas, high e low, do mesmo grafo de quatro estrelas com
duas folhas por estrela (r=4,n=2 na fonte), usando k=2 e a previsão high em
ambas. Cada tabela enumera as 8² sequências. Os valores algébricos a testar
são OPT_high=8, OPT_low=4, custo esperado high=9,75 e low=4; **não são
resultados de execução**. A família sharp da seção 4 permanece somente prova
algébrica, sem novos casos finitos anunciados. Preservar recusas e não ajustar
casos após resultados. A auditoria testa correção finita, não acurácia, tempo,
prioridade ou ganho neural. Nenhuma execução foi feita por esta nota.

## 7. Corolário para orientação bipartida e auditoria de prioridade

Problema clássico distinto do decoder: um grafo bipartido especifica quais
comparações precisam ser resolvidas. Cada vértice v tem intervalo aberto
conhecido I_v e valor desconhecido w_v∈I_v. Valores nos extremos de cada
aresta são distintos. Uma consulta revela w_v, a custo unitário. Os valores
são fixados antes dos sorteios e não têm restrições conjuntas adicionais.
Descartar arestas com intervalos disjuntos, cuja orientação já é conhecida;
chame H o grafo restante. Defina

\[
M=\{v:\exists u\in N_H(v),\ w_u\in I_v\}.
\]

**Certificados.** Se uma aresta não tem ponta consultada, os intervalos
abertos sobrepostos admitem ambas as ordens: qualquer certificado cobre H.
Se v∈M não foi consultado, há u com w_u no interior de I_v; mesmo revelando
todos os demais valores, v admite valores dos dois lados de w_u. Logo todo
certificado contém M. Reciprocamente, num cover que contém M, cada ponta v
não consultada tem todos os vizinhos u consultados e w_u∉I_v. Assim todas
as comparações são determinadas. Portanto o certificado é exatamente
`cover + M`, e OPT=|M|+vc(H−M).

Uma previsão de valores em seus intervalos determina Mhat e, para cada alvo
p∈Mhat, um vizinho previsto u(p) como testemunha. Consultar u(p) aprova
exatamente quando w_u(p)∈I_p, o que implica p∈M. Depois de consultar qualquer
cover, cada comparação ainda incerta identifica uma ponta ausente de M;
consultá-las conclui o certificado. São precisamente as hipóteses da seção 1.
Consequentemente, as garantias das seções 2–3 valem para essa operação
existente, com MVC polinomial por bipartição. Isto é uma prova escrita de
transferência, não uma medição nem uma nova definição de orientação.

A barreira determinística também tem realização direta nesse problema.
Use estrelas disjuntas, centros com I=(0,2), folhas com I=(1,3). Na instância
perfeita, centros valem 1,5 e folhas 2,5: só as folhas são mandatory. Trocar
centros não consultados para 0,5 mantém os transcripts das folhas e permite
resolver cada estrela alterada consultando apenas seu centro. A argumentação
da seção 5 se aplica. Comparações entre folhas não são solicitadas; adicionar
todas elas mudaria o problema para sorting e invalidaria esta construção.

**O que os antecedentes já contêm.**

- [Erlebach et al., IJCAI 2023](https://arxiv.org/html/2305.09245v1),
  lemas 2.3/2.6 e seção 3: mandatory, witnesses, MVC e fallback são conhecidos.
  Teoremas 2.1/3.7 tratam de tradeoffs determinísticos multiplicativos; seção
  3.3 randomiza o arredondamento de um parâmetro, não este teste de k alvos.
  Teorema 4.2 já resolve sorting com consistência 1 e robustez 2.
- [Learning-Augmented Query Policies](https://arxiv.org/abs/2011.07385),
  teoremas 2.1/2.4 e apêndice C.10: limites determinísticos e randomização por
  arredondamento; não localizamos ali a garantia aditiva desta nota.
- [Bampis et al., ESA 2021](https://arxiv.org/html/2107.00572v1): a
  decomposição por mandatory e cover também é anterior. Seu fator 4/3 para
  grafos bipartidos pressupõe distribuições independentes conhecidas dos
  valores, informação ausente aqui. Não é um comparador do mesmo contrato.
- [Fast Imprecise Oracles, NeurIPS 2024](https://arxiv.org/html/2402.02774):
  já há garantias com erro/termo aditivo em algoritmos com dois oráculos para
  matroides; não reivindicamos a ideia geral de usar termo aditivo ou verificar
  conselhos. O benchmark, os certificados e as consultas são diferentes.
- [R-RANSAC, BMVC 2002](https://bmva-archive.org.uk/bmvc/2002/papers/50/full_50.pdf):
  testar amostras aleatórias antes da verificação completa é um padrão antigo.

A busca dirigida incluiu esses artigos e suas provas, o catálogo ALPS e
consultas de trabalhos de 2024–2026 sobre explorable uncertainty, orientação,
query policies e previsões. Não encontramos o mesmo tradeoff
`OPT+k` / `(2+c_k)OPT+k`, sua degradação e sharpness para orientação
bipartida. Isso documenta uma **candidata de prioridade específica**, sem
certificar ausência mundial de antecedente. Não demonstramos que a fronteira
seja ótima entre todos os algoritmos aleatórios; sharpness é só desta política.

**Custo e relevância.** Há leitura do grafo e previsão, dois MVC, no máximo k
consultas de auditoria e as consultas de conclusão. Sorteio uniforme exato
por rejeição de bits usa O(k log(m+1)) bits esperados; cache mantém as respostas
e a saída total de estrelas tem tamanho O(|E|) para consultas sem repetição.
Comparações racionais pagam o tamanho em bits dos valores; nenhum solver é
gratuito. O benefício teórico é certificado quase ótimo sob conselhos corretos
e limitação uniforme do custo sob conselhos arbitrários, com uma separação
frente a qualquer determinístico com a mesma consistência aditiva constante.
Esse é um resultado positivo de aquisição certificada de informação. Não
implica aceleração de dLLM: na qualificação nativa V1 o controle lazy já
certifica as seis propostas corretas antes de qualquer auditoria. Esse dado
permanece negativo e não será ampliado para salvar a aplicação. Uma ligação
neural útil, distinta e com comparador competente ainda precisa ser justificada.

## 8. Resultado CPU da extensão

Fonte e protocolo das seções 1–7 congelados em `3d156d67`, antes da primeira
execução. Comando:

```bash
.venv-live/bin/python attempts/87-conditional-choice-readout/multiple_probe.py --audit
```

Saída completa:

```json
{"counts": {"forecast_k_cases": 1082, "instances": 47, "policy_runs": 17648, "subset_checks": 720}, "protocol": "A87-multiple-probe-CPU-v1", "scope": "finite rational correctness only; no neural/performance/priority claim", "stars_r4_n2_k2": {"perfect": "39/4", "wrong": "4"}}
```

Todas as asserções passaram, sem recusa: certificados independentes,
deduplicação, equivalência com k=1, dois limites esperados, probabilidades de
aprovação, consistência por execução e referências de OPT. O par de estrelas
confirmou exatamente os valores previamente anunciados, 39/4 e 4. Os 720
subconjuntos são 45 instâncias de quatro vértices vezes 16; as duas instâncias
adicionais são os casos de estrelas. Não houve PRNG nem execução neural.

Esses números verificam os casos do protocolo; a prova cobre a família
abstrata sob suas hipóteses. Nenhum dos dois estabelece prioridade mundial,
ganho de tempo de modelo ou adequação final como tema central ligado a dLLMs.

## 9. Revisão adversarial: conclusão lazy e nova família sharp

Posterior ao congelamento e à auditoria da fonte: a conclusão que consulta
cegamente todo o cover escolhido admite dominância. Depois das auditorias,
processe as pontas realmente forced e, antes de consultar cada vértice do
cover, pule-o se todas as suas arestas já estiverem certificadas. Atualize os
bounds após cada resposta e pare somente com certificado completo. Arestas
certificadas não reabrem. Essa conclusão usa somente vértices do cover
escolhido e de M, além das auditorias já pagas. Portanto as provas superiores
das seções 2–3 continuam válidas. Trata-se de uma especificação/prova de
refinamento, não de uma implementação já auditada; `multiple_probe.py`
permanece congelado como está.

Na família da seção 4, consultar c primeiro pode eliminar todas as folhas
falsamente previstas. Sua sharpness é apenas da política congelada mais fraca;
ela não justifica sharpness para essa conclusão lazy. Preservamos o argumento
anterior com seu escopo e apresentamos **outra família**, sem alterar dados.

Tome uma estrela c—ℓ_j com r folhas e n−1 arestas isoladas x_i—y_i. Ponha

\[
τ={1\over8(n+r+1)},\qquad ε={τ^2\over16},\qquad δ={ε\over4}.
\]

Use α_c=α_x=τ/4, β_ℓ=τ−ε e β_y=τ−δ. Na estrela real, u=v=ε/4;
nas arestas isoladas, u=v=τ/8. Todas as caps são menores que τ, toda aresta
pertence a H e todas as somas de resposta são estritamente menores que a cap.
As somas de caps de A e B são menores que 1/32 e 1/8, respectivamente, de
modo que há roots normalizados positivos. Em cada estrela,
u+β_ℓ=τ−3ε/4<τ e v+α_c<τ: **não há vértice mandatory**. Nos pares,
somente y_i é mandatory. Logo M={y_i} e OPT=n.

A previsão produto-raiz tem componentes 2αβ. Na estrela,
τ(τ−ε)/2>ε, mas τ/4+τ(τ−ε)/2<τ. Assim prevê todas as folhas e não c.
Nos pares prevê y_i e não x_i. Portanto Mhat={ℓ_j}∪{y_i}, P=Mhat e
Cpred=∅. Exatamente n−1 dos n−1+r testes de alvo aprovam.

Se as k auditorias aprovam, nenhuma consulta em c ocorreu. Consultar uma
folha certifica somente sua própria aresta e não força c. Mesmo a conclusão
lazy precisa de todas as r folhas e dos n−1 vértices y_i mandatory; as fontes
x_i das auditorias acrescentam no máximo k consultas. Se um teste rejeita,
c já foi consultado. Com C0={c,x_i}, todos os pares exigem x_i e depois y_i,
inclusive os já revelados por auditorias; o custo total é 2n−1. Portanto

\[
q=\left({n-1\over n-1+r}\right)^k,
\quad ALG_{aceita}=n-1+r+O(k),\quad ALG_{rejeita}=2n-1.
\]

Com k≥2 fixo e r=(k+1)(n−1)/(k−1) inteiro, a razão esperada tende a
2+c_k. Para k=1, r=n³ fornece limite 3. Esta sharpness resiste à poda ativa
e às consultas forced imediatas dessa conclusão, sem afirmar limite inferior
para todos os algoritmos aleatórios. Os componentes iguais dos dois lados
permitem a mesma extensão a uma joint positiva descrita na seção 4.

Também não basta randomizar a ordem de P sem auditar testemunhas externas:
na estrela isolada desta família, previsão manda consultar todas as folhas,
mas M real é vazio e OPT=1 pelo centro. Toda ordem de folhas, mesmo aleatória
com poda/forced, custa r; o teste no centro rejeita e conclui em uma consulta.
Esse separador explicita por que a auditoria tem conteúdo além de ordenar ou
podar as consultas previstas. Continua sendo utilidade teórica sob o contrato,
sem observação de ganho neural.
