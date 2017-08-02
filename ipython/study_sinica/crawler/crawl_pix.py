
# coding: utf-8
#! python3

from urllib.request import Request, urlopen
import urllib
from bs4 import BeautifulSoup,NavigableString
from time import sleep
import re
import sys
import traceback
from datetime import datetime
import json
from tqdm import tqdm

# for error logging
import logging


logger = logging.getLogger('crawler')
logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - \n%(message)s')
ch.setFormatter(formatter)

# add the handlers to logger
logger.addHandler(ch)


def getUrlContent(url):
    headers={'User-Agent': 'Mozilla/5.0'}
    req = Request(url,headers=headers)
    response_html = urlopen(req).read()
    return response_html


def getUrlListOfBoard(board, sleep_sec = 1):
    url_list=[]
    
    p_ind = 1 
    while p_ind < 1000:
        try:
            if p_ind % 10 == 1:
                logger.info('parse page {}'.format(p_ind))

            url = 'https://styleme.pixnet.net/{}?page={}'.format(board, p_ind)
            html_content = getUrlContent(url)
            #print(html_content.decode("utf-8"))
            soup = BeautifulSoup(html_content,"html.parser")
            #print soup.prettify()
            logger.debug("page title  "+soup.title.string)

            # fetch all article blocks
            articles= soup.find_all('div', class_="article-bg")
            if len(articles) == 0:
                break

            for article in articles:
                a_tag=article.find('a')
                if not a_tag : #如果沒有a tag就跳過
                    continue
                href = a_tag.get('href') #取得網址
                if href and len(href) > 1:
                    article_url = "https://styleme.pixnet.net" + href #網址
                    url_list.append(article_url)              
                # break 
            p_ind += 1
            sleep(sleep_sec)
            
        except Exception as e:
            s=traceback.format_exc()

            logger.error(url)
            logger.error(s)
        
    return url_list
    

def parseArticle(article_html,url):

    #用html.parser如果頁面結構不對(如tag沒有正確地close)的話，會導致parse不完全..
    soup = BeautifulSoup(article_html,"html5lib") 
    
    #remove js
    for script in soup(["script", "style"]):
        script.decompose()    # rip it out

    #category
    nav_cate_tags = soup.find_all('a', class_ = 'breadcrumb__link')
    category = nav_cate_tags[1].get_text().replace('>','').replace(' ','')
    logger.debug(category)

    #article-metaline下的 article-meta-value包含標題作者時間
    article_tag= soup.find('article', "post__left-content")

    #header
    header = article_tag.find('header')
    ##date
    day = header.find('p', class_ = 'post__time__day').string
    month= header.find('p', class_ = 'post__time__month').string
    year = header.find('p', class_ = 'post__time__year').string
    date =  '{}-{}-{}'.format(year, month, day)
    date = datetime.strptime(date,'%Y-%b-%d')
    logger.debug(date.strftime('%Y-%m-%d'))

    ##title
    title_tag = header.find('h1', class_= "post__info__title")
    title = title_tag.string
    logger.debug(title)

    ##author
    author_tag = header.find('a', class_='post__info__author__link')
    author = author_tag.get_text().replace('by ','')
    author_link = 'https://styleme.pixnet.net' + author_tag.get('href')
    logger.debug(author)
    logger.debug(author_link)

    #tags
    tag_list = []
    tag_ul = article_tag.find('ul', class_ = 'post__tags')
    if tag_ul: # 有可能沒有tags
        tag_lis = tag_ul.find_all('li')
        for tag in tag_lis:
            tag_list.append(tag.get_text())
    logger.debug('\t'.join(tag_list))

    #artitcle content
    article_content = article_tag.find('div', class_ = 'post__article').get_text()
    logger.debug(article_content)

    article = {'url':url, 'category':category, 'post_date':date.isoformat(),  'title':title, 'author': author, 'author_link':author_link, 'tags': tag_list, 'content': article_content}
    return article



def main(board):
    logger.setLevel(logging.INFO)
    sleep_sec= 1
    article_url_list = getUrlListOfBoard(board, sleep_sec)

    #remove duplicate
    article_url_list_u=[]
    for url in article_url_list:
        if url not in article_url_list_u:
            article_url_list_u.append(url)
    article_url_list=article_url_list_u       

    logger.info("Finish: fetch url list of {} url".format(len(article_url_list))) 
    with open('urls.txt', 'w' , encoding = 'utf-8') as outfile:
        outfile.write('\n'.join(article_url_list))

    article_list = []

    for url in tqdm(article_url_list):
        try:
            logger.debug("Parse article {}".format(url))        
            article_html=getUrlContent(url)
            article = parseArticle(article_html,url)
            article_list.append(article)

            sleep(sleep_sec)
            
        except Exception as e:
            s=traceback.format_exc()

            logger.error(url)
            logger.error(s)

    print('total article count {}'.format(len(article_list)))
    
    output_fname = board + '.txt'
    with open(output_fname, 'w') as outfile:
        json.dump(article_list, outfile, ensure_ascii=False)

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        board = sys.argv[1]
        main(board)