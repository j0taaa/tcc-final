# Novidade e utilidade do MWPC e do reparo JSON: revisão crítica

**Atualização de escopo:** após esta revisão, o usuário reafirmou que o TCC deve
priorizar dLLMs. O [protocolo M22](m22-dllm-discovery-protocol.md) e os
[resultados ao vivo](generated/m22-results.md) passam a orientar a aplicação
principal. A proposta de reparo externo abaixo é histórica e auxiliar; a revisão
de antecedentes continua válida dentro do seu recorte.

Consulta: **28/09/2026**. Código examinado: commit
`87ceedb6315acf6a41bd16b19cd450da49a0e84c`.
Resultados locais: M21, produzidos pelo commit `47b93c4`.

## Parecer

**O problema tem uso real. A novidade algorítmica ampla não se sustenta.
Uma contribuição aplicada e incremental é defensável; a utilidade prática desta
implementação ainda precisa de confirmação em erros reais.**

Reparo por distância mínima, restrições gramaticais ponderadas, interseção de
gramáticas com autômatos e geração JSON restrita já têm antecedentes claros.
O principal antecedente adicional é *The Weighted CFG Constraint*, de 2008:
ele aproxima o trabalho de técnicas clássicas de programação por restrições,
além dos trabalhos de parsing ponderado já citados no TCC.

O diferencial a investigar é a adaptação e avaliação dessas técnicas para
seleção de propostas paralelas em suporte finito de tokens, com posições
comprometidas, rastreabilidade e semântica explícita de término; o reparo é uma
aplicação desse mecanismo. A revisão não estabelece prioridade mundial nem
autoriza chamar a combinação de inédita apenas porque não apareceu idêntica
nas fontes consultadas.

## Como a busca foi conduzida

Revisão exploratória, não revisão sistemática. Foram pesquisadas combinações de
`minimum edit JSON repair`, `weighted CFG constraint Hamming`,
`error correcting parsing minimum distance`, `grammar constrained diffusion
parallel decoding`, `JSON repair data preservation`, `certified minimum cost
repair` e problemas de reparo em projetos públicos. Seguiram-se referências e
links para artigos, páginas de autores, documentação, código e incidentes.

Foram lidos textos ou seções relevantes dos trabalhos centrais abaixo. Para
*Debugging Inputs*, usou-se o resumo institucional dos autores; sua avaliação
completa não foi reanalisada. Repositórios e documentos de projeto são evidência
de funcionalidades anunciadas, não validação independente de desempenho.
As datas dos artigos vêm da publicação, não da data de indexação da busca.
Links para `main` são mutáveis e foram consultados na data acima.

## Antecedentes que delimitam a contribuição

