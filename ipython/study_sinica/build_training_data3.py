# coding: utf-8
import os, json, csv
import re
from bs4 import BeautifulSoup
from collections import namedtuple

import jieba

### load dictionary
def load_dictionary():
    cosmetic_dict_path = './dict.txt.big'
    jieba.set_dictionary(cosmetic_dict_path)

    f = open('./resources/cosmetic_headwords.txt', 'r', encoding='utf-8')
    # with open('../Data/cosmetic_headwords.txt', 'r') as f:
    lines = f.readlines()
    pheads = [l.strip() for l in lines]
    f.close()
    for hw in pheads:
        jieba.add_word(hw)


column_list = ['編號', '品牌通路', '品牌', '系列中文名稱', '系列英文名稱', '中文品名', '英文品名', '中文簡介', '英文簡介', '用途', '品項', '功效', '上市日期', '規格', '販售國家', '停產國家', '是否限量', '產品別名', '建立時間', '修改時間', '是否為口碑之星', '是否在前台隱藏', '精選文章數', '是否上過首頁推薦', '產品圖', '圖1', '圖2', '圖3', '圖4', '圖5']
column_dict = {'ID':'編號', 'brand':'品牌', 'zh_series_name':'系列中文名稱', 'en_series_name':'系列英文名稱', 'zh_product_name':'中文品名', 'en_product_name':'英文品名', 'zh_intro':'中文簡介', 'en_intro':'英文簡介', 'usage':'用途', 'items':'品項', 'effect':'功效', 'date':'上市日期', 'spec':'規格', 'sell_country':'販售國家', 'unsold_country':'停產國家', 'limit_edition':'是否限量', 'product_alias':'產品別名', 'built_date':'建立時間', 'edit_date':'修改時間', 'article_num':'精選文章數'}

brand_to_products = {} # filter by brand (key: brand; value: list of product)
pname_to_products = {} # filter by chinese product name (key: product name; value: list of product)
brand_alias_dict = {}
 
Product = namedtuple('Product', ['pid', 'brand', 'pname'])

def classification(col, data):
    ''' This is a function to classify the products in database by 品牌 and 中文品名 relatively
    
    :param col: 品牌 or 中文品名
    :param data: single product to be classified 
    '''
    valid_col = False
    if col=='品牌':
        # print data[col], len(data), data
        class_ = brand_to_products
        valid_col = True
    elif col=='中文品名':
        class_ = pname_to_products
        valid_col = True

    if valid_col==True:
        if  data[col] in class_:
            class_[data[col]].append(data)
        else:
            class_[data[col]] = [data]
            
def load_style_me_data(file):
    with open(file, 'r') as fin:
        for row in csv.DictReader(fin):
            if row['品牌']=='': 
                continue
            data = {'中文品名': row['中文品名'], '品牌': row['品牌'], '編號': row['編號'], '產品別名':row['產品別名']}
            classification('品牌', data)
            classification('中文品名', data)

    # store brand alias as a dictionary. (K, V) = (brand name <type 'str'>, brand alias <type 'list'>)
    for b in brand_to_products.keys():
        brand_alias_dict[b] = get_brand_alias(b)

def get_brand_alias(b):
    b_ = b.lower()
    parathesis = re.compile(r'\(.+\)')
    parathesis.sub('', b_)
    b_alias = b_.split(' ')
    whole_products= brand_to_products[b]
    for p in whole_products:
        p_name = p[column_dict['zh_product_name']]
        p_name_alias = p[column_dict['product_alias']].split(',')
        for p_a in p_name_alias:
            if p_name in p_a:
                a_ = p_a.replace(p_name, '').strip().lower()
                if len(a_)>0 and not a_ in b_alias:
                    b_alias.append(a_)
    
    to_remove=[]
    for b_a in b_alias:
        if len(b_a)==1 and re.search('\W', b_a): #remove special character
            to_remove.append(b_a)
    for tr in to_remove:
        b_alias.remove(tr)

    return b_alias

def remove_special_char(product):
    product = re.sub(r'SPF\s?\d+\+?[\/\s\.]PA[\s]*\+*', '', product, re.IGNORECASE)
    product = re.sub(r'SPF\d+\+?', '', product, re.IGNORECASE)
    product = re.sub(r'[／/]*PA\++', '', product, re.IGNORECASE)
    product = re.split(r'\(|（', product)[0]
    product = re.sub(r'[^\w|\s|\u4e00-\u9eff]+', '', product)
    
    return product

