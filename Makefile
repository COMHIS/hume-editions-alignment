python = python3

all: html_output

data/work/texts.csv:
	$(python) code/segment_texts.py data/raw/*.json > $@

data/final/alignments.csv: data/work/texts.csv
	$(python) code/run_alignment.py \
	    -i data/work/texts.csv -e data/work/embeddings.pt > $@

html_output: data/work/texts.csv data/final/alignments.csv
	mkdir -p html_output
	$(python) code/render_alignments.py \
	    -i data/work/texts.csv -a data/final/alignments.csv -o html_output

