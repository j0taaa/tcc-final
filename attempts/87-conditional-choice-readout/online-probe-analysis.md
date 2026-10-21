# A87 — Uma auditoria aleatória antes de confiar no certificado previsto

Estado em 2026-10-21: **método e provas escritas candidatos; prioridade,
auditoria independente, ganho neural e seleção como tema central pendentes**.
Esta nota acrescenta uma operação online, sem alterar fontes ou dados congelados.
Não apresenta execução computacional nem medição de modelo.

## 1. Operação e comparador

Usamos o alvo nativo `J`, consultas por estrela e classe de informação
**interior** de [star-certificate-analysis.md](star-certificate-analysis.md),
§§1–2. Uma alternativa é uma aresta bipartida `e=(a,b)`, com

\[
 J(e)=u_e+v_e,\qquad 0<u_e<\alpha_a,\quad 0<v_e<\beta_b.
\]

Consultar `a` revela todos os `u_e` incidentes; consultar `b`, todos os `v_e`.
Todas as respostas completas e a previsão estão fixadas **antes** de sortear.
Não se pressupõem condicionais globalmente compatíveis. IDs originais, EOS/PAD,
produto por bloco e massa externa ao codebook seguem o contrato citado.
Custos de estrela são unitários; a raiz e o transcript de entrada já foram pagos.

A operação básica recebe proposta `w` com os dois endpoints conhecidos, logo
`tau=J(w)`. Deve certificá-la ou refutá-la. A execução sempre confere respostas
reais; a hipótese de que `w` é o vencedor único entra **somente no limite de
custo**, não é promessa gratuita de correção. A seção 6 cobre proposta falsa.
`OPT` é o menor número de consultas adicionais de um certificado válido na
mesma classe de informação: um comparador offline com respostas conhecidas.
Não significa avaliar todas as alternativas. Obter a previsão tem custo.

## 2. Transcript residual e obrigatório real

Elimine comparações já certificadas. Se uma aresta tem apenas um endpoint
`p` desconhecido e `known_e+cap_p>tau`, consultar `p` é necessário em todo
certificado da proposta verdadeira: uma resposta próxima ao cap a faria perder.
Consulte esse endpoint e propague. Se ambos conhecidos refutarem `w`, devolva
a refutação. Igualdade com cap de endpoint desconhecido é segura no interior;
igualdade entre scores conhecidos segue a prioridade total de desempate.
Também consulte um endpoint ainda desconhecido `z` com `cap_z>=tau` incidente
a rival: a outra contribuição é estritamente positiva, portanto omitir `z`
mantém upper bound maior que `tau` mesmo conhecendo o vizinho. Essa
obrigatoriedade é conhecida na raiz e não deve ser creditada ao forecaster.

Seja `Q0` o conjunto dessas consultas. Indutivamente, `Q0` está em todo
certificado do transcript anterior. Cada aresta não certificada restante tem
dois endpoints desconhecidos. Seu grafo residual é

\[
 H=(A\cup B,E_H),\qquad
 E_H=\{(a,b):\alpha_a+\beta_b>\tau\}.
\]

A seguir `OPT` é o ótimo residual. Defina arco ruim `a -> b` quando
`u_e+beta_b>tau`, e `b -> a` quando `v_e+alpha_a>tau`. Seja `M` o conjunto
das pontas desses arcos, deduplicadas.

**Lema 1.** Se a proposta é o vencedor único real, `Q` é certificado se e
somente se cobre `H` e contém `M`. `M` é exatamente o conjunto de vértices
presentes em todos os certificados.

**Prova.** Aresta descoberta mantém upper bound `alpha_a+beta_b>tau` e uma
realização permitida derrota a proposta. Se `a -> b` é ruim, omitir `b` deixa
upper bound pelo menos `u_e+beta_b>tau`, mesmo consultando `a`; portanto `b`
é obrigatório. Reciprocamente, numa aresta duplamente consultada o score real
é menor que `tau`. Se só `a` foi consultado e `M` está incluído, `b` não é
obrigatório: `u_e+beta_b<=tau`, suficiente no interior. O simétrico é igual.
Para omitir um vértice fora de `M`, basta consultar todos os demais. Fim.

