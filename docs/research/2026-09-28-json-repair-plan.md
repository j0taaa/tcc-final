# Plano de quatro semanas: reparo certificado de JSON com preservação de dados

Decisão de 28/09/2026. **Proposta de pesquisa, ainda sem implementação ou resultados de reparo.**
Prazo relativo: 28 dias de trabalho, reservando os dias 29–30 para contingências.
Os resultados atuais de geração continuam válidos e não serão substituídos.

## Escolha e pergunta científica

Priorizar um pós-processador que recebe um rascunho de JSON, um esquema restrito
e trechos que não podem mudar; devolve uma correção válida e um certificado de
custo mínimo **sobre as alternativas de tokens representadas**, ou um status
explícito de falha. Aplicação: exportação de registros de atendimento/pedidos para
uma API, preservando identificadores, nomes e quantidades fornecidos pelo usuário.
Exemplo de entrada: um registro com valores corretos, porém aspas, delimitadores
ou separadores errados. Não há promessa de recuperar informação ausente ou de
corrigir fatos errados.

Pergunta: **sob o mesmo orçamento e informação, a seleção exata recupera mais
registros estruturalmente válidos e semanticamente corretos, preservando campos
protegidos, do que reparos simples; e evita uma nova inferência do modelo?**

A escolha alinha a função objetivo ao uso: preservar o rascunho passa a ser um
objetivo verificável de reparo. No experimento atual, maximizar propostas por
passo não implica satisfazer o prompt. Não insistiremos em provar aceleração
geral da geração, nem treinaremos outro modelo neste mês.

## Contribuição defensável e trabalhos anteriores

