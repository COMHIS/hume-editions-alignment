import argparse
from collections import defaultdict
import csv
import json
import os.path as P
import sys
import torch
import tqdm

from matrix_align import matrix_align
from sentence_transformers import SentenceTransformer

SIM_RAW_THR = 5
SIM_SYM_THR = 0.1
SIM_ONESIDED_THR = 0.1

def load_texts_by_book(filename):
    results = []
    with open(filename) as fp:
        reader = csv.DictReader(fp)
        for r in reader:
            if not results or results[-1]['book'] != r['book']:
                results.append({ 'book': r['book'], 'sentences': [] })
            results[-1]['sentences'].append({
                'pos': len(results[-1]['sentences']), 'text': r['text'] })
    return results

def load_texts_by_page(filename):
    results = []
    with open(filename) as fp:
        reader = csv.DictReader(fp)
        for r in reader:
            if not results or results[-1]['book'] != r['book'] \
                           or results[-1]['page'] != r['page']:
                results.append({ 'book': r['book'], 'page': r['page'],
                                 'sentences': [] })
            results[-1]['sentences'].append({ 'pos': int(r['pos']), 'text': r['text'] })
    return results

def _doc_id(t, level):
    if level == 'book':
        return f'{ t["book"] }'
    elif level == 'page':
        return f'{ t["book"] }@{ t["page"] }'
    else:
        raise NotImplementedError()

def parse_arguments():
    parser = argparse.ArgumentParser(description='Convert SKVR to CSV files.')
    parser.add_argument(
        '-i', '--input-file', metavar='FILE',
        help='The file to read the texts from.')
    parser.add_argument(
        '-e', '--embeddings-file', metavar='FILE',
        help='The file to save embeddings to or load them from.')
    parser.add_argument(
        '-l', '--level', choices=['book', 'page'], default='page',
        help='The level of grouping sentences into texts.')
    parser.add_argument(
        '-m', '--model', metavar='NAME',
        help='The SentenceBERT model to use.')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()

    # load the texts
    if args.level == 'book':
        texts = load_texts_by_book(args.input_file)
    elif args.level == 'page':
        texts = load_texts_by_page(args.input_file)
    else:
        raise NotImplementedError()

    # determine text boundaries
    b = torch.cumsum(torch.tensor([0] + [len(t['sentences']) for t in texts]), 0)
    
    # load or make the embeddings
    if P.isfile(args.embeddings_file):
        x = torch.load(args.embeddings_file)
    else:
        model = SentenceTransformer('all-MiniLM-L12-v2')
        sentences = [s['text'] for t in texts for s in t['sentences']]
        x = model.encode(sentences, convert_to_tensor=True,
                         normalize_embeddings=True)
        torch.save(x, args.embeddings_file)

    # check that the embeddings agree with the boundaries vector
    assert x.shape[0] == b[-1]

    # calculate the alignments
    als_w = csv.DictWriter(sys.stdout, ('doc_id_1', 'pos_1', 'doc_id_2', 'pos_2', 'sim_cos'))
    als_w.writeheader()
    for i in tqdm.tqdm(range(b.shape[0]-1)):
        s, a, w = matrix_align(x[b[i]:b[i+1],], x[b[i+1]:,], b[(i+1):]-b[i+1],
                               threshold=0.6, rescale=True, return_alignments=True)
        p1_len = b[i+1]-b[i]
        sim_l = s / p1_len
        p2_len = b[(i+2):]-b[(i+1):-1]
        sim_r = s / p2_len
        sim_sym = 2*s / (p2_len + p1_len)
        
        doc_id_1 = _doc_id(texts[i], args.level)
        for j in torch.argwhere((s > SIM_RAW_THR) \
                                & ((sim_l > SIM_ONESIDED_THR) \
                                    | (sim_r > SIM_ONESIDED_THR)) \
                                & (sim_sym > SIM_SYM_THR)
                               ).flatten():
            
            doc_id_2 = _doc_id(texts[i+int(j)+1], args.level)
            _ = als_w.writerows([{
                'doc_id_1': doc_id_1, 'pos_1': int(a[b[i+j+1]-b[i+1]+p]),
                'doc_id_2': doc_id_2, 'pos_2': p,
                'sim_cos': float(w[b[i+j+1]-b[i+1]+p])
            }
            for p in range(b[i+j+2]-b[i+j+1]) if a[b[i+j+1]-b[i+1]+p] > -1])

