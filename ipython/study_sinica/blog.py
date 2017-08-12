#! python3
# -*- coding:utf-8-*-

import re
import numpy as np
import jieba

from ProductsRepo import ProductsRepo


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
    

def longest_common_substring(s1, s2):
    m = [[0] * (1 + len(s2)) for i in range(1 + len(s1))]
    longest, x_longest = 0, 0
    for x in range(1, 1 + len(s1)):
        for y in range(1, 1 + len(s2)):
            if s1[x - 1] == s2[y - 1]:
                m[x][y] = m[x - 1][y - 1] + 1
                if m[x][y] > longest:
                    longest = m[x][y]
                    x_longest = x
            else:
                m[x][y] = 0
    return s1[x_longest - longest: x_longest]

class Sentence():
    def __init__(self, aid, line_no, content):
        self.aid = aid
        self.line_no = line_no
        self.content = content
        self.content_seg = jieba.lcut(content)
        self.product_id = []
        
    def get_features_with_product(self, product, brand):
        '''
            product : list of terms
            brand : list of brand alias
        '''
        brand = [b.lower() for b in brand]
        sent = [term.lower() for term in self.content_seg]
        sent_str = ''.join(sent)
        sent_set =set(sent)
        product = [term.lower() for term in product]

        term_match_bin =  [1 if term in sent_set else 0 for term in product]

        # term match count
        p_term_count = len(product)
        term_match_count = sum(term_match_bin)
        term_match_prop = term_match_count / p_term_count

        #bigram
#         if p_term_count <2:
#             bigram_match_prop = 0
#         else:
#             bigram_match_count = 0
#             for i in range( (p_term_count-1) ):
#                 # bi_match  = 1 if term_match_bin[i]==1 and term_match_bin[i+1]==1 else 0
#                 bigram = product[i] + product[i+1]
#                 bi_match  = 1 if bigram in sent_str else 0
#                 bigram_match_count += bi_match

#             bigram_match_prop = bigram_match_count / (p_term_count-1)

#         #trigram
#         if p_term_count <3:
#             trigram_match_prop = 0
#         else:
#             trigram_match_count = 0
#             for i in range( (p_term_count-2) ):
#                 # tri_match  = 1 if term_match_bin[i]==1 and term_match_bin[i+1]==1 and term_match_bin[i+2]==1 else 0
#                 trigram = product[i] + product[i+1]+ product[i+2]
#                 tri_match  = 1 if trigram in sent_str else 0
                
#                 trigram_match_count += tri_match

#             trigram_match_prop = trigram_match_count / (p_term_count-2)
        
        #length of longest common substring 
        lcs_len = len(longest_common_substring(sent_str, ''.join(product)))
        
        #head term
        head_match = term_match_bin[0]

        #last term
        tail_match = term_match_bin[-1]

        #last 2 terms
        if p_term_count > 1:
            last2_match = 1 if term_match_bin[-1] == 1 and term_match_bin[-2]==1 else 0
        else:
        #last2_match = tail_match
            last2_match = 0

        #character level
        product_str = ''.join(product)
        sent_char_set = set(list(sent_str))
        char_match_count = sum([1 for c in product_str if c in sent_char_set])
        char_match_prop = char_match_count / len(product_str)

        #brand score
        brand_chi = []
        brand_eng = []
        for b in brand:
            if  check_contain_chinese(b):
                brand_chi.append(b)
            else:
                brand_eng.append(b)
        
        brand_chi_match = sum([1 for chi in brand_chi if chi in sent_set])
        brand_eng_match = 0
        for eng in brand_eng:
            mcount = sum([1 for word in eng.split(' ') if word in sent_set])
            mprop = mcount / len(eng.split(' '))
            if mprop > brand_eng_match:
                brand_eng_match = mprop

        brand_score = brand_chi_match + brand_eng_match

        features = np.array([term_match_prop, 
                                         #bigram_match_prop, 
                                         #trigram_match_prop, 
                                         lcs_len,
                                         head_match, 
                                         tail_match, 
                                         last2_match, 
                                         char_match_prop, 
                                         brand_score, 
                                         p_term_count])
        return features
    

    def __str__(self):
        s = 'article: {}\n{} - {}\n'.format(self.aid, self.line_no, self.content)
        return s
    
    
class Article():
    def __init__(self, aid, title, content, url, author, post_date, category, tags, hits):
        self.aid = aid
        self.title = title
        self.content = content
        self.url = url
        self.author = author
        self.post_date = post_date
        self.category = category
        self.tags = tags
        self.hits = hits
    
        self.sentences = []
        lines =  re.split(r'\\n| 。|，|!|！|,|\\?|． ' , content)
        for i, line in enumerate(lines):
            sent = Sentence(aid, i+1, line)
            self.sentences.append(sent)
    
    def __str__(self):
        s = 'title: ' + self.title + '\n' + 'content: ' + self.content[:200] + '\n'
        s += 'number of sentences {}'.format(len(self.sentences))  + '\n'
        s += str(self.sentences[0])
        return s
        

if __name__ == '__main__':
    from bs4 import BeautifulSoup
    import json
    
    article_dir = '../../data/styleMe/article_filtered/part-00000'
    with open(article_dir, 'r', encoding='utf-8') as fin:
        for line in fin:
            data = json.loads(line)
            # print(data)
            break
            
    soup = BeautifulSoup(data['content'], 'html.parser')
    for script in soup(["script", "style"]):
        script.decompose()    # rip it out
    content_clean = soup.get_text()
    a = Article(data['article_id'], data['title'], content_clean, data['url'], data['author'], data['post_date'], data['category'], data['tags'], data['hits'])
    print(a)

    style_repo = ProductsRepo('resources//StyleMe.csv')

    sent = Sentence(-1, -1, 'BOURJOIS 妙巴黎] 舒芙蕾糖霜分霧唇彩 是蜜糖還是毒藥？ #04#05兩色分享')
    p='舒芙蕾粉霧糖霜唇彩'
    p_seg = jieba.lcut(p)

    brand = style_repo.pname_to_brand[p]
    brand_alias = ProductsRepo.get_brand_alias(brand)
    
    print(sent.content_seg)
    print(p_seg)
    print(brand_alias)
    print(sent.get_features_with_product(p_seg, brand_alias))
    