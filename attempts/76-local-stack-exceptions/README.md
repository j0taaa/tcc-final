# A76 — Exceções locais de efeito de pilha

## Decisão após o protocolo V1

**Não selecionar A76 nesta formulação como contribuição central do TCC.**
O gate barato aceitou **0/6 capturas reais** e **0/6 sondagens estruturais de
tokenizer**. Há uma redução matemática condicional consistente e o gadget foi
reproduzido, mas não há cobertura real elegível, ganho próprio sobre o controle
especializado ou medição neural integral. Não foi construído um solver amplo
depois dessa reprovação; não foram inventados novos casos ou top-k para salvar
o resultado. Isso não é uma impossibilidade universal de compilar Dyck/BPE.

Protocolo e produtor foram congelados em **`f88e8ade`**, antes de executar.
[results-v1.json](results-v1.json) é a primeira execução, preservada; o replay
em arquivo novo reproduziu seus bytes integralmente. Não houve falha de
execução, correção de dados, novo forward, uso de GPU ou benchmark de tempo.
O requisito de aguardar a liberação do coordenador para timings/GPU foi
respeitado: a decisão decorre de auditoria offline, sem depender de recursos.
A liberação chegou durante os checks; o gate negativo foi preservado, sem
iniciar medições ou ampliar o corpus depois dessa mensagem.

### Cobertura efetivamente encontrada

LLaDA: todos os **126.080 IDs ordinários**, 839.137 bytes de emissões, **73
efeitos externos** distintos; 269 IDs adicionados ficam explicitamente fora.
Qwen: **151.643 IDs ordinários**, 975.969 bytes, **85 efeitos**, 27 IDs
adicionados excluídos. Foram verificadas 277.723 decodificações com o decoder
original `tokenizers`, incluindo bytes UTF-8 parciais via a mesma substituição
de exibição. Os bytes brutos são preservados pelo adaptador composicional;
não se retokenizam sequências. Nenhum token ordinário desses dois artefatos
teve mismatch interno irreparável. Os maiores grupos de mesmo efeito têm
123.757 IDs no LLaDA e 146.544 no Qwen. Não se somam
probabilidades desses IDs.

As sondagens de n=32,128,512 usam todo o suporte ordinário em cada slot,
sem pins: não há efeito determinado que ofereça um guard. Independentemente
do principal, cada slot tem mais de duas classes e vira exceção. Logo
LLaDA dá Q=73^n (199, 793 e 3.170 bits, respectivamente) e Qwen Q=85^n
(206, 821 e 3.282 bits). Todos excedem Q<=4096 e k<=8, já no menor n.
São auditorias de suporte de tokenizers reais, não capturas de logits nem
amostra estatística de todos os usos desses modelos.

As seis capturas preexistentes LLaDA p0/p1, n=33,129,513 preservam os IDs
`[7,8,58,60,2]`, bytes `(`,`)`,`[`,`]`,`#`. Não há pins, cada slot tem cinco
efeitos, nenhum guard e k=n. Portanto Q=5^33, 5^129 e 5^513 (77, 300 e
1.192 bits), para ambos os prompts. A massa omitida varia, sobre todas as
posições, de aproximadamente **0,72538666 a 0,99999829**. Os limites racionais
por frame estão nos dados; nenhuma cauda foi renormalizada. O argmax guardado
é explicitamente sobre esses cinco IDs; a captura não permite reconstruir a
proposta de vocabulário inteiro. A reutilização desses logits testa a nova
parametrização A76, sem reexecutar nem alterar a aplicação A72.

As doze recusas são **REFUSED_PARAMETER**: nem inviabilidade, nem timeout,
nem recusa por memória, nem seis perdas de latência fictícias. Nas capturas,
n repetições do ID original 2 (`#`) já dão uma completação válida em Dyck3
com bytes neutros. O gate não inclui contração
global por um parser nem suporta guards arbitrários: seu produtor declara a
hipótese verificada de suporte idêntico em todos os slots e não fixado. Um
compilador mais amplo exigiria outro protocolo, e não foi desenvolvido aqui.

### O que os testes pequenos sustentam

A normalização concordou com uma pilha independente em **19.608 palavras**,
13 contextos e **254.904 comparações**, incluindo `[](`, `{}(` e mismatch
interno. A enumeração conferiu **428 sistemas** de prefix bounds até m=5 e
**80.308 pares I/Z** disjuntos, sem contraexemplo à alegação de extensão.
Esses testes não são uma prova de todo compilador nem verificação Lean.

