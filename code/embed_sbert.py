import argparse
import csv
import torch

from sentence_transformers import SentenceTransformer


def parse_arguments():
    parser = argparse.ArgumentParser(description='Calculate SentenceBERT embeddings.')
    parser.add_argument(
        '-i', '--input-file', metavar='FILE',
        help='The file to read the texts from.')
    parser.add_argument(
        '-e', '--embeddings-file', metavar='FILE',
        help='The file to save embeddings to or load them from.')
    parser.add_argument(
        '-m', '--model', metavar='NAME', default='all-MiniLM-L12-v2',
        help='The SentenceBERT model to use.')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()

    with open(args.input_file) as fp:
        sentences = [r['text'] for r in csv.DictReader(fp)]

    model = SentenceTransformer(args.model)
    x = model.encode(sentences, convert_to_tensor=True,
                     normalize_embeddings=True)
    torch.save(x, args.embeddings_file)

