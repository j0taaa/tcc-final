# A80 — Calibração certificada de uma projeção privada

Estado: candidata teórica, com prova escrita revisada por subagentes; aplicação
offline ainda não executada. Não há revisão humana, prioridade mundial,
privacidade de um executável ou utilidade semântica estabelecidas. A meta de três
temas distintos continua aberta.

## Operação e diferença proposta

Recebemos samplers e avaliadores normalizados de duas distribuições sobre os
mesmos IDs completos de uma linguagem pública finita: alvo congelado `P` e
referência pública `mu > 0`. Para `R > 1`, queremos calibrar

```text
c_a(x) = clip(P(x), a mu(x), R a mu(x)),  a in [1/R, 1]
Z(a) = sum_x c_a(x)
Q_a = c_a / Z(a)
```

A raiz `Z(a*) = 1` dá a projeção de `P` em `C_R`, a classe cuja amplitude da
razão `q/mu` é no máximo `R`. Clipping, projeção e SAA com controle variável são
conhecidos. A contribuição candidata é a condição global de Bernstein da
[prova](theory.md): ela permite orçamento uniforme de excesso KL sem curvatura
mínima. A realização comprimida preserva esse orçamento sem guardar todos os
ratios grandes. Histogramas e varreduras não são apresentados como invenções.

O consumidor deste desenvolvimento é um serviço de calibração e emissão de uma
lei racional em suporte gramatical implícito. Ele não representa a trajetória
nativa de uma dLLM. A aplicação a um head racionalizado é possível, mas este
protocolo não executa um modelo nem comprova utilidade de respostas privadas.

