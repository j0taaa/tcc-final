# A77 — compartilhamento de charts e erro no quociente semântico

Este arquivo começa como contrato, auditoria de prioridade, prova escrita e
protocolo **antes dos dados**. A seção de resultados será acrescentada em outro
commit. Base: `84b34969`. Escopo exclusivo desta tentativa; A73/A75 foram
consultadas em leitura nos caminhos absolutos fornecidos pelo usuário. Nenhuma
aplicação encerrada será reaberta.

## Operação e consumidor

Uma consulta recebe um único head original congelado, m módulos alinhados de
n slots, pesos racionais positivos w[j,k,v], suporte S comum entre módulos,
uma mesma GLC não ambígua G e os mesmos pins de IDs nas posições relativas.
P é a lei produto desses pesos condicionada a cada módulo pertencer a G e
respeitar os pins. Não é MWPC, trajetória nativa, lei de commitments ou medida
de qualidade. Normalizar cada linha do head antes de definir w é parte do
contrato; não mudar essa escala depois para melhorar δ.

O consumidor proposto é um pool não ordenado de candidatos AST puros de uma
mesma linguagem: construtor externo `Bag(AST_1,...,AST_m)`, que mantém repetições.
Isso serve, por exemplo, para entregar termos de uma soma/conjunção pura a um
avaliador independente da ordem. Não se deduplicam termos e não se reivindica
que esse consumidor seja frequente em workloads reais. A linguagem usada é
`E ::= a | b | (E+E) | (E*E)`, fatorada para LL(1). O AST de cada módulo mantém
operador, associação e ordem interna. Só a permutação dos módulos externos é
ignorada. Não se declara `if`, subtração, chamadas com efeitos ou floating point
com redução dependente da ordem comutativos.

Primeiro se amostram IDs originais; só depois se faz a projeção σ para o bag de
ASTs. Aliases de bytes e caminhos de tokenização distintos conservam suas
massas, multiplicidades e slots. A prova começa no bag mais fino de sequências
de IDs, e a projeção determinística posterior também satisfaz a cota. EOS/PAD
ausentes; separadores externos são IDs fixados fora dos módulos. Pins diferentes
entre módulos, liberação de posições, expansão de suporte, outra gramática ou
outra semântica não recebem esta garantia. Condição adicional C deve ser uma
união de órbitas (pode ser condição no bag de ASTs), com massa positiva.

## Método e benefício verificável proposto

r[k,v] = mean_j w[j,k,v]; e[j,k,v] = w[j,k,v]/r[k,v] - 1;
δ = max_{j,k,v em S} |e[j,k,v]| < 1.
Construir um único chart inside H com r, amostrar m módulos de H e reconstruir
os IDs. Q é a lei resultante antes da projeção. Para C, é necessário amostrar
Q(.|C), por exemplo com atributos finitos explícitos ou rejeição contabilizada;
o chart de Q sem C não é amostrador da lei condicionada. Não há promessa de
eficiência para C rara. O benefício candidato é reduzir avaliações de charts
de m para uma enquanto se certifica TV após σ. Não se elimina backbone/head.

## Auditoria primária de prioridade (consulta em 2026-10-19)

