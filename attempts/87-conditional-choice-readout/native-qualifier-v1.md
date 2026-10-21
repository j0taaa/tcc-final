# A87 — qualificação nativa V1 de desenvolvimento

**Preparação, sem forwards. Não é gate de seleção do tema central.** Congelar
este protocolo, o coletor e `native-inputs-v1.json` antes de capturar respostas.
Executar primeiro as auditorias CPU da operação e da política. Uma coleta
correta não demonstra prioridade, aceleração integral ou qualidade geral.

## Operação e consumidor

Classificação BANKING77 entre os **77 nomes naturais originais**. Trocar somente
`_` por espaço; manter caixa, pontuação e IDs produzidos pelo tokenizer. Sem
aliases inventados, índices de classes ou treinamento. Cada alternativa recebe
EOT `126348`, seguido de PAD `126081` até comprimento fixo
`L = max(comprimento lexical) + 1`. Estes são símbolos explícitos no score:
não há parada precoce ao encontrar EOT, nem remoção de seus PADs. O bloco A é
o slot 0; B contém os outros `L-1` slots. O contexto lista as 77 alternativas e
solicita exatamente uma intenção para o pedido. Os slots começam todos com MASK
`126336`. Contexto total no máximo 2048, sem truncamento.

O alvo é a mistura de duas políticas nativas de dois blocos, conforme a
[nota matemática](star-certificate-analysis.md), com raízes e respostas congeladas:

\[
\alpha_a=\tfrac12p_0(a),\quad
\beta_b=\tfrac12\prod_{i=1}^{L-1}p_i(b_i),\qquad
J(a,b)=\alpha_a\prod_{i=1}^{L-1}p_i(b_i\mid a)
       +\beta_b p_0(a\mid b).
\]

