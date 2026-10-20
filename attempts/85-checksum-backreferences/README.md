# A85 — Capturas livres por relaxação de checksum

Estado: **construção teórica candidata; não selecionada como tema central**.
Não houve protótipo, medição, captura neural ou campanha. A revisão encontrou
um controle de condicionamento por string que impede inferir utilidade apenas
do limite de rejeições abaixo. Não ampliar sem resolver essa objeção.

## Operação e hipóteses

Congele um head produto racional sobre IDs originais, suporte finito e posições
fixadas. A decodificação conjunta correta produz bytes; não se pressupõe que
concatenar `decode([id])` do tokenizer reproduza essa operação. Cada peso de
token participa uma vez, inclusive quando um token cruza fronteiras de campos.
Aliases continuam sendo atribuições distintas. EOS/PAD seguem a política
declarada da integração; podar suporte produz `exact_on_support`.

Uma gramática identifica uma captura e até R referências, cada uma com até B
bytes. Os spans são disjuntos, embora suas fronteiras sejam escolhidas durante
o parse. Exige-se **uma anotação por palavra original**, não somente uma GLC
não ambígua no alfabeto acrescido de marcadores. Uma gramática não ambígua
sobre os bytes com papéis determinados pela sua árvore única pode satisfazer
essa hipótese. Não se admitem ciclos epsilon com multiplicidade infinita.

Se C é o conjunto que satisfaz sintaxe e igualdade byte a byte, a operação é
amostrar Q(x) = w(x) 1_C(x) / Z, com w(x) = produto_i p_i(x_i) e Z > 0.
U é a massa somente sintática e rho = Z/U. Isso define uma lei de um head;
não estabelece a lei nativa da trajetória neural nem qualidade semântica.

## Construção

Escolha H = 2^b. Para cada referência j, offset t e símbolo a, sorteie entradas
independentes A[j,t,a] uniformes de b bits. Inclua um símbolo END distinto dos
256 bytes e offsets de 0 até B. Defina

```text
phi_j(s) = XOR_{t < len(s)} A[j,t,s[t]] XOR A[j,len(s),END]
chi(x)   = XOR_{j=1..r} (phi_j(captura) XOR phi_j(referencia_j))
```

Um autômato mantém um registro chi de H valores. A captura contribui com
XOR_j A[j,t,a]; a referência j contribui com A[j,t,a]. Reinicie o offset
em cada span e aplique END na saída. Se r não é conhecido, adivinhe-o no
início e confira a contagem no fim: cada anotação aceita tem uma única
adivinhação correta, inclusive r = 0. Contadores de referência, adivinhação,
offset e modo usam O(R²(B+1)H) estados, além da representação sintática.

Interseccione a relaxação chi = 0 com a gramática e o lattice dos IDs.
Amostre exatamente com os pesos declarados, reconstruindo os IDs. Compare
os bytes da captura e das referências independentemente; rejeite colisões.

## Prova escrita

**Colisão unilateral.** Se x pertence a C, cada entrada da captura se cancela
com a referência correspondente, portanto chi(x) = 0 para qualquer tabela.
Se alguma referência difere da captura, seu vetor de incidência sobre
(j,t,a) é não nulo em GF(2). Comprimentos diferentes deixam uma entrada END
sem par; conteúdos diferentes deixam pelo menos uma entrada de byte sem par.
Referências diferentes usam j diferentes e não cancelam esse testemunho.
Condicionando todas as outras entradas, uma entrada independente restante
torna chi uniforme. Logo Pr_A[chi(x) = 0] = 1/H para toda palavra inválida.
Não é necessária independência das colisões de palavras diferentes.

**Lei aceita.** Para uma tabela fixa A, a relaxação contém C. Sua massa é Z_A.
Cada proposta válida tem probabilidade w(x)/Z_A e a aceitação tem probabilidade
Z/Z_A. Condicionando a aceitação, a saída tem exatamente Q, para toda tabela.
O número de propostas tem média Z_A/Z. Pela linearidade da esperança,

```text
E_A[Z_A] = Z + (U-Z)/H
E_A E[N | A] = 1 + (rho^(-1)-1)/H.
```

O último limite é médio sobre a tabela: não vale para cada hash fixo.
Um hash ruim pode preservar quase toda a massa inválida. Head e pins precisam
ser fixados independentemente do hash para a análise de custo. Com Z = 0,
rejeitar indefinidamente não certifica inviabilidade.

**Custo.** Suponha preparação completa limitada por A H^a operações em bits
e custo esperado de uma proposta limitado por S, uniforme nos hashes e H
permitidos. A preparação inclui tabelas aleatórias, inferência e todas as
escolhas condicionais do amostrador. S inclui RNG, reconstrução e verificação.
Então o custo esperado é no máximo

```text
F(H) = A H^a + S [1 + (rho^(-1)-1)/H].
```

Para uma estrutura regular, o produto explícito permite a = 1. O produto
genérico com GLC e preparação de todas as escolhas permite um limite
conservador a = 3, inclusive memória cúbica se necessária para essas escolhas.
Não são limites de otimalidade. A invariância XOR permite representar
deslocamentos de checksum e usar convoluções Walsh–Hadamard no inside;
amostrar filhos condicionados também precisa ser contabilizado.

Integerize racionalmente os pesos por posição. Para massas de charts
produtivos e alcançáveis, uma conclusão fixa dá uma injeção nas derivações
completas, sem multiplicidade. Os inteiros ficam limitados pelo produto
U_max = produto_i soma_v a_i(v). Seja L seu comprimento em bits. Pode-se
limitar H a uma potência de dois de ordem 2^(L+1); índices, escolhas
categóricas e RNG usam O(L) bits, mas operações com esses inteiros têm custo.
Não se trata de amostragem em tempo constante em uma máquina de reais.

