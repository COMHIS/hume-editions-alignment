import argparse
import csv
import torch

from shortsim.ngrcos import vectorize


def parse_arguments():
    parser = argparse.ArgumentParser(description='Calculate n-gram embeddings.')
    parser.add_argument(
        '-i', '--input-file', metavar='FILE',
        help='The file to read the texts from.')
    parser.add_argument(
        '-e', '--embeddings-file', metavar='FILE',
        help='The file to save embeddings to or load them from.')
    parser.add_argument(
        '-d', '--dim', type=int, default=200,
        help='The number of dimensions of n-gram vectors')
    parser.add_argument(
        '-n', type=int, default=2,
        help='The size (`n`) of the n-grams (default: 2, i.e. ngrams).')
    parser.add_argument(
        '-w', '--weighting', choices=['plain', 'sqrt', 'binary'],
        default='plain', help='Weighting of bigram frequencies.')

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()

    with open(args.input_file) as fp:
        sentences = [r['text'] for r in csv.DictReader(fp)]

    x = vectorize(sentences, n=args.n, dim=args.dim, weighting=args.weighting,
                  normalize=True)
    torch.save(torch.from_numpy(x), args.embeddings_file)

