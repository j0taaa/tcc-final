# A32 — Acoplamento nativo por classes com orçamento de oráculo

Iniciada2026-10-11. Candidata, NÃO novidade/publicação confirmada. Independente
de31/v3; seu piloto negativo não é convertido em evidência desta operação.
Antes de implementar, o contrato e as oito perguntas são registrados abaixo.

1. **Uso real.** Dois candidatos JSON/DSL de uma dLLM com EPIC completo e
   verificador/dry-run. Retém literalmente o primeiro candidato e altera
   dependência entre candidatos, preservando cada lei nativa inclusive a
   ordem usada na recuperação. Ruídos adicionais do mesmo head são baratos
   relativamente a forwards, mas seu custo entra completo. Pass@1 não muda.
2. **Relevância/diferença.** Bernoulli factories, Barker, Dirichlet, dependent
   rounding e antithetic sampling são conhecidos. Candidata: limiar MÍNIMO
   de quatro draws p-blind para melhoria estrita de cobertura, limite ótimo
   por orçamento e realização adaptativa ótima nesse limite com menos de
   um draw auxiliar esperado. A aplicação trata o sampler nativo finito como
   oráculo e não substitui sua lei por PL ideal. A suficiência deste recorte
   para artigo ainda exige revisão de antecedentes e uso real competitivo.
3. **Escolha.** Sem avaliar a probabilidade verdadeira das classes, mantém
   a lei nativa inteira e a primeira resposta. Para toda propriedade final,
   pass@2>=iid do MESMO decoder e variância média<=iid. Um efeito que distingue
   duas classes equilibradas ganha6.25 pontos percentuais de cobertura local
   (0.75->0.8125), NÃO medição de acerto neural. Comparadores: EPIC iid2/iid4,
   A31/root/history, antitéticos com probabilidades conhecidas, CARMS/CDF,
   repair de colisões por palavra e diversidade completa quando aplicável.
4. **Matemática.** Oráculo iid arbitrário P, projeção binária c e primeiro
   draw inalterado. Segundo draw independente; só em colisão de classe, um
   proposal e um coin adicional tentam trocar para a classe oposta. Provar
   marginais, covariância, custo, limite de Bernstein para n draws, otimalidade
   n=4 e corolário adaptativo Markov/CFG. NÃO lower bound de algoritmos que
   conhecem p, acessam densidades/side information ou mudam a marginal.
5. **Validação honesta.** Enumeração independente de TODOS draws em pequenos
   P/projeções/funções e kernels adaptativos; não benchmarks inventados.
   Primeiro replay nativo com heads falsos e fonte pinada; depois protocolo
   externo congelado, dados/seed/gates definidos antes de heads. Preservar
   todos fracassos. O piloto31 tem casos fáceis e NÃO confirma32.
6. **Custo completo.** Até dois draws auxiliares por encontro, esperado
   1-p(1-p)<=1; inclui classificar e armazenar chave e D2H/H2D. Nenhum forward
   auxiliar para coordenar; mais diversidade pode causar MAIS forwards
   únicos e reduzir caching. Contabilizar isso, preparação e verifier/saída.
   Overhead tem limite determinístico; ele não prova latência total menor.
7. **Objeções.** Saber p permite antitéticos mais fortes; a bound só vale ao
   acesso p-blind declarado. Classificação sem relação com o valor futuro
   dá ganho zero. Sampler4 draws é ruído, não quatro gerações completas, mas
   iid4 é comparador importante na fronteira de custo. Agrupar outras partes
   do estado incorretamente pode perder garantias. Mesmo efeito já conhecido
   ou alternativa exata mais barata pode refutar novidade. Rejeitar direção
   se for só aplicar uma fábrica/Barker sem resultado distintivo útil.
8. **Artigo.** Faltam conferir fontes primárias, provar limite/gain, encontrar
   contraexemplos, implementar referência mínima e testar utilidade externa.
   Nada disso é concluído apenas por criar este README. Não há revisão humana,
   aceitação ou superioridade geral sobre EPIC. Não modificar vendor/31.

## Estado

Contrato: sampler finito nativo de ruído/ordem, não posterior CFG nem MWPC.
Projeção/posição dependem só do estado/head e política comum, nunca de gold.
Massa da classe serve à análise, NÃO é input exigido do algoritmo.
Uma ordem inteira retorna de um draw original; não trocar só o vencedor.
As fontes de31/v3 permanecerão congeladas. Copiar apenas fonte pinada com
hash/atribuição se necessário; não importar sua implementação mutável.

## Gate inicial executado

`work/theory-v1.md` contém a prova escrita e o limite oracle-only. Quatro
oráculos independentes passam0.766s: todas as classes/distribuições pequenas,
eventos/scores, orçamento e729 sequências de kernels adaptativos. O limite
contra métodos que sabem p NÃO é reivindicado. Antecedentes e pendências em
`work/antecedents-v1.md`; novidade do limite específico ainda aberta.

`work/probe_native.py` executou216 casos do EPIC pinado, com heads FALSOS:
216 primeiras trajetórias iguais, inclusive recuperação/EOS/rejeições e
isolamento de RNG CPU/CUDA;156 nós compartilhados,128 draws auxiliares,
978 calls FALSAS. Todos hashes em `work/evidence/native-fake-v1.json`.
O draft que falhou por device CUDA implícito está preservado separadamente.
Nenhum forward neural novo nem timing competitivo para32 até este ponto.
Classe binary cumula CDF do head somente para escolher uma partição antes
do ruído; essa estimativa NÃO é usada como probabilidade verdadeira na troca.
Cada troca devolve o vetor de ruído original inteiro do row, sem cortar cauda.
Suíte offline127 testes passa65.861s; Ruff explícito dos novos fontes passa.