Há também uma prova escrita curta desse passo, independente dos casos:
Z independente em M* equivale a E\\Z conter uma base de M, logo a restrição
M|(E\\Z) tem rank r. I independente em M e disjunto de Z é independente
nessa restrição. Pela extensão de independentes a bases, existe uma base
de M|(E\\Z) que contém I. A volta é imediata. Isso justifica a soma direta
para propostas de classe 1 em P e classe 0 em N disjuntos; não justifica
aceitar dois IDs distintos propostos no mesmo slot.

Para bases com prefix>=L_j, I é extensível iff
|I intersect (j,m]|<=r-L_j para todo j. Z é coindependente iff
|Z intersect [1,j]|<=j-L_j e |Z|<=m-r. Preencher posições disponíveis mais
à esquerda prova a suficiência dos bounds. São duas famílias de capacidades
em cadeias, com greedy clássico, range-add/min e ordenação em O(m log m),
sob comparação aritmética unitária. Este raciocínio sustenta o núcleo
condicional do custo declarado; não demonstra um compilador geral de tokens,
prioridade ou desempenho real. Os testes V1 enumeram bases, não implementam
esse data structure otimizado nem todos os perfis do compilador pretendido.

O gadget tem exatamente `(())`, `()()` e `[()]`. Greedy por viabilidade
escolhe posições 3 e 1, valor **4,1**; o ótimo sob cap 2 escolhe 2 e 4,
valor **6**, testemunho `[()]`, com IDs ASCII originais nessa fixture
explicitamente sintética. Seu perfil por cap 0..4 é `(0,4,6,6,6)`.
O teste também reconstrói testemunhos `{[()]}^F`, F=1,2,4,8, reconhecidos
por pilha; preserva Q_f=4, soma Q_f=4F e enumeração global 4^F.

O controle especializado recebe esses mesmos guards e resolve 16 atribuições
locais por gadget, custo O(F) sem quota ativa. Com cap ativo usa o mesmo
max-plus; neste gadget idêntico o perfil tem até a fórmula direta
4 min(b,F) + 2 min(max(b-F,0),F). Os perfis foram comparados com essa fórmula
e, para F<=2, com enumeração independente da palavra inteira. Portanto a
separação contra 4^F global ou contra greedy 4,1 **não** separa A76 do controle
competente. Nenhuma latência de candidato/controle foi medida.