Antecedentes e comparadores: [Husain et al.](https://proceedings.mlr.press/v108/husain20a.html),
[Park et al.](https://arxiv.org/abs/2410.22699),
[Owen–Zhou](https://artowen.su.domains/reports/seis.pdf),
[MetaGrad](https://jmlr.org/papers/v22/20-1444.html) e
[Greenwald–Khanna](https://www.cis.upenn.edu/~sanjeev/papers/sigmod01_quantiles.pdf).
Uma SAA competente que use nosso lema recebe a mesma garantia; não se reivindica
superioridade sobre um algoritmo idêntico.

## Contrato

- `P` e `mu` são normalizadas, congeladas, com avaliadores correspondentes.
  Massa zero de entrada é um resultado separado. A referência cobre todo o
  domínio público. Expansões, mudanças de semântica ou de pins exigem preparação.
- IDs aliases continuam eventos distintos, mesmo emitindo bytes iguais. Posições
  e bytes são preservados; EOS/PAD estão ausentes. O domínio da aplicação é
  deliberadamente finito, sem alegação sobre cauda de outro vocabulário.
- A concentração usa amostras IID ideais. Seeds de um PRNG servem à reprodução
  experimental, não certificam privacidade de software. Emissão usa novas
  propostas, independentes da calibração; não reutiliza palavras selecionadas.
- A garantia de privacidade libera somente a palavra final. Contagens, limiar,
  tempos, recusas e consumo observável não integram esse teorema. Quantizar o
  head define outro alvo; não transfere a fidelidade ao softmax ideal.
- Falta demonstrar prioridade suficiente, custo integral competitivo e um
  consumidor com utilidade privada absoluta. Uma projeção pouco útil não se torna
  útil por ter pequeno excesso KL.

## Protocolo de desenvolvimento V1 — anterior às medições

O primeiro commit desta tentativa congela este protocolo e a prova. Depois da
implementação e dos testes, um segundo commit congelará o executável produtor.
Resultados novos ficam em um diretório novo. Correções científicas posteriores
terão origem explícita e não sobrescreverão estes arquivos congelados.

### Casos e fontes

São duas gramáticas LL(1), em slots de um byte, com comprimentos `8, 16, 32`:

```text
dyck: S -> '(' S ')' S | '[' S ']' S | epsilon
expr: S -> 'a' | '!' S | '&' S S
```

IDs: Dyck `0:'(', 1:')', 2:'[', 3:']', 4:'('`; expressões
`0:'a', 1:'!', 2:'&', 3:'a'`. As cópias são aliases originais, não fundidos.
Todos os slots estão livres. A referência tem pesos unitários por ID. O alvo
tem pesos positivos inteiros determinísticos de 40 bits:

```text
tag = ASCII('A80-v1|familia|n|posicao|id')
z = integer_big_endian(SHA256(tag)) mod (2^38 + 1)
w = 2^39 - 2^37 + z
```

`familia` é literalmente `dyck` ou `expr`; os demais números são decimais sem
zeros iniciais. O alvo condicionado usa esses pesos diretamente, normalizados
pelo inside. Não são logits ou observações de um modelo. A preparação gramatical
tem teto de 200.000 células, 1.000.000 alternativas e 5.000.000 operações de
preprocessamento. Não há poda probabilística.

Casos de correção, fora de timings: família de três átomos da prova; `P=mu`;
zeros de `P`; platôs; roots e bins nos extremos; aliases; tokens multibyte; pins
públicos; suporte de massa zero. Esses fixtures não selecionam casos favoráveis.

### Parâmetros, métodos e ordem

- `R in {2,16}`, excesso condicional `xi=1/50`, confiança por execução
  `beta=1/20`, seeds `{11,23}`.
- Majorantes públicos: `bar_b(2)=7/10`, `bar_b(16)=14/5` e
  `log(2/beta) <= 37/10`. Para SAA aproximada:
  `M=ceil(2*(32+56*bar_b/3)*(37/10)/xi)`.
- Grade escolhida por limites públicos: uniforme com
  `Q=ceil(32*(R+1)*max(1,bar_b)/xi)` ou diádica com
  `m=ceil(32*max(1,bar_b)/xi)`, `h=ceil(log2(R+1))`. Usar a de menos pontos;
  empate favorece uniforme. Nenhuma decisão depende dos dados.
- Métodos centrais: ratios retidos com bisseção certificada; índices quantizados
  retidos e ordenados; contagens densas com sweep; GK determinístico sobre os
  mesmos índices. GK usa `eps=xi/(128*max(1,bar_b))`, erro de CDF no máximo
  `2 eps`, e portanto erro adicional de score no máximo `8 eps`.
- Mediana R23: uniforme auxiliar de 64 bits, `eta=xi/(bar_b+xi)`,
  `M_med` é o menor ímpar pelo menos
  `2*(37/10)/(eta-2^-63)^2`. A correção `2^-63` contabiliza o erro de CDF do
  uniforme discreto. Ela tem orçamento próprio para a mesma meta condicional.
- Enumeração/histograma exato é controle quando a quantidade de palavras for no
  máximo 65.536; acima disso, registrar recusa por recursos, sem impossibilidade.
  O limite é conferido contando a linguagem antes de enumerar.
- Um certificado exato de `P in C_R` retorna `P` sem calibrar e recebe esse custo.
  No serviço, esse precheck usa max/min sobre o mesmo circuito, pago por todos.
- MetaGrad e CV com coeficiente aprendido permanecem controles teóricos
  adicionais. Este V1 não implementa uma garantia finita deles: nenhuma vitória
  deste ensaio estabelecerá superioridade sobre todos os calibradores. O
  propósito primário é verificar a realização com a garantia comum aprovada.

Há 24 configurações por método: duas famílias, três comprimentos, dois `R` e
duas seeds. A ordem é `(familia, comprimento, R, seed)` lexicográfica; os cinco
métodos amostrais são rotacionados ciclicamente pelo índice da configuração.
Source RNG de cada configuração é `Random` com seed-string
`A80-v1|familia|n|R|seed|source`; uniforme da mediana usa sufixo `|median`;
emissão usa sufixo `|emit`. Prefixos de amostras são compartilhados em lei entre
métodos, sem exigir independência entre métodos. Nenhuma amostra de calibração
é proposta final. O controle exato não usa calibração amostral.

### Custos, qualidade e recursos

Cada método é executado em processo novo, com o mesmo sampler preparado de
inside e massas das alternativas; esse preparo, inclusive CDFs se utilizadas,
fica disponível a todos. Não exigir outside de um controle que só precisa
amostrar. Não alterar a biblioteca mantida para o ensaio.

Registrar separadamente compilação/precheck, preparo de `P,mu`, coleta, solução,
emissão/validação e total da primeira saída. O total inclui geração e avaliação
de **todas** as palavras internas. Guardar apenas resumos e linhas compactas,
não todas as palavras/ratios. Registrar pico RSS do processo, payload dos estados
de calibração, largura máxima de operandos e bits RNG. Medição de objetos não
será apresentada como RSS ou VRAM. Não há custo neural medido neste ensaio.

A qualidade primária é o certificado da perda empírica aproximada que permite
aplicar a garantia condicional `(xi,beta)`. Em suporte enumerável, conferir
independentemente `a*`, normalização e excesso KL condicional; logaritmos são
diagnósticos numéricos ou intervalos certificados explicitamente identificados.
Três ou menos seeds não verificam uma probabilidade de falha. O teorema da KL
marginal final exige outro orçamento e não é atribuído a este desenvolvimento.

Emissão: 16 palavras por método, propostas frescas, envelope público
`(1-1/R)P+a mu`, 16 tentativas máximas, fallback fresco de `mu`. Isso conserva
`C_R` idealmente; não se atribui ao `K=16` a garantia marginal de outro protocolo.
Conferir IDs, bytes e gramática por reconhecedor independente.

Limites por processo: 1 GiB de endereço virtual, 120 segundos de parede e
200.000 palavras de calibração. Limite global: 900 segundos de parede. Ao
atingi-lo, registrar os casos restantes como não executados. Preservar timeout,
memória, massa zero, exceção e erro como resultados diferentes. Não repetir
somente perdas, escolher melhor seed, ampliar comprimentos ou alterar o gate.
Sem outros testes pesados/modelos em paralelo com os timings.

Correção é obrigatória. A economia de memória contra ratios retidos é uma
verificação de realização, não novidade. Uma promoção operacional restrita exige
redução de pelo menos 20% no total da primeira saída frente ao melhor controle
executado aplicável, nas duas famílias, usando mediana das razões por família;
recusas tornam a comparação correspondente inconclusiva. Falhar encerra esta
aplicação V1, preservando a prova. Passar ainda não prova utilidade privada
semântica, superioridade contra MetaGrad ou o objetivo de três temas.

## O que falta

Implementação, verificadores, congelamento do executável e execução deste V1.
Só depois caberá relatar resultados. Não há campanha neural selecionada.