Assim `|M|<=OPT`, `vc(H)<=OPT`, e o certificado ótimo conhecido offline é
`M union C`, com `C` cobertura mínima de `H-M`. Esse uso de obrigatórios e
cobertura tem antecedentes; não é a reivindicação específica desta nota.

**Controle sem previsão.** Consulte uma cobertura mínima `C0` de `H`.
Cada aresta ainda não certificada tem só um endpoint desconhecido, obrigatório
real pelo lema; consulte o conjunto deduplicado `F` deles. O custo é
`|C0|+|F|<=2OPT`. Cache só reduz esse custo.

## 3. Algoritmo: uma testemunha antes de comprar o plano

A interface mínima recebe quaisquer arcos previstos sobre arestas de `H`.
Para um produtor por componentes `hat u_e,hat v_e`, exija limites interiores
e scores previstos menores que `tau`; entrada inválida pode usar o controle.
Quem declarar previsão de uma realização nativa deve fornecer distribuições
produto normalizadas factíveis; isso tem custo. A robustez vale mesmo para
advice de arcos não realizável; a consistência exige os arcos reais corretos.

Calcule o conjunto obrigatório previsto `Mhat`. Para cada `p` nele, guarde
uma testemunha determinística `u(p) -> p` e sua aresta `e(p)`. Tome `C` uma
cobertura mínima de `H-Mhat` e `P=Mhat union C`. Esse conjunto cobre `H` e
é ótimo para a realização prevista, quando factível. Para qualquer previsão,
`|C|<=vc(H)<=OPT`, pois remover vértices não aumenta a cobertura mínima.

Verifique certificados e refutações reais após cada consulta; não repita cache:

1. Se `Mhat` é vazio, consulte `P=C`, faça a conclusão obrigatória `F` e pare.
2. Caso contrário, sorteie `p` uniformemente em `Mhat` e consulte `u(p)`.
3. Aceite o plano apenas se a resposta verificar o arco ruim real:
   `z_[u(p),e(p)]+cap_p>tau`.
4. Se aceitou, consulte `P`; se rejeitou, consulte a cobertura mínima `C0`
   de `H`. Conclua consultando os endpoints únicos ainda desconhecidos de
   arestas não certificadas, até certificar ou refutar.

O teste não pede coincidência do vetor inteiro. Uma obrigatoriedade demonstrada
permite comprar o plano; a decisão só sai quando o certificado real completo
é válido. Uma amostra não substitui esse certificado.

## 4. Prova positiva

**Teorema 2.** Para proposta verdadeira única, custo unitário, interior e
realização fixada antes do sorteio:

- previsão perfeita: `ALG<=OPT+1` em toda execução;
- previsão arbitrária admitida: `E[ALG]<=3OPT+1`;
- a decisão emitida é sempre certificada, qualquer que seja a previsão.

**Prova.** Se a previsão é perfeita, todas as testemunhas são realmente ruins.
O teste sempre aceita e `P` é certificado real ótimo. A consulta de auditoria
custa no máximo uma além de `P`; se `Mhat` é vazio, o custo é exatamente `OPT`.

Para a robustez, ponha `m=|Mhat|>0`, `t=|Mhat intersect M|` e evento `A`
de aceitação. Aceitar comprova `p in M`. Como o sorteio é uniforme em um
conjunto fixo,

\[
 \Pr(A)\le t/m,\qquad m\Pr(A)\le t\le |M|\le OPT.
\]

Rejeitar custa no máximo `1+2OPT`. Aceitar custa no máximo a consulta inicial,
`|P|<=m+OPT`, e `|F|<=OPT`: depois de uma cobertura, cada endpoint adicional
necessário é obrigatório real. Portanto, em cada execução,

