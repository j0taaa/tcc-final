# Decisão de pesquisa após comparar as tentativas

Investigação em 2026-10-08; base `d739b46`. Esta é uma continuação da
tentativa 15, relacionada à 16, sem novo decoder ou campanha experimental.
As versões congeladas e os resultados desfavoráveis permanecem intactos.

## Antecedente adicional e consequência para a novidade

[Ji et al., PLDI 2020, Question Selection for Interactive Program Synthesis](https://zhenjiang888.github.io/pub/pldi20.pdf),
§3.2, §§5.1–5.3, Teorema 5.7 e Figura 1: VSampler já representa programas
consistentes com exemplos por version space algebra (VSA), calcula suas massas
e amostra a distribuição de uma PCFG condicionada aos exemplos. A construção
anota os não terminais com vetores dos resultados de execução. Isso é um
antecedente mais direto dos perfis semânticos que uma simples referência
genérica a parsing probabilístico. Não é suficiente reivindicar novidade por
amostrar regras válidas segundo exemplos ou por calcular seus perfis.

Uma redução clássica explica a proximidade. Na floresta acíclica e não ambígua
de caminhos de tokens, seja `Z(v) = sum_a lambda(a) product_c Z(c)`, com pesos
locais que contam cada token original uma vez. Para `Z(v)>0`, normalize cada
alternativa por `pi_v(a)=lambda(a) product_c Z(c)/Z(v)`. Na árvore de uma saída,
os fatores `Z(c)` cancelam e a probabilidade resulta no produto dos pesos dos
tokens dividido por `Z(root)`. Alternativas de massa zero não são sorteadas.
Essa é uma PCFG acíclica sobre a floresta. Anotar essa representação com a
execução e condicioná-la aos exemplos fornece a mesma operação probabilística
por técnicas de VSA. IDs de tokens/arestas precisam permanecer nas folhas,
inclusive quando dois IDs renderizam os mesmos bytes; não se deduplicam textos.
Esta redução não demonstra que o software VSampler aceite diretamente nossa
API, nem que sua compilação tenha o mesmo custo. Mostra por que a operação e a
normalização, isoladamente, não são o passo científico distintivo.

[FactorDLM, v1](https://arxiv.org/html/2609.32900v1), §3.1 e related work:
reutiliza planos sob mudanças de unários e reconhece circuitos compilados como
antecedentes. Um comparador justo também compila uma vez quando pode; não se
deve cobrar recompilação completa em cada passo para fabricar amortização.
[CARS, v2](https://arxiv.org/html/2510.01902v2), §3, Algoritmo 1, mantém
exclusões de prefixos. A comparação C1 da tentativa 16 continua delimitada a
essa atualização, sua família e contagem de rejeições. VSampler não refuta C1;
torna insuficiente usar CARS como o único concorrente semântico.

## Objeção matemática: núcleos pequenos não existem em geral

Observação de expressividade, não reivindicada como teorema novo. Considere
`d>=1` campos Booleanos, `m` registros distintos e uma linguagem com variáveis,
AND, OR e NOT sem limite de tamanho das fórmulas. Para qualquer registro `r`,
a conjunção dos literais que especificam seus `d` valores é um indicador
`I_r`: vale um exatamente em `r`. Disjunções desses indicadores realizam
qualquer rotulação dos registros. A função sempre falsa pode ser escrita
`x AND NOT x`, sem precisar adicionar uma constante à linguagem.

Para qualquer requisito omitido `i`, construa a fórmula que concorda com os
alvos de todos os registros, exceto `i`, cujo alvo é invertido. A construção
tem tamanho `O(md)`. Ela satisfaz qualquer subconjunto que omita `i`, mas não
o conjunto completo. Logo, nenhum subconjunto próprio preserva exatamente
todas as conclusões válidas nessa linguagem: o núcleo precisa dos `m` exemplos.

Isso não contradiz certificados pequenos no suporte finito atual: a fórmula
separadora pode não caber nos slots ou seus tokens podem estar ausentes.
Também não contradiz a redução por fronteiras em linguagens monotônicas.
Impede extrapolar desses casos para regras Booleanas arbitrárias e reforça
que expansão de suporte/remasking não preservam automaticamente o certificado.

## Respostas aos oito critérios atuais

1. **Uso:** completar regras JSON/DSL consumidas por software, preservando um
   esboço e exemplos de comportamento durante consultas sucessivas da dLLM.
   Escolher uma aplicação real antes da avaliação; a captura pequena existente
   é evidência de desenvolvimento, não a aplicação externa definitiva.
2. **Significância:** a novidade geral do condicionamento por exemplos é fraca
   diante de VSampler/FTA. O resultado candidato teria de melhorar uma operação
   ou um limite de custo que esses métodos não oferecem diretamente. Esse passo
   distintivo ainda não está identificado e provado.
3. **Adoção:** a condição desejada é menor custo total/memória de uma sequência
   de consultas sob o mesmo contrato. Comparar com VSA/circuitos reutilizados,
   fatoração compacta e enumeração quando pequena. CARS serve para comparação
   de amostragem; EPIC para geração sintática/progresso, com objetivos separados.
4. **Matemática:** exigir especificação, diferença para o antecedente, prova
   de vantagem e aplicação que satisfaça as hipóteses. R1/R3 e C1 são resultados
   existentes delimitados; não preenchem sozinhos a lacuna de novidade atual.
5. **Experimentos:** se necessário, congelar uma avaliação independente antes
   de medir, com todos os casos e métodos aplicáveis. Não ampliar o canvas de
   desenvolvimento até obter uma vitória; a auditoria completa já conserva as
   derrotas para enumeração e o custo de certificação.
6. **Custo/dLLM:** incluir preparação, todas as consultas, bits, modelo e
   manutenção após alterações. Pesos podem mudar globalmente; não assumir
   atualizações esparsas sem evidência. Contração/novos commitments são
   compatíveis; expansão/liberação exigem tratar nova preparação/certificação.
7. **Objeções:** a redução VSA, a irredundância acima, um fatorador compacto e
   a certificação cara podem eliminar o benefício. Não assumir `k<<m`.
8. **Publicação:** ainda faltam um passo distintivo relevante, sua vantagem
   contra o antecedente competente, aplicação independente e revisão humana.
   Nenhuma dessas obrigações é marcada concluída por este documento.

## Próximo investimento recomendado e critério de decisão

Continuar uma investigação curta da tentativa 15, com a 16 como resultado
complementar, antes de ampliar a implementação. A pergunta é: **há uma redução
certificada do custo total de inferência em consultas sucessivas realmente
necessárias à dLLM, além de reutilização/seleção de exemplos já conhecidas?**

O primeiro entregável deve ser uma comparação matemática com VSA/circuitos e
fatores competentes sob os mesmos tokens, evidência e alterações admitidas.
Escolher uma aplicação concreta com múltiplas saídas, identificar por que as
hipóteses favoráveis ocorrem nela e procurar primeiro a redução que elimina a
suposta novidade. Não começar por outro modelo, integração ou campanha grande.

Para preparação `P` e consulta `c`, comparar `P_core + sum_t c_core(t)` com
`P_base + sum_t c_base(t)`. Se os custos por consulta forem constantes e
`c_base>c_core`, a amortização exige
`T > (P_core-P_base)/(c_base-c_core)`. É apenas a identidade de custos, não um
novo teorema nem um limiar medido: medianas de lotes e somas de certificação
para 256 alvos do arquivo atual não estimam esse limiar para uma trajetória.

Um bloco inicial de alguns dias é orçamento de investigação, não prazo para
descoberta. Prosseguir se houver diferença explícita, vantagem demonstrável e
uso compatível. Se restar apenas aplicar VSampler/circuitos ou retirar
restrições logicamente redundantes, registrar o descarte como contribuição
central e escolher outra direção. A ausência de resultado distintivo não
autoriza concluir que o objetivo foi atingido, nem afirmar que o TCC inteiro
não tem valor. Uma contribuição empírica de eficiência continua autorizada,
mas precisa de algoritmo/engenharia próprios, controles fortes e avaliação
independente; não é uma vantagem já estabelecida nesta revisão.

Esta revisão não propõe treinar um equivalente geral de Jev nem usa o tamanho
do projeto, as provas Lean ou esforço despendido como medida de relevância.
