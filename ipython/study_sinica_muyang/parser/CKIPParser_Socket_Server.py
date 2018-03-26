#!/usr/bin/python
#-*- encoding: UTF-8 -*-

import socket
import time
import threading
import os
import json
import re
from multiprocessing import Pool
from ctypes import *
# import pyodbc

inifile = ''
ws = None
wrap = None
parser = None
parserini = None
pool = None
# con = pyodbc.connect("Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=E:\\CKIPParser\\account_db\\CKIPService.mdb")

class nonblocking_socket:
    def __init__(self, client, buffer = 4096):
        self.buffer = buffer
        self.client = client

    def get_iters(self, data):
        try:
            field = data.split(u':', 1)
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
        pack_data = length + u':' + JSONData
        pack_data = pack_data.encode('utf-8',  errors='ignore')
        return pack_data

    def decapsulate(self, data):
        data = data.decode('utf-8', errors='ignore')
        JSONData = data.split(u':', 1)[1]
        info = json.loads(JSONData)
        return info

class ParserStruct(Structure):
    _fields_ = [('nNo',c_int),("result",c_char*200000)]

def loadINI(ini_file):
    import sys
    if sys.version[:1] == '2':
        from ConfigParser import SafeConfigParser as ConfigParser
    else:
        from configparser import ConfigParser

    global parserini
    config=ConfigParser()
    config.read(ini_file)
    options=config.options('Parser')
    for option in options:
        value=config.get('Parser',option)
        #value=config.get('Parser',option,"")
        parserini[option]=value

def initial(pyWrap_dll, ini_file, ws_main_dll, ws_py_dll, ws_ini):
    # global ws
    global wrap
    global parser
    global parserini

    # 初始化斷詞
    # c_main_dll = c_wchar_p(ws_main_dll)
    # c_ini = c_wchar_p(ws_ini)
    # ws = CDLL(ws_py_dll)
    # ws.Initial(c_main_dll,c_ini)

    # 載入 pyWrapParser.dll
    wrap = CDLL(pyWrap_dll)
    parser = ParserStruct()
    parserini = {}

    #載入 系統
    wrap.LoadDLL(byref(parser))

    #只要1次, 基本的設定及預設值
    parser.result=(os.getcwd()+"\\").encode('utf-8')
    wrap.ParserCommand("InitParser\t".encode('utf-8')+parser.result,byref(parser))

    #------------------以下為載入 *.ini 的內容, 會參考的部份------------------------------------
    #'parser.ini'
    loadINI(ini_file)
    #Default
    wrap.ParserCommand("Default".encode('utf-8'), byref(parser))
    wrap.ParserCommand("SetHeadProb\ttrue".encode('utf-8'),byref(parser))
    wrap.ParserCommand("SetBinary\ttrue".encode('utf-8'),byref(parser))
    #細詞類?
    if parserini.get('setmap','0')=='1':
        wrap.ParserCommand("LoadMap".encode('utf-8'),byref(parser))
        wrap.ParserCommand("SetMap\ttrue".encode('utf-8'),byref(parser))
    else:
        wrap.ParserCommand("SetMap\tfalse".encode('utf-8'),byref(parser))
    #斷詞系統?
    if parserini.get('setautotag','0')=='1':
        wrap.ParserCommand("SetAutoTagVersion\t1".encode('utf-8'),byref(parser))
    else:
        wrap.ParserCommand("SetAutoTagVersion\t0".encode('utf-8'),byref(parser))
        if parserini.get('setdm','0')=='1':
            wrap.ParserCommand("BreakDM".encode('utf-8'),byref(parser))
        else:
            wrap.ParserCommand("MergeDM".encode('utf-8'),byref(parser))
        value=parserini.get('setdicfile','')
        if value!='':
            wrap.ParserCommand(("AssignDic\t"+value).encode('utf-8'),byref(parser))
        else:
            wrap.ParserCommand("cleardic".encode('utf-8'),byref(parser))
    #簡化詞類
    if parserini.get('setpos13','0')=='1':
        wrap.ParserCommand("SetPos13\ttrue".encode('utf-8'),byref(parser))
    else:
        wrap.ParserCommand("SetPos13\tfalse".encode('utf-8'),byref(parser))
    #角色
    if parserini.get('setrole','0')=='1':
        wrap.ParserCommand("loadkb",byref(parser))
        wrap.ParserCommand("setrole\ttrue".encode('utf-8'),byref(parser))
    else:
        wrap.ParserCommand("setrole\tfalse".encode('utf-8'),byref(parser))
    #句長
    value=parserini.get('setlength','')
    if value!="":
        wrap.ParserCommand(("SetLength\t"+value).encode('utf-8'),byref(parser))
    else:
        wrap.ParserCommand("SetLength\t30".encode('utf-8'),byref(parser))
    #pos轉換
    if parserini.get('setchangepos','0')=='1':
        wrap.ParserCommand("SetChangePos\ttrue".encode('utf-8'),byref(parser))
    else:
        wrap.ParserCommand("SetChangePos\tfalse".encode('utf-8'),byref(parser))

    #------------------------------------------------------

    #開始剖析
    wrap.ParserCommand("ParsingIni".encode('utf-8'), byref(parser)) #必要