| Fonte primária | Relação com este TCC e limite da comparação |
| --- | --- |
| [Aho e Peterson, 1972, *A Minimum Distance Error-Correcting Parser for Context-Free Languages*](https://epubs.siam.org/doi/10.1137/0201022) | O reparo de linguagens livres de contexto por distância mínima é um problema clássico. Não reivindicar sua invenção. |
| [Katsirelos, Narodytska e Walsh, CPAIOR 2008, *The Weighted CFG Constraint*](https://gkatsi.github.io/papers/knwcpaior08.pdf) | Seções 2 e 4: variáveis com domínios finitos, CYK ponderado e restrições suaves com distâncias de Hamming e edição. É o antecedente mais próximo para o núcleo de otimização por substituições. A publicação é de 2008, embora o preprint arXiv seja de 2009. |
| [Hanneforth, 2011](https://aclanthology.org/W11-4408/) | Algoritmo de interseção de CFG ponderada com autômato finito. Parsing ponderado sobre uma representação de alternativas não constitui novidade geral. |
| [Pasti et al., EACL 2023](https://aclanthology.org/2023.eacl-main.52/) | Interseção CFG/linguagem regular, incluindo tratamento de epsilon. Fundamenta a construção; não atribuir ao TCC a ideia geral. |
| [Kociumaka e Saha, versão corrigida de 2024](https://arxiv.org/abs/1411.7315v4) | Distância de edição e parsing com pontuações são problemas já estudados. Usar a versão corrigida ao discutir complexidade. |
| [Korn et al., PVLDB 2013, *On Repairing Structural Problems in Semi-structured Data*](https://www.vldb.org/pvldb/vol6/p601-korn.pdf) | Reparo estrutural de dados, sobretudo marcação aninhada, com programação dinâmica ótima e heurísticas. Preservar conteúdo e evitar alterações em cascata já são motivações explícitas. Não é uma comparação de desempenho com o nosso JSON. |
| [Diekmann e Tratt, ECOOP 2020, CPCT+](https://soft-dev.org/pubs/html/diekmann_tratt__dont_panic/) | Recupera conjuntos de reparos de custo mínimo em um ponto de erro de parser LR. Sua garantia local e critérios de retomada diferem da otimização sobre toda a sequência finita deste TCC. |
| [Kirschner, Soremekun e Zeller, ICSE 2020, *Debugging Inputs*](https://pure.royalholloway.ac.uk/en/publications/debugging-inputs/) | DDMax recupera entradas processáveis removendo fragmentos. A noção de minimalidade usada não equivale à otimalidade global do nosso objetivo. |
| [Luo et al., ISSRE 2025, *Automatic Data Repair without Format Specifications*](https://rahul.gopinath.org/resources/issre2025/luo2025automatic.pdf) | epsilonREPAIR explora informações de erros do parser para reparar dados, incluindo JSON, sem uma especificação formal fornecida separadamente. Preservação de dados já é métrica central. Seu corpus de corrupção também não equivale a uma amostra de falhas espontâneas de LLM. |
| [Mündler et al., *Constrained Diffusion Language Models*](https://constrained-diffusion.ai/) | Restrições gramaticais e geração estruturada com difusão já são aplicações publicadas. A existência de preenchimentos de lacunas abstratas não é a mesma condição que uma testemunha com número fixo de slots. |
| [Jin e Han, EPIC, 2026](https://arxiv.org/html/2606.00722v1) | O algoritmo de seleção usa aproximação regular, divisão por confiança e redução validada. Isso deixa uma pergunta pertinente sobre qualidade da seleção perante um ótimo no mesmo suporte. Comparar contratos diferentes exige explicitar a diferença. |
| [CLAD, 2026](https://arxiv.org/html/2605.29607v1) | Já há seleção paralela exata em outra formulação, baseada em conflitos entre grupos de atenção. Não reivindicar genericamente a primeira seleção ótima de tokens em difusão. |

### Por que mudar o nome do objetivo não cria um problema novo

No reparo com uma proposta original por posição, peso `w_i >= 0` e sequência
original `x`, maximizar `sum_i w_i [y_i = x_i]` equivale a minimizar
`sum_i w_i [y_i != x_i]`: a soma dos pesos é constante. É distância de Hamming
ponderada, restrita à linguagem e ao suporte. Essa equivalência é uma dedução
direta do objetivo implementado, não um resultado experimental novo.

O MWPC geral admite múltiplas propostas e exige contabilização correta de
proveniência. Isso torna a implementação e a formulação específicas relevantes,
mas não elimina o parentesco com otimização gramatical ponderada. O artigo de
2008 usa pesos em produções; uma redução para pesos por posição/token precisa
ser descrita, não presumida como identidade literal de APIs.

### Ferramentas que também precisam ser consideradas

- [json_repair, Python](https://github.com/mangiucugna/json_repair): baseline já
  medido na versão 0.63.5, inclusive modos com esquema. Sua funcionalidade é mais
  abrangente que nosso suporte de substituições.
- [jsonrepair, TypeScript](https://github.com/josdejong/jsonrepair): outra
  implementação prática de reparo, com operações ausentes no protótipo.
- [agentjson](https://github.com/realsigridjin/agentjson): o projeto anuncia
  núcleo Rust, candidatos por busca em feixe, ordenação por esquema e informações
  de edição. Portanto, Rust, esquema e rastreabilidade isoladamente não são
  diferenciais suficientes. Seus números não foram reproduzidos nesta revisão.
- [SquirrelParser, documento de projeto](https://github.com/lukehutch/squirrelparser/blob/main/ERROR_RECOVERY_DESIGN.md):
  descreve busca exata de reparo e verificações cruzadas, incluindo limitações
  semânticas de custo mínimo. É documentação técnica, não artigo revisado por
  pares; serve como antecedente a examinar, não como benchmark validado aqui.

Dois resultados adicionais foram triados sem fundamentar o parecer: o
[rascunho OIP-CAD](https://github.com/xuda1979/papers/blob/main/paper_codex_patch.tex)
e a [descrição técnica CN120509399A](https://patents.google.com/patent/CN120509399A/en).
Encontrar terminologia semelhante nesses documentos não estabelece equivalência
de garantias, implementação ou resultados.

## Há necessidade real?

**Sim: reparar saída estruturada é uma função de software existente.** O Dify
[integrou json_repair para saídas estruturadas](https://github.com/langgenius/dify/pull/18977)
em 2025. Seu [gerador de respostas](https://github.com/langgenius/dify/blob/main/api/core/llm_generator/llm_generator.py)
contém caminhos que tentam leitura JSON e recorrem a reparo. Isso demonstra
adoção da tarefa em um produto, não demanda comprovada pelo nosso algoritmo.

Há um exemplo concreto de perda de conteúdo: um
[incidente do Dify](https://github.com/langgenius/dify/issues/31436) relata UUIDs
truncados ao reparar valores sem aspas. A
[correção incorporada em 24/01/2026](https://github.com/langgenius/dify/pull/31444)
atualizou a dependência após correção upstream. O episódio já foi resolvido e
não constitui vantagem sobre a versão 0.63.5 usada no TCC. Além disso, nosso
suporte atual não insere aspas: não há evidência de que resolveria aquela entrada.
O incidente fundamenta a importância de preservar conteúdo, não a eficácia local.

**Prevenção é uma alternativa forte.** Quando é possível controlar a geração,
[vLLM oferece saídas restritas por JSON Schema e gramática](https://docs.vllm.ai/en/latest/features/structured_outputs/).
Reparo não deve receber crédito por um problema que uma configuração acessível
do gerador já evita. Validade sintática tampouco garante verdade dos valores.

O cenário proposto mais plausível é uma etapa de recuperação em lote, após
receber saídas de uma fonte que não permite controlar o decodificador, ou quando
uma nova geração tem custo relevante. Um consumidor conhece a estrutura esperada
e consegue conferir valores contra a fonte. Reparo barato, validação, reparo
exato limitado e encaminhamento de falhas podem compor esse fluxo. Essa é uma
**hipótese de uso a testar**, não uma implantação realizada.

Há uma tensão importante: número fixo de tokens e BPE fazem sentido dentro do
decodificador de difusão; para corrigir um JSON externo, podem ser restrições
artificiais que reduzem cobertura. Deve-se comparar custo por byte/caractere e
por token e justificar a escolha pelo benefício ao consumidor. Proteger bytes
não garante que um valor continue associado ao mesmo campo.

## O que os resultados locais permitem dizer

O [relatório M21](../../paper/generated/m21_repair_v1/report.md) e sua
[interpretação](m21-findings.md) preservam os resultados completos:

- Nas aberturas corrompidas da confirmação, o exato recupera 20/20 documentos,
  contra 0/20 de json_repair nos modos avaliados. Porém, parser sem pesos,
  guloso e enumeração também acertam: esse contraste não isola os pesos.
- Na ablação de gramática ambígua, exato e enumeração recuperam 8/8 aberturas;
  guloso e parser sem pesos, 0/8. A enumeração é mais rápida nesse caso.
- Há uma classe em que o exato perde para o guloso, e outra em que não consegue
  representar a inserção que a biblioteca faz. Custo mínimo não significa
  recuperação da intenção.

São corrupções controladas de registros fictícios. As 4.992 chamadas incluem
métodos, tokenizações e repetições; não são 4.992 tarefas independentes. Não se
mediu taxa de ocorrência das falhas, economia de novas gerações ou superioridade
sobre os novos comparadores encontrados nesta revisão.

O [validador independente](../../src/mwpc_exact/validator.py) verifica caminho,
gramática, suporte, posições fixas, propostas e objetivo recalculado. **A
testemunha é verificável, mas sua verificação isolada não prova que inexiste
solução melhor.** A garantia de otimalidade depende do algoritmo e de sua
justificativa, apoiados pelos oráculos e testes diferenciais. Evitar apresentar
o artefato como uma prova autônoma de otimalidade verificada mecanicamente.

## Recorte recomendado e próximo experimento

Formulação defensável para a contribuição:

> Adaptação de otimização gramatical ponderada à seleção de propostas em suporte
> finito de tokens, com testemunhas verificáveis, e avaliação reproduzível de
> quando sua aplicação ao reparo estrutural preserva mais dados que heurísticas.

Pergunta prática prioritária: **adicionar a etapa exata a um fluxo convencional
recupera mais registros corretos, com custo aceitável e sem aumentar alterações
indevidas?** A palavra “corretos” exige referência externa, não só parsing válido.

Para o mês restante, manter o solver atual e concentrar a evidência:

1. **Semana 1 — congelar a avaliação.** Dois ou três formatos pequenos de
   registros compatíveis com o domínio declarado; conjunto independente de
   desenvolvimento; orçamento e critérios publicados antes da confirmação.
   Testar casos públicos de reparo separadamente. Eles não estimam frequência
   de erros de LLM e não podem ser usados para ajustar e confirmar o método.
2. **Semana 2 — coletar saídas reais.** Como desenho inicial, 100–200 documentos
   com respostas esperadas, incluindo todos os outputs, válidos e inválidos.
   Registrar modelos/revisões, prompts, custo e configuração. Separar templates
   entre desenvolvimento e confirmação. Se quase não houver falhas, relatar a
   baixa incidência: não provocar erros e chamá-los de espontâneos.
3. **Semana 3 — comparar o fluxo inteiro.** Validação + json_repair atualizado
   com esquema; uma segunda biblioteca; o mesmo fluxo acrescido do exato; uma
   nova tentativa do modelo; geração restrita quando disponível. Para a alegação
   algorítmica, incluir um reparador clássico de custo mínimo sobre o mesmo
   suporte, além da enumeração pequena já existente. Avaliar a viabilidade de
   adaptar epsilonREPAIR/CPCT+ sem tratar suas diferentes garantias como iguais.
4. **Semana 4 — analisar e escrever.** Recuperação integral e por campo,
   preservação de valores e associações, cobertura do suporte, abstenções,
   erros introduzidos em entradas válidas, latência e custo total. Comparações
   pareadas por documento; repetições de tempo não aumentam a amostra de tarefas.
   Incorporar ao artigo os antecedentes desta revisão e todos os resultados.

Se o orçamento só permitir um comparador adicional, priorizar uma biblioteca
prática no experimento de uso; restringir a alegação algorítmica em vez de alegar
superioridade sobre algoritmos exatos não implementados. A inclusão de inserções,
deleções, outro modelo ou um novo algoritmo completo não é requisito deste
recorte de um mês.

Um resultado positivo convincente seria um ganho incremental de recuperação
correta em casos reais previamente separados, perante o fluxo convencional,
com latência/custo e perdas documentados. O tamanho do ganho não pode ser
prometido antes da coleta. Se o benefício não aparecer, o resultado controlado
continua existindo, mas não deve ser convertido em alegação de utilidade geral.

O [JSONSchemaBench](https://arxiv.org/abs/2501.10868) fornece uma referência de
esquemas e de avaliação de geração estruturada; não fornece, por si só, os pares
de entrada corrompida/resposta correta de que esse experimento precisa. O
protótipo tampouco suporta automaticamente todos os seus esquemas.

## Alegações autorizadas e vedadas

| Defensável com a evidência atual | Ainda não defensável |
| --- | --- |
| Ótimo para o objetivo, etapa e suporte declarados (`exact_on_support`). | Ótimo sobre todas as edições, vocabulário ou trajetória de geração. |
| Vantagem de recuperação em classes controladas identificadas. | Superioridade geral, ganho de produção ou economia de retries já demonstrados. |
| Aplicação específica e artefato reproduzível de técnicas conhecidas. | Primeiro reparo JSON mínimo, primeiro parser ponderado ou primeira geração CFG por difusão. |
| Testemunha com fatos checados independentemente. | Certificado que sozinho demonstra optimalidade ou preservação semântica. |
| Demanda documentada por reparo e preservação de dados. | Adoção, necessidade ou eficácia comprovadas deste pacote em produção. |

Esta revisão atualiza o posicionamento e o plano. Não modifica medições,
configurações congeladas ou o PDF entregue anteriormente, e não substitui uma
nova campanha experimental por uma conclusão desejada.
