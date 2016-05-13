import sys,os
import codecs
import json
import argparse
import inspect
from inspect import currentframe, getframeinfo
import subprocess
import shlex
from operator import itemgetter

import numpy as np

reload(sys)
sys.setdefaultencoding('utf-8')


class Features(object):
    def __init__(self, collection_path):
        self.corpus_path = os.path.abspath(collection_path)
        if not os.path.exists(self.corpus_path):
            frameinfo = getframeinfo(currentframe())
            print frameinfo.filename, frameinfo.lineno
            print '[Features Constructor]:Please provide a valid corpus path'
            exit(1)

        self.split_results_root = os.path.join(self.corpus_path, 'split_results')
        self.features_root = os.path.join(self.corpus_path, 'features')
        if not os.path.exists(self.features_root):
            os.makedirs(self.features_root)

    def output_retrieval_score(self):
        all_queries = {}
        for fn in os.listdir(self.split_results_root):
            fn_split = fn.split('_')
            query_type = fn_split[0]
            qid = fn_split[1].split('-')[0]
            if qid not in all_queries:
                all_queries[qid] = {}
            termid = fn_split[1].split('-')[1]
            method = fn_split[-1]
            with open(os.path.join(self.split_results_root, fn)) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        row = line.split()
                        docid = row[2]
                        if docid not in all_queries[qid]:
                            all_queries[qid][docid] = {}
                        if method not in all_queries[qid][docid]:
                            all_queries[qid][docid][method] = []
                        all_queries[qid][docid][method].append(float(row[4]))
        with open( os.path.join(self.features_root, 'retrieval_score.json'), 'wb' ) as f:
            json.dump(all_queries, f, indent=2, sort_keys=True)

    def output_features_json(self, fn_path, docno, raw_content):
        with open( os.path.join(self.corpus_path, 'json', 'judgement.json') ) as f:
            judgement = json.load(f)
        template = {}
        for query in judgement:
            template[query] = {}
            for doc in judgement[query]:
                template[query][doc[0]] = {'pos_cnt': doc[1]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-j", "--output_features_json",
        nargs=1,
        help="")

    parser.add_argument("-r", "--output_retrieval_score",
        nargs=1,
        help="")

    args = parser.parse_args()

    if args.output_features_json:
        Features(args.output_features_json[0]).output_features_json()
    if args.output_retrieval_score:
        Features(args.output_retrieval_score[0]).output_retrieval_score()
