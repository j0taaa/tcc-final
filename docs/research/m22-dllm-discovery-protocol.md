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