\[
 ALG\le1+2OPT+m\mathbf1_A,
 \qquad \mathbb E[ALG]\le1+2OPT+t\le1+3OPT.
\]

Se `m=0`, usa-se o controle de custo `2OPT`. A correção é dada pelos bounds
reais e pela regra final de certificado, independentemente da previsão. Fim.

Acertar todos os números é mais forte que o necessário: bastam `Mhat=M` e
a preservação dos arcos testemunhados. Acertar apenas `Mhat=M` não garante que
a testemunha escolhida continue ruim.

Se `OPT_initial` é o ótimo antes de `Q0`, depois do mesmo transcript de entrada,
vale `OPT_initial=|Q0|+OPT`: todo certificado contém `Q0`, e um ótimo residual
completa esse conjunto. Assim o custo esperado incluindo propagação é
`|Q0|+3OPT+1<=3OPT_initial+1`; com previsão perfeita, `OPT_initial+1`.

## 5. Obstruções: por que a auditoria aleatória interessa

Tome uma estrela `K_(n,1)`, limiar `tau>0` e `epsilon=tau/(8n)`. Cada folha
tem cap `alpha=tau-epsilon`; o centro, cap `beta=tau/2`. A previsão dá
`u_i=tau/4` nas folhas e `v_i=2epsilon` em cada componente do centro.
Consultar uma folha certifica sua aresta (`u_i+beta=3tau/4`); consultar o
centro não certifica nenhuma (`alpha+v_i=tau+epsilon`). O único certificado
ótimo previsto são as `n` folhas. Mude só o centro para `v_i=epsilon/2`:
consulta única a ele agora certifica tudo, e as folhas respondem como antes.

**Proposição 3.** Consistência exata `ALG<=OPT` em previsão perfeita é
incompatível com robustez constante, mesmo exigida só em esperança. No caso
perfeito, correção e ótimo único obrigam as `n` folhas, sem extra quase
certamente. O transcript da segunda realização permanece igual até terminar;
logo custa `n` com ótimo um. Fim.

**Proposição 4.** Para qualquer constante aditiva `c>=0`, nenhum método
**determinístico** com `ALG<=OPT+c` em previsão perfeita tem robustez uniforme
constante. Faça `r` estrelas disjuntas. Na realização perfeita, consultam-se
as `rn` folhas e no máximo `q<=floor(c)` centros extras. Fixe esse transcript:
centros consultados mantêm a previsão; os não consultados mudam para o vetor
baixo. O transcript observado permanece idêntico, mas agora

\[
 ALG\ge rn,\qquad OPT_{real}=qn+(r-q)\le cn+r,
 \qquad \frac{ALG}{OPT_{real}}\ge\frac{rn}{cn+r}.
\]

Escolher `r` e depois `n` grandes torna a razão arbitrariamente grande. Essa
proposição determinística não contradiz a robustez esperada do Teorema 2. Fim.

As famílias cabem no contrato nativo com um token por bloco e símbolo externo.
O vetor alto do centro soma `2n epsilon=tau/4<beta`; sobra massa positiva.
Escolher `tau=1/[100(rn+r+3)]` deixa as somas dos caps de raiz de cada parte
abaixo de `1/2`. Uma proposta exclusiva de score `tau`, com endpoints já
consultados, pode ser acrescentada e ainda sobra massa externa positiva.
Todas as contribuições são interiores racionais e as arestas rivais reais
ficam abaixo de `tau`. Não se usam vetores com soma impossível. A técnica de
indistinguibilidade tem os antecedentes da seção 9; não é reivindicada nova.

## 6. Classificador sempre exato, com custo condicionado à proposta

Uma regra barata declarada propõe `w`. Consulte seus dois endpoints e execute
o método. Se rival totalmente conhecido vencer `w` por score/desempate,
complete todas as estrelas ainda não consultadas, aproveite cache e retorne
o MAP exato de `J`. Caso o certificado confirme `w`, retorne-o. Empates
conhecidos usam a prioridade total; inconclusão não permite saída antecipada.
O custo máximo é `V` estrelas distintas além da raiz, mesmo com proposta falsa.

