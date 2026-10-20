# A86 — Planejamento de consultas pelo prefixo efetivamente executável

Data: 20/10/2026. **Candidata prospectiva, sem seleção como tema central**.
Formulação e provas escritas; o decoder ainda não foi implementado ou medido.
A sonda de custo tem protocolo e produtor separados, congelados antes de executar.
Não há verificação formal.
Prioridade e suficiência da contribuição permanecem abertas após encontrar Gupta (2026).

## 1. Operação real e consumidor

O consumidor é geração greedy nativa de um dLLM, com um evento por passo incluindo
**posição e ID original do token**. Dado o cabeçalho já calculado do estado atual,
escolher quais estados futuros consultar em paralelo para
executar vários passos nativos consecutivos antes de uma nova rodada de consultas.
Não se procura melhorar a qualidade semântica: a saída deve coincidir com a nativa.

A proposta é calibrar o conjunto de consultas pelo comprimento do **prefixo todo
disponível**, dividido pelo custo de executá-lo. Frequência isolada de um estado
superestima seu uso quando a ordem nativa chega a ele através de pais ausentes.
O alvo verificável é menor latência integral, preservando os mesmos IDs e estados,
frente a controles que também escolhem tamanho e estrutura das consultas.

## 2. Antecedente mais próximo e diferença ainda sob auditoria