## Refinamentos v2/v3, preservando v1

`work/theory-v2.md` e `work/walk.py` estendem o orçamento finito sem adicionar
FAIL ou aproximar a lei original. Referência compacta de pool em `work/pool.py`
tem a MESMA lei ótima e memória O(V), também: não usamos um pool ingênuo
como único adversário. O walk economiza calls, mas o pool vetorizado pode
ser fisicamente mais rápido. Seis novos oráculos passam1.650s: TODOS bits
até n=12, marginais completas/aliases e RNGs do pool, custo e um contraexemplo
de que mais energia local pode PIORAR cobertura final. Toda suíte133 passa
67.804s.432/432 replays FAKE CPU/CUDA preservam primeira trajetória/RNG,
312 encontros1024 draws auxiliares1956 calls FALSAS. Fontes/SHAs e todos
registros em `work/evidence/native-fake-v2.json`; nada é modelo neural novo.

A revisão encontrou um antecedente MAIS próximo: Nacu–Peres2005,
Section6/Proposition24, realiza por first passage o polinômio Q_n, e
B_n=Q_n-p. Isto é uma redução exata. A construção de caminhada/Bernstein
NÃO é novidade nossa. `work/antecedents-v2.md` explicita o que foi lido,
incluindo slides primários2025 e acesso ainda ausente ao manuscrito2026.

As oito perguntas foram reavaliadas em `work/minimax-v3.md` ANTES da otimização
de árvores. Candidata mais forte: para TODO método p-blind adaptativo com
orçamento n que preserve B1, marginal p e atinja B_n para todo p, o custo
esperado minimax é EXATAMENTE floor(n/2)+1, atingido pela referência. Não é
comparação apenas contra pool fixo. Nem lower bound para métodos que sabem p,
velocidade EPIC, dados balanceados com side information ou novidade conferida.

O adversário `work/stopping_tree_lp.py` otimiza TODAS árvores pequenas sob
coeficientes da lei para TODO p (não só a marginal numérica observada).
54 casos n=2..10/p predefinidos: zero contraexemplos numéricos,36 certificados
duais RACIONAIS verificados exatamente,18 reconstruções não certificadas.
Isto NÃO prova otimalidade pontual para qualquer n/p, nem prioridade.
Comando opt-in pinado SciPy1.16.3/NumPy2.4.6 e fonte preservados em
`work/evidence/stopping-tree-v3`. Sem novos heads/ganho competitivo para32.

Continua faltando benefício prático independente e novidade específica
suficiente. A resposta não é esconder Nacu–Peres nem executar um benchmark
favorável: primeiro fechar o resultado próprio e o comparador competente.

## V4 — aplicação pública numérica, protocolo antes de heads

`work/protocol-v4-inputs.md` reavalia as oito perguntas; `protocol-v4.md/json`
fixam métodos, custos, sementes e gates antes de novos forwards.32 perguntas
train e64 test do GSM8K oficial pinado são escolhidas só por hash da pergunta;
seleção não acessa valores de respostas, embora os arquivos públicos baixados
contenham ambas. A gramática aceita qualquer número, sem catálogo do gabarito.
JSON numérico é subclasse regular de GLC, não teste de recursão geral.

Inclui EPIC completo iid2/iid4, temperatura mista/determinística, raw-ticket
root/history/state pinados de31, pools compactos e vetorizados e um controle
known-p competitivo (aproximação PL contínua declarada, não lei finita exata).
Classe numérica só projeta ruído e não poda IDs. Nenhum novo forward A32
foi produzido ao preparar este contrato; confirmação é condicional ao gate.

864 replays de heads FALSOS passam com primeira trajetória e RNG preservados,
588 encontros4916 draws auxiliares3900 calls falsas, registrados em
`work/evidence/native-fake-v4.json`. Smoke separado atravessa wrapper completo
com126337 IDs falsos:32 configurações/68 respostas. Draft original preservado
com seus hashes, antes da anotação ClassVar. Dois novos testes independentes
de avaliação JSON numérica passam; toda suíte135 passa68.297s.
Isto valida fronteiras de implementação, não novidade, acerto real ou timing.

## V4 — piloto real encerrado com resultado negativo

Produtor congelado `8fc0999736724b7b28159653503693f95b272c4a`:1056/1056
registros,2208 JSONs válidos,32.716 novos forwards, nenhum erro/recusa ou
divergência da primeira trajetória. As OITO candidatas acertam20/32, igual
a iid2 nas duas temperaturas, com custo wall/CPU maior. Misto acerta21/32
com menor custo; iid4 acerta23/32 a0.5 e22/32 a1, com custo maior.

O screen negativo definido ANTES de medir encerra esta aplicação. Não foram
executados os outros três seeds nem aberta a avaliação test. Uma seed NÃO
refuta estatisticamente o método inteiro, mas tampouco fornece o benefício
exigido. Não retunar a classe/seleção nesta evidência para fabricar ganho.

Todos os dados, inclusive custos de escrita/flush, estão preservados em
`work/evidence/external-pilot-v4`; `analysis/audit_v4.py` recalcula a igualdade
numérica com Fraction/JSON estrito, confere1056 identidades e a primeira
trajetória, e soma os custos I/O. Metadados registram hardware/modelo/vendor
e hashes. O pool vetorizado state a1 acerta22/32 nesta seed, mas tem a MESMA
lei conjunta do walk16: não interpretar essa diferença RNG como melhor
qualidade esperada de uma dessas implementações.
