# Controle com limites estruturais exatos

As primeiras campanhas usam `L=sum min lambda_i`, válido mas por vezes
inatingível sob a gramática/evidência. Uma eventual vitória contra esse
rejeitador não deve ser promovida sem comparar o melhor envelope constante.

Antes de nova medição, será acrescentada uma passagem min/max clássica no
mesmo circuito, descartando somente escolhas incompatíveis com a evidência.
Ela calcula `L*=min_{F_A} S` e `H*=max_{F_A} S` sem enumerar os caminhos.
Rejeição usará `f(L*)`; mistura terá a grade em `[L*,H*]`. Cada método pagará
sua passagem de preparação. Os casos, eventos, sementes, budgets, repetições
e lotes continuam os mesmos. Resultados das versões anteriores serão mantidos.

Na avaliação final, considerar também os controles sem essa preparação,
tomando o melhor custo observado entre as configurações competentes. Esse
controle otimista não é um seletor implementado; serve para impedir que a
mistura pareça vantajosa só porque o concorrente pagou uma passagem desnecessária.

Os oito critérios do README permanecem: essa é otimização/controle clássico,
não novidade; a finalidade é testar a vantagem contra um concorrente melhor;
correção decorre de min/soma e max/soma em circuito acíclico; custo adicional
`O(F)` e aritmética racional entram na preparação; a objeção é desaparecer a
vantagem observada; publicação/treinamento continuam sem confirmação.

O oráculo enumerativo deve conferir os dois extremos exatamente e integrar
as leis condicionais novamente antes do novo replay. Escolher esta versão
depois dos primeiros resultados é desenvolvimento declarado, não um novo
conjunto de validação independente nem justificativa para alterar os inputs.
