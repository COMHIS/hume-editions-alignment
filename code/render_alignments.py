import argparse
from collections import defaultdict
import csv
import os
import os.path

PAGE_TEMPLATE = '''
<html>
<head>
<style>
body {{
  font-family: arial;
}}
.text {{
  max-width: 450px;
  text-align: right;
  padding: 10px;
}}
</style>
</head>
<body>
{body}
</body>
</html>
'''

# TODO duplication of run_alignment.py
def _doc_id(t, level):
    if level == 'book':
        return f'{ t["book"] }'
    elif level == 'page':
        return f'{ t["book"] }@{ t["page"] }'
    else:
        raise NotImplementedError()


def parse_arguments():
    parser = argparse.ArgumentParser(description='Render alignments as HTML.')
    parser.add_argument(
        '-i', '--input-file', metavar='FILE',
        help='The file to read the texts from.')
    parser.add_argument(
        '-a', '--alignments-file', metavar='FILE',
        help='The file to read the alignments from.')
    parser.add_argument(
        '-l', '--level', choices=['book', 'page'], default='page',
        help='The level of grouping sentences into texts.')
    parser.add_argument(
        '-o', '--output-dir', metavar='DIR',
        help='The directory to output the HTML files to.')
    return parser.parse_args()


def render_alignment(doc_id_1, doc_id_2, al, texts, output_dir):
    result = []
    
    ROW = '<tr><td class="text"><sup>{} </sup>{}</td>'\
          '<td class="text"><sup>{} </sup>{}</td><td>{:.3}</td></tr>'
    result.append('<table>')
    result.append('<tr><th class="text">{}</th><th class="text">{}</th>'
                  '<th>sim</th></tr>'.format(doc_id_1, doc_id_2))
    
    text_1 = texts[doc_id_1]
    text_2 = texts[doc_id_2]
    max_pos_1 = len(text_1)-1
    max_pos_2 = len(text_2)-1
    i, j = 0, 0
    while i <= max_pos_1 or j <= max_pos_2:
        if (not al and i <= max_pos_1) or (al and i < al[0][0]):
            result.append(ROW.format(i, text_1[i], '', '', ''))
            i += 1
            continue
        if (not al and j <= max_pos_2) or (al and j < al[0][1]):
            result.append(ROW.format('', '', j, text_2[j], ''))
            j += 1
            continue
        if al:
            result.append(ROW.format(i, text_1[i], j, text_2[j], al[0][2]))
            al.pop(0)
            i += 1
            j += 1
    result.append('</table>')
    
    filename = f'diff--{ doc_id_1 }--vs--{ doc_id_2 }.html'
    with open(os.path.join(output_dir, filename), 'w+') as fp:
        fp.write(PAGE_TEMPLATE.format(body = '\n'.join(result)))

def read_texts(filename, level='page'):
    result = defaultdict(list)
    with open(filename) as fp:
        reader = csv.DictReader(fp)
        for r in reader:
            result[_doc_id(r, level)].append(r['text'])
    return result

def process_alignments(filename, texts, output_dir):
    with open(filename) as fp:
        reader = csv.DictReader(fp)
        cur_doc_id_1, cur_doc_id_2 = None, None
        alignment = []
        for r in reader:
            if r['doc_id_1'] != cur_doc_id_1 or r['doc_id_2'] != cur_doc_id_2:
                if cur_doc_id_1 is not None and cur_doc_id_2 is not None:
                    render_alignment(cur_doc_id_1, cur_doc_id_2, alignment, texts, output_dir)
                cur_doc_id_1, cur_doc_id_2 = r['doc_id_1'], r['doc_id_2']
                alignment = []
            alignment.append((int(r['pos_1']), int(r['pos_2']), float(r['sim_cos'])))
        if cur_doc_id_1 is not None and cur_doc_id_2 is not None:
            render_alignment(cur_doc_id_1, cur_doc_id_2, alignment, texts, output_dir)

if __name__ == '__main__':
    args = parse_arguments()
    texts = read_texts(args.input_file, args.level)
    process_alignments(args.alignments_file, texts, args.output_dir)

