# A29 — Reparo estacionário de colisões entre duas amostras

Investigação independente iniciada em2026-10-11. **Candidata, não conquista
confirmada nem novidade suficiente para publicação.** Não herda os ganhos
de A24, A26 ou A28. Não modifica o EPIC ou o núcleo mantido.

## Critérios de decisão antes do protótipo

1. **Uso real.** Produzir dois candidatos JSON/DSL para validação/dry-run,
   preservando as duas leis originais de uma predição de dLLM condicionada
   por GLC. A operação extra só ocorre quando os candidatos originais são
   idênticos. O primeiro permanece literalmente intacto. O verificador não
   participa da escolha. O objetivo é cobertura, não pass@1 ou latência.
2. **Relevância e diferença.** Metropolis–Hastings, formas de Dirichlet,
   modificação antitética e inferência gramatical são antecedentes. A diferença
   candidata é um transformador implícito de pares de leis possivelmente
   diferentes: uma proposta adicional no máximo, somente em colisões, duas
   densidades não normalizadas e dominância para todo verificador. Ainda é
   necessário decidir se este algoritmo/contrato já está coberto por um
   antecedente e se a consequência prática tem tamanho suficiente. Uma
   prova curta e código pequeno não estabelecem suficiência acadêmica.
3. **Por que escolher.** Mantém P e Q individualmente e melhora fracamente
   pass@2 para TODO conjunto aceitável. Há ganho estrito quando o conjunto
   e seu complemento intersectam o suporte comum de P/Q. Pode reutilizar
   amostras e planos existentes sem preparar o posterior P·Q. Comparadores:
   par independente, estratificação/arithmetic sampling, CARMS, modificação
   antitética de Neal e amostragem sem reposição. Os últimos não são adversários
   fracos: podem ter ganhos maiores. A29 não demonstra superioridade sobre
   essas alternativas, sobre EPIC ou em custo total.
4. **Prova sem código.** `work/theory-v1.md` define a transformação geral por
   qualquer kernel estacionário para a lei de colisão; deriva preservação,
   covariância não positiva e ganho de cobertura. A implementação particular
   usa MH com proposta P e razão Q(z)/Q(x), sem normalizador ou enumeração.
   O corolário CFG usa produtos dos pesos ORIGINAIS por posição; aliases
   não podem ser confundidos com uma mesma sequência de bytes.
5. **Experimentos honestos.** Primeiro, enumeração independente de todas as
   decisões aleatórias em distribuições racionais pequenas, incluindo leis
   diferentes, suportes parcialmente disjuntos e TODOS os verificadores.
   São oráculos de correção, não benchmarks. Não executar seleção/timing
   competitivo antes de congelar protocolo, custos e controles próprios.
6. **Custo completo/dLLM.** A transformação não adiciona forward quando P/Q
   já são posteriores de um passo. Acrescenta até uma chamada ao sampler P
   e duas avaliações de peso Q; custo esperado extra ponderado pela chance
   de colisão D. Todas essas operações, preparo e aritmética em bits precisam
   entrar numa comparação. A lei de um passo não é a lei final de qualquer
   decoder. A extensão adaptativa exige a MESMA política futura nos grupos
   de históricos completos idênticos; duas políticas futuras diferentes não
   recebem automaticamente a garantia terminal.
7. **Objeção decisiva.** Em espaços amplos D pode ser minúsculo. Ren et al.
   (ICML2019, teorema1) já limita ganho universal de variância para uniforme.
   Uma redução a métodos antitéticos existentes, ou ganho desprezível em
   uso útil, derruba esta candidata como protagonista. Não esconder a amostra
   adicional nem afirmar vitória de compute contra três amostras iid. Se a
   aplicação permite simplesmente validar três saídas, essa alternativa entra.
8. **Artigo defensável.** Faltam prioridade delimitada, magnitude útil,
   integração neural e custo competitivo. A prova escrita precisa de revisão
   adversarial e oráculos; não há revisão humana, formalização ou experimento
   externo desta tentativa. Não promover antes dessas obrigações.

## Arquivos

- `work/theory-v1.md`: definições, prova e fronteiras.
- `work/antecedents-v1.md`: fontes primárias e possíveis reduções.
- `work/coupling.py`: referência racional com interfaces de sampler/peso.
- `tests/test_collision_coupling.py`: oráculos finitos independentes ativos.

Nenhum peso, cache ou código mutável de outra tentativa é importado.

## Primeira auditoria e decisão

Cinco oráculos passam (`.venv/bin/python -m unittest
tests.test_collision_coupling -v`,0.553s):361 pares de distribuições,2.888
verificadores e9.747 pontuações racionais; lei por enumeração de todas as
decisões aleatórias, não frequências. Incluem oito eventos JSON originais
com aliases, recusa de pesos inexatos/incompatíveis, avaliação preguiçosa,
reparo ingênuo com marginal errada e um contraexemplo de políticas futuras
diferentes. Ruff explícito passa. Nenhum forward ou benchmark foi executado.
Toda a suíte offline atual passa:109 testes em39.529s (`make test`).
`make check` também passa, incluindo integridade das75 versões já congeladas.

A seção7 da prova encontra uma limitação decisiva de TODA esta família:
ganho de cobertura é limitado pela menor massa de colisões dos dois lados
do evento. Para uma alternativa rara de massa epsilon, o teto é epsilon²,
contra epsilon(1-epsilon) de um acoplamento direto competente. Portanto,
**não promover o reparo de palavras como protagonista nem iniciar uma
campanha extensa só pela dominância sobre iid**. A transformação e sua
prova ficam preservadas. O objetivo de publicação continua em aberto.

## Correção científica posterior, 2026-10-11

A comparação rara do parágrafo anterior e de `theory-v1.md`, seção7, está
INCORRETA: o teto epsilon² vale para TODO acoplamento que conserve as duas
marginais. Não existe o ganho epsilon(1-epsilon) ali atribuído ao comparador.
Veja `work/erratum-2026-10-11.md`, com demonstração e consequência: o MH de
A29 atinge1-epsilon do máximo nesse caso binário. As provas e decisões antigas
permanecem preservadas; a objeção errada não pode ser usada novamente.
Novidade, benefício de custo e aplicação suficiente continuam não confirmados.
