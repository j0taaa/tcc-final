# Parecer técnico e científico do TCC

Revisão de 28/09/2026. Código examinado: `a43e1cf904eceff8bbcc802b5c0b2abb1c10c059`
(`v0.2.0-4-ga43e1cf`), com árvore inicialmente limpa. Este parecer e o
reprodutor acompanhante são os únicos arquivos acrescentados pela revisão.
Não foram alterados implementação, artigo, dados, tarefas, branches ou releases.

**Avaliação:** há um trabalho de TCC tecnicamente consistente e uma contribuição
aplicada defensável. A evidência mais forte é um otimizador por etapa,
exato no suporte representado, com testemunhas verificáveis. A novidade
algorítmica é limitada pela literatura clássica de parsing ponderado.
Os experimentos atuais não demonstram melhora prática da geração completa.
Na confirmação realizada, a configuração exata é mais lenta e não obtém
sucesso funcional. Isso deve integrar a conclusão científica, como já ocorre
na versão atual do manuscrito.

## Achados que merecem correção

### 1. Prioridade média: o limite total da API gulosa não é verificado no retorno

Local: [selection.py](../../src/mwpc_exact/evaluation/selection.py), linhas
663–672 e 705–745.

`select_greedy_exact_feasibility` verifica o prazo antes/depois das consultas
de viabilidade e antes de reaproveitar uma testemunha, mas o caminho final
recalcula o score e retorna `FEASIBLE_ON_SUPPORT` sem comparar o tempo final
com `total_timeout_seconds`. Assim, uma conclusão tardia ainda leva score e
testemunha na API pública.

O [reprodutor mínimo](repro_greedy_total_deadline.py) usa `S -> a`, um slot,
uma proposta e um relógio injetado. Com limite 1 e relógio final 2, ambos os
backends retornam:

```text
backend=python status=feasible_on_support runtime_seconds=2.0 score=1.0 witness=(0,)
backend=rust status=feasible_on_support runtime_seconds=2.0 score=1.0 witness=(0,)
```

Comando: `.venv/bin/python docs/reviews/repro_greedy_total_deadline.py`.
O código de saída 1 é intencional: identifica a violação. Os tempos são valores
do relógio controlado, não medições de desempenho.

Correção sugerida: verificar o prazo também depois da recomputação final e
antes de construir o resultado conclusivo, retornando `TIMEOUT` sem certificado;
transformar o caso em regressão. Auditar também os caminhos sem nova consulta.

**Alcance:** não encontrei aqui um erro do ótimo MWPC. O runner M19 faz sua
própria checagem de prazo total em `run_review_offline.py:93`, protegendo os
resultados publicados desse estudo. O problema afeta consumidores diretos
da API e comparações que presumam que ela já aplica o prazo ao retorno inteiro.

### 2. Prioridade alta para a entrega: o bundle recomendado não contém a revisão atual

Local: [README.md](../../README.md), linhas 27–39;
[release v0.2.0](../releases/v0.2.0.md);
[metodologia do artigo](../../paper/main.tex), linha 485.

O README recomenda clonar `mwpc-exact-v0.2.0.bundle` e fazer checkout de
`v0.2.0`. O bundle local anuncia HEAD/main em `a309b1c`; o HEAD revisado é
`a43e1cf`. O tag v0.2.0 não contém configurações nem tabelas M18/M19.
Portanto, seguir a entrega anunciada não reproduz as últimas conclusões do
artigo atual. Há um PDF separado da auditoria em `dist/`, mas isso não atualiza
o bundle e o pacote de evidências anteriores.

Verificado com `git bundle list-heads dist/mwpc-exact-v0.2.0.bundle`,
`git describe --tags --always` e `git ls-tree -r --name-only v0.2.0`.

Correção sugerida: preparar uma nova entrega identificada por commit/tag,
contendo fonte, PDF e evidências correspondentes; atualizar o caminho principal
de reprodução. Preservar as releases históricas. Não foi criada release nesta revisão.

