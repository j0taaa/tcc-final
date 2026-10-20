# Obstrução adicional: identificadores em JSON irrestrito

Prova escrita posterior à sondagem de rank, não um novo gate neural nem uma
reformulação para resgatar A73. O enunciado é específico da contração por ID
e do suporte que contém os testemunhos abaixo. Não prova ausência de qualquer
otimização de head, nem lower bound de GPU ou de MAP.

## Teorema

Fixe n>=6 slots de tokens originais, EOS/PAD ausentes e sem posições fixadas.
L é o conjunto das sequências cujo concatenado de bytes é um documento JSON
válido completo. O suporte contém o ID v, as aspas, espaço, dígitos 0/1 e
os IDs de um byte necessários a `true`, `false`, `null`, `a`, `b`.
O ID v emite uma palavra ASCII w em `[A-Za-z_][A-Za-z0-9_]*`. São admitidos
outros tokens, inclusive multi-byte, mas não emissões vazias, EOS ou semântica
que trate PAD como bytes ignoráveis. Todas as tokenizações declaradas são
sequências válidas; não se impõe retokenização canônica do texto produzido.

Seja p(w)=1 se w é prefixo não vazio de `true`, `false` ou `null`, e zero
caso contrário. Seja s(w)=1 se w é sufixo não vazio desses literais OU casa
`[eE][0-9]+`, e zero caso contrário. Então

    U_v = span{e_i : 1<=i<=n-2}
          + (span{e_0} se p(w)=1)
          + (span{e_{n-1}} se s(w)=1),

e portanto q_v=n-2+p(w)+s(w). O número é exatamente o de posições onde v
pode ocorrer. Assim A73 não elimina nenhuma consulta desse ID em relação
ao sparse que conhece sua viabilidade por posição. A conclusão vale mesmo
que existam aliases de v: os testemunhos mantêm o ID original e não os poolam.

## Prova

Use como âncora os IDs de `0` seguido de n-1 espaços. Ela é JSON válido e
não contém v. Para cada posição interna i escolha uma palavra com aspas nos
extremos, um token `a` em cada posição interna e v somente em i. Se v é o
ID de `a`, use `b` como preenchimento. Os bytes de todas essas palavras são
strings JSON válidas; w não contém aspas, escape ou controle. O vetor de
indicadores de v é exatamente e_i. Logo todos os e_i internos pertencem a U_v.

Se w é prefixo de um literal, use v na primeira posição e complete o literal
com IDs de um byte, preenchendo o resto com espaços. São necessários no máximo
cinco slots; n>=6 garante espaço para todo caso. A primeira coordenada é 1,
a última é 0, e qualquer ocorrência restante de v está no interior, já
gerado. Subtraindo essas coordenadas internas obtemos e_0.

Se w é sufixo de um literal, coloque espaços à esquerda, o prefixo faltante
em IDs de um byte e v na última posição. Existe ao menos um espaço inicial
porque n>=6. Sua primeira coordenada é 0 e a última é 1. Subtraindo eventuais
ocorrências internas de v obtemos e_{n-1}. Se w casa `[eE][0-9]+`, use espaços,
o token `1` e v: os bytes são um número JSON com expoente; novamente obtemos
e_{n-1}. Essas diferenças são contra a mesma âncora, que não contém v.

Resta excluir posições extras. Se v vem primeiro, seus bytes começam por
letra ou underscore e não contêm delimitadores ou whitespace. No JSON só
podem iniciar um literal `true`/`false`/`null`; portanto w precisa ser prefixo
de um deles. Se v vem por último, seus bytes não fecham strings, arrays ou
objetos e não contêm whitespace. Só podem completar um literal, caso em que
w é sufixo, ou completar um número. Um sufixo de número que começa por letra
precisa começar pelo marcador de expoente e/E e terminar nos dígitos desse
expoente. Não há sinais em w. Logo ele casa `[eE][0-9]+`. Em qualquer outra
situação a respectiva coordenada é identicamente zero. Isso dá a inclusão
inversa e conclui a igualdade de spans.

O resultado não vale automaticamente sob uma máscara diferente: uma contração
do suporte ou novos commitments podem remover as strings testemunhas e diminuir
o rank. Também não autoriza trocar sintaxe JSON por schema sem nova análise.

## Auditoria finita predeclarada antes de executar

Verificar TODOS os 32.804 IDs da classe identificador no tokenizer pinado,
em n=6,8,16,32, sem modelo, GPU ou timings. Para cada ID gerar a âncora,
todos os testemunhos internos e os testemunhos de fronteira aplicáveis.
Conferir número de slots, bytes originais, validade por `json.loads`,
coeficientes de fronteira e pivôs triangulares independentes. Não enumerar L
inteiro nem chamar essa verificação de prova de completude do teorema.
Conferir ainda por busca direta em n=6 sobre alfabetos pequenos as ocorrências
de fronteira para os exemplos `a`,`b`,`t`,`true`,`e`,`e1`,`l`,`_` que existirem.
Essa busca é ataque finito, não uma demonstração da necessidade para todo BPE.

Não medir latência nem mudar os seis casos do protocolo operacional. Publicar
contagens, hashes, falhas e eventuais correções separadas da prova congelada.
