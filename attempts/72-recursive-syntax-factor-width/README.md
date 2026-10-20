# A72 — Limite robusto para representações de sintaxe recursiva

Investigação de 2026-10-20 (UTC). Há uma prova escrita e oráculos finitos.
A prioridade específica e a suficiência científica continuam abertas.
Nenhuma campanha neural, ganho de latência ou aprovação acadêmica é alegada.

## Operação e contrato da tentativa

1. **Operação real:** condicionar um produto de pesos posicionais à GLC
   LL(1) fixa `S -> P # P; P -> ( P ) | [ P ] | ε`. São cinco tokens
   originais de um byte, N slots e EOS/PAD ausentes. O limite inferior
   usa pesos uniformes, sem treinamento nem logits adversariais.
2. **Antecedente mais próximo:** Kadioglu/Sellmann (2010) e Wang/Yap
   (2023) já separam sintaxe e árvores de restrições no caso EXATO.
   A candidata é a resistência QUANTITATIVA à aproximação da lei, com
   ocultos arbitrários e qualquer grafo escolhido depois de conhecer o alvo.
3. **Benefício verificável:** determinar se uma aproximação pequena permite
   trocar recursão por um grafo de baixa capacidade. Um limite para todas
   as codificações admitidas evita culpar apenas uma codificação ruim.
4. **Hipóteses e prova:** um observado categórico por posição original,
   fatores não negativos, domínios finitos e grafo primal. Cardinalidades
   dos ocultos contam. [A prova](proof.md) explicita os contratos e os lemas.
5. **Comparador competente:** qualquer grafo e quantidade de auxiliares;
   permitir estados contraídos e permutação interna de posições. O controle
   positivo enumera marcadores e resolve matchings de largura 1. CFDs e
   circuitos contextuais são alternativas eficientes reconhecidas.
6. **Custo completo:** capacidade é soma de log2 dos domínios por bolsa;
   número de nós sozinho não basta. Contar bits dos pesos e massas, RNG,
   preparação e saída. O controle paga O(N²) operações aritméticas para
   pesos gerais; nenhum forward neural entra como gratuito.
7. **Objeções:** a linguagem-base e os argumentos de separadores e afinidade
   são clássicos. A extensão pode ser pequena para o objetivo do usuário.
   O limite não proíbe algoritmos simbólicos, circuitos ou enumeração de
   contextos, nem mede o comportamento dos logits de um dLLM real.
8. **O que falta:** julgar a prioridade e a relevância da extensão frente à
   literatura de aproximação de modelos probabilísticos. Não iniciar uma
   campanha neural apenas porque os oráculos passaram.

## Resultado escrito

Para N=2l+1, seja P a distribuição uniforme da gramática acima. Qualquer
lei Q na interface de fatores, com erro total de variação e<1/5, exige

    W >= l/6 + log2(5(1/5-e)^2),

onde W é a maior capacidade de bolsa em qualquer decomposição em árvore,
incluindo ocultos. Para erro de 10%, alguma bolsa tem pelo menos

    2^((N-1)/12) / 20 estados conjuntos.

O grafo pode ser escolhido especificamente para esse único alvo. Não se
exige uma topologia preparada para servir a vários pesos. A prova usa
apenas pesos uniformes. Ao mesmo tempo, um sampler clássico representa a
mesma lei com trabalho linear, escolhendo o marcador e os bits dos pares.

**O que a utilidade significa:** uma garantia uniforme de aproximação não
justifica tratar toda sintaxe recursiva como tabelas pequenas num único
plano genérico de fatores. A estrutura de cada caso pode ser necessária.
Isso é uma obstrução de representação; não prova que um novo decoder é
mais rápido, gera respostas melhores ou vence métodos sensíveis ao contexto.

A direção inversa baseada em cópias, considerada num rascunho inicial,
foi retirada: uma permutação interna põe os pares juntos e torna a GLC
pequena. Não se alega uma incomparabilidade geral com esse argumento.

## Auditoria de antecedentes

