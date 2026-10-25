# Resultado A89 — não selecionada como contribuição central

**A investigação e o piloto foram executados. A evidência não sustenta avançar
esta formulação como tema central do TCC.** Não foi obtido algoritmo geral novo,
benefício funcional neural ou vantagem integral. Isso não demonstra impossibilidade
de toda abordagem de expansão sob CFG; encerra a qualificação desta implementação
especializada, sem campanha adicional para resgatar o resultado.

## O que foi implementado e por quê

Um verificador exato de capacidade em IDs reais do LLaDA, com propagação
bidirecional incremental em C++ e uma referência CUDA em operações inteiras
Torch. Uma MASK consome exatamente uma posição. IDs com vários caracteres ou
lexemas e aliases mantêm seus efeitos completos. EOS/EOT só podem aparecer
depois da raiz JSON fechada e o restante é padding EOS; não há remoção interior.

O estado do parser especializado é (profundidade de arrays, estado lexical).
O limite de 96 IDs implica profundidade máxima 192, pois um ID admitido abre
no máximo dois arrays. Isso permite representar **exatamente, nesse orçamento**,
uma linguagem recursiva de arrays de strings ASCII, sem espaços ou escapes.
Não é JSON completo, SQL, C++ ou uma representação compacta de qualquer CFG.
São 23.582 IDs admissíveis, 44 classes de efeito e 771 estados.

Para cada proposta fora de ordem, o teste fixo cruza prefixos alcançáveis e
sufixos coacessíveis. O adaptativo permite a proposta se há um caminho no grafo
(posição, estado) que consome o canvas e insere até o orçamento restante.
Consumir posição custa zero e inserir um token custa um. O caminho de custo
mínimo determina conjuntamente quantas MASKs inserir e em quais fronteiras;
somente MASKs são inseridas, sem fornecer a testemunha ao modelo. CPU usa
fechamento por Dijkstra; GPU usa a mesma distância min-plus preparada.

Esse mecanismo admite deliberadamente propostas que o fixo recusaria. Se todo
compromisso preserva uma conclusão nas posições atuais, não aparece impasse por
falta de espaço espontaneamente. As falhas finais observadas são esgotamento
de passos/shortlist e erros semânticos, não uma refutação dessa invariável.
Confiança baixa é exclusivamente o gatilho do controle simples; não é sinônimo
de inviabilidade atual ou de inviabilidade sob qualquer expansão permitida.

Os algoritmos de alcance, propagação e caminhos mínimos usados são clássicos.
Não foi demonstrada contribuição algorítmica própria suficiente. Contrato e
reconstrução determinística estão em [mechanism.md](mechanism.md).

## Protocolo e dados realmente novos

[Protocolo](protocol-v1.md), produtores e inputs foram congelados por hashes
antes dos forwards. As únicas correções anteriores foram um dtype CUDA não
suportado e um teste de paridade que desconsiderava padding; logs preservados.

BBH word_sorting pinado, seleção por hash sem filtro: dois textos VAL e quatro
TEST. Cada texto origina JSON plano e JSON agrupado pela inicial. São quatro
itens VAL e oito TEST, mas apenas quatro listas independentes no TEST. A segunda
tarefa é uma transformação própria, não um benchmark publicado. O gabarito não
entra no verificador. Não há sobreposição de índices com a seleção BBH de A84;
isso não certifica ausência de exposição no treinamento do modelo.

Mesmos pesos locais LLaDA-8B-Instruct, snapshot
`08b83a6feb34df1a6011b80c3c00c7563e963b07`, NF4/double-quant/BF16, RTX 3080 Ti
12 GiB. Nenhum treino, compra de compute ou captura neural antiga reutilizada.
Os pesos, ambiente e binário Rust existentes são identificados em
[reused-assets.json](evidence/reused-assets.json).

Foram executados **48 decodes VAL + 336 TEST**, incluindo três repetições
pareadas, 8/16 passos, sete modos e ordens rotacionadas. TEST contém 3.996
forwards e 332,215 s somados de decode. VAL contém 566 forwards e 84,175 s.
Com os dois warmups, são 4.564 forwards reais. Nenhuma execução pontuada foi
descartada. Há 207 saídas TEST incompletas por orçamento e 129 completas válidas;
nenhuma exceção ou timeout chegou ao registro externo. O fallback interno do
selector EPIC não foi instrumentado individualmente, portanto não se afirma
ausência de exceções internas silenciosas.

## Resultado funcional e comparação integral

**Zero acertos da tarefa em todos os métodos, nos oito itens TEST e nos dois
orçamentos.** Também não houve acerto em VAL. Repetições de tempo não transformam
esses oito itens derivados em 336 problemas independentes.

