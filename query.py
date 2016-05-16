# -*- coding: utf-8 -*-
import sys,os
import json
import re
import string
import ast
import xml.etree.ElementTree as ET
import uuid
import itertools
from subprocess import Popen, PIPE
from inspect import currentframe, getframeinfo
import argparse
import numpy as np

reload(sys)
sys.setdefaultencoding('utf-8')

class Query(object):
    """
    Get the judgments of a corpus.
    When constructing, pass the path of the corpus. For example, "../wt2g/"
    """
    def __init__(self, collection_path):
        self.corpus_path = os.path.abspath(collection_path)
        if not os.path.exists(self.corpus_path):
            frameinfo = getframeinfo(currentframe())
            print frameinfo.filename, frameinfo.lineno
            print '[Evaluation Constructor]:Please provide a valid corpus path'
            exit(1)

        self.query_file_path = os.path.join(self.corpus_path, 'json', 'unique_query.json')
        if not os.path.exists(self.query_file_path):
            frameinfo = getframeinfo(currentframe())
            print frameinfo.filename, frameinfo.lineno
            print """No query file found! 
                query file should be called "raw_topics" under 
                corpus path. You can create a symlink for it"""
            exit(1)

        self.parsed_query_file_path = os.path.join(self.corpus_path, 'json', 'parsed_topics.json')
        self.index_path = os.path.join(self.corpus_path, 'index')
        self.split_queries_root = os.path.join(self.corpus_path, 'split_queries')
        self.split_results_root = os.path.join(self.corpus_path, 'split_results')

    def write_query_file(self, t=[]):
        fpath = str(uuid.uuid4())
        with open(fpath, 'w') as f:
            for ele in t:
                f.write('<DOC>\n')
                f.write('<TEXT>\n')
                f.write(ele)
                f.write('\n')
                f.write('</TEXT>\n')
                f.write('</DOC>\n')
        return fpath


    def parse_query(self, t=[]):
        """
        use IndriTextTransformer to parse the query
        """
        fpath = self.write_query_file(t)
        try:
            process = Popen(['IndriTextTransformer', '-class=trectext', '-file='+fpath], stdout=PIPE)
            stdout, stderr = process.communicate()
            r = []
            for line in stdout.split('\n'):
                line = line.strip()
                if line:
                    r.append(line)
            os.remove(fpath)
        except:
            os.remove(fpath)
            raise NameError("parse query error!")
        return r


    def get_queries(self):
        """
        Get the query of a corpus

        @Return: a list of dict [{'num':'401', 'title':'the query terms',
         'desc':description, 'narr': narrative description}, ...]
        """

        if not os.path.exists(self.parsed_query_file_path):
            unique_queries = {}
            _all = []
            with open(self.query_file_path) as f:
                query_array = json.load(f).keys()
                idx = 1
                for i, query in enumerate(query_array):
                    parsed_query = self.parse_query([query])[0]
                    if parsed_query not in unique_queries:
                        unique_queries[parsed_query] = idx
                        _all.append({'query': parsed_query, 'num': idx, 'orig': query})
                        idx += 1
            with open(self.parsed_query_file_path, 'wb') as f:
                json.dump(_all, f, indent=2)

        exit()
        with open(self.parsed_query_file_path) as f:
            return json.load(f)

    def get_queries_dict(self):
        """
        Get the query of a corpus

        @Return: a dict with keys as qids {'401':{'title':'the title', 'desc':'the desc'}, ...}
        """
        all_queries = self.get_queries()
        all_queries_dict = {}
        for ele in all_queries:
            qid = ele['num']
            all_queries_dict[qid] = ele

        return all_queries_dict
        
    def get_queries_of_length(self, length):
        """
        Get the queries of a specific length

        @Input:
            length - the specific length. For example, length=1 get all queries
                     with single term

        @Return: a list of dict [{'num':'403', 'title':'osteoporosis',
         'desc':description, 'narr': narrative description}, ...]
        """

        all_queries = self.get_queries()
        filtered_queries = [ele for ele in all_queries if len(ele['title'].split()) == length]

        return filtered_queries


    def indent(self, elem, level=0):
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i


    def gen_query_file_for_indri(self, output_foler='split_queries', 
            index_path='index', is_trec_format=True, count=9999999, 
            remove_stopwords=False, use_which_part=['query']):
        """
        generate the query file for Indri use.

        @Input:
            output_root - the output root of the splitted query files
            index_path - the index path, default "index".
            is_trec_format - whether to output the results in TREC format, default True
            count - how many documents will be returned for each topic, default 1000
        """
        if remove_stopwords:
            with open('stopwords') as f:
                stop_words_list = [line.strip() for line in f.readlines()]

        output_root = os.path.join(self.corpus_path, output_foler)
        if not os.path.exists(output_root):
            os.makedirs(output_root)

        all_topics = self.get_queries()

        for ele in all_topics:
            for part in use_which_part:
                for i, query_term in enumerate(ele[part].split()):
                    for index_path in os.listdir(self.index_path):
                        qf = ET.Element('parameters')
                        index = ET.SubElement(qf, 'index')
                        index.text = os.path.join(self.corpus_path, 'index', index_path)
                        ele_trec_format = ET.SubElement(qf, 'trecFormat')
                        ele_trec_format.text = 'true' if is_trec_format else 'false'
                        ele_count = ET.SubElement(qf, 'count')
                        ele_count.text = str(count)

                        if remove_stopwords:
                            ele_stopwords = ET.SubElement(qf, 'stopper')
                            for w in stop_words_list:
                                stopword = ET.SubElement(ele_stopwords, 'word')
                                stopword.text = w
                        
                        t = ET.SubElement(qf, 'query')
                        qid = ET.SubElement(t, 'number')
                        qid.text = str(int(ele['num']))+'-'+str(i+1)
                        q = ET.SubElement(t, 'text')
                        q.text = query_term

                        self.indent(qf)

                        tree = ET.ElementTree(qf)
                        tree.write(os.path.join(self.corpus_path, output_root, part+'_'+qid.text+'_'+index_path))


    def gen_run_split_query_paras(self, methods, use_which_part=['query']):
        all_paras = []
        if not os.path.exists(self.split_results_root):
            os.makedirs(self.split_results_root)

        for qf in os.listdir( self.split_queries_root ):
            which_part = qf.split('_')[0]
            if which_part not in use_which_part:
                continue
            for m in methods:
                if 'paras' in m:
                    for p in itertools.product(*[ele[1] for ele in m['paras'].items()]):
                        para_str = '-rule=method:%s' % m['name']
                        tmp = '_%s' % m['name']
                        for k_idx, k in enumerate(m['paras'].keys()):
                            para_str += ',%s:%s' % (k, p[k_idx])
                            tmp += ',%s:%s' % (k, p[k_idx])
                        if m['name'] == 'worddocdensity':
                            para_str += ',dd_score_folder:%s' % os.path.join(self.corpus_path, 'queries_dd')
                        results_fn = os.path.join(self.split_results_root, qf+tmp)
                        if not os.path.exists(results_fn):
                            all_paras.append( (os.path.join(self.split_queries_root, qf), \
                                para_str, results_fn) )
                else:
                    para_str = '-rule=method:%s' % m['name']
                    results_fn = os.path.join(self.split_results_root, qf+'_%s' % m['name'])
                    if m['name'] == 'smart':
                            para_str += ',ctf_score_folder:%s' % os.path.join(self.corpus_path, 'smart_ctf')
                    if not os.path.exists(results_fn):
                        all_paras.append( (os.path.join(self.split_queries_root, qf), \
                            para_str, results_fn) )
        return all_paras

    def gen_query_mappings(self):
        """
        generate the query mapping: the original query 
        may contain characters (e.g. $,') which were removed 
        for IndrinRunQuery_EX. We need a mapping as well as 
        a mapping to query ID.
        """



    def gen_change_split_results_paras(self):
        """
        Reduce the split results contents by 
        removing the documents that are not occurred 
        in the query id. 
        """
        pass
        # judgement = {}
        # with open( os.path.join(self.corpus_path, 'json', 'judgement.json') ) as f:
        #     _judgement = json.load(f)
        #     for qid in _judgement:
                
        # for fn in os.listdir(self.split_results_root):
        #     with open(os.path.join(self.split_results_root, fn)) as f:
        #         pass


    def output_query_stats(self, query_part=None):
        l = []
        idf = []
        with open(self.parsed_query_file_path) as f:
            queries = json.load(f)
            for q in queries:
                if query_part:
                    q_terms = q[query_part].split()

                l.append( len(q_terms) )
                query_topic_idf = 0.0
                for t in q_terms:
                    process = Popen(['dumpindex_EX', os.path.join(self.corpus_path, 'index'), 'tf', t], stdout=PIPE)
                    stdout, stderr = process.communicate()
                    #print stdout
                    try:
                        j = json.loads(stdout)
                    except:
                        # it is probably because the term is not in the collection(index)
                        continue
                    query_topic_idf += float(j['log(idf1)'])
                idf.append( query_topic_idf )
        print np.mean(l), np.std(l)
        print np.mean(idf), np.std(idf)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-1", "--gen_standard_queries",
        nargs=1,
        help="Generate the standard queries for Indri. Please give the collection path!")

    parser.add_argument("-2", "--print_query_stats",
        nargs=1,
        help="Please give the collection path!")

    args = parser.parse_args()

    if args.gen_standard_queries:
        Query(args.gen_standard_queries[0]).gen_query_file_for_indri()

    if args.print_query_stats:
        Query(args.print_query_stats[0]).output_query_stats()
        