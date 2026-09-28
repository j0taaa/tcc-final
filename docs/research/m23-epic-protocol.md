# M23 — comparação com EPIC no domínio M22

Protocolo congelado antes das medições. O pedido do usuário exige comparação
com o EPIC real; o guloso do M22 nunca deve receber esse nome.

## Contrato e coorte

Reusar integralmente os 100 pedidos M22, sem seleção por resultado. Isso é uma
comparação adicional em uma coorte já conhecida, não nova confirmação independente.
Modelo, tokenizer/revisão, NF4, GPU, prompt, preservação de operandos, 24 slots,
limite de 24 forwards e 120 s por geração são mantidos. Gabarito só no avaliador.
Piloto: cinco primeiros pedidos, sem ajuste por acurácia. Confirmação: todos os
100 pedidos, cinco métodos, ordem rotativa por tarefa; repetição em ordem inversa.

## Métodos e assimetrias

- `exact`: MWPC Rust M22, probabilidades do vocabulário completo, domínios
  posicionais e gramática byte CFG, até 24 propostas por forward, mesma conclusão
  e fallback certificado do M22.
- `epic_native_1`, `epic_native_4`: gerador LLaDA original do commit EPIC
  `5b1b31098f34ed3691d2a9f4aae14fdf5839d072`, com vocabulário nativo; respectivamente
  1 e 4 etapas programadas (24 ou 6 transferências na primeira etapa), até 100
  rejeições. Regular cover, verificação exata do lote, DFA-free checker e caches
  ativados. Reamostragem e conclusão EOS do upstream são preservadas.
- `epic_domains_1`, `epic_domains_4`: mesmo gerador, logits mascarados para os
  domínios posicionais M22. **A máscara renormaliza a confiança**, portanto é um
  controle de domínio adicional, não isolamento perfeito do seletor MWPC.

A gramática exportada contém as mesmas produções byte-CNF e reconhece as mesmas
strings, com lexemas de um byte. O símbolo inicial vem primeiro, como exige o
leitor de regular cover do upstream; `to_normal_form()` prepara o cache do parser.
Esses são cuidados de integração, sem alteração no código vendorizado.
A escolha de lexemas por byte acompanha a representação do MWPC e não demonstra
que esta seja a representação mais eficiente possível para EPIC.

O EPIC usa lacunas abstratas nas consultas de viabilidade; mesmo sua variante
com logits mascarados não tem o contrato de conclusão nos domínios finitos do
MWPC. EPIC pode tentar várias alternativas no mesmo forward e terminar em EOS
preenchendo a cauda; MWPC faz novas inferências depois de aceitar o conjunto.
Não atribuir diferenças finais exclusivamente à optimalidade de seleção.
Não há reparo posterior nem infilling externo adicionado a nenhum método.

## Instrumentação e verificações

Hooks só observam o seletor e `check_valid` originais, sem substituir decisões;
contar lotes tentados/selecionados e erros que o upstream intercepta. Registrar
eventos de canvas, rejeições, forwards reais, status, saída e correção exata da
chamada. Modelo observado sincroniza CUDA e mede forwards; tempos de seleção,
checagem serial e máscara de domínio são separados. Parsing/backtracking são
internos ao upstream e não separáveis por esses hooks. Registrar custo de setup
separado e incluí-lo no tempo total reportado; excluir carregamento/warmup e a
consulta contrafactual do MWPC. Não comparar tempos de hardware distintos.

Testes CPU anteriores ao piloto: equivalência de linguagem em domínio exaustivo,
execução efetiva do seletor de lotes original, preservação dos hooks/env e coorte.
Congelar fonte/config em commit limpo. Arquivar todos os resultados, inclusive
falhas; gerar tabelas via script com hashes e verificação semântica dos outputs.
Métrica principal: chamada exata correta. Secundárias: validade na linguagem
permitida, forwards, tempo total e pares de sucesso/derrota. Repetições não são
novas tarefas. Nenhuma superioridade é pressuposta.

## Correção de avaliação após o piloto, antes da coorte completa

O piloto de 25 gerações (commit `2067ec3`) identificou espaços e quebras de linha
legais nas chamadas EPIC. Seu registro original de igualdade textual é preservado,
mas não sustenta uma comparação funcional justa. Na coorte completa a avaliação
usa AST de chamada, sem executar código, reparar ou simplificar operações. Só
ignora whitespace aceito pelo parser e mantém a exigência de geração completa
(um MASK ocultado pelo decoder não conta como resposta). O MWPC usa o mesmo
critério, equivalente à igualdade textual para seus outputs canônicos.

