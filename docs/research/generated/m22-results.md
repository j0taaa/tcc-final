# M22 — Geração real por dLLM: resultados verificados

Arquivo gerado por `scripts/exact_commit/summarize_tool_screen.py`.

## Confirmação com parser Rust

LLaDA-8B-Instruct, NF4, RTX 3080 Ti; 100 pedidos únicos, duas execuções
com ordem inicial invertida. As repetições não são novas tarefas.

| Método | Acertos/100 | Forwards por execução | Mediana total por pedido |
| --- | ---: | ---: | ---: |
| greedy | 63 | 205 | 559.9 ms |
| exact | 65 | 205 | 264.6 ms |

Tempo: mediana das duas execuções por pedido/método, depois entre pedidos;
inclui inferência sincronizada, candidatos, seleção, atualização e compilação
da gramática por pedido; exclui carregar pesos, aquecimento e consulta-sombra
diagnóstica. Não equivale a latência de um serviço implantado.

Nos 63 pares que ambos acertam, a mediana da razão
tempo guloso / tempo exato é **2.13x**.

Diferenças de acerto: **2 vitórias e 0 derrotas** do exato.
Poucos pares discordantes não sustentam superioridade populacional de acurácia.
O ganho de tempo não veio de menos forwards: veio da seleção/validação.

O comparador é viabilidade gulosa por confiança com reutilização de testemunha,
usando o mesmo parser, suporte, gramática e fallback. **Não é EPIC.**
Não se demonstrou superioridade sobre geração livre ou todos os decodificadores.

## Exemplos da confirmação

- `nested-220104-161`: Subtract 1 from the product of 1 and 1. Put the nested expression in the first argument.
  Exato: `sub(mul(1,1),1)`; guloso: `sub(sub(1,1),1)`.
  Primeira etapa: 8 propostas ordinárias retidas pelo exato, contra 3 pelo guloso; EOS/PAD excluídos dessa contagem.
- `nested-220104-71`: Subtract 1 from the product of 3 and 1. Put the nested expression in the first argument.
  Exato: `sub(mul(3,1),1)`; guloso: `sub(sub(3,1),1)`.
  Primeira etapa: 6 propostas ordinárias retidas pelo exato, contra 3 pelo guloso; EOS/PAD excluídos dessa contagem.

## Todas as tentativas exploratórias

| Coorte | Orçamento | Método | Acertos/pedidos | Forwards |
| --- | ---: | --- | ---: | ---: |
| m22_tool_screen_v1 | 4 | exact | 24/24 | 96 |
| m22_tool_screen_v1 | 4 | greedy | 24/24 | 96 |
| m22_tool_screen_v1 | 16 | exact | 24/24 | 24 |
| m22_tool_screen_v1 | 16 | greedy | 24/24 | 24 |
| m22_tool_screen_v2 | 8 | exact | 24/30 | 111 |
| m22_tool_screen_v2 | 8 | greedy | 24/30 | 111 |
| m22_tool_screen_v2 | 24 | exact | 19/30 | 71 |
| m22_tool_screen_v2 | 24 | greedy | 19/30 | 71 |
| m22_tool_screen_v3 | 24 | exact | 24/60 | 138 |
| m22_tool_screen_v3 | 24 | greedy | 24/60 | 140 |
| m22_tool_screen_v4 | 24 | exact | 41/60 | 120 |
| m22_tool_screen_v4 | 24 | greedy | 41/60 | 118 |

V1: chamadas simples. V2: chamadas aninhadas determinísticas. V3:
propostas amostradas. V4: preservação do multiconjunto de operandos
dentro da geração; houve uma vitória e uma derrota, com empate global.
A triagem usou enumeração canônica; a confirmação usou o parser Rust
sobre domínios posicionais e CFG de bytes, permitindo outras tokenizações.

## Alcance científico

São pedidos sintéticos de compilação de expressões para chamadas de funções,
com inferência real, um único modelo quantizado e templates compartilhados.
A restrição preserva operandos lidos do pedido; não recebe a resposta esperada.
O domínio é finito/regular: não isola uma vantagem de expressividade de CFGs.
A garantia é por etapa e suporte, com testemunha verificada; não garante semântica.
A linguagem de calculadora é uma aplicação limitada de geração de programas,
não um benchmark de APIs reais. A enumeração também continua sendo uma
alternativa forte quando todo o catálogo é pequeno e explícito.

A contribuição observada é um benefício restrito durante a geração pela dLLM:
seleção exata mais rápida que a viabilidade gulosa comparada e 2 pedidos
novos recuperados corretamente. Os resultados negativos anteriores permanecem.
