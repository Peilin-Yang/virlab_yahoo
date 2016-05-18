import sys,os
import codecs
import json
import argparse
import inspect
from inspect import currentframe, getframeinfo
import subprocess
import shlex
from operator import itemgetter

reload(sys)
sys.setdefaultencoding('utf-8')


g_collection_root = '../'

class Process(object):
    def __init__(self, collection_path):
        self.corpus_path = os.path.abspath(collection_path)
        if not os.path.exists(self.corpus_path):
            frameinfo = getframeinfo(currentframe())
            print frameinfo.filename, frameinfo.lineno
            print '[Process Constructor]:Please provide a valid corpus path'
            exit(1)

        self.unique_query_fn = os.path.join(self.corpus_path, 'json', 'unique_query.json')
        self.query_mapping_fn = os.path.join(self.corpus_path, 'json', 'query_mapping.json')

    def output_doc(self, fn_path, docno, raw_content):
        with open( fn_path, 'ab') as f:
            f.write('<DOC>\n')
            f.write('<DOCNO>%s</DOCNO>\n' % docno)
            f.write('<TEXT>\n')
            f.write('%s\n' % raw_content)
            f.write('</TEXT>\n')
            f.write('</DOC>\n')

    def output_documents_for_index(self):
        raise RuntimeError("Must Be implement by derived class")

class ProcessTask0(Process):
    def output_documents_for_index(self):
        with open( os.path.join(self.corpus_path, 'json', 'docs.json') ) as f:
            docs = json.load(f)

        for query in docs:
            for doc in docs[query]:
                docno = str(doc['url'])
                self.output_doc(os.path.join(self.corpus_path, 'corpus', 'title'), docno, doc['title'])
                self.output_doc(os.path.join(self.corpus_path, 'corpus', 'abstract'), docno, doc['abstra'])
                self.output_doc(os.path.join(self.corpus_path, 'corpus', 'raw'), docno, doc['rawText'])
                word_vec = ' '.join(doc['rawText'].split()[:30])
                self.output_doc(os.path.join(self.corpus_path, 'corpus', 'first30'), docno, word_vec)


class ProcessTask1(Process):
    def output_documents_for_index(self):
        with open( os.path.join(self.corpus_path, 'json', 'docs.json') ) as f:
            docs = json.load(f)

        for doc in docs:
            docno = str(doc['docno'])
            self.output_doc(os.path.join(self.corpus_path, 'corpus', 'title'), docno, doc['title'])
            self.output_doc(os.path.join(self.corpus_path, 'corpus', 'abstract'), docno, doc['abstra'])
            self.output_doc(os.path.join(self.corpus_path, 'corpus', 'raw'), docno, doc['rawText'])
            word_vec = ' '.join(doc['rawText'].split()[:30])
            self.output_doc(os.path.join(self.corpus_path, 'corpus', 'first30'), docno, word_vec)

    def output_judgement(self):
        """
        NOTICE: MUST RUN "python run_batch.py -a 0" BEFORE THIS CALL!!!!

        For each query, output all the documents that occur at least 
        once in its judgement. Try to count the times the document gets 
        positive and negative; We might want a ranking list though.
        """
        with open( self.unique_query_fn ) as f:
            queries = json.load(f)
        with open( self.query_mapping_fn ) as f:
            query_mapping = json.load(f)
        unique_query = {}
        for query in queries:
            if query not in query_mapping:
                continue
            qid = query_mapping[query]['num']
            unique_query[qid] = []
            for docid in queries[query]:
                unique_query[qid].append( (docid, queries[query][docid]['pos_cnt']) )
        for qid in unique_query:
            unique_query[qid].sort(key=itemgetter(1, 0), reverse=True)
        with open( os.path.join(self.corpus_path, 'json', 'judgement.json'), 'wb' ) as f:
            json.dump(unique_query, f, indent=2, sort_keys=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-o", "--output_documents_for_index",
        nargs=1,
        help="")

    parser.add_argument("-j", "--output_judgement",
        nargs=1,
        help="See the explanations in function definition")

    args = parser.parse_args()

    if args.output_documents_for_index:
        p = ProcessTask0 if args.output_documents_for_index[0] == 'task_0' else ProcessTask1
        p(os.path.join(g_collection_root, args.output_documents_for_index[0]))
            .output_documents_for_index()
    if args.output_judgement:
        p = ProcessTask0 if args.output_judgement[0] == 'task_0' else ProcessTask1
        p(os.path.join(g_collection_root, args.output_judgement[0]))
            .output_judgement()

