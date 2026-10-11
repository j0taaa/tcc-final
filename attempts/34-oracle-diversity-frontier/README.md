# A34 — Fronteira matemática entre custo e diversidade de um oráculo

Iniciada em 2026-10-11 durante a campanha CONGELADA A32/v4. Investigação
independente, por enquanto escrita: não altera aquele produtor, não herda
seus timings e não tem novidade ou publicação confirmadas.

## Oito critérios, antes de qualquer implementação

1. **Uso real.** Coordenar dois candidatos de um decoder dLLM+GLC sem calcular
   a probabilidade de uma classe de transições. O primeiro candidato permanece
   literal e cada marginal continua sendo a do decoder original. Um head
   congelado permite draws auxiliares sem outro forward, mas rankings,
   recuperação e parsing continuam custando. JSON/DSL tem verificador externo;
   a classe nunca é a resposta correta obtida do gabarito.
2. **Diferença candidata.** Ruína do jogador, Cramér–Rao sequencial, fábricas
   de moedas e antitéticos são antigos. Investigar uma fronteira EXATA, para
   todo orçamento esperado real, da fração minimax do ganho de Fréchet obtida
   por QUALQUER acoplador p-blind regular. A contribuição NÃO é uma nova prova
   de correção desses princípios. A integridade dos outputs introduz um limite
   mais forte que Cramér–Rao quando o orçamento não é inteiro. A prioridade
   desse contrato específico ainda precisa de revisão, especialmente DeGroot
   1959, Ghosh1987 e os antecedentes de fábricas de Bernoulli.
3. **Por que escolher.** Para orçamento b>=2, a candidata fornece pelo menos
   eta(b)=1-2(2m+1-b)/(m(m+1)) da melhoria máxima binária sobre iid, m=floor(b),
   para TODA probabilidade desconhecida p. Nenhum algoritmo da classe pode
   garantir mais com esse orçamento. b=3 dá pelo menos1/3, b=4 pelo menos1/2.
   Isto não é vitória contra quem conhece p, iid com mais saídas, EPIC em
   latência total ou qualidade semântica geral. Esses controles são obrigatórios.
4. **Matemática.** Especificar oráculo, acesso apenas por amostragem, outputs,
   orçamento TOTAL e regularidade. Primeiro provar a fronteira inferior com
   score parado e aritmética inteira; depois a construção que a atinge, lei
   completa e corolário para uma transição estruturada. Provas escritas em
   `work/theory-v1.md`, ainda sem revisão independente ou Lean.
5. **Testes.** Não iniciar mais uma campanha neural apenas porque a fórmula
   parece nova. Primeiro resolver reduções e contraexemplos. Se sobreviver,
   oráculos independentes pequenos e protocolo externo congelado, controles
   com probabilidades conhecidas, corridas, walks, pools e custo completo.
   A32/v4 permanece uma avaliação distinta e conserva TODOS seus resultados.
6. **Custo completo.** Esperança b é contagem de draws, não tempo. A cauda da
   parada é exponencial, mas sua constante depende do orçamento; classificar
   transições pode ser caro. Incluir memória, bits, setup, forwards, parsing,
   transferência, recuperação e saída. O bound é de um passo; só a dominância
   fraca por encontro pode passar ao processo adaptativo, não a fração minimax.
7. **Objeções.** O resultado pode estar inteiro em estimação sequencial ou ser
   um corolário imediato pequeno demais. Uma classe sem sinal semântico dá
   ganho ZERO; eventos raros têm ganho absoluto no máximo p². Mais candidatos
   podem ser melhores. A prova não autoriza escolher p=1/2 num benchmark ou
   excluir um comparador prático que dispõe de logits/probabilidades.
8. **Artigo.** Faltam prioridade específica, argumento de significância,
   revisão matemática, implementação mínima e aplicação barata útil. Nenhuma
   dessas obrigações é cumprida por organizar outra tentativa. Se a redução
   eliminar a diferença científica, preservar e recusar, sem campanha extensa.

## Contrato e gate inicial

Somente notas matemáticas e revisão em `work/`. Não importa código de outra
tentativa. Não chamar uma construção clássica, uma lista de buscas negativas
ou um futuro oráculo de correção de confirmação de novidade/publicabilidade.

