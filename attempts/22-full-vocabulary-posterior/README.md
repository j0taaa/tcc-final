# Tentativa 22 — Posterior JSON exato no vocabulário inteiro

Hipótese em investigação, não conquista confirmada. Retoma o núcleo probabilístico
mantido com um requisito novo: não truncar tokens por topK. Inferência/lexer e
quocientes são antecedentes conhecidos. Não é vitória de geração sobre EPIC.
Fontes independentes de21; nenhuma dependência mutável de outra tentativa.

1. **Uso real:** calcular massa de validade, marginais de TODOS os tokens e
   amostrar a previsão congelada de uma dLLM condicionada a JSON recursivo,
   em lacunas arbitrárias. Top16 pode ter massa válida zero e excluir boas
   conclusões; vocabulário completo elimina essa cauda, sem inventar gabarito.
   Saída são probabilidades e tokens originais, consumidos pelo decoder.
2. **Relevância:** inferência gramatical e quociente global são conhecidos
   (Rivaud–Pachet; FactorDLM Prop2). Candidata é compilação automática para
   fronteiras BPE arbitrárias e classes locais sobrepostas, que torna prática
   inferência recursiva exata em TODA a saída do modelo e devolve marginais/lei
   sobre originais. Pode ser engenharia especializada, não descoberta teórica.
   Seu impacto precisa ser capacidade ou custo demonstrados contra baseline
   competente, sem apresentar simples correção como novidade.
3. **Por que escolher:** exatidão no vocabulário inteiro, não exact_on_topK;
   dimensões do parsing dependem do efeito lexical em vez de50000 folhas de
   tokens. Comparar lexer com originais, classes globais (competente) e locais;
   todos usam o mesmo parser, gramática e tabela lexical. O controle global por
   posição usa APENAS estados alcançáveis por prefixos lexicais, sem gabarito.
   Rejeição exata é
   controle de amostragem, não calcula massa/marginais exatas finitamente.
4. **Matemática:** cada original determina caminho lexical e grupos únicos;
   fechar grupo tem peso soma dos originais. Inside calcula massa; derivadas
   outside e refinamento global recuperam todos os marginais originais.
   Amostrar grupos e então original com peso proporcional cancela as somas,
   obtendo exatamente o produto condicionado. Ganho de estrutura e custo
   completos escritos em specification.md, independentemente do código.
5. **Protocolo:** antes de forwards/tempos novos, mesmas seis entradas de
   desenvolvimento e seis nunca-model-testadas para confirmação, máscaras4/8/16.
   Não selecionar raras massas depois dos resultados. Todas as recusas/perdas,
   inclusive rejeição mais barata, entram. Três repetições; nove na confirmação.
   Benefício precisa sobreviver à preparação por pedido e custo do modelo;
   tabela/modelo comuns em serviço preparado têm custo de startup declarado.
6. **Custo completo:** tabela lexical completa é compartilhada pelos controles,
   não gratuita exclusiva; registrar cold e prepared. Converter todos os
   floats a inteiros racionais normalizados, agregar, compilar, inside/outside,
   expandir marginais50k, amostrar, validar, memória e bit arithmetic. Não
   confundir amostra de um passo com lei de toda trajetória ou qualidade.
7. **Objeção:** classes globais podem obter o mesmo benefício ou ganhar; isso
   deve orientar a implementação escolhida. Rejeição ganha quando massa válida
   é alta; inferência de CFG genérica pode compartilhar essa vantagem.
   O serviço pré-compilado amortiza a tabela. Sintaxe JSON não prova semântica;
   suporte completo não promete maior acurácia da dLLM.
8. **Artigo:** prioridade mundial, teoria nova e revisão humana não confirmadas.
   Precisamos massa/marginais/lei corretas, cálculo completo executado em logits
   reais, comparação justa e ganho de capacidade ou custo em entrada externa.
   Se nem esta operação for viável/útil, preservar e continuar investigação.

