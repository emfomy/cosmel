#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import csv
import re
# import jieba
import os
import pickle

#from CKIP_Client.CKIP_Client import *
from PyWordSeg import *

def load_predifined_headword(path = './resources/myLexicon/cosmetic_headwords.txt', sort=False):
    product_head = []
    with open(path, 'r', encoding='utf-8') as fin:
        for line in fin:
            if line.strip() in product_head: continue
            product_head.append(line.strip())
    if sort:
        product_head.sort(key=lambda x: len(x), reverse=True)
    return product_head

##word segmentation package
# def load_dictionary():
#     jieba.set_dictionary('dict.txt.big')

#     pheads = load_predifined_headword('./resources/cosmetic_headwords.txt')
#     for hw in pheads:
#         jieba.add_word(hw)

#     # jieba.suggest_freq('乳液', True)

#     with open('./resources/brands_in_chinese.txt', 'r', encoding='utf-8') as f:
#         lines = f.readlines()
#         brands = [l.strip() for l in lines]
#         for b in brands:
#             jieba.add_word(b)
# load_dictionary()

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
        self.allbrands = []
        self.pind_to_complete_product = {} # (k, v)=('pind', ['product', [(brand)], [[complete_product]], 'last_word'])
        self.complete_product_to_pind = {} # (k, v)=('complete_product', 'pind')
        self.pind_to_pname = {}
        self.pname_to_pind = {}
        self.pname_to_brand = {}

        self.bind_to_brand = {}
        self.brand_to_bind = {}

        self.makeup_headwords = load_predifined_headword()

        for item in p_repo:
            origin_name = item['zh_product_name'].strip()
            ind = item['ID']
            brand = item['brand']

            # name = self.remove_special_char_in_product(origin_name)
            name = origin_name
            name = name.strip()

            if len(name)==0 or len(brand)==0:
                continue

            self.allproducts_origin.append(origin_name)
            self.allproducts.append(name)
            self.allpinds.append(ind)
            self.allbrands.append(brand)
            self.pname_to_pind[name] = ind
            self.pind_to_pname[ind] = name
            self.pname_to_brand[name] = brand

            # if '指甲油' in origin_name and 'Dior' in brand:
            #     print('index:{}, brand:{}, product:{}'.format(ind, brand, origin_name))

        self.pind_to_complete_product = self.get_complete_brand_n_product_as_dict()
        # print(self.pind_to_complete_product)

        self.all_brand_set = self.get_all_brand_as_dict()

        brands_set = set( [b.lower() for b in self.allbrands])
        # try:
        #     brands_set.remove('')
        # except ValueError:
        #     pass
        for i, b in enumerate(brands_set):
            self.bind_to_brand[i] = b
            self.brand_to_bind[b]=i

        self.allproducts_seg = []
        self.pind_to_pname_seg = {} # (k, v)=('pid', 'CKIP斷詞 w/ POS')
        self.pind_to_complete_product_seg = {} # (k, v)=('pid', 'CKIP斷詞 w/ POS'), complete_product
        ## add saving file
        f_ws_all_product_pkl = './WSed_pickles/ws_all_products.pkl'
        f_ws_complete_product_pkl = './WSed_pickles/ws_complete_product.pkl'
        if os.path.exists(f_ws_all_product_pkl) and os.path.exists(f_ws_complete_product_pkl):
            print('loading WSed pickle files: {}, {}'.format(f_ws_all_product_pkl, f_ws_complete_product_pkl))
            self.pind_to_pname_seg = pickle.load(open(f_ws_all_product_pkl, 'rb'))
            self.pind_to_complete_product_seg = pickle.load(open(f_ws_complete_product_pkl, 'rb'))

        elif not os.path.exists(f_ws_all_product_pkl) and os.path.exists(f_ws_complete_product_pkl):
            p_ori_file = './resources/myLexicon/all_product.txt'
            p_ws_file = './resources/myLexicon/all_product.txt.tag'
            all_product_seg_dict = self.load_product_ws(p_ori_file, p_ws_file)
            for k in self.pind_to_pname:
                self.pind_to_pname_seg[k] = all_product_seg_dict[self.pind_to_pname[k]]

            pickle.dump(self.pind_to_pname_seg, open(f_ws_all_product_pkl, 'wb'))

            print('loading WSed pickle files: {}'.format(f_ws_complete_product_pkl))
            self.pind_to_complete_product_seg = pickle.load(open(f_ws_complete_product_pkl, 'rb'))

        elif os.path.exists(f_ws_all_product_pkl) and not os.path.exists(f_ws_complete_product_pkl):
            cp_ori_file = './resources/myLexicon/complete_brands_product.txt'
            cp_ws_file = './resources/myLexicon/complete_brands_product.txt.tag'
            all_complete_product_seg_dict, last_word = self.load_complete_brand_n_product_ws(cp_ori_file, cp_ws_file)
            for k in self.pind_to_complete_product:
                c_product = self.pind_to_complete_product[k][2][0][0]
                if c_product in all_complete_product_seg_dict:
                    self.pind_to_complete_product_seg[k] = all_complete_product_seg_dict[c_product]
            pickle.dump(self.pind_to_complete_product_seg, open(f_ws_complete_product_pkl, 'wb'))

            print('loading WSed pickle files: {}'.format(f_ws_all_product_pkl))
            self.pind_to_pname_seg = pickle.load(open(f_ws_all_product_pkl, 'rb'))
        else:
            print('doing word segmanting')

            p_ori_file = './resources/myLexicon/all_product.txt'
            p_ws_file = './resources/myLexicon/all_product.txt.tag'
            all_product_seg_dict = self.load_product_ws(p_ori_file, p_ws_file)
            for k in self.pind_to_pname:
                self.pind_to_pname_seg[k] = all_product_seg_dict[self.pind_to_pname[k]]

            pickle.dump(self.pind_to_pname_seg, open(f_ws_all_product_pkl, 'wb'))

            cp_ori_file = './resources/myLexicon/complete_brands_product.txt'
            cp_ws_file = './resources/myLexicon/complete_brands_product.txt.tag'
            all_complete_product_seg_dict, last_word = self.load_complete_brand_n_product_ws(p_ori_file, p_ws_file)
            for k in self.pind_to_complete_product:
                c_product = self.pind_to_complete_product[k][2][0][0]
                if c_product in all_complete_product_seg_dict:
                    self.pind_to_complete_product_seg[k] = all_complete_product_seg_dict[c_product]
            pickle.dump(self.pind_to_complete_product_seg, open(f_ws_complete_product_pkl), 'wb')

            # print('(L)self.pind_to_pname_seg: ', self.pind_to_pname_seg)
        print('--finish WS product name--')
        # embed()
        # print(self.pind_to_pname_seg)

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



    def load_product_ws(self, ori_file, ws_file):
        product_ws_dict = {}
        product = []
        product_ws = []

        product = [line.replace('\tN_product', '').strip() for line in open(ori_file, 'r', encoding='utf-8').readlines()]
        product_ws = [line.strip() for line in open(ws_file, 'r', encoding='utf-8').readlines()]

        print(len(product), len(product_ws), len(product_ws_dict))


        duplicated = []
        for idx in range(len(product)):
            if product[idx] in product_ws_dict:
                duplicated.append(product[idx])
                # print('product: {}, ws: {}'.format(product[idx], product_ws[idx]))
            product_ws_dict[product[idx]] = product_ws[idx]


        print(len(product_ws_dict))

        return product_ws_dict


    def load_complete_brand_n_product_ws(self, ori_file, ws_file):
        product_ws = {}
        complete_product_list = []
        complete_product_ws_list = []

        complete_product_list = [line.replace('\tN_Cproduct', '').strip() for line in open(ori_file, 'r', encoding='utf-8').readlines()]
        complete_product_ws_list = [line.strip() for line in open(ws_file, 'r', encoding='utf-8').readlines()]

        # self.complete_product_list_to_pind
        # self.pind_to_complete_product_list

        # print(len(complete_product_list), len(complete_product_ws_list), len(product_ws))

        duplicated = []
        for idx in range(len(complete_product_list)):

            if complete_product_list[idx] in product_ws:
                duplicated.append(complete_product_list[idx])
                # print('complete: {}, ws: {}'.format(complete_product_list[idx], complete_product_ws_list[idx]))
            product_ws[complete_product_list[idx]] = complete_product_ws_list[idx]
        ## duplicated: 14896-14827=69
        ## remove duplicated -> complete_product # 14758
        # print(len(product_ws))
        for ele in duplicated:
            del product_ws[ele]

        last_word = []

        for pid in self.pind_to_complete_product:
            # embed()
            # print(pid, self.pind_to_complete_product[pid])
            complete_product = self.pind_to_complete_product[pid][2][0][0]
            # print('complete_product:{}'.format(complete_product))
            if complete_product in product_ws:
                # print('123')
                c_ws = product_ws[complete_product]
                self.pind_to_complete_product[pid].append(c_ws.split('　')[-1])
                # print('ws_word:{}, last_word:{}'.format(c_ws, c_ws.split('　')[-1]))
                last_word.append(c_ws.split('　')[-1])
                # print(self.pind_to_complete_product[pid])

        return product_ws, set(last_word)


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
            print(p_seg)
            hw = p_seg[-1][0]
            if not p_seg[-1][1]=='FW':
                hws.add(hw)
        return hws

    @staticmethod
    def remove_special_char_in_product(product):
        # product = re.sub(r'SPF\s?\d+\+?[\/\s\.]PA\+*', '', product, re.IGNORECASE)
        # product = re.sub(r'SPF\d+\+?', '', product, re.IGNORECASE)
        # product = re.sub(r'\W', '', product)
        product = re.sub(r'SPF\s?\d+\+?[\/\s\.／]*PA[\s]*\+*', '', product, re.IGNORECASE)
        product = re.sub(r'SPF\s*\d+\+?', '', product, re.IGNORECASE)
        product = re.sub(r'PA\++', '', product, re.IGNORECASE)
        product = re.sub(r'\s', '', product, re.IGNORECASE)

        # product = re.sub(r'\W', ' ', product)
        # product = re.split(r'\(|（', product)[0]

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
        return self.allbrands

    def get_all_brands_chinese(self):
        b_set = set()
        for b in self.get_all_brands():
            aliases = self.get_brand_alias(b)
            for a in aliases:
                if check_contain_chinese(a):
                    b_set.add(a)
        return b_set

    def get_all_brand_as_dict(self, build_lexicon=False):

        brands = []
        b_string = ''

        for b in self.get_all_brands():
            temp_b = ''
            eng=''
            chi=''
            for ele in b.split(' '):
                if not ele:
                    continue
                if check_contain_chinese(ele):
                    chi+=ele
                else:
                    eng = eng + ele

            eng = eng.lower().strip()
            chi = chi.split('（')[0].strip() #資生堂（東京櫃）
            # print('brand: {}, eng:{}, chi:{}'.format(b, eng, chi))
            # exit()

            if not len(chi)==0 and not len(eng)==0:
                temp_b += eng+'\tN_brand\n'
                temp_b += chi+'\tN_brand\n'
                temp_b += eng+chi+'\tN_brand\n'
                temp_b += chi+eng+'\tN_brand\n'

                brands.append(eng)
                brands.append(chi)
                brands.append(eng+chi)
                brands.append(chi+eng)

            if not len(chi)==0 and len(eng)==0:
                temp_b += chi+'\tN_brand\n'
                brands.append(chi)

            if len(chi)==0 and not len(eng)==0:
                temp_b += eng+'\tN_brand\n'
                brands.append(eng)

            # print(temp_b)
            b_string += temp_b

        if build_lexicon:
            open('./resources/myLexicon/all_brands.txt', 'w').write(b_string)
        return set(brands)

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

    def get_all_product_as_dict(self):
        p_string = ''

        for product in self.allproducts_origin:
            product = re.sub(r'SPF\s?\d+\+?[\/\s\.／]*PA[\s]*\+*', '', product, re.IGNORECASE)
            product = re.sub(r'SPF\s*\d+\+?', '', product, re.IGNORECASE)
            product = re.sub(r'PA\++', '', product, re.IGNORECASE)
            product = re.sub(r'\s', '', product, re.IGNORECASE)
            p_string += product+'\tN_product\n'
        with open('./resources/myLexicon/all_product.txt', 'w') as fout:
            fout.write(p_string)


    def get_complete_brand_n_product_as_dict(self, build_lexicon=False):

        b_string = ''
        pind_to_complete_product = {}

        duplicate_complete_product_str = ''

        for i, product in enumerate(self.allproducts_origin):
            # if '指甲油' in product:
            #     print('index:{}, chi:{}, eng:{}, product:{}'.format(self.allpinds[i], chi, eng, product))
            brand_list = []
            complete_product_list = []
            product = re.sub(r'SPF\s?\d+\+?[\/\s\.／]*PA[\s]*\+*', '', product, re.IGNORECASE)
            product = re.sub(r'SPF\s*\d+\+?', '', product, re.IGNORECASE)
            product = re.sub(r'PA\++', '', product, re.IGNORECASE)
            product = re.sub(r'\s', '', product, re.IGNORECASE)
            brand = self.allbrands[i]

            eng = ''
            chi = ''
            temp_b = ''
            for ele in brand.split(' '):
                if not ele:
                    continue
                if check_contain_chinese(ele):
                    chi += ele
                else:
                    eng += ele

            eng = eng.lower().strip()
            chi = chi.split('（')[0].strip() #資生堂（東京櫃）
            if not len(chi)==0 and not len(eng)==0:
                temp_b += eng+product+'\tN_Cproduct\n'
                temp_b += chi+product+'\tN_Cproduct\n'
                temp_b += eng+chi+product+'\tN_Cproduct\n'
                temp_b += chi+eng+product+'\tN_Cproduct\n'
                brand_list.append((brand, eng, chi))
                complete_product_list.append([eng+product, chi+product, eng+chi+product, chi+eng+product])
            elif not len(chi)==0 and len(eng)==0:
                temp_b += chi+product+'\tN_Cproduct\n'
                brand_list.append((brand, chi))
                complete_product_list.append([chi+product])
            elif len(chi)==0 and not len(eng)==0:
                temp_b += eng+product+'\tN_Cproduct\n'
                brand_list.append((brand, eng))
                complete_product_list.append([eng+product])

            for Cpro in complete_product_list:
                for c in Cpro:
                    duplicate_complete_product_str += self.add_to_complete_product_to_pind(c, self.allpinds[i])

        # with open('./resources/myLexicon/all_product.txt', 'w') as fout:
        #     fout.write(p_string)
            # print(temp_b)
            b_string += temp_b
            pind_to_complete_product[self.allpinds[i]] = [product, brand_list, complete_product_list]
        # b_set = set(self.get_all_brands())

        # for b in alias:
        #     # aliases = self.get_brand_alias(b)
        #     for a in aliases:
        #         b_string += a+'\tNb\n'
        if build_lexicon:
            open('./resources/myLexicon/complete_brands_product.txt', 'w').write(b_string)
        # print(b_string)
        # print('len(complete_product_to_pind):{}'.format(len(self.complete_product_to_pind)))
        print(duplicate_complete_product_str)
        return pind_to_complete_product

    def add_to_complete_product_to_pind(self, complete_product, pind):
        duplicate_complete_product = ''
        if complete_product in self.complete_product_to_pind:
            # print('d: {}, current id:{}, new_id:{}'.format(complete_product, self.complete_product_to_pind[complete_product], pind))
            del self.complete_product_to_pind[complete_product]
            # duplicate_complete_product = complete_product+'\n'
        else:
            self.complete_product_to_pind[complete_product] = pind

        return duplicate_complete_product

if __name__ == '__main__':
    style_repo = ProductsRepo('resources//StyleMe.csv')
    # print(style_repo.allproducts[:10])
    # print(style_repo.allproducts_seg[:10])
    # print(style_repo.get_brand_alias('L\'OREAL PARIS 巴黎萊雅'))
    # print(style_repo.get_all_descriptive_termset())
    # print(style_repo.get_head_termset())
    # print(style_repo.brand_to_bind)
    # print(style_repo.bind_to_brand)
    # style_repo.get_all_brand_as_dict()
    # style_repo.get_all_product_as_dict()
    # style_repo.get_complete_brand_n_product_as_dict()

    with open('style_repo.pkl', 'wb') as handle:
        pickle.dump(style_repo, handle, protocol=pickle.HIGHEST_PROTOCOL)
