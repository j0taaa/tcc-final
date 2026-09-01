# TCC in LaTeX — Exact MWPC for CFG-constrained dLLMs

This directory contains the SBC-format article for the TCC **“Exact
Maximum-Weight Parallel Commitment under Context-Free Grammars for Diffusion
Language Models.”**

The current build has **16 pages**. The manuscript includes the essential
theory, formal definitions, theorems, proofs, three pseudocode listings,
complexity analysis, implementation methodology, experimental protocol,
three generated result elements, limitations, and the AI-use declaration.

## Files

- `main.tex`: main manuscript and project entry point;
- `referencias.bib`: BibTeX database;
- `sbc-template.sty`, `sbc.bst`, and `caption2.sty`: SBC format files;
- `main.pdf`: local compiled preview;
- `FIELDS_TO_FILL.md`: checklist of implementation-dependent fields;
- `generated/`: small tables and figures produced only by scripts from
  versioned raw JSONL; and
- `Makefile`: build and cleanup commands.

## Building with Overleaf

1. Create an empty project and upload every file in this directory.
2. Set `main.tex` as the main document.
3. Select `pdfLaTeX` as the compiler.
4. Overleaf runs BibTeX automatically. If references remain unresolved, use
   **Recompile from scratch**.

## Building locally

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Or:

```bash
make
```

## Remaining fields

Information that has not yet been established appears through this command:

```latex
\ph{field to fill}
```

The PDF renders these fields in bold and inside brackets. To find all of them:

```bash
grep -n '\\ph{' main.tex
```

Replace a field only when verifiable evidence is available. Results, runtimes,
memory use, and metrics must never be estimated or fabricated. Do not edit
numbers under `generated/` manually; use the generator and manifest described
in `docs/artifacts/README.md`.

## Important notes

- The proven optimality is per-step and relative to the finite support actually
  represented by the lattice.
- With top-K support, the final text must say `exact_on_support`; it must not
  claim global exactness over the full vocabulary.
- The proofs assume that the lattice and lexical interface exactly represent
  their declared semantics. Every approximation must be documented.
- The bibliography and novelty claims must be updated before the final version
  because this is a rapidly evolving research area.
- The AI-use declaration must describe the author's actual use of the tools.
