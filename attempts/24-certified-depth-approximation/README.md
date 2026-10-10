# 24 — Aproximação por profundidade com erro probabilístico certificado

**Investigação matemática inicial; não implementação nem benefício confirmado.**
Motivação: as inferências completas22/23 ficam caras quando permitem todas as
estruturas profundas de probabilidade pequena. Um limite de profundidade
arbitrário é rápido, mas altera uma distribuição em quantidade desconhecida.
Aqui o limite só é autorizado por um certificado do erro condicionado.

## Oito critérios científicos (versão inicial)

1. **Uso real.** Preencher ou gerar JSON recursivo com uma dLLM, usando TODOS
os IDs originais e uma distribuição conjunta válida. Permitir a um serviço
escolher tolerância de erro frente ao posterior de recursão irrestrita, em
vez de trocar silenciosamente a gramática por uma de profundidade fixa.
Saída: amostra válida, marginais aproximadas e certificado de massa/distância.
2. **Novidade/significância.** Limitar pilhas, aproximar gramáticas por
autômatos, calcular probabilidades por DP e propagar erro entre kernels são
antecedentes. Denkinger2017 trata inclusive aproximação ponderada de storage;
Mohri/Nederhof2001 regularizam gramáticas ponderadas. Não reivindicá-los.
O recorte candidato é um certificado barato, sobre os eventos originais do
tokenizer, para o erro CONDICIONADO a JSON, com ligação ao decoder completo.
Precisamos conferir se este certificado já é uma aplicação descrita desses
antecedentes. Sua significância permanece aberta, não presumida pelo enunciado.
3. **Por que escolher.** Decoder finito limitado à profundidade d, com
certificado contra o posterior recursivo completo. Comparadores: inferência
completa competente por CFG/pilhas; o MESMO decoder limitado com certificado
mais simples de atingir profundidade excessiva; limites triviais de cauda.
Hipótese: um limite de massa que exige também fechamento do documento permite
usar d menor e pagar menos, mantendo a tolerância declarada. Custos completos.
4. **Prova sem código.** Se L_d é a massa válida até profundidade d e U_d
limita a massa válida acima dela, então TV <= U_d/(L_d+U_d). Calcular U_d
por lexer determinístico e contador de delimitadores, exigindo profundidade
não negativa e zero ao final, sem memória dos tipos. Isso conta cada evento
original uma vez e fornece upper bound polinomial. Provar U_d <= bound que
só observa overflow. Conectar tolerâncias por passo à trajetória com a MESMA
política de commits usando acoplamento. Não inferir exatidão global de um passo.
5. **Experimentos honestos.** Antes de timing, definir tolerâncias, d
candidatos, todos os documentos externos, controles, recursos e regra de
escolha/refusa/fallback. Usar os logits originais já arquivados como
desenvolvimento. Não excluir casos de certificados fracos ou decoder caro.
Os cinco documentos externos ainda sem forwards ficam reservados até gate.
Não medir ainda: novidade e prova vêm primeiro, depois protótipo mínimo.
6. **Custo dLLM.** Incluir tabela, full softmax, agregação de TODOS os tokens,
counter, preparação do decoder limitado, amostra, marginais e forward.
Counter precisa O(n D Q F) operações para altura máxima física D, estados
lexicais Q e efeitos F; memória streaming. Decoder limitado tem dependência
exponencial em d, não é gratuitamente linear. Aridade de tokens e bits entram.
Modelos mudam entre passos: limite da trajetória exige orçamento de erro ao
longo de TODAS as histórias e mesma política. Recursos insuficientes recusam.
7. **Objeção forte.** U_d pode ser largo demais quando validade é rara; uma
cauda absoluta pequena não basta. O decoder completo ou o certificado simples
pode ser mais barato. Aproximação ponderada existente pode já conter o recorte.
Mosaic/FactorDLM podem aproveitar o MESMO certificado; não alegar exclusividade
do decoder finito. Diferença de política baseada em marginais aproximadas pode
invalidar o acoplamento global; usar política comum, ou certificar estabilidade.
8. **Artigo.** Falta conferir o antecedente mais próximo, terminar prova/
custo, enumerar eventos originais independentemente, medir todos os controles
e confirmar externamente. Não há revisão humana, Lean novo, treinamento ou
publicação. Um certificate que sempre recusa não cumpre a utilidade desejada.

Fontes primárias: [Denkinger2017](https://arxiv.org/abs/1703.09910),
[artigo completo](https://cgi.cse.unsw.edu.au/~eptcs/paper.cgi?GANDALF2017.7.pdf=),
[Mohri/Nederhof2001, catálogo do autor](https://sites.cs.st-andrews.ac.uk/people/mn31/publications/),
[Diffinity2026](https://arxiv.org/html/2602.12468v1),
[FactorDLM](https://arxiv.org/html/2609.32900v1).

`work/specification.md` delimita o argumento. Nenhum módulo importa tentativas
mutáveis anteriores. Cada futuro protótipo terá cópias e snapshots próprios.
