#! python3
# -*- coding:utf-8 -*-
# for error logging

from anytree.iterators import LevelOrderGroupIter

from ProductsRepoTree import ProductsRepoTree, StyleMe_Tree
from blog import Article, Sentence, load_articles

#-------------- for error logging -------------- 
import logging
logger = logging.getLogger('tree-method')
logger.setLevel(logging.INFO)
# logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - \n%(message)s')
ch.setFormatter(formatter)

# add the handlers to logger
logger.addHandler(ch)
#-------------- end for error logging -------------- 

class DecisionTreeMethod(object):
    """docstring for ClassName"""
    def __init__(self):
        # self.tree = tree
        pass

    def extract_product(self, sentence, article, products_data):
        found = False

        if len(sentence.content_seg) == 0: 
            return found

        for n in products_data.Tree.root.children:
            if n.name in sentence.content_seg:
                head_id = sentence.content_seg.index(n.name)
                start_id = head_id
                # print(products_tree.getAllChildrenName(n))
                cur_node = n
                #TODO: brand alias的比對？？
                #TODO: 找惹兩次？！
                # FIXED
                while sentence.content_seg[start_id - 1] in products_data.Tree.getAllChildrenName(cur_node):
                    node_idx = products_data.Tree.getAllChildrenName(cur_node).index(sentence.content_seg[start_id - 1])
                    # print('cur_word:', sentence.content_seg[start_id-1], cur_node, node_idx)
                    cur_node = cur_node.children[node_idx]
                    start_id -= 1
                    # print('new_cur_word:', sentence.content_seg[start_id - 1], cur_node, node_idx)
                    if start_id < 0: break

                if cur_node.is_leaf:
                    # exact match of brand
                    logger.debug('cur_node.is_leaf ' + cur_node.type)
                    logger.debug('start_id: {} end_id: {}'.format(start_id, head_id))
                    sentence.product_ids.append(cur_node.product_id)
                    sentence.span_ranges.append((start_id, head_id))
                    sentence.product_brands.append(cur_node.name)
                    sentence.span_methods[(start_id, head_id)] = 'a'
                    found = True

                if not found and 'brand' in products_data.Tree.getAllChildrenType(cur_node):
                    # need brand alias match
                    # some product has the same 中文品名 but with different brand
                    # e.g. (3367, shu uemura 植村秀, 指甲油), (5593, CHANEL 香奈兒, 指甲油), (8692, Smith & Cult, 指甲油), (16816, Dior 迪奧, 指甲油)
                    logger.debug('get product id: {} {}'.format(cur_node.children[0].product_id, cur_node.children[0].name))
                    logger.debug('start_id: {} end_id: {}'.format(start_id, head_id))
                    brand_alias = [(products_data.get_brand_alias(cur_node.children[idx].name), idx) for idx, t in enumerate(products_data.Tree.getAllChildrenType(cur_node)) if t == 'brand']
                    # brand_alias = products_data.get_brand_alias(cur_node.children[0].name)
                    found_brand = False
                    for brand in brand_alias:
                        for b in brand[0]:
                            if b in reversed([w.lower() for w in sentence.content_seg[:start_id]]):
                                found_brand = True
                                break
                        if found_brand:
                            sentence.product_ids.append(cur_node.children[brand[1]].product_id)
                            sentence.span_ranges.append((start_id, head_id))
                            sentence.product_brands.append(cur_node.children[brand[1]].name)
                            sentence.span_methods[(start_id, head_id)] = 'a'
                            found = True

                if not found and cur_node.type == 'headword':
                    # continue
                    # decision tree (1)
                    # if sentence.line_no == 54:  print('DT(1) cur_node:', cur_node)
                    '''make this sentence to parser! 
                    pattern: 這.*headword must be a NP of this sentence
                    '''
                    #TODO: 如果被斷成這款 這瓶..呢？？
                    # FIXED
                    possible_start_id =  [idx for idx, ele in enumerate(sentence.content_seg[:start_id]) if '這' in ele]
                    if len(possible_start_id)==0: return 0 # not found '這.* headword'
                    ''''''
                    start_id = possible_start_id[-1]
                    logger.debug('start_id: {} end_id: {}'.format(start_id, head_id))
                    if head_id-start_id > 3: return 0 # not found '這.* headword'
                    nearest_product_id = article.match_products[-1][-1] if not len(article.match_products)==0 else -1
                    nearest_brand = article.match_brands[-1][-1] if not len(article.match_brands)==0 else ''
                    if nearest_brand=='': return 0 # step(1), no product brand found in previous content
                    if nearest_product_id==-1: return 0 # step(2), no product id found in previous content
                    nearest_product_name = products_data.pind_to_pname[nearest_product_id]
                    if (products_data.pname_to_brand[nearest_product_name] == nearest_brand and cur_node.name in nearest_product_name):
                        # step(2)
                        sentence.product_ids.append(nearest_product_id)
                        sentence.span_ranges.append((start_id, head_id))
                        sentence.product_brands.append(nearest_brand)
                        sentence.span_methods[(start_id, head_id)] = 'b'
                        found = True

                if not found and cur_node.type == 'description':
                    # continue
                    # decision tree(2)
                    nearest_product_id = article.match_products[-1][-1] if not len(article.match_products) == 0 else -1
                    nearest_brand = article.match_brands[-1][-1] if not len(article.match_brands) == 0 else ''
                    if nearest_brand=='': return 0 # step(1), no product brand found in previous content
                    if nearest_product_id==-1: return 0 # step(2), no product id found in previous content
                    nearest_product_name = products_data.pind_to_pname[nearest_product_id]
                    if (products_data.pname_to_brand[nearest_product_name] == nearest_brand and n.name in nearest_product_name):
                        # step(2), nearest product id contains nearest brand and matched product head
                        logger.debug('step(2), nearest product id contains nearest brand and matched product head')
                        logger.debug('start_id: {} end_id: {}'.format(start_id, head_id))
                        sentence.product_ids.append(nearest_product_id)
                        sentence.span_ranges.append((start_id, head_id))
                        sentence.product_brands.append(nearest_brand)
                        sentence.span_methods[(start_id, head_id)] = 'c'
                        found = True
                
                    else:
                        # step(3)
                        #TODO: 好像怪怪的！？
                        product_candidates = products_data.productHead2product[n.name] # n: headword node
                        if len(product_candidates)>1: return 0 # (found brand + current matched words) is not a unique combination in the db
                        logger.debug(type(product_candidates))
                        logger.debug(' '.join(map(str,product_candidates)))
                        
                        des = ''.join(a.name for a in cur_node.ancestors if not a.is_root)
                        logger.debug('des '+des)
                        count = 0
                        for p in product_candidates:
                            pname = p[0]
                            logger.debug(type(p), p, '\n', pname)
                            if products_data.pname_to_brand[pname] == nearest_brand and des in p[0]:
                                count += 1
                        if count == 1:
                            sentence.product_ids.append(nearest_product_id)
                            sentence.span_ranges.append((start_id, head_id))
                            sentence.product_brands.append(nearest_brand)
                            sentence.span_methods[(start_id, head_id)] = 'c'
                            found = True
                            
        return found


def main():
    styleMe_data = ProductsRepoTree('./resources/StyleMe.csv')
    tree_searcher = DecisionTreeMethod()

    # article_dir = './resources/hackthon_makeup.json'
    article_dir = '../../data/styleMe/article_filtered/part-00000'
    articles = load_articles(article_dir)
    for a in articles:
        for sent in a.sentences:
            found = tree_searcher.extract_product(sent, a, styleMe_data)
            if found:
                print(sent.product_ids)
                print(sent.line_no, sent.content)
                for span in sent.span_ranges:
                    print(' '.join(sent.content_seg[pos] for pos in range(span[0], span[1]+1)))

if __name__ == '__main__':
    main()
    #TODO: 會容易抓到沒有描述詞的產品！！例如3361的化妝箱與3367的指甲油