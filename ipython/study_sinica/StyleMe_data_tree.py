#! python3
# -*- coding: utf-8 -*-

import csv
import re
import jieba

from anytree import Node, RenderTree, AsciiStyle, ContStyle


### load dictionary
def load_dictionary():
    cosmetic_dict_path = './dict.txt.big'
    jieba.set_dictionary(cosmetic_dict_path)


    with open('./resources/cosmetic_headwords.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        pheads = [l.strip() for l in lines]
    for hw in pheads:
        jieba.add_word(hw)
    jieba.suggest_freq('乳液', True)

    with open('./resources/brands_in_chinese.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        brands = [l.strip() for l in lines]
    for b in brands:
        jieba.add_word(b)

def check_contain_chinese(check_str):
    for ch in check_str:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False

class StyleMe_data():
    def __init__(self, file):
        self.column_dict = {'ID':'編號', 'brand':'品牌', 'zh_series_name':'系列中文名稱', 'en_series_name':'系列英文名稱', 'zh_product_name':'中文品名', 'en_product_name':'英文品名', 'zh_intro':'中文簡介', 'en_intro':'英文簡介', 'usage':'用途', 'items':'品項', 'effect':'功效', 'date':'上市日期', 'spec':'規格', 'sell_country':'販售國家', 'unsold_country':'停產國家', 'limit_edition':'是否限量', 'product_alias':'產品別名', 'built_date':'建立時間', 'edit_date':'修改時間', 'article_num':'精選文章數'}
        self.brand = {} # filter by brand (key: brand; value: list of product)
        self.product_name = {} # filter by chinese product name (zh_product_name) (key: product name; value: list of product)
        self.sort_by_product_head = {} # filter by product headword (key: product headword; value: list of product)

        self.product_headword = self.load_product_headword()
        self.load_style_me_data(file)
        self.brand_alias_dict = self.get_all_brand_alias()


    def load_style_me_data(self, file):
        with open(file, 'r', encoding='utf-8') as fin:
            last_brand = ''
            tmp = 0
            for row in csv.DictReader(fin):
                self.classification(self.column_dict['brand'], row)
                self.classification(self.column_dict['zh_product_name'], row)
                self.classification('p_headword', row)

    def classification(self, col, data):
        ''' This is a function to classify the products in database by 品牌 and 中文品名 relatively
    
        :param col: 品牌 or 中文品名 or p_headword
        :param data: single product to be classified 
        '''
        valid_col = False
        if col == '品牌':
            if data[self.column_dict['brand']] == '': return
            class_ = self.brand
            valid_col = True
        elif col == '中文品名':
            if len(data[self.column_dict['zh_product_name']]) == 0: return
            class_ = self.product_name
            valid_col = True
        elif col == 'p_headword':
            if len(data[self.column_dict['zh_product_name']])==0: return
            class_ = self.sort_by_product_head

            product = self.remove_special_char(data[self.column_dict['zh_product_name']])
            h_pattern = r'|'.join(h for h in self.product_headword)
            series_pattern = re.compile(r'.+(款|型|版|代|色)|含.+|.*UV.*|\d+.*')
            matched_product_heads = re.findall(h_pattern, product)
            got_sure_head = False
            new_ordered_product = []

            ### special case
            ### '可愛動物面膜' / '福神面膜'
            spe_mask = re.compile(r'可愛動物面膜|福神面膜')
            if spe_mask.search(product):
                got_sure_head = True
                found_head = '面膜'
                start_index = product.find(found_head)
                new_ordered_product = [product[start_index+len(found_head):], product[:start_index+len(found_head)]]

            ### headword search
            if len(matched_product_heads)>0:
                found_head = matched_product_heads[-1]
                start_index = product.find(found_head)
                if product[start_index:]==found_head:
                    ### headword is the last word of the product
                    new_ordered_product = [product]
                    got_sure_head = True
                else:
                    if series_pattern.search(product[start_index+len(found_head):]) or \
                        product[start_index+len(found_head)]==' ' or \
                        not check_contain_chinese(product[start_index+len(found_head):]):
                        ### product as the following pattern:
                        ### product 產品系列, e.g. 植物精萃潔顏油 綠茶版
                        ### re-order the product to make headword the last word, i.e. re-order 植物精萃潔顏油 綠茶版 to 綠茶版 植物精萃潔顏油
                        new_ordered_product = [product[start_index+len(found_head):].strip(), product[:start_index+len(found_head)].strip()]
                        got_sure_head = True

            if got_sure_head is False:
                ### products do not follow the pattern above
                ### split product with space, determine which part contains any headword
                ### e.g. 寶可夢保濕乳霜 可達鴨(起司緊膚)
                ### i.e. re-order ['寶可夢保濕乳霜', '可達鴨', '起司緊膚'] to ['可達鴨', '起司緊膚', '寶可夢保濕乳霜']
                p_seg = re.split(r'\s+', product)
                found_head_idx = -1

                for idx, p in enumerate(p_seg):
                    seg_list = jieba.lcut(p)
                    seg_list = [t for t in seg_list if not t.isspace()]
                    head_mark = self.contain_headword(seg_list)
                    if len(head_mark)>0:
                        # print(idx, seg_list, head_mark)
                        found_head_idx = idx
                if found_head_idx==len(p_seg)-1:
                    # headword is at last segmented part
                    new_ordered_product = p_seg
                else:
                    new_ordered_product = p_seg[found_head_idx+1:]+p_seg[:found_head_idx+1]

            seg_list = jieba.lcut(' '.join(p.strip() for p in new_ordered_product))
            seg_list = [t for t in seg_list if not t.isspace()]

            ### make sure headword is Chinese
            i = -1
            while not check_contain_chinese(seg_list[i]) and (re.search(r'\W+', seg_list[i]) or seg_list[i].isalnum()) and (i+len(seg_list)>0): i-=1
            if (i+len(seg_list))==0: i=-1 # if product contains only English, then make the last word as product headword
            product_head = seg_list[i] # assign product headword

            if product_head in class_:
                class_[product_head].append((data, seg_list))
            else:
                class_[product_head] = [(data, seg_list)]

        if valid_col == True:
            if data[col] in class_:
                class_[data[col]].append(data)
            else:
                class_[data[col]] = [data]

    def get_all_brand_alias(self):
        b_alias_dict = {}
        for b in self.brand.keys():
            b_ = b
            parathesis = re.compile(r'\(.+\)')
            parathesis.sub('', b_)
            b_alias = b_.split(' ')
            whole_product = self.brand[b]
            for p in whole_product:
                p_name = p[self.column_dict['zh_product_name']]
                p_name_alias = p[self.column_dict['product_alias']].split(',')
                for p_a in p_name_alias:
                    if p_name in p_a:
                        a_ = p_a.replace(p_name, '').strip()
                        a_ = a_.split(' ')[0] # exclude post-description
                        if len(a_) > 0 and not a_ in b_alias:
                            b_alias.append(a_)
            b_alias_dict[b] = b_alias
        return b_alias_dict


    def load_product_headword(self):
        product_head = []
        with open('./resources/cosmetic_headwords.txt', 'r', encoding='utf-8') as fin:
            for line in fin:
                if line.strip() in product_head: continue
                product_head.append(line.strip())
        product_head.sort(key=lambda x: len(x), reverse=True)
        return product_head

    def remove_special_char(self, product):
        product = product
        product = re.sub(r'SPF\s?\d+\+?[\/\s\.／]*PA[\s]*\+*', '', product, re.IGNORECASE)
        product = re.sub(r'(SPF|spf)\s*\d+\+?', '', product, re.IGNORECASE)
        product = re.sub(r'PA\++', '', product, re.IGNORECASE)
        product = re.sub(r'\W+', ' ', product)
        product = product.strip()

        return product

    def contain_headword(self, list):
        mark = []
        for head in self.product_headword:
            if head in list:
                mark.append((head, list.index(head)))

        return mark

    def build_tree(self):
        print('start building tree---')
        # print('head_num', len(self.sort_by_product_head))
        # print(self.sort_by_product_head.keys())

        root = StyleMe_Node('root', 'StyleMe')
        # root = Node('StyleMe')

        for k in self.sort_by_product_head.keys():
            # node = Node(k, parent=root)
            node = StyleMe_Node('headword', k, parent=root)
            for item in self.sort_by_product_head[k]:
                # print('\n', item[1])
                last = node
                current = node
                next = node
                same_node_name = False
                for idx, s in enumerate(reversed(item[1])):
                    # print('current:', s)
                    same_node_name = False
                    if idx==0:
                        last = node
                        current = node
                        next = node
                        continue
                    # n = Node(s)
                    if not current==node and not same_node_name:
                        # n = Node(s, parent=current)
                        n = StyleMe_Node('description', s, parent=current)
                        current = n
                        continue
                    for t_n in last.children:
                        # print('t_n.name', t_n.name, 'current:', s)
                        if not t_n.name == s:
                            next = t_n.parent
                            same_node_name = False
                            if t_n.is_leaf:
                                next = last
                                # break
                        if t_n.name == s:
                            last = t_n
                            same_node_name = True
                            break
                    if not same_node_name:
                        if next.name==s:
                            current = next
                            continue
                        # n = Node(s, parent=next)
                        n = StyleMe_Node('description', s, parent=next)
                        current = n
                    else:
                        continue
                # n = Node(item[0][self.column_dict['brand']], parent=current)
                n = StyleMe_Node('brand', item[0][self.column_dict['brand']], parent=current, product_id=item[0][self.column_dict['ID']])

        tree = RenderTree(root, style=AsciiStyle)
        # print(tree)
        # for pre, fill, node in tree:
        #     print('%s%s' % (pre, node.name))
        return tree

class StyleMe_Node(Node):
    def __init__(self, type, string, parent=None, product_id=-1):
        '''
        :param type: headword, description or brand 
        :param string: exact string, e.g. 護手霜, 迪奧, etc.
        :param parent: parent node
        :param product_id: product id, only exists in brand node
        '''
        super().__init__(string, parent=parent)
        self. type = type
        self.product_id = product_id


def main():
    load_dictionary()

    styleMe_file = './resources/StyleMe.csv'
    styleMe_data = StyleMe_data(styleMe_file)
    styleMe_tree = styleMe_data.build_tree()
    print('--finish building tree--')
    print(styleMe_tree)

if __name__=='__main__':
    main()
