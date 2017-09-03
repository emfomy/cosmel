#! python3
# -*- coding:utf-8 -*-

from ProductsRepo import *
from blog import Article, Sentence, load_articles

from CKIPParser.call_ckip_parser import *
from CKIPParser.parse_tree import TreeNode

import numpy as np
from sklearn.externals import joblib

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

class ClassifierMethod(object):
    """docstring for ClassName"""
    def __init__(self, model_path):
        self.model = joblib.load(model_path) 
        self.method_id = 'd'
        # pass

    @staticmethod
    def search_span(sentence, headword_set, decription_set, brand_set):
        possible_spans = []

        decription_set = set([term.lower() for term in decription_set])
        brand_set = set([term.lower() for term in brand_set])
        headword_set = set([term.lower() for term in headword_set])

        existed_heads = [] 
        for i, term in enumerate(sentence.content_seg):
            if term in headword_set:
                existed_heads.append((i, term))

        for pos, term in existed_heads:
            if pos==0:  #只有headword的就不管
                continue

            end = pos
            start = pos
            
            #at least one desciption word
            prev = sentence.content_seg[pos-1]
            if prev in decription_set:
                start -=1

            if start < end: #check continuously 
                #search for desciption or brand
                check_pos= pos-1 
                while check_pos>0:
                    prev = sentence.content_seg[check_pos-1]
                    if prev in decription_set | brand_set:
                        start -=1
                        check_pos -= 1 
                    else:
                        break

            else:
                prev_all = ''.join(sentence.content_seg[:pos])
                # if '這' in prev_all:
                #     #find position of 這
                #     for prev_pos in range(pos-1,  -1, -1): #if headword at i=3, check position 2,1,0
                #         if '這' in sentence.content_seg[prev_pos]:
                #             this_pos = prev_pos
                #     this_clause = ''.join(sentence.content_seg[this_pos: pos+1])  #取出這款唇膏之類的

                #     #use parser and construct parse tree
                #     try:
                #         parse_result = parse_sentences(this_clause)[0]
                #         root = TreeNode(parse_result)

                #         #find NP clause
                #         all_np = root.getAllTargetNodes('NP')
                #         all_np_str = [''.join(node.getAllLeafData()) for node in all_np]

                #         if this_clause in all_np_str:
                #             start = this_pos

                #     except Exception as e:
                #         print(str(e))
                #         print('Error occurs when parsing sentence')
                         
            if start < end:
                possible_spans.append((start,end)) 

        # select the longest span
        possible_spans.sort(key= lambda pair: pair[1]-pair[0])

        repeat = []
        for i,span in enumerate(possible_spans):
            for span_check in possible_spans[i+1:]:
                if span[0] >= span_check[0] and span[1] <= span_check[1]: #check if span_check contains span
                    repeat.append(span)
                    break 
        for repeat_span in repeat:
            possible_spans.remove(repeat_span)

        return possible_spans
 
    @staticmethod
    def get_features_with_product(sentence, product, brand, span_range):
        '''
            product : list of terms
            brand : list of brand alias
        '''
        span_positions = list(range(span_range[0], span_range[1]+1))
        span_terms = [sentence.content_seg[pos] for pos in span_positions]

        span_termset = set(span_terms)
        span_str = ''.join(span_terms)
        
        context_positions = [i for i in range(len(sentence.content_seg)) if i not in span_positions]
        context_termset = set([sentence.content_seg[i] for i in context_positions])

        brand = [b.lower() for b in brand]
        brand_chi = []
        brand_eng = []
        for b in brand:
            if  check_contain_chinese(b):
                brand_chi.append(b)
            else:
                brand_eng.append(b)

        product = [term.lower() for term in product]
        product_str = ''.join(product)

        # --------------- features from span ---------------

        span_term_match_bin =  [1 if term in span_termset else 0 for term in product]

        # term match count
        p_term_count = len(product)
        span_term_match_count = sum(span_term_match_bin)
        span_term_match_prop = span_term_match_count / p_term_count

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
        span_lcs_len = len(longest_common_substring(span_str, ''.join(product)))
        
        #head term
        span_head_match = span_term_match_bin[0]

        #last term
        span_tail_match = span_term_match_bin[-1]

        #last 2 terms
        if p_term_count > 1:
            span_last2_match = 1 if span_term_match_bin[-1] == 1 and span_term_match_bin[-2]==1 else 0
        else:
        #last2_match = tail_match
            span_last2_match = 0

        #character level
        span_char_set = set(list(span_str))
        span_char_match_count = sum([1 for c in product_str if c in span_char_set])
        span_char_match_prop = span_char_match_count / len(product_str)

        #brand score
        brand_chi_match = sum([1 for chi in brand_chi if chi in span_termset])
        brand_eng_match = 0
        for eng in brand_eng:
            mcount = sum([1 for word in eng.split(' ') if word in span_termset])
            mprop = mcount / len(eng.split(' '))
            if mprop > brand_eng_match:
                brand_eng_match = mprop

        span_brand_score = brand_chi_match + brand_eng_match

        #--------------- features from span context ---------------
        context_term_match_bin =  [1 if term in context_termset else 0 for term in product]

        # term match count
        context_term_match_count = sum(context_term_match_bin)
        context_term_match_prop = context_term_match_count / p_term_count

        #head term
        context_head_match = context_term_match_bin[0]

        #last term
        context_tail_match = context_term_match_bin[-1]

        #last 2 terms
        if p_term_count > 1:
            context_last2_match = 1 if context_term_match_bin[-1] == 1 and context_term_match_bin[-2]==1 else 0
        else:
            context_last2_match = 0

        #brand score
        brand_chi_match = sum([1 for chi in brand_chi if chi in context_termset])
        brand_eng_match = 0
        for eng in brand_eng:
            mcount = sum([1 for word in eng.split(' ') if word in context_termset])
            mprop = mcount / len(eng.split(' '))
            if mprop > brand_eng_match:
                brand_eng_match = mprop

        context_brand_score = brand_chi_match + brand_eng_match

        features = np.array([span_term_match_prop, 
                                         #bigram_match_prop, 
                                         #trigram_match_prop, 
                                         span_lcs_len,
                                         span_head_match, 
                                         span_tail_match, 
                                         span_last2_match, 
                                         span_char_match_prop, 
                                         span_brand_score, 
                                         context_term_match_prop,
                                         context_head_match,
                                         context_tail_match,
                                         context_last2_match,
                                         context_brand_score,
                                         p_term_count])
        return features
    
    def extract_product(self, sentence, article, products_repo):
        detected = []
        phead_set = products_repo.get_head_termset()
        decription_set = products_repo.get_all_descriptive_termset()
        brands_ori = products_repo.get_all_brands()
        brand_set = set(brands_ori)
        for b in brands_ori:
            brand_set.update(products_repo.get_brand_alias(b))

        possible_spans = self.search_span(sentence, phead_set, decription_set, brand_set)
        
        # no span
        if not possible_spans:
            return 0
        
        found = False
        for span_range in possible_spans: 
            X = []
            for pid, pname_seg in zip(products_repo.allpinds, products_repo.allproducts_seg):
        #         if len(pname_seg) == 0:
        #             continue
                brand = products_repo.pname_to_brand[products_repo.pind_to_pname[pid]]
                brand_alias = products_repo.get_brand_alias(brand)
                feat = self.get_features_with_product(sentence, pname_seg, brand_alias, span_range)
                X.append(feat)

            X = np.array(X)

            proba = self.model.predict_proba(X)
            pred_pid_id = np.argmax(proba, axis=0)[1]
            if proba[ pred_pid_id, 0] > proba[pred_pid_id, 1]: # proba of class 0 > proba of class 1:
                pass

            else:
                pred_pid = products_repo.allpinds[pred_pid_id]
                pred_brand = products_repo.pname_to_brand[products_repo.pind_to_pname[pred_pid]]
                sentence.product_ids.append(pred_pid)
                sentence.product_brands.append(pred_brand)
                sentence.span_ranges.append(span_range)
                sentence.span_methods[span_range] = self.method_id    
                found = True
            
        return found

