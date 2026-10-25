# Dados e materiais de terceiros

Código A90 original segue a licença do repositório. Arquivos `sources/billion-*`
são cópias de inspeção do billion-context, commit fixo registrado no relatório,
licença MIT de Xianglei Ran e contribuidores; texto integral em
`sources/billion-LICENSE.txt`. Não se incorporou seu código ao executor A90.

`data/streams.json` inclui sete histórias do LongMemEval cleaned, revision
`98d7416c24c778c2fee6e6f3006e7a073259d48f`; `data/evaluation.json` contém perguntas e
referências correspondentes. Autores Di Wu et al.; licença MIT indicada na ficha
oficial do dataset e licença do repositório em `sources/longmemeval-LICENSE.txt`.
Histórias sintéticas são definidas em `prepare.py`. Conteúdo de avaliação não é
usado para treinar nem construir memória.

PDFs/HTMLs acadêmicos são downloads locais de consulta, ignorados pelo Git;
origem, hashes e leitura estão em `novelty.md` e manifests. Seus autores/licenças
mantêm os respectivos direitos. Não se republicam os artigos nesta tentativa.

Pesos LLaDA e Qwen não são copiados para o repositório. Revisions, fichas e blobs
locais estão em `evidence/models.json`; Qwen quantizado pelo projeto Unsloth.
Ver condições dos checkpoints oficiais antes de redistribuir pesos. Nenhuma
redistribuição de modelo faz parte desta entrega.
