all:
	pdflatex main.tex pdflatex -shell-escape
	-bibtex main
	pdflatex main.tex pdflatex -shell-escape
	
clean:
	-rm -f  *.aux
	-rm -f  *.log
	-rm -f  *.gz
	-rm -f  *.blg
	-rm -f  *.bbl
	-rm -f  *.lof
	-rm -f  *.lot
	-rm -f  *.out
	-rm -f  *.ptc
	-rm -f  *.toc
	-rm -f  *blx.bib
	-rm -f  *run.xml
	-rm -f  *.bcf    