**Corolário 5.** A saída coincide sempre com o scorer integral. Condicionalmente
a a proposta ser o vencedor único real, se `OPT_global` é o certificado global
mínimo antes de consultar seus endpoints,

\[
 \mathbb E[ALG_{global}]\le3OPT_{global}+3.
\]

Com previsão perfeita e proposta correta, `ALG_global<=OPT_global+3` em toda
execução. A raiz comum está excluída; propor e prever têm custo adicional.

**Prova.** Um certificado global ótimo `Q*`, unido aos endpoints de `w`,
continua válido quando seu score passa a ser conhecido. Logo
`|Q0|+OPT<=|Q* minus endpoints(w)|<=OPT_global`. Some no máximo duas
consultas da proposta aos limites anteriores. Se a proposta é falsa, o limite
de razão não se aplica; o fallback finito mantém a correção. Fim.

Não se provou razão constante incondicional para encontrar o MAP, nem para
reinícios sucessivos. O certificado preserva o alvo `J` declarado; não prova
que sua decisão tenha melhor acurácia semântica que outros classificadores.

## 7. Oráculo fixo, RNG e pior execução

A realização deve ser oblivious: fixa antes do sorteio. Se um adversário a
escolhesse após observar `p`, poderia tornar só esse vértice obrigatório,
aceitar e cobrar `|Mhat|` com ótimo pequeno. Modelo determinístico, dropout
inativo e política numérica fixa são um possível contrato; forwards estocásticos
exigem coleção de seeds fixada por contexto e alvo explícito. Reamostrar o
mesmo contexto altera o problema e não herda a prova.

Para amostra uniforme exata em `m>=2`, tome `k=ceil(log2 m)` bits justos,
aceite o inteiro se menor que `m` e repita senão. Esperam-se `2^k/m<2`
tentativas e menos de `2k` bits, com buffer `O(log m)`; `m=1` não usa bits.
Não há teto determinístico de tentativas, embora termine quase certamente.
Um limite de recursos retorna inconclusivo/refusa; truncar ou usar PRNG finito
exige declarar outra política, sem atribuir-lhe automaticamente a lei ideal.

`3OPT+1` é limite esperado. Uma aceitação rara pode comprar `Theta(V)` consultas.
O teto por execução é `V` estrelas distintas; RNG tem a ressalva anterior.
Isso importa para latência de cauda e não deve ser omitido na avaliação.

## 8. Custos completos, consumidor e limitações

Para `K` arestas, `V` tuplas distintas, `N` posições, vocabulário `D` e
racionais de até `B` bits por numerador/denominador, produtos de bloco têm
`O(NB)` bits. Toda multiplicação/comparação paga esse tamanho; não se assume
aritmética racional unitária. Raiz e forwards normalizam cabeças sobre o
vocabulário completo. Extrair só candidatos não elimina esse custo ou a massa
externa. Floats/intervalos precisam de contrato numérico próprio: underflow
não garante interior nem permite comparações exatas presumidas.

Preparar palavras/produtos custa `O(KN)` operações aritméticas. Montar `H`,
`Mhat` e testemunhas custa `O(K+V)` operações de grafo e comparações de
`O(NB)` bits. Há no máximo duas coberturas bipartidas unitárias, cada uma
solúvel via matching em `O((K+V)sqrt(V))` operações; mincut equivalente serve.
Uma implementação simples reexamina `K` arestas após cada consulta e paga
`O(KV)` comparações. Atualização de incidências pode reduzir trabalho, mas
não é implementação medida ou requisito do teorema.

Armazenar IDs diretamente usa `O(KN log D)` bits; componentes/caps, incidências
e testemunhas usam `O(KNB+K log V+V log V)` bits; cache de consultas, `O(V)`
bits, e RNG, `O(log V)`. Pesos, ativações, logits `N x D`, normalização,
transporte, saída e previsão densa são custos adicionais. Processar e descartar
cabeças pode reduzir armazenamento persistente, mas não sua produção.

