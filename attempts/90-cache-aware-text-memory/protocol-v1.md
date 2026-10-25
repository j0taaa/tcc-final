# Protocolo V1 — congelar antes de qualquer forward A90

23/10/2026. Piloto de descarte sem treinamento. Não seleciona contribuição central.

## Perguntas e decisão

1. A edição localizada reduz custo integral sem perder fatos/atualizações?
2. A dLLM oferece algo além do mesmo seletor/estrutura executado por AR?
3. O ganho sobrevive a histórico completo com prefix cache real?

Gate prospectivo: apenas considerar avanço se dLLM-local (a) não perder acerto
sintético nem aumentar fatos superados frente a AR-local e histórico completo,
(b) não perder utilidade externa frente a AR-local, (c) reduzir >=10% a soma de
seleção + edição + respostas frente a AR-local e ao melhor controle com qualidade
>= à candidata, e (d) respeitar orçamento e cache. Reportar todos os resultados,
não somente a configuração vencedora. N pequeno: nem passar comprova generalidade.
Nenhum pós-treino nesta rodada. Colisão substancial de novidade também impede
promoção mesmo com gate operacional positivo.

## Dados, congelamento e acesso

Quatro histórias sintéticas predefinidas, três eventos cada: preservação de fatos,
mudança de cidade/endereço, mudança de compromisso/lembrete e contato.
Todos os estados são avaliados. Perguntas e fatos esperados ficam em arquivo
separado que o atualizador não recebe. Não há tuning nessas histórias.

LongMemEval **cleaned**, snapshot fixo registrado em `data/source.json`:
menor SHA256 de `a90-v1:question_id` em cada uma das seis categorias sem `_abs`,
e mais um caso de abstenção selecionado pelo mesmo hash. Seleção por ID apenas,
sem filtrar comprimento/dificuldade/acerto. Sete histórias completas do arquivo
oracle, ordenadas por data e ID de sessão, sem `has_answer`, `answer_session_ids`,
pergunta, resposta ou data da pergunta no compressor. Todos os métodos recebem
os mesmos eventos de até 1.536 tokens Qwen, sem cortar a história. Oracle é uma
condição favorecida de recuperação, comum a todos; não é LongMemEval completo,
nem teste de recuperação query-blind do corpus de 115k. Avaliação externa: uma
pergunta final por história. Não haverá judge/API pago; registrar saídas completas
e escore lexical conservador mais revisão semântica local pelo agente (não humana independente), com rubrica congelada:
0=incorreta/ausente, 1=parcial sem contradição, 2=responde todos os requisitos.
Revisão sem identificação do método; publicar também a chave após a classificação.
Não converter a rubrica local em acurácia oficial LongMemEval.

## Métodos e interface comum

Consumidor congelado: Qwen2.5-3B-Instruct NF4 (Unsloth, revision fixa), sem offload.
Mesmo AR é o editor AR. LLaDA-8B-Instruct NF4 existente, compute BF16, sem offload.
Modelos não pareados por pré-treino/parâmetros: resultados não isolam arquitetura.
Mesma estrutura para todos os compressores: quatro blocos de até 64 tokens Qwen,
serialização fixa `B0: ...`, ...; teto total 320 tokens, incluindo separadores.
Geração sem sampling; cap de conteúdo 256 tokens para rewrite global e 64 por
bloco afetado para patch. Todos podem ler a memória inteira e o novo evento.

- `dllm_local`: seletor determinístico de sobreposição lexical sem perguntas,
  fechamento por vocabulário compartilhado entre blocos, slots novos quando evento
  não relacionado; se preciso, reescrita global. Somente blocos selecionados são
  substituídos. dLLM gera o patch conjunto em canvas mascarado; partes não
  selecionadas são copiadas exatamente pelo montador. Isso testa uma interface de
  patch externo, **não** infill nativo em posições da memória inteira.
- `ar_local`: exatamente o mesmo seletor, formato, cap e montador, AR gera patch.
- `dllm_global`: reescreve toda a memória incrementalmente, mesmo formato/teto.
- `ar_global`: resumidor AR incremental, mesma informação/formato/teto.
- `extractive`: seleção incremental de sentenças por recência, densidade de entidades
  e diversidade, independente de perguntas, sob o mesmo teto.
- `raw_tail`: últimos tokens disponíveis de memória+evento, controle sem modelo.
- `full_history`: histórico completo append-only, sem compactação; exceção explícita
  ao teto para estabelecer custo e teto de informação com cache competente.

O seletor local abre blocos com >=2 palavras de conteúdo compartilhadas com o
novo evento; inclui dependentes que compartilham >=3 palavras de conteúdo com
blocos abertos, até ponto fixo. Se nenhum: usa primeiro vazio ou último bloco.
Inicialização e evento grande (>768 tokens) abrem todos. Se >=3 blocos abertos,
reescrita global. Regra fixa, heurística, sem alegação de novidade ou ótimo de custo.
Atualizações dependentes podem exigir reabrir prefixo; esse custo é contabilizado.

## Execução e custos

Lock `/tmp/tcc-final-gpu-pilot.lock` com `flock`, do carregamento à liberação da
VRAM. Checar processos computacionais antes de qualquer chamada CUDA e dentro
do lock; recusar se houver PID alheio. Sem interromper outros trabalhos. Espera
limitada de aquisição; retomar CPU se indisponível. Medir sincronizando CUDA.

Executar editores em fases separadas e consumidor em fase comum para limitar RAM
e VRAM. Salvar memórias por atualização. Custo integral residente é soma de tempos
reais de edição/seleção/montagem e consumidor: **replay de pipeline**, não latência
intercalada observada com ambos modelos residentes. Registrar separadamente loads,
warmups, tempo frio, import/preparo, wall time, NFEs/tokens, picos CPU/GPU e disco.
A implementação não usa offload desigual. Soma fria inclui load/preparo por fase;
nenhuma projeção de throughput ou latência de produção. Isso limita resultado positivo.

Consumidor: um KV real por método/história, a partir de prompts serializados pelo
chat template real. Tokenizar o prompt novo inteiro; reusar só LCP de IDs até o
comprimento realmente em cache, crop antes da primeira diferença. Descartar TODO
sufixo após divergência; não reusar KV de regiões estáveis após edição causal.
Medir reutilizados, tokens de prefill novos, forwards, tokens de decode, bytes KV.
Baseline full_history usa a mesma implementação e retém todos os prefixos válidos.
Sem resposta passada ao compressor, sem histórico de perguntas na memória.

Em cada atualização externa, interação padronizada `Acknowledge receipt.` com cap
4 tokens, e só na última a pergunta externa com cap 96. Sintéticos: uma resposta
combinada de cap 96 em cada estado para todos os fatos, mesma pergunta por história.
Custos externos incluem acknowledgments. Uma repetição sem treino por célula;
ordem pseudoaleatória fixa das células/fases, sem IC de latência neste piloto.

Auditar cache com execução fresca/cached para fixture com mudança no começo/meio/
fim e append, tokenizer boundary adversarial e prompts reais; comparar logits
(tolerância BF16 explícita) e saídas gulosas. Correção lógica de reutilização não é
promessa de bit-identidade de kernels. Falha de validade bloqueia conclusões de
custo até correção documentada; não omitir execução malsucedida.