VAL escolheu fixo32 em ambas as famílias por desempate de tempo entre
32/64/96, todos com zero acertos. A reserva96 foi mantida separadamente. A
auditoria CPU posterior encontrou gabaritos com 10–60 IDs na tokenização
canônica, incluindo EOS: todos cabem na reserva96. Esse diagnóstico não foi
fornecido às políticas e não é um certificado de tokenização mínima.

A tabela mostra a mediana entre itens, após tomar a mediana das três repetições
de cada item. Tempos em segundos incluem prompt, tensorização, modelo/head,
ranking, verificações, transferências, inserções, saída, avaliação e sincronização.

| Método | Plano 8 | Plano 16 | Agrupado 8 | Agrupado 16 | Válidos TEST / 48 execuções |
| --- | ---: | ---: | ---: | ---: | ---: |
| Fixo CPU, 32 | 0,5503 | 1,1039 | 0,5646 | 1,1316 | 36 |
| Fixo GPU, 32 | 0,6014 | 1,1567 | 0,6073 | 1,1738 | 36 |
| Adaptativo CPU, 32→96 | 0,5616 | 1,1174 | 0,6647 | 1,1590 | 12 |
| Adaptativo GPU, 32→96 | 0,6228 | 1,1673 | 0,8384 | 1,2901 | 12 |
| Expansão simples CPU | 0,5550 | 1,1223 | 0,6708 | 1,3673 | 15 |
| Reserva generosa CPU, 96 | 0,6879 | 1,3789 | 0,7862 | 1,5696 | 3 |
| EPIC, 96 | 0,7211 | 1,3980 | 0,8785 | 1,6633 | 15 |

Razões **pareadas por item/repetição** frente ao melhor controle medido, fixo32
CPU, diferem da razão das medianas acima:

| Regime | Adaptativo CPU / controle | Adaptativo GPU / controle |
| --- | ---: | ---: |
| Plano, 8 passos | 1,0116 | 1,1208 |
| Plano, 16 passos | 1,0006 | 1,0483 |
| Agrupado, 8 passos | 1,0694 | 1,2858 |
| Agrupado, 16 passos | 1,0125 | 1,0818 |

Nenhum gate de continuidade passou. Não há ganho de acerto, as candidatas não
reduzem tempo e perdem validade. Intervalos bootstrap por item estão nos
[dados agregados](evidence/analysis-v1.json); com quatro itens por família são
descritivos, não evidência de generalização. As curvas completas, mesmo com
acerto zero em todos os pontos, estão no [SVG](evidence/quality-latency.svg),
[PNG](evidence/quality-latency.png) e [CSV](evidence/analysis-v1.csv).

O controle simples insere quatro MASKs perto de baixa confiança, com o mesmo
verificador CPU incremental; é uma ablação inspirada em DAEDAL, não reprodução
integral do método. O EPIC preservado recebeu o mesmo filtro lexical,
softmax reutilizado por forward, preparo lexical reutilizado e omissão de
forwards sem MASK. Seus 540 forwards TEST ficam abaixo dos 576 de cada outro
modo; não foi derrotado por computação vazia deliberada. Seu oráculo de lacunas
lexicais arbitrárias difere do teste exato em IDs, logo não se exige trajetória
igual ao fatorial. Nenhuma recuperação automática escondeu saídas incompletas.

Um programa determinístico que extrai e ordena as palavras do mesmo prompt
resolve 8/8 itens TEST; `[]` resolve 0/8. Não foi feita medição competitiva de
latência desse programa. Esse teto demonstra que a tarefa não necessita dLLM.
O zero neural geral limita a interpretação: este piloto não qualifica um
decoder útil nem distingue totalmente danos do prompt, gramática ampla e
política de compromisso. **Não é evidência de que a expansão em geral seja
incapaz de melhorar um decoder competente.** É evidência suficiente para não
promover este protótipo nem investir em sua aceleração para o TCC.

## Perfil CPU, equivalência e custo completo

O verificador CPU competente consumiu mediana de **1,4375%** do decode
adaptativo VAL. O gate pré-fixado exigia 10%; não foi escrito kernel próprio.
Eliminar esse componente medido pouparia aproximadamente 1,4% nesse perfil,
antes de pagar a comunicação/preparo da alternativa. O resultado não diz que
todo parser, linguagem ou regime do EPIC custa pouco.

TEST adaptativo CPU: 42,985 s completos, dos quais 41,386 s de modelo e 1,161 s
de verificação/alocação. GPU: 48,701 s completos, 41,160 s de modelo e 7,090 s
de verificação/alocação. As categorias são disjuntas; o restante fica como
residual de ranking/tensores/saída/instrumentação, sem somar tempos aninhados.
GPU e backbone compartilham a placa; esta implementação é serial, sem overlap
presumido. Operações Torch, lançamentos e a cópia da testemunha são pagos.

Cada braço adaptativo realizou 516 expansões e inseriu 744 posições nas 48
execuções TEST. As contagens repetem trajetórias, não 516 situações independentes.
O controle simples inseriu 1.092 posições. Houve três execuções adaptativas
atingindo o teto96. Expansão muda o contexto: não há cache KV, e o próximo
forward recalcula tudo. Comprimentos e somatórios dos tokens processados por
forward estão em cada registro e no CSV; menor parsing não foi vendido como
aceleração neural.

Os **96 pares CPU/GPU** (48 fixos e 48 adaptativos) coincidem em todos os IDs,
estados emitidos, decisões e expansões. Antes disso passaram 1.554 configurações
finitas, 19.531 strings contra `json.loads`/oracle independente, 48 alocações
pequenas e 15 configurações com tokenizer real. Auditoria CPU adicional passou
1.460 propostas e 365 atualizações incrementais, incluindo dependência conjunta
entre duas lacunas. Isso comprova o domínio testado, não qualquer CFG.

Picos alocados TEST: aproximadamente 5,45 GiB nos modos próprios e 6,13 GiB no
EPIC, incluindo o modelo. Reserva Torch máxima 7,24 GiB e RSS cumulativo do
processo 3,56 GiB; a reserva retida pelo allocator e o RSS **não** são medidas
isoladas da memória de cada algoritmo. Não são a memória total da placa/sistema.
O preparo GPU do verificador alocou inicialmente 2.780.160 bytes.

Compilação C++ medida sem `.so` em cache: **0,859 s**. Preparo de tokenizer e
tabelas: 1,555 s em VAL e 0,785 s em TEST; init GPU dentro disso foi medido
separadamente nos logs. Preparo EPIC: 1,946/0,074 s. Carga do modelo:
**249,133/81,325 s**; warmup: 0,840/0,777 s. São custos observados em duas
execuções com cache de arquivos distinto, não uma distribuição de latência fria.
Importação Python, hashes de origem e inicialização anterior ao primeiro
marcador não têm um cronômetro global do processo; portanto o uso frio completo
é **parcialmente medido**, e não se publica uma soma desses marcadores como
latência fria integral. Essa limitação não afeta os decodes sincronizados
integrais e não poderia transformar o resultado sem acertos em sucesso.

Todos os custos detalhados e limitações de atribuição estão em
[costs-v1.json](evidence/costs-v1.json), [environment.md](environment.md) e
[implementation-notes.md](implementation-notes.md). A GPU foi liberada após TEST;
nenhuma execução A89 posterior concorreu com o piloto A90.

## Originalidade, antecedentes e decisão

DAEDAL já insere MASKs por confiança; DreamOn já treina estados de expansão e
remoção; Mündler et al., apêndice E, já discutem expansão e o custo de contar
tokens restantes. EPIC já oferece lexing reutilizado, parsing e compromissos
paralelos. Gram2Token já leva restrições gramaticais à GPU. FactorDLM já oferece
inferência finita CPU/CUDA: o alcance de nossa representação pode ser codificado
como fatores em cadeia, sem reivindicar nova inferência finita.

A busca encontrou ainda [SWYB](https://arxiv.org/html/2608.28229) e
[TruncProof](https://arxiv.org/html/2605.13076), antecedentes de horizonte e
distância em tokens para conclusão gramatical. A distinção ainda investigável
seria representar e alocar capacidade **conjunta** entre lacunas fora de ordem
para CFGs gerais com custo competitivo. Não se encontrou uma prova/algoritmo
próprio que realize isso; o caminho mínimo neste autômato especializado é
clássico. [Fontes iniciais](sources.md) e [auditoria adicional](priority-audit-v2.md)
separam implementação, sugestão e diferenças de escopo. Ausência de colisão
idêntica numa busca não certifica prioridade mundial.

Para o objetivo de contribuição original e substancial com benefício positivo
demonstrável, **este caminho ainda não está adequado**. Não há base para alegar
artigo, originalidade ou benefício neural. Não se recomenda outro experimento
da mesma campanha: primeiro seria necessária uma contribuição algorítmica
distinta e um consumidor neural justificado. A implementação e os resultados
negativos ficam preservados para revisão, sem reescrever A19/A28/A36.

## Reprodução e revisão

Os registros brutos [VAL](evidence/val-v1.jsonl) e [TEST](evidence/test-v1.jsonl)
guardam IDs, estados, propostas/decisões próprias, expansões, contagens e tempos.
[reproduce.sh](reproduce.sh) executa o fluxo em nomes novos e sob o lock comum.
[prepare_inputs.py](prepare_inputs.py) reproduz os inputs byte a byte;
[analyze.py](analyze.py) regenera a seleção, agregados, pareamentos e gates.
O vendor e os resultados históricos ficaram intactos. Entrega local, sem PR,
publicação, treinamento ou compra de recursos.