**A previsão não é gratuita.** Consultar todas as estrelas para prevê-las
perfeitamente já paga o scorer integral. Falta selecionar produtor barato,
sem treino e com custo declarado, bem como a regra de proposta. Cache antigo
é apenas previsão não confiável e seu preparo/armazenamento também se cobra.
Não se atribui nesta nota benefício de tempo ou de acurácia a nenhum produtor.

O benefício teórico verificável é quase minimizar consultas quando a informação
auxiliar acerta, mantendo limite esperado para qualquer previsão em propostas
corretas. Falta benefício nativo. Caps de blocos longos podem ser frouxos e
obrigar quase todas as estrelas; falta de compartilhamento pode favorecer
controles simples. Não se provaram custos ponderados, batching ou vantagem
sobre outra semântica de score. O consumidor é escolha textual finita geral;
não se afirma método para toda GLC por representar o codebook como gramática.

## 9. Antecedentes e diferença candidata

- [TUBE, §2.3](https://arxiv.org/html/2605.24292v1) e
  [DUEL, Proposição D.2](https://arxiv.org/abs/2603.01367): misturas de ordens
  agrupadas já definem likelihood. O alvo `J` não é novo.
- [Erlebach et al., ESA 2022](https://arxiv.org/pdf/2206.15201), Teoremas 7 e 9:
  obrigatoriedade, matching e tradeoffs de consultas com previsão são anteriores.
  A família de estrelas usa a mesma técnica de indistinguibilidade. Um resultado
  de MST não se transfere a vetores por contexto sem redução explícita.
- [Erlebach et al., IJCAI 2023](https://arxiv.org/html/2305.09245v1), Lemas
  2.3/2.6 e §§3.2–3.3: obrigatórios mais cobertura e a conclusão por consultas
  obrigatórias já aparecem. A randomização de §3.3 mistura valores inteiros
  vizinhos de `gamma`; não é o teste uniforme de uma testemunha antes de
  comprar `Mhat`. Seu modelo principal consulta um escalar por elemento;
  aqui uma consulta revela componentes diferentes por aresta incidente.
- [Megow–Schlöter, MinCover, §4.2](https://arxiv.org/html/2211.01097v2): revelar
  vários coeficientes por consulta também é anterior. O limiar fixo cabe como
  cobertura por reduções `cap-actual`. Suas garantias estocásticas requerem
  distribuição/balanceamento, não estabelecendo diretamente o teorema para
  realizações arbitrárias e previsão não confiável.
- [Diwan et al., STACS 2026](https://drops.dagstuhl.de/storage/00lipics/lipics-vol364-stacs2026/LIPIcs.STACS.2026.32/LIPIcs.STACS.2026.32.pdf),
  Corolário 28: certificado mínimo por cobertura bipartida já é conhecido
  para verificar uma base de peso mínimo. Sua operação consulta pesos escalares;
  não se identificou ali a auditoria única de testemunha com o limite desta nota.
- [Accelerating Matroid Optimization through Fast Imprecise Oracles](https://openreview.net/pdf/bfe61671c74fb06c0182c32252b26c64125ab10a.pdf):
  combinar um oráculo barato impreciso com consultas caras corretas é anterior.
  Seus resultados tratam independência/base de matroide e distância entre bases,
  não o mesmo certificado por componentes vetoriais de um score de duas ordens.

A diferença candidata é testar **uma ponta prevista obrigatória consultando
sua testemunha**, e só comprar o plano inteiro quando essa obrigatoriedade foi
demonstrada. A cobrança `|Mhat| Pr(aceitar)<=|M|` fornece adição de uma consulta
em previsão perfeita e robustez constante esperada. Não se localizou o mesmo
resultado nas fontes inspecionadas; isso não comprova prioridade mundial nem
exclui redução a um teorema mais geral ainda não localizado.

Antes de campanha: auditoria independente e prioridade específica; oráculo
finito congelado; diagnóstico de ótimos/obrigatórios nativos; produtores
baratos; comparação com cobertura sem previsão, aquisição por upper bound,
scorer integral de dois blocos e controles de classificação. Preserve perdas,
refutações, consultas, RNG, preparo, memória, tempo e recusas. Esta nota não
seleciona campanha nem permite ajustar casos após observar dados.

## 10. Protocolo CPU antes da primeira execução

O auditor [online_probe.py](online_probe.py) recebe somente dados públicos,
arcos previstos e uma callback de consulta. As respostas não consultadas ficam
no produtor da fixture. A aleatoriedade é enumerada exatamente, sem PRNG:
cada ponta prevista é escolhida uma vez e o custo médio é uma fração.

Após congelar esta nota e o código em commit produtor, executar:

```bash
.venv-live/bin/python attempts/87-conditional-choice-readout/online_probe.py --audit
```

Escopo congelado no cabeçalho do auditor: todos os 15 grafos bipartidos 2x2
não vazios; três tabelas racionais positivas por suporte; seis previsões por
instância, incluindo arcos de cada tabela, todos, nenhum e complemento dos
reais. Para cada ponta sorteável, conferir certificado independente e limite
de consistência quando os arcos são reais; conferir a esperança `<=3OPT+1`.
Comparar o ótimo por todos os 16 subconjuntos com a referência dos quatro
cortes, usando vencedor exclusivo conhecido. Acrescentar estrelas disjuntas
com `r in {1,2,4,8}`, `n in {2,3}` e previsões perfeita/sem arcos/centro errado.
As fixtures residuais têm `cap_z<tau`; não medem o pré-processamento raiz.

Imprimir JSON de contagens e frações, sem resultados automáticos nem timings.
Falhas interrompem com erro preservado; correções ficam em outra versão, sem
sobrescrever o produtor. Este auditor não implementa nem valida o fallback
global para proposta falsa, RNG físico, numérica neural ou custo integral.
Seu sucesso seria evidência finita de correção, não prova de prioridade,
vantagem empírica ou aprovação da direção como TCC.

## 11. Auditoria CPU do produtor congelado

Em 2026-10-21, o comando acima sobre o produtor `b8acf2cb` terminou com
exit code zero: **61 instâncias, 294 previsões, 664 execuções de política e
752 subconjuntos**. Todas as comparações de certificado, ótimo independente,
consistência e esperança previstas passaram. Nas oito famílias de estrelas,
as contagens perfeitas/sem previsão foram respectivamente
`3/3, 4/4, 5/6, 7/8, 9/12, 13/16, 17/24, 25/32`;
com centros previstos errados, foram `1,1,2,2,4,4,8,8`.
Não houve consulta neural. Esses resultados são auditoria finita da operação
residual, sem validar o wrapper global, prioridade ou vantagem nativa.

## 12. Auditoria adicional de antecedentes

A leitura dirigida posterior localizou [R-RANSAC, §§2–3, 2002](https://bmva-archive.org.uk/bmvc/2002/papers/50/full_50.pdf):
pré-testar pontos aleatórios antes da avaliação completa, incluindo `d=1`,
é anterior. Portanto o padrão genérico de pré-teste não é reivindicação nova.
[Bampis et al., ESA 2021, Observação 7](https://arxiv.org/abs/2107.00572)
já dá a decomposição por obrigatórios e cobertura; sua escolha probabilística
usa distribuições conhecidas. [Learning-Augmented Query Policies](https://arxiv.org/abs/2011.07385)
também trata previsões não confiáveis. Não se localizou nessas fontes o mesmo
teste de testemunha com garantia aditiva de uma consulta perfeita e robustez
esperada constante para esta operação vetorial. A diferença candidata fica
restrita a essa operação e garantia; prioridade mundial continua não confirmada.