Uma consulta fixa exatamente os IDs de A ou de B e revela todas as cabeças
selecionadas desse canvas em B1. A raiz e **cada A/B distinto** são capturados
uma única vez por caso; compartilhamentos são preservados. Não se condicionam
as cabeças a pertencer ao conjunto de rótulos. A massa fora das 77 alternativas
é `1 - sum(J)`; não renormalizá-la silenciosamente. O alvo de score e as políticas
de blocos têm antecedentes em [TUBE](https://arxiv.org/abs/2605.24292) e
[DUEL](https://arxiv.org/abs/2603.01367); não são contribuição alegada.

## Fontes e seleção anterior aos resultados

[BANKING77 / PolyAI](https://github.com/PolyAI-LDN/task-specific-datasets/tree/57ec275d8078af65b7731c2a98be812d844a6d6b/banking_data),
revisão `57ec275d8078af65b7731c2a98be812d844a6d6b`, arquivos
`categories.json` e `train.csv`. Atribuição: Iñigo Casanueva, Tadas Temčinas,
Daniela Gerz, Matthew Henderson e Ivan Vulić, 2020,
[Efficient Intent Detection with Dual Sentence Encoders](https://arxiv.org/abs/2003.04807).
A licença primária é [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/),
intitulada **“Attribution 4.0 International”** no `LICENSE` do repositório.
Pedidos permanecem iguais; a transformação dos nomes e sua tokenização são
explicitadas acima. Os dados são disponibilizados sem garantias, nos termos
da licença. Os arquivos completos e a licença ficam em cache ignorado
`artifacts/a87-native-v1-sources/`; seus SHA256 e URLs estão no manifesto.

Indexar as linhas de dados a partir de zero, excluindo o cabeçalho. Escolher as
oito menores strings hexadecimais SHA256 de `A87-native-v1:<índice>`, em ordem
desse hash. A seleção não usa texto, rótulo, logits ou resultados anteriores.
Todos os 77 rótulos são usados em todos os casos. Não substituir casos,
formatos, comprimentos ou partição depois da coleta. São exemplos de treino
reservados para qualificação de desenvolvimento, sem estimativa de generalização.

Tokenizer/modelo local GSAI-ML/LLaDA-8B-Instruct, snapshot
`08b83a6feb34df1a6011b80c3c00c7563e963b07`. `--prepare` carrega somente
o tokenizer e baixa fontes públicas; salva prompts, IDs completos, posições,
rótulos, arestas, índices, fontes e hashes. Não carrega pesos nem executa forward.
O coletor copia apenas a constante de localização usada em A86; não importa
código ou medições daquela aplicação.

## Coleta e contrato numérico

Batch 1, NF4, double quantization, computação BF16, quatro threads CPU, seed
87001, `use_cache=False`. Hook da projeção final calcula somente as L cabeças
dos slots, mantendo o contexto completo no transformer. Essa otimização exige
qualificação de fidelidade; sua equivalência bit a bit com outra forma de
projetar ou agrupar consultas **não foi estabelecida nesta etapa**.

Converter logits selecionados para FP32, excluir somente MASK por `-inf`,
e calcular softmax sobre **todo o vocabulário**. Cada entrada FP32 não negativa
é exatamente um inteiro `W / 2^149`. Para campo de expoente `e` e mantissa `m`:

\[
W=(m+\mathbf1_{e>0}2^{23})\,2^{\max(e-1,0)}.
\]

Somar os significandos em bins de expoente com `numpy.bincount`. O vocabulário
deve ter no máximo `2^17` IDs; cada bin soma inteiros menores que `2^24`, logo
é no máximo `2^41` e é somado exatamente em FP64. Reconstruir a soma inteira
com shifts Python, e usar `Fraction(W, sum_clean W)` para cada ID necessário.
Isso normaliza **exatamente a linha FP32 capturada no vocabulário limpo completo**,
incluindo todos os IDs fora das alternativas. Não é exatidão dos logits reais,
do softmax matemático ou de uma distribuição sem quantização.

Registrar por consulta SHA256 das linhas FP32, denominadores inteiros,
quantidade de zeros fora de MASK, frações dos componentes incidentes, tempo
wall/CPU, evento CUDA, custo de racionalização e memória. A raiz salva A, B,
caps, produto por rótulo e proposta de maior produto, com desempate pelo índice
original de `categories.json`. Os componentes condicionais e esses dados bastam
para reconstruir J, seus limites e as previsões do produto raiz sem novo forward.
Não salvar tensores completos ou grandes traces.

Se qualquer entrada limpa for zero, registrar `CLOSED`; não usar os lemas que
exigem interior estritamente positivo. Caps zero ou um contrato de certificado
não suportado devem ser reportados como não suportados no replay, preservando
o caso. Não adicionar epsilon, podar alternativas ou reclassificar zeros.
O teste considera todas as L cabeças, inclusive posições já fixadas: `CLOSED`
por zero numa cabeça fixada é uma classificação conservadora, mesmo quando as
cabeças efetivamente amostradas permaneceriam no interior.

O produtor registra SHA256 dos seis shards de pesos listados no índice,
`configuration_llada.py`, `modeling_llada.py`, config, índice e arquivos do
tokenizer. O hashing dos pesos é streaming (`hashlib.file_digest`), sem carregar
shards inteiros na RAM; registrar bytes e custos wall/CPU dessa etapa, incluídos
no tempo total. Validar os IDs, estrutura dos blocos/arestas, MASK e EOT/PAD
do manifesto antes da carga. Exigir shape de logits exatamente `L x 126464`.

Registrar versões, GPU, driver, RAM CUDA livre/total, processos estrangeiros,
carregamento e memória. Recusar se houver outro processo CUDA ou menos de
7 GiB livres antes da carga. Uma consulta verifica novamente processos CUDA.
Orçamento cooperativo de 30 minutos incluindo carga; checado antes de cada
forward. Há no máximo `8*(1+|A|+|B|)` forwards, com a contagem exata no manifesto
(limite absoluto `8*155`). Sem warmup neural adicional. Não repetir captura para
escolher um resultado. Saída em modo exclusivo `x`, somente sob `artifacts/`.
Recusa, erro, interrupção e progresso parcial são preservados; timeout/recusa são
inconclusivos. O orçamento cooperativo não garante preempção de um kernel travado.
`query_begin` registra a identidade de cada chamada imediatamente antes de
invocar o modelo; a contagem inclui invocações que falham, e não só respostas
capturadas. O tempo total preserva também carga, preparação e falhas.

## Análise posterior prevista, ainda não integrada

Replay racional deve reconstruir J e comparar o vencedor com a proposta do
produto raiz. Reportar a massa fora das alternativas, empates, caps zeros,
fronteira fechada/interior e fidelidade do contrato. Calcular certificado ótimo
**global** pelas quatro escolhas dos endpoints do vencedor, contagem de
obrigatórios e arcos previstos/errados pelo produto raiz. A previsão de cada
componente é `root_product / 2`; previsões nunca substituem respostas observadas.

Comparar contagens de consultas com lazy caps forte, escolha por custo e grau
máximo e controles por minVC. Custos unitários e depois custos observados têm
interpretações distintas; qualquer oráculo com vencedor/limiar verdadeiro deve
ser identificado, e suas consultas de obtenção contabilizadas numa aplicação.
O coletor não implementa a política online, não presume seu promise e não
calcula métricas antecipadamente. A política e os controles precisam de fontes
e protocolo próprios congelados antes de avaliar seu desempenho.

Nenhum ganho de wall time pode ser inferido de replay de consultas. Custo total,
projeção, batching, aquecimento, preparo, RNG, saída e decoder nativo ainda
precisam de avaliação operacional própria. Acurácia destes oito exemplos de
treino não sustenta superioridade, melhoria geral ou escolha do tema central.

O diagnóstico congelado `native_replay_v1.py` usa certificados **CLOSED** em
todos os casos, sem oferecer ao controle informação sobre cabeças futuras.
Calcula OPT global, obrigatórios exatos e o controle lazy de uma consulta por
passo especificado no cabeçalho. Condição necessária de desenvolvimento: em
pelo menos dois dos oito casos, `lazy - OPT >= 2` e `10*lazy >= 11*OPT`.
São margens possíveis sobre esse controle, não ganho do método novo. Todos os
casos precisam estar completos e suportados; caso contrário, inconclusivo.
Falha encerra V1 sem ampliar casos ou trocar partição para resgatá-la. Sucesso
apenas justificaria considerar a política nativa; não seleciona tema central.
Somas racionais podem exceder 4.300 dígitos; o diagnóstico libera esse limite
de serialização para dados locais confiáveis e paga aritmética/saída em bits.

## Comandos

Preparação permitida antes do freeze, sem modelo:

```bash
.venv-live/bin/python attempts/87-conditional-choice-readout/native_qualifier_v1.py --prepare
```

**Somente após freeze e auditoria CPU**, captura nova:

```bash
.venv-live/bin/python attempts/87-conditional-choice-readout/native_qualifier_v1.py \
  --capture --output artifacts/a87-native-qualifier-v1.jsonl
```

O coletor verifica que seus três arquivos coincidem exatamente com `HEAD`.
Nenhuma inferência está autorizada pelo simples preparo destes arquivos.
