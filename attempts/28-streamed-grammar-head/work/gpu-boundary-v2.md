# V2 — fronteira GPU/CPU com pesos binários preservados

Addendum anterior à implementação/timings. V1 permanece no snapshot próprio.

1. **Uso:** um head dLLM entrega pesos binary64 não negativos na GPU; amostrar
   JSON conjunto no vocabulário inteiro com o mesmo posterior CFG em CPU.
   Preservar exatamente a distribuição dos números representados, sem trocar
   soma inteira por soma flutuante ou ignorar probabilidades pequenas.
2. **Diferença:** agrupamento FlashSampling e superacumulação ExBLAS/Neal são
   conhecidos. A candidata é uma fronteira implementada para condicionamento
   conjunto com recuperação posterior de IDs. Não é nova teoria de soma ou
   prova de prioridade. Suficiência para publicação ainda precisa de vantagem
   integral e confronto com esses antecedentes; um kernel que funciona não basta.
3. **Escolha:** diminuir comunicação/conversão de todos nV pesos para somas
   por blocos de classes e n blocos escolhidos. Comparar com transferência
   integral + NumPy vetorizado e com PyTorch vetorizado inteiro na GPU; ambos
   recebem os mesmos blocos, parser, pesos, budgets e recuperação eficiente.
   Não comparar só contra o loop Python antigo. EPIC nativo tem outra operação
   e deve receber acelerações comuns; não há vitória sobre EPIC aqui.
4. **Prova:** cada binary64 finito positivo é m*2^e com m inteiro de53 bits
   (subnormal incluído). Por posição, remover o expoente mínimo comum apenas
   escala a distribuição. Somar dígitos de32 bits por bloco B<=1024 em uint64
   sem carry/overflow: cada soma é menor que B*2^32<=2^42. A CPU recompõe o
   inteiro somando os dígitos deslocados; carry fica implícito nessa soma.
   Massas de classe dão o caminho condicionado. Escolher bloco pela massa e
   ID pela massa dentro do bloco preserva o evento original por disintegração.
   Para C classes, M<=C+ceil(V/B) blocos; P palavras por peso, transferir
   O(n(MP+B)) palavras em vez de nV. O benefício exige MP+B<V; não é lower
   bound de todos os algoritmos (reservatórios GPU também podem evitar nV).
5. **Validação:** primeiro oráculo opt-in GPU com binary64s extremos, zeros,
   subnormais, NaN/Inf/negativos, aliases, blocos incompletos e uma partição
   independente. Conferir TODAS as somas contra inteiros Python, incluindo os
   controles vetorizados. Não cronometrar antes de congelar protocolo próprio.
6. **Custo:** manter pesos nV na GPU nesta versão; NÃO reivindicar menor pico
   da cabeça neural. Pagar classificação/partição, exponentes, kernels,
   transferências, carry CPU, parser, RNG, leitura dos blocos e IDs. Projeção
   completa permanece. O softmax compartilhado pode ser GPU, mas então a lei
   declarada é a saída GPU nova, não igualdade bit a bit com captura CPU antiga.
   Primeira chamada JIT deve ser registrada separadamente de regime compilado.
7. **Objeções:** vetorização CPU pode anular o ganho; P grande, muitos grupos
   pequenos ou parsing podem dominar. Recuperação de blocos acrescenta viagem
   GPU/CPU. Um algoritmo intervalar clássico pode preservar amostragem exata
   com menos trabalho que inteiros completos. Investigar, sem ignorá-lo por
   resolver melhor a operação. A política não depende dos sorteios ocultos.
8. **Artigo:** faltam oráculo de implementação GPU, replay, protocolo de custo
   integral, nova execução neural e evidência independente. Não substituir o
   artigo atual por esta hipótese, nem atribuir números antigos ao novo código.

Antecedentes adicionais conferidos: Neal2015
https://arxiv.org/abs/1505.05571 e ExBLAS2015
https://perso.lip6.fr/Stef.Graillat/papers/ITNG2015.pdf. GSP README foi finalmente
obtido pela API oficial GitHub em2026-10-11; confirma projeção restrita conhecida,
com pequenas diferenças numéricas de redução. Seus números são reportados pelo
autor, não replicação nossa. Não sobrescrever a ficha v1 que registra o acesso
inicial incompleto. ADZ1999 é antecedente importante de geração combinatória
com aritmética flutuante; a extensão ponderada/intervalar deve ser conferida
antes de reivindicar novidade de precisão adaptativa.

Esta fase só valida correção. Timings/capturas novas requerem protocolo
congelado posterior e todas as perdas/recusas preservadas.
