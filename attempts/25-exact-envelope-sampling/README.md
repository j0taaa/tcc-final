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
perdas. A kernel25/v1 foi congelada ANTES das capturas externas de24; o gate
de24 autorizou essas capturas.25 pode reutilizar essas cabeças explicitamente,
sem chamar isso de novos forwards ou dados ainda não vistos por24. Sua seleção
ocorre somente no desenvolvimento. Não reaproveitar timing de A24 como vitória
desta operação diferente.
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

## Reavaliação do contrato e comparador forte, antes de timings25

As oito respostas anteriores continuam sendo critérios, com estas correções
específicas. **Uso/garantia:** respostas aceitas têm lei local exata; orçamento
finito k inclui estado FAIL, e sua trajetória só tem TV<=sum delta_t^k contra
o decoder de produtos congelados. Não alegar igualdade incondicional de uma
trajetória interrompível (`work/finite-budget-trajectory.md`). **Comparador:**
counter+CARS leve/perfeito também foi implementado, com término de propostas
no primeiro prefixo impossível e aprendizagem de TODOS irmãos inválidos;
não cobrar o resto de uma proposta que já pode ser rejeitada. Seis oráculos
verificam os sorteios efetivos nas quatro configurações,0.248s.

**Antecedente mais próximo do princípio geral:** OS* (Dymetman, Bouchard e
Carter2012), [§2 e §3.2, fonte original](https://aclanthology.org/W12-6106.pdf),
já faz amostragem exata mediante propostas superiores computáveis por DP,
com refinamento e aplicação à interseção PCFG/LM. Portanto amostrar por um
envelope/refinar uma abstração não é a invenção. O recorte candidato é a
fronteira gramatical token-original/first-overflow com fechamento, certificado
antes da primeira proposta e separações ESPECIFICADAS. Uma variante OS* pode
usar este mesmo envelope e compartilhar a vantagem. A tese não separa o
método de todo OS*, CFG compacto ou counter+CARS; custos desses controles
são indispensáveis, e a significância/prioridade específicas seguem abertas.

**Teste honesto/custo:** `work/protocol.json` declara13 métodos, todos18
estados antigos, primeira amostra exata sem cobrar marginais desnecessárias
aos controles, lote32 separado, custos completos, três/nove rotações e
critério forte20% wall E CPU/todos adversários/sinal favorável. A kernel25/v1
foi congelada antes dos forwards externos de24; reutilizar esses inputs será
explicitado, sem fingir novas capturas. Nenhum timing25 foi feito.

**Objeções/artigo:** o híbrido pode vencer, e o bound genérico é conhecido.
A família de prova não será executada como benchmark de vitória. Registre
leis, limites de recurso e falhas separadamente. Falta confirmar velocidade,
uso iterativo e redação científica, além da revisão humana inexistente.

## Refinamento v2 e fronteira formal

`work/empty-lower-addendum.json` registra uma correção estática antes de
QUALQUER timing25: com massa rasa zero, não computar um bound que só pode
ser1 ou indefinido. Refinar e manter fallback completo; a API direta de cauda
sem requisito de certificação continua funcionando. Sétimo oráculo independente
verifica essa distinção. V1 permanece imutável. V2 foi preparado DEPOIS das
capturas compartilhadas24 e ANTES das medições25; não dizer que seus inputs
eram desconhecidos por24. Casos, seeds, controles e gate não foram alterados.

`formal/MWPC/ExactEnvelope.lean` verifica sete identidades/limites de contagem
para rejeição finita; `CertifiedAmplification.lean` verifica duas comparações
algebraicas do corolário24. `make check-formal` completo passou; evidência
em `work/evidence/formal-v2`. Não é verificação do Python, da cobertura de
gramática, do backbone ou do acoplamento global escrito. O oráculo13-worker
verifica a mesma operação de primeira amostra e evita atribuir a ela uma
recusa observada apenas depois no lote. Timings competitivos continuam pendentes.
