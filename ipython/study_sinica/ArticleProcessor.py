#! python3
# -*- coding:utf-8 -*-

import os
import glob
import pickle
from DecisionTreeMethod import DecisionTreeMethod, load_articles
from ClassifierMethod import ClassifierMethod
from ProductsRepoTree import ProductsRepoTree


class ArticleProcessor(object):
    """extract products in articles"""
    def __init__(self, articles, product_repo):
        self.articles = articles
        self.product_repo = product_repo
        self.method_queue = []

    def add_method(self, method):
        self.method_queue.append(method)

    def process_all_articles(self):
        count = 0
        for a in self.articles:
            init = True
            # print('--{}_{}.txt'.format(a.author, a.aid))
            for sent in a.sentences:
                for method in self.method_queue:
                    found = method.extract_product(sent, a, self.product_repo)
                    if found:
                        if init:
                            print('--{}_{}.txt'.format(a.author, a.aid))
                            init = False
                            count += 1
                        sent.markSpan()
                        # print(str(method))
                        print(sent.label_content)
                        a.matched_sentence_id.append(sent.line_no)
                        a.match_products.append(sent.product_ids)
                        a.match_brands.append(sent.product_brands)
                        break # if found: not apply the next method
        print('#_all_article: {}, #_exact_match: {}'.format(len(self.articles), count))

    def write_results(self, output_dir):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for a in self.articles:
            output_path = os.path.join(output_dir, '{}_{}.txt'.format(a.author, a.aid))
            with open(output_path,'w',encoding='utf-8') as fout:
                for s in a.sentences:
                    if s.label_content:
                        fout.write(s.label_content)
                    else:
                        fout.write(s.content)
                    fout.write('\n')




            
def main():

    articles = []
    f_ws_all_article_pkl = './WSed_pickles/ws_all_article.pkl'
    if not os.path.exists(f_ws_all_article_pkl):
        path = '../../data/styleMe/article_filtered'
        filenamelist = sorted(glob.glob(os.path.join(path,'*')))
        # print(filenamelist)
        for idx, fileName in enumerate(filenamelist):
            article_dir = fileName
            articles += load_articles(article_dir, dump_articles=False, input_ws=True)
            # if idx==0: break
        pickle.dump(articles, open(f_ws_all_article_pkl, 'wb'))
    else:
        print('loading WSed pickle file')
        articles = pickle.load(open(f_ws_all_article_pkl, 'rb'))

    # exit()

    # article_dir = '../../data/styleMe/article_filtered/'
    # for 
    # articles = load_articles(article_dir)

    style_me = ProductsRepoTree('./resources/StyleMe.csv')

    tree_searcher = DecisionTreeMethod()
    # classifier_searcher = ClassifierMethod('models/randomforest_span2.pkl')

    processor = ArticleProcessor(articles, style_me)
    processor.add_method(tree_searcher)
    # processor.add_method(classifier_searcher)

    processor.process_all_articles()

    processor.write_results('resources/label_xml_exact_match')

if __name__ == '__main__':
    main()