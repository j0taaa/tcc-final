# Benefício encontrado dentro da geração por dLLM

O recorte encontrado é a **geração de pequenas chamadas de funções aninhadas,
preservando os operandos do pedido**, com seleção exata durante o denoising do
LLaDA. Não há reparo posterior. O modelo é executado em todos os forwards; pesos
e revisão do tokenizer estão fixados nos artefatos.

O [relatório gerado](generated/m22-results.md) contém a comparação completa,
inclusive quatro tentativas exploratórias e os exemplos contrários. A
[configuração confirmatória](../../configs/experiments/m22_tool_parser_confirmation_v1.json)
foi congelada antes de medir seus 100 pedidos; eles não repetem as instruções
das coortes de desenvolvimento, mas compartilham os mesmos templates pequenos.

## Por que este resultado é sobre dLLMs

As alternativas são avaliadas a partir das probabilidades atuais do modelo em
várias posições mascaradas. Cada decisão muda o canvas que será visto pelo
próximo forward. Gramática, domínios, pesos e orçamento são iguais entre os
métodos, e a resposta esperada só é consultada no avaliador final. A restrição
de operandos é construída a partir do pedido do usuário, não do gabarito.

Na confirmação, o parser Rust é usado tanto pelo MWPC quanto pela viabilidade
gulosa com reutilização de testemunha. A garantia é para o objetivo por etapa
na interseção de domínios posicionais, linguagem de bytes e slots EOS finitos.
Não implica optimalidade semântica nem global sobre a trajetória.

Há dois tipos de benefício observado: geração mais rápida perante esse guloso,
e exemplos novos em que a decisão exata preserva a operação pedida. A repetição
com ordem invertida conserva os outputs e os forwards. O ganho de tempo vem de
resolver a seleção em uma consulta ponderada, evitando múltiplas consultas de
viabilidade; o número total de forwards não caiu.

## Exemplo e mecanismo a investigar

Pedido da confirmação: subtrair 1 do produto de 3 e 1.

```text
Exato:  sub(mul(3,1),1)  -> 2
Guloso: sub(sub(3,1),1)  -> 1
```

Os rastros mostram que o ótimo da primeira etapa retém uma combinação de
propostas com pontuação maior e conduz à operação correta. Isso é evidência
do mecanismo nesse caso. Uma hipótese explicativa adicional é a diferença de
segmentação BPE: `(sub` ocupa um token, enquanto `(mul` se divide em `(m` e `ul`.
Uma proposta isolada pode ser mais confiante que cada parte de uma alternativa,
mas inferior ao conjunto. Ainda falta uma ablação específica para atribuir o
ganho causalmente à segmentação, em vez de apenas à escolha do conjunto.

## O que isso autoriza defender

Contribuição aplicada: implementação e avaliação de seleção exata de propostas
de uma dLLM com restrições de linguagem e conteúdo conhecido, mostrando um
benefício delimitado de ponta a ponta diante de um seletor guloso comparável.
O domínio de programas executáveis permite verificar o efeito funcional da
operação errada, além de apenas checar sintaxe ou pontuação.

Ainda não é uma demonstração de superioridade sobre EPIC, geração livre,
enumeradores especializados ou métodos de inferência probabilística em autômatos.
Há apenas um modelo quantizado, uma GPU, poucos formatos e uma linguagem finita.
A enumeração continua especialmente competitiva em catálogos pequenos. Os dois
pares discordantes de acerto não sustentam uma alegação estatística ampla de
melhor acurácia. As derrotas da exploração e os experimentos negativos históricos
permanecem nos arquivos.

O uso proposto é compilação de pedidos para uma DSL/API com argumentos que
precisam ser preservados. A linguagem de calculadora é uma instância controlada
desse uso, não evidência de implantação ou desempenho em APIs reais. A literatura
já avalia chamadas de funções com dLLMs e inferência sob restrições:
[Dang e Ermon, 2026](https://arxiv.org/abs/2607.07026). A novidade deve ser
reivindicada na adaptação e avaliação específica de MWPC, não nessa aplicação geral.

Para o mês restante, a prioridade é comparar EPIC e um método especializado
competitivo, ampliar os pedidos para um benchmark de chamadas de funções e
testar a hipótese da tokenização em uma coorte pré-especificada. O resultado M22
é uma base positiva para essa investigação, sem garantia de que a vantagem se
mantenha fora deste recorte.

## Reprodução

Recalcular resultados e validar arquivos, caminhos, custos e respostas sem GPU:

```bash
.venv/bin/python scripts/exact_commit/summarize_tool_screen.py \
  docs/artifacts/raw/m22_dllm_discovery_v1/screen_v1 \
  docs/artifacts/raw/m22_dllm_discovery_v1/screen_v2 \
  docs/artifacts/raw/m22_dllm_discovery_v1/screen_v3 \
  docs/artifacts/raw/m22_dllm_discovery_v1/screen_v4 \
  docs/artifacts/raw/m22_dllm_discovery_v1/confirmation \
  docs/artifacts/raw/m22_dllm_discovery_v1/repeat \
  --output docs/research/generated/m22-summary.json \
  --report docs/research/generated/m22-results.md --check
```

Para repetir a inferência, usar o driver e as configurações indicados no
[protocolo](m22-dllm-discovery-protocol.md), com ambiente `.venv-live` e os pesos
em cache. Os commits produtores estão em cada linha e nos metadados arquivados;
cada diretório tem manifesto SHA-256. O PDF entregue em M21 ainda não incorpora M22.
