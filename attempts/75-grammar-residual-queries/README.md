# A75 — Consultas residuais contra uma referência gramatical

Investigação autorizada na branch existente, a partir de
`84b3496952243f2a5b3c5dd2d31191073be3a304`. Esta tentativa não reabre
aplicações encerradas nem altera o estado global da pesquisa.

## Operação e possível contribuição

Um consumidor hipotético fornece um oráculo **coerente**: uma chamada devolve
todas as marginais condicionais de uma mesma lei conjunta P, sob qualquer
pinning. O objetivo é uma amostra aproximadamente conjunta de P usando uma
referência normalizada R, fixa, amostrável e condicionável. P é acessível somente
por esse oráculo; a fórmula e os valores de F não são dados ao sampler.
Na família principal, R é uniforme nas palavras binárias com n/2 uns e
P=RF/E_R F, com 1≤F≤1+α e Lipschitz αc/√n em distância de Hamming.
Não se restringe F a uma função da contagem. EOS/PAD estão ausentes; os dois
IDs abstratos originais são 0 e 1, com bytes `0` e `1`, sem aliases agregados.

A possível contribuição é a análise uniforme Θ(α) da **especialização**
residual para essa classe e essa interface, incluindo a gramática não regular
quando se consideram todos os comprimentos. Cada fatia finita é regular.
Não é a invenção do factory, de clipping, Rao–Blackwell ou rejeição.
O benefício verificável procurado é erro conjunto menor que o de R com
O(α) consultas, independentemente de n; ganho de tempo exige referência
muito mais barata que o oráculo. Um consumidor neural real ainda é um gate.

## Antecedentes primários conferidos

Consulta em 2026-10-19, versões acessíveis nas URLs abaixo. Busca delimitada
por combinações de grammar/reference, single-increment, conditional marginals
e FORS; ausência de resultado não certifica prioridade mundial.

- [SIRS, §5.2, v1 de 15/10/2026](https://arxiv.org/html/2610.22238):
  já apresenta incremento aleatório, sua média sobre posições, clipping e
  factory Poisson. A75 substitui o denominador produto por condicionais da
  mesma referência e analisa uma classe de tilts sob pinning.
- [FORS, §3.1 e Teorema 3.1](https://arxiv.org/html/2602.01338): já admite
  proposta arbitrária q e estimador limitado do log-tilt. FORS com R e o
  mesmo incremento é exatamente nosso algoritmo, portanto um empate obrigatório.
- [Pemantle–Peres](https://arxiv.org/abs/1108.0687): concentração e stochastic
  covering são antecedentes. A prova abaixo usa diretamente a fatia uniforme;
  não presume extensão para Bernoullis ponderados.
- [FactorDLM, §3.1](https://arxiv.org/html/2609.32900): condiciona o produto
  congelado de um passo. Esse alvo é diferente de uma conjunta com condicionais
  acessíveis por remasking.
- [PoE-Bridge](https://arxiv.org/html/2606.08048) usa aproximações de chunks;
  [Twister, §3](https://arxiv.org/html/2609.35609) distingue alvo por passo de
  trajetória. Nenhum fornece automaticamente o oráculo exigido aqui.
- [Autospeculation](https://arxiv.org/abs/2511.07869) estuda paralelismo de
  consultas: rodadas e número total de avaliações são métricas distintas.

O teorema completo específico não foi localizado nos primários examinados.
Isso deixa prioridade e relevância científica abertas, inclusive porque os
ingredientes e o mecanismo de amostragem já são conhecidos.

## Hipóteses, controles e custo

[A prova escrita](proof.md) reconstitui o argumento e seus limites, antes do
protótipo. [O protocolo](protocol.json) congela casos, controles, métricas,
precisão, seeds e gates antes de execução científica ou timings. Os oráculos
finitos são testes da implementação, não prova universal nem observação neural.

Controles: R sem consultas; sequential+closure; FORS com o mesmo estimador;
SIRS original com proposta produto, mantendo zeros e massa fora da gramática;
posterior produto congelado (comparação de alvo); e pair heat bath em bloco de
duas posições, que se move na fatia. Single-site Gibbs fica congelado e não
serve como comparador competente. Refresh da referência fica fora do lower
bound estacionário. A antiga instância hard-core tem também um controle de
reconstrução por uma consulta raiz, sem ocultá-lo.

Cada proposta paga amostragem de R, máscara, RNG, aritmética e saída. Uma
consulta paga transformer, head **completo** e normalização; nenhum desses
custos é medido por uma tabela sintética. Se R exigir um root head novo,
somar uma consulta por operação ou declarar amortização. R balanceada não o
exige. Em CFG geral há inside/outside por máscara, não um inside universal.
Fisher–Yates parcial custa O(n) operações de palavra e O(n log n) bits
esperados de RNG e memória de índices; rejeições do RNG não têm teto fixo.
R_i(1)=k/l exige O(log n) bits; o denominador agregado precisa de dois logs.
Logs/exp reais ideais não são binariamente idênticos a Torch/CUDA.

Objeções centrais: a hipótese de oráculo é forte; tolerância κα tende a zero
com α, mas R já está a O(α) de P; as constantes do teorema podem ser ruins;
FORS empata exatamente; uma fórmula conhecida de F pode permitir zero
consultas. A consulta raiz não identifica o par witness BALANCE, mas isso não
é lower bound contra uma consulta arbitrária. A melhoria relativa no pequeno
oráculo não estabelece benefício de decoder, semântica ou prioridade.

## Resultado da rodada

**Positivo no oráculo, ponte neural não estabelecida.** Os 12 casos BALANCE
passaram pelo gate congelado; a reprodução hard-core concordou com os números
do briefing, mas seu reconstrutor especializado é mais forte. FORS com o mesmo
estimador empata exatamente. A prova escrita sustenta Θ(α) na interface
declarada, sem certificar prioridade ou utilidade prática de decoder.

O primeiro oráculo falhou numa posição fixada em zero: a
[correção explícita](correction-v1.md) preserva a origem e o dado negativo.
O [relatório](report.md) separa prova, auditoria finita, execução contada,
controles e gate neural. Dados: [auditoria corrigida](results-v1-corrected.jsonl),
[execução sem timings](runtime-v1.jsonl) e [replay de bits](runtime-bits-v1.json).
Não houve forwards de modelo nem timings sob concorrência. Esta rodada fica
encerrada sem selecionar uma contribuição neural positiva.
