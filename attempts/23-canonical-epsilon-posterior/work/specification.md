# Operação e prova escrita (referência inicial, não prova mecanizada)

## Definições

Há n slots físicos, vocabulário original V e bytes composicionais por ID.
O quadro inicial fixa alguns IDs; os demais slots têm V inteiro. EOS não é
um terminador admitido. O lexer JSON determinístico valida também UTF8,
escapes, números e palavras reservadas. Mantém estado entre tokens e emite
terminais sintáticos; STRING e NUMBER (incluindo Boolean/null coarsenados)
não carregam seu valor textual. Os bytes/IDs originais são preservados.
Uma sequência é aceita quando seu texto é um JSON UTF8 completo, sob a
gramática determinística de valores/arrays/objetos, seguida de END explícito.

Para cada posição livre p, interpretar os floats finitos não negativos como
racionais exatos e normalizar por sua SOMA exata. Obter inteiros w[p,t] e
denominador d[p], com soma_t w[p,t]=d[p]. Posição fixa é delta de peso1.
Por quadro, construir um DAG lexical acíclico. Transições sem sintaxe são
epsilon; fechar cada token contribui exatamente uma folha (p,c), cujo valor
W[p,c] é a soma dos w[p,t] dos membros originais da classe naquele estado.
As classes podem diferir conforme o estado de entrada. Um caminho conserva
uma escolha em cada slot, mesmo quando um token emite zero terminais ou
vários terminais. Distintas classes com mesmo próximo estado podem ser somadas.

## Fechamento vazio com proveniência

Seja x_e a variável da escolha de um arco epsilon e peso1 nos arcos
sintáticos. Para cada início a solicitado pelo parser, o polinômio E_a(v)
das rotas epsilon de a até v satisfaz:

    E_a(a)=1;
    E_a(v)=sum_{e:u→v epsilon} E_a(u) x_e.

Cada arco sintático v→b de rótulo l contribui E_a(v) ao scanner R_l(a,b).
Somar essas contribuições se há mais de um arco com os mesmos l,b. Compilar
os E como circuitos de somas/produtos, mantendo suas folhas de tokens, em vez
de apenas guardar valores numéricos. A gramática só vê terminais reais.

Para END, a rota termina no único sumidouro F. Pode-se compartilhar a
recorrência inversa:

    H(v)=sum_{e:v→u epsilon} x_e H(u) + #arcos(v→F,END).

Scanner END(a,F) usa H(a). Se há flush NUMBER antes de END, ele continua um
terminal verdadeiro: H não atravessa NUMBER. Nenhum sufixo é contado duas vezes.

## Lema de bijeção (clássico, aqui com identificação de slots)

Todo caminho aceito possui uma única decomposição em blocos: zero ou mais
epsilon, depois exatamente um terminal verdadeiro. END absorve os epsilon
finais. Essa decomposição é única porque os terminais verdadeiros marcam as
fronteiras, não porque escolhemos fronteiras arbitrárias de não terminais.
Por aciclicidade, as recorrências acima enumeram uma vez cada rota do bloco,
com produto das mesmas folhas. A gramática JSON tem uma única derivação da
palavra sintática. Logo a floresta sobre scanners corresponde bijetivamente
aos caminhos do DAG original, conservando seus produtos.

Dentro de cada folha, substituir W[p,c]=sum_{t nos membros} w[p,t]. A
distributividade expande o caminho em eventos de IDs originais. O lexer
determinístico identifica um único estado de entrada por evento, portanto
o fato de grupos de estados distintos se sobreporem não duplica eventos.
Obtém-se o polinômio exato

    Z(w)=sum_{y JSON válido e compatível} product_p w[p,y_p].

Cada monômio contém exatamente uma variável original por posição. Z dividido
por product_p d[p] é a massa válida. Há saída impossível se Z=0, mas recusa
por recursos não decide Z. Não existe cauda topK omitida nesta operação.

## Marginais, amostragem e reuso

Avaliação inside calcula o polinômio no semianel dos inteiros não negativos.
Outside é diferenciação formal reversa do circuito: somas propagam o mesmo
adjunto, produtos propagam adjunto vezes inside do outro filho. A folha
(p,c) recebe ∂Z/∂W[p,c]. Levantar até IDs originais dá

    numerator[p,t]=w[p,t] sum_{c contém t} ∂Z/∂W[p,c].

O denominador condicional comum é Z. A soma de cada linha é Z, inclusive
nas posições fixas. Isso é consequência da multiafinidade por posição.

Amostre uma alternativa de soma proporcional ao seu inside inteiro e todos
os filhos de produto. Na folha, amostre t proporcional a w[p,t] dentro de
seus membros. Os fatores intermediários telescopam até product_p w[p,y_p]/Z.
Uma amostra contém exatamente um ID por slot. RNG usa inteiros, sem
arredondamento flutuante. Se Z=0, amostragem/marginais condicionais recusam.

O circuito é estrutural e vale sob mudança de pesos, clamps adicionais e
remasking de posições inicialmente livres. Quadros inicialmente fixos não
podem ser liberados; mudança de tamanho, lexer, gramática, bytes ou
vocabulário exige reconstrução. Não é garantia da trajetória da dLLM inteira.

## Custos e benefício que NÃO foi provado

Construir tabela completa do lexer e classes é preparação de serviço, com
custo sobre V e os bytes de todos os tokens. Por quadro, construir o DAG e
o trimming lexical custa O(n soma_q grupos(q)), além de seus arcos privados.
Se A são inícios realmente consultados, o fechamento custa O(sum_{a em A}
(vertices/arcos epsilon alcançados + saídas sintáticas alcançadas)); no pior
caso O(|vertices|(|vertices|+|arcos|)). END compartilhado custa O(|arcos|).
Essa é remoção ponderada epsilon clássica sob demanda, não um novo limite.

Se C é o total de nós do circuito e T de alternativas/ocorrências de filhos,
inside/outside custam O(C+T) operações aritméticas. Inteiros intermediários
de um circuito relevante representam subprodutos de slots, portanto têm
comprimento limitado pela soma dos comprimentos dos totais por slot mais
constantes de representação; considerar custos de multiplicação/adição
em bits. Conversão completa e saída de marginais custam Ω(f|V|+n), onde f
é o número de posições livres. Não prometer consulta sublinear nessas saídas.
Sample paga percurso da derivação e CDF dos grupos de originais consultados.

Em uma cadeia de n epsilon sem terminais internos, gramática Skip pode criar
constituintes de muitos intervalos; o fechamento compartilhado END tem n
passos. Esse exemplo apenas explica trabalho artificial da representação
antiga. Uma inferência de pilhas ou outro parser epsilon adequado também
pode usar tempo linear nessa cadeia. **Não é separação inédita frente a todos
os controles, nem justifica um benchmark feito dessa cadeia.** A vantagem
útil da implementação23 permanece hipótese até medição forte independente.

Antecedentes: Mohri2002 (inclui caso acíclico e execução sob demanda),
Opedal2023 (dedução ponderada Earley), Rivaud/Pachet2017 (amostragem CFG),
FactorDLM2026 (quocientes por fatores e planos reutilizáveis). Provas escritas
aqui especificam a composição e o tratamento dos IDs; não estabelecem
prioridade histórica dos princípios, revisão humana ou verificação do código.