**Sem conhecer rho.** Tome D_0 = 4 max(A,S) e D_t = 2^t D_0. Em cada estágio,
use hash fresco, o maior H permitido com A H^a <= D_t/2 e no máximo
floor(D_t/(2S)) propostas completas. Quando D_t >= 10 F(H), o H escolhido
é ao menos H e o número de propostas é ao menos quatro vezes a média
1 + (rho^(-1)-1)/H. Markov limita a falha do estágio por 1/4. Hashes frescos
tornam o mesmo limite válido condicionado ao histórico. Os orçamentos dobram
enquanto as probabilidades de alcançar estágios posteriores caem por 1/4:
somar a série dá, conservadoramente, custo <= 60 min_H F(H).

Cada aceitação em qualquer estágio tem a mesma Q, portanto a adaptação por
falhas preserva a lei. Um cap em H limita o mínimo aos H permitidos; depois
dele, pode-se aumentar apenas a quantidade de propostas. Caps por contagem de
propostas completas preservam esse argumento. Interromper propostas lentas
por timeout pode enviesar a lei condicionada a terminar no prazo.

As provas foram revisadas por dois subagentes. Não foram formalizadas em Lean
nem verificadas por implementação independente.

## Antecedentes e diferença pretendida

- Hash por tabulação XOR e fingerprints unilaterais são clássicos:
  [Pătrașcu–Thorup](https://people.csail.mit.edu/mip/papers/charhash/charhash.pdf)
  e [Babu–Limaye–Varma](https://eccc.weizmann.ac.il/report/2010/094/).
- [AWRS, §3 e Apêndice J](https://www.cs.jhu.edu/~jason/papers/lipkin%2Bal.colm25.pdf)
  já gera com restrições context-sensitive, incluindo backreferences.
  [CARS, §3](https://arxiv.org/html/2510.01902v2) já usa rejeição adaptativa
  com prefixes inválidos. Exatidão por rejeição não é contribuição própria.
- [PAWS, §3](https://www.cs.cornell.edu/~ermonste/papers/sampling-nips2013.pdf)
  acrescenta hashes para particionar soluções verdadeiras, com garantia
  aproximada. Aqui se relaxa igualdade para um superconjunto e se verifica
  a saída exatamente. Isso distingue mecanismos, não prova prioridade.
- [Paul–Eisner](https://aclanthology.org/N12-1024/) trata consenso ponderado
  entre autômatos. Spans conhecidos e suas tokenizações independentes exigem
  esse controle; não reivindicar novidade na composição de lattices.
- [Bille–Gørtz–Jessen](https://arxiv.org/html/2609.16914v1) trata uma captura
  com várias referências em texto fixo.
  [Nogami–Terauchi](https://arxiv.org/html/2406.18918v2) caracteriza classes
  de backreferences e MCFGs. Essas reduções não viram automaticamente um
  amostrador ponderado novo.
- [FactorDLM](https://arxiv.org/html/2609.32900v1),
  [Mosaic](https://arxiv.org/html/2607.07026v1) e
  [Decode-Time Grammars](https://arxiv.org/html/2607.18357v1) são controles
  de inferência estruturada e geração com ambientes de nomes.

A diferença candidata é a compilação de fronteiras ainda desconhecidas e
várias referências em um só checksum, acompanhada do custo completo de
amostragem. A busca delimitada não encontrou essa combinação específica;
isso não confirma prioridade mundial nem relevância suficiente.

## Objeção de utilidade e controle mais forte

O benefício escrito reduz um limite frente à rejeição de saídas sintáticas
independentes. Esse controle pode ser muito fraco. Para uma string s, defina

```text
F(s) = massa sintática com captura = s
G(s) = massa válida com captura = s.
```

Uma proposta sintática dá s com lei F(s)/U. Para um limite certificado
M >= max_s G(s)/F(s), aceite s com probabilidade G(s)/(M F(s)) e amostre
uma conclusão válida condicionada a s. A saída também tem exatamente Q.
F(s) e G(s) usam interseções com autômatos literais; fronteiras desconhecidas
não impedem esse controle.

Com spans independentes uniformes sobre K strings, escolher a string e
condicionar as referências pode aceitar toda proposta. A rejeição de todas
as ocorrências independentes teria rho = K^(-R), tornando o limite do
checksum artificialmente favorável frente a um controle incompetente.
Mesmo quando a massa semântica máxima é difícil, o limite certificado
max_s q(s) <= sqrt(soma_s q(s)^2), obtido por consenso de dois lattices,
pode alcançar o expoente favorável do checksum com preparação menor.

Também são controles necessários: fatoração por bytes em layouts simples,
enumeração de fronteiras quando pequena, enumeração de strings candidatas,
interseção sincronizada, cópia/renderização, MAP com massa omitida certificada
e implementações por convolução XOR. Se a métrica for qualidade da resposta,
métodos aproximados também são comparadores válidos.

Nomes alpha-equivalentes podem ser canonicalizados. Nomes já dados no prompt
podem ser copiados. Fuzzing precisaria mostrar cobertura ou bugs adicionais
frente a geradores conhecidos; exigir Q somente para favorecer o método não
justifica esse consumidor. Não foi encontrado um consumidor natural que
supere essas objeções e caiba nos recursos. Por isso **a prova não seleciona
o tema**, e nenhuma campanha está autorizada por esta tentativa.
