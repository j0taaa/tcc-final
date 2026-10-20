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

## Protocolo prospectivo de diagnóstico V1

Congelar este arquivo e `diagnose.py` em commit antes da primeira execução.
Não escolher casos depois de ver saídas. Casos próprios, pequenos, não um
benchmark representativo: soma em objeto, lista de três inteiros e classificação
de sentimento com enum. Textos e schemas exatos ficam em `CASES` no produtor.

- LLaDA-8B-Instruct, snapshot `08b83a6feb34df1a6011b80c3c00c7563e963b07`,
  NF4, double quantization, compute BF16, somente arquivos locais.
- RTX 3080 Ti 12 GB; quatro threads CPU. Não encerrar outros consumidores GPU.
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
  softmax do decoder, contagens, conclusão, JSON/schema e resposta esperada.
  Tempos internos aninhados não devem ser somados. Medir pico GPU alocado e RSS.
- Sincronização CUDA nos wrappers de tempo; medições são instrumentadas e
  não alegam throughput de produção. Outros processos GPU são confundidores.
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
.venv-live/bin/python attempts/83-epic-operational-diagnosis/diagnose.py --output /tmp/a83-v1.jsonl
```

Prova escrita, inspeção de fonte, execução neural e validação de JSON são
evidências distintas. Nenhuma prova aqui estabelece novidade mundial ou melhora
de qualidade neural.
