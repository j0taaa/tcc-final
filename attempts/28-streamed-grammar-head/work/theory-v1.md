# Resumo amostrável de uma cabeça: contrato e prova escrita

## Definições

Há n slots, IDs originais T={0,...,V-1}, pesos inteiros w_i(t)>=0 e
D_i=sum_t w_i(t)>0. Uma posição fixa possui apenas seu ID com peso1.
q(y)=prod_i w_i(y_i)/D_i é o produto congelado. Uma partição c:T->C
preserva a aceitação: existe A subset C^n tal que y é válido se e somente
se (c(y_1),...,c(y_n)) está em A. No lexer JSON, usamos o efeito em TODOS
os estados lexicais; efeitos incluem operações estruturais completas,
não somente altura ou estado final. Uma derivação múltipla não duplica y.

Defina S_i(a)=sum_{t:c(t)=a}w_i(t). Para cada par (i,a) positivo, obtenha
um sorteio independente R_i,a com P(R_i,a=t)=w_i(t)/S_i(a), dentro da
classe. Esses sorteios são independentes do sorteio gramatical seguinte.
O resumo guarda apenas S_i(a), R_i,a, D_i e IDs fixos. Os pesos originais
e os logits podem ser descartados após a acumulação.

## Teorema1 — Lei conjunta original

Se Z_A=sum_{a in A}prod_i S_i(a_i)>0, sorteie a in A com probabilidade
prod_i S_i(a_i)/Z_A e retorne y_i=R_i,a_i. Então

    P(y) = 1[valid(y)] prod_i w_i(y_i) / Z_A = q(y | valid).

Prova: y determina exatamente uma sequência de classes a. Se a não é
aceita, sua probabilidade é zero. Se aceita, a probabilidade de a vezes
as probabilidades dos sorteios internos é

    prod_i S_i(a_i)/Z_A * prod_i w_i(y_i)/S_i(a_i)
    = prod_i w_i(y_i)/Z_A.

As massas zero não são sorteadas. Somando por todos os IDs de cada classe
mostra também que Z_A é o numerador da massa válida original. Aliases
continuam eventos distintos; nenhum texto representativo substitui seu ID.
O resultado usa fatorização hierárquica conhecida, não introduz Gumbel-Max.

## Teorema2 — Acumulação exata em fluxo

Para cada classe, comece com S=0. Ao receber um ID t com peso w>0,
faça S'=S+w e substitua R por t com probabilidade w/S'. Um inteiro
uniforme em {0,...,S'-1} decide a substituição. Ao final, R tem a lei
w(t)/S. Prova por indução: o novo ID tem sua probabilidade declarada;
cada ID antigo u tem w(u)/S * S/S' = w(u)/S'.

Massas/sorteios de blocos disjuntos também podem ser combinados por essa
mesma regra. Isto é reservatório ponderado e fatorização conhecidos.
Não requer variáveis Gumbel aproximadas ou somas flutuantes.

## Consequência de memória e limite da comparação

Com pesos de b bits, S e D precisam de no máximo b+ceil(log2 V) bits,
e cada R de ceil(log2 V) bits. O resumo ocupa
O(nC(b+log V)) bits, além da partição O(V log C), pesos do modelo,
blocos temporários e floresta gramatical. A passagem de referência faz
O(nV) adições/decisões de RNG; em bits há custo por inteiro e rejeições
do randbelow. Não é um algoritmo que evita projetar todos os tokens.

Uma interface que RETÉM cada peso individual ocupa Omega(nVb) bits
no pior caso. Para C << V, este resumo tem memória menor nessa fronteira.
Isso não é limite inferior de toda alternativa: um controle que processe
grupos em fluxo pode ter a mesma memória. Kernel fundido precisa ser
medido contra esse controle, não apenas contra uma tabela desnecessária.

Se a avaliação da floresta custa H operações, a fase gramatical trabalha
com S por classe/local-effect e custa O(H), seguida de O(n) saída.
Inteiros da floresta podem crescer até n(b+log V) bits. Nenhum custo do
backbone, projeção, compilação ou aritmética é removido da comparação.

## Resumo de uso único e evolução da dLLM

Uma segunda chamada pode reutilizar os mesmos R e correlacionar IDs,
mesmo quando as classes são sorteadas novamente. Não promete iid; esta
interface consome o resumo. Se a escolha do evento A depender dos R
observados, a fatorização acima também deixa de ser aplicável. Restrição
estrutural independente pode ser declarada antes do sorteio; uma nova
chamada adaptativa exige novos pesos/sorteios ou uma interface diferente.

Em um ciclo neural, cada resumo novo é gerado a partir da mesma cabeça
congelada que o comparador e de aleatoriedade fresca. Se os kernels de
transição são os mesmos pela prova acima, a lei da trajetória inteira
coincide por indução. Isso preserva somente a política especificada de
amostragem gramatical; não é igualdade ao decoder EPIC ou à distribuição
nativa da dLLM condicionada apenas no estado terminal.

## Obrigações ainda abertas

Provar o compilador completo, construir fusão neural numérica adequada,
medir custos totais e localizar diferença científica suficiente. Um
kernel que acumula massas por floats pode perder bits ou massa; não
herda automaticamente a exatidão desta referência inteira. Para float32
positivo, um acumulador de bits fixos pode representar a soma exata dos
pesos representados; superacumulação é antecedente conhecido. Exponenciar
um logit e sorteá-lo em precisão finita são operações com leis próprias.
