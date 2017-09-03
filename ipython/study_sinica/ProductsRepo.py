#! python3
# -*- coding:utf-8 -*-

import csv
import re
import jieba
import os

def load_predifined_headword(path = './resources/cosmetic_headwords.txt', sort=False):
    product_head = []
    with open(path, 'r', encoding='utf-8') as fin:
        for line in fin:
            if line.strip() in product_head: continue
            product_head.append(line.strip())
    if sort:
        product_head.sort(key=lambda x: len(x), reverse=True)
    return product_head

##word segmentation package
def load_dictionary():
    jieba.set_dictionary('dict.txt.big')    
        
    pheads = load_predifined_headword('./resources/cosmetic_headwords.txt')
    for hw in pheads:
        jieba.add_word(hw)

    # jieba.suggest_freq('乳液', True)

    with open('./resources/brands_in_chinese.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        brands = [l.strip() for l in lines]
        for b in brands:
            jieba.add_word(b)
load_dictionary()

#check if a string contains chinese characters
def check_contain_chinese(check_str):
    for ch in check_str:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False
    
class ProductsRepo():
    def __init__(self, file_path):
        filename, file_extension = os.path.splitext(file_path)
        if file_extension == '.csv':
            p_repo = self.load_from_csv(file_path)
        elif file_extension =='.json':
            p_repo = self.load_from_json(file_path)
       
        self.allproducts = []
        self.allproducts_origin = []
        self.allpinds = []
        self.pname_to_pind = {}
        self.pind_to_pname = {}
        self.pname_to_brand = {}
        self.bind_to_brand = {}
        self.brand_to_bind = {}

        for item in p_repo:
            origin_name = item['zh_product_name']
            ind = item['ID']
            brand = item['brand']

            name = self.remove_special_char_in_product(origin_name)
            if len(name) <1:
                continue 
            self.allproducts_origin.append(origin_name)
            self.allproducts.append(name)
            self.allpinds.append(ind)
            self.pname_to_pind[name] = ind
            self.pind_to_pname[ind] = name
            self.pname_to_brand[name] = brand
        
        brands_set = set( [b.lower() for b in self.pname_to_brand.values()])
        try:
            brands_set.remove('')
        except ValueError:
            pass  
        for i, b in enumerate(brands_set):
            self.bind_to_brand[i] = b
            self.brand_to_bind[b]=i
        
        self.allproducts_seg = []
        self.pind_to_pname_seg = {}
        for p in self.allproducts:
            pseg = jieba.lcut(p) 
            self.allproducts_seg.append(pseg)
            ind = self.pname_to_pind[p]
            self.pind_to_pname_seg[ind] = pseg
    
    def load_from_csv(self, file_path):
        column_dict = {'產品別名':'product_alias','精選文章數':'article_num','系列英文名稱':'en_series_name',
        '系列中文名稱':'zh_series_name','建立時間':'built_date','中文簡介':'zh_intro','品牌':'brand','功效':'effect','規格':'spec',
        '修改時間':'edit_date','上市日期':'date','英文品名':'en_product_name','販售國家':'sell_country','英文簡介':'en_intro',
        '品項':'items','用途':'usage','停產國家':'unsold_country','是否限量':'limit_edition','編號':'ID','中文品名':'zh_product_name'}

        with open(file_path, 'r', encoding='utf-8') as f:
            p_repo = []
            for row in csv.DictReader(f):
                item = {}
                if len(row['中文品名']) == 0 or '測試' in row['中文品名'] or  '測試' in  row['品牌']:
                    continue
                item[column_dict['編號']] = row['編號']
                item[column_dict['中文品名']] = row['中文品名']
                item[column_dict['產品別名']] = row['產品別名']
                item[column_dict['品牌']] = row['品牌']
                p_repo.append(item)
            return p_repo

    def load_from_json(self, file_path):
        #TODO: redefine by data
        column_dict = {'產品別名':'product_alias','精選文章數':'article_num','系列英文名稱':'en_series_name',
        '系列中文名稱':'zh_series_name','建立時間':'built_date','中文簡介':'zh_intro','品牌':'brand','功效':'effect','規格':'spec',
        '修改時間':'edit_date','上市日期':'date','英文品名':'en_product_name','販售國家':'sell_country','英文簡介':'en_intro',
        '品項':'items','用途':'usage','停產國家':'unsold_country','是否限量':'limit_edition','編號':'ID','中文品名':'zh_product_name'}

        with open(file_path,'r',encoding='utf-8') as fin:
            json_data = json.load(fin)
            p_repo = []
            for row in json_data:
                item = {}
                item[column_dict['編號']] = row['編號']
                item[column_dict['中文品名']] = row['中文品名']
                item[column_dict['產品別名']] = row['產品別名']
                item[column_dict['品牌']] = row['品牌']
                p_repo.append(item)
            return p_repo

    def get_all_descriptive_termset(self):
        # from collections import Counter
        # desc_set = Counter()
        desc_set = set()
        for p_seg in self.allproducts_seg:
            desc_set.update(p_seg[:-1])
        if '的' in desc_set:
            desc_set.remove('的')
        return desc_set
    
    def get_head_termset(self):
        hws = set()
        for p_seg in self.allproducts_seg:
            hw = p_seg[-1]
            if check_contain_chinese(hw):
                hws.add(p_seg[-1])
        return hws

    @staticmethod
    def remove_special_char_in_product(product):
        # product = re.sub(r'SPF\s?\d+\+?[\/\s\.]PA\+*', '', product, re.IGNORECASE)
        # product = re.sub(r'SPF\d+\+?', '', product, re.IGNORECASE)
        # product = re.sub(r'\W', '', product)
        product = re.sub(r'SPF\s?\d+\+?[\/\s\.／]*PA[\s]*\+*', '', product, re.IGNORECASE)
        product = re.sub(r'SPF\s*\d+\+?', '', product, re.IGNORECASE)
        product = re.sub(r'PA\++', '', product, re.IGNORECASE)
        product = re.sub(r'\W', ' ', product)
        product = re.split(r'\(|（', product)[0]

        return product
    
    @staticmethod
    def get_brand_alias(brand):
        #TODO: 要斷開嗎?
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
        return list(self.bind_to_brand.values())
        
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

    # def get_brand_alias_mapping(self):
    #     brand_to_alias = {}
    #     for b in self.get_all_brands():
    #         b_ = b
    #         parathesis = re.compile(r'\(.+\)')
    #         parathesis.sub('', b_)
    #         b_alias = b_.split(' ')
    #         whole_product = self.brand2product[b]
    #         for p in whole_product:
    #             p_name = p[self.column_dict['zh_product_name']]
    #             p_name_alias = p[self.column_dict['product_alias']].split(',')
    #             for p_a in p_name_alias:
    #                 if p_name in p_a:
    #                     a_ = p_a.replace(p_name, '').strip()
    #                     a_ = a_.split(' ')[0] # exclude post-description
    #                     if len(a_) > 0 and not a_ in b_alias:
    #                         b_alias.append(a_)
    #         brand_to_alias[b] = b_alias
    #     return brand_to_alias

if __name__ == '__main__':
    style_repo = ProductsRepo('resources//StyleMe.csv')
    print(style_repo.allproducts[:10])
    print(style_repo.allproducts_seg[:10])
    print(style_repo.get_brand_alias('L\'OREAL PARIS 巴黎萊雅'))
    # print(style_repo.get_all_descriptive_termset())
    print(style_repo.get_head_termset())
    # print(style_repo.brand_to_bind)
    # print(style_repo.bind_to_brand)
    # print(style_repo.get_all_brands())
    