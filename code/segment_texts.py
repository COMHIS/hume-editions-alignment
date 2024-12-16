import argparse
import csv
import json
import os.path
import sys
from spacy.lang.en import English

# TODO segment also the footnotes
# add a flag for sentence segmentation?

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Convert multiple JSON files to sentence-segmented CSV.')
    parser.add_argument(
        'input_files', nargs='*', metavar='FILE', default=[],
        help='A list of input files in JSON format.')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()

    # initialize the spacy model
    nlp = English()
    nlp.add_pipe("sentencizer")

    writer = csv.DictWriter(sys.stdout, ('book', 'page', 'region', 'pos', 'text'))
    writer.writeheader()
    for f in args.input_files:
        with open(f) as fp:
            data = json.load(fp)
            for page in data['pages']:
                for reg in page['PageData']:
                    region = reg['region']
                    pos_counter = 0 # Pos counter value is reseted after each region.
                    for sentence in nlp(' '.join(reg['lines'])).sents:
                        writer.writerow({
                            'book': os.path.basename(f).replace('.json', ''),
                            'page': page['PageNumber'],
                            'region': region,
                            'pos': pos_counter,
                            'text': str(sentence).replace('- ', '')
                        })
                        pos_counter += 1
