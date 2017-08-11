# coding: utf-8
import os, json, csv
import re
from bs4 import BeautifulSoup


import jieba
import codecs

### load dictionary
cosmetic_dict_path = './dict.txt.big'
jieba.set_dictionary(cosmetic_dict_path)

f = codecs.open('./resources/cosmetic_headwords.txt', 'r', encoding='utf-8')
# with open('../Data/cosmetic_headwords.txt', 'r') as f:
lines = f.readlines()
pheads = [l.strip() for l in lines]
f.close()
for hw in pheads:
    jieba.add_word(hw)

column_list = ['編號', '品牌通路', '品牌', '系列中文名稱', '系列英文名稱', '中文品名', '英文品名', '中文簡介', '英文簡介', '用途', '品項', '功效', '上市日期', '規格', '販售國家', '停產國家', '是否限量', '產品別名', '建立時間', '修改時間', '是否為口碑之星', '是否在前台隱藏', '精選文章數', '是否上過首頁推薦', '產品圖', '圖1', '圖2', '圖3', '圖4', '圖5']
column_dict = {'ID':'編號', 'brand':'品牌', 'zh_series_name':'系列中文名稱', 'en_series_name':'系列英文名稱', 'zh_product_name':'中文品名', 'en_product_name':'英文品名', 'zh_intro':'中文簡介', 'en_intro':'英文簡介', 'usage':'用途', 'items':'品項', 'effect':'功效', 'date':'上市日期', 'spec':'規格', 'sell_country':'販售國家', 'unsold_country':'停產國家', 'limit_edition':'是否限量', 'product_alias':'產品別名', 'built_date':'建立時間', 'edit_date':'修改時間', 'article_num':'精選文章數'}
brand = {} # filter by brand (key: brand; value: list of product)
product_name = {} # filter by chinese product name (key: product name; value: list of product)
brand_alias_dict = {}

def classification(col, data):
    valid_col = False
    if col=='品牌':
        # print data[col], len(data), data
        class_ = brand
        valid_col = True
    elif col=='中文品名':
        class_ = product_name
        valid_col = True

    if valid_col==True:
        if class_.has_key(data[col]):
            class_[data[col]].append(data)
        else:
            class_[data[col]] = [data]
            
def load_style_me_data(file):
    with open(file, 'r') as fin:
        last_brand = ''
        tmp = 0
        for row in csv.DictReader(fin):
            tmp += 1
            if row[column_list[2]]=='':
                continue
#                 row[column_list[2]] = 'Other'
#             else:
#                 last_brand = row[column_list[2]]
            classification(column_list[2], row)
            classification(column_list[5], row)

styleMe_file = './resources/StyleMe.csv'
load_style_me_data(styleMe_file)

def get_brand_alias(b):
    b_ = b
    parathesis = re.compile(r'\(.+\)')
    parathesis.sub('', b_)
    b_alias = b_.split(' ')
    whole_product = brand[b]
    for p in whole_product:
        p_name = p[column_dict['zh_product_name']]
        p_name_alias = p[column_dict['product_alias']].split(',')
        for p_a in p_name_alias:
            if p_name in p_a:
                a_ = p_a.replace(p_name, '').strip()
#                 if b=='CHANEL 香奈兒':
#                     print p_a
                if len(a_)>0 and not a_ in b_alias:
                    b_alias.append(a_)
    
    return b_alias

for b in brand.keys():
    brand_alias_dict[b] = get_brand_alias(b)
    # print b, brand_alias_dict[b]


def remove_special_char(product):
    product = product.decode('utf-8')
    product = re.sub(r'SPF\s?\d+\+?[\/\s\.]PA[\s]*\+*', '', product, re.IGNORECASE)
    product = re.sub(r'SPF\d+\+?', '', product, re.IGNORECASE)
    product = re.sub(r'[／/]*PA\++', '', product, re.IGNORECASE)
    product = re.split(ur'\(|（', product)[0]
    product = re.sub(ur'[^\w|\s|\u4e00-\u9eff]+', '', product)
    product = product.encode('utf-8').strip()
    
    return product

def has_exact_match(title):
    exact_match = False
    found_product = []
    for b in brand.keys():
        find_brand = False
        b_ = r'\b(?:%s)\b' % '|'.join(v for v in brand_alias_dict[b])
        if re.search(b_, title):
            find_brand = True
            find_product = False
            for p in brand[b]:
                product_name = p['中文品名']
                if len(product_name)==0: continue
                product = remove_special_char(product_name)
                if re.search(product, title):
                    seg_list = jieba.lcut(product)
                    seg_list = [t for t in seg_list if not t.isspace()]
                    head = seg_list[-1].encode('utf-8')
                    # if len(re.findall(head, title))>1:
                        ### skip different product with same product head and same brand but only exactly match one product
                        ### e.g. 倩碧Clinique娃娃濃密睫毛膏+娃娃精準下睫毛膏
                        ### only 倩碧Clinique娃娃濃密睫毛膏 is in the database
                        # print '(multi-same heads!)'+head+','+title
                        # return False, []
                    found_product.append((p['編號'], b, product_name)) # ID, brand, product_name
                    find_product = True
    
    if len(found_product)>0:
        exact_match = True
    
    return exact_match, found_product


