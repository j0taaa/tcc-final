# M25 — Consultas externas com argumentos fundamentados no pedido

Data: 2026-09-29. Continuação de M24, autorizada pelo usuário. Slides, roteiro e
apresentação foram retirados do escopo a pedido do usuário.

A contribuição é seleção paralela certificada na dLLM e avaliação de políticas
de compromisso. Confiança, max-marginais e parsing ponderado são antecedentes,
não invenções deste trabalho. Não condicionar publicação a resultado positivo.

## Elegibilidade antes da inferência

Auditar os mesmos 658 registros públicos BFCL fixados em
`6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`. Uma função, de um a três parâmetros,
tipos escalares string/integer/number/float/boolean, exatamente um campo string
sem enum, e nome contendo weather/forecast/search/find/get/lookup/query/check/
retrieve/fetch. São nomes de consultas; não executar funções remotas do benchmark.
Todos os casos elegíveis entram na auditoria, inclusive suporte ausente, excesso
de tamanho, falha ou timeout. Oito casos de M24 não têm campo livre e ficam fora.
A regra identifica 68 casos; contagem e IDs serão gerados por script.

Separar por nome de função casefold. Ordenar famílias por SHA256 do prefixo
`m25-250929:` seguido do nome. As primeiras oito famílias são desenvolvimento;
todas as outras são confirmação. Nenhuma inferência ou taxa de acertos determina
esse split. Ele separa nomes, não garante disjunção de todos os domínios semânticos.

## Suporte sem resposta esperada

Argumentos enum/boolean preservam o esquema. O campo de texto livre recebe valores
de trechos contíguos do pedido (até seis palavras), formas preservadas e minúsculas,
trechos entre aspas, nomes capitalizados e defaults declarados no esquema.
Reter no máximo 96 candidatos com ordenação determinística documentada. Números
vêm do pedido, números escritos zero a vinte e defaults; usar 0–10 somente quando
não houver número disponível. Propriedades opcionais permitem omissão.
Limite declarado de 4.096 chamadas e 64 slots; valores/strings que não couberem
não podem desaparecer da contagem de cobertura. A representação byte-CFG pode
aceitar outras tokenizações dos mesmos textos no produto dos domínios posicionais.

O gabarito só entra no avaliador e na auditoria posterior de cobertura. Não
reduzir domínios aos valores certos, nem remover casos porque o gabarito ficou
fora. O recorte continua finito e não cobre strings arbitrárias do vocabulário.
A comparação MAP canônica permanece obrigatória quando a enumeração cabe.

## Experimento congelado

LLaDA-8B-Instruct, revisão e NF4 de M24, uma GPU e um thread CPU. Começar com um
smoke pequeno de desenvolvimento, depois o piloto completo. Comparar confiança
MWPC 0,8; MWPC orçamento quatro; MWPC orçamento amplo; guloso com confiança 0,8;
EPIC lexical 8/32/64 incluindo recuperação; MAP canônico com orçamento 8/64.
O piloto pode revelar incompatibilidade de engenharia ou custo proibitivo; qualquer
alteração exige nova configuração e preservação da execução anterior. Selecionar
no máximo duas políticas MWPC pela fronteira de acurácia/tempo no desenvolvimento,
antes de abrir resultados de confirmação. Manter os controles fortes mesmo que
ganhem. O EPIC usa vocabulário nativo e a mesma linguagem declarada, com espaços
lexicais; a avaliação normalizada de espaços será uma métrica secundária declarada.

Comparação primária inicial: MWPC confiança 0,8 contra EPIC 32. Reportar diferença
de acurácia pareada, intervalo conservador, razão de latências por pedido,
forwards, validade, tamanho/cobertura do suporte, timeouts e falhas. Não assumir
não inferioridade com esta amostra pequena; não reutilizar a confirmação para
ajustar parâmetros. Repetir com ordem invertida e agregar tempos por pedido.

A tarefa é avaliação de chamadas únicas escalares com avaliador próprio explícito,
não score BFCL oficial. Não afirmar ganho em expressividade CFG com base numa
linguagem finita. Resultados M24 e M25 têm suportes e tarefas diferentes e serão
reportados separadamente.

## Entregas

Demonstração de consulta geográfica somente de leitura, com chamada gerada pela
dLLM, validada e despachada por allowlist. Manter replay reproduzível separado de
inferência ao vivo e respostas de rede com data e origem. Atualizar artigo e
resumo em português a partir dos artefatos; manter autoria, modelo SBC e limite
de páginas. Entregar código, comandos, PDF verificado e pacote local de evidências.

## Correção de engenharia antes do piloto completo

O smoke v1 foi interrompido após quatro das dezoito células: `re.escape`
produzia escapes de espaços incompatíveis com a biblioteca de regex do EPIC.
A execução parcial e o diagnóstico ficam em
`docs/artifacts/raw/m25_grounded_v1/interrupted_smoke/`. A correção está na
conversão local de literais, sem modificar o EPIC ou a linguagem permitida.
Regressões cobrem espaços, Unicode e metacaracteres; compilação CPU dos 68
suportes passou. Suíte completa após a correção: 1.123 testes; Ruff e MyPy
(87 arquivos) passaram. O smoke v2 repete os mesmos casos e políticas.

## Retomada auditável do desenvolvimento

O processo de desenvolvimento foi interrompido entre registros após 127/234
células, sem exceção registrada. A causa exata do encerramento é desconhecida.
O prefixo original fica em `interrupted_development`, com manifest e diagnóstico;
é um snapshot dos mesmos registros, não uma segunda amostra. A retomada aceita
somente um prefixo íntegro da ordem congelada, configuração/suporte idênticos e
mesmas revisões, versões e GPU. Ela não repete células já concluídas. Cada sessão
registra seu commit, início, número de células anteriores e reinicialização da
semente; escolhas de recuperação do EPIC continuam podendo variar entre processos.
Não há seleção de políticas a partir de resultados de confirmação.