def has_exact_match(title):
    ''' This is a function to check if title has exact match(es) of brand and product
    :param title: title to check
    :return: exact_match, found_product
    '''
    found_product = []
    for b in brand_to_products:
        b_ = r'(?:%s)' % '|'.join(brand_alias_dict[b])    
        if re.search(b_, title, re.IGNORECASE):
            for p in brand_to_products[b]:
                product_name = p['中文品名']
                product = remove_special_char(product_name)
                if len(re.sub(r'\s','',product))==0 : 
                    continue
                if re.search(product, title, re.IGNORECASE):
                    # seg_list = jieba.lcut(product)
                    # seg_list = [t for t in seg_list if not t.isspace()]
                    # head = seg_list[-1]
                    # if len(re.findall(head, title))>1:
                        ### skip different product with same product head and same brand but only exactly match one product
                        ### e.g. 倩碧Clinique娃娃濃密睫毛膏+娃娃精準下睫毛膏
                        ### only 倩碧Clinique娃娃濃密睫毛膏 is in the database
                        # print '(multi-same heads!)'+head+','+title
                        # return False, []
                    found_product.append(Product(pid=p['編號'], brand=b, pname=product_name)) # ID, brand, product_name
    
    return found_product

def find_product_by_found(sentence, found_list):
    # import pdb;pdb.set_trace()
    partial_list = []    
    patterns = []

    ### Find product head list
    p_head_list = []
    for p in found_list:
        pname = p[-1] # (id, brand, pname)
        product = remove_special_char(pname)
        seg_list = jieba.lcut(product)
        seg_list = [t for t in seg_list if not t.isspace()]
        p_head_list.append((seg_list[:-1], seg_list[-1])) # (description, product_head)

    for idx, p_head in enumerate(p_head_list):
        exact_product =  found_list[idx]
        ##exact match
        pname = exact_product.pname
        pname = remove_special_char(pname)
        
        if pname in sentence:
            match_str = '(0) sentence exact match'
            partial_list.append(exact_product) 
            patterns.append(match_str)
            continue

        if len(p_head[0])==0:
            ### product[idx] has no description
            ### (3) A + C
            b_ = r'(?:%s)' % '|'.join(brand_alias_dict[found_list[idx][1]])
            if re.search(b_, sentence, re.IGNORECASE) and p_head[1] in sentence:
                match_str = '(3)'+b_+';'+p_head[1]
                partial_list.append(exact_product) 
                patterns.append(match_str)
               
        else: #at least one description word
            ### product[idx] has description B, segmented as n B_
            ### (1) if sentence contains A: match A + at least one B_ + C
            ### (2) else: if n=2, match n B_ + C; else, at least n/2 B_ + C
            b_ = r'(?:%s)' % '|'.join(brand_alias_dict[found_list[idx][1]]) 
            if re.search(b_, sentence, re.IGNORECASE):
                p_des = r'(?:%s)' % '|'.join(p_head[0])  
                if re.search(p_des, sentence, re.IGNORECASE) and p_head[1] in sentence:
                    match_str = '(1)' + p_des + ';' + p_head[1]
                    partial_list.append(exact_product) 
                    patterns.append(match_str)

            else:
                if len(p_head[0])==2:
                    # p_des = r'(?:%s)' % '.*'.join(p_head[0])
                    p_des = r'.*'.join(p_head[0])
                    if re.search(p_des, sentence, re.IGNORECASE) and p_head[1] in sentence:
                        match_str = '(2-1)' + p_des + ';' + p_head[1]
                        partial_list.append(exact_product) 
                        patterns.append(match_str)

                else:
                    searched = False
                    n = len(p_head[0])
                    for i in range(0, int((n+1)/2)):
                        for j in range(0, i+1):
                            # p_des = r'(?:%s)' % '.*'.join(p_head[0][j:n-i+j])
                            p_des = r'.*'.join(p_head[0][j:n-i+j])
                            if re.search(p_des, sentence, re.IGNORECASE) and p_head[1] in sentence:
                                match_str = '(2-2)' + p_des + ';' + p_head[1]
                                partial_list.append(exact_product) 
                                patterns.append(match_str)
                                searched = True

                                break
                        if searched: 
                            break
    return partial_list, patterns        

def head(data, n=6):
    if 'list' in str(type(data)):
        print('\n'.join(data[:n]))
    elif 'dict' in str(type(data)):
        choose_keys = list(data.keys())[:n]
        for k in choose_keys:
            print('{}: {}\n'.format(k, data[k]))


def init():
    load_dictionary()
    styleMe_file = './resources/StyleMe.csv'
    load_style_me_data(styleMe_file)

