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
