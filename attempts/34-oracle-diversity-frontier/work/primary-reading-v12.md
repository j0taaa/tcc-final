# Regularidade: leituras originais depois de V11

2026-10-11. Auditoria de antecedentes, não revisão humana ou prioridade
confirmada. As notas V11 permanecem congeladas; V12 acrescenta uma prova
pontual independente em pointwise-score-v12.md. Nenhum head/timing novo.

## Nacu e Peres, 2005: enunciados exatos

Original: https://arxiv.org/pdf/math/0309222, SHA256 do download
81e80e4f098af71409a0d6f682e739db0a1e8b4fcc7ee0c279df71ffbfdd17e2.
Leitura direta das Seções5 e7, Proposições22/23 e Questão3:

- A Proposição22 exige caudas dos momentos uniformemente pequenas para
  concluir Ck. Não é enunciada apenas com um bound do kth momento.
- A Proposição23 conclui Lipschitz sob esperança uniformemente limitada
  em um intervalo fechado interior.
- A Questão3 pergunta pela equivalência entre kth momento uniformemente
  limitado e k derivadas contínuas, admitindo condições técnicas.

V11 dá a direção NECESSÁRIA k1 localmente, sem a hipótese de cauda uniforme
da Proposição22. NÃO resolve a equivalência, a direção suficiente, momentos
maiores ou prioridade desde2005. V12 dá diferenciação no ponto de esperança
finita, sem um bound uniforme vizinho. Este contraste de enunciados é uma
leitura literal e derivação própria; não prova que ninguém a publicou depois.

## Holtz, Nazarov e Peres, 2011

Original arXiv0808.1936v3, datado2010-01-25; publicação Constructive
Approximation33 (2011), DOI10.1007/s00365-010-9108-5.
https://arxiv.org/pdf/0808.1936, SHA256
d7d15d66f964800f8a50999e3a515194d56d45388f90812917f21cedf2044f23.
Leitura direta das Seções2/3/7 e Teoremas8/13:

- O Teorema8 caracteriza Hölder não inteiro por taxas de cauda associadas
  à escala de aproximação Bernstein. Não é um enunciado de custo pontual.
- O Teorema13 trata a regularidade Zygmund na taxa inteira correspondente.
- A Seção7 mantém separada a questão de momentos finitos e sugere Besov.

As taxas uniformes destes resultados não são automaticamente iguais a
E_pN finita num ponto. Não afirmar que V12 resolve sua questão de todos os
momentos ou inventa a relação entre regularidade e consumo de bits.

## Paes Leme, tutorial autoral de fevereiro2022

Original: https://www.renatoppl.com/bernoulli/bernoulli-tutorial-feb-22.pdf,
SHA2564a3dda76cb94fbe543c322a21c3f1882a857cfb1a06bda9528e863f06bb03070.
Leitura direta da Seção1.3, Lema1.8 e Problemas1.1/1.2:

O Lema1.8 reapresenta o bound Lipschitz uniforme de Nacu--Peres. O Problema1.1
pergunta por esperança infinita no próprio ponto da cúspide do exemplo.
O resultado pontual escrito em V12 IMPLICA essa impossibilidade dentro de
seu contrato. O Problema1.2 tem função suave no interior, não é resolvido
por essa necessidade. Um tutorial antigo pode conter uma questão já resolvida
noutra fonte; NÃO apresentar o contraste como solução nova confirmada de
problema aberto. Buscar a literatura posterior/estatística sequencial.

## Flegal e Herbei, 2012

Original publicado EJS6 (2012), DOI10.1214/11-EJS663, arXiv1012.3768v2.
https://arxiv.org/pdf/1012.3768, SHA256
b5a33daf63855662c6d78e462ebb659eb4a6abb49300cbbac0a9107d6d9bbe67.
Leitura direta da Seção3/3.1: suavizar o cotovelo melhora as taxas de
aproximação e a implementação da fábrica. Isto antecede qualquer motivação
genérica de suavizar funções para amostragem mais eficiente. Não encontrei
nesse trecho um teorema pontual geral de necessidade, mas a ausência no
trecho lido não é uma busca exaustiva ou prioridade estabelecida.

## Decisão científica atual

As provas V11/V12 retiram hipóteses dispensáveis do comparador A34. A
fronteira escrita fica mais ampla, mas regularidade e estimação sequencial
são áreas antigas, não descobertas decorrentes da troca de nome para dLLM.
Ainda faltam prioridade ESPECÍFICA da fronteira output-restrita e operação
estruturada cujo custo completo/sinal ofereçam benefício competitivo. Os
resultados negativos não foram reclassificados, não há nova campanha neural,
nova teoria CFG ou superioridade sobre EPIC. Não promover a nota ao artigo
como contribuição publicável confirmada antes de fechar essas obrigações.
