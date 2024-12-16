python = python3

all: html_output

data/work/texts.csv:
	$(python) code/segment_texts.py data/raw/*.json > $@

data/work/embeddings_ngrams.pt: data/work/texts.csv
	$(python) code/embed_ngrams.py -i $< -e $@ -d 450 -n 2

# Note: use the -m parameter to change the SentenceBERT model
data/work/embeddings_sbert.pt: data/work/texts.csv
	$(python) code/embed_sbert.py -i $< -e $@

data/final/alignments_ngrams.csv: \
  data/work/texts.csv \
  data/work/embeddings_ngrams.pt
	$(python) code/run_alignment.py \
	    -l book -i data/work/texts.csv -e data/work/embeddings_ngrams.pt > $@

data/final/alignments_sbert.csv: \
  data/work/texts.csv \
  data/work/embeddings_sbert.pt
	$(python) code/run_alignment.py \
	    -l book -i data/work/texts.csv -e data/work/embeddings_sbert.pt > $@

html_output: data/work/texts.csv data/final/alignments_ngrams.csv data/final/alignments_sbert.csv
	mkdir -p html_output
	mkdir -p html_output/ngrams
	mkdir -p html_output/sbert
	$(python) code/render_alignments.py \
	    -l book -i data/work/texts.csv -a data/final/alignments_ngrams.csv -o html_output/ngrams
	$(python) code/render_alignments.py \
	    -l book -i data/work/texts.csv -a data/final/alignments_sbert.csv -o html_output/sbert

