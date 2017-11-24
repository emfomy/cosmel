#! python3
# -*- coding: utf-8 -*-
import re
# import jieba
from IPython import embed
from ProductsRepo import *
from anytree import Node, RenderTree, AsciiStyle, ContStyle

#-------------- for error logging -------------- 
import logging
logger = logging.getLogger('build-tree')
# logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
# ch.setLevel(logging.DEBUG)
ch.setLevel(logging.INFO)

# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(message)s')
ch.setFormatter(formatter)

# add the handlers to logger
logger.addHandler(ch)

# load_dictionary()

class ProductsRepoTree(ProductsRepo):
    def __init__(self, file_path):
        super().__init__(file_path)
        
        self.predifined_headword = load_predifined_headword(sort=True)
        
        ## key: headword, value: product
        self.productHead2product = {}
        ## key: product, value: product series
        ##      (e.g '福神面膜-戀愛狐仙(茶花香)', '福神面膜開運達摩（茶花香）', '福神面膜除厄招福（茶花香）'')
        ##      (k:v)=('福神面膜':['戀愛狐仙(茶花香)', '開運達摩（茶花香）', '除厄招福（茶花香）'])
        self.product2series = {}
        # save product2series as pickle
        f_product2series_pkl = './WSed_pickles/product2series.pkl'
        if not os.path.exists(f_product2series_pkl):
            for product in self.allproducts:
                if product=='111': continue
                valid, new_produtct = self.rephrase_product(product.strip())
                logger.debug('{}, current product:{}, new_produtct:{}'.format(valid, product.strip(), new_produtct))
                if valid:
                    ### make sure headword is Chinese
                    i = -1
                    while not check_contain_chinese(new_produtct[i]) and (re.search(r'\W+', new_produtct[i]) or new_produtct[i].isalnum()) and (i+len(new_produtct)>0):
                        i -= 1
                    if (i+len(new_produtct))==0: 
                        i = -1 # if product contains only English, then make the last word as product headword
                    product_head = new_produtct[-1] # assign product headword
                    print(product_head)
                    if product_head in self.productHead2product:
                       self.productHead2product[product_head].append((product, new_produtct))
                    else:
                        self.productHead2product[product_head] = [(product, new_produtct)] 
                # print(self.product2series)
                # pickle.dump(self.product2series, open(f_product2series_pkl, 'wb'))
        else:
            print('loading WSed pickle file: product2series.pkl')
            self.product2series = pickle.load(open(f_product2series_pkl, 'rb'))

        

            ### make sure headword is Chinese
            # i = -1
            # while not check_contain_chinese(new_produtct[i]) and (re.search(r'\W+', new_produtct[i]) or new_produtct[i].isalnum()) and (i+len(new_produtct)>0): 
            #     i-=1
            # if (i+len(new_produtct))==0: 
            #     i=-1 # if product contains only English, then make the last word as product headword
            # product_head = new_produtct[i] # assign product headword

            # if product_head in self.productHead2product:
            #     self.productHead2product[product_head].append( (product, new_produtct)) #(product index, segment list of rephrased product name)
            # else:
            #     self.productHead2product[product_head] = [(product, new_produtct)]  

        # build tree via product headwords
        self.Tree = self.build_tree()
        print('#: {}, headwords:{}'.format(len(self.productHead2product.keys()), self.productHead2product.keys()))
        # print('headwords:{}'.format(self.Tree.root.children))
        
        
    def check_has_product_series(self, product):
        series_pattern = re.compile(r'.+(款|型|形|版|代|色|系列)$|#\d+.*')
        if series_pattern.search(product):
            return True
        return False
        

    def rephrase_product(self, product):
        '''
            :param product: product name to be rephrased
            :return: (Bool, List)
                    valid main_product name
                    main product name after word segmentation (type: list)
        '''
        
        # seg_list = seg(product)
        h_pattern = r'|'.join(h for h in self.predifined_headword)
        if self.check_has_product_series(product):
            main_product = ''
            series = ''
            if ' ' in product:
                for idx, p in enumerate(product.split(' ')):
                    # print(idx, p)
                    if len(re.findall(h_pattern, p))>0 and not self.check_has_product_series(p):
                        main_product = ' '.join(s for s in product.split(' ')[:idx+1])
                        series = ' '.join(s for s in product.split(' ')[idx+1:])
                        logger.debug('(1.1) main_product: {} series: {}'.format(main_product, series))
                        # print('got head(?)', main_product, series)
                if main_product=='' or series=='':
                    for idx, p in enumerate(product.split(' ')):
                        # N 5香水低調奢華版
                        # N 5典藏香水
                        matched_product_heads = re.findall(h_pattern, p)
                        if len(matched_product_heads)>0:
                            found_head = matched_product_heads[0]
                            head_index = product.index(found_head)
                            main_product = product[:head_index+len(found_head)]
                            series = product[head_index+len(found_head):]
                            # main_product = ' '.join(s for s in product.split(' ')[:idx+1])
                            # series = ' '.join(s for s in product.split(' ')[idx+1:])
                            logger.debug('(1.2) main_product: {} series: {}'.format(main_product, series))
                    
                if main_product=='' or series=='':
                    for idx, p in enumerate(product.split(' ')):
                        # 未收詞headword導致可能判斷不出來head
                        # 取series前當主要產品名稱
                        if not self.check_has_product_series(p):
                            main_product = ' '.join(s for s in product.split(' ')[:idx+1])
                            series = ' '.join(s for s in product.split(' ')[idx+1:])
                            logger.debug('(1.3) main_product: {} series: {}'.format(main_product, series))
                    
                if main_product=='' or series=='':
                    matched_product_heads = re.findall(h_pattern, product)
                    if len(matched_product_heads)>0:
                        found_head = matched_product_heads[0]
                        head_index = product.index(found_head)
                        main_product = product[:head_index+len(found_head)]
                        series = product[head_index+len(found_head):]
                        logger.debug('(1.4) main_product: {} series: {}'.format(main_product, series))
                        
            else:
                # find headword
                matched_product_heads = re.findall(h_pattern, product)
                if len(matched_product_heads)>0:
                    found_head = matched_product_heads[0]
                    head_index = product.index(found_head)
                    main_product = product[:head_index+len(found_head)]
                    series = product[head_index+len(found_head):]
                    logger.debug('(2.1) main_product: {} series: {}'.format(main_product, series))
                if main_product=='' or series=='':
                    # 未收詞headword導致可能判斷不出來head
                    # 取series前（含）三個字當系列名稱
                    matched_series = re.findall(r'.+(款|型|形|版|代|色|系列)$|#\d+.*', product)
                    series_index = product.index(matched_series[-1])
                    main_product = product[:series_index-2]
                    series = product[series_index-2:]
                    logger.debug('(2.2) main_product: {} series: {}'.format(main_product, series))
                

            logger.debug('product: {}, main_product: {}, series: {}'.format(product, main_product, series))
            return self.add_product2series(main_product, series, product)
            # if main_product in self.product2series:
            #     self.product2series[main_product].append(seg(series))
            #     return False, seg(main_product)
            # else:
            #     self.product2series[main_product] = [seg(series)]

        else:
            if ' ' in product:
                matched_product_heads = re.findall(h_pattern, product)
                if len(matched_product_heads)>0:
                    found_head = matched_product_heads[0]
                    head_index = product.index(found_head)
                    # logger.debug('product: {}, found_head: {}, head_index: {}'.format(product, found_head, head_index))
                    if head_index+len(found_head)==len(product):
                        return self.add_product2series(product, '')
                    if product[head_index+len(found_head)]==' ':
                        main_product = product[:head_index+len(found_head)].strip()
                        series = product[head_index+len(found_head):].strip()
                        logger.debug('(3) main_product: {} series: {}'.format(main_product, series))
                        logger.debug('product: {}, main_product: {}, series: {}'.format(product, main_product, series))
                        return self.add_product2series(main_product, series, product)
                    
            return self.add_product2series(product, '', product)

        ###############
        ### OLD CODE
        # h_pattern = r'|'.join(h for h in self.predifined_headword)
        # series_pattern = re.compile(r'.+(款|型|形|版|代|色|系列)$|含.+|.*UV.*|\d+.*')
        # matched_product_heads = re.findall(h_pattern, product)
        # got_sure_head = False
        # new_ordered_product = []

        # ### special case
        # ### '可愛動物面膜' / '福神面膜'
        # spe_mask = re.compile(r'可愛動物面膜|福神面膜')
        # if spe_mask.search(product):
        #     got_sure_head = True
        #     found_head = '面膜'
        #     start_index = product.find(found_head)
        #     new_ordered_product = [product[start_index+len(found_head):], product[:start_index+len(found_head)]]

        # ### headword search
        # if len(matched_product_heads)>0:
        #     found_head = matched_product_heads[-1]
        #     start_index = product.find(found_head)
        #     if product[start_index:]==found_head:
        #         ### headword is the last word of the product
        #         new_ordered_product = [product]
        #         got_sure_head = True
        #     else:
        #         if series_pattern.search(product[start_index+len(found_head):]) or \
        #             product[start_index+len(found_head)]==' ' or \
        #             not check_contain_chinese(product[start_index+len(found_head):]):
        #             ### product as the following pattern:
        #             ### product 產品系列, e.g. 植物精萃潔顏油 綠茶版
        #             ### re-order the product to make headword the last word, i.e. re-order 植物精萃潔顏油 綠茶版 to 綠茶版 植物精萃潔顏油
        #             new_ordered_product = [product[start_index+len(found_head):].strip(), product[:start_index+len(found_head)].strip()]
        #             got_sure_head = True

        # if got_sure_head is False:
        #     ### products do not follow the pattern above
        #     ### split product with space, determine which part contains any headword
        #     ### e.g. 寶可夢保濕乳霜 可達鴨(起司緊膚)
        #     ### i.e. re-order ['寶可夢保濕乳霜', '可達鴨', '起司緊膚'] to ['可達鴨', '起司緊膚', '寶可夢保濕乳霜']
        #     p_seg = re.split(r'\s+', product)
        #     found_head_idx = -1

        #     for idx, p in enumerate(p_seg):
        #         # seg_list = jieba.lcut(p)
        #         seg_list = seg(p)
        #         seg_list = [t for t in seg_list if not t[0].isspace()]
        #         head_mark = self.contain_headword(seg_list)
        #         if len(head_mark)>0:
        #             # print(idx, seg_list, head_mark)
        #             found_head_idx = idx
        #     if found_head_idx==len(p_seg)-1:
        #         # headword is at last segmented part
        #         new_ordered_product = p_seg
        #     else:
        #         new_ordered_product = p_seg[found_head_idx+1:]+p_seg[:found_head_idx+1]

        # # seg_list = jieba.lcut(' '.join(p.strip() for p in new_ordered_product))
        # seg_list = seg(' '.join(p.strip() for p in new_ordered_product))
        # seg_list = [t for t in seg_list if not t[0].isspace()]

        # return seg_list

    def add_product2series(self, main_product, series, product):
        pid = self.pname_to_pind[product]
        product_seg = self.pind_to_pname_seg[pid]
        last_word = main_product[-1]
        main_product_idx = 0
        for idx, p in enumerate(product_seg):
            if last_word in p:
                main_product_idx = idx
        # wordseg = PyWordSeg()
        # (oL, uwL) = wordseg.ApplyList(['text_to_be_ws'])
        seg_main_list = product_seg[:main_product_idx+1]
        logger.debug('origin:{}, seg:{}'.format(main_product, seg_main_list))
        if series == '':
            return True, seg_main_list    
        seg_serires_list = product_seg[main_product_idx+1:]
        embed()
        logger.debug('[seg] main_product:{}, series:{}'.format(seg_main_list, seg_serires_list))
        if main_product in self.product2series:
            self.product2series[main_product].append(seg_serires_list)
            return False, seg_main_list
        else:
            self.product2series[main_product] = [seg_serires_list]
            return True, seg_main_list

    def contain_headword(self,  term_lst):
        mark = []
        for head in self.predifined_headword:
            if head in term_lst:
                mark.append((head, term_lst.index(head)))

        return mark

    def build_tree(self):
        print('start building tree---')
        # print('head_num', len(self.sort_by_product_head))
        # print(self.sort_by_product_head.keys())

        root = StyleMe_Node('root', 'StyleMe')
        # root = Node('StyleMe')

        for k in self.productHead2product:
            # node = Node(k, parent=root)
            node = StyleMe_Node('headword', k, parent=root)
            for item in self.productHead2product[k]:
                # print('\n', item[1])
                last = node
                current = node
                next = node
                same_node_name = False
                for idx, s in enumerate(reversed(item[1])):
                    # print('current:', s[0])
                    same_node_name = False
                    if idx==0:
                        last = node
                        current = node
                        next = node
                        continue
                    # n = Node(s)
                    if not current==node and not same_node_name:
                        # n = Node(s, parent=current)
                        n = StyleMe_Node('description', s[0], parent=current)
                        current = n
                        continue
                    for t_n in last.children:
                        # print('t_n.name', t_n.name, 'current:', s)
                        if not t_n.name == s[0]:
                            next = t_n.parent
                            same_node_name = False
                            if t_n.is_leaf:
                                next = last
                                # break
                        if t_n.name == s[0]:
                            last = t_n
                            same_node_name = True
                            break
                    if not same_node_name:
                        if next.name==s[0]:
                            current = next
                            continue
                        # n = Node(s, parent=next)
                        n = StyleMe_Node('description', s[0], parent=next)
                        current = n
                    else:
                        continue
                # n = Node(item[0][self.column_dict['brand']], parent=current)
                brand = self.pname_to_brand[item[0]]
                p_id = self.pname_to_pind[item[0]]
                n = StyleMe_Node('brand', brand, parent=current, product_id=p_id)

        # tree = RenderTree(root, style=AsciiStyle)
        tree = StyleMe_Tree(root)
        
        print('--finish building tree--')
        # print(tree)
        # for pre, fill, node in tree:
        #     print('%s%s' % (pre, node.name))
        return tree


class StyleMe_Tree(RenderTree):
    def __init__(self, root, style=AsciiStyle):
        super().__init__(root, style=style)
        self.root = root

    def getAllChildrenName(self, node):
        children = []
        for c in node.children:
            children.append(c.name)
        return children

    def getAllChildrenType(self, node):
        type_ = []
        for c in node.children:
            type_.append(c.type)
        return type_

class StyleMe_Node(Node):
    def __init__(self, type, string, parent=None, product_id=-1):
        '''
        :param type: headword, description or brand 
        :param string: exact string, e.g. 護手霜, 迪奧, etc.
        :param parent: parent node
        :param product_id: product id, only exists in brand node
        '''
        super().__init__(string, parent=parent)
        self.type = type
        self.product_id = product_id



def main():
    styleMe_file = './resources/StyleMe.csv'
    styleMe_data = ProductsRepoTree(styleMe_file)

    # styleMe_file = './resources/StyleMe.json'
    # styleMe_data = StyleMe_data(styleMe_file, file_extension='json')
    # styleMe_tree = styleMe_data.build_tree()
    print(styleMe_data.Tree)

if __name__=='__main__':
    main()
