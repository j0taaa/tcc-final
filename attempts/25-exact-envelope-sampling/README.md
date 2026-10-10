# 25 — Amostragem exata por envelope de profundidade e fechamento

**Investigação matemática e protótipo isolado. Rapidez prática e prioridade
acadêmica ainda não confirmadas.** A24 permanece intacta: aproxima uma
distribuição e está sendo medida sob seu protocolo original. Aqui a operação
é diferente: usar sua cauda abstrata como proposta de rejeição, preservando
TODOS os eventos válidos, inclusive os profundos. Não descartar uma tentativa.

## Oito critérios antes da implementação

1. **Uso real.** Gerar/preencher JSON com uma dLLM e exigir a lei produto
de um forward condicionada à validade, sem truncar conclusões raras. Utilidade
para inferência estruturada que consome amostras conjuntas, diversidade e
confiança certificada. O modelo fornece texto/probabilidades; não aprende regras
Booleanas de exemplos como15/16. Suporte original completo, trechos fixos,
aliases e intratoken peaks explícitos. Não é correção semântica automática.
2. **Significância.** Rejeição com envelope conhecido e programação dinâmica
são antecedentes. A alegação candidata é um envelope de eventos originais que
mantém sintaxe até first-overflow e exige fechamento ponderado depois, com
garantia ANTES da primeira amostra e preparação polinomial numa classe JSON
onde CARS com o update publicado necessita exponencialmente muitas propostas.
Esse é um comparador delimitado, não lower bound de todo algoritmo CFG.
Novidade específica e suficiência para artigo permanecem questões de pesquisa.
3. **Por que escolher.** Amostra exata sem compilar todas as pilhas profundas.
Se o certificado vale delta<=0.001, aceitação é pelo menos99.9%, incluindo
eventos profundos. Comparadores obrigatórios: rejeição bruta, counter-only
fechado, envelope grammar-hit, CARS produto com pruning forte, inferência
exata compacta por CFG/pilha. O counter-only pode vencer; não omiti-lo.
4. **Prova sem código.** J_d e B_d são disjuntos, J⊆J_d união B_d,
L=q(J_d), U=q(B_d). Amostrar a mistura com pesos L,U e rejeitar só documentos
fora de J produz exatamente q(.|J). Aceitação Z/(L+U)>=1-delta, expectativa
de propostas<=1/(1-delta), refusa após k tentativas<=delta^k. Há prova de
separação com tokenizer fixo e JSON rico em conclusões; não é benchmark.
5. **Experimentos.** Primeiro oráculos independentes da lei efetiva e
contraexemplos. Depois congelar protocolo e código antes de novos timings.
Usar TODOS os18 estados existentes como desenvolvimento e manter recusas/
perdas. Não capturar os cinco documentos externos reservados antes do gate.
Não reaproveitar timing de A24 como vitória desta operação diferente.
6. **Custo completo.** Pagar forward, full-V softmax/conversão, lexer,
profundidades tentadas, counter, reconstrução original e verificação JSON.
Contabilizar cold/primeira saída/lote, memória e bits. Marginais de J_d com
intervalos NÃO são marginais exatas de J. Integrar com a mesma política comum
preserva a lei do decoder de posteriors congelados, não a trajetória NATIVA
condicionada: Twister2026 já demonstra essa diferença.
7. **Objeções.** Um recognizer compacto ou counter-only pode ser mais barato.
Envelopes largos podem não ajudar; métodos adaptativos podem amortizar melhor.
A separação CARS vale somente para updates dos prefixos visitados, mesmo com
oracle perfeito; computar massas CFG globalmente é outro algoritmo e permanece
comparador. Família matemática não prova que logits reais têm aquela forma.
8. **Artigo.** Falta validar o sampler, medir competentemente, confirmar
em inputs independentes e integrar numa aplicação dLLM. Prova escrita não
é Lean nem refinamento formal do Python. Antecedentes não podem ser apagados;
nenhuma revisão humana, prioridade ou publicação foi obtida.

Fontes primárias conferidas: [CARS v2, §3/update/teorema3.2](https://arxiv.org/html/2510.01902v2),
[Denkinger2017, §4.4](https://arxiv.org/abs/1703.09910),
[Sakharov2017, §3/4](https://arxiv.org/html/1707.07670),
[Mohri/Nederhof2001, §4](https://sites.cs.st-andrews.ac.uk/people/mn31/publications/2001a.pdf),
[Rivaud/Pachet2017](https://arxiv.org/abs/1711.10436),
[AWRS2025](https://arxiv.org/html/2504.05410v1),
[Twister2026, §3/4](https://arxiv.org/html/2609.35609v1).

`work/theory.md` formula a lei, a vantagem comparativa e suas fronteiras.
Cópias independentes vêm SOMENTE de24/v3/source.zip, commit3f0ae1b; hashes
registrados em `work/reference-origin.json`. Nenhum import de tentativas
mutáveis. O núcleo de produção e o experimento24 em execução não são alterados.

## Primeira validação (sem timings competitivos)

Seis testes independentes enumeram a lei dos sorteios efetivos. A suíte
atual passa80 testes (`make test`,36.413s). Após acrescentar recusa explícita
do reconhecedor JSON por falta de pilha, os seis testes da tentativa passam
novamente (0.226s); a recusa não é tratada como invalidez. Lint/format das
cópias e novos módulos passam. `make check` passa upstream/lint/types e
preservação25 tentativas/60 versões; isso não confirma benefício científico.

O corolário `work/counter-separation.md` compara também com counter-only
na família de prova e explicita por que counter+CARS pode obter a mesma
ordem. Ele entra como baseline obrigatório antes do protocolo de timings.
`adaptive.py` paga todos os d tentados, usa gramática-hit se já certificar
aceitação e conserva fallback completo. Ainda não foi cronometrado contra
controles com logits de modelo. Nenhuma vitória de24 é resultado de25.
