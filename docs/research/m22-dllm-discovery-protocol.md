# M22: procurar benefício dentro da geração por dLLM

Este é um protocolo exploratório. O reparo externo M21 fica como aplicação
auxiliar; não é evidência de ganho da dLLM. Nenhum resultado positivo é pressuposto.

## Contrato

O LLaDA-8B-Instruct quantizado em NF4 executa cada forward. A seleção recebe suas
probabilidades sobre o vocabulário completo. Gramática, suporte, orçamento de
propostas, ordem de confiança e regra de progresso são comuns aos métodos.
Nenhum seletor recebe a resposta esperada. O objetivo continua sendo MWPC por
etapa no suporte declarado, nunca otimalidade da trajetória ou da semântica.

## Triagem v1

O domínio é despacho para calculadora: `add(a,b)`, `sub(a,b)`, `mul(a,b)`,
`neg(a)` e `abs(a)`, com argumentos de 0 a 9. O catálogo de 320 saídas é fixo
antes dos prompts e contém todas as chamadas desse domínio. O modelo precisa
escolher operação e argumentos; não se pede que calcule o resultado.

O suporte contém as tokenizações canônicas dessas saídas, completadas com EOS
até 16 posições. É uma linguagem regular finita: esta triagem não demonstra uma
vantagem própria de CFGs recursivas. Não representa todas as tokenizações ou
variações de espaços da mesma chamada. Cada posição propõe o token de maior
logit na união de tokens do catálogo nessa posição; não há filtragem pela
resposta do prompt. Os pesos são probabilidades não renormalizadas do modelo.

Comparam-se enumeração exata dos caminhos e seleção gulosa por confiança com
viabilidade no mesmo catálogo. Não são EPIC nem tempos do parser Rust. Orçamentos
4 e 16, 24 pedidos gerados com seed 220001, limite de 16 forwards e 120 segundos.
O mesmo protocolo pode ser ampliado somente com configurações novas, preservando
os resultados anteriores. Configuração: `configs/experiments/m22_tool_screen_v1.json`.

Ambos fixam as propostas aceitas, e usam uma posição da testemunha como fallback
explicitamente separado se nenhuma proposta casar. Posições fixas nunca mudam.
Não se aplica reparo ao resultado final. EOS conta na pontuação, mas o registro
distingue commits ordinários para detectar ganhos que sejam só preenchimento.

Cada trajetória salva propostas, probabilidades, canvas, testemunha, objetivos
dos dois seletores no mesmo estado, progresso e componentes de tempo. O contraste
na mesma trajetória é diagnóstico; resultados de geração comparam trajetórias
independentes. Tempo diagnóstico é registrado separadamente. Há dois forwards
de aquecimento; carregamento do modelo é excluído; CUDA é sincronizada. A ordem
dos métodos alterna por pedido. A resposta esperada só entra no avaliador final.

Critério de descoberta: uma diferença favorável em resposta funcional ou número
de forwards com resposta igualmente correta. Pontuação maior sozinha não conta.
Relatar também perdas, empates e totais de todos os pedidos. Um caso escolhido
após observação é um exemplo exploratório, não confirmação estatística.

## Depois da triagem

Se houver sinal, reproduzir a decisão com parser de produção e validação
independente, congelar pedidos novos antes de medir, e comparar serial/EPIC
quando suas interfaces e contratos forem compatíveis. Incluir custo integral
do parser: tempo do enumerador não demonstra aceleração do sistema existente.
Se não houver sinal, examinar rastros e testar uma hipótese nova em configuração
separada, sem apagar a tentativa malsucedida.

