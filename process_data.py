import sys,os
import codecs
import json
import argparse
import inspect
from inspect import currentframe, getframeinfo
import subprocess
import shlex

reload(sys)
sys.setdefaultencoding('utf-8')


class Process(object):
    def __init__(self, collection_path):
        self.corpus_path = os.path.abspath(collection_path)
        if not os.path.exists(self.corpus_path):
            frameinfo = getframeinfo(currentframe())
            print frameinfo.filename, frameinfo.lineno
            print '[Evaluation Constructor]:Please provide a valid corpus path'
            exit(1)

    def output_doc(self, fn_path, docno, raw_content):
        with open( fn_path, 'wb') as f:
            f.write('<DOC>\n')
            f.write('<DOCNO>%s</DOCNO>\n', docno)
            f.write('<TEXT>\n')
            f.write('%s\n' % raw_content)
            f.write('</TEXT>\n')
            f.write('</DOC>\n')

    def output_documents_for_index(self):
        with open( os.path.join(self.corpus_path, 'docs.json') ) as f:
            docs = json.load(f)

        abstract_dir = os.path.join(self.corpus_path, 'abstract')
        if not os.path.exists(abstract_dir):
            os.makedirs(abstract_dir)
        raw_dir = os.path.join(self.corpus_path, 'raw')
        if not os.path.exists(raw_dir):
            os.makedirs(raw_dir)
        first_30_char_dir = os.path.join(self.corpus_path, 'first30')
        if not os.path.exists(first_30_char_dir):
            os.makedirs(first_30_char_dir)

        for doc in docs:
            docno = doc['docno']
            self.output_doc(os.path.join(abstract_dir, docno), docno, doc['abstra'])
            self.output_doc(os.path.join(raw_dir, docno), docno, doc['rawText'])
            word_vec = ' '.join(doc['rawText'].split()[:30])
            self.output_doc(os.path.join(first_30_char_dir, docno), docno, word_vec)
            

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-o", "--output_documents_for_index",
        nargs=1,
        help="Re-generate MicroBlog Corpus")

    args = parser.parse_args()

    if args.output_documents_for_index:
        Process(args.output_documents_for_index[0]).output_documents_for_index()