| Fonte primária e trecho lido | Consequência para a candidata |
| --- | --- |
| [Kadioglu/Sellmann (2010)](https://www.researchgate.net/publication/225789014_Grammar_Constraints), Teorema 6; [Wang/Yap, AAAI 2023](https://ojs.aaai.org/index.php/AAAI/article/download/25526/25298), definições e Proposições 4, 7, 8 | A família de dois palíndromos e a separação exata com ocultos são antecedentes diretos. Não são contribuição própria. A Proposição 8 também impede usar cópia reordenável como separação inversa. |
| [McAllester/Collins/Pereira, UAI 2004](https://arxiv.org/pdf/1207.4135), CFDs e parsing | Circuitos sensíveis ao contexto já evitam limitações de grafos. O controle por marcador é clássico. |
| [Braun/Pokutta, revisão de 2016](https://eccc.weizmann.ac.il/report/2013/056/revision/4/download/), introdução e enquadramento de informação comum | Interpretar fatoração não negativa como mistura produto e usar informação/afinidade para limites inferiores é conhecido. |
| [Kučera, CP 2023](https://drops.dagstuhl.de/storage/00lipics/lipics-vol280-cp2023/LIPIcs.CP.2023.22/LIPIcs.CP.2023.22.pdf), introdução, equivalência BCT/SDNNF e compilação por largura | Liga árvores de restrições a decomposição estruturada. A equivalência declarada é de representação exata de relações; não estabelece automaticamente o novo contrato de TV. |
| [Leland/Choi, NeurIPS 2025](https://arxiv.org/html/2506.01281), Seções 3–4 | Já prova dificuldades de aproximação em TV e uma separação entre PCs decomponíveis e também determinísticos. Não reivindicar a ideia geral de que aproximação pode manter separações exponenciais. A candidata cobra capacidade de grafos para uma GLC fixa e um alvo já tratável. |
| [Amarilli et al., STACS 2026](https://drops.dagstuhl.de/storage/00lipics/lipics-vol364-stacs2026/html/LIPIcs.STACS.2026.5/LIPIcs.STACS.2026.5.html), Proposições 3.1, 5.3 e conclusão | Condicionamento por GLC não ambígua e circuitos tratáveis já são antecedentes. O artigo pergunta pela classificação de linguagens em representações estruturadas; isso não torna toda resposta parcial nova. |
| [Zhao et al. (2026)](https://arxiv.org/html/2605.12940), Seção 5 e Apêndice A.4 | A rigidez de uma decomposição fixa já é estudada em modelos de linguagem. A separação ali enunciada é exata, com uma hipótese de incompatibilidade entre estruturas; conferir aproximações/corolários continua necessário. |
| [FactorDLM (2026)](https://arxiv.org/html/2609.32900), Seções 2–3 | Compila fatores reutilizados por passo e cobra largura ponderada, reconhecendo circuitos como extensão. Não promete que toda recursão é barata; A72 não refuta uma promessa que o artigo não faz. |

Não foi encontrado um enunciado equivalente ao limite quantitativo nas
fontes conferidas. Isso é uma conclusão limitada desta busca, não prova
de prioridade mundial, de publicação futura ou de impacto. Uma prova
correta de um refinamento também pode ser insuficiente como contribuição.

## Reprodução e fronteira da verificação

```bash
python3 attempts/72-recursive-syntax-factor-width/check.py
.venv/bin/python attempts/72-recursive-syntax-factor-width/check.py --library
.venv/bin/ruff check attempts/72-recursive-syntax-factor-width/check.py
```

O primeiro comando usa somente a biblioteca padrão. Confere 20 coberturas
de matching, 107.929 partições balanceadas de componentes (exaustivas até
N=9 e amostras maiores), 5.256 contrações para o lema de afinidade,
128 palavras de palíndromos e 80 partições ponderadas do controle forte.
As comparações usam inteiros, inclusive após elevar afinidades ao quadrado.

O segundo comando também confere LL(1), massa e TODAS as marginais da
biblioteca contra palavras construídas independentemente para N=3,5,7,9.
O suporte é explicitamente o alfabeto finito de cinco tokens; não é uma
medição no vocabulário inteiro de um tokenizer real.

Os oráculos finitos não enumeram todos os grafos nem substituem a prova.
Não houve treinamento, modelo ou medição de desempenho neural. Esta
tentativa não altera o solver, o baseline ou fontes científicas congeladas.