Uma referência próxima encontrada nesta busca é
[Dang e Ermon, julho de 2026](https://arxiv.org/abs/2607.07026), sobre inferência
constrangida por autômatos em dLLMs, incluindo chamadas de funções. Ela sustenta
a relevância da tarefa, mas também impede alegar novidade da ideia geral de
inferência exata estruturada para dLLMs. Seu objetivo probabilístico difere da
seleção de propostas MWPC.

Execução opt-in, com pesos previamente em cache e código/configuração congelados:

```bash
.venv-live/bin/python scripts/exact_commit/run_tool_screen.py \
  --config configs/experiments/m22_tool_screen_v1.json
```

## Extensão exploratória v2: chamadas aninhadas

Após v1 não mostrar diferença funcional (ambos 24/24 em cada orçamento), v2
mantém o protocolo e amplia a dependência estrutural: 1.512 chamadas legais
com no máximo uma chamada aninhada, literais 0..3, 24 slots, orçamentos 8/24,
30 pedidos, seed 220002. A instrução pede preservar operações e explicita a
ordem dos argumentos. Não é uma coorte confirmatória: domínio e configuração
foram escolhidos após v1. Configuração nova, resultados anteriores preservados.

## Extensão exploratória v3: propostas amostradas

V2 terminou sem diferenças de objetivo ou resultado entre seletores. V3 testa
uma hipótese diferente: conflitos entre propostas amostradas, em vez de argmax.
Mesma linguagem de v2, temperatura 1, 60 pedidos novos (seed 220003), orçamento
24. Amostragem categórica via Gumbel dentro de cada domínio posicional, com
pesos ainda iguais às probabilidades originais sobre o vocabulário completo.
Métodos usam os mesmos números aleatórios em cada passo/posição. Trata-se de
uma condição estocástica legítima, mas escolhida depois dos resultados neutros;
qualquer vantagem ainda exige confirmação separada e comparação com temperatura 0.

## Extensão exploratória v4: preservação de operandos durante a geração

V3 produziu diferenças de pontuação, mas não melhoria de acerto ou de forwards
em respostas corretas. V4 testa geração de programas que preservam exatamente
as ocorrências de operandos fornecidas pelo usuário. O catálogo é filtrado pelo
multiconjunto de dígitos do pedido, sem ler a resposta esperada, operação ou
ordem corretas. Ainda há múltiplos programas possíveis em cada tarefa. Isso é
uma restrição de conteúdo da tarefa, além da sintaxe, aplicada igualmente aos
dois métodos dentro da geração. O número de candidatos ativos fica registrado
por índices no catálogo comum. Temperatura 0, seed 220004, 60 pedidos novos,
orçamento 24; permanece exploratório. Não alegar equivalência com uma gramática
JSON genérica nem novidade da otimização sob restrições de inventário.

## Confirmação com parser de produção v1

V4 encontrou uma vitória e uma derrota de acerto do exato. O estado inicial da
vitória (pedido `nested-220004-56`) também foi checado pelo parser Rust: ele
escolhe `sub(mul(2,1),1)`, enquanto a viabilidade gulosa com reutilização de
witness escolhe `sub(sub(2,1),1)`. Isso é motivação para confirmar, não uma
estimativa de ganho médio.

A configuração `m22_tool_parser_confirmation_v1.json` congela 100 pedidos únicos
não presentes nas três coortes aninhadas anteriores. São novas combinações de
operandos/operações, mas compartilham templates e domínio pequeno. Nenhuma
alegação de generalização para novos templates, modelos ou tarefas é autorizada.

Agora ambos usam o parser de produção Rust com bytes e validação independente,
inclusive o guloso com reutilização de testemunha. A linguagem é uma CFG
compilada do catálogo filtrado apenas pelos operandos do pedido. O suporte é o
produto dos domínios posicionais intersectado com essa linguagem e com slots
EOS finitos. **Pode conter tokenizações alternativas**; não é o mesmo suporte
canônico mais estreito da triagem. A garantia é `exact_on_support` para esse
novo contrato comum. Gramática e tokens têm seus dados salvos; a compilação
por pedido tem tempo separado, que deve entrar na avaliação de latência total.

Métrica primária: chamada final exatamente pedida. Métricas secundárias:
forwards e tempo em pares que ambos acertaram, e taxa de sucesso por unidade de
tempo incluindo todos os pedidos. O contrafactual no mesmo estado é diagnóstico;
não entra no tempo de execução do método. Não chamar esse comparador de EPIC:
é seleção gulosa com viabilidade exata no mesmo suporte e mesma gramática.
O resultado total da coorte e todos os casos contrários devem ser publicados.

Os metadados globais de v4 nomeiam a cardinalidade do catálogo-base; os índices
`active_catalog_indices` em cada linha especificam o suporte ativo menor. A
versão de confirmação explicita o contrato ativo no campo `exactness_scope`.
Isso não muda o algoritmo ou os resultados de v4; evita interpretar o ótimo
como se tivesse sido calculado sobre o catálogo-base inteiro.

## Repetição de tempo

A confirmação observou 65/100 acertos do exato e 63/100 do guloso, com o mesmo
número total de forwards. Antes de concluir sobre latência, repetir os mesmos
100 pedidos com ordem inicial dos métodos invertida. Configuração nova
`m22_tool_parser_repeat_v1.json`; não é uma nova amostra de 100 tarefas. Usar a
mediana das duas execuções por pedido/método antes de agregar. Não interpretar
as duas vitórias de acerto como significância estatística populacional.
