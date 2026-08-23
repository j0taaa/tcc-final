# TCC em LaTeX — MWPC para dLLMs sob CFGs

Este projeto contém uma base de artigo acadêmico no formato SBC para o TCC **“Compromisso Paralelo Exato de Peso Máximo sob Gramáticas Livres de Contexto para Modelos de Linguagem por Difusão”**.

Na compilação fornecida, o artigo possui **15 páginas**. O texto inclui a parte teórica essencial, definições formais, teoremas, demonstrações, três pseudocódigos, análise de complexidade, metodologia de implementação, protocolo experimental, resultados a preencher, limitações, cronograma e declaração de uso de IA.

## Arquivos

- `main.tex`: texto principal e ponto de entrada do projeto;
- `referencias.bib`: base BibTeX;
- `sbc-template.sty`, `sbc.bst` e `caption2.sty`: arquivos do formato SBC;
- `main.pdf`: prévia compilada;
- `CAMPOS_A_PREENCHER.md`: checklist dos dados que dependem da implementação;
- `Makefile`: comandos de compilação e limpeza.

## Compilação no Overleaf

1. Crie um projeto vazio e envie todos os arquivos deste diretório.
2. Defina `main.tex` como documento principal.
3. Use `pdfLaTeX` como compilador.
4. O Overleaf executará BibTeX automaticamente; em caso de referências pendentes, use **Recompile from scratch**.

## Compilação local

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Ou:

```bash
make
```

## Campos pendentes

Informações ainda desconhecidas aparecem por meio do comando:

```latex
\ph{informação a preencher}
```

No PDF, elas são exibidas em negrito e entre colchetes. Para localizar todas:

```bash
grep -n '\\ph{' main.tex
```

Substitua cada campo somente quando houver informação verificável. Resultados, tempos, uso de memória e métricas não devem ser estimados ou fabricados.

## Observações importantes

- A otimalidade demonstrada é relativa à etapa atual e ao suporte efetivamente representado no lattice.
- Caso seja usado top-K, o texto final deve afirmar que o método é exato sobre o suporte truncado, e não sobre todo o vocabulário.
- As provas pressupõem que o lattice e a interface lexical representam exatamente a semântica declarada; qualquer aproximação deve ser documentada.
- A bibliografia e as afirmações de novidade devem ser atualizadas antes da versão final, pois a área é recente.
- A declaração de uso de IA deve ser preenchida de acordo com o uso efetivo realizado pelo autor.
