# Antecedente e contrato: não eliminar normalizadores que a operação exige

2026-10-11. Leitura estática de fontes primárias, sem executar o projeto externo.
[GPIO-LLM](https://github.com/AwaleSagar/gpio-llm), commit
`6b0846503592c9bd2fc8e0f36bc5fac24f57ddf9`, datado2026-09-19 pela API GitHub.
Seu README e docs/ENGINE.md descrevem computar somente logits admitidos pela
gramática e pular decisões forçadas. O fonte confirma: `gl_logits_sparse`
faz dot products das linhas indicadas; `decode.c` obtém IDs admitidos e chama
essa função quando há mais de uma escolha. É um decoder autoregressivo,
não uma inferência conjunta de dLLM. Seus tempos são declarações do autor,
não nossas medições e não evidência de aceleração no nosso hardware.

Fontes pinadas conferidas:

- [forward.c](https://github.com/AwaleSagar/gpio-llm/blob/6b0846503592c9bd2fc8e0f36bc5fac24f57ddf9/engine/src/forward.c#L276),
  função276--291; SHA256 `99e69fac208a83b1e214863ebfb6eb62fe0d44b2b29913ef83370d180b296b11`.
- [decode.c](https://github.com/AwaleSagar/gpio-llm/blob/6b0846503592c9bd2fc8e0f36bc5fac24f57ddf9/engine/src/decode.c#L130),
  fluxo130--161; SHA256 `e55a55b751c4b40b7c01a1785c8449422246c3701ab2f1887083f3e75a75bc54`.

## Derivação própria para avaliar a transferência, não nova identidade

Seja S o conjunto de conclusões tokenizadas válidas, não vazio. Para cada
slot i, seja A_i o conjunto dos IDs que aparecem naquele slot em ALGUM y de
S. Com logits l_{i,v}, P_i(v)=exp(l_{i,v})/D_i e D_i soma sobre todo V,

    Q(y) = 1_{y em S} prod_i exp(l_{i,y_i})
           / sum_{z em S} prod_i exp(l_{i,z_i}).

Os D_i cancelaram porque todo caminho consome os mesmos slots. Portanto
calcular somente as linhas em A_i preserva Q e seus aliases originais. É
válido também usar um SUPERconjunto seguro de A_i; uma poda que remova um
token de uma conclusão de peso positivo já muda Q. Estados de massa zero,
EOS/slots variáveis ou mudanças de gramática não recebem esta fórmula sem
verificar as hipóteses correspondentes.

Já a massa válida ORIGINAL é

    Z = [sum_{z em S} prod_i exp(l_{i,z_i})] / prod_i D_i.

Para obter esse Z exato, os D_i continuam necessários. Uma API que promete
certificar probabilidade válida não pode simplesmente omitir esse custo.
Igualmente, confiança de um token na política nativa usa o normalizador
original: substituí-lo por soma sobre A_i muda limiares, prioridades e
possivelmente commitments. Economizar trabalho mudando a operação sem
declarar seria um comparador inadequado, não uma vitória científica.

Uma viabilidade prévia por CFG, suporte crescente e execução GPU eficiente
ainda podem exigir trabalho real. Mas esta versão não localizou um resultado
distintivo além de projeção esparsa já implementada e cancelamento clássico.
Não justificar implementação extensa apenas pelo fator teórico V/|A_i|.
