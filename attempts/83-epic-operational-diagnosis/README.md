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