[Spiffy v4](https://arxiv.org/html/2509.18085v4), §§4.3–4.4 e apêndice D,
já verifica estados futuros, reutiliza resultados e funde ordens de revelação
num DAG com vários pais. Sua calibração escolhe tamanho fixo e maximiza contagens
de nós sob conectividade; a poda online usa probabilidades do cabeçalho atual.
O próprio artigo estuda a troca entre número de consultas e latência.

O antecedente matemático mais próximo é
[Gupta, *Exact Memory-Time Optimization for Prefix-Cached Language Model Serving*,
v1, 02/10/2026](https://arxiv.org/html/2610.02766v1), §§3–4, equação (2) e teorema 2.
Ele já contabiliza prefixos utilizáveis como conjunções e cria certificados com
implicações para a disponibilidade local e o certificado anterior, reduzindo a
fechamento máximo com grafo linear. **Não reivindicamos essa redução como nova.**

[Gallo–Grigoriadis–Tarjan (1989), §4.2](https://doi.org/10.1137/0218003) já apresenta
programação fracionária e *maximum-ratio closure*, aninhamento e iterações lineares; o
[texto integral disponibilizado pelo autor](https://www.researchgate.net/publication/220616489_A_Fast_Parametric_Maximum_Flow_Algorithm_and_Applications)
foi consultado. [Huang–Gleich–Veldt, WWW 2024, §3](https://www.cs.purdue.edu/homes/dgleich/publications/Huang%202024%20-%20densest%20subhypergraph.pdf)
também trata densidade supermodular com algoritmo exato fortemente polinomial.

A diferença candidata é o contrato de parada para consultas endógenas de um dLLM,
com canvases de vários pais e objetivo de progresso por latência. O cache estático
de Gupta tem outra operação, mas o núcleo é próximo. A transferência pode ser útil;
**integração conhecida, sozinha, não satisfaz o requisito de contribuição própria
do TCC**. Falta justificar um avanço substantivo além dessa transferência.

## 3. Benefício verificável e contrato da macro com cabeçalho em cache

O oráculo deve ser determinístico. Seu estado inclui tokens, máscaras, posições
fixadas, bloco, passo/tempo, agenda de revelação, EOS/PAD,
desempates e toda informação de software que afete a próxima transição.
Só se fundem canvases iguais nesse estado completo. Não se usa KV aproximado.

1. O cabeçalho do estado corrente já está em cache. Ordenar as posições ativas
   pela confiança nativa, com desempate fixo; nas oito primeiras posições,
   congelar o token top-1 original previsto nesse cabeçalho.
2. Um universo finito `U` contém fórmulas de subconjuntos dessas revelações.
   O pool completo tem até 255 fórmulas não vazias; pools menores, por exemplo
   até 128, são possíveis. Com outro gerador pode-se limitar o pool a 256.
   A codificação por ranks fica fixa durante esta macro e é refeita na próxima.
3. O primeiro evento nativo é conhecido pelo cache. Seu estado resultante `S1`
   é obrigatório: `M={S1}`. No regime principal, `S1` é não terminal e pertence
   a `U`. Se o evento já termina a geração, executá-lo diretamente, sem planner.
4. Consultar todos os estados escolhidos `F`, em ondas de microbatch `B≤4–8`,
   usando forwards independentes com o contexto correto. Todas as ondas são
   cobradas, inclusive consultas depois não aproveitadas.
5. Reter por estado somente top-1 e confiança de **cada posição ativa do bloco**,
   calculados como no decoder nativo. Liberar logits de vocabulário completo
   antes da próxima onda; não guardar um tensor `N×bloco×vocabulário`.
6. Seguir o próximo evento nativo calculado pelo cache. Avançar enquanto o
   próximo estado completo estiver em `F`; parar no último estado consultado,
   conservando seu cabeçalho para a próxima macro. Não revelar um evento bônus
   cujo estado seguinte ainda não foi consultado.

Por indução, cada evento coincide com a transição nativa, se o oráculo consultado
em lote e serialmente for a mesma função. `S1` garante pelo
menos um avanço no regime principal, e o cache final restabelece a hipótese da
próxima macro. A primeira inferência de toda a geração é cobrada separadamente.
Terminais posteriores são tratados na próxima entrada pela mesma regra direta.

Igualdade matemática dos forwards não garante igualdade em ponto flutuante.
Kernels, quantização, tamanho do lote e reduções podem mudar argmax/confiança.
Essa equivalência exige verificação de IDs, posições e estados completos; sem
ela, não se pode afirmar preservação exata da geração nativa implementada.

## 4. Hipóteses, formulação e prova delimitada

Fixar `U`, `N=|U|`, e traces `τ` com pesos racionais positivos `wτ`, somando um.
Cada trace começa em `S1` e fornece a sequência
`qτ,1,…,qτ,Lτ` de estados futuros, expressa nos ranks congelados da sua raiz.
Truncar no primeiro estado fora de `U` ou terminal; não pular a falha e contar
estados posteriores. Os pesos são frequências empíricas, não probabilidades
certificadas da trajetória do modelo nem produtos de marginais do cabeçalho.

Para `M⊆F⊆U`, sejam `Aτ,d={qτ,1,…,qτ,d}` e

\[
r_\tau(F)=\sum_{d=1}^{L_\tau}\mathbf1[A_{\tau,d}\subseteq F],\qquad
\mu(F)=\sum_\tau w_\tau r_\tau(F).
\]

Isso conta exatamente o prefixo consultado consecutivo no replay. Cada indicador
AND é monótono e supermodular: para quaisquer `X,Y`, seu valor em `X` mais seu
valor em `Y` é no máximo o valor em `X∪Y` mais o valor em `X∩Y`. Somar com pesos
positivos prova as mesmas propriedades para `μ`.

Exemplo: traces equiprováveis `(s,a,c)` e `(s,b,c)`, `M={s}`, `F={s,a,c}`.
A conectividade permite chegar a `c` via `a`; porém `μ(F)=(3+1)/2=2`.
A soma das frequências dos nós selecionados é `1+1/2+1=2,5`.
Essa discrepância é de objetivo, mesmo com um grafo conectado.

Assumir custo `g(F)=a+b|F|`, com `a≥0`, `b>0`; então `g>0` porque `M≠∅`.
Resolver o objetivo **local e empírico**

\[
R^*=\max_{M\subseteq F\subseteq U}\frac{\mu(F)}{a+b|F|}.
\]

Todos os subconjuntos são admissíveis. O teorema não resolve limite rígido `|F|≤D`;
impor orçamento pode restaurar seleção difícil. Todo `U` deve caber na execução.

### 4.1. Redução explícita a fechamento e remoção da conectividade OR

Para um preço `λ≥0`, criar um nó de estado para cada `q∈U`, com peso `−λb`.
Criar um certificado `hτ,d` com peso `wτ` e implicações
`hτ,d→qτ,d` e, quando `d>1`, `hτ,d→hτ,d−1`. Forçar os nós de `M`.
Certificados com o mesmo predecessor e estado podem ser fundidos somando pesos.
Há `O(N+P)` nós e arcos, onde `P=Στ Lτ`; a construção não é um algoritmo novo
de fluxo nem um primeiro uso de certificados de prefixo.

Todo `F` admite os certificados de seus prefixos completos, formando fechamento
com peso `μ(F)−λb|F|`. Reciprocamente, implicações de qualquer fechamento só
permitem certificados cujos prefixos estão em `F`. Acrescentar certificados
utilizáveis omitidos não reduz peso. Logo o fechamento máximo calcula
`max_F[μ(F)−λg(F)]`, subtraindo externamente a constante `λa`.

O corte usa arcos fonte→certificado de capacidade `wτ`, estado→sorvedouro de
capacidade `λb` e implicações/fonte→obrigatórios de capacidade
`Q>W+λbN`, `W=Στ wτLτ`. Existe corte válido de custo no máximo `W+λbN`;
portanto um corte mínimo não viola implicações nem obrigatoriedade.
Seu custo é `W` menos o peso do fechamento. Isso prova a equivalência com mincut.

Não acrescentar a condição “algum pai selecionado” de um DAG arbitrário.
Para qualquer `F`, seja `F⁺` a união de todos os seus prefixos completos mais `M`.
Temos `μ(F⁺)=μ(F)` e `F⁺⊆F`. Se `μ(F)>0`, retirar estado fora de `F⁺` reduz
estritamente o denominador e melhora a razão. Assim um ótimo da razão não tem
estado inútil; seus estados são união de prefixos observados e são alcançáveis
a partir da raiz no grafo de transições desses traces. A conectividade emerge
da utilidade. Para objetivo precificado com `λ>0`, vale a mesma remoção;
em `λ=0`, estados inúteis podem permanecer por empate.

### 4.2. Razão ótima, aninhamento e número de cortes

Aplicar a iteração fracionária clássica: `λ0=0`; escolher `Fk` maximizando
`μ(F)−λk g(F)` por corte; calcular `Δk=μ(Fk)−λk g(Fk)`.
Se `Δk=0`, terminar. Caso contrário, definir `λk+1=μ(Fk)/g(Fk)`.
A primeira atualização é razão factível; as seguintes permanecem abaixo de
`R*`, com `Δk≥0`. Se `Δk>0`, o preço cresce estritamente. Se `Δk=0`, para todo
`F` vale `μ(F)≤λk g(F)`, e `Fk` atinge igualdade: certificado de ótimo global.

Para provar aninhamento, sejam `A,B` ótimos nos preços `λ1<λ2`. A otimalidade
de `A` frente a `A∪B` e de `B` frente a `A∩B` dá

\[
\mu(A\cup B)-\mu(A)\le\lambda_1b|B\setminus A|,\qquad
\mu(B)-\mu(A\cap B)\ge\lambda_2b|B\setminus A|.
\]

Supermodularidade coloca o primeiro ganho acima do segundo. Como `b>0`,
`B\A` deve ser vazio. Logo as soluções diminuem quando o preço aumenta,
inclusive com empates entre soluções no mesmo preço.

No preço zero pode-se escolher `F0=U`, um ótimo maximal por monotonicidade.
Após isso, cada chamada não terminal com conjunto diferente remove ao menos
um estado; se o conjunto repete o anterior, seu preço já é sua própria razão e
o residual é zero. Há no máximo `N−|M|` remoções, mais a chamada inicial e a
certificação terminal: **`N−|M|+2≤N+1` cortes**. Um solver que devolve somente
o lado alcançável da fonte no residual usualmente escolhe o fechamento mínimo,
não o maximal; `F0=U` pode ser imposto sem depender desse desempate.

### 4.3. Transferência para uma tabela de latência

Se uma função afim positiva `L(m)=a+bm` satisfaz uniformemente
`L(m)≤C(m)≤κL(m)` para todos os tamanhos e condições admitidos, o ótimo `F̂`
para `μ/L` satisfaz, para o ótimo real `F*` de `μ/C`,

\[
\frac{\mu(\hat F)}{C(|\hat F|)}\ge
\frac{\mu(\hat F)}{\kappa L(|\hat F|)}\ge
\frac{\mu(F^*)}{\kappa L(|F^*|)}\ge
\frac1\kappa\frac{\mu(F^*)}{C(|F^*|)}.
\]

No modelo ideal de ondas preenchidas de tamanho `B`, custo constante `c` por
onda e `m≥1`, `C(m)=c⌈m/B⌉` admite `L(m)=c(1+m/B)/2` e `κ=2`.
Esse exemplo não prova custo constante de GPU. Preparação, transferência e
reduções precisam entrar em `C`; dependência de raiz/forma exige limites
uniformes também nessas variáveis. Uma tabela medida só certifica sua própria
aproximação numérica, não tempos futuros de uma GPU sujeita a ruído.
Uma garantia de fator dois pode ser fraca demais para justificar o método.

## 5. Comparadores competentes

- Geração nativa serial, com o mesmo contrato numérico e cache final reutilizado.
- Spiffy v4: contagens, seleção conectada e poda online; também o controle
  simplificado de grau um da v3. Ajustar os tamanhos por latência, sem enfraquecê-los.
- Cadeias especulativas/SSD com tamanho escolhido pelo mesmo perfil de custo;
  política de custo adaptativa inspirada em CaDDTree, identificada como adaptação.
- Oráculo pequeno: para `N≤20`, agregar recompensas por máscaras de prefixo e
  calcular `μ` para todos os `2^N` conjuntos por transformação zeta; otimizar
  diretamente `μ/C`, inclusive para custo não afim. É controle forte, não ingênuo.
- Seleção online usando o cabeçalho da raiz e políticas atualizadas nos estados
  visitados pela própria execução; registrar também tempo de calibração/seleção.

## 6. Custo completo e viabilidade em 12 GB

O preparo inclui traces, ranks, universo, certificados e perfil de latência.
Resolver usa até `N+1` cortes em grafos `O(N+P)`, além de reconstrução e replay.
A exatidão requer racionais ou inteiros escalados; tolerância de ponto flutuante
não vira prova exata. Com denominador comum `D` dos pesos, as
razões usam somas de até `P` recompensas e `a+bm`, `m≤N`; os bits dessas somas,
razões e capacidades são polinomiais no tamanho da entrada. Cada preço é
recalculado como razão desses dados, sem uma cadeia ilimitada de denominadores.
O custo dos cortes deve contar esses bits, não apenas operações aritméticas.

A memória de GPU cresce com `B` e o contexto, sem reter `N` cabeçalhos completos;
metadados CPU crescem com `N×bloco`, e o tempo neural cresce com `⌈|F|/B⌉`.
Isso é um desenho compatível com testar em 12 GB, não uma medição de cabimento.
Contar pesos quantizados, ativações, picos de logits, cópias, sincronização,
planejamento, primeira inferência, eventos terminais, saída e amortização do preparo.
Não há treinamento; qualquer RNG de avaliação deve ter custo e seeds registrados.

## 7. Objeções e limite entre objetivo local e trajetória

O teorema otimiza o replay de uma macro sob raízes congeladas, não o tempo de
uma geração inteira. Exemplo abstrato numa cadeia nativa: a política A avança
dois passos em raízes pares e dez em ímpares; B avança três em todas as raízes.
Sob raízes uniformes, A tem média seis, B três. Partindo de zero, A visita apenas
pares e avança dois por macro; B avança três. Com custos iguais, ou intercepto
dominante e diferenças pequenas de custo, escolher A pelo objetivo congelado
piora a execução integral. O exemplo não é observação de um modelo neural.

A distribuição das raízes muda porque a política salta estados. Frequências de
treino, pool top-1, equivalência numérica, custo afim e generalização podem falhar
separadamente. Calibrar melhor o objetivo local não elimina isso. Um pool pequeno pode tornar o
oráculo zeta mais barato; muitas ondas podem eliminar qualquer paralelismo útil.
Prioridade continua frágil diante da combinação direta Gupta + razão clássica.

## 8. O que falta e critério para avançar

Antes de protótipo extenso: auditar a contribuição própria restante; delimitar o
decoder e sua equivalência numérica; verificar a redução por enumeração independente;
congelar perfil, casos, splits e controles competentes.
Uma eventual avaliação deve separar ganho de objetivo em replay de latência
integral em geração, incluindo custos amortizados e perdas/recusas preservadas.
Só uma melhoria substancial e reproduzível de tempo completo, sem mudar a saída
nativa e com contribuição além da integração conhecida, justificaria selecionar
esta direção como tema central. No estado atual, esses requisitos estão abertos.
