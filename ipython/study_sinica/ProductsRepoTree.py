#! python3
# -*- coding: utf-8 -*-
import re
import jieba
from ProductsRepo import *
from anytree import Node, RenderTree, AsciiStyle, ContStyle

load_dictionary()

class ProductsRepoTree(ProductsRepo):
    def __init__(self, file_path):
        super().__init__(file_path)
        
        self.predifined_headword = load_predifined_headword(sort=True)

        ##key: headword, value: product
        self.productHead2product = {}
        for product in self.allproducts:
            new_produtct = self.rephrase_product(product)

            ### make sure headword is Chinese
            i = -1
            while not check_contain_chinese(new_produtct[i]) and (re.search(r'\W+', new_produtct[i]) or new_produtct[i].isalnum()) and (i+len(new_produtct)>0): 
                i-=1
            if (i+len(new_produtct))==0: 
                i=-1 # if product contains only English, then make the last word as product headword
            product_head = new_produtct[i] # assign product headword

            if product_head in self.productHead2product:
                self.productHead2product[product_head].append( (product, new_produtct)) #(product index, segment list of rephrased product name)
            else:
                self.productHead2product[product_head] = [(product, new_produtct)]  

        self.Tree = self.build_tree()

    def rephrase_product(self, product):
        h_pattern = r'|'.join(h for h in self.predifined_headword)
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

        return seg_list

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