def main():
    article_dir = '../../data/styleMe/article_filtered'
    file_list = [os.path.join(article_dir, f) for f in sorted(os.listdir(article_dir))]

    key_list = ['category', 'content', 'hits', 'title', 'url', 'author', 'post_date', 'comment_count', 'post_at', 'comment_ids', 'article_id', 'tags', 'is_spam']

    num_of_sen = [0, 0, 0, 0, 0]
    str_of_sen = ['', '', '', '', '']
    total_sen_num = 0
    for i in range(len(file_list)):
    # for i in range(1):
        current_filename = file_list[i].split('\\')[-1]
        print 'current file:', current_filename
        with open(file_list[i], 'r') as fin:
            output_str = ''
            for line in fin:
                contain_same_product_head = False
                data = json.loads(line)
        #             print data['url'], data['title']
                title = data['title'].encode('utf-8')
                print data['url'].encode('utf-8'), data['title'].encode('utf-8')
                exact_match, found_list = has_exact_match(title)
                if exact_match is True:
                    output_str += json.dumps({'title': title, 'url': data['url'].encode('utf-8'), 'sentence': title, 'product': found_list, 'pattern':'(0) title exact match'})+'\n'
                    ### for log
                    num_of_sen[0] += 1
                    str_of_sen[0] += '\t(0) title: '+title+';'+str(found_list)+';url:'+data['url'].encode('utf-8')+'\n'
                    total_sen_num += 1
                    ###
    #                 print data['url'], data['title']
                    content = data['content'].encode('utf-8')
                    soup = BeautifulSoup(content, 'html.parser')
        #             print content
        #             pure_text = soup.get_text().encode('utf-8')
                    pure_text = [text for text in soup.stripped_strings]

                    ### Find product head list
                    p_head_list = []
                    p_describe_list = []
                    for p in found_list:
                        product = remove_special_char(p[-1])
    #                     print product
                        seg_list = jieba.lcut(product)
                        seg_list = [t for t in seg_list if not t.isspace()]
                        # print seg_list[-1]
                        if seg_list[-1] in p_head_list:
                            contain_same_product_head = True
                        p_head_list.append((seg_list[:-1], seg_list[-1])) # (description, product_head)
    #                     if len(seg_list)>1:
    #                         ### product contains B
    #                         p_describe_list.append(seg_list[:-1])
    #                     else:
    #                         p_decribe_list.append([])

                    label_data = []
                    for line in pure_text:
                        #### type(line)='unicode'
    #                     print line
                        ### for log
                        total_sen_num += 1
                        ###
                        tag = []
                        for idx, p_head in enumerate(p_head_list):
                            # print type(p_head[1])
                            #  print idx, p_head, type(p_head), found_list[idx][1].decode('utf-8'), type(found_list[idx][1].decode('utf-8')), type(line)
                            if len(p_head[0])>0:
                                ### product[idx] has description B, segmented as n B_
                                ### (1) if sentence contains A: match A + at least one B_ + C
                                ### (2) else: if n=2, at least n B_; else, at least n/2 B_
                                b_ = r'\b(?:%s)\b' % '|'.join(v for v in brand_alias_dict[found_list[idx][1]]) # type(b_) = <type 'str'>
                                if re.search(b_, line.encode('utf-8')):
                                    p_des = r'\b(?:%s)\b' % '|'.join(v for v in p_head[0])
                                    if re.search(p_des, line) and p_head[1] in line:
                                        # print '(1)'+p_des.encode('utf-8')+';('+found_list[idx][1]+','+found_list[idx][2]+');'+line.encode('utf-8')
                                        # print type(p_des)
                                        match_str = '(1)' + p_des.encode('utf-8') + ';' + p_head[1].encode('utf-8')
                                        tag.append((found_list[idx], match_str))
                                        ### for log
                                        num_of_sen[1] += 1
                                        str_of_sen[1] += '\t(1)'+p_des.encode('utf-8')+';('+found_list[idx][1]+','+found_list[idx][2]+');'+line.encode('utf-8')+';url:'+data['url'].encode('utf-8')+'\n'
                                        ###
                                else:
                                    if len(p_head[0])==2:
                                        p_des = r'\b(?:%s)\b' % '.*'.join(v for v in p_head[0])
                                        if re.search(p_des, line) and p_head[1] in line:
                                            # print '(2-1)' + p_des.encode('utf-8')+';('+found_list[idx][1]+','+found_list[idx][2]+');'+line.encode('utf-8')
                                            match_str = '(2-1)' + p_des.encode('utf-8') + ';' + p_head[1].encode('utf-8')
                                            tag.append((found_list[idx], match_str))
                                            ### for log
                                            num_of_sen[2] += 1
                                            str_of_sen[2] += '\t(2-1)' + p_des.encode('utf-8')+';('+found_list[idx][1]+','+found_list[idx][2]+');'+line.encode('utf-8')+';url:'+data['url'].encode('utf-8')+'\n'
                                            ###
                                    else:
                                        searched = False
                                        n = len(p_head[0])
                                        for i in range(0, int((n+1)/2)):
                                            for j in range(0, i+1):
                                                p_des = r'\b(?:%s)\b' % '.*'.join(v for v in p_head[0][j:n-i+j])
                                                if re.search(p_des, line) and p_head[1] in line:
                                                    # print '(2-2)' + p_des.encode('utf-8')+';('+found_list[idx][1]+','+found_list[idx][2]+');'+line.encode('utf-8')
                                                    match_str = '(2-2)' + p_des.encode('utf-8') + ';' + p_head[1].encode('utf-8')
                                                    tag.append((found_list[idx], match_str))
                                                    searched = True
                                                    ### for log
                                                    num_of_sen[3] += 1
                                                    str_of_sen[3] += '\t(2-2)' + p_des.encode('utf-8')+';('+found_list[idx][1]+','+found_list[idx][2]+');'+line.encode('utf-8')+';url:'+data['url'].encode('utf-8')+'\n'
                                                    ###
                                                    break
                                            if searched is True: break
                            else:
                                ### product[idx] has no description
                                ### (3) A + C
                                b_ = r'\b(?:%s)\b' % '|'.join(v for v in brand_alias_dict[found_list[idx][1]])
                                if re.search(b_, line) and p_head[1] in line:
                                    # print '(3)' + b_ +';('+found_list[idx][1]+','+found_list[idx][2]+');'+line.encode('utf-8')
                                    match_str = '(3)'+b_+';'+p_head[1].encode('utf-8')
                                    tag.append((found_list[idx], match_str))
                                    ### for log
                                    num_of_sen[4] += 1
                                    str_of_sen[4] += '\t(3)' + b_ +';('+found_list[idx][1]+','+found_list[idx][2]+');'+line.encode('utf-8')+';url:'+data['url'].encode('utf-8')+'\n'
                                    ###

                        if len(tag)>0:
                            label_data.append((line, tag))
                    # print len(label_data), label_data
                    for idx, label in enumerate(label_data):
                        # print label_data[idx][0], label_data[idx][1][0]
                        # print label_data[idx][1][0][0], label_data[idx][1][0][1]
                        output_str += json.dumps({'title': title, 'url': data['url'].encode('utf-8'), 'sentence': label_data[idx][0], 'product': label_data[idx][1][0][0], 'pattern': label_data[idx][1][0][1]})+'\n'

        # print output_str
        label_data_dir = './resources/label_data_multi_match'
        if not os.path.exists(label_data_dir):
            os.makedirs(label_data_dir)
        with open(label_data_dir+'/'+current_filename, 'w') as fout:
            fout.write(output_str)
        print ('--------finish file'+current_filename+'---------------')

    with open(label_data_dir+'/pattern_matched_result.txt', 'w') as fout:
        fout.write('(0) title exact match: '+str(num_of_sen[0])+'\n')
        fout.write(str_of_sen[0]+'\n')
        fout.write('(1) match A + at least one B_ + C: '+str(num_of_sen[1])+'\n')
        fout.write(str_of_sen[1]+'\n')
        fout.write('(2-1) n=2, match at least n B_ + C: '+str(num_of_sen[2])+'\n')
        fout.write(str_of_sen[2]+'\n')
        fout.write('(2-2) n>2, match at least n/2 B_ + C: ' + str(num_of_sen[3])+'\n')
        fout.write(str_of_sen[3]+'\n')
        fout.write('(3) product has no description, match A + C: '+str(num_of_sen[4])+'\n')
        fout.write(str_of_sen[4]+'\n')
        fout.write('total sentence number:'+str(total_sen_num)+'\n')
        fout.write('matched sentence number'+str(num_of_sen[0]+num_of_sen[1]+num_of_sen[2]+num_of_sen[3]+num_of_sen[4])+'\n')


if __name__=='__main__':
    main()