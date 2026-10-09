# Controles de perfis com menor custo de preparação

Plano declarado antes de medir qualquer discretização mais grossa. A rodada
v4 em execução continua sem alterações; a rodada final `--fast-forced` inclui
os dois controles adicionais em todos os inputs, não somente no caso promissor.
As versões anteriores permanecem preservadas.

1. **Uso:** mesma lei condicional PL sobre tokens originais de JSON/GLC. Testar
   se uma troca de preparação por rejeições torna o controle mais competitivo.
2. **Significância:** ajustar discretização é otimização clássica de comparador,
   não contribuição nova. Não justificar a mistura com um controle inflexível.
3. **Adoção:** manter perfis finos e adicionar forças 2 e 4; nenhuma escolha do
   melhor parâmetro para a mistura. Todos os métodos recebem mesmos recursos.
4. **Prova:** na árvore fixa, rho entre S e gamma^m S, com
   gamma=1+a/(2km). Cada soma com zero conserva um ponto da grade e não acrescenta
   arredondamento. Folha positiva mais no máximo m-1 merges positivos num caminho
   dão o limite. Todo S em uma célula satisfaz S>=rho/gamma^m. O mínimo exato da
   célula é atingível por decomponibilidade; f(S_min) domina f(S) nessa célula.
   Portanto a correção aceita exatamente mu_A para qualquer força declarada.
   O normalizador de rejeição é <=exp(a/2)(1+1/1024) Z_A. Usar limites simples
   2, 3 e 8 para a=1,2,4 respectivamente. Mais grosso não significa lei aproximada.
5. **Experimento:** mesmos nove inputs/48 eventos, sementes, três repetições,
   lote 4096 e checkpoint cumulativo 1024; sete controles iid. Na avaliação
   neural, mesmas seis entradas externas e duas potências; nove estimadores.
   Todos os status e perdas publicados. Critério predeclarado de redução 20%
   em CPU/wall e sinal nas três repetições continua, agora contra todos os
   controles concluídos. Sem selecionar casos ou limiar após medir.
6. **Custo:** toda construção, backpointer, correção, cache, aritmética e
   compilação continuam incluídos; mesmos tetos 1M células/3M transições/30s
   de preparação e 60s de amostragem em bulk. Nenhum clock do processo antigo
   é reutilizado como tempo de uma implementação modificada.
7. **Objeção:** granulações ainda maiores/adaptativas, linguagem compilada ou
   outra implementação podem ser melhores. A análise não promete um vencedor
   sobre todas as possíveis otimizações; estes controles atacam especificamente
   a escolha artificial de preparação cara com poucas rejeições.
8. **Artigo:** perfil continua antecedente, novidade/revisão seguem pendentes.
   Se apagar o ganho da mistura, concluir isso e conservar o sinal anterior
   como desenvolvimento, sem fabricar outro benchmark para recuperá-lo.