def build_training_data():
    article_dir = '../../data/styleMe/article_filtered'
    file_list = [os.path.join(article_dir, f) for f in sorted(os.listdir(article_dir))]

    output_data = []
    for i in range(len(file_list)):
        current_filename = file_list[i].split('\\')[-1]
        print('current file:', current_filename)
        with open(file_list[i], 'r', encoding='utf-8') as fin:
            output_str = ''
            for line in fin:
                # contain_same_product_head = False
                data = json.loads(line)
                title = data['title']
                article_id = data['article_id']
                # print(data['url'], data['title'])

                found_list = has_exact_match(title) # see if current title contains exact match
                if len(found_list) > 0:
                    # output_str += json.dumps({'title': title, 'url': data['url'], 'sentence': title, 'product': found_list, 'pattern':'(0) title exact match'})+'\n'
                    matched_pids = [p.pid for p in found_list]
                    matched_pnames = [p.pname for p in found_list]
                    output_data.append({'article_id' : article_id, 'title' : title, 'url' : data['url'], 'sentence' : title, 'product_ids' : matched_pids, 
                                                        'product_names' : matched_pnames, 'pattern' : ['(0) title exact match']})

                    content = data['content'] 
                    soup = BeautifulSoup(content, 'html.parser')
                    pure_text = [text for text in soup.stripped_strings] # get pure text of content
                    
                    for line in pure_text:
                        partial_list, patterns = find_product_by_found(line, found_list)
                        if len(partial_list)>0:
                            # output_str += json.dumps({'title': title, 'url': data['url'].encode('utf-8'), 'sentence': label_data[idx][0], 'product': label_data[idx][1][0][0], 'pattern': label_data[idx][1][0][1]})+'\n'
                            matched_pids = [p.pid for p in partial_list]
                            matched_pnames = [p.pname for p in partial_list]
  
                            output_data.append({'article_id' : article_id, 'title' : title, 'url' : data['url'], 'sentence' : line, 'product_ids' : matched_pids, 
                                                                'product_names' : matched_pnames, 'pattern' : patterns})
            # break

    #output        
    import time
    current = str(time.time()).split('.')[0]
    label_data_fname = './resources/label_data_' + current + '.json'
    with open(label_data_fname, 'w', encoding= 'utf-8') as fout:
        # json.dump(output_data, fout, ensure_ascii=False)
        for entry in output_data:
            #special case :
            if re.search(r'娃娃.*精準下睫毛膏', entry['sentence']):
                continue
            fout.write(json.dumps(entry, ensure_ascii=False))
            fout.write('\n')


#         # print output_str
#         label_data_dir = './resources/label_data_multi_match'
#         if not os.path.exists(label_data_dir):
#             os.makedirs(label_data_dir)
#         with open(label_data_dir+'/'+current_filename, 'w') as fout:
#             fout.write(output_str)
#         print ('--------finish file'+current_filename+'---------------')

#     with open(label_data_dir+'/pattern_matched_result.txt', 'w') as fout:
#         fout.write('(0) title exact match: '+str(num_of_sen[0])+'\n')
#         fout.write(str_of_sen[0]+'\n')
#         fout.write('(1) match A + at least one B_ + C: '+str(num_of_sen[1])+'\n')
#         fout.write(str_of_sen[1]+'\n')
#         fout.write('(2-1) n=2, match at least n B_ + C: '+str(num_of_sen[2])+'\n')
#         fout.write(str_of_sen[2]+'\n')
#         fout.write('(2-2) n>2, match at least n/2 B_ + C: ' + str(num_of_sen[3])+'\n')
#         fout.write(str_of_sen[3]+'\n')
#         fout.write('(3) product has no description, match A + C: '+str(num_of_sen[4])+'\n')
#         fout.write(str_of_sen[4]+'\n')
#         fout.write('total sentence number:'+str(total_sen_num)+'\n')
#         fout.write('matched sentence number'+str(num_of_sen[0]+num_of_sen[1]+num_of_sen[2]+num_of_sen[3]+num_of_sen[4])+'\n')

def test(title, sentence):
    found_list = has_exact_match(title) # see if current title contains exact match
    if found_list:
        partial_list, patterns = find_product_by_found(sentence, found_list) 
        print(partial_list)
    else:
        print('no exact match in title')

init()
if __name__=='__main__':
    build_training_data()
    # head(brand_alias_dict)
    # title = ' GIORGIO ARMANI奢華漂染腮紅盒11色全試色大圖/經典的奢華升級並且延續'
    # sentence = 'GIORGIO ARMANI  奢華腮紅盒 11色全試色大圖/經典的奢華升級並且延續'
    # test(title, sentence)
