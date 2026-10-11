# Tentativa 27 — Fechamento finito antes da inferência irrestrita

Início: 2026-10-11, base `2aa488aa793ea69d0bbbc9db03addb35f9e076d9`.
Pesquisa isolada, sem alteração dos decoders mantidos ou do artigo principal.
**Hipótese em investigação; novidade e vantagem prática não confirmadas.**

## Oito critérios, antes do protótipo

1. **Uso:** amostragem de preenchimentos JSON pela predição de um passo de
   uma dLLM, com IDs originais e trechos fixos. A operação pretendida é produzir
   uma amostra exata do produto condicionado à gramática, com preparação menor
   quando conclusões profundas são raras. Configurações e chamadas recursivas
   admitem várias respostas; o modelo escolhe conteúdo, a gramática restringe
   sintaxe. Não é um modelo treinado de geração de regras.
2. **Significância e antecedente:** A25 perdeu todas as comparações primárias.
   Seu contador de fechamento ainda guarda alturas. Investigamos uma continuação
   de dimensão finita: resíduos da altura ou potenciais exponenciais. Resíduos,
   desigualdades de Chernoff, aproximação regular e rejeição por envelope são
   conhecidos; não serão reivindicados. A contribuição candidata teria de ser
   uma construção operacional com custo demonstravelmente menor e aplicação
   competitiva, além de uma diferença precisa para os antecedentes. Se for
   apenas uma instanciação sem consequência relevante, não sustenta a meta.
3. **Escolha:** reduzir preparação e primeira amostra frente aos controles
   completos de A25, preservando a distribuição e todos os tokens. O comparador
   forte é inferência CFG compacta ou counter+CARS, não rejeição ingênua.
   Potenciais são apenas limites; não podem ser apresentados como um sampler
   já implementado. EPIC resolve outra política: não recebe crédito de derrota
   por não calcular este posterior.
4. **Matemática:** provar inclusão da cauda JSON nos eventos de fechamento,
   decomposição exclusiva pelo primeiro overflow, custo sem todas as alturas
   e lei aceita exata se um envelope amostrável for implementado. O resultado
   comparativo pretendido é uma preparação linear em slots para dimensão fixa,
   frente ao contador completo cuja representação cresce com a altura possível.
   Isso não é limite inferior de todos os algoritmos CFG nem ganho semântico.
5. **Experimentos:** primeiro oráculos de correção independentes e diagnóstico
   declarado abaixo. Nenhum timing competitivo ou forward independente nessa
   fase. Uma campanha posterior exigirá protocolo congelado, todos os controles
   A25 fortalecidos e corpus externo novo, sem escolha pela vitória. Resultados
   anteriores são desenvolvimento, nunca confirmação independente nova.
6. **Custo completo:** tabela lexical, probabilidades de todo o vocabulário,
   compilação rasa, transferências ponderadas, limites, sampler e validação
   precisam ser pagos. Resíduos com módulo m custam O(n m F) operações; g
   potenciais custam O(n g F), mas seus inteiros crescem com os expoentes.
   Constantes, precisão em bits, forward e rejeições não são gratuitos.
7. **Objeção:** os limites podem ser frouxos e obrigar a aumentar módulo ou
   profundidade. Um controle clássico com a mesma continuação finita pode
   obter o mesmo ganho. A literatura de separabilidade de one-counter já usa
   altura exata abaixo de um limiar e resíduos acima dele; OS* já faz rejeição
   por envelope. Procurar essa redução antes de ampliar a implementação.
8. **Artigo:** falta confirmar diferença específica, provar benefício total,
   medir contra controles fortes e validar um ciclo neural pertinente. O
   protótipo não resolve essas pendências. Revisão humana e aceitação não
   foram obtidas. Esta pasta não é evidência de conquista publicável.

## Contrato do diagnóstico v1

O protótipo calcula limites da cauda, não altera probabilidades e não gera um
novo decoder. Originais, aliases, macro-tokens, posições fixas e EOS ausente
seguem o contrato atual. Cada evento é contado uma vez; nenhum token de origem
é inserido no suporte. Recusas continuam inconclusivas.

Antes de executar: enumerar instâncias pequenas reconhecidas por `json.loads`
e conferir todos os limites contra a cauda exata. Incluir alturas internas de
macro-tokens, strings com delimitadores, aliases, probabilidades nulas e
retornos negativos que os resíduos deliberadamente relaxam. Diagnosticar
também o mesmo primeiro head público completo, sem novos forwards, para todos
os módulos 2/3/4/8/16 e potenciais 0/1/2/4 declarados. Publicar todos os limites;
não selecionar o mais favorável como evidência independente. Essa captura já
foi usada, e não é um benchmark de utilidade ou velocidade.

As referências congeladas em `work/frozen/` são cópias, com hashes e origem,
e não imports de outra tentativa mutável. A formulação está em
[`work/theory-v1.md`](work/theory-v1.md) e a revisão em
[`work/antecedents-v1.md`](work/antecedents-v1.md).