- [εACP, v3, 27/08/2025](https://arxiv.org/html/2504.20784v3), algoritmo 1,
  equação 5, apêndice D e teorema 7: já agrupa fatores próximos, substitui
  potenciais pela média aritmética e trata simetrias comutativas. Seu bound de
  distribuição conjunta é de distância de razão logarítmica; não atribuímos ao
  artigo a cota quadrática específica de A77.
- [HACP, v2, 29/08/2025](https://arxiv.org/html/2505.22288v2), algoritmo 2,
  linhas 17–21: a mesma substituição pela média, com hierarquia de grupos e
  cotas. Não exige calcular primeiro leis completas dos módulos para agrupar
  seus fatores unários correspondentes.
- [Roos, v3, 21/02/2018](https://arxiv.org/pdf/1612.03702v3), introdução,
  teoremas 3.3 e 4.1: aproxima permanente normalizado por produto das médias
  das colunas e apresenta expansão de segunda ordem. A órbita de A77 é um
  permanente m×m, mas as médias de seus fatores de módulo não são exatamente
  os produtos das médias das folhas. A identificação não permite invocar uma
  constante de Roos sem controlar também essa diferença.
- [Roos 2008, v1](https://arxiv.org/pdf/0811.0622), observação 2.1(b),
  equações 14–18: convolução de leis por potência de sua média e cancelamento
  de primeira ordem. Média de leis completas de ASTs é outro aproximante e
  em geral custaria m charts; não é o controle correto para A77.
- [Van den Broeck–Niepert 2014](https://arxiv.org/html/1412.0315): simetrias
  aproximadas para propostas MCMC corrigidas por Metropolis–Hastings. Não é
  uma garantia de mistura finita nem o sampler independente de A77.
- [Severo et al. 2021](https://arxiv.org/html/2107.09202): compressão de
  multisets e leis exchangeable. Ignorar ordem e preservar multiplicidades
  não é uma nova ferramenta de A77.
- [Goodman 1999](https://aclanthology.org/J99-4004/): parsing por semirings.
  Compartilhar subproblemas com as mesmas entradas é programação dinâmica
  usual, não uma nova operação neural.

### Redução competente que ameaça a contribuição inteira

Escrever a densidade como ∏j 1[G,pins](x_j) ∏jk w[j,k,x_jk]. Aplicar o pooling
de εACP/HACP **aos unários das folhas**, agrupados por k, dá exatamente r.
Manter os indicadores gramaticais idênticos como restrições duras, sem alterar
zeros. Não se invoca um teorema desses artigos que exija positividade dos
indicadores: a identidade do aproximante é algébrica. O grafo contém m cópias
idênticas após o pooling. Um parser competente memoiza uma avaliação de H e
faz m extrações. A proposta, seus IDs, RNG e custo são idênticos aos de A77.
A comparação não dá m charts de presente ao controle: ele também calcula a
média nas folhas antes de compilar/avaliar. Não precisa enumerar ASTs.

A parte do certificado que resta é o cancelamento em uma órbita, seguido de
concentração de permutações e normalização. A prova abaixo reconstitui esse
passo sem ferramenta nova ou propriedade especial de G. Não foi localizado
nessa auditoria um teorema com exatamente a mesma constante D; isso não
estabelece prioridade. Uma constante/corolário específico precisa benefício
próprio para sustentar o TCC. O gate de novidade é **não demonstrado** já aqui;
mesmo eventual cobertura neural não estabelece avanço sobre esse controle.

## Prova escrita (não Lean)

Fixar uma tupla de módulos de IDs x=(x_1,...,x_m) admissível. Q é constante na
órbita, incluindo os estabilizadores quando há módulos repetidos. A razão
entre massas **não normalizadas** da órbita é

    A_x = (1/m!) Σπ ∏jk (1+e[j,k,x_{π(j),k}]).

Cada elemento distinto aparece |Stab(x)| vezes; portanto 1/m!, e não um peso
uniforme incorreto sobre bags, é a média certa. Definir Sπ como o log do
produto. Para |t|≤δ<1,

    t - t²/[2(1-δ)] ≤ log(1+t) ≤ t.

Por exemplo, a parte negativa vem de Σ_{l≥2}|t|^l/l ≤ t²/[2(1-δ)]. Para cada
k e valor fixo v, Σj e[j,k,v]=0. Uma permutação uniforme dá EΣjk e=0,
inclusive com repetições. Logo −a≤ES≤0, a=mnδ²/[2(1-δ)].

Uma transposição troca dois módulos e altera 2n termos. Como a derivada de
log(1+t) é no máximo 1/(1-δ), |Sπ−Sπτ|≤c=4nδ/(1-δ).
Revelar π(1),...,π(m−1). Duas escolhas possíveis no próximo passo podem ser
acopladas por trocar esses dois rótulos nas permutações restantes. Assim os
valores condicionais do martingal de Doob estão em intervalo de largura c,
não apenas em [−c,c]. O lema de Hoeffding para variável centrada em intervalo
de largura c dá log E exp(S−ES)≤(m−1)c²/8=b, com
b=2(m−1)n²δ²/(1-δ)². O último rótulo é determinado. Jensen dá

    −a ≤ log A_x ≤ b;  osc_x log A_x ≤ D=a+b.

Se m=1, e=δ=0 e P=Q. Para os demais casos, se U é a razão não normalizada
de massas, U∈[L,H] e H/L≤exp(D). Normalizar dá TV=E_Q|U/E_Q U−1|/2.
Para média μ, a convexidade de |U−μ| dá TV≤(H−μ)(μ−L)/(μ(H−L)).
Maximizar em μ∈[L,H] (máximo em sqrt(LH)) fornece

    TV(σP,σQ) ≤ (sqrt(H/L)−1)/(sqrt(H/L)+1)
              ≤ tanh(D/4) ≤ D/4.

Restringir a órbitas de C com massa positiva não muda [L,H]. Uma projeção
determinística adicional agrega razões por médias com pesos Q positivos,
preservando o intervalo. Portanto o mesmo bound vale para σP(.|C) e
σQ(.|C), independentemente de quão rara C seja. Isso é estabilidade de uma
razão RELATIVA uniforme, não eficiência de condicionamento raro, nem a
aplicação inválida de uma cota absoluta de TV dividida por P(C).

O permanente acima usa B[j,l]=∏k(1+e[j,k,x_lk]); A=per(B)/m!.
Sua média de coluna é 1+O_n(δ²), pois o termo linear se cancela. Logo a
aproximação de permanente e a correção da média de coluna são precisamente
os dois efeitos clássicos a controlar; Roos não deve ser apresentado como
se sua matriz fosse simplesmente 1+e de uma folha quando n>1.

Para duas Bernoulli contrapostas, p_1=(1+δ)/2, p_2=(1−δ)/2, Q tem p=1/2.
As quatro diferenças ordenadas dão TV_texto=δ/2+δ²/4; o bag de dois valores
dá TV_bag=δ²/2. A vantagem de ordem é real em tamanho fixo: δ permitido de
ordem sqrt(ε) versus ε. O exemplo não prova novidade ou vantagem neural.

## Custo completo e controles

Backbone, head de vocabulário original e leitura/média continuam: O(mnV)
valores; somas/divisões racionais também custam seus bits. Compilação comum
do forest é reutilizável por **todos**; m charts exatos com pesos distintos
podem ser avaliados em batch/cache de topologia. A77 reduz somente avaliações
numéricas para uma. Um chart da recorrência específica n=253 tem 168.672
termos de split e oito têm 1.349.376: contagem, não lower bound nem latência.
Não se transfere essa razão para speedup de geração.

Controles: charts exatos heterogêneos com topologia em cache/batch; pooling
manual com exatamente a mesma média; εACP/HACP nas folhas mais cache; parser
especializado competente; média de leis completas só como aproximante
distinto. Para o controle da mesma média, lei e operações coincidem, logo não
há separação operacional atribuível a A77. Os certificados podem ser usados
por esse mesmo controle.

K amostras continuam emitindo Kmn IDs (Ω(Kmn) saída), com RNG exato inteiro,
rejeições do randbelow, backtracking, bytes e projeção. Produtos/inside podem
ter operandos de muitos bits. Cobrar também preparação, armazenamento do
head, transferências, suporte, pins e condições extras; não ignorar custos de
atributos ou rejeição para C. Um head neural armazenado em floats vira uma lei
racional representada; isso não certifica exp/softmax reais de precisão infinita.

## Protocolo V1 congelado antes da execução

Tolerância ε=1/100, sem alteração após os dados. Cobertura suficiente exige
δ<1 **e D/4≤ε**, computados com racionais em TODO S, nunca em top-k adaptado.
Rejeitar a cota suficiente não prova TV real>ε. Recursos ocupados, OOM,
timeout, zero massa gramatical e erro são resultados distintos.

1. Oráculo CPU independente: suporte sintético de IDs 0..7 emitindo
   `a,a,b,(,),+,*,(a`. Enumerar IDs e reconhecer bytes por descida recursiva,
   sem usar parser da biblioteca para a referência. Casos fixos (m,n,pin):
   (2,1,nenhum), (3,1,nenhum), (2,4,nenhum), (2,5,nenhum), (2,5,ID3 em k=0).
   Pesos racionais normalizados por linha, seeds 770101..770105, vieses
   1/100 e 1/5. Conferir massas/marginais e a lei de TODOS os ramos do sampler
   do chart contra enumeração independente, média nas folhas contra controle
   manual e razões de órbita contra permanente. Auditar TV, bound, aliases e
   pins; condição C fixa: todos os ASTs do pool são idênticos. Para C usar a
   lei condicionada enumerada dos DOIS métodos, sem amostrar outra lei.
   Bernoulli δ=1/100,1/10,1/2 e uma condição rara separada com base b=1/1000
   são checks algébricos, não testes de utilidade. Seeds RNG 770201+i,
   32 pools/caso; reportar bits/operandos/saída, sem inferir lei por frequências.
2. Gate local novo, separado de A72/A73: Qwen3-0.6B diffusion MDLM, revisão
   `c8d24a3f4adaeef46881b450e1bf7d1005203bd7`, cache absoluto
   `/home/jota/projects/tcc-final/.cache/a52-model-metadata`, ambiente existente
   `.venv-a52`. Sem treino/download. Pesos/tokenizer hashes conferidos no
   produtor; BF16 eval, SDPA, TF32 off, cache off, 4 threads, seed 770301.
   Dois prompts abaixo × (m,n)=(2,13),(8,13),(8,253), nessa ordem. São seis
   casos de desenvolvimento construídos, não benchmark de qualidade.

   P0: `Return an unordered pool of pure arithmetic expression AST candidates.
   Each module uses only a, b, (, ), +, and *. Modules are interchangeable;
   retain duplicates. Fill every masked module, separated by #.\nPool: `

   P1: `Propose a bag of candidate symbolic expressions for a pure commutative
   sum. Use grammar E ::= a | b | (E+E) | (E*E) in each module. Module order is
   ignored; internal AST order is retained. Separate modules by #.\nPool: `

   Prefixo tokenizado sem template; n máscaras originais por módulo e ID `#`
   fixado entre módulos. Nenhum pin interno. S contém TODOS os IDs ordinários
   do tokenizer cujos bytes não vazios pertencem a `[ab()+*]+`, incluindo
   representações multibyte. Verificar independentemente com decoder original;
   manter aliases se houver. Não filtrar por logits, viabilidade ou resultado.
   EOS/PAD/MASK não pertencem a S. Há fronteiras de slots fixas: não admitir
   tokens que atravessam módulos. O escopo é **exact_on_support**; registrar
   massa de S sob softmax de vocabulário completo em cada posição. Não
   renormalizar S antes de tirar a média. A GLC condiciona esses IDs depois.
   Head original BF16 em blocos de 32 posições; softmax FP64 no vocabulário
   inteiro; os pesos capturados são racionais exatos dos floats representados.
   Guardar captura completa de S fora Git, hash e testemunho racional extremo
   no resultado pequeno. Sem amostragem neural se cobertura falhar.
3. Lock exclusivo `/tmp/tcc-final-candidate-tests-gpu.lock` para todo uso de
   GPU e timing. O coordenador confirmou todos os checkouts preparados antes
   da execução. Preflight: nenhum processo compute alheio e utilização ≤5%
   antes de carregar; ao longo da captura verificar processos alheios por caso.
   Se ocupado, registrar recusa de recurso para todos os casos pendentes;
   não matar `llama-server` ou outro processo. Teto de carga 180 s, de cada
   caso 120 s, sem substituir modelos/casos. Limites não são inviabilidade.
   Captura de head é custo do gate, não benchmark comparativo: tempos/RSS/GPU
   são descritivos, uma execução, sem alegação de speedup.
4. Seleção científica exige conjuntamente novidade substantiva demonstrada,
   cobertura em todos os seis casos e benefício integral contra o melhor
   controle da MESMA operação. O controle pooling+cache já reproduz a proposta;
   por isso esta rodada não implementará um extenso benchmark de parsing para
   procurar separação artificial. Cobertura positiva isolada não seleciona
   A77. Se recursos impedirem a captura, a cobertura neural fica inconclusiva;
   a objeção de prioridade/controle não desaparece. Não ampliar os casos.

Objeções/faltas antes dos dados: δ exige proximidade relativa em todo suporte;
o coeficiente n² pode inviabilizar ε=0,01; o suporte lexical não é vocabulário
inteiro; nenhum consumidor externo foi validado; não há prova formal Lean,
novidade demonstrada, ganho de qualidade ou benefício neural integral.
