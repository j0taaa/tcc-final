# A76 — Exceções locais de efeito de pilha

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