### 3. Prioridade média: o gate do artigo não verifica os valores M19

Local: [Makefile](../../Makefile), linhas 101–103 e 123–124;
[build_review_results.py](../../scripts/exact_commit/build_review_results.py),
linhas 18–20; [main.tex](../../paper/main.tex), linha 57.

`make paper` depende de verificadores M13 e M17. O manuscrito também importa
`generated/m19_selection_audit_v1/audit-values.tex`, que esses verificadores
não regeneram nem comparam. Uma edição acidental desses números pode passar
pelo gate anunciado. O CI também não supre essa verificação específica.

Nesta revisão, regenerei M19 manualmente a partir dos arquivos com hashes
verificados: tanto `summary.json` quanto `audit-values.tex` coincidem byte a
byte com os arquivos versionados. Não há discrepância numérica observada;
há uma lacuna na proteção contra discrepâncias futuras.

Correção sugerida: incluir um verificador M19 determinístico nas dependências
de `article-results-check` e no fluxo de CI relevante, sem reexecutar benchmarks.

### 4. Prioridade média: paginação e documentação de submissão discordam

A compilação atual tem **18 páginas**. [paper/README.md](../../paper/README.md)
informa 16, e [o plano de páginas](../article/M13_RESULTS_AND_PAGE_BUDGET.md)
registra um limite institucional de 10–16, incluindo referências.
Não verifiquei um regulamento externo da instituição; é necessário resolver
qual limite vale para esta entrega. Se o limite registrado continuar vigente,
o PDF atual o excede em duas páginas.

O teste `test_t1258_article_budget.py` verifica texto do planejamento, não
o número de páginas compiladas. Outros testes de documentação chegam a
exigir uma data antiga de pesquisa bibliográfica e uma justificativa literal
sobre ultrapassar 16 páginas. Eles protegem registros históricos, mas não
validam a situação atual nem a correção científica do conteúdo.

Correção sugerida: distinguir registros históricos de documentação corrente;
medir a paginação no gate de submissão, quando o limite vigente estiver definido.

### 5. Prioridade científica: discutir antecedentes mais próximos da redução

O artigo reconhece CKY, interseção CFG–regular e semirings. Ainda assim, faltam
antecedentes diretamente ligados à construção ponderada e às transições vazias:

- [Nederhof e Satta, *Probabilistic Parsing as Intersection* (2003)](https://aclanthology.org/W03-3016/): extensão ponderada da interseção entre gramática e autômato.
- [Hanneforth, *A Practical Algorithm for Intersecting Weighted Context-free Grammars with Finite-State Automata* (2011)](https://aclanthology.org/W11-4408/): algoritmo prático para essa combinação.
- [Pasti et al., *On the Intersection of Context-Free and Regular Languages* (2023)](https://arxiv.org/abs/2209.06809): generalização com arcos epsilon e preservação da estrutura dos caminhos.
- [Saha, *Language Edit Distance & Scored Parsing*](https://arxiv.org/abs/1411.7315): ligação com parsing com custos e distância a uma linguagem.

Esses trabalhos não demonstram, por si, que já exista exatamente a integração
MWPC aqui implementada. Eles tornam inadequado apresentar a inferência
ponderada sobre CFG e autômato, isoladamente, como um novo princípio algorítmico.
As referências foram consultadas em fontes primárias nesta revisão.

Também convém mencionar [CLAD](https://arxiv.org/abs/2605.29607) no corpo do texto:
ele já formula seleção de peso máximo para compromisso paralelo, mas a
compatibilidade vem de conflitos derivados de atenção, não de uma conclusão
CFG-válida. O repositório já o registra na busca bibliográfica; falta explicitar
essa distinção ao leitor do artigo.

## Correção matemática e de implementação

O contrato usado na revisão foi: pesos finitos não negativos; ótimo somente
no suporte declarado; preservação de posições fixas e slots físicos; distinção
entre inviabilidade, timeout e erro; recuperação de todos os matches positivos;
testemunha, proveniência e objetivo verificáveis; nenhuma promessa sobre a
trajetória futura do modelo.

Não encontrei falha na prova da equivalência central sob essas hipóteses.
Cada subconjunto compatível admite uma testemunha; com pesos não negativos,
incluir todos os matches positivos dessa testemunha não reduz a recompensa.
A maximização sobre completamentos cobre, portanto, o valor de todos os
subconjuntos compatíveis. A hipótese de não negatividade tem função real.

A recorrência CKY e sua extensão a pares de estados topologicamente ordenados
são coerentes. A saturação epsilon mantém um representante ótimo entre
extremos fixos, e há tratamento separado do caminho inteiramente vazio.
Ambiguidade da gramática não multiplica recompensa em max-plus com produções
neutras. A prova de terminação é condicional a progresso e viabilidade em cada
passo; ela não promete concluir dentro de um orçamento fixo de 16 forwards.

No código examinado, são pontos fortes:

- implementação Python e Rust independente do núcleo de otimização;
- comparação exata de somas binary64, preservando termos antes do arredondamento;
- ByteLevel composicional, sem confundir `decode` isolado com bytes do token;
- tratamento explícito de EOS/PAD, inclusive conteúdo vazio;
- validação externa ao parser, suporte congelado e autoridade de commit ligada à entrada;
- preservação do EPIC e de suas licenças/proveniência;
- testes com enumeração, posições fixas, duplicatas de escolhas, empates e controles de recurso.

Um certificado de testemunha prova validade e permite recomputar o score;
sozinho, ele não prova que não existe solução melhor. A garantia de ótimo
depende da programação dinâmica e das suas hipóteses. Os oráculos fornecem
evidência independente nos casos pequenos, não uma prova formal de todo o código.

A cobertura é forte para o escopo ensaiado. Não autoriza declarar o software
livre de bugs, suportar qualquer tokenizer/lexer, ou prometer escalabilidade
para código de tamanho industrial. Por exemplo, o normalizador enumera
subconjuntos de símbolos anuláveis antes de binarizar
(`reference/normalization.py:387`), com risco exponencial no tamanho de uma
produção. O artigo exclui essa etapa da cota do parser; essa exclusão deve ser
mantida em qualquer apresentação de complexidade do sistema completo.

## Contribuição científica e utilidade

Uma forma útil de delimitar a novidade é escrever, para um conjunto fixo C:

```text
R(y) = soma_j w_j * 1[y_i_j = t_j]
D(y) = soma_j w_j * 1[y_i_j != t_j]
R(y) + D(y) = soma_j w_j
```

Logo, maximizar os matches equivale a minimizar violações ponderadas. Com
uma proposta por posição, isso tem a estrutura de uma distância de Hamming
ponderada à linguagem, restrita ao suporte e às posições fixas. Essa é uma
dedução da definição do próprio TCC, não uma descoberta bibliográfica de
que o projeto inteiro já havia sido publicado.

A contribuição defensável é a formulação específica para o passo de um dLLM,
a construção finita que mantém identidade dos tokens e recompensa correta,
a integração com EOS/PAD e o estudo reproduzível de benefícios e limites.
O teorema principal é simples; os cuidados de representação e implementação
são a parte mais substancial. Na minha avaliação, isso sustenta um TCC de
graduação. Para uma publicação com exigência de forte novidade algorítmica
ou superioridade prática, a contribuição atual seria mais vulnerável.

[EPIC](https://arxiv.org/html/2606.00722v1) usa seleção relaxada, validação e
fallback; o projeto realmente oferece um ótimo para o problema finito
representado. Isso não demonstra uma substituição superior de todo o EPIC:
as semânticas de suporte, os custos e os caminhos de integração diferem.
Não encontrei na busca direcionada um trabalho idêntico em todas essas
especificações, mas ausência em uma busca não certifica prioridade mundial.

Usos já sustentados: referência exata para medir a perda de heurísticas;
geração de testemunhas de compatibilidade em problemas finitos; seleção
simultânea de lotes sob o objetivo declarado. O benchmark M19 demonstra
economia de tempo desse componente para lotes maiores frente ao guloso
avaliado. Uso em reparo de saídas estruturadas ou como componente de um sistema
interativo é plausível, mas exigiria sua própria avaliação.

O objetivo de somar probabilidades de propostas não equivale à probabilidade
conjunta da sequência nem à satisfação do prompt. Recompensas EOS/PAD podem
dominar os totais. Portanto, há utilidade técnica real, mas ainda não foi
demonstrada utilidade superior para o usuário final de um gerador de código/JSON.

## O que os experimentos efetivamente mostram

Reproduzi a análise M19 dos arquivos versionados: 1.944 chamadas,
540 resultados viáveis e 108 inviáveis por método, sem timeout/erro.
Contra o guloso que reaproveita testemunhas, as medianas das razões pareadas
tempo-guloso/tempo-exato variam conforme K:

| Orçamento máximo de propostas | Razão pareada | Interpretação |
| --- | --- | --- |
| 2 | 0,96–1,00 | Sem vantagem clara do exato |
| 8 | 1,71–2,05 | Exato mais rápido neste componente e benchmark |
| 32 | 2,35–3,82 | Exato mais rápido neste componente e benchmark |

Não são speedups da geração completa. Os tempos excluem inferência e extração
top-K; o comparador não é EPIC nem um parser booleano incremental. Estados,
larguras e repetições compartilham 12 prompts e não são amostras independentes.

O único estado/largura/orçamento com ganho de objetivo tem oito contra sete
matches de conteúdo, mais os mesmos 23 EOS/PAD em cada método. Ambas as
testemunhas falham no prompt. A análise regenerada mantém zero testemunhas
funcionalmente corretas entre as 540 viáveis de cada método. Isso não equivale
a executar 540 novas gerações completas.

Na confirmação ao vivo arquivada, com 12 tarefas e duas repetições:

| Família | Tempo mediano exact / serial / EPIC | Sucessos funcionais exact / serial / EPIC |
| --- | --- | --- |
| Aritmética | 3,44 / 1,19 / 1,24 s | 0 / 0 / 0 em 8 tentativas |
| Colchetes/parênteses | 3,13 / 0,97 / 1,02 s | 0 / 0 / 0 em 8 tentativas |
| JSON | 5,09 / 1,32 / 1,37 s | 0 / 2 / 2 em 8 tentativas |

O exato conclui 8/24 tentativas e acerta funcionalmente 0/24; serial e EPIC
concluem 10/24 e acertam 2/24, correspondendo a uma tarefa JSON repetida.
Os tempos incluem saídas incompletas. São resultados descritivos pequenos,
não uma estimativa universal. Ainda assim, na configuração efetivamente
ensaiada, o resultado prático é desfavorável ao exato.

## Avaliação do artigo

O texto é organizado, define o problema, fornece um exemplo útil e expõe
as limitações com honestidade. Resumo e conclusão atuais não escondem os
resultados negativos. A distinção entre exatidão local e qualidade global
é adequada. Não encontrei placeholders ativos no corpo.

Compilei uma cópia temporária do artigo e examinei visualmente as 18 páginas
renderizadas. Não observei cortes ou sobreposições; o log final não tem
overfull boxes nem citações/referências indefinidas. Há dois avisos de
`Underfull \\vbox`, sem defeito visual grave observado.

A apresentação ainda carrega a história do projeto: resultados históricos
pequenos e confusões já corrigidas recebem espaço considerável antes da
evidência atual mais informativa. Eu condensaria a exposição clássica de CKY
e os experimentos literais antigos, usando o espaço para antecedentes diretos,
uma tabela curta M19 com tempos absolutos e uma discussão causal da falha
end-to-end. Os algoritmos flutuantes interrompem algumas provas; aproximá-los
dos parágrafos relevantes melhoraria a leitura.

Uma frase de contribuição apropriada seria: “Formulamos e implementamos
seleção exata por etapa de propostas compatíveis com CFGs em suportes finitos
tokenizados, com certificados verificáveis, e avaliamos quando sua melhoria
local se traduz — ou não — em benefício de decodificação.”

## Verificações executadas nesta revisão

| Comando/verificação | Resultado observado |
| --- | --- |
| `.venv/bin/python -m pytest -q` | 842 passaram |
| `make check` | Upstream, Ruff e MyPy passaram; 14 unitários + 808 exact-commit |
| `make test-rust-parser` | 21 testes unitários + 3 aleatórios; fmt e Clippy passaram, incluindo binding |
| `make test-upstream` | 406 passaram, 8 skips preexistentes, 2 avisos de depreciação de parametrização |
| `make test-m5-differential` | 500 normais + 2.000 estendidos; zero falhas |
| `make test-m6-differential` | 500 normais + 2.000 estendidos; zero falhas |
| `make test-m7-differential` | 500 normais + 2.000 estendidos; zero falhas |
| `make article-results-check final-artifacts-check` | Derivados M13/M17/T1203 conferem |
| Regeneração manual M19, JSON e LaTeX, seguida de `cmp` | Ambos idênticos aos versionados |
| `make release-wheel-smoke` | Wheel e sdist construídos; instalação isolada, Q3 e gerador passaram, sem import do checkout |
| `make -C <cópia temporária de paper>` + Poppler | PDF de 18 páginas; revisão visual descrita acima |
| Reprodutor de prazo guloso | Falha confirmada em Python e Rust, saída 1 esperada |

Os 7.500 casos das campanhas são casos configurados/gerados, não tarefas reais.
M7 usa seu oráculo/interpretação EOS e solver Python; M5/M6 exercitam também
a implementação Rust. Não somei esses números como se fossem medições
independentes de desempenho ou evidência de 100% de correção universal.

Comandos da verificação M19:

```bash
.venv/bin/python -m scripts.exact_commit.run_review_offline \
  --analyze-directory docs/artifacts/raw/m19_selection_audit_v1 \
  > /tmp/tcc-review-m19-summary.json
.venv/bin/python -m scripts.exact_commit.run_review_offline \
  --analyze-directory docs/artifacts/raw/m19_selection_audit_v1 --latex \
  > /tmp/tcc-review-m19-values.tex
cmp paper/generated/m19_selection_audit_v1/summary.json /tmp/tcc-review-m19-summary.json
cmp paper/generated/m19_selection_audit_v1/audit-values.tex /tmp/tcc-review-m19-values.tex
```

Não repeti inferência GPU, não treinei modelos, não rodei uma instalação completa
do zero com downloads e não executei uma revisão sistemática de toda a literatura.
A revisão usa leitura do núcleo e fronteiras relevantes, testes locais,
provas do manuscrito, regeneração de evidências e consulta direcionada a fontes
primárias. Não equivale a verificação formal de cada linha do repositório.

## Ordem recomendada de fechamento

1. Corrigir o prazo final do comparador e acrescentar a regressão mínima.
2. Ligar M19 ao gate do artigo e alinhar fonte, PDF, evidências e instruções de entrega.
3. Resolver o limite de páginas e acrescentar os antecedentes mais próximos.
4. Dar maior destaque à contribuição de formulação/implementação e ao resultado
   negativo end-to-end. Nenhuma mudança dos dados é necessária para isso.
5. Se o objetivo passar a ser demonstrar uso prático superior, congelar um novo
   experimento com tarefa útil e métrica funcional, orçamento pareado, lotes
   maiores e contabilidade de custo total. Tratar melhoria como hipótese;
   não escolher somente os casos em que o exato vence.
