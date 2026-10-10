# Certificado de profundidade: formulação e prova escrita inicial

## Operação

Uma predição produto congelada q sobre n IDs de tokens originais, slots fixos,
bytes composicionais, EOS ausente. Converter floats finitos em pesos inteiros
w[p,t], normalizados pela soma exata de cada posição; fixos são deltas. D é
produto dos denominadores. Todos os zeros/aliases/bytes permanecem explícitos.

O lexer JSON determinístico valida UTF8/literais e emite terminais de sintaxe.
Dentro de strings, '[' e '{' não abrem estruturas. Seja h(y) a máxima
profundidade dos delimitadores EMITIDOS, não a contagem de caracteres crus.
Se J são eventos originais cujo texto é JSON válido, J_d={y em J:h(y)<=d}.
Seja L_d=q(J_d), R_d=q(J\J_d). O objetivo é uma amostra de q(.|J_d) com
certificado de distância frente a q(.|J); não chamá-la amostra exata de J.

## Lema 1 — Identidade de condicionamento (antecedente elementar)

Se L_d>0, então TV(q(.|J_d),q(.|J))=R_d/(L_d+R_d).

Prova: nos eventos de J_d, a razão das duas probabilidades é a constante
(L_d+R_d)/L_d. Fora dele, a primeira é zero. As duas partes da soma das
diferenças absolutas têm massa R_d/(L_d+R_d); dividir por2 dá o resultado.
Portanto, para qualquer upper bound U_d>=R_d, temos

    TV <= delta_d = U_d/(L_d+U_d).

Isso é válido mesmo quando q(J) é minúsculo. Não usar U_d diretamente como
erro condicionado. Se L=U=0, a validade completa tem massa zero. Se L=0<U,
nada autoriza amostragem/certificado pequeno. Recursos insuficientes são
inconclusivos. Limites de marginais e de expectativas de funções [0,1]
também são delta_d, por definição de TV.

## Lema 2 — Upper bound por contador determinístico

Construa C_d: eventos lexicalmente completos cujas profundidades parciais
jamais são negativas, terminam em zero e excedem d em algum momento.
Ignorar tipo de fechamento e regras de chave/vírgula/valor: isso relaxa J.
Todo evento de J\J_d pertence a C_d. Logo U_d=q(C_d)>=R_d.