A contagem estrutural preliminar (sem medir vantagem) encontrou197 classes
lexicais globais para50257 tokens GPT2; grupos locais por estado variam1..70.
Esses números justificam protótipo mínimo, não vitória física ou novidade.
Fonte/tokenizer pinados e contagens em work/evidence/representation-counts.json.

Antecedentes:
[FactorDLM Prop2](https://arxiv.org/html/2609.32900v1),
[SynCode](https://arxiv.org/html/2403.01632v3),
[DOMINO](https://arxiv.org/abs/2403.06988),
[Opedal et al.2023](https://aclanthology.org/2023.acl-long.204.pdf).


Refinamento v2 antes da confirmação fresca:116/216 registros da rodada v1
preservados em work/evidence/development-v1-partial. Sem conclusão confirmada:
faltava controle de quociente por posição e os limites de contagem podiam
causar recusa antes de esgotar tempo/memória. Interrompemos a rodada inteira,
sem excluir caso desfavorável. Mesmos floats de modelo capturados em f900bd7.
A nova rodada compara CINCO métodos, com guardas10x maiores,120s/8GiB iguais.
Métricas/limiar20% não mudam. A classificação por posição é antecedente
conhecido; pode eliminar o benefício. Repetir TODOS os casos de desenvolvimento.


Refinamento v3 operacional, antes da confirmação fresca:11/270 registros v2
preservados integralmente.8GiB virtual por processo excedia a memória disponível
neste host15GiB com aplicativos ativos; exceção por prazo liberava um heap
muito grande lentamente. Todos os métodos passam a3GiB igualmente; supervisor
mata após150s incluindo startup/auditoria/cleanup, além do prazo interno120s.
Não atribuir uma recusa a inviabilidade ou chamar a rodada parcial de sucesso.
Mudança necessária ao hardware disponível, não seleção de casos favoráveis.


Desenvolvimento v3 executado:270/270 registros,208 completos e62 recusas.
Sem divergência nos resultados concluídos. Critério forte passou em6/18
configurações (5 ganhos de tempo/CPU,1 de capacidade), inclusive controle por
posição; não é confirmação fresca ainda. Rejeição NÃO perdeu no critério de
amostragem em nenhum caso. Dados/tempos/recusas em evidence/development-v3.

Auditoria adicional (critérios4/5/8, operação inalterada):24 quadros com uma
lacuna, demais originais fixados EXPLICITAMENTE ao documento externo para
permitir enumeração. Todas as50258 opções foram reconhecidas por UTF8/Python
JSON independentes;96 comparações nas4 representações concordam exatamente.
Não houve forward novo; são verificações de correção, não benchmark/qualidade.
Comando: módulo work.audit_full_rows, --capture .cache/a22-development-cuda-v1.

Custos: prepared_total inclui conversão racional, preparação POR PEDIDO,
inside/outside, originais, amostra/validação e o forward comum realmente medido.
A tabela lexical/gramática/modelo/tokenizer são serviço já carregado, com seus
startups registrados separadamente. cold_total nos dados acrescenta APENAS
startup da tabela/gramática, não todo carregamento de modelo/tokenizer nem
construção do mapa de bytes. Não usar esse campo para alegar latência de um
processo inteiramente frio. Empacotamento/auditoria de matrizes não é timing.
Novidade teórica e superioridade de geração/EPIC/qualidade não foram confirmadas.


Reprodução opcional pequena (critérios6/8, mesmas garantias): capture aceita
--archive-logits-first para um único caso de4 lacunas. Logits originais de toda
a cabeça são gravados APÓS o relógio, antes da política de MASK. São valores
F32 elevados exatamente a F64; a rede/softmax e os kernels de inferência não
mudam. verify_capture confere hashes, softmax completa byte a byte e massa/
matriz recomputadas. Não afirma reproduzir o forward sem os pesos opcionais.
A confirmação será executada sem escolher caso pelo resultado, seguindo o
protocolo completo (12 documentos de refinamento e6 novos, todos os tamanhos).


Refinamento v5 (perguntas3/4/5/6/7/8, mesma operação): um controle competente
também deve eliminar estados lexicais incompatíveis com o sufixo fixado.
Implementamos forward/backward estrutural, sem pesos, gramática ou gabarito,
para TODAS as quatro representações. O quociente por posição usa efeitos
efetivamente admissíveis em todos os estados coacessíveis. Trimming de FSTs
é antecedente conhecido; não é anunciado como nova contribuição.
As provas de massa/marginais/lei/reuso permanecem, pois nenhum caminho aceito
pode visitar um estado sem sufixo lexical completo. Os oráculos anteriores passaram
para OITO variantes; as contagens de todos72 quadros conservam58 desigualdades
estritas de arestas, sem afirmar velocidade. Custo adicional O(n soma_s |grupos_s|).

As270 linhas de desenvolvimento e540 de refinamento anteriores estão preservadas.
A rodada fresca foi interrompida inteira com50/810 registros para acrescentar
esse controle; não é confirmação. Seus seis documentos já receberam forwards,
portanto não serão apresentados como nunca vistos outra vez. O protocolo v5
compara as seis representações de partições estáticas, as duas candidatas locais,
inferência determinística de pilhas e rejeição. Seleciona uma candidata somente no desenvolvimento, por quantidade
de ganhos fortes; empate prefere bidir_local. Nenhum ganho rejeita ambas.
Antes de novos forwards, congela essa escolha. A confirmação independente usa
TODOS os cinco documentos elegíveis do JSONTestSuite pinado (positivos, objeto/
array, UTF8/JSON estritos,16..96 tokens), sem criar um sexto artificial.
Mesmo limiar20%, limites3GiB/120s e todos os resultados/recusas. Novidade e
suficiência acadêmica permanecem separadas de capacidade/custo observados.


Controle adicional v5, antes de qualquer medição (perguntas1–8): a operação
continua massa, todas as marginais originais e uma amostra do produto de um
passo condicionado a JSON. Além das seis partições, `stack_control.py` aplica
o parser preditivo LL(1) clássico diretamente às saídas lexicais. Recebe o
mesmo trimming, somas locais e probabilidades; memoiza transições por camada,
elimina estados gramaticais sem caminho até a aceitação,
soma arcos com o mesmo estado de destino e usa condições necessárias de
sufixo (terminais e fechamentos restantes). Não limita arbitrariamente a
profundidade. Sua passagem de ida/volta e reconstrução de tokens são exatas.
É uma alternativa competente diferente do parser de floresta; se vencer,
não será omitida nem reinterpretada como outro problema. O critério passa a
exigir ganho contra TODOS os sete controles, antes da confirmação independente.

Também fornecemos a TODOS os métodos a equivalência sintática clássica entre
NUMBER, TRUE, FALSE e NULL: são valores atômicos com as mesmas continuações
na gramática JSON. STRING permanece separada, pois pode ser chave de objeto.
Os tokens, bytes e valores originais não são fundidos no resultado; o lexer
ainda valida cada literal. As contagens197/454 e58/72 anteriores são históricas,
anteriores a esse refinamento. Nada disso é reivindicado como princípio novo.
A objeção central é justamente que a inferência clássica de pilhas ou uma
eliminação equivalente obtenha o mesmo benefício; a implementação mínima
agora permite testá-la antes de novas capturas. A vantagem de tamanho do
DAG não implica superar esse algoritmo diferente. Necessitamos vantagem
observada com custo completo e confirmação independente; ainda não houve.

O novo oráculo completo concorda em216 comparações,24 quadros ×9 métodos,
sobre1.206.192 candidatos originais reconhecidos independentemente. As cinco
verificações pequenas também passam. Isso sustenta correção, não custo ou novidade.
