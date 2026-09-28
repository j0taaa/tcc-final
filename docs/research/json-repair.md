# Reparo certificado de JSON

A implementação está em `src/mwpc_exact/repair.py`. Ela reutiliza os solvers
independentes existentes e não carrega modelo nem baixa tokenizer.

```bash
make bootstrap-rust-parser
.venv/bin/python -m mwpc_exact.repair --profile records \
  '{"id":7,"payload":[["a":1,"b":2}]}'
```

A saída inclui `output_text`, custo de substituição, posições alteradas, suporte
completo e certificado. Neste exemplo, a troca do segundo `[` por `{` recupera:

```json
{"id":7,"payload":[{"a":1,"b":2}]}
```

`--profile records` é o esquema compacto com `id` inteiro e lista de registros
inteiros `a`/`b`, nessa ordem. O perfil padrão aceita JSON com inteiros, strings
ASCII/escapadas, booleanos, null, objetos/listas e espaços. Não cobre floats nem
JSON Schema completo. Os candidatos automáticos só trocam tipos de delimitadores
e vírgula/dois-pontos fora de strings; não inserem ou removem posições.

`--protect 6:7` protege o intervalo de bytes UTF-8 `[6,7)` do rascunho. A API de
tokens congela todo token que intersecta o intervalo. Isso protege os bytes do
trecho, não garante que um caminho semântico de JSON permaneça o mesmo sob qualquer
gramática. No esquema de registros, a estrutura também fixa o campo `id`.

Para outros esquemas/suportes, use `repair_tokens` com um `CnfGrammar`, adapter
composicional e alternativas por posição. O adapter aceita o vocabulário real;
`structural_token_support` conserva somente substituições presentes nele. O
perfil de bytes da CLI não deve ser apresentado como tokenização de LLaDA.

O certificado `OPTIMAL` garante o menor custo de substituição de tokens no suporte
informado, preservando as posições protegidas. Não garante distância de edição
irrestrita, correção factual ou sucesso semântico. `TIMEOUT`,
`INFEASIBLE_ON_SUPPORT`, `UNSUPPORTED` e `ERROR` são separados; nenhum deles
retorna uma correção certificada. Chaves duplicadas são rejeitadas por validação
JSON adicional, com abstenção, sem alegar que sua unicidade foi modelada pela CFG.

O limite da API é cooperativo e verifica o tempo total antes de entregar o resultado;
use o runner supervisionado para impor também limite de processo/memória. No runner,
a saída atrasada perde o certificado e conta como falha, mesmo que fosse válida.

## Evidência e reprodução

- Protocolo: `docs/research/m21-repair-protocol.md`.
- Resultados completos: `paper/generated/m21_repair_v1/report.md`.
- Resumo e comparações pareadas: `paper/generated/m21_repair_v1/summary.json`.
- Saídas brutas: `docs/artifacts/raw/m21_repair_v1/`.
- Construção/verificação: `scripts/exact_commit/build_json_repair_results.py`.

```bash
.venv/bin/python -m scripts.exact_commit.build_json_repair_results --check
make article-results-check
.venv/bin/python -m pytest -q tests/exact_commit/test_repair.py
```

As medições usam um commit limpo e configurações congeladas. A confirmação usa
20 documentos com seis variantes de erro/controle e duas repetições, em perfis
separados de bytes e tokenizer real do LLaDA. O estudo de gramática ambígua tem
oito documentos novos. Não são erros coletados de gerações reais do modelo.

O uso apropriado é recuperação estrutural restrita quando preservação importa,
com validação independente da aplicação. Reparadores simples são mais rápidos e
cobrem inserções fora desse suporte. Um parser sem pesos pode bastar quando o
esquema determina uma única correção; a ablação mede isso explicitamente. O próximo
estudo de saídas reais e nova tentativa do modelo continua separado, sem resultados
atribuídos a ele.
