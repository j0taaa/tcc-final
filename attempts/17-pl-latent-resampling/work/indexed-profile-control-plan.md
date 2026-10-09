# Perfis por índices: controle competente da representação

Plano antes de medir a representação compacta. As campanhas anteriores continuam
completas, incluindo v5 atualmente em execução; seu código já foi carregado.
Não mudar a mistura, a política, os casos, a granulação ou os limites.

1. **Uso:** mesmas consultas iid ao posterior PL/GLC de tokens descartados.
2. **Significância:** inteiros em vez de rótulos racionais e memoização são
   engenharia clássica do comparador, não contribuição científica nova.
3. **Adoção:** diminuir custo evitável em todas as três granulações de perfis.
   Comparar com a campanha final de sete controles, preservando suas perdas.
4. **Prova:** para rho_j=rho_min gamma^j, rho_a+rho_b=
   rho_min gamma^min(a,b)(1+gamma^|a-b|). O índice arredondado é min(a,b)+d_t,
   d_t=ceil(log_gamma(1+gamma^t)). Cache por t; soma com zero retorna o outro
   índice sem arredondamento. As folhas usam ceiling racional exato, com cache
   por taxa. O relabeling é bijetivo e mantém massas, mínimos, backpointers,
   ordem de inserção, CDFs e moedas. Portanto preserva até caminhos/tentativas
   para o mesmo PRNG, quando ambos concluem. Nenhum float/log numérico é usado.
5. **Protocolo:** nova campanha somente destes três controles; todos os nove
   inputs/48 eventos, três repetições, 4096 saídas e prefixo cumulativo 1024.
   Mesmo orçamento e seeds. Não executar modelo durante os timings. A comparação
   entre campanhas tem os mesmos estados/repetições e clocks de processo, mas
   não é pareamento contemporâneo de latência. Aplicar o critério anterior de
   20% CPU/wall e sinal nas três repetições; relatar todas as recusas.
6. **Custo:** preparação, cache, aritmética, saída e compilação entram no tempo;
   memória reportada é lógica. Corrigir a representação não muda a operação
   matemática nem faz desaparecer seu custo de tabelas/combinações.
7. **Objeção:** outras otimizações/linguagens podem melhorar tempos. Eliminar
   essa ineficiência óbvia é necessário antes de recomendar a mistura. Não
   exigir exclusividade sobre todos os algoritmos, mas não premiar um controle
   propositalmente caro. Congelar esta comparação; não selecionar novos casos.
8. **Artigo:** não promover índices/cache como novidade. Não repetir forwards
   neurais só porque mudou o controle: sua lei iid é a mesma. O estudo neural
   é fechado contra enumeração se até o piso de custo zero dos outros samplers
   iid não a superar. Se esse piso não bastar, declarar avaliação de custo
   pendente em vez de inventar o timing neural da representação nova.