Para um efeito lexical (q→q',palavra de terminais), pré-calcular a tripla
(net,minprefix,maxprefix) dos passos +1 para aberturas, -1 para fechamentos
e0 para outros terminais. Um estado do counter é (q,altura,overflow).
Descartar se altura+minprefix<0; atualizar altura pelo net e overflow por
altura+maxprefix>d. Somar probabilidades de TODOS os tokens originais com
o mesmo efeito de counter; cada ID possui efeito determinístico. No final,
aceitar apenas finish(q) possível, altura0 e overflow verdadeiro. Flush
NUMBER final não muda altura.

A recorrência forward soma produtos das mesmas probabilidades de tokens.
Não há nondeterminismo de storage que multiplicaria derivações de um evento.
Assim calcula a probabilidade EXATA da linguagem relaxada C_d, inclusive
aliases e tokens que atravessam múltiplos delimitadores. Massas estão em[0,1].

Se H_d é o evento de atingir altura>d com prefixo lexical válido/não negativo,
sem exigir a conclusão lexical/estrutural, C_d⊆H_d. O bound de hit é q(H_d).
Portanto o certificado fechado é sempre ao menos tão forte:

    U_d<=q(H_d); delta_d<=q(H_d)/(L_d+q(H_d)).

Pode ser estrito: tokens/prefixos que abrem fundo mas não conseguem fechar no
orçamento restante pertencem a H_d e não a C_d. Essa é explicação/objeto de
prova, não licença para selecionar benchmark real com esses exemplos.

## Custo

Se Q é o lexer e F o total de efeitos agrupados do counter, altura tem limite
físico Dmax pela soma do máximo de aberturas por slot; não impor teto guessed.
Forward custa O(n Dmax F) operações aritméticas, memória O(Q Dmax) inteiros
com duas camadas e flags. Agrupar somas de tokens custa O(f|V|+n F), ou usar
classes globais pré-computadas sem descartar originais. Dmax<=n J, com J o
máximo de terminais de abertura emitidos por token; contar J e os bytes.
Preparação de serviço é paga/documentada; suporte omitido não é renormalizado.

J_d é regular: JSON tem um recognizer determinístico de pilha visível, com
controle finito c e alfabeto de frames Gamma. Até altura d, no máximo
c sum_{k=0}^d |Gamma|^k estados, antes de composição lexical. Parsing de
macrotokens deve verificar alturas INTERNAS do token, não só sua altura final.
Calcular L_d e amostrar com DP finita custa linear em n e no automato efetivo,
mas exponencial em d. Não prometer baixo custo para d grande. Recuperar todas
as marginais originais continua Ω(f|V|+n); produzir um sample é ao menos Ω(n).
Inteiros de submassas têm O(soma_p bitlen(d[p])) bits; incluir soma/produto.

Isto evita inferência irrestrita APENAS quando um d pequeno já certifica a
tolerância e cabe nos recursos. Não é bound universal de speedup ou um novo
princípio de regularização; a diferença candidata é o certificado operacional.

## Lema 3 — Trajetória inteira, sob política comum

Considere um decoder referência que, em cada história h_t, obtém q_t do modelo,
amostra o posterior COMPLETO q_t(.|J_t) e aplica a política K_t. O decoder
aproximado recebe o mesmo q_t quando as histórias coincidem e usa um J_{t,d}
certificado com TV<=epsilon_t(h_t). K_t é A MESMA aplicação aos tokens, ao
quadro e às probabilidades originais, com aleatoriedade compartilhável.

Usar acoplamento maximal da proposta em histórias iguais: a probabilidade de
divergência nova é no máximo epsilon_t. Se as propostas coincidem, a política
comum preserva a coincidência da história seguinte e portanto dos próximos
inputs ao modelo. Por soma sobre o primeiro desacoplamento, TV das trajetórias
e das saídas finais é no máximo soma_t epsilon_t (ou orçamento e se essa soma
é <=e ao longo de toda história admitida). O modelo pode mudar suas predições
arbitrariamente: não se exige estabilidade de seus logits quando h é igual.

Esse é um lema clássico de perturbação de kernels, aqui especificando sua
ligação com a dLLM. Também limita a diferença de qualquer métrica semântica
em[0,1] entre ESTES dois decoders por e; não prova que o baseline é bom nem
qualidade superior ao EPIC, que executa outra operação/política.

Não usar silenciosamente marginais aproximadas numa política diferente:
argmax/threshold podem mudar abruptamente. Usar probabilidades ORIGINAIS
comuns, ou provar robustez da decisão a intervalos de marginais. Massa zero,
falhas e timeouts requerem contrato próprio; não condicionar artificialmente
o resultado apenas aos pedidos exitosos. Se um d não certifica, aumentar d
ou recorrer ao posterior completo; nenhum sample sem certificado vira sucesso.

## Obrigações antes de implementar extensivamente

- Conferir Denkinger2017/Mohri-Nederhof2001: regularização e upper bounds
  ponderados são conhecidos; não criar novidade por rebatizar um corolário.
- Conferir antecedentes de certificados de normalização/TV e approximation
  de CFG sob probabilidades de palavra/token; priority ainda não estabelecida.
- Construir um recognizer bounded-depth independente e testar o counter por
  enumeração de eventos ORIGINAIS, incluindo altura interna a um macrotoken.
- Protocolo honesto com TODOS os controles fortes e falhas, antes de timings.
- Demonstrar ao menos um custo útil/certificado em entradas externas novas;
  a inequação sozinha não garante utilidade se sempre força profundidade cara.
