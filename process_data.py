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
        with open( fn_path, 'ab') as f:
            f.write('<DOC>\n')
            f.write('<DOCNO>%s</DOCNO>\n' % docno)
            f.write('<TEXT>\n')
            f.write('%s\n' % raw_content)
            f.write('</TEXT>\n')
            f.write('</DOC>\n')

    def output_documents_for_index(self):
        with open( os.path.join(self.corpus_path, 'docs.json') ) as f:
            docs = json.load(f)

        for doc in docs:
            docno = str(doc['docno'])
            self.output_doc(os.path.join(self.corpus_path, 'abstract'), docno, doc['abstra'])
            self.output_doc(os.path.join(self.corpus_path, 'raw'), docno, doc['rawText'])
            word_vec = ' '.join(doc['rawText'].split()[:30])
            self.output_doc(os.path.join(self.corpus_path, 'first30'), docno, word_vec)
            

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-o", "--output_documents_for_index",
        nargs=1,
        help="Re-generate MicroBlog Corpus")

    args = parser.parse_args()

    if args.output_documents_for_index:
        Process(args.output_documents_for_index[0]).output_documents_for_index()


