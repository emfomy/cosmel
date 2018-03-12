#!/usr/bin/env python3
#-*- encoding: UTF-8 -*-

# from nltk.tree import *
# from nltk.draw.tree import TreeView
import socket
import json
import time

class nonblocking_socket:
    def __init__(self, client, buffer = 4096):
        self.buffer = buffer
        self.client = client

    def get_iters(self, data):
        try:
            field = data.split(':', 1)
            length = int(field[0])
            if len(data) == self.buffer: iters = int(length / self.buffer) + 1
            else: iters = int(length / self.buffer)
        except:
            iters = None
        return iters

    def receive(self):
        self.client.setblocking(0)

        count = 0
        data = bytes()
        first = True
        iters = None

        while True:
            try:
                request = self.client.recv(self.buffer)
                if not request:
                    time.sleep(0.05)
                    continue
            except:
                continue
            if first:
                first = False
                iters = self.get_iters(request.decode('utf-8'))
                if iters is None: break
                data = request
            else:
                data += request
                count += 1
            if count == iters: break
        try:
            data = self.decapsulate(data)
        except:
            data = None

        return data

    def send(self, data):
        data = self.encapsulate(data)
        self.client.sendall(data)

    def close(self):
        self.client.close()

    def encapsulate(self, data):
        JSONData = json.dumps(data)
        length = str(len(JSONData))
        pack_data = length + ':' + JSONData
        pack_data = pack_data.encode('utf-8',  errors='ignore')
        return pack_data

    def decapsulate(self, data):
        data = data.decode('utf-8', errors='ignore')
        JSONData = data.split(':', 1)[1]
        info = json.loads(JSONData)
        return info

def connect(host, port):
    # create socket
    # AF_INET 代表使用標準 IPv4 位址或主機名稱
    # SOCK_STREAM 代表這會是一個 TCP client
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # client 建立連線
    client.settimeout(10)
    client.connect((host, port))
    return client

def communicate(host, port, info, retry):
    data = None

    for i in range(retry):
        try:
            client = connect(host, port)
            client = nonblocking_socket(client)
            client.send(info)
            data = client.receive()
            client.close()
            break
        except Exception as e:
            print(e)
            time.sleep(5 * (i + 1))

    return data

def parse(sentence, uname, pwd, ws=False):
    target_host = "172.16.1.64"
    target_port = 6400
    target_host = "192.168.109.32"
    target_port = 9998
    retry = 3

    # Segmentation
    info = {}
    info['text'] = sentence.strip()
    info['user'] = uname
    info['pwd'] = pwd
    info['ws'] = str(ws)

    response = []
    # Communication
    data = communicate(target_host, target_port, info, retry)
    if(data is not None):
        response = data.strip().replace('\r\n', '\n').split('\n')

    return response

def treeConstruct(sentence):
    treeList = []
    ResultList = parse(sentence)
    for result in ResultList:
        field = result.rstrip().split('#')
        sentence_parse_result = field[1].split('] ')[1]
        sentence_parse_result = u"(" + sentence_parse_result + u")"
        sentence_parse_result = sentence_parse_result.replace(u"|",u")(")
        syntax_tree = ParentedTree.fromstring(sentence_parse_result)
        treeList.append(syntax_tree)
        #TreeView(syntax_tree) #show structure
        #TreeView(syntax_tree)._cframe.print_to_file('output.ps') #show structure
    return treeList

def demo():
    uname = '_tester'
    pwd = 'tester'
    #Sent = '我喜歡吃麥當勞的薯條，弟弟則喜歡吃肯德基的炸雞。'
    Sent = '我(Nh)　喜歡(VK)　吃(VC)　麥當當勞(Nc)　的(DE)　美味薯條(Na)　，(COMMACATEGORY)'

    start = time.time()
    ResultList = parse(Sent, uname, pwd, True)
    print('Spend Time:',time.time() - start)
    print(ResultList)

if __name__=="__main__":
    demo()
