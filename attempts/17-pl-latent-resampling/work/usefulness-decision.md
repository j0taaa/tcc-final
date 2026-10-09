# Decisão encerrada: onde há benefício e onde não escolher a mistura

**Há benefício útil e delimitado para obter muitas amostras independentes do
posterior de propostas descartadas após uma seleção PL, em uma predição
gramatical congelada de dLLM. Não foi confirmada uma vantagem geral de
treinamento, inferência final ou uma contribuição inédita suficiente para
publicação.** Esses são vereditos diferentes.

## Operação que justifica a escolha

Depois de fixar alguns tokens, a seleção por confiança também informa algo
sobre os tokens descartados. Condicionar apenas aos valores fixados perde essa
informação. O alvo inclui a probabilidade da ordem PL observada. Um usuário
pode querer estimar, por exemplo, a frequência condicional de um token
alternativo ou uma estatística da proposta descartada para auditar essa política.

A mistura permite amostrar esse alvo usando o circuito gramatical existente e
pesos racionais, sem escrever seu normalizador exato. A escolha prática aparece
quando são necessárias muitas saídas e a preparação é amortizada. Não é um
decoder que produz o JSON final mais rápido, nem mede confiança semântica na
resposta do modelo.

Os [resultados completos gerados](evidence/utility/final-utility-decision.md)
contêm os nove inputs M34 originais: oito compilam, 48 eventos, 13 métodos ou
configurações, três repetições e 6.215.868 draws aceitos. Uma compilação segue
inconclusiva. Os mesmos estados/seeds são usados nas campanhas sequenciais;
isso não é um experimento simultâneo pareado de latência, nem uma nova avaliação
independente de generalização.

Em `json-context0-16`, potência 1, oito commitments, o lote de 4096 tem medianas
de **8,67 s contra 21,41 s** do SingleTilt: aproximadamente 2,47 vezes. Cobrando
a compilação, **11,08 s contra 23,82 s**, aproximadamente 2,15 vezes. O SingleTilt
usa envelope secante e precisão fortalecida; não é rejeição sem otimização.

Nesse mesmo evento, BaseRejection não completou em 60 s de amostragem, e a
enumeração recusou o produto cartesiano acima do limite declarado. Os perfis
compactos com mais espaço também esgotaram os 30 s de preparação nas três
granulações/repetições. Portanto essa observação não depende apenas dos antigos
tetos de 1M células/3M transições. Ela não prova que nenhuma implementação de
perfis, enumeração ou outro algoritmo possa melhorar esses tempos.

O critério predeclarado de redução de pelo menos 20% em CPU e parede, com sinal
favorável nas três repetições contra os controles concluídos, passa em **3/48**
eventos com circuito disponível e em **2/48** quando se cobra compilação.
O [prefixo de 1024](evidence/utility/final-prefix-decision.md) não apresenta
nenhum ganho que satisfaça esse critério. A preparação e todas as perdas entram
no relato; não escolher somente um tamanho/caso vencedor.

## Situações em que eu não a escolheria

No estudo neural, seis documentos externos foram selecionados por hash antes
dos forwards, sem injetar tokens do gabarito. Foram executados 4044 registros
com nove estimadores e 12 configurações de gradiente da cabeça real de MDLM,
com aproximadamente 38,6 milhões de parâmetros e backbone congelado.

Uma réplica iid reduz a variância entre 8,75% e 40,06%, preservando a média do
estimador especificado. Porém **a média condicional por enumeração vence nas
12 configurações** nos quatro escopos de custo. Ela vence até o piso ideal de
custo extra zero para uma réplica iid, recalculado pelo gerador do relatório.
Logo tornar os perfis mais baratos não muda essa recomendação. Essa redução
de variância não é uma descoberta do projeto: é Rao–Blackwellização conhecida.

Use enumeração quando ela couber e for mais barata. Use rejeição simples ou
uma inclinação única quando já tiverem boa aceitação. Se a proposta original
foi conservada, considere MH/Gibbs estacionário para redução de variância com
réplicas correlacionadas; independência não é obrigatória para essa finalidade.
O controle MH foi executado. A versão contínua de Gibbs foi somente derivada.
Na tarefa auxiliar com referência conhecida, esses resultados também não
justificam escolher RL em vez de treinamento supervisionado mais simples.

Não houve atualização de parâmetros, curva de aprendizado, comparação de
qualidade final com EPIC, inferência em GPU ou avaliação de gradientes do modelo
inteiro. A operação neural foi testada; melhor treinamento completo permanece
sem demonstração.

## Benefício matemático que não depende desses tempos

A [auditoria da prova](mathematical-review.md) verifica a lei condicional e o
limite esperado polinomial **relativo ao circuito fornecido**, incluindo
aritmética em bits e enclosures racionais. Não garante que toda gramática
arbitrária compile em tempo/espaço polinomial nem verifica todo o Python/Rust.

A [separação escrita](product-proposal-separation.md) mostra uma família JSON
com custo esperado exponencial para qualquer proposta produto única, mesmo
assimétrica e otimamente escolhida, enquanto a mistura mantém limite
polinomial. O comparador é essa classe, não todos os algoritmos: um contador
especializado também é polinomial naquela família.

A [obstrução em bits](normalizer-bit-obstruction.md) mostra que escrever a
fração normalizadora exata pode exigir mais de 2^m bits para entrada de O(m²)
bits, embora amostrar exatamente seja polinomial. Essa vantagem de contrato é
compartilhada com rejeição simples na família do teorema. O
[corolário de auditoria](conditional-audit-corollary.md) liga a operação a uma
precisão probabilística declarada; seu limite por contagem de propostas é
teórico. Os outputs cronometrados/censurados não receberam certificado de 95%.

Esses argumentos justificam a operação matematicamente. Não provam prioridade
histórica, exclusividade do método ou significância suficiente para publicação.

## Controles, limites e reprodução

Os perfis receberam CDFs exatas, majorantes fortes, três granulações, índices
inteiros e finalmente 10M células/30M transições com proteção de 3 GiB de RSS.
Todos os 48 eventos foram executados. A última campanha tem 76 recusas por
prazo e duas por RSS; nenhuma por aqueles tetos de tabelas. RSS é observado em
verificações periódicas e inclui reservas do alocador; não é pico exato nem
comparação de memória com métodos cujo RSS não foi registrado.

Foram verificados 321 fluxos completos idênticos entre perfis tradicionais e
compactos, e mais 342 entre compactos e controles com mais recursos, incluindo
prefixos. A igualdade inclui hashes de caminhos, histogramas e tentativas.
Não houve mudança silenciosa da operação. Históricos, erros de harness e a
campanha interrompida continuam preservados.

Capturas e momentos são reproduzíveis offline; refazer sua origem neural
exige o checkpoint público pinado. Os relatórios são gerados por
`utility_report.py`, com inputs/produtores/comandos/hashes em
[final-analysis-provenance.json](evidence/utility/final-analysis-provenance.json).
Não foram editados números de tabelas à mão. Provas novas são escritas, não
novos resultados de Lean ou revisão humana.

**Decisão para o projeto:** consolidar este kernel como contribuição candidata
especializada de inferência condicional e esta vantagem de lote como evidência
de uso. Não promovê-lo como avanço confirmado de treinamento/decoder nem
encerrar o gate de anterioridade e significância T3602. A última avaliação
resolve a objeção concreta dos recursos; não abre outra busca de casos até
fabricar uma vitória.
