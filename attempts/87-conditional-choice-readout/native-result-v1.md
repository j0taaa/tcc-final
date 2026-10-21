# A87 — Qualificação nativa V1

Data: 2026-10-21. Produtor e protocolo congelados em `b01da8f2`;
nenhum caso, partição ou critério foi alterado após a coleta.

A condição necessária de desenvolvimento passou em **2/8 casos**, mas não
demonstra ganho do método de auditoria. Os dois casos que passaram tinham
proposta inicial errada; nos seis restantes, o controle já usou duas consultas.
O benefício específico da auditoria aleatória continua sem demonstração.
Há uma razão direta: nas seis propostas corretas, `lazy=2` significa que a
consulta dos dois endpoints iniciais já certificou a resposta. O wrapper da
nota matemática termina antes de acionar a auditoria em todos esses casos.
Nas duas propostas falsas, o limite positivo de custo da nota não se aplica.
Assim, o PASS necessário não justifica implementar a auditoria nesta V1 nem
ampliar seus casos/partição para obter um resultado favorável.

| Caso | OPT global | Obrigatórios | Lazy | Proposta = vencedor J | Condição necessária |
| --- | ---: | ---: | ---: | --- | --- |
| 0 | 1 | 0 | 2 | sim | não |
| 1 | 2 | 2 | 4 | não | sim |
| 2 | 1 | 1 | 3 | não | sim |
| 3 | 1 | 1 | 2 | sim | não |
| 4 | 1 | 1 | 2 | sim | não |
| 5 | 1 | 1 | 2 | sim | não |
| 6 | 1 | 1 | 2 | sim | não |
| 7 | 1 | 1 | 2 | sim | não |

OPT é offline e conhece as respostas. O controle recebe apenas caps e respostas
que consultou. Ambos usam o contrato fechado e desempate pela ordem original
das categorias. Os oito certificados finais foram validados; todas as cabeças
capturadas eram interiores, sem caps/componentes zero. A soma de OPT é nove;
o lazy usou 19 consultas condicionais; o scorer integral usa 936. Esta última
diferença pertence ao controle e não pode ser atribuída ao novo algoritmo.

O scorer J acertou 6/8 rótulos e o produto raiz 5/8. São oito exemplos de treino
escolhidos por hash, sem estimativa de superioridade semântica/generalização.
A comparação não inclui dJev, batching competitivo ou decoder completo.

## Recursos e evidências

Foram 944 forwards B1 válidos, incluindo oito raízes, sem interrupções ou
recusas. RTX 3080 Ti 12 GB, LLaDA-8B-Instruct NF4/double/BF16. Pico alocado
CUDA: 5,4771 GiB. Tempo total da captura: 297,5606 s, incluindo hashes e carga;
carga: 74,6683 s. Soma dos tempos de consulta: 180,3516 s; eventos CUDA:
155,2106 s; racionalização: 7,0773 s. Os intervalos sobrepõem-se: não somá-los.
O replay completo, incluindo serialização, levou 1,25 s, com RSS máximo
45.788 KiB. Frações das massas somadas chegaram a 24.750 bits.

Não são tempos de um decoder online nem demonstração de speedup. Os dados
incluem identidades e custo por consulta, contagens de zeros, todos os valores
racionais necessários a J/certificados e hashes das seis shards do modelo.
O hook selecionado e agrupamentos diferentes ainda exigem qualificação de
fidelidade antes de reivindicar equivalência operacional.

Captura integral compactada sem perda, 635.495 bytes:
[a87_native_v1.jsonl.gz](../../docs/artifacts/raw/a87_native_v1.jsonl.gz).
SHA256 dos 1.906.297 bytes descompactados:
`c828867d81991ee26f8887858839471e2c3fdbdac6a677993d47cdd024675f04`.
Os hashes das fontes, dataset, tokenizer e pesos estão no produtor/manifesto.
O arquivo compactado descomprime exatamente para a captura original.

Para reconstruir o diagnóstico, a partir das fontes congeladas:

```bash
gzip -dc docs/artifacts/raw/a87_native_v1.jsonl.gz > artifacts/a87-native-replay-input.jsonl
.venv-live/bin/python attempts/87-conditional-choice-readout/native_replay_v1.py \
  artifacts/a87-native-replay-input.jsonl --output artifacts/a87-native-replay-reproduced.json
```

O comando exige fontes/manifesto iguais a HEAD e saída nova. Não se executou
novamente o modelo para escolher dados favoráveis. O sucesso da condição
necessária não seleciona campanha, tema central ou melhoria nativa do método.
