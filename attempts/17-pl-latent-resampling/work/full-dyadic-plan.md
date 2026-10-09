# Refinamento de coeficientes e decisão de utilidade

Iniciado em 2026-10-08 após o usuário solicitar continuar até decidir se há
benefício útil. A v5 permanece congelada. Oito critérios: os do README valem;
a correção abaixo altera somente o custo da representação, sem mudar política,
suporte, alvo ou hipótese de novidade. Não é contribuição científica isolada.

1. Uso: posterior dos tokens descartados numa seleção PL, potencialmente para
   reduzir variância em treinamento on-policy de geração JSON/GLC.
2. Significância: arredondar coeficientes também é uma otimização numérica
   conhecida. O resultado candidato continua o kernel condicional com limite
   uniforme, não essa alteração. Publicação/prioridade permanecem em aberto.
3. Comparadores: mesmos controles competentes, com arredondamento aplicado
   também ao majorante do SingleTilt. Variáveis auxiliares são controle de
   aplicação separado; não exigir iid para manter um score sem viés.
4. Prova: obter o coeficiente superior em erro delta_a/2 e arredondá-lo para
   cima num denominador dyádico comum com passo <=delta_a/2. O erro total é
   <=delta_a, preservando f<=2 Rbar<=(2J+1)f e a moeda racional exata. As
   massas dos componentes passam a ter denominadores que dividem o produto
   dos denominadores das q locais vezes uma única potência de 2. Não usar
   LCM de coeficientes com fatores primos diferentes quando dispensável.
5. Protocolo: reaplicar os nove inputs M34, os 48 eventos nativos/sementes,
   as três repetições, quatro métodos, limites e lotes 1/4/16 existentes.
   Todos os casos ficam. É desenvolvimento no mesmo conjunto, não held-out.
6. Custo: preparação, consulta, primeira saída/lote, bits e recusas publicados;
   não converter tentativas em segundos. Forward/backward não entram nesse
   replay. Medição neural posterior requer protocolo próprio antes de executar.
7. Objeções: pode acelerar controles mais que a mistura; uma esperança menor
   não basta para custo total; Gibbs/enumeração podem tornar o kernel dispensável
   em treinamento. Nenhum benchmark favorável será eleito como conclusão geral.
8. Falta: comparar custo vezes variância em gradientes/política concretos e
   delimitar anterioridade. Não encerrar essa tarefa somente com tarefas novas.

O script anterior chega a normalizadores de quase meio milhão de bits, contra
inside muito menor. Isto motiva uma correção localizada antes de decidir que
seu custo é uma limitação essencial do método matemático. Não altera os registros
anteriores: nova variante `full-dyadic`, saída/evidência/snapshot próprios.
