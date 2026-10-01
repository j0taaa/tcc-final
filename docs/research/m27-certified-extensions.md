# M27 — Extensões certificadas e simplificação

Autorizado em 01/10/2026. As três propostas fazem sentido com as condições
abaixo. São aplicações de técnicas estabelecidas, não uma alegação de prioridade
mundial. A prova de qualidade continua sendo sobre a recompensa das propostas
da etapa, e não sobre a correção semântica da resposta da dLLM.

## 1. Limites independentes para um lote válido

Fixe exatamente o problema M26. Agregue todas as propostas por posição/token,
incluindo as que não estão no suporte, e ignore posições já fixas. Seja
`m_i = max_a r_i(a)` e seja `U_B` a soma dos `min(B, |I|)` maiores `m_i`.
Uma testemunha válida e um lote `T` com no máximo B posições livres dão uma
recompensa recomputada `L`.

**Teorema.** `L <= OPT_B <= U_B`. Para qualquer conclusão e lote válidos,
`sum_{i in T} r_i(y_i) <= sum_{i in T} m_i <= U_B`. Como a testemunha do
incumbente é viável, ela prova a primeira desigualdade. Portanto a perda aditiva
é no máximo `U_B-L`; para `U_B>0`, `L/U_B` é uma razão garantida. Se `U_B=0`,
toda solução válida tem recompensa zero e é ótima. QED.

**Corolário de expansão.** O mesmo limite vale em qualquer expansão de suporte
que mantenha propostas, pesos, posições fixas, gramática e semântica dos slots.
Se `L=U_B`, nenhuma dessas expansões melhora a recompensa. O resultado do
solver continua carregando seu suporte original e `exact_on_support`; este
corolário é um certificado adicional, não um relabeling do suporte.

O limite pode ser arbitrariamente frouxo: uma gramática pode impedir todas as
propostas positivas. Não se promete uma razão constante positiva nem frequência
de certificados apertados. Um timeout sem incumbente válido permanece timeout.
Um incumbente deve ser validado antes de emitir qualquer limite inferior.
Um certificador barato não equivale a um algoritmo anytime com limites que
necessariamente melhoram a cada intervalo; essa distinção será documentada.

## 2. Compartilhamento de prefixos com fechamento identificável

A construção privada atual repete `len(bytes(token))-1` estados internos por
token ordinário. A construção compacta usa um estado por **prefixo próprio
distinto** dos tokens de um slot. O arco que fecha uma escolha retém token_id,
posição, papel EOS/PAD e os IDs das propostas. A alternativa paga deve estar
nesse fechamento, pois o prefixo compartilhado ainda não identifica o token.

Se a emissão inteira também é prefixo próprio de outro token, o fechamento é
epsilon. Caso contrário, o último byte e o fechamento usam o mesmo arco. EOS e
PAD fecham diretamente por epsilon; tokens com bytes idênticos ainda têm
fechamentos diferentes. Posições fixas não podem ser pagas.

**Equivalência.** Cada caminho entre duas fronteiras físicas segue um prefixo
único e fecha uma única escolha original. Assim ele identifica um token inteiro,
com a mesma emissão, transição EOS, recompensa e custo físico. A operação
inversa segue os prefixos do token e seu fechamento. Concatenando essas
operações em todos os slots, os pares `(conclusão, lote)` e seus valores são
preservados. Os optima para todos os orçamentos são iguais. Não há poda.

**Tamanho.** Seja `P_i` o conjunto de prefixos próprios não vazios no slot i.
Então `|P_i| <= sum_t (len(bytes(t))-1)`. Logo, com as mesmas fronteiras EOS,
o número de estados compactos nunca excede o privado. A redução é estrita
quando dois tokens compartilham algum prefixo próprio. Isso reduz os parâmetros
do limite de complexidade do parser, não prova uma razão de tempo real.

## 3. Certificado completo da entrada original

O checker M26 prova o ótimo em relação ao grafo entregue. A extensão deve
verificar separadamente que esse grafo representa a entrada original: escolhas
do suporte, pesos agregados exatos, slots, bytes, controles e todos os arcos
permitidos. Uma testemunha deve ser recomputada a partir de tokens/posições;
seus metadados não podem ser aceitos só porque o caminho no grafo é válido.

O checker não pode importar o otimizador nem confiar em seu fingerprint. Uma
entrada alterada precisa falhar por correspondência semântica, mesmo quando
seu grafo e seus limites continuam formando uma prova válida para outro
problema. Uma prova autocontida tem uma entrada explícita; a vinculação a uma
entrada externa usa essa entrada como argumento ou compara seu hash esperado.

## Lean e cobertura de verificação

Toolchain fixada: `leanprover/lean4:v4.34.0`, sem Mathlib ou dependências remotas
de execução. A biblioteca padrão é suficiente para definições finitas e pesos
inteiros. Pesos racionais não negativos são escalados por um denominador comum
positivo; nenhuma soma é arredondada.

`formal/MWPC/` implementa limites por indução em caminhos/derivações,
optimalidade e inviabilidade certificadas, relaxação por posições, qualidade,
aperto sob expansão, lemas de prefixos/tamanho e consequências condicionais
de dominação e capacidade. A [cobertura exata](../../formal/README.md) separa
provas universais, instâncias verificadas, correspondência e componentes externos.
O kernel confere desigualdades finitas e os construtores das testemunhas
exportadas. A correspondência completa entre grafo e entrada é uma verificação
Python independente; a implementação do compilador não foi refinada
universalmente em Lean. Não há provas admitidas, axiomas de projeto ou
`native_decide`; os axiomas lógicos padrão aparecem na auditoria explícita.
`make check-formal` é obrigatório na CI; `make check-project` reúne Lean,
Python/Rust, baselines e reconstrução dos artefatos do artigo. Não se afirma
que o kernel verifica automaticamente todo Python, Rust, CUDA ou a semântica
de uma dLLM. Completude do DP e famílias infinitas de separação continuam
como provas escritas, além dos testes.

## Auditoria inicial de simplificação

145 arquivos Python em `src/` e `scripts/`, com 45.386 linhas antes da mudança.
A busca AST não encontrou funções privadas de topo cujo nome aparece uma só
vez em código/testes. Isso não prova ausência de código morto, mas impede
justificar remoções apenas pela aparência. Foram encontradas duplicações
exatas de validação, hashing e I/O de artefatos. Foram consolidadas 27 cópias
de helpers exatamente iguais em 11 implementações compartilhadas. Parsers e
oráculos independentes permanecem independentes.

O caminho orçado atual também constrói a normalização ponderada de epsilon do
MWPC comum e não usa o resultado. A construção direta elimina essa operação
dispensável. Scripts históricos que regeneram tabelas, falhas e
comparações são dependências científicas e não são código inútil.

## Antecedentes consultados

- [ARA*, NeurIPS 2003](https://papers.nips.cc/paper_files/paper/2003/hash/ee8fe9093fbbb687bef15a38facc44d2-Abstract.html): busca com limites provados de subotimalidade; o princípio não é novo.
- [Trie Automata, 2026](https://arxiv.org/abs/2608.12574): prefixos compartilhados em decodificação restrita; nossa obrigação adicional é preservar recompensas, custos físicos e provenance.
- [Certifying DP, CP 2024](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.CP.2024.9): antecedente de algoritmos certificadores.
- [Lean 4.34.0](https://lean-lang.org/doc/reference/latest/releases/v4.34.0/) e [Elan](https://lean-lang.org/doc/reference/latest/Build-Tools-and-Distribution/Managing-Toolchains-with-Elan/): toolchain reproduzível e kernel de verificação.
