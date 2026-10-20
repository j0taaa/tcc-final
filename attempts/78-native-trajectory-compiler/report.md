# A78 — Compilar uma trajetória nativa de dependência pequena

Base: `84b34969`; branch `research/a78-native-trajectory-compiler`.
Auditoria iniciada em 2026-10-19. A autorização é para testar a candidata.
Não há descoberta aprovada, revisão humana, prova Lean ou ganho neural implícito.

**Decisão: não selecionar A78 como contribuição central de TCC nesta formulação.**
O gate barato não encontrou um dLLM utilizável com a promessa global exigida.
A parte condicional combina aprendizado e inferência clássicos; não demonstrou
diferença própria nem benefício integral frente ao mesmo controle competente.
As checagens finitas abaixo passaram, sem converter esse gate em seleção.

## Operação e benefício que precisariam existir

Fixar prompt, posições, pins, suportes de **IDs originais** S_i, |S_i|≤K,
e uma permutação π das posições livres. O canvas c_t tem os tokens já gerados,
os pins e MASK nas demais posições. A operação é amostrar

    Q_π(x) = ∏_t q_{π(t)}(x_{π(t)} | c_t),
    Q_π(x | G) = 1_G(bytes(x)) Q_π(x) / Z_π,   Z_π > 0.

Cada q é uma categórica normalizada no suporte declarado. Não se exige uma
conjunta cujas condicionais sejam todos os heads masked: Q_π é a lei do decoder
fixado, e ordens distintas podem definir leis distintas. Isso remove a exigência
inacessível de P(.|G,pins) de A75, mas não fornece dependência pequena.
Não é MWPC, produto congelado de um passo nem uma afirmação semântica.
Uma política adaptativa, remasking ou remanejamento dos slots fica fora deste
contrato. Pins integram o canvas desde o começo; condicionar pins depois da
geração seria outra operação.

Se p_i for full-vocabulary, restringir explicitamente define
q_i(v|c)=p_i(v|c)/s_i(c), s_i(c)=∑_{v∈S_i}p_i(v|c)>0. A cauda
1−s_i(c) permanece declarada por contexto; isso é `exact_on_support`,
não o modelo completo condicionado em permanecer nos suportes: neste último,
os fatores s_i(c) também pesariam as trajetórias. Não foram calculadas caudas
neurais nesta tentativa. Não fundir aliases, retokenizar ou substituir IDs por
caracteres. Cada ID conserva seus bytes e sua probabilidade. EOS/PAD estão
**ausentes** do teorema/checagens; MASK é estado de entrada, nunca saída.
Um consumidor com EOS/PAD precisa especificar transições, término e bytes
antes da preparação. Massa zero, entrada não suportada, recusa e erro diferem.

O benefício candidato seria pagar consultas simultâneas de calibração uma vez,
reconstruir fatores pequenos e servir amostras exatas de Q_π|G sem novos
forwards, incluindo a preparação na amortização. Comparação correta: rejeição
da mesma Q_π; inferência com pais/tabelas conhecidos; aprendizado clássico de
juntas com o mesmo head simultâneo; enumeração/Doob exato em instâncias pequenas.
Twister é o controle central de **alvo de trajetória**, embora SMC com população
finita não deva ser chamado sampler exato i.i.d. por causa do nome do artigo.
Produto raiz projetado é controle de alvo diferente, útil para diagnosticar erro.

## Antecedentes e auditoria primária delimitada

Fontes consultadas ao vivo; versões e hashes dos arquivos pequenos em
`sources.json`. Não se baixaram pesos nem se executou código remoto.