# def parsing(Sent):
#     global ws
#     global wrap
#     global parser

#     Sent = Sent.strip()
#     # Preprocessing
#     token = [u'，', u',',u'；',u';', u'。', u':', u'：', u'？', u'?', u'!', u'！']
#     for tok in token:
#         Sent = Sent.replace(tok, tok + u'\n')
#     Sent = Sent.strip()

#     parser_result = ''
#     try:
#         #Segmentation
#         ws_cresult = ws.Segment(Sent)
#         ws_cresult = cast(ws_cresult,c_wchar_p)
#         ws_result = ws_cresult.value
#         ws_result = ws_result.replace(u'\n(FW)　', u'\n')
#         #print(ws_result)
#         #Parsing
#         cmd=(u"Parsing\t" + ws_result).encode('big5', errors='ignore')
#         parser.result = bytes()
#         wrap.ParserCommand(cmd, byref(parser))
#         parser_result = parser.result.decode('big5', errors='ignore')
#     except:
#         pass
#     finally:
#         return parser_result

# handling text that has already been segmented
def parsing_ws(ws_result):
    # global ws
    global wrap
    global parser
    parser_result = ''
    try:
        ws_result = ws_result.replace(u'\n(FW)　', u'\n')
        #Parsing
        cmd=(u"Parsing\t" + ws_result).encode('big5', errors='ignore')
        parser.result = bytes()
        wrap.ParserCommand(cmd, byref(parser))
        parser_result = parser.result.decode('big5', errors='ignore')
    except:
        pass
    finally:
        return parser_result

# def check(_user, _pwd):
#     global con
#     cur = con.cursor()
#     rows = cur.execute('SELECT * FROM Account;')

#     for row in rows:
#         vtime = row[2]
#         user = row[3]
#         pwd = row[4]
#         if vtime is not None and vtime!='0' and user==_user and pwd==_pwd:
#             return True

#     return False

def handle_client(client):
    global pool

    client = nonblocking_socket(client)
    # Receiving Data
    info = client.receive()

    result = ''
    try:
        # Check account
        uname = None
        pwd = None

        if info.get(u'user') is not None:
            uname = info[u'user']
        if info.get(u'pwd') is not None:
            pwd = info[u'pwd']

        if uname is not None and pwd is not None:

            # check function <- you need to implement by yourself
            # valid = check(uname, pwd)

            # if not valid:
            #     result = u'Account Error'
            # else:
            # Parsing
            if info.get(u'text') is not None:
                Sent = info[u'text']
                res = None
                # print(Sent[:50]+'...')
                # if info.get(u'ws')=='True':
                res = pool.apply_async(parsing_ws, (Sent,))
                # else:
                    # res = pool.apply_async(parsing, (Sent,))
                result = res.get()
        else:
            result = u'Account Error'
    except:
        result = 'Error'
        print ("[*] Error: %s" % data.decode('utf-8',  errors='ignore'))
    finally:
        client.send(result)
        client.close()

if __name__=="__main__":

    bind_ip = "0.0.0.0"
    bind_port = 6400

    ws_main_dll = 'CKIPWS.dll'
    ws_py_dll = 'PY_CKIPWS.dll'
    ws_ini = 'ws.ini'

    parser_pyWrap_dll = 'pyWrapParser'
    parser_ini = 'parser.ini'

    #Processes Number can be modified
    pool = Pool(processes = 16, initializer=initial, initargs=(parser_pyWrap_dll,parser_ini,ws_main_dll,ws_py_dll,ws_ini), \
        maxtasksperchild=1000)

    #Server Start
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((bind_ip, bind_port))
    server.listen(16)

    print ("[*] Listening on %s:%d" % (bind_ip, bind_port))

    #Watiing Client
    while True :
        client, addr = server.accept()
        print ("[*] Acepted connection from: %s:%d" % (addr[0],addr[1]))
        client_handler = threading.Thread(target=handle_client, args=(client,))
        client_handler.start()
