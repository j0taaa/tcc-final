# Fechar a objeção dos limites de representação

Plano registrado antes da nova medição. A campanha indexed v6 continua intacta:
ela revelou recusas por 1M células/3M transições, anteriores ao prazo. Não usar
essas recusas como prova de que um controle com mais memória seria mais lento.

1. **Uso:** mesma auditoria iid do posterior PL de tokens descartados da dLLM
   sob JSON, mesmo circuito e evidência; nenhuma mudança do alvo.
2. **Significância:** ampliar limites e medir RSS é controle de recursos,
   não novidade científica nem nova heurística para favorecer o candidato.
3. **Adoção:** verificar se as vantagens da mistura sobrevivem a um controle
   por perfis que recebe mais espaço para suas tabelas. Não recomendar a mistura
   com base apenas nas recusas artificiais dos contadores anteriores.
4. **Matemática:** a representação e moedas são as de IndexedProfiles; somente
   as condições de recusa mudam. Sem recusa, os mesmos seeds conservam caminhos,
   contagens e histogramas; isso será verificado. Nenhuma garantia iid é atribuída
   ao condicionamento a um prazo de parede ou recusa dependente de memória.
5. **Protocolo:** todas as nove entradas/48 eventos e três granulações 1/2/4;
   três repetições, 4096 draws e prefixo cumulativo 1024. Mesmos seeds, preparação
   30s e amostragem 60s. Nova campanha sequencial, sem modelo nos timings.
   Tetos de tabelas passam a 10M células/30M transições. Proteção Linux de 3 GiB
   de RSS do processo, checada a cada 4096 combinações e 256 draws; o possível
   excesso entre
   verificações não é um teto físico rígido. Antes do plano havia 8,6 GiB de
   MemAvailable na máquina. Não interromper processos externos. Toda recusa,
   inclusive memória/prazo, permanece no resultado. Critério de 20% anterior
   não muda; não escolher somente eventos em que a mistura venceu.
6. **Custo:** preparação, chamadas de proteção, aritmética, saída e compilação
   entram nos clocks. Reportar RSS das verificações além da memória lógica.
   Esse RSS inclui dados/backend e reservas do alocador, não só tabelas. Os
   métodos anteriores não tiveram RSS registrado: não inventar uma comparação
   de pico de memória, nem afirmar que todos usaram um mesmo teto de RSS.
7. **Objeção:** outros compiladores/linguagens e MCMC podem ser preferíveis.
   Mesmo com mais recursos, uma recusa não prova impossibilidade intrínseca.
   Esta é a última verificação desta objeção concreta, não uma busca de
   configurações/casos até produzir uma vitória.
8. **Artigo:** consolidar a decisão depois desta comparação. Estudo neural
   continua fechado pela enumeração versus piso de custo extra zero: mudar
   somente recursos de um sampler iid não melhora sua variância. Não atribuir
   a essa campanha treinamento, prioridade, superioridade sobre EPIC ou revisão
   humana. Preservar as campanhas menores e suas conclusões.
