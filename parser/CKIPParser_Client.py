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
    assert host is not None
    assert port is not None
    # create socket
    # AF_INET 代表使用標準 IPv4 位址或主機名稱
    # SOCK_STREAM 代表這會是一個 TCP client
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # client 建立連線
    client.settimeout(5)
    client.connect((str(host), int(port)))
    return client

def communicate(host, port, info, retry):
    data = None

    err = None
    for i in range(retry):
        try:
            client = connect(host, port)
            client = nonblocking_socket(client)
            client.send(info)
            data = client.receive()
            client.close()
            break
        except Exception as e:
            err = e
            time.sleep(5 * (i + 1))
    else:
        print(err)

    return data

def parse(sentence, uname, pwd, ws=False, host=None, port=None):
    retry = 3

    # Segmentation
    info = {}
    info['text'] = sentence.strip()
    info['user'] = uname
    info['pwd'] = pwd
    info['ws'] = str(ws)

    response = []
    # Communication
    data = communicate(host, port, info, retry)
    if(data is not None):
        response = data.strip().replace('\r\n', '\n').split('\n')

    return response

def demo():
    uname = '_tester'
    pwd = 'tester'
    #Sent = '我喜歡吃麥當勞的薯條，弟弟則喜歡吃肯德基的炸雞。'
    Sent = '我(Nh)　喜歡(VK)　吃(VC)　麥當當勞(Nc)　的(DE)　美味薯條(Na)　，(COMMACATEGORY)'
    Sent = '　'.join([str(i+1)+'(FW)' for i in range(80)])
    print(Sent)

    start = time.time()
    ResultList = parse(Sent, uname, pwd, True)
    print('Spend Time:',time.time() - start)
    print(ResultList)

if __name__=="__main__":
    demo()
