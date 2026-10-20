# A83 — Diagnóstico de uma implementação existente

20/10/2026. Execução solicitada depois da revisão do processo de pesquisa.
O objetivo é localizar um problema real antes de propor outro método. Isto
não reabre aplicações anteriores nem seleciona uma contribuição de TCC.

## Operação e fontes

Gerar JSON sob três schemas com o loop LLaDA original do EPIC, sem editar
`vendor/`. Fonte oficial conferida em 20/10: o HEAD upstream continua
`5b1b31098f34ed3691d2a9f4aae14fdf5839d072`, igual ao snapshot preservado.

- [EPIC, versão 2](https://arxiv.org/html/2606.00722v2), seções 4 e C.
- [Código oficial](https://github.com/hyundong98/EPIC-Decoding).
- [LAVE, versão 3](https://arxiv.org/abs/2602.00612v3): antecedente necessário
  para qualquer proposta de lookahead seguido de verificação.

Fluxo observado no código: forward neural → propostas/confianças → filtro
regular de um lote → verificação CFG exata → commitments → rejeição sequencial
para o orçamento restante. O loop também recalcula softmax denso dentro da
rejeição. Nenhuma dessas observações de código estabelece um gargalo medido.

## Protocolo prospectivo de diagnóstico V2

V1 foi interrompida durante a carga, antes de qualquer decode, após a auditoria
independente detectar que o reset Python não limpava o cache Rust. O registro
de carga interrompida fica em `load-interrupted-v1.jsonl`; a fonte V1 está no
commit `8cfc6c71`. V2 acrescenta o reset Rust por execução, registro de exceções
antes do fallback que as captura no upstream, ordenação explícita do atalho e
rótulo correto do RSS cumulativo. Não houve saídas de casos para escolher a
correção. A auditoria também confirmou a equivalência sob as hipóteses abaixo.

Congelar este arquivo e `diagnose.py` em commit antes da primeira execução.
Não escolher casos depois de ver saídas. Casos próprios, pequenos, não um
benchmark representativo: soma em objeto, lista de três inteiros e classificação
de sentimento com enum. Textos e schemas exatos ficam em `CASES` no produtor.

- LLaDA-8B-Instruct, snapshot `08b83a6feb34df1a6011b80c3c00c7563e963b07`,
  NF4, double quantization, compute BF16, somente arquivos locais.
- RTX 3080 Ti 12 GB; quatro threads Torch e quatro Rayon, sem alegar limite
  global de quatro threads. Não encerrar outros consumidores GPU.
  Recusar carga se houver menos de 6,5 GiB livres.
- Seed 83001 por execução; temperatura zero; 64 posições, blocos de 32,
  oito passos totais; máximo de 100 rejeições, sem modificar o upstream.
- Três modos por caso, ordem rotacionada explicitada no produtor: `epic`,
  `exact_first`, `sequential`. Uma execução de cada; sem significância estatística.
- `epic`: subset selector original com componentes aceleradores ligados.
- `exact_first`: testar o lote inteiro com o mesmo oráculo CFG primeiro;
  se recusado, chamar o selector original, reutilizando esse resultado apenas
  dentro dessa chamada. Controle clássico de ordenação de testes, sem novidade.
- `sequential`: desabilitar somente a tentativa de lote. Não é um baseline
  substituto do EPIC; serve para atribuir custo e mudanças de trajetória.
- Caches lexicais e de cover frios por execução. Medir preparação por schema,
  carga/tokenizer uma vez, decode, forward, seleção, checks exatos/regulares,
  softmax do decoder, contagens, exceções, conclusão, JSON/schema e resposta esperada.
  Tempos internos aninhados não devem ser somados. Medir pico GPU alocado e
  pico RSS cumulativo do processo, sem atribuí-lo isoladamente a um modo.
- Sincronização CUDA nos wrappers de tempo; medições são instrumentadas e
  não alegam throughput de produção. Copiar IDs a cada yield também custa
  tempo, especialmente no modo sequencial. Outros processos GPU são confundidores.
- Limite cooperativo de 120 s por decode, verificado também nos wrappers;
  timeout de oráculo nativo continua o original. Erro, interrupção, OOM e saída
  incompleta ficam registrados e não equivalem a inviabilidade da gramática.
- Preservar todas as nove execuções; sem repetição seletiva. Não chamar o
  autocomplete de recuperação para esconder interrupções do loop observado.

## Hipótese do controle e limites

Se o lote inteiro passa na CFG, passa no cover porque `L(G) ⊆ L(cover)`.
Com oráculos corretos e sem falhas de recursos, o selector original retorna
esse lote inteiro. Portanto o atalho `exact_first` toma a mesma decisão nesse
caso; se o teste falha, devolve a decisão ao selector original. O cache usa o
canvas completo da consulta e é descartado ao terminar cada seleção. Não há
aproximação de probabilidades ou alteração de IDs/EOS/PAD.

Isto é uma prova escrita de equivalência do atalho sob essas hipóteses, não
uma contribuição nova. Falhas dos oráculos, suas exceções e arredondamentos
neurais podem limitar a equivalência da execução física; comparar todos os
IDs finais e estados emitidos, além dos textos.

Benefício verificável: se o cover for custo relevante em lotes já válidos,
esse custo pode ser evitado. Objeções: o oráculo exato pode ser mais caro nos
lotes inválidos; JSON pequeno pode ter pouca relevância; a inferência neural
pode dominar; quantização e instrumentação impedem extrapolar os números do
artigo. Só depois dos dados será formulada uma direção, se houver evidência.

Reprodução local (ambiente live existente, sem download):

```bash
.venv-live/bin/python attempts/83-epic-operational-diagnosis/diagnose.py --output /tmp/a83-v2.jsonl
```

Prova escrita, inspeção de fonte, execução neural e validação de JSON são
evidências distintas. Nenhuma prova aqui estabelece novidade mundial ou melhora
de qualidade neural.

## Diagnóstico causal V3, depois dos dados V2

V2 terminou as nove execuções. A soma atingiu 100 rejeições nos três modos,
com um MASK anterior ao EOS. JSON após remover tokens especiais passou, mas
o loop não terminou; os outros dois casos terminaram. Testes CPU no canvas
final confirmaram que preencher o buraco com espaço ou newline é permitido
pelo mesmo checker. O próximo diagnóstico não muda casos nem tenta melhorar
o resultado: `--trace` executa os mesmos três casos, somente EPIC original,
registrando cada consulta sequencial (posição, ID original, palavra, aceite,
forward e canvas lexical) e as entradas dos forwards. Congelar essa fonte em
novo commit antes da execução. São dados de investigação da causa em casos
já vistos; não um teste independente ou evidência de generalização.

```bash
.venv-live/bin/python attempts/83-epic-operational-diagnosis/diagnose.py --trace --output /tmp/a83-v3.jsonl
```

## Controle de trabalho vazio V4, prospectivo após V3

V3 confirmou a falha da soma: as últimas propostas rejeitadas na posição 12
incluíam nomes de campos, números e palavras; não houve tentativa de whitespace
nessa posição. Nos outros dois casos, entradas dos oito forwards tinham
respectivamente `[64,56,16,7,0,0,0,0]` e `[64,56,48,7,0,0,0,0]` máscaras.
A segunda metade do decode avaliava a rede com o canvas inteiro preenchido.

V4 (`--empty-control`) compara, nos mesmos três casos, o original com um
controle que devolve os logits anteriores quando não há MASK algum. Nessas
iterações, os orçamentos de reveal são todos zero: os logits não são usados
para nenhuma atualização. Sob modelo sem efeitos colaterais observáveis,
omitir esses forwards preserva todos os estados e IDs. Não há teorema novo:
é eliminação de trabalho sem consumidor, disponível como controle competente.
Não remover EOS, PAD ou MASK para simular conclusão.

Uma execução por modo/caso, ordem alternada (epic/controle, controle/epic,
epic/controle); sem ampliar casos, seeds ou alegar significância. Carga e
preparação continuam contadas separadamente; comparar primeiro a redução
determinística de NFEs, depois os tempos instrumentados. Se o loop original
terminar com MASK, realizar **uma** predição separada no canvas interrompido
e consultar o checker para suas dez primeiras propostas por buraco. Registrar
o custo dessa sonda; ela não altera a saída nem é incluída como ganho do
controle. Não é um método de recuperação avaliado. O wrapper público do EPIC
já possui autocomplete em caso de interrupção; esta investigação isola o loop
neural, sem alegar quebra da garantia do wrapper ou superioridade sobre ele.

```bash
.venv-live/bin/python attempts/83-epic-operational-diagnosis/diagnose.py --empty-control --output /tmp/a83-v4.jsonl
```

## Evidência V2/V3 e mudança do processo

[V2: nove execuções completas do protocolo](diagnostic-v2.jsonl), produtor
`de362100`; [V3: três rastreamentos](causal-v3.jsonl), produtor `0d654eeb`.
São casos de diagnóstico desenvolvidos aqui, sem representatividade estatística.

| Caso | Modo | NFEs | Softmax | Rejeições | Loop concluído | Decode (s) |
| --- | --- | ---: | ---: | ---: | --- | ---: |
| soma | EPIC | 4 | 126 | 100 | não | 1,477 |
| soma | exato primeiro | 4 | 126 | 100 | não | 0,873 |
| soma | sequencial | 4 | 128 | 100 | não | 0,875 |
| lista | EPIC | 8 | 20 | 4 | sim | 0,760 |
| lista | exato primeiro | 8 | 20 | 4 | sim | 0,756 |
| lista | sequencial | 8 | 35 | 4 | sim | 0,814 |
| enum | EPIC | 8 | 41 | 22 | sim | 0,843 |
| enum | exato primeiro | 8 | 41 | 22 | sim | 0,839 |
| enum | sequencial | 8 | 53 | 22 | sim | 0,890 |

Não interpretar a diferença de tempo da soma como ganho do atalho: o primeiro
EPIC teve tempo neural de 0,690 s vs 0,345 s nos outros dois modos. Ordem,
aquecimento e outro processo GPU impedem atribuir essa diferença ao atalho.
Nos três casos, `exact_first` preservou todos os IDs finais **e** hashes de
todos os estados emitidos. O custo somado das verificações regulares e exatas
ficou entre 0,7% e 2,3% do decode instrumentado; acelerar só o parser não ataca
o custo dominante **nestes casos**, sem extrapolar para C++ ou outros modelos.
Na soma, softmax consumiu 0,416–0,442 s; a conversão prévia para float64 nem
está incluída nesse subtotal. Carga V2: 81,876 s. Preparação por schema abaixo
de 0,01 s; pico GPU alocado do processo do experimento: 5,73–5,93 GiB,
além do outro processo GPU registrado. RSS é cumulativo, não independente.

Todas as nove strings renderizadas passaram no JSON/schema e na resposta
esperada. Isso **não** torna os nove loops concluídos: remover tokens especiais
escondeu o MASK na posição 12 das três somas. A fonte pública ainda tem
autocomplete para essa situação; não foi executado nem cobrado neste diagnóstico
do loop. Não declarar vantagem integral sobre o wrapper público.

V3 identificou nomes como `result`, `total`, `sum` e `number` sendo rejeitados
na posição 12 no quarto forward, embora no canvas final esse buraco fique entre
whitespace, fora de strings. Testes CPU do mesmo checker aceitaram espaço,
newline, tab e vazio nesse buraco. O trace mostra uso de uma cabeça calculada
antes das últimas alterações, mas não estabelece sozinho que uma nova cabeça
resolva o caso; essa é a pergunta da sonda V4.

As causas substituem a premissa anterior de construir primeiro uma prova:
o consumidor real aqui é o loop de geração, seus controles incluem atalhos
clássicos e o custo relevante inclui trabalho neural inútil e propostas antigas.
O atalho de ordenação não virou contribuição. Nem a correção de trabalho vazio
deverá ser apresentada como método inédito de TCC.

## Resultado do controle V4

[Seis execuções e a sonda](empty-control-v4.jsonl), produtor `03068bf1`.
Todos os três pares preservaram os IDs finais e os hashes de **todos** os
estados emitidos. Nenhuma exceção foi registrada. Soma continua com um MASK
e 100 rejeições em ambos; não foi reclassificada como concluída.

| Caso | NFEs original → controle | Decode original → controle (s) | Estado |
| --- | --- | --- | --- |
| soma | 4 → 4 | 1,804 → 0,893 | inconcluso nos dois |
| lista | 8 → 4 | 0,746 → 0,423 | concluído, mesmos IDs/estados |
| enum | 8 → 4 | 0,833 → 0,509 | concluído, mesmos IDs/estados |

A queda da soma não é ganho do controle: contagens e estados são iguais e o
primeiro original teve tempo neural maior (0,758 s vs 0,346 s), além de maior
tempo de softmax. O desenho não isola aquecimento e contenção. Nos dois
casos completos, a redução medida de NFEs é 50%; a de decode instrumentado,
43%/39%. São observações individuais de casos já vistos, com outro processo
GPU, sem teste de generalização nem throughput de produção. A carga V4 custou
72,035 s e não foi omitida do registro; os percentuais são de requisições com
modelo residente, não do tempo incluindo carga. Não houve recuperação externa.

Prova de preservação restrita: nos forwards vazios observados, o próximo bloco
começa sem MASK e `get_num_transfer_tokens` cria um orçamento zero em cada
passo. A tentativa de lote é desativada pelo tamanho zero e o laço sequencial
executa zero iterações. Nenhum valor produzido pela rede afeta `x`,
`generated_words` ou os estados emitidos. Suprimir avaliações sem efeitos
colaterais observáveis preserva esses valores por indução nos quatro passos.
Isto não autoriza aplicar o guarda a qualquer scheduler/modelo com estado.

Na sonda da soma, uma predição sobre o canvas interrompido colocou newline
(ID original 198) em **primeiro** lugar; o mesmo checker o aceitou. Tab também
passou em décimo lugar. O forward custou 0,0856 s; top-k, detokenização e as
dez consultas não tiveram custo total isoladamente medido. A sonda não aplicou
o token nem retomou a trajetória: demonstra disponibilidade de uma proposta
compatível nesse estado, sem provar recuperação geral ou vantagem integral.

## Decisão e questão que os dados permitem

Há um diagnóstico positivo de engenharia: chamadas sem trabalho podem ser
removidas preservando a operação; no caso preso, atualizações do canvas mudam
a primeira proposta disponível. Não há contribuição científica nova confirmada.
A auditoria independente distinguiu esses fatos de um suposto defeito da rede
ou quebra da garantia do wrapper.

**Questão concreta para pesquisa:** quando vale atualizar a predição neural
durante a rejeição, em vez de continuar consultando propostas calculadas antes
dos commitments? Diferentemente das antigas construções abstratas, há aqui
um consumidor e um estado neural que expõem o problema. Ainda faltam controles
de reaproveitamento de softmax/normalizadores, atualização após um número fixo
de rejeições, a recuperação completa do EPIC e a recuperação do LAVE. O LAVE
já modifica o contexto em seu mecanismo de recuperação (seção 3.3); executar
outro forward não pode ser anunciado como novidade por si só.

Não abrir uma campanha de um novo decoder com base nestes três casos. Antes
de promovê-la, essa pergunta precisa sobreviver aos controles simples e ao
antecedente mais próximo, ganhar uma operação/prova próprias e ser avaliada
em dados independentes com custo completo. A prova de ausência de trabalho
não é uma prova de melhoria de qualidade nem de novidade.

## Seleção científica após o requisito de impacto

20/10/2026. O usuário condicionou a continuação a uma contribuição de impacto
que fortaleça uma candidatura ao mestrado. **A83 não é selecionada como tema
central nem como campanha de um novo decoder.** O diagnóstico e os controles
corretos ficam preservados. Esta decisão não afirma que nenhuma extensão
possível possa dar resultado; afirma que a evidência atual não justifica esse
investimento para o objetivo solicitado.

A leitura adicional e uma avaliação independente por subagente confrontaram
a questão com fontes primárias:

- [LAVE v3, seção 3.3](https://arxiv.org/html/2602.00612v3#S3.SS3): já monitora
  rejeições consecutivas e recupera a geração usando prefixos verificados e
  mudanças de contexto. Reagir a uma contagem de rejeições é antecedente, não
  uma diferença científica suficiente.
- [Saber, seções 4.2/4.3 e apêndice A](https://aclanthology.org/2026.acl-long.165.pdf):
  adapta o preenchimento e reavalia escolhas conforme o contexto muda, com
  remasking e análise sob hipóteses explícitas de calibração e confiabilidade.
  Não resolve o mesmo controlador de rejeição CFG, mas cobre a motivação geral
  de previsões que deixam de ser adequadas ao novo contexto.
- [DecoCal, seções 3.2–3.5](https://aclanthology.org/2026.acl-long.545.pdf):
  acumula previsões entre passos, decide preenchimento/revisão e usa mecanismos
  de progresso. Não é prova de que toda atualização CFG já foi estudada.

A diferença ainda concebível é usar rejeições CFG e custos medidos para decidir
quando reavaliar a rede mantendo os commitments existentes. Isso é uma hipótese
de controle computacional, sem algoritmo próprio, prioridade verificada,
teorema de benefício ou superioridade frente a regras fixas e recuperações
completas. A garantia sintática viria do verificador já existente. Nenhum dos
18 decodes estabelece uma vantagem dessa política, pois ela não foi implementada.

O próximo investimento nessa pergunta só se justifica se aparecer um mecanismo
distinto acompanhado de uma propriedade útil demonstrável e de um comparador
competente. Não há campanha adicional selecionada apenas para otimizar o caso
da soma. O requisito de impacto permanece nas instruções do projeto; nenhuma
decisão aqui promete aprovação acadêmica ou declara revisão humana.