- [Bshouty–Costa, 2017](https://arxiv.org/html/1706.06934v1), §§1–3,
  tratam aprendizado exato de juntas por membership queries; §2.1 dá universal
  sets e o argumento probabilístico. Recuperar suporte/tabela por consultas
  separadoras é primitiva anterior. A78 não melhora aqueles bounds.
- [Angluin–Aspnes–Chen–Wu](https://cs.yale.edu/homes/aspnes/papers/injecting-values-abstract.html)
  estudam aprendizado por injeção de valores, com observação de uma saída.
  A78 recebe todas as distribuições masked simultaneamente: interface diferente
  e mais informativa, não descoberta da ideia de reconstruir dependências.
- [Sarkar et al., 2016](https://arxiv.org/html/1605.02131v1), §2,
  registram covering arrays, universal sets e limites logarítmicos no número de
  colunas. A cobertura usada abaixo é uma aplicação desses objetos clássicos.
- [Dechter, bucket elimination](https://arxiv.org/abs/1302.3572)
  fornece a primitiva de eliminação; sua dependência da largura não é nova.
- [PUNT, 2025](https://arxiv.org/html/2510.21961v1), §3.1/Assumption 3.3
  e apêndice B, testa influência contextual e assume estabilidade. Uma proposta
  local e sua justificativa por atenção não certificam a igualdade global de
  funções exigida aqui; caminhos por outras posições/camadas também contam.
- [FactorDLM, 2026](https://arxiv.org/html/2609.32900v1), §3.1,
  condiciona o produto mean-field de um passo, com auxiliares de extensão única
  e custo por largura. A78 mudaria os potenciais para fatores de trajetória,
  não inventaria eliminação, extensão única ou inferência em pseudoflorestas.
- [Twister, 2026](https://arxiv.org/html/2609.35609v1), §3.1 e §4,
  já declara a lei nativa terminalmente condicionada via Doob e corrige a
  composição por SMC. A diferença candidata de A78 seria computar essa lei
  exatamente sob uma promessa global de junta e largura tratável, usando heads
  simultâneos mesmo sem coerência entre ordens. O alvo condicionado não é novo.

Essas leituras não estabelecem prioridade específica. A composição proposta
continua sem contribuição própria demonstrada contra aprendizado clássico
com a mesma interface, mesmo que sua prova condicional esteja correta.

## Gate barato de consumidor

O conjunto auditado é LLaDA-8B-Instruct local, Dream-v0-Instruct-7B, PUNT,
SparseD e LoSA; não é uma quantificação sobre todo dLLM possível.

O snapshot LLaDA local `08b83a6feb34df1a6011b80c3c00c7563e963b07` foi
lido sem carregar pesos. `config.json` tem 32 camadas, 32 heads,
vocab_size=126464, MASK=126336 e EOS=PAD=126081. Em `modeling_llada.py`,
linhas 624–660/711–717 usam atenção não causal; 1161–1172 constroem bias
bidirecional zero e 1248–1292 tratam máscaras opcionais; 1300–1346 propagam
pelos blocos. Não existe uma garantia arquitetural de k pequeno nem um
certificado global de aproximação nessa interface. Isso **não prova** que cada
peso do checkpoint produza influência não nula de todas as posições.
[Fonte original do snapshot](https://huggingface.co/GSAI-ML/LLaDA-8B-Instruct/blob/08b83a6feb34df1a6011b80c3c00c7563e963b07/modeling_llada.py).

[Dream](https://huggingface.co/Dream-org/Dream-v0-Instruct-7B/blob/373705a/modeling_dream.py)
também usa SDPA não causal e atenção completa. Um forward, correlação pequena,
atenção pequena ou coincidência de logits em exemplos não substitui a promessa.

[SparseD](https://arxiv.org/html/2509.24014v1), §3.3/Algorithm 1, começa
com atenção completa e escolhe padrões por Q/K antes de reutilizá-los. Isso não
certifica pais fixos pequenos para todos os canvases do decoder.
[LoSA](https://arxiv.org/html/2604.12056v1), §§2.3–4, seleciona prefixos
por queries/keys, reutiliza estatísticas e mantém atenção densa no bloco.
Sua seleção dependente da entrada e sua composição multicamada não fornecem
o contrato de junta global nem erro uniforme condicionado em uma gramática rara.
Esses são limites inferidos dos mecanismos descritos, não medições desses modelos.

Mesmo uma máscara de atenção **fixa** de grau d por camada só limita as
dependências pela união transitiva das posições alcançáveis nas L camadas
(até min(n−1, O(d^L))); não basta olhar d numa camada. Com seleção por conteúdo,
a própria escolha dos índices pode depender de posições não selecionadas.
Alterar o modelo para impor pais seria outro decoder, e não teste de A78 no
modelo existente. Não houve tal alteração.

**Resultado da auditoria de contrato: NO_USABLE_SMALL_DEPENDENCY_CONTRACT.**
Não se encontrou neste conjunto um consumidor com promessa global utilizável
ou nova certificação aproximada útil e acessível. Esse gate já impede uma
campanha neural ou protótipo extenso. Não depende da ocupação da GPU.

## Provas escritas condicionais e suas fronteiras

**Identificação sob promessa.** Supor que, quando i está MASK, q_i depende
somente dos estados completos (MASK ou ID original) de J_i, |J_i|≤k,
em **todos** os canvases admissíveis. Prompt/pins são constantes. O oráculo
retorna vetores racionais exatos com representação de até B bits por entrada;
acesso a probabilidades reais arbitrárias não custa B bits por definição.

Para suportes uniformes, q=K+1. Tome uma covering array de força
t=min(n,2k+1) sobre os estados. Se dois candidatos de suporte ≤k diferem numa
linha com i=MASK, cobrir {i}∪J∪J' reproduz essa diferença, contradizendo a
consistência com as consultas. Logo um candidato consistente coincide
globalmente **dentro da classe prometida**. Para suportes heterogêneos, usar
os alfabetos próprios (ou índices redundantes mapeados para IDs admissíveis);
nunca injetar em uma posição um ID só permitido em outra.

Há M=binom(n,t)q^t interações; T linhas uniformes falham com probabilidade
≤M exp(−T/q^t). Basta T≥q^t(log M+log(1/η)). A forma abreviada
O(q^(2k+1)(k log n+log(1/η))) vale no regime k≥1, t=2k+1≤n e q fixo.
Se q varia, incluir t log q; se k=0, uma consulta all-MASK basta.
A possibilidade de gerar uma array ou a probabilidade ≥1−η de cobertura
não é uma verificação da promessa sobre o modelo.

Enumerar suportes para cada saída e agrupar suas linhas custa, conservadoramente,
O(n^(k+1) T (k+K)) operações de palavra para k fixo, mais comparação/cópia de
B bits, construção e leitura das queries. É a abreviação usual
O(n^(k+1)TK) quando esses parâmetros são constantes, não um bound de bits.
A tabela final ocupa O(nKq^kB+n k log n) bits; reter o transcript custa
O(nTKB) bits além dos canvases O(nT log q). Streaming/reconsulta mudam o custo.
Consultar todas as linhas de uma tabela exponencial não é calibração grátis.

**Da tabela para Q_π.** Em q_i, pais anteriores recebem seus valores gerados;
pais posteriores recebem MASK. Isso define φ_i^π normalizado sobre x_i e com
pais apenas anteriores em π. O produto é uma rede Bayesiana e coincide termo
a termo com Q_π, inclusive se o oráculo for incoerente entre ordens. Para G,
construir um circuito booleano determinístico sobre bytes/IDs e auxiliares
funcionais. Cada palavra precisa de uma extensão auxiliar única. Somar parses
de uma gramática ambígua pesa multiplicidades e pode mudar a lei de palavras.
Eliminação exata calcula Z, marginais e backward sampling com racionais.
São cobrados tokenizer, construção do reconhecedor e largura conjunta de
fatores+gramática; k pequeno não limita essa largura (fronteira de A72).

**Caso bipartido k=1.** Há m drivers e m filhos. Cada filho consulta um único
driver desconhecido, com tabela h(MASK),h(0),h(1). Três queries uniformes
obtêm esses valores. Para cada bit do índice do driver, fazer duas queries:
MASK/0 e MASK/1 conforme o bit; filhos sempre MASK. Se a tabela não é constante,
uma das duas sondas distingue os bits e identifica o pai. Tabelas constantes
não identificam pai porque ele é irrelevante. São 3+2⌈log₂m⌉ forwards,
O(m log m) comparações/entradas binárias, mais B bits e custo dos heads.
É codificação/separação clássica aplicada simultaneamente, não nova primitiva.

Para um lower bound de **reconstrução**, usar pais entre m drivers e
h(s)=1/4 se s∈{MASK,0}, h(1)=3/4. Há m^m mapas. Uma query devolve no máximo
m bits informativos de filhos (drivers não dão informação dos pais), logo uma
árvore de respostas exatas tem 2^(mT) folhas e T≥log₂m para identificação
determinística de todos os mapas. O mesmo Ω(log m) segue por contagem para
sucesso constante sob mapa uniforme. Isto não é lower bound de amostrar uma
palavra. Raw sampling requer somente **dois rounds**, drivers e depois filhos.
O controle que conhece pais/tabelas dispensa essa calibração.

**Consumidor gramatical construído.** Use S→aSb|cSd|#, LL(1). A palavra é
opens(X_0…X_{m−1}) # closes(Y_{m−1}…Y_0), sendo 0↔a/b e 1↔c/d.
Drivers justos são gerados antes dos filhos; cada filho combina com o bit de
seu pai com probabilidade 3/4, e com pai MASK é justo. G equivale a Y_i=X_i.
Então Q_π(X,Y=X)=2^(−m)∏_i ψ(X_parent(i),X_i), ψ igual a 3/4 ou 1/4.

O grafo i→parent(i) tem outdegree 1; cada componente contém um ciclo dirigido
com árvores anexas, mesmo com indegree ilimitado. Self-loops viram fatores
unários; ciclos de tamanho 2 combinam dois fatores na mesma aresta. Depois de
eliminar folhas, sobra um ciclo simples. Largura ≤2 dá O(mK³) operações
racionais por eliminação/transferência, sem novidade de BP. Com ψ binário
fixo, inteiros de mensagens podem crescer O(m) bits; não há tempo linear em
bits automaticamente. Para racionais B-bit arbitrários, contabilizar também
denominadores comuns, reduções e domínios K. RNG exato e saída custam à parte.

Se os ciclos dirigidos têm comprimentos ℓ_c,

    Z_π = 2^(−m) ∏_c (1+2^(−ℓ_c)).

De fato, somar cada folha elimina um kernel normalizado; a matriz ψ tem
autovalores 1 e 1/2, e cada ciclo contribui trace(ψ^ℓ). Para **um ciclo**
de tamanho m, Z=2^(−m)(1+2^(−m)), justificando rejeição exponencial nessa
família. Para m self-loops, Z=(3/4)^m e Q_π(X|G) é uniforme; não generalizar
a separação do ciclo para todos os mapas.

Na família de um ciclo, o número D de discordâncias entre vizinhos é par.
Sob Q_π|G, D tem Bin(m,1/4) condicionada a paridade par; sob produto raiz
projetado, Bin(m,1/2) condicionada a paridade par. O evento D≤3m/8 separa as
leis com erro O(1/m), por Chebyshev e probabilidade de paridade ≥1/2. Logo TV→1.
A lei condicionada deixa de ser uniforme, mas seu cálculo continua exatamente
o controle clássico de pais conhecidos. Se todos os filhos forem gerados
antes dos drivers, sua lei será produto justo e o posterior será uniforme:
a distinção entre ordens é real, não inconsistência da definição de Q_π.

**Impossibilidade de certificação black-box genérica.** Para um alvo MASK com
q^(n−1) contextos, qualquer auditor exato que deixe um contexto z sem consultar
recebe o mesmo transcript de h≡Bern(1/2) e de h' que muda somente em z.
h' depende de todas as n−1 coordenadas (variar qualquer uma sai de z).
Isso inclui consultas adaptativas, seguindo o transcript constante. Portanto
elas não certificam a promessa contra funções arbitrárias. Com z uniforme entre
N contextos, T consultas adaptativas acertam z com probabilidade no máximo T/N
no transcript constante. Distinguir com sucesso constante também exige Ω(N)
consultas nesse par de classes. Testes aleatórios podem testar distância sob
uma distribuição escolhida, não garantir igualdade global; isto não é um
lower bound contra inspeção/prova de arquitetura.
Restringir a promessa aos prefixos de π pode bastar para essa ordem, mas o
último alvo ainda tem K^(n−1) prefixos possíveis sem estrutura adicional.

**Aproximação e eventos raros.** Se TV(Q,Q̃)≤Δ e ambos dão massa positiva a G,
TV(Q|G,Q̃|G)≤min(1,Δ/max(Z,Z̃))≤min(1,Δ/Z̃). Para demonstrar a primeira
desigualdade, use o conjunto que realiza a TV condicional: quando Z≥Z̃,
Q(A)−Q̃(A)≥Z·TV; no outro caso use seu complemento dentro de G.
Com massa ε em G e condicionais quase disjuntas, a desigualdade é apertada.
Logo aproximação média não basta em uma gramática rara. Uma garantia global
multiplicativa por fator, e^(−ε_i)≤φ_i/φ̃_i≤e^ε_i, dá razão de trajetórias
entre e^(−E) e e^E, E=∑ε_i. Depois de condicionar, a razão fica entre
e^(−2E) e e^(2E), implicando TV≤tanh(E), independentemente de Z.
Isso é um bound condicional útil **se** o certificado uniforme já existir;
uma auditoria finita de um head arbitrário não o estabelece. Nenhum certificado
desse tipo foi encontrado para os modelos auditados. Não se exige P(.|G,pins).

## Protocolo V1 congelado antes da execução

Não há casos neurais elegíveis após o gate de contrato. A execução autorizada
é somente uma checagem de fronteiras de prova com stdlib/Fraction, sem tempos,
GPU, amostragem empírica ou treinamento. Não implementar compiler geral,
learner geral, engine de BP ou benchmarks para fabricar um gate positivo.

Casos determinísticos, sem seeds/RNG:

1. Auditoria incompleta: três coordenadas ternárias, omitir (0,1,0), comparar
   head constante e alteração nessa única linha; conferir as três influências.
2. Amplificação: ε=1/1024, leis (ε(1−ε), ε², 1−ε) e a troca das duas
   primeiras coordenadas; G são as duas primeiras. Conferir o bound racional.
3. As sondas de k=1: m=1…5, todo pai e todas as 27 tabelas com valores em
   {1/4,1/2,3/4} para MASK,0,1; incluir constantes e dependência só em MASK.
4. Todo mapa de pais para m=1…4: enumerar a lei nativa, reconhecer bytes por
   implementação LL(1) independente, conferir fórmula de Z e largura ≤2;
   self-loops, indegree ilimitado, ciclos e arestas recíprocas estão incluídos.
5. Ciclo único m∈{1,2,4,8,16,32,64}: fórmula binomial racional de Z e TV
   contra produto raiz projetado uniforme. Nenhum desses números é ganho LLM.
6. Contraexemplo de contagem de parses: palavras a/b equiprováveis e duas
   extensões para b; conferir mudança da lei, preservação por extensão única.

Nos casos gramaticais os IDs **artificiais**, não IDs de um modelo, são
17→b'a', 23→b'c', 31→b'b', 47→b'd', 59→b'#'; MASK=−1. O slot # é pin
fixo, sem probabilidade multiplicada. Suportes de opens=(17,23), closes=(31,47),
sem aliases presentes. Ordem π: opens da esquerda para direita, depois closes
da direita para esquerda. Há 2m saídas e um pin. A enumeração paga todos os
2^(2m) pares; não é sampler implementado nem demonstração de complexidade.

Saída pequena, exclusiva (`open(...,'x')`), contendo checks, contagens e
frações como strings; uma falha deve ser preservada e corrigida em versão
separada. Hash do produtor e commit produtor acompanham os dados. Não alterar
casos, métricas ou gates após executar. Checagem passa somente se **todas**
as identidades e os contraexemplos passam; isto é gate de correção limitado.
Seleção científica exige consumidor utilizável, diferença própria e benefício
integral contra controles competentes: passar correção não satisfaz seleção.

Todo uso futuro de GPU/timing exige autorização de preparação (recebida do
coordenador nesta execução), flock **exclusivo** em
`/tmp/tcc-final-candidate-tests-gpu.lock` e preflight sem processos compute
alheios nem benchmark concorrente. Se ocupado, registrar indisponibilidade
sem matar processos ou medir. A execução V1 não usa GPU nem lê relógios.

## Custo completo e faltas

Cobrar construir queries/cobertura, CPU de aprendizado, forwards/backbone,
head full ou sparse, normalização e cauda, leituras/transfers, tabelas,
construção da gramática/tokenizer, largura e mensagens de eliminação, bits de
operandos, RNG e escrita de IDs/bytes. Para R amostras, o custo é preparação
mais R vezes inferência/RNG/saída; a preparação não desaparece em R=1.
No bipartido, comparar calibração 3+2⌈log₂m⌉ com dois rounds raw, e com
zero calibração de pais conhecidos. Rejeição custa 2/Z rounds esperados
nesse decoder, mas não é o único controle. Não há latências medidas aqui.

Faltam consumidor/certificado utilizável, separação de antecedente competente,
vantagem integral e implementação numérica que cumpra o contrato neural.
A73 foi lida apenas em seu `followup.md` absoluto: JSON/Dyck empatam sparse,
copy empata pooling. A75 foi lida apenas em seu `report.md` absoluto: factory
com mesmo estimador é idêntico e não há oráculo coerente neural. Essas lições
motivam os controles; não foram reabertas suas aplicações nem copiadas fontes.
O exemplo de seis slots citado no pedido não veio com sua tabela de oráculo;
seus números 729/296/545/142 não serão apresentados como reprodução de A78.

## Resultado de execução e decisão

`d4636b91` congelou protocolo, argumentos, manifesto de fontes e produtor antes
de executar. [results-v1.jsonl](results-v1.jsonl) é a saída original exclusiva;
seu cabeçalho registra commit e hashes SHA-256 do produtor e manifesto.
Não houve falha científica, correção de dados, seed escolhida ou caso retirado.
Nenhuma fonte/dado histórico, biblioteca, vendor ou outra branch foi alterada.

As **6/6** checagens de fronteira passaram:

- 26 contextos consultados não distinguem uma constante de uma função alterada
  na 27ª linha; essa função depende das três coordenadas. É contraexemplo à
  certificação global por aquele transcript, não execução de um Transformer.
- Erro incondicional **511/524288** vira erro condicional **511/512** quando
  Z̃=1/1024, exatamente Δ/Z̃. A amplificação não é um problema numérico de float.
- 405 casos pai/tabela confirmaram as sondas, incluindo 45 tabelas constantes.
  Custos de calibração por m=1…5: **3, 5, 7, 7, 9** consultas simultâneas.
  Até nessa família construída são mais que os dois rounds do sampler raw;
  pais conhecidos não pagam essa calibração. Não se mediu velocidade.
- Todos os **288 mapas** para m≤4 passaram normalização, fatoração da massa
  válida e largura executada ≤2. Foram 67.332 avaliações de palavras por ordem
  (duas ordens), com 340 reconhecimentos de bytes distintos. Em 284 mapas os
  posteriores das duas ordens diferiram; os quatro mapas só de self-loops
  deram posterior uniforme, como exige a exceção escrita.
- Os sete ciclos congelados confirmaram as fórmulas racionais. Em m=64,
  Z=(2^64+1)/2^128 e TV contra produto raiz projetado é aproximadamente 0,96486.
  Essa separação é construída; o controle clássico com pais conhecidos calcula
  **a mesma lei**. Não estabelece melhoria de decodificação neural.
- Duas extensões para b mudaram (1/2,1/2) em (1/3,2/3), TV=1/6; extensão
  única preservou a lei. Não se ponderou uma palavra pelo número de parses.

**Zero forwards, zero uso de GPU, zero bits de RNG e nenhum benchmark/timing
experimental.** A disponibilidade de GPU não foi avaliada nem usada como
motivo de rejeição. Após a confirmação de preparação do coordenador, o gate
de contrato continuou negativo. Não há "0/n ganhos neurais" em casos que não
foram executados; não se declarou inviabilidade de inferência ou impossibilidade
de todo dLLM futuro. A ausência atual de consumidor e a falta de diferença
demonstrada bastam para não selecionar esta formulação e parar antes de
protótipo extenso. A contribuição científica positiva do projeto fica aberta.

Não implementar sampler neste gate evita inventar contadores: os únicos
contadores executados acima são da enumeração/sondas finitas. O custo em bits,
memória e RNG de um compiler neural continua não medido; os bounds e itens de
custo da seção anterior são requisitos teóricos, não uma medição de software.

## Reprodução e verificações

Python 3.11.16; stdlib basta para o produtor. O ambiente de desenvolvimento
existente `/home/jota/projects/tcc-final/.venv` foi reutilizado sem instalação
ou alteração de pacotes; `PYTHONPATH` aponta para **este** worktree. Os corpos
de fontes externos ficaram em `/tmp/a78-primary-source-audit`, fora do Git;
o manifesto preserva versões/URLs/hashes, não garante disponibilidade eterna
nem byte-estabilidade do HTML de um servidor.

```bash
# Sempre uma saída nova; results-v1.jsonl não pode ser sobrescrito.
a78_replay=$(mktemp -d /tmp/a78-replay.XXXXXX)
PYTHONDONTWRITEBYTECODE=1 python3 \
  attempts/78-native-trajectory-compiler/check.py --output "$a78_replay/check.jsonl"
PYTHONDONTWRITEBYTECODE=1 /home/jota/projects/tcc-final/.venv/bin/python \
  -m ruff check attempts/78-native-trajectory-compiler
PYTHONDONTWRITEBYTECODE=1 /home/jota/projects/tcc-final/.venv/bin/python \
  -m ruff format --check attempts/78-native-trajectory-compiler
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/src" \
  MYPY_CACHE_DIR=/tmp/a78-mypy-cache RUFF_CACHE_DIR=/tmp/a78-ruff-cache \
  make check VENV_PY=/home/jota/projects/tcc-final/.venv/bin/python
git diff --check
```

Ruff e formatação da tentativa passaram antes do congelamento e na conferência
final; `git diff --check` passou. **`make check` passou: 345 testes**, snapshot
EPIC preservado, lint/formato e mypy em 55 arquivos da biblioteca. Esses checks
são validação de software, não timings científicos nem validação de novidade.
Nenhum teste Lean foi criado ou alegado.
