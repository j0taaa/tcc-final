# Tentativa 18 — Preservar a política de geração e evitar trabalho gramatical repetido

Iniciada em 2026-10-09 sobre `89078ecf589e187927c1ba3d4f54f87ba9df43cd`.
Pesquisa isolada; a tentativa 17 e os decoders mantidos não são substituídos.
Status: **controle fortalecido CPU/GPU completo sem ganho; núcleo nativo validado**.

Versão v1 preserva o protótipo/protocolo inicial. Antes de qualquer forward ou
timing, a inspeção do corpus encontrou só nove documentos de 24..96 tokens,
insuficientes para a divisão predeclarada de 18. A faixa passou a 16..96
(24 documentos disponíveis); a divisão por hash, os tamanhos de máscara e os
controles permanecem iguais. Nenhum resultado de modelo/solver orientou isso.

## Resultado CPU e próxima verificação

[Relatório gerado CPU](work/evidence/cpu-decision.md): 324 registros de
desenvolvimento e 648 de avaliação externa separada. Em 504 comparações de
execuções completas, suportes, propostas, commits e saídas coincidem exatamente.
O propagador completa 17/18 configurações de desenvolvimento e 21/36 de
avaliação; as restantes não admitem JSON no top16 declarado. Não eliminá-las.
Nenhuma configuração passa o critério forte de redução total >=20% em parede
e CPU contra todos os controles concluídos. Algumas seleções ficam mais baratas,
mas o modelo/compilação/preparação diluem a economia.

[Extensão GPU](work/gpu-addendum.json) usa exatamente os mesmos documentos,
casos, comparadores e critérios. Foi registrada após desenvolvimento CPU,
antes de qualquer forward CUDA. CPU não é renomeado como resultado favorável.
O limite matemático continua válido, mas não prova velocidade física.

[GPU original](work/evidence/gpu-decision.md): 1/18 configurações de
desenvolvimento e 1/36 externas passam o critério, com mais 504 comparações
exatas de trajetórias. Ainda NÃO confirmar a vantagem: os métodos baseados em
floresta processam também células que não participam de nenhuma derivação da
raiz. Eliminação dessas células é uma otimização clássica competente, deve
beneficiar igualmente propagador e controles. O refinamento terá plano próprio,
os mesmos documentos/máscaras e custos totais, sem substituir dados originais.
Os oito critérios permanecem iguais: isso é um controle mais forte, não uma
nova contribuição ou seleção de casos favoráveis.

[Plano de relevância](work/relevance-addendum.json), congelado antes das novas
medições, aplica a mesma poda a TODOS os controles de floresta e ao propagador.
Contabiliza sua execução e preserva todas as derivações da raiz; os oráculos
independentes verificam trajetórias antes/depois. Reavalia os critérios 3/6/7:
um ganho perdido frente a controles adequados não será usado para justificar
adoção. Critérios 1/2/4/5/8 e a divisão de casos permanecem iguais.

O [refinamento nativo](work/native-addendum.json) investiga a proposta
lexicográfica original, agora sem construir uma floresta completa. Antes de
implementar/medir, reavalia os critérios: (1) mesma operação de infilling;
(2/4) os fundamentos continuam conhecidos, a candidata é uma integração com
equivalência de política e eventual vantagem prática, sem prioridade teórica;
(3/7) guloso nativo com testemunho persistente, inicialização antecipada e
tardia compartilham o mesmo kernel e validação; (5) TODOS os casos antigos,
agora avaliação de refinamento e não conjunto externo inédito; (6) custos
integrais, inclusive conversão de prioridades, construção/normalização a cada
consulta e validação linear JSON; (8) benefício ainda não medido, revisão
humana/publicação pendentes. O backend já compara somas de floats de entrada
exatamente por BigUint; díades representam prioridades, não arredondamentos
usados para decidir. Mais de 1075 prioridades exige recusa nesta versão.

[Resultado com poda](work/evidence/trim-decision.md): nenhuma das 18/36
configurações de desenvolvimento/avaliação passa o critério, em CPU ou GPU.
1.944 registros antes/depois preservam exatamente status, suporte, propostas,
commits e output. Isso invalida os ganhos GPU originais como justificativa de
adoção frente a controles competentes. O refinamento nativo tem cinco testes
offline focados; 20 trajetórias adicionais passam pelo Rust reconstruído,
inclusive todas as 1075 prioridades. Seus tempos ainda não foram medidos.