Também incluir `epic_native_24` e `epic_domains_24` antes da coorte completa: têm
o mesmo teto de etapas MWPC; transferem um token por etapa, então o próprio
upstream não ativa lotes nesse schedule. São controles de maior orçamento,
explicitamente distinguíveis das execuções paralelas 1/4. Não escolher um
schedule vencedor depois de observar a coorte; relatar todos os sete métodos.
A confirmação e a repetição têm 700 gerações cada. Os cinco pedidos do piloto
continuam na coorte, sem alegação de holdout novo. A alteração não dependeu de
vantagem de acurácia; corrige o avaliador e amplia o controle de orçamento.

## Controle lexical adicional

Adicionado enquanto a primeira coorte completa ainda estava em execução, antes
de conhecer sua tabela final: três configurações EPIC de vocabulário nativo com
lexemas naturais (funções inteiras, dígitos e pontuação), 1/4/24 etapas. A gramática
é construída exclusivamente do mesmo catálogo permitido, não da resposta.
A linguagem canônica é testada contra todos os 1.512 elementos do catálogo; o
lexer upstream pode admitir whitespace, avaliado pelo mesmo AST. Manter os
resultados por bytes também, sem substituir a representação menos favorável.

Arquivos `m23_epic_lexical_{confirmation,repeat}_v1.json`: os mesmos 100 pedidos,
três EPIC + nova execução MWPC em cada rodada; 800 gerações adicionais, repetição
com ordem invertida. O MWPC é reexecutado como controle contemporâneo. Essa
sensibilidade de representação é parte da comparação, não nova evidência
independente de generalização. O leitor de regular cover recebe símbolo inicial
primeiro; o CFG normalizado tem seu cache inicializado antes da primeira consulta.

Antes das execuções lexicais, acrescentar também 2 etapas EPIC: aproxima o número
habitual de forwards do MWPC M22 (205/100). Assim são quatro EPIC + MWPC por rodada
lexical, **1.000** gerações adicionais. Isso substitui a contagem planejada de 800
acima; nenhum pedido ou resultado anterior é removido.

Métrica secundária acrescentada na análise, sem mudar a primária: executar apenas
a AST validada de calculadora e comparar o inteiro resultante. Identidade de
chamada pode penalizar expressões aritmeticamente equivalentes; relatar ambos.
Coincidência do valor não prova preservação das operações solicitadas. Nunca
usar `eval`, reparar textos ou aceitar MASKs escondidos como respostas completas.

## Fechamento obrigatório: recuperação oficial do wrapper EPIC

A comparação do gerador isolado não encerra a avaliação do EPIC: o método
`LLaDAModel` em `eval/dllm/models/llada/model.py` chama `autocomplete_valid` quando
a geração não termina. A restrição inicial deste protocolo a "sem infilling
externo" é insuficiente para representar esse fluxo completo e é corrigida aqui.
Preservar as tabelas do gerador, mas a conclusão deve considerar também **EPIC +
recuperação oficial**, sem confundir recuperação determinística com novo forward.

Reexecutar a função original sobre TODOS os estados finais incompletos arquivados,
nas duas representações e duas repetições. Mesmos lexemas/gramáticas/pedaços fixos,
sem consultar gabarito. O wrapper original e o replay usam lacunas abstratas: a
recuperação não está limitada aos domínios posicionais ou ao comprimento em slots
do MWPC. Isso deve ser explícito, inclusive para a variante domains.

Config `m23_epic_recovery_v1.json`, fonte congelada antes do replay. Testes CPU
verificam preenchimento de MASK pelos dois léxicos sem modelo nem resposta e que
saídas já completas ficam intactas. Avaliar AST, resultado numérico e preservação
dos fragmentos fixos independentemente. Guardar None, timeout e erro separadamente.

A recuperação não modifica a trajetória anterior; replay permite reaproveitar
os estados exatos sem repetir inferência. Executar após terminar a GPU. Medir
separadamente o custo de recuperação CPU, excluindo reconstruir gramática/lexer
que o wrapper já possui. Se somado ao tempo anterior, nomear **tempo reconstruído**,
não latência de pipeline medida conjuntamente. Não usar vantagens sobre o gerador
sem recuperação para afirmar superioridade sobre o EPIC completo.
