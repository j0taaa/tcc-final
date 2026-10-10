# 24 — Aproximação por profundidade com erro probabilístico certificado

**Protótipo e vantagem de certificação demonstrada por escrito; rapidez,
confirmação independente e novidade acadêmica ainda não estabelecidas.**
Motivação: as inferências completas22/23 ficam caras quando permitem todas as
estruturas profundas de probabilidade pequena. Um limite de profundidade
arbitrário é rápido, mas altera uma distribuição em quantidade desconhecida.
Aqui o limite só é autorizado por um certificado do erro condicionado.

## Oito critérios científicos (versão inicial, refinados abaixo)

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

## Protótipo e fronteira dos antecedentes

`work/{certificate,stack_control}.py` materializa o counter e o decoder
limitado. Cópias/extrações independentes do commit cd8267f estão identificadas
por SHA256 em `work/reference-origin.json`. Seis testes enumeram massa,
marginais, bounds e a lei efetiva de sorteio, inclusive aliases, UTF8,
remasking e picos intratoken. Não são evidência de velocidade ou novidade.

[Future Validity, Nie et al.2026](https://arxiv.org/html/2605.07698v1),
seção4/teorema7 e apêndicesB/C, já relaciona erro de normalização à TV e
propaga erro local na geração autoregressiva. Nossa desigualdade elementar
e o acoplamento não são novidade genérica. O recorte que resta investigar
é um certificado DETERMINÍSTICO computável, sem ground truth da massa total,
para posterior recursivo no vocabulário completo de um passo de dLLM.
Denkinger2017, seção4.4/teorema34, já fornece bounds ponderados por abstração
de storage; não atribuir originalidade a esse princípio. Prioridade dessa
especialização e tamanho da contribuição continuam questões abertas.

[Sakharov2017](https://arxiv.org/html/1707.07670), seções3/4,
proposições1/4, já aproxima GLCs por linguagens one-counter que as contêm.
Exigir contador zero ao final e obter custo quadrático não são novidade.
Sua construção geral é não determinística, voltada ao reconhecimento e
reconstrução de árvores; nosso certificado probabilístico conta eventos
originais de um produto posicional, não a multiplicidade dessas derivações.
Essa diferença delimita a implementação, sem provar prioridade acadêmica.

Antes de timings competitivos, `work/diagnostic-protocol.json` fixa todos
os18 estados de desenvolvimento existentes, profundidades e tolerâncias.
A primeira execução verifica se o certificado consegue autorizar alguma
aproximação útil; ela NÃO confirma rapidez, geração completa ou vantagem
externa. Se não certificar, não iniciar outra infraestrutura grande.

## Refinamento: primeira ultrapassagem gramatical e continuação abstrata

Os oito critérios anteriores continuam válidos. O comparador reforçado é
agora o limite de massa descartada na primeira ultrapassagem de d por um
PREFIXO GRAMATICAL, calculado pelo próprio decoder limitado. Esse controle
não paga um counter separado. Antes de ampliar, a hipótese distintiva é
continuar esses prefixos com um counter lexical ponderado: exigir fechamento
provável, em vez de cobrar massa1 a todo futuro desconhecido. A prova em
`work/handoff-proof.md` mostra dominância simultânea sobre esse comparador
e sobre o counter independente, e uma família onde o aperto é ilimitado.
Essa família é objeto da prova, não benchmark de desempenho.

Essa operação NÃO adiciona uma nova política de commitment ou acerto
semântico. Preserva a amostra de J_d e melhora o certificado frente a J.
O custo extra é um DP de counter que ignora tipos e sintaxe somente APÓS
a primeira ultrapassagem. Abstração de storage, primeira passagem e DP são
conhecidos; novidade da combinação/aplicação continua sem confirmação.
Medir contra grammar-hit, suffix-hit, counter-closed e posterior completo.
Uma vitória contra hit lexical fraco não basta. Oráculos precisam encontrar
erros na partição de primeira ultrapassagem, inclusive quando ela ocorre
dentro de um único token que abre E fecha várias estruturas.

## Reavaliação antes de medidas competitivas

1. **Aplicação.** Preenchimento probabilístico de JSON, preservando trechos
fixos, com marginais usadas por uma política de geração. A saída é uma
distribuição conjunta válida com tolerância escolhida pelo consumidor, e não
apenas uma string que um validador aceita. O posterior é o produto de um
forward congelado da dLLM, sem alegação de qualidade semântica.
2. **Diferença científica.** `work/certificate-separation.md` prova, com um
tokenizer FIXO e documentos com campo `payload`, uma separação de poder entre
certificados. Fechamento ponderado autoriza profundidade1 e erro
`4/[3(n+1)!]`; primeira ultrapassagem gramatical exige profundidade pelo menos
`n+2` para tolerância abaixo de1/9. A implicação de espaço é exponencial
somente para compiladores de pilhas explícitas. A abstração ponderada geral
é antecedente; suficiência para publicação e prioridade específica não estão
confirmadas. A prova não pressupõe que um modelo real produza essa família.
3. **Escolha e comparadores.** Uma pessoa escolheria o método se certificados
determinísticos permitirem inferência útil mais barata frente ao posterior
completo, com erro conhecido. Grammar-hit recebe prefixos gramaticais e todos
os testes necessários existentes; suffix-hit recebe contexto lexical e
capacidade de fechamento. Quatro inferências EXATAS competentes incluem CFG
compacta, poda bidirecional, scanner epsilon e pilhas com cache. Rejeição é
controle de primeira amostra, mas não calcula massa/marginais certificadas.
4. **Benefício provado.** A separação acima independe do código. Handoff
domina simultaneamente o counter fechado e grammar-hit porque conserva a
sintaxe até a primeira ultrapassagem e relaxa só a continuação. Dominância de
bound não implica rapidez. Corolário JSON, custo em bits e a perturbação para
suportes positivos estão escritos. A amostra continua exata em J_d.
5. **Protocolo.** `work/protocol.json` fixa ANTES de timings9 métodos, todos18
estados de desenvolvimento, três rotações e erro1/1000. Regra: melhoria de
20% na mediana pareada wall E CPU e sinal favorável em todas repetições contra
TODOS seis controles obrigatórios, ou capacidade localizada com mesmos limites.
Selecionar uma variante só no desenvolvimento; zero vitórias rejeita o gate.
Somente depois, avaliar todos cinco documentos externos ainda sem forwards,
com nove rotações. Nenhuma perda será removida. `analyze.py` impede adoção
positiva de campanhas parciais e confere certificados contra massa exata.
6. **Custo completo.** Pagar conversão full-V, TODOS os d tentados, fallback,
certificado, amostra, marginais originais e o mesmo forward arquivado. Registrar
também início a frio com tabela/normalização. Controle exato usa fonte imutável
de23/v2, nunca imports de uma tentativa mutável. Inteiros/denominadores,
memória, timeouts e recusas permanecem explícitos. Ainda não é uma medição de
geração completa; essa etapa terá política comum e orçamento de trajetória.
7. **Objeções.** Um counter pode não compensar, o certificado de primeira
passagem pode ser suficiente, a CFG exata pode ser mais rápida e rejeição pode
ganhar na amostra única. Fora da família do teorema não há bound universal de
aceleração. Gramáticas ambíguas, semântica e EOS não são ampliados. O resultado
não deve ser descrito como vitória sobre execuções nativas de EPIC/FactorDLM.
8. **Pendências e evidências.** Nove oráculos pequenos passam; enumeração
independente full-V confere168 comparações sobre24 frames de uma lacuna e
1.206.192 escolhas originais (`work/evidence/full-vocabulary-oracle-v1.json`).
São testes de correção. O diagnóstico handoff congelado em f8ad7b9 conserva108
consultas: sete de18 quadros permitem d menor que grammar-hit e seis d menor
que counter-closed, em erro1/1000. Dados em
`work/evidence/handoff-feasibility-v1`. Não confirmar velocidade com esses
diagnósticos. Faltam timings competitivos, confirmação externa, ciclo dLLM,
revisão humana e redação final; não foram inventados.

Reprodução offline após o freeze, com caches originais disponíveis:

```bash
.venv/bin/python -m unittest attempts.24-certified-depth-approximation.work.test_correctness
.venv-live/bin/python -m attempts.24-certified-depth-approximation.work.run --capture .cache/a22-development-cuda-v1 --output .cache/a24-development-measure-v1
.venv/bin/python -m attempts.24-certified-depth-approximation.work.analyze --input .cache/a24-development-measure-v1 --output .cache/a24-development-decision-v1
```

Pesos de modelo, logits/cache e grandes matrizes continuam locais; snapshots
preservam fontes, protocolo, hashes e evidências declaradas. Capturas adicionais
dependem da passagem pelo gate e usam modelo/tokenizer pinados.
