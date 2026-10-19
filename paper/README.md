# Artigo

`main.tex` é o manuscrito **Certified Closure Bounds for JSON Infilling with
Diffusion Language Models**. Ele descreve o certificado de fechamento A24,
suas hipóteses, a comparação histórica e a aplicação iterativa.

O ganho histórico de consulta de 3/15 vale sob os comparadores originais.
O gate operacional posterior falhou nos 15 estados contra controles mais
fortes. Esse desfecho integra a leitura atual do projeto; consulte
[estado da pesquisa](../docs/status.md). Não há superioridade geral de geração,
qualidade semântica ou prioridade científica estabelecida.

```bash
make paper
```

Na raiz do repositório, esse comando verifica os dados e derivados antes de
compilar. Requer pdfLaTeX, BibTeX e `pdfinfo`; o PDF sai em `paper/main.pdf`.
Dentro desta pasta, `make` executa somente a compilação e a verificação do PDF.
Overleaf: envie a pasta, selecione `main.tex` e use pdfLaTeX.

`generated/` contém tabelas e números derivados. Não edite seus valores à mão.
As demais fontes `.tex` incluem suplementos e versões históricas; nem todas
são incluídas no artigo principal. O suplemento semântico é compilado com
`make -C paper research-note` a partir da raiz.
