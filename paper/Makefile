BIBTEX ?= bibtex

.PHONY: all clean

all:
	pdflatex -interaction=nonstopmode -halt-on-error main.tex
	$(BIBTEX) main
	pdflatex -interaction=nonstopmode -halt-on-error main.tex
	pdflatex -interaction=nonstopmode -halt-on-error main.tex
	python3 ../scripts/check_paper.py

clean:
	rm -f main.aux main.bbl main.blg main.fdb_latexmk main.fls main.log main.out main.toc main.synctex.gz