## Contrato e oito critérios

1. **Uso:** completar lacunas de documentos JSON com uma dLLM, preservando
   texto existente. A operação consumida pelo próximo forward é o lote de
   tokens fixados. Procurar menos trabalho de constraints com exatamente o
   mesmo lote da política gulosa especificada, não uma pontuação diferente.
2. **Relevância/novidade:** programação dinâmica lexicográfica é conhecida
   (Goodman 1999; Sproat et al. 2014). Propagação incremental AND/OR com custo
   amortizado por uma sequência de contrações também é conhecida (Quimper e
   Walsh, §GRAMMAR de 2009, referindo resultados de 2007). NÃO apresentar
   essas técnicas como novas. A contribuição candidata é uma integração
   curta que preserva as transições de uma política de dLLM, inclusive filtro,
   orçamento e fallback, e contabiliza tokens originais e geração inteira.
   Um ganho relevante medido pode sustentar uma contribuição de engenharia
   científica; prioridade/suficiência para publicação continuam pendentes.
3. **Escolha:** comparar lexicográfico, guloso com reutilização de testemunho
   e propagação incremental competente. O alvo é menor custo total sem alterar
   as saídas, e não ganhar contra um guloso que deliberadamente reconstrói tudo.
   Enumeração independente entra quando o produto cartesiano cabe. Não alegar
   ganho sobre EPIC sem executar sua operação completa em tarefa alinhada.
4. **Matemática:** demonstrar equivalência lexicográfico–guloso e equivalência
   de transições após filtro/cap; estudar um propagador por deleções monotônicas.
   O custo após compilação é linear no tamanho da floresta mais propostas ao
   longo de toda a geração, com saída e aritmética contabilizadas. Este limite
   é uma especialização do antecedente incremental, não um novo limite geral.
5. **Experimentos:** protocolo congelado antes de qualquer timing de nova
   implementação. Desenvolvimento e avaliação separados por hash dos exemplos
   externos. Incluir recusas, divergências, enumeração mais rápida e todos os
   tamanhos predeclarados. Não selecionar documentos por conflitos ou vitória.
6. **Custo completo:** medir preparação, primeiro forward, suporte, compilação,
   consultas, atualizações e saída. Executar forwards de todos os decoders;
   replay não vira geração completa. Suporte inicial permanece fixo, não usa
   gabarito e pode excluir respostas relevantes. Nova previsão muda a ordem,
   não expande suporte. Remasking/expansão requerem recompilação e estão fora
   do teorema de contrações. Modelo/contexto/tokenizer iguais.
7. **Objeção forte:** a técnica incremental clássica pode tornar lexicográfico
   desnecessário. Se isso ocorrer, rejeitar o lexicográfico como protagonista,
   em vez de omitir o controle. Compilação pode dominar, enumeração vencer e
   top-K fixo limitar utilidade. Preservar essas possibilidades no relatório.
8. **Artigo:** falta medir geração, conferir igualdade das transições, obter
   revisão humana e delimitar a diferença publicável. Os fundamentos conhecidos
   devem aparecer na apresentação. Não converter CI, Lean ou ganho contra um
   próprio baseline em prioridade mundial/qualidade semântica superior.

## Antecedentes conferidos

- [Semiring Parsing, Goodman (1999)](https://aclanthology.org/J99-4004/).
- [Lexicographic Semirings, Sproat et al. (2014)](https://aclanthology.org/J14-4002/).
- [Grammar Constraints, Quimper e Walsh (2009), §GRAMMAR](https://arxiv.org/pdf/0903.0470):
  propagação por decomposição e custo de toda uma branch igual a uma propagação.
- [EPIC v2, 2026-10-04, §§4.2–4.3](https://arxiv.org/html/2606.00722v2):
  cover regular, redução de batches e verificação exata em grafo. Não preserva
  por definição cada decisão do nosso guloso em suporte finito.

## Organização

`work/` contém protótipos independentes, especificação/provas e protocolo.
O compilador mantido pode ser reutilizado, com seu commit congelado no snapshot;
nenhum import depende do código mutável de outra tentativa. Versões congeladas
serão criadas após código e evidências serem commitados. Pesos/logits completos
permanecem fora do repositório. Não restaurar testes históricos.
