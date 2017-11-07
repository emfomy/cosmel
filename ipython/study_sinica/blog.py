#! python3
# -*- coding:utf-8-*-

import re
import numpy as np
# import jieba
import os

from ProductsRepo import ProductsRepo

# from CKIPParser.call_ckip_parser import *
# from CKIPParser.parse_tree import TreeNode

from CKIP_Client.CKIP_Client import *

#-------------- for error logging -------------- 
import logging
logger = logging.getLogger('blog')
# logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(message)s')
ch.setFormatter(formatter)

# add the handlers to logger
logger.addHandler(ch)

def check_contain_chinese(check_str):
    for ch in check_str:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False


# jieba.set_dictionary('dict.txt.big')    
# with open('resources/cosmetic_headwords.txt', 'r', encoding='utf-8') as f:
#     lines = f.readlines()
#     pheads = [l.strip() for l in lines]
# for hw in pheads:
#     jieba.add_word(hw)
    
# with open('resources/brands_in_chinese.txt', 'r', encoding='utf-8') as f:
#     lines = f.readlines()
#     brands = [l.strip() for l in lines]
# for brand in brands:
#     jieba.add_word(brand)
 
class Sentence():
    def __init__(self, aid, line_no, content, input_ws=False):
        self.aid = aid
        self.line_no = line_no
        self.sid = (aid,line_no)

        self.content = ''
        self.content_seg = []
        content = content.lower()
        if not input_ws:
            # logger.debug('content: {}'.format(content))
            self.content = content
            # self.content_seg = [s for s in jieba.lcut(content) if not s.isspace()]
            # self.content_seg = seg(content)
            # logger.debug('content: {}'.format(self.content_seg))
        else:
            self.content_seg = [ w.replace('('+w.split('(')[-1],'').replace('\n','') for w in content.split(u'　') if w != '']
            self.content = ''.join(w for w in self.content_seg)
            # logger.debug('content: {}\ncontent_seg: {}'.format(self.content, self.content_seg))
            
        self.label_content = ''

        self.span_ranges = []
        self.span_methods = {}
        self.product_ids = []
        self.product_brands = []
        # self.span_list = []

    def markSpan(self):
        # print('--marking span--')
        spans = [self.content_seg[s[0]:s[1] + 1] for s in self.span_ranges]
        for i, sp in enumerate(spans):
            item = ''.join(t for t in sp)
            method = self.span_methods[self.span_ranges[i]]
            label = '<pid_{}= \'{}\', gid= \'\'>{}</pid_{}>'.format(method, self.product_ids[i], item, method)
            pattern = '\s*'.join(t for t in sp)
            # self.label_content = self.content.replace(item, label) #TODO: space problem
            self.label_content = re.sub(pattern, label, self.content) 
    
    def dump(self):
        return self.content+'\n'

    def __str__(self):
        s = '{}- \n{}\n'.format(self.sid, self.content)
        return s
    
    
class Article():
    def __init__(self, aid, title, sentences, url, author, post_date, category, tags, hits, input_ws_sentence=[]):
        self.aid = aid
        self.title = title
        # self.content = content
        self.url = url
        self.author = author
        self.post_date = post_date
        self.category = category
        self.tags = tags
        self.hits = hits
        
        self.matched_sentence_id = []
        self.match_products = []
        self.match_brands = []

        self.sentences = []
        #title
        self.sentences.append(Sentence(aid, 0, title))
        
        if len(input_ws_sentence)==0:
            sentences_ss = []
            for s in sentences: #sentences: from argument ;
                ss = re.split(r'\n| 。|。|，|!|！|,|\?|． ' , s)
                sentences_ss.extend(ss)
            
            line_no = 1
            for line in sentences_ss:
                # if re.search('\S', line) is None:
                #     continue
                line = line.strip()
                if len(line)==0: continue
                sent = Sentence(aid, line_no, line)
                self.sentences.append(sent)
                line_no +=1
        else:
            line_no = 1
            for line in input_ws_sentence:
                line = line.strip()
                if len(line)==0: continue
                sent = Sentence(aid, line_no, line, input_ws=True)
                self.sentences.append(sent)
                line_no += 1
    
    def dump(self):
        s = 'title:{}, {}\n'.format(self.title, self.url)
        for sent in self.sentences:
            s += sent.dump()
        return s

    def __str__(self):
        s = 'title: ' + self.title + '\n'
        s += self.url + '\n'
        s += 'number of sentences {}'.format(len(self.sentences))  + '\n'
        s += str(self.sentences[0])
        return s


def load_articles(article_dir, restricted_num=None, dump_articles=False, input_ws=False):
    import json
    from bs4 import BeautifulSoup

    articles = []

    with open(article_dir, 'r', encoding='utf-8') as fin:
        for i, line in enumerate(fin.readlines()):
            if restricted_num and i > restricted_num:
                break

            data = json.loads(line)
            try:
                soup = BeautifulSoup(data['content'], 'html.parser')
            except KeyError:
                print('KeyError, line:', line, 'data:', data)
                continue

            for script in soup(["script", "style"]):
                script.decompose()  # rip it out
            s_clean = [s for s in soup.stripped_strings]

            seg_content = []
            if input_ws:
                ws_fin_dir = './resources/original_article_ws/'+article_dir.split('/')[-1]
                ws_fin = os.path.join(ws_fin_dir, '{}_{}.txt.tag'.format(data['author'], data['article_id']))
                seg_content = open(ws_fin, 'r', encoding='utf-8').readlines()[1:]
                # logger.debug('seg_content:{}'.format(seg_content[:5]))

            a = Article(data['article_id'], data['title'], s_clean, data['url'], data['author'], data['post_date'],
                        data['category'], data['tags'], data['hits'], input_ws_sentence=seg_content)
            # print(a)
            ## dump articles as raw text file
            if dump_articles:
                output_dir = './resources/original_article/'
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                output_file_dir = output_dir+article_dir.split('/')[-1]
                if not os.path.exists(output_file_dir):
                    os.makedirs(output_file_dir)
                output_file = os.path.join(output_file_dir, '{}_{}.txt'.format(a.author, a.aid))
                with open(output_file, 'w') as fout:
                    fout.write(a.dump())

            articles.append(a)

    logger.debug('finish loading filepart: {}'.format(article_dir.split('/')[-1]))
    return articles

if __name__ == '__main__':
    from bs4 import BeautifulSoup
    import json
    
    article_dir = '../../data/styleMe/article_filtered/part-00000'
    a = load_articles(article_dir, 1)[0]
    print(a)
