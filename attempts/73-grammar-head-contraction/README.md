# A73 — Contração do head por invariantes de palavras

Base: `84b3496952243f2a5b3c5dd2d31191073be3a304`, branch própria, 2026-10-19.
Investigação delimitada; nenhuma novidade ou aceleração neural estabelecida.

## Operação, hipótese e consumidor

Dados n slots fixos, EOS/PAD ausentes, hidden states H e head compartilhado W,
retornar **um MAP conjunto** dos IDs originais em uma linguagem finita L não
vazia, maximizando Σ_i(h_i·W[y_i]+b[y_i]). O consumidor é uma proposta completa
de um passo de infilling com todos os campos comprometidos simultaneamente.
Não usa confidências por posição, não mantém o scheduler EPIC/FactorDLM e não
promete qualidade semântica nem a trajetória nativa. É `exact_on_support` da
linguagem declarada, não inferência no vocabulário completo sem restrição.

Compilar U_v=span_Q{x_v(y)-x_v(z)} a partir de um forest AND/OR produtivo,
finito e sem ciclos, com alternativas do mesmo escopo e produtos de escopos
disjuntos. Uma base em forma escalonada reduzida B_v tem colunas pivôs J_v e
D=B_v^T D[J_v]. Avaliar somente (B_v H) W_v nos pivôs, com bias (B_v 1)b_v.
Isso preserva diferenças de escores; uma constante por linguagem foi omitida.
A [prova escrita](proof.md) delimita também a consequência para Gibbs ideal,
que não é uma implementação de amostragem exata com floats.

## Antecedentes e diferença candidata

Fontes primárias consultadas em 2026-10-19:

- [Müller-Olm–Seidl, POPL 2004](https://www2.in.tum.de/bib/files/Muller-Olm04Precise.pdf):
  análise precisa de relações afins por álgebra linear. O cálculo de um affine
  hull não é invenção desta tentativa.
- [Li–Eisner, EMNLP 2009](https://aclanthology.org/D09-1005/): semirings de
  expectativas e covariâncias em forests. Sob pesos positivos, o núcleo da
  covariância de indicadores identifica as mesmas relações afins; é outra
  construção clássica do objeto. Não atribuir a eles contração de LM-head.
- [Ciobanu–Zetzsche, 2024](https://arxiv.org/abs/2405.07911): fechos de linguagens
  indexadas e equações de palavras com contagens; a discussão de affine hulls
  de conjuntos semilineares remete à análise afim clássica.
- [GPIO, ENGINE](https://github.com/AwaleSagar/gpio-llm/blob/main/docs/ENGINE.md)
  §§Grammar/What it does: projeta somente IDs legais e omite decisões forçadas.
- [GSP, v0.1.1](https://github.com/StealthEyeLLC/grammar-sparse-projection/tree/v0.1.1):
  projeção esparsa anterior à normalização, com runtime GPU. É controle de
  seleção de linhas, não evidência de que já implemente invariantes entre slots.
- [FactorDLM](https://arxiv.org/html/2609.32900v1), §§3.1–3.3: eliminação exata
  com unárias e confidências originais; Proposição 2 é quociente de classes.
  Substituir variáveis iguais e somar unárias é controle competente; antecipar
  essa soma através de um head linear já dá o pooling do exemplo de cópia.

A20/A28/A36 são antecedentes internos negativos/controles, não novas aplicações
a reabrir. A diferença candidata é extrair automaticamente relações **entre
posições** antes de projetar, inclusive relações além de igualdades simples.
Não se encontrou nestas fontes uma demonstração dessa integração específica;
isso não estabelece prioridade, e compor mecanismos conhecidos pode ser
insuficiente como contribuição. A identidade de pooling de cópia é elementar.

## Benefício verificável e comparadores

Comparar a MESMA operação MAP, mesmas palavras e mesmos hidden states:
head denso apenas nos slots livres + solver especializado; head legal-ID
esparso + mesmo solver; pooling manual por igualdades antes do head; e a
compilação A73. Flattening de igualdades antes do head recebe a mesma otimização
linear do pooling manual. Não chamar um controle que recebe todos os logits de
limite inferior do FactorDLM otimizado. GPIO/GSP são princípios implementados
por GEMMs PyTorch competentes aqui; não são benchmarks dos runtimes originais.

No exemplo de cópia, q_v=1 para cada ID: r|D| produtos viram |D|, mas o pooling
manual já faz exatamente isso. Em escolhas independentes, q_v pode ser n e a
contração não economiza nada. Um caso de contagem balanceada, sem igualdades
entre posições, testa a diferença algébrica além do pooling. Ele não é prova
de utilidade em uma tarefa natural de geração.

## Custo e objeções

Contar aquisição/validação dos bytes/IDs, construção do forest, anchors,
eliminação racional, grouping de B, bits e memória; carregamento de modelo,
backbone inteiro, seleção/conversão de linhas W, transformações de H, head,
solver, transferências e serialização da saída. MAP usa zero RNG online;
seed de construção não é custo de amostragem escondido. Reutilização precisa
pagar preparação e declarar o número de consultas, incluindo Q=1.

Com M contando nós **e arestas**, iterar ingenuamente todos os IDs pode custar
O(M V n^3) operações racionais. A versão esparsa aqui examina somente os <=2n
IDs nos dois anchors de cada aresta OR: são O(Mn) geradores, com inserção
incremental O(n²) por gerador, portanto O(Mn³) operações de corpo no total,
além de grouping/ordenação. Anchors explícitos podem ocupar O(Mn).
Diferenças de indicadores têm entradas em {-1,0,1}; uma base escolhida dessas
diferenças admite determinantes e numeradores de O(n log n) bits por Hadamard.
Usar RREF não elimina custo de bits nem custo dos intermediários.

Online, grupos idênticos de B custam O(d Σ_g nnz(B_g) + d Σ_v q_v), contra
O(d Σ_i |D_i|) no sparse legal; dense nVd é um comparador adicional. Formas
reais de tensores, gather, alocação e GEMV versus GEMM podem inverter a vantagem.
Permitir preprocessar/misturar linhas de W invalida o modelo restrito do limite
de consultas. Não há alegação de ótimo universal/GPU nem de lower bound de MAP.

Aliases de bytes continuam IDs distintos: em igualdade por bytes, a melhor
pontuação de uma classe é a soma dos máximos por posição; sua massa é o produto
das somas exponenciais. Não substituir por igualdade de IDs. A prova é ideal;
fl((Σh)W) pode diferir de Σfl(hW). A avaliação numérica deve certificar o MAP
ou retornar inconclusivo; igualdade entre dois argmax floats não é certificado.

## Gates e escopo

Primeiro: prova escrita, compilador e oráculos exatos independentes, recusas de
forests inválidos, ambiguidade, aliases, bias, fixações e ausência de economia.
Depois: [protocolo operacional](protocol.md) congelado em commit ANTES de
qualquer timing. Modelo local em leitura, nenhum treinamento/download de pesos.
Todos os timings e todo uso de GPU sob lock exclusivo
`/tmp/tcc-final-candidate-tests-gpu.lock`, com `nvidia-smi` e sem concorrência.

Gate científico exige uma diferença suficientemente delimitada e consumidor
útil além de uma identidade clássica. Gate operacional exige MAP certificado
e ganho integral >=20% contra TODOS os controles, inclusive pooling, pagando
setup e amortização declarada. Perder para pooling não pode ser compensado
selecionando vitória contra dense. Falhas, recusas e interrupções são resultados
preservados. Se gates falharem, encerrar esta campanha sem expandi-la.