A auditoria de prioridade continuou após o gate, sem alterar seus casos.
[Hans Leiß, An Algebraic Representation of the Fixed-Point Closure of
*-Continuous Kleene Algebras](https://www.cis.uni-muenchen.de/~leiss/MSCS-2020-072.R2.rev279.pdf),
página 11 do PDF, explicita a forma normal do monoide policíclico:
fechamentos antes de aberturas, ou zero por mismatch. É precisamente o
antecedente algébrico do resumo popword/pushword, com bytes neutros apagados.
Portanto nem essa normalização é uma primitiva nova da tentativa. Essa
fonte acrescenta uma atribuição; não transforma os testes em prova de novidade.

### Custos, alcance e reprodução

O auditor leu os dois tokenizers e suas configs, percorreu 1.815.106 bytes de
emissões ordinárias, construiu classes com todos os IDs e fez as contagens
finitas acima. Q foi contado em inteiros, não enumerado. Hashes dos inputs,
do produtor e da tabela (ID, bytes, efeito) estão no resultado, junto aos IDs
de controle excluídos. Os operandos racionais das capturas chegam a 53 bits
no numerador e 77 no denominador (máximos por frame registrados). Não houve
RNG, treinamento, consulta ao modelo, leitura de pesos, transferência CUDA
ou nova geração de logits. Os custos históricos de captura não são timings
A76. RSS e tempo de preparação/saída não foram medidos; não há comparação
integral de velocidade nem estimativa que os considere gratuitos.

Para um solver eventual cobrar também modelo/head, preparação, transferência,
validação independente de IDs/bytes/pins/objetivo, bit comparisons, memória e
saída. O perfil condicional declarado não promete vocabulário pleno eficiente.
Nenhum arquivo do vendor, biblioteca, dados históricos ou outros worktrees foi
editado; não foram baixados pesos ou instaladas dependências.

Reprodução offline com Python 3.11 e `tokenizers` já existente no ambiente
compartilhado, consultado em leitura. A saída deve ser NOVA:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/src" \
  /home/jota/projects/tcc-final/.venv-a52/bin/python \
  attempts/76-local-stack-exceptions/audit.py \
  --output /tmp/a76-gate-replay.json
cmp attempts/76-local-stack-exceptions/results-v1.json /tmp/a76-gate-replay.json
PYTHONDONTWRITEBYTECODE=1 /home/jota/projects/tcc-final/.venv/bin/python \
  -m ruff check attempts/76-local-stack-exceptions
PYTHONDONTWRITEBYTECODE=1 /home/jota/projects/tcc-final/.venv/bin/python \
  -m ruff format --check attempts/76-local-stack-exceptions
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' PYTHONPATH="$PWD/src" \
  make check VENV_PY=/home/jota/projects/tcc-final/.venv/bin/python
```

O replay e lint/formato da tentativa passaram. **`make check` passou**:
snapshot EPIC, lint/formato, tipos e **345 testes**. Os testes de manutenção
são verificações offline; sua duração não é benchmark científico da candidata.

## Registro anterior ao gate

Esta tentativa testa uma candidata, sem pressupor descoberta, novidade ou
aprovação. Base: `84b34969`, branch própria. A73 `followup.md` e A75
`report.md` foram lidos nos worktrees indicados pelo usuário, somente em
leitura. Suas aplicações não serão reabertas. O consumidor aqui é MWPC de um
passo após um forward, não posterior nem trajetória nativa.

### Operação e representação

Entrada: slots finitos, suporte de IDs originais, bytes composicionais, pins,
no máximo UMA proposta de ID por slot, pesos racionais não negativos e cap
global b de novas propostas selecionadas. Duplicatas do mesmo ID podem agregar
peso; IDs distintos propostos na mesma posição ficam fora deste contrato.
Saída pretendida: batch de peso máximo com até b propostas e uma completação
reconstruível em Dyck de três tipos, ignorando bytes diferentes de `()[]{}`.
Isso não reconhece JSON, escapes ou semântica de um programa.

EOS/PAD/mask e demais tokens adicionados não emitem bytes nesta operação:
ficam explicitamente excluídos. A cobertura de vocabulário ordinário será
declarada; não se alega cobrir controles. Suporte reduzido é
`exact_on_support`. Nas capturas, probabilidades IEEE salvas são convertidas
exatamente a racionais, sem normalizar a cauda omitida. Se forem necessárias
propostas, escolhe-se argmax dentro do suporte capturado, desempate pelo menor
ID; isso não é o argmax desconhecido do vocabulário inteiro.

Cada token é reduzido isoladamente a (popword, pushword), ou ZERO se um par
interno conflita. Popword lista tipos na ordem de consumo; pushword lista
aberturas do fundo ao topo. Assim `[](` e `{}(` têm o efeito de `(`. Não há
cancelamento atravessando masks. Classes preservam listas de IDs e bytes:
para casar uma proposta escolhe-se precisamente aquele ID, sem somar massas
de aliases. ZERO pode ser eliminado com segurança, pois nenhum contexto o
repara. Ausência de uma solução após essa eliminação não será inferida de um
limite de recursos.

### Antecedentes auditados em fontes primárias

Consultas web desta rodada, em 2026-10-20 UTC, com leitura dos textos abaixo.
Uma busca delimitada não certifica prioridade.

- [Ardila, The Catalan Matroid](https://arxiv.org/abs/math/0209354), teorema
  2.1: posições de up-steps de caminhos Dyck são bases de matroide.
- [Bonin, de Mier e Noy](https://arxiv.org/abs/math/0211188), teoremas 3.3,
  3.5 e 3.6: bases entre caminhos, dualidade e somas diretas. Os bounds de
  prefixo abaixo são uma apresentação dessa estrutura clássica.
- [Bouchet e Cunningham](https://www.math.uwaterloo.ca/~whcunnin/step.pdf),
  seção 2: greedy e consulta de extensão com inclusões/exclusões já estão
  explícitos. Não se reivindica a primitiva greedy como contribuição.
- [Codeforces 3D](https://codeforces.com/problemset/problem/3/D) já pede
  completação de parênteses com custos por alternativa. O tutorial primário
  [OCPC 2025, Kempt Kale](https://assets.ucup.ac/tutorials/tutorials-4-25-en.pdf),
  páginas 42–44, explicita matroide e O(n log n) para brackets ponderados.
- [Das et al., Weighted Edit Distance Computation](https://arxiv.org/abs/2302.04229),
  teorema 1.3: O(n + k_edit^12) para Dyck edit ponderado sob skewmetric.
  É outra operação/parâmetro: propostas todas de fechamento podem ter
  k_struct=0 e distância de edição linear. Não serve como controle direto.
- [Williams, Gomes e Selman, IJCAI 2003](https://www.ijcai.org/Proceedings/03/Papers/168.pdf)
  introduzem backdoors; [Ganian, Ramanujan e Szeider](https://arxiv.org/abs/1507.02479)
  tratam classes dispersas por componentes. Enumerar exceções e resolver
  componentes fáceis tem antecedente explícito, inclusive componente local.
  Esses teoremas de CSP não são apresentados como um teorema pronto sobre BPE.

A diferença candidata é um compilador de efeitos exatos de tokens, guards
determinados e exceções **por face**, com reconstrução de IDs para MWPC.
Precisa demonstrar cobertura real ou algoritmo diferente do controle abaixo.
Implementar primitivas conhecidas ou vencer enumeração global não basta.

### Hipóteses e prova escrita a auditar

Um tipo é guard se só aparece em efeitos determinados (slot fixo ou uma
única classe), ausente de todos os efeitos de slots variáveis. Sua projeção
precisa ser Dyck. Os pares conhecidos delimitam faces; nenhuma abertura de
outro tipo pode atravessar sua fronteira em uma palavra válida. Logo faces
são independentes antes de enumerar exceções. Tokens são unidades atômicas:
um slot variável não pode ser dividido entre faces. Qualquer compilador deve
preservar essa condição e a ordem de bytes dentro de tokens determinados.

Em uma face escolhe-se seu principal próprio. Slots de uma classe são fixos;
um bom variável tem dois efeitos só desse principal, com deslocamentos d0,d1
e mínimos de prefixo m0,m1. Exige-se D=d1-d0>0 comum à face e
0<=m1-m0<=D. Os demais slots são exceções; Q_f é o produto de seus números
de efeitos, sem aliases. Após fixá-los, os tipos secundários precisam formar
Dyck e suas faces principais precisam formar Dyck de um tipo.

Com altura base H e j escolhas anteriores, o requisito de um bom é
prefix_antes>=ceil((-m0-H)/D) ou, para a alternativa 1,
prefix_antes>=ceil((-m1-H)/D). Os tetos diferem em 0 ou 1. Quando iguais,
obtém-se bound antes do slot; quando diferem por 1, bound incluindo o slot.
Chunks fixos acrescentam bounds. O saldo final exige soma x_i=r inteiro.
Tomando prefixmax dos bounds, bases são os subconjuntos de tamanho r com
prefix_j>=L_j. Viabilidade: 0<=r<=m e L_j<=min(j,r), incluindo j=0.
É um lattice path matroid, sem afirmação de prioridade.

**A alegação adicional a testar**, recebida no brief, é que compromissos
classe 1 I e classe 0 Z, disjuntos, são extensíveis exatamente quando I é
independente em M e Z independente em M*. Isso daria a soma direta
M|P ⊕ M*|N, truncada por b, e uma ordem greedy para todos os perfis.
Esta alegação não será aceita apenas por estar no brief: testes exaustivos
pequenos devem compará-la com as bases explícitas. Sem ela, o custo e a
otimalidade pretendidos não estão demonstrados.

Uma completação deve incluir I e evitar Z; seleção leftmost de posições
disponíveis é uma reconstrução candidata, a conferir pelos bounds e por uma
pilha independente sobre bytes. O máximo entre combinações pode perder
concavidade; cap global exige DP max-plus entre perfis de faces, nunca greedy
global sobre a união. Sem cap ativo, somam-se os ótimos locais.

### Controle competente, custos, objeções e benefício exigido

O controle especializado recebe os MESMOS efeitos, guards, exceções e bounds:
enumeração local de exceções + otimização clássica de caminhos/matroide +
max-plus sob cap. Para o gadget constante, pode enumerar as 16 atribuições
locais por guard, custo linear em F, em lugar de enumerar 4^F globalmente.
O exemplo 4,1 contra 6 testa greedy de viabilidade; não estabelece vantagem
contra esse controle nem melhora de resposta final. Não se usará CYK/ILP
genérico como único controle, nem se esconderá do controle uma decomposição.

O custo aritmético pretendido, **condicional à alegação de extensão**, é
O(Bprep + soma_f Q_f(B_f+n_f log n_f+b) + F b²). Sem quota ativa omite-se
knapsack. Bprep inclui ler o suporte, bytes, normalização, classes, guards,
compilação e memória de testemunhos. Modelo/head/transferência de logits,
extração da proposta, comparações de pesos racionais (tamanho em bits), RNG
se houver, consultas, validação e saída são adicionais explícitos. Não há
novo forward nem RNG no gate offline. Inteiros de Q terão fatoração e
bit_length, não serão tratados como constantes de máquina.

Objeções: vocabulário real pode dar k=n e Q exponencial; retirar tokens só
para produzir guards muda a operação; bytes neutros não dão validade JSON;
um tipo apenas já tem controles clássicos; aliases de mesma classe não são
probabilidades somáveis; uma demonstração condicional não é Lean, ganho
neural, novidade ou evidência de uso natural. Falta compilador geral validado,
testemunho original-ID sob cap e comparação integral, se os gates permitirem.

### Protocolo V1 congelado antes de resultados

Não medir relógios nem usar GPU nesta auditoria. Timings/uso de GPU somente
depois da mensagem do coordenador confirmando todos os worktrees preparados,
com flock exclusivo `/tmp/tcc-final-candidate-tests-gpu.lock` e preflight de
processos e recursos. Não encerrar processos alheios. Nenhum timing é
necessário para constatar uma obstrução de contrato ou Q.

Corpus fechado:

1. Dois tokenizers BPE ByteLevel existentes, somente leitura:
   LLaDA `08b83a6feb34df1a6011b80c3c00c7563e963b07` no cache Hugging Face;
   Qwen no diretório local `/home/jota/projects/tcc-final/.cache/a52-model-metadata`.
   Auditar TODOS os IDs ordinários, mapear adicionados separadamente, hashes
   dos artefatos e concordância independente com `tokenizers`.
   Para cada um, slots 32,128,512, sem pins, suporte ordinário inteiro em
   cada slot, EOS/PAD ausentes. São seis sondagens estruturais de tokenizer,
   NÃO seis capturas neurais. Não carregar pesos.
2. As seis frames de `../72-recursive-syntax-factor-width/capture-v2.jsonl`,
   sem novo forward nem repetir a aplicação A72. Usar IDs originais
   `7,8,58,60,2`, suporte fixado pela captura, sem pins. A gramática nova do
   gate é Dyck3 com bytes neutros, NÃO a antiga gramática aninhada com `#`.
   Nenhum top-k ou suporte por prompt será inventado. Registrar massa omitida
   por posição sem renormalizar. Falta de propostas full-vocab é explícita.

Gate de relevância: escolher principal que minimize Q (empate por `([{`).
Um tipo guard precisa ocorrer e satisfazer a regra acima; sem guards há uma
face. Limite Q_f<=4096 e k_f<=8 em TODAS as faces, preservando o suporte.
Relatar números aceitos/recusados separadamente para capturas e sondagens.
Recusa de parametrização não é inviabilidade nem timeout. Um caso apenas
Dyck1 não satisfaz relevância própria. Prosseguir a protótipo amplo só se
houver pelo menos uma captura elegível, contrato correto e diferença
verificável do controle especializado. Se falhar, encerrar negativamente sem
procurar casos extras ou gerar um top-k favorável.

Correção pequena, separada de relevância: normalização em todas as palavras
de comprimento <=5 sobre `()[]{}x`, contextos de pilha <=2; teste da alegação
de extensão para todos os prefix bounds viáveis até m=5, todos I/Z disjuntos;
gadget de quatro slots do brief, pesos inteiros escalados `(1,30,40,30)`
(dividir por 10), cap 0..4 e testemunhos. Repetições F=1,2,4,8 com guards
curly fixos são sintéticas e o controle recebe as mesmas faces. Nenhuma seed,
caso, métrica, limite ou controle muda depois dos resultados. Falhas ficam
preservadas; correções precisam de nova origem explícita.

O produtor e este registro serão commitados antes de executar o gate. Saída
exclusiva em arquivo novo; replays em `/tmp`, sem sobrescrever evidência.