Não reivindicar invenção de parsing ponderado, interseção CFG–autômato, reparo de
JSON ou distância de edição. Os antecedentes incluem
[Nederhof e Satta (2003)](https://aclanthology.org/W03-3016/),
[Hanneforth (2011)](https://aclanthology.org/W11-4408/),
[Pasti et al. (2023)](https://aclanthology.org/2023.eacl-main.52/) e
[Language Edit Distance & Scored Parsing](https://arxiv.org/abs/1411.7315).
O [json_repair](https://github.com/mangiucugna/json_repair) é um concorrente
prático obrigatório, não uma comparação opcional.

Contribuições pretendidas:

1. Adaptar e verificar o solver existente para reparo com tokens de subpalavras,
   suporte finito declarado e trechos protegidos, produzindo certificado auditável.
2. Produzir uma avaliação pareada e reproduzível que separe validade, preservação,
   correção semântica, cobertura e custo. Disponibilizar entradas, falhas e checkers.
3. Identificar em quais classes de erro a otimização exata acrescenta utilidade a
   um reparador barato, incluindo o custo de abstenção/encaminhamento ao modelo.

A novidade é incremental e aplicada; a força vem da combinação especificada e da
comparação que a isola. Na semana 1, complementar a revisão de reparo com restrições
e preservação de dados. Se já existir a mesma combinação, reposicionar como
replicação/extensão empírica; não alegar prioridade sem evidência.

Título de trabalho, a adotar no artigo somente após implementação e avaliação:
**Reparo certificado de saídas JSON de modelos de linguagem com preservação de
campos e otimização exata em suporte finito.** A formulação MWPC permanece como
base técnica; o artigo atual continua descrevendo o que já foi executado.

## Contrato técnico e escopo mínimo

Entrada: sequência de tokens rascunho d, slots finitos, suporte S_i em cada slot,
CFG de bytes, pesos positivos e máscara de posições protegidas. Todas as posições
não protegidas são variáveis, com uma proposta original (i, d_i, w_i) por slot.
A função é maximizar soma_i w_i [y_i = d_i]. Como a soma dos pesos é constante,
isso equivale a minimizar soma_i w_i [y_i != d_i] entre completamentos factíveis.
Uma proposta ausente do suporte contribui um custo inevitável; registrar isso,
nunca esconder a perda de cobertura. Produção: incluir o token original no suporte.

Este é custo de **substituição ponderada em slots**, não distância de Levenshtein
nem reparo mínimo entre todas as strings JSON. Preservar o contrato EOS/PAD do
solver. Não inserir silenciosamente epsilon para simular remoção de tokens de
conteúdo. A primeira versão não suporta edição arbitrária de comprimento.
Reservas de sufixo só podem usar a semântica EOS/PAD existente e devem constar da
especificação do suporte. Relatar separadamente erros fora dessa capacidade.

Trechos protegidos vêm do chamador ou de correspondência literal determinística
com o texto de origem, nunca do gabarito oculto. Congelar todos os tokens que
intersectam cada trecho; um token pode conter também pontuação, reduzindo cobertura.
Guardar a proveniência dos bytes e validar os trechos no resultado. Mostrar essa
limitação explicitamente, sem prometer preservação de campos apenas por um peso alto.
Valores não protegidos podem mudar: o checker semântico precisa detectar a mudança.

Escopo: um tokenizer/modelo já instalado; Python/Rust existentes; JSON UTF-8 com
objetos de chaves fixas, strings simples, inteiros e uma lista curta de itens.
Suportar explicitamente escapes usados; outros casos retornam UNSUPPORTED.
Começar com 32/64 slots e K=2/4; escolher uma configuração final apenas no piloto.
Gramática compartilhada entre todos os exemplos do mesmo esquema, sem literais
com as respostas específicas. Não implementar JSON Schema completo, novas
arquiteturas, novo parser, múltiplos modelos ou uma interface web.

Suporte inicial sem novas inferências: token original mais alternativas estruturais
provenientes de uma tabela determinística de substituições no texto do token,
retendo somente alternativas de um token. Logits salvos podem ser uma ablação,
com construção e custos próprios; não podem ser usados apenas pelo método exato
na comparação com greedy. Explicitar quando o tokenizador impede uma correção.

Não recompensar PAD apenas para inflar preservação: usar pesos unitários para
slots de conteúdo e zero para slots artificiais. Campos protegidos são restrições
rígidas. Uma segunda política ponderada só entra como ablação pré-especificada.
Apenas OPTIMAL validado recebe a garantia exact_on_support. TIMEOUT, INFEASIBLE_ON_SUPPORT,
UNSUPPORTED e ERROR são separados, com todos os exemplos nos denominadores.

## Dados e comparações justas

Usar registros fictícios gerados por script, sem dados pessoais nem coleta externa.
“Saídas reais” significa respostas efetivamente produzidas pelo modelo, não dados
pessoais de usuários. Dois conjuntos distintos; nunca misturá-los num único número:

- **Erros controlados:** documentos corretos com corrupção de aspas, separadores,
  delimitadores e tokens. Contém casos representáveis e não representáveis,
  ambiguidades e documentos já válidos. Mede mecanismo e limites, não prevalência
  de falhas de um modelo. Gabarito acessível somente ao avaliador.
- **Saídas reais:** gerar uma vez com o checkpoint já disponível, salvar todos os
  rascunhos, depois passar as mesmas entradas a todos os reparadores. Separar
  falha de sintaxe, esquema e semântica. Não corromper essas saídas nem escolher
  apenas as que o método consegue reparar. Manter todas as saídas válidas também.

Tamanho planejado, sujeito apenas ao piloto e congelado antes da confirmação:
40 prompts de desenvolvimento; 200 prompts distintos de confirmação com duas
seeds cada. Mais 200 documentos-base controlados com três corrupções registradas
por documento. Separar templates/fontes de documentos entre desenvolvimento e
confirmação para evitar quase duplicatas. A unidade estatística é o prompt ou
documento-base, não cada seed/corrupção. Se o piloto mostrar poucos erros reais,
relatar a baixa necessidade de reparo; não fabricar uma taxa de falha conveniente.

Comparadores obrigatórios:

1. Sem reparo: mede necessidade e regressões em entradas já corretas.
2. json_repair com versão/configuração fixadas e validação independente do esquema.
3. Reparador determinístico informado pelo esquema: correções locais sem busca
   exata, mesmas restrições e mesmas alternativas admissíveis.
4. Greedy com reutilização de testemunha, mesmo suporte, pesos, locks e orçamento:
   isola o valor da otimização exata, não o efeito de dar mais informação.
5. Uma nova tentativa do mesmo modelo: recebe o rascunho, esquema, trechos protegidos
   e diagnóstico de erro. Sem gabarito; apenas uma chamada, mesmo teto de tokens.

Todos passam pelo mesmo checker; violar um campo protegido conta como falha.
Não atribuir à CFG correção semântica. Não comparar somente contra um reparador
sem conhecimento do esquema. Registrar prompts de retry integralmente.
A política prática avaliada separadamente pode ser: validar, tentar reparo barato,
se rejeitado tentar exato, então retry. Informar custo e sucesso da cascata inteira.
Não declarar superioridade da cascata sobre um componente sem contabilizar etapas.

## Métricas, orçamento e critérios prospectivos

Primária: fração de todos os rascunhos reais que terminam válidos no esquema,
com valores esperados e todos os campos protegidos preservados. Reportar também
recuperação na coorte de rascunhos inicialmente inválidos; não trocar denominador
para anunciar ganho. Verificador independente usa parsing JSON estrito, rejeita
chaves duplicadas e compara campos/valores com o registro de origem.

Secundárias: validade sintática, conformidade de esquema, alteração indevida de
campos, regressão de entradas inicialmente corretas, cobertura do suporte, custo
de substituição, gap contra ótimo, estados do solver, latência mediana/p95,
pico de RAM e quantidade de novas chamadas ao modelo. Medir custo de construção,
parsing, validação e fallback separadamente, além do tempo total por entrada.
Sincronizar GPU nas medições, excluir carregamento do modelo e publicar ambiente.

Relatar diferenças pareadas com intervalos de 95% por bootstrap de prompts/documentos
(seeds e corrupções ficam agrupadas). Não inferir qualidade a partir de um ganho
na pontuação do solver. Não tratar timeout como inviabilidade.

Orçamento inicial do piloto: até 2 segundos de reparo total por documento, incluindo
construção/validação, e limite de processo de 2 GiB; menor prazo nativo dentro do total.
A proteção precisa cobrir também Python/FFI; matar o worker após o limite e classificar
TIMEOUT sem certificado. O orçamento pode ser reduzido no piloto, mas é congelado
antes da confirmação. Não prometer competir em latência com json_repair.

Critério prático ambicioso, ainda não medido: aumentar em pelo menos 5 pontos
percentuais o sucesso semântico sobre o melhor reparador sem nova inferência na
coorte inválida, sem regressões nas entradas corretas nem violações protegidas.
Publicar incerteza, mesmo se o intervalo incluir zero. Comparar qualidade com retry
e custo total; só afirmar vantagem sobre retry quando os dados a sustentarem.
O ganho mínimo e a coorte são fixados antes da confirmação, sem escolher após os dados.

Ablações pequenas: exato versus greedy no mesmo suporte; com/sem proteção; suporte
estrutural versus logits salvos (apenas se já disponíveis). Analisar por classe de
erro e tamanho, sem promover uma classe escolhida após o teste como resultado principal.

## Calendário e pontos de decisão

| Período | Entrega concreta | Critério para avançar |
|---|---|---|
| Dias 1–3 | Adaptador de reparo, prova da equivalência de custo, checker, oráculo pequeno e regressões | Certificados válidos, custo ótimo contra enumeração, campos preservados; baselines existentes passando |
| Dias 4–7 | Piloto com 40 prompts e corpus controlado; cinco comparadores mínimos; revisão de reparo | Pelo menos dez recuperações semanticamente corretas no piloto controlado, custo dentro do teto e vantagem identificável em casos onde reparo barato falha; relatar separadamente a evidência real |
| Dias 8–14 | Corrigir somente mecanismos diagnosticados no piloto; congelar dados, configs e análise; ensaio de reprodução | Suporte suficiente para testar a hipótese; definir antes da confirmação os limiares, pesos e protocolos finais |
| Dias 15–21 | Uma campanha de confirmação, ablações e análise automática; reexecução de correções de bugs preserva dados antigos | Todas as entradas contabilizadas, nenhuma divergência de oráculo/certificado, tabelas saem dos dados brutos |
| Dias 22–28 | Artigo, figuras, pacote reproduzível, demonstração curta e ensaio de defesa | Argumento e limitações sustentados pelos dados; revisão do orientador; PDF no limite institucional |

Reservar cerca de 20–25 horas semanais, com a última semana sem novas funcionalidades.
Se houver menos disponibilidade, reduzir tamanho do estudo antes de congelá-lo;
não sacrificar os comparadores fortes nem a correção do solver.

**Regra de parada no dia 7:** se os erros dominantes exigirem inserção/remoção
arbitrária ou inferência semântica, não construir outro sistema durante o mês.
Concentrar a contribuição no reparo limitado que pode ser certificado e no conjunto
controlado, explicando o limite de validade externa. Se nem aí houver vantagem
sobre o reparador informado pelo esquema, encerrar a alegação de utilidade nova e
levar imediatamente o diagnóstico ao orientador. Não gastar três semanas tentando
obter um número favorável. Nenhum plano honesto pode garantir de antemão uma
superioridade experimental.

## Evidência e entregáveis

Criar um novo marco M21 antes da implementação, dependente dos gates M20. Versionar
as configurações antes das medições. Cada JSONL registra commit limpo, seed, revisões
do modelo/tokenizer, hashes do esquema/entrada/suporte, política de proteção, status,
certificado quando aplicável, hardware, versões e tempos. Raw imutável separado de
análise. Dependências novas só se necessárias, com lock e justificativa.

Arquivos pretendidos: módulo independente `src/mwpc_exact/repair.py`, testes em
`tests/exact_commit/`, um runner reutilizando infraestrutura atual, configurações
em `configs/experiments/`, dados e análise nos diretórios existentes. Não criar
outra camada genérica de experimentação. Saídas finais: biblioteca/CLI simples,
corpus/checkers, três tabelas geradas (qualidade, preservação/cobertura, custo),
um caso explicado com certificado e pacote reproduzível.

O artigo deve separar claramente: teorema e corretude do otimizador; mecanismo do
reparo; resultados controlados; resultados reais; limites. Os resultados anteriores
negativos explicam a mudança de pergunta e permanecem acessíveis. Uma demonstração
bem-sucedida ilustra o método, mas não substitui o experimento comparativo.
