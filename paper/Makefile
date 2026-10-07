BIBTEX ?= bibtex

.PHONY: all research-note clean

all:
	pdflatex -interaction=nonstopmode -halt-on-error main.tex
	$(BIBTEX) main
	pdflatex -interaction=nonstopmode -halt-on-error main.tex
	pdflatex -interaction=nonstopmode -halt-on-error main.tex
	python3 ../scripts/check_paper.py

research-note:
	pdflatex -interaction=nonstopmode -halt-on-error semantic-conditioning.tex
	$(BIBTEX) semantic-conditioning
	pdflatex -interaction=nonstopmode -halt-on-error semantic-conditioning.tex
	pdflatex -interaction=nonstopmode -halt-on-error semantic-conditioning.tex
	python3 ../scripts/check_paper.py --pdf semantic-conditioning.pdf --min-pages 1 --max-pages 8
	mkdir -p ../output/pdf
	cp semantic-conditioning.pdf ../output/pdf/semantic-conditioning.pdf

clean:
	rm -f main.aux main.bbl main.blg main.fdb_latexmk main.fls main.log main.out main.toc main.synctex.gz