def test_articles():
    styleMe = ProductsRepo('./resources/StyleMe.csv')
    classifier_searcher = ClassifierMethod('models/randomforest_span.pkl')

    article_dir = '../../data/styleMe/article_filtered/part-00000'
    articles = load_articles(article_dir)
    for a in articles:
        for sent in a.sentences:
            found = classifier_searcher.extract_product(sent, a, styleMe)
            if found:
                print(sent.product_ids)
                print(sent.line_no, sent.content)
                for span in sent.span_ranges:
                    print(' '.join(sent.content_seg[pos] for pos in range(span[0], span[1]+1)))

def test_sentence():
    import jieba
    load_dictionary()

    style_repo = ProductsRepo('./resources/StyleMe.csv')
    headword_set = style_repo.get_head_termset()
    decription_set = style_repo.get_all_descriptive_termset()
    brands_ori = style_repo.get_all_brands()
    brand_set = set(brands_ori)
    for b in brands_ori:
        brand_set.update(style_repo.get_brand_alias(b))
    # sent = Sentence(-1, -1, 'BOURJOIS 妙巴黎] 舒芙蕾糖霜粉霧唇彩 是蜜糖還是毒藥？ #04#05兩色分享')
    sent = Sentence(-1, -1, '而giorgio armani家的極緞絲柔 粉底精華')
 
    # p='舒芙蕾粉霧糖霜唇彩'
    p= '極緞絲柔粉底精華'
    p_seg = jieba.lcut(p)

    brand = style_repo.pname_to_brand[p]
    brand_alias = ProductsRepo.get_brand_alias(brand)
    
    print(sent.content_seg)
    print(p_seg)
    print(brand_alias)

    spans = ClassifierMethod.search_span(sent, headword_set, decription_set, brand_set)
    print(spans)
    for span in spans:
        print(' '.join(sent.content_seg[pos] for pos in range(span[0], span[1]+1)))
        print(ClassifierMethod.get_features_with_product(sent, p_seg, brand_alias, span))

    #parse
    # print(parse_sentences(['天使惡魔羽透輕紗氣墊濾鏡遮瑕筆','臻雪丹御至善賦活精華','魅光星采粉', '挺濃翹U型防水睫毛膏']))
    # print(parse_sentences(['天使惡魔羽透輕紗氣墊濾鏡遮瑕筆'])) # 只有一句的時候 遮瑕  筆 會被斷開！？


if __name__ == '__main__':
    test_sentence()
    test_articles()