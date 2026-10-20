# A84 — Certificado de paralelismo com a segunda alternativa

20/10/2026. Candidata em investigação, **não selecionada como tema central**.
Este contrato precede implementação e medição. Não reabre aplicações encerradas.

## Operação e diferença candidata

Um dLLM mascarado prevê uma distribuição categórica em cada posição. Escolher
quantos argmaxes fixar no próximo passo, sem treinamento ou forward adicional.
Para posição i, sejam c_i a maior probabilidade, q_i a segunda maior e
e_i=1-c_i. Para um conjunto S, usar

    sum_{i in S} e_i + max_{i in S} q_i < 1-delta.

O antecedente direto é [Fast-dLLM++, teorema 4.1 e §6](https://arxiv.org/html/2606.02955v1):
usa max e_i no segundo termo e declara não explorar gaps/full softmax.
[Prophet](https://arxiv.org/abs/2508.19982) e
[Jot](https://arxiv.org/abs/2602.11133) já usam top-2; não se atribui novidade
ao sinal. A diferença candidata é o certificado conjunto ótimo sob marginais
completas e sua política de seleção. Boole, Fréchet, acoplamentos e heap são
clássicos; esta especialização não estabelece prioridade mundial. A auditoria
de antecedentes continua pendente. Não há resultado novo de GLC neste núcleo.

## Prova escrita e limites

Fixe um contexto e uma lei conjunta P cuja marginal em cada posição seja
exatamente a distribuição declarada. Não suponha independência. Defina y pelos
argmaxes e E=sum e_i. Boole dá P(y)>=max(0,1-E). Para qualquer z!=y, existe
i com z_i!=y_i, logo P(z)<=p_i(z_i)<=q_i<=max q. Portanto, se
1-E-max q>delta>=0, y é o modo conjunto único, com gap maior que delta.

Quando E<=1, o limite é atingido: atribua massa 1-E a y e massa p_i(v)
à palavra que difere de y somente em i, com valor v!=y_i. As massas somam 1
e reproduzem todas as marginais. O rival mais provável tem massa max q.
Logo nenhum certificado válido para **todas** as leis com essas mesmas
marginais pode garantir gap>delta quando esta desigualdade falha nesse regime.
Quando E>=1, o limite de Fréchet permite P(y)=0: escolha eventos de erro
com essas probabilidades cuja união cobre o espaço e, dentro de cada evento,
distribua rótulos errados conforme p_i(v)/e_i. Assim y não é modo único.
O certificado caracteriza a possibilidade de certificar gap positivo nesta
classe irrestrita. Isso é uma prova escrita, não uma verificação Lean.

Como q_i<=e_i, o teste domina o de Fréchet no mesmo conjunto e margem.
**Mas acrescenta no máximo uma posição** frente ao melhor prefixo Fréchet:
de um S aceito, retire j de maior e. Então

    sum_{i in S\{j}} e_i + max_{i in S\{j}} e_i <= sum_{i in S} e_i < 1-delta.

O prefixo de menores e com |S|-1 posições também passa. Este teto é material;
não se promete aumento arbitrário de paralelismo. Exemplo estrito: duas
posições com distribuições (.7,.1,.1,.1), delta=.25. O novo gap certificado
é .3; Fréchet dá .1. A lei de zero/um erro atinge .3.

Selecionar cardinalidade máxima pode ordenar posições por q e manter um
max-heap dos e já vistos. Após cada inserção, retire os maiores e enquanto
sum e+q_atual>=1-delta; guarde o maior conjunto encontrado. Para cada teto q,
os menores e oferecem a maior cardinalidade viável. Conforme o teto aumenta,
o orçamento diminui, e itens descartados por custo não passam a ser necessários
para melhorar a cardinalidade. Custo O(n log n), O(n) memória, além de top-2
no vocabulário. Esse mecanismo clássico não é reivindicado como invenção.

Os logits reais são aproximações e floats: o teorema não certifica que sejam
marginais verdadeiras, calibradas, nem intervalos numéricos rigorosos. O piloto
é um decoder heurístico justificado por um resultado condicional. Não preserva
a trajetória nativa e não garante acurácia semântica, menor NFE total ou
latência: revelar mais agora pode piorar os contextos seguintes. Fallback de
uma posição é explicitamente **não certificado** quando o teste não aprova.

## Utilidade, controles e custo

O consumidor é geração geral com menos forwards, a mesma operação de
Fast-dLLM++; não exige documentos, duas priors artificiais ou lei congelada
exata como fim. Benefício verificável: parede completa por resposta com
acurácia e truncamentos preservados. A oportunidade pode ser pequena.
O custo inclui carregar/quantizar modelo, tokenização, todos os forwards,
softmax/top-2, seleção, sincronização, finalização EOS e decodificação.
Separar carga única de latência por pedido e reportar ambas. Sem claims de
amostragem racional/exatidão de software GPU. Nenhum RNG de geração é usado
no decode guloso; sementes controlam inicialização/backend.

Controles competentes: Fréchet prefixo original, mesmo prefixo com runner-up,
seleção ótima com runner-up, factor/threshold, Prophet/Jot nos contratos
publicados. O piloto limitado abaixo compara os dois primeiros, com trabalho
top-2 cobrado somente onde necessário. Ele pode eliminar a candidata;
**sozinho não aprova o tema nem estabelece superioridade geral**. Seleção
ótima, novas gramáticas ou outros modelos exigem justificativa posterior.

## Protocolo prospectivo V1: piloto pequeno de descarte

Sem olhar respostas do modelo, selecionar oito perguntas por família usando
os menores SHA256 do texto da pergunta, com desempate por índice original:

- GSM8K test, `openai/grade-school-math`, commit
  `3101c7d5072418e28b9008a6636bde82a006892c`,
  `grade_school_math/data/test.jsonl`.
- BBH word_sorting, `suzgunmirac/BIG-Bench-Hard`, commit
  `9ee07bd481feebf959a6b59d61ea57bdcf30964d`, `bbh/word_sorting.json`.

Fontes brutas ficam em cache ignorado; registrar URL, hash integral, índices,
perguntas e golds usados no resultado pequeno. Gold só entra na avaliação.
As fontes e suas licenças permanecem dos respectivos autores; não se alteram
os datasets. Prompt GSM8K: pergunta + instrução para explicar e encerrar com
`Final answer: NUMBER`. Prompt word_sorting: pergunta + instrução para retornar
somente a lista ordenada. Template oficial do tokenizer, sem exemplos/golds.

Backbone LLaDA-8B-Instruct local, snapshot
`08b83a6feb34df1a6011b80c3c00c7563e963b07`, NF4 + double quant, BF16compute.
Batch1, canvas256, blocos32, delta=.25, decode guloso monotônico, sem KV-cache.
MASK proibido como previsão; terminais EOS nativo126081 e `<|eot_id|>` do
tokenizer oficial. Pode parar somente quando
existe EOS comprometido e todas as posições anteriores já estão reveladas.
Não renderizar MASK para transformar incompletude em sucesso. Ordenar por
confiança, desempate por posição; os dois métodos usam esse mesmo prefixo.
Comparadores `frechet` e `runner_up`; ambos fazem softmax float32, mas somente
o segundo consulta top-2. Fallback: argmax de maior confiança. Número máximo
de forwards256; sem timeout de parede neste piloto. Manter erro, recusa,
interrupção e truncamento. Nenhum autotuning.

Um aquecimento não pontuado por método, com prompt 'Say hello.', canvas32.
Executar cada par em ordem alternada pelo índice selecionado. Depois repetir
uma vez em ordem inversa; total64 decodes pontuados. Semente84001, threadsCPU4.
Registrar IDs, resposta, NFEs, seleção por passo, tempos, memória, acerto e
truncamento. Não armazenar heads grandes. Registrar hardware/software/commit.
Inspecionar outros processos CUDA antes/depois de cada decode, fora do tempo
por pedido; sobreposição observada torna o gate de tempo inconclusivo. Essa
instrumentação não exclui trabalho transitório entre inspeções. Falhas de
carga e aquecimento também devem ser preservadas; não encerrar processos alheios.

GSM8K: extrair número após último `Final answer:` (fallback último número),
comparar com número depois de `####` do gold. Word_sorting: ignorar espaços
externos, normalizar whitespace; comparar exatamente com target. Registrar
textos completos para detectar falhas do avaliador sem mudar retroativamente
o score. Parse de número via Decimal, sem arredondamento silencioso.

Gate de descarte: exigir 64/64 decodes completos tecnicamente, nenhum acerto
líquido perdido em cada família, nenhuma elevação de truncamento por família,
e razão de soma de tempos runner_up/frechet<=.90 **em cada família**, somando
as duas ordens. Se falhar, encerrar este piloto sem trocar prompts, margens,
subset ou métrica para salvá-lo. Se passar, ainda faltam prioridade específica,
comparadores top-2 fortes, amostra maior e benefício fora destas duas famílias.
Contribuição central só pode ser considerada depois dessas etapas.

Antes de qualquer medição: congelar este contrato e o produtor por commit.
Verificação de correção prévia: comparação racional do certificado com leis
conjuntas finitas e construção extremal; teorema do teto; validação do prefixo
contra enumeração direta. Testes não contam como prioridade ou ganho neural.
