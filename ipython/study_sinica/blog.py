#! python3
# -*- coding:utf-8-*-

import re
import numpy as np
import jieba

from ProductsRepo import ProductsRepo

from CKIPParser.call_ckip_parser import *
from CKIPParser.parse_tree import TreeNode

def check_contain_chinese(check_str):
    for ch in check_str:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False


jieba.set_dictionary('dict.txt.big')    
with open('resources/cosmetic_headwords.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    pheads = [l.strip() for l in lines]
for hw in pheads:
    jieba.add_word(hw)
    
with open('resources/brands_in_chinese.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    brands = [l.strip() for l in lines]
for brand in brands:
    jieba.add_word(brand)
 
class Sentence():
    def __init__(self, aid, line_no, content):
        self.aid = aid
        self.line_no = line_no
        self.sid = (aid,line_no)

        content = content.lower()
        self.content = content
        self.content_seg = [s for s in jieba.lcut(content) if not s.isspace()]
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

    def __str__(self):
        s = '{}- \n{}\n'.format(self.sid, self.content)
        return s
    
    
class Article():
    def __init__(self, aid, title, sentences, url, author, post_date, category, tags, hits):
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
        
        sentences_ss = []
        for s in sentences: #sentences: from argument ;
            ss = re.split(r'\n| 。|。|，|!|！|,|\?|． ' , s)
            sentences_ss.extend(ss)
        
        line_no = 1
        for line in sentences_ss:
            # if re.search('\S', line) is None:
            #     continue
            sent = Sentence(aid, line_no, line)
            self.sentences.append(sent)
            line_no +=1
            
    def __str__(self):
        s = 'title: ' + self.title + '\n'
        s += self.url + '\n'
        s += 'number of sentences {}'.format(len(self.sentences))  + '\n'
        s += str(self.sentences[0])
        return s
        

def load_articles(article_dir, restricted_num=None):
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
            a = Article(data['article_id'], data['title'], s_clean, data['url'], data['author'], data['post_date'],
                        data['category'], data['tags'], data['hits'])
            # print(a)
            articles.append(a)

    return articles

if __name__ == '__main__':
    from bs4 import BeautifulSoup
    import json
    
    article_dir = '../../data/styleMe/article_filtered/part-00000'
    a = load_articles(article_dir, 1)[0]
    print(a)
