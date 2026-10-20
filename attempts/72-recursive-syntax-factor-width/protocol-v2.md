# A72 V2 — Protocolo anterior às medições

Base: `c74ab700111adcc4b0cd9aa85fd0b560394e7d97`. Data: 2026-10-20 UTC.
Esta é uma investigação nova da A72; não reabre A65/A68/A70. Nenhum
resultado numérico desta V2 foi observado antes deste protocolo.

## Operação, hipótese e possível diferença

Preparar a distribuição do marcador e gerar uma amostra conjunta de
`S -> P # P; P -> ( P ) | [ P ] | ε`, com N slots e EOS/PAD ausentes,
a partir de pesos posicionais racionais. Preservar cinco IDs originais
de um tokenizer quando houver modelo. O alvo é o produto congelado
condicionado nesse suporte explícito, não a trajetória neural inteira.

A operação clássica calcula l+1 massas, cada uma com l fatores de pares,
em O(N²). A hipótese adjacente é calcular LOG-massas por aproximação
polinomial do kernel log(1+xy) e convoluções triangulares. Isso permite,
em aritmética real e sob |xy|<=ρ<1, custo
O(K N log² N), com K=O(log(N/ε)/log(1/ρ)). Não é uma alegação para
GLCs gerais. FFT, kernels de baixa dimensão, Taylor e condicionamento
são antecedentes clássicos; prioridade da composição não é presumida.

Defina A_i=w_i('(')+w_i('['), C_i=w_i(')')+w_i(']'),
x_i=(w_i('(')-w_i('['))/A_i e y_i=(w_i(')')-w_i(']'))/C_i.
O fator de um par a<b é A_a C_b (1+x_a y_b)/2. Para cada grau k,
H_s=Σ_{a<b,a+b=s} x_a^k y_b^k é calculável por divisão e conquista
com convoluções entre as metades. A soma no matching j usa somente
H_{2j-1}+H_{2l+2j+1}, interpretando índices ausentes como zero.
O erro absoluto de cada log-massa após K termos é no máximo
l ρ^(K+1)/((K+1)(1-ρ)). Se esse erro é <=η, a TV após normalização
é no máximo exp(2η)-1, cota conservadora suficiente. A amostragem
condicional dos tipos dado o marcador continua inteira e exata.

Antes de medir, escrever a derivação e suas objeções na própria A72.
O protótipo FFT64 não recebe automaticamente uma garantia numérica
universal da prova em aritmética real. A auditoria de cada caso deve
converter suas probabilidades de marcador a racionais e calcular a TV
exata contra massas inteiras independentes. O custo dessa certificação
entra separado E no total se necessária ao consumidor. Nenhum ganho
de proposta sem certificado será chamado ganho integral certificado.

## Casos fixados

- Sintéticos: N=33,129,513,2049; limites de viés r=0,25; 0,75; 0,99;
  seeds 720201,720202,720203. Para cada slot sortear A,C e marcador
  inteiros de 1 a 16; vieses numa grade racional de denominador 256,
  limitados por r, com pesos inteiros após escala comum por posição.
  Todos os 36 casos permanecem no relatório.
- Neurais: LLaDA-8B-Instruct, snapshot local
  `08b83a6feb34df1a6011b80c3c00c7563e963b07`, NF4 de quatro bits,
  sem treinamento, duas instruções abaixo e N=33,129,513, seis casos.
  Seed Torch 720204, quatro threads CPU, uma captura por caso.
  Instruções: (1) `Return two fully nested bracket expressions separated
  by #. Use only (, ), [, ], and #. Do not add explanation.`;
  (2) `Complete this structured payload using two nested expressions
  separated by #. Round and square brackets must match. Output only
  the payload.`. Usar template de chat do tokenizer e slots MASK após
  a instrução. Não escolher casos por suas respostas ou pelos vieses.
  Se faltarem IDs atômicos, registrar entrada não suportada. Guardar a
  massa fora dos cinco IDs; nunca alegar exatidão no vocabulário inteiro.

Recursos neurais: GPU existente de 12 GiB, sem interromper processos
alheios. Recusar carregamento se houver menos de 6,5 GiB livres; limite
externo de 180 s para carregar e 120 s por forward. OOM/timeout ficam
como recusas/inconclusivos, sem trocar modelo ou prompts. Não guardar
modelos nem logits de vocabulário completo no Git; somente seis linhas
de captura com os cinco pesos por posição e metadados, teto de 2 MiB.

## Controles, custos e decisão

Controles competentes da mesma operação: (1) condicionamento por
marcador com massas inteiras; (2) avaliação vetorizada quadrática de
log-massas, equivalente ao circuito contextual completo para essa
gramática; (3) cobertura que ignora os tipos, sem convolução, para
detectar ganhos explicáveis só por unários de orientação. A biblioteca
LL(1) mantida serve de controle independente em N<=33, com os limites
de recursos já existentes; não usar seu eventual custo como única base
para alegar aceleração.

Tolerância TV ε=0,01; η=log(1+ε)/2. O candidato escolhe o menor K cuja
cota de cauda é <=η/2, cobrando reserva numérica; se K>64, A_i C_i=0,
ρ>=1 ou existe peso zero, recusa antes da convolução. Recusa é uma
falha de cobertura desse método, não inviabilidade gramatical. Não
aumentar 64 ou mudar ε após os dados. Registrar todas as recusas.

Tempos CPU com `perf_counter_ns`, uma chamada de aquecimento e cinco
repetições, ordem rotativa por seed. Mediana e máximo por caso; preparação,
proposta, auditoria, RNG e saída separados. Usar o mesmo amostrador
inteiro condicionado a j para todos. Guardar estados racionais e sua
capacidade em bits; descrever memória do processo e do modelo. FFT64
é protótipo aproximado. Nenhuma rodada extra de tuning depois do gate.

Gate operacional: em TODOS os seis casos neurais suportados, TV<=0,01,
nenhuma recusa do candidato e mediana de preparação + certificação +
amostra menor que o melhor controle aplicável. Resultado sintético
favorável sem passar esse gate não estabelece utilidade neural. Não
confundir ganho do componente CPU com ganho da geração inteira: carga,
forward, transferências e captura também são cobrados e reportados.

Se o gate falhar, encerrar esta aplicação V2 e dar uma decisão explícita
sobre a A72 como contribuição central. Não ampliar casos ou transferir
a alegação para outro consumidor para salvar o resultado. O teorema de
representação e sua prova permanecem fontes separadas do experimento.
