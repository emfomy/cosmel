# !python2
#!/usr/bin/python
#-*- encoding: UTF-8 -*-

import ctypes, sys, json
import os
from IPython import embed

class PyWordSeg(object):
    def __init__(self):
        __LIBRARY__="/home/jina/CKIPWS_Linux/bin/libWordSeg.so"
        __inifile__= "/home/jina/PIXNET/named-entity-extraction/ipython/study_sinica/resources/ws_makeup_headword_jina.ini"
        self.lib=ctypes.cdll.LoadLibrary(__LIBRARY__)
        self.obj=self.lib.WordSeg_New()
        self.lib.WordSeg_InitData.restype=ctypes.c_bool
        self.lib.WordSeg_ApplyFile.restype=ctypes.c_bool
        self.lib.WordSeg_ApplyList.restype=ctypes.c_bool
        self.lib.WordSeg_ApplyArticle.restype=ctypes.c_bool
        self.lib.WordSeg_GetResultBegin.restype=ctypes.c_wchar_p
        self.lib.WordSeg_GetResultNext.restype=ctypes.c_wchar_p
        self.lib.WordSeg_GetUWBegin.restype=ctypes.c_wchar_p
        self.lib.WordSeg_GetUWNext.restype=ctypes.c_wchar_p
        ret=self.lib.WordSeg_InitData(self.obj, __inifile__)
        if not ret:
            raise IOError("Loading %s failed."%(__inifile__));

    def EnableLogger(self):
        self.lib.WordSeg_EnableConsoleLogger(self.obj)

    def ApplyFile(self, inputfile, outputfile, uwfile=None):
        return self.lib.WordSeg_ApplyFile(self.obj, inputfile, outputfile, uwfile)

    def ApplyList(self, inputList):
        if len(inputList)==0:
            return []
        inArr=(ctypes.c_wchar_p*len(inputList))()
        inArr[:]=inputList
        #print((self.obj, len(inputList), inArr))
        ret=self.lib.WordSeg_ApplyList(self.obj, len(inputList), inArr)
        #print('go1',ret)
        if ret==None:
            return []

        outputList=[]
        out=self.lib.WordSeg_GetResultBegin(self.obj)
        while out!=None:
            outputList.append(out)
            out=self.lib.WordSeg_GetResultNext(self.obj)

        uwList=[]
        out=self.lib.WordSeg_GetUWBegin(self.obj)
        while out!=None:
            uwList.append(out)
            out=self.lib.WordSeg_GetUWNext(self.obj)

        return (outputList, uwList)

    def ApplyArticle(self, inputList):

        if len(inputList)==0:
            return ([],[])
        inArr=(ctypes.c_wchar_p*len(inputList))()
        inArr[:]=inputList
        ret=self.lib.WordSeg_ApplyArticle(self.obj, len(inputList), inArr)
        if ret==None:
            return ([],[])

        outputList=[]
        out=self.lib.WordSeg_GetResultBegin(self.obj)
        while out!=None:
            outputList.append(out)
            out=self.lib.WordSeg_GetResultNext(self.obj)

        uwList=[]
        out=self.lib.WordSeg_GetUWBegin(self.obj)
        while out!=None:
            uwList.append(out)
            out=self.lib.WordSeg_GetUWNext(self.obj)

        return (outputList, uwList)

    def __del__(self):
        self.lib.WordSeg_Destroy(self.obj)

if __name__=="__main__":
    print('GO test')
    wordseg=PyWordSeg()
    #wordseg.EnableLogger()
    for idx in range(2,len(sys.argv),2):
        inf=open(sys.argv[idx])
        L=[]
        for line in inf:
            line=str(line).decode("UTF-8")
            print(line)
            L.append(line)
        (oL, uwL)=wordseg.ApplyList(L)
        print(oL, uwL)
        outf=open(sys.argv[idx+1],"w")

        for line in oL:
            outf.write(line.encode("UTF-8")+"\n")
