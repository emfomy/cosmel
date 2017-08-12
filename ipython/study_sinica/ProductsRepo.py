#! python3
# -*- coding:utf-8 -*-

import csv
import re
import jieba

##word segmentation package
jieba.set_dictionary('dict.txt.big')    
    
with open('resources/cosmetic_headwords.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    pheads = [l.strip() for l in lines]
for hw in pheads:
    jieba.add_word(hw)
    
#check if a string contains chinese characters
def check_contain_chinese(check_str):
    for ch in check_str:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False
    
class ProductsRepo():
    def __init__(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            p_repo = []
            for row in csv.DictReader(f):
                item = {}
                item['編號'] = row['編號']
                item['中文品名'] = row['中文品名']
#                 item['產品別名'] = row['產品別名']
                item['品牌'] = row['品牌']
#                 item['英文品名'] = row['英文品名']
                p_repo.append(item)
        
        self.allproducts = []
        self.allpinds = []
        self.pname_to_pind = {}
        self.pind_to_pname = {}
        self.pname_to_brand = {}

        for item in p_repo:
            name = item['中文品名']
            ind = item['編號']
            brand = item['品牌']

            name = self.remove_special_char_in_product(name)
            if len(name) <1:
                continue 
            self.allproducts.append(name)
            self.allpinds.append(ind)
            self.pname_to_pind[name] = ind
            self.pind_to_pname[ind] = name
            self.pname_to_brand[name] = brand
            
        self.allproducts_seg = []
        self.pind_to_pname_seg = {}
        for p in self.allproducts:
            pseg = jieba.lcut(p) 
            self.allproducts_seg.append(pseg)
            ind = self.pname_to_pind[p]
            self.pind_to_pname_seg[ind] = pseg
        
    @staticmethod
    def remove_special_char_in_product(product):
        product = re.sub(r'SPF\s?\d+\+?[\/\s\.]PA\+*', '', product, re.IGNORECASE)
        product = re.sub(r'SPF\d+\+?', '', product, re.IGNORECASE)
        product = re.sub(r'\W', '', product)
        product = re.split(r'\(|（', product)[0]

        return product
    
    @staticmethod
    def get_brand_alias(brand):
        alias = set()
        eng=''
        chi=''
        for ele in brand.split(' '):
            if not ele:
                continue
            if check_contain_chinese(ele):
                chi+=ele
            else:
                eng = eng + ' ' + ele

        eng = eng.lower().strip()
        chi =chi.split('（')[0].strip() #資生堂（東京櫃）
        alias.add(eng)
        alias.add(chi)
        alias.add(eng.replace( "\'","").replace( "-","" ).replace( ".", "" ) )
        alias.add(eng.replace( "-"," " ))
        alias.add(eng.replace(".",  " " ))
        alias = list(alias)
        try:
            alias.remove('')
        except ValueError:
            pass 
        return alias
    
    def get_all_brands(self):
        brands_lst = list(set( [b.lower() for b in self.pname_to_brand.values()] ))
        try:
            brands_lst.remove('')
        except ValueError:
            pass
        return brands_lst
        
    def get_all_brands_chinese(self):
        b_set = set()
        for b in self.get_all_brands():
            aliases = self.get_brand_alias(b)
            for a in aliases:
                if check_contain_chinese(a):
                    b_set.add(a)
        return b_set
#         for b in self.get_all_brands() :
#             b = b.strip().split('（')[0]
#             b_chi = re.sub('\W','', b)
#             b_chi = re.sub(r'[a-zA-Z]','',b_chi)
#             if  len(b_chi) > 0:
#                 b_set.add(b_chi)

if __name__ == '__main__':
    style_repo = ProductsRepo('resources//StyleMe.csv')
    print(style_repo.allproducts[:10])
    print(style_repo.allproducts_seg[:10])
    print(style_repo.get_brand_alias('L\'OREAL PARIS 巴黎萊雅'))
    