#!/usr/bin/env python
# coding: utf-8
import numpy as np
import pandas as pd
import sys
import json
import time
from telnetlib import Telnet
import logging
import threading
import time
from threading import Event
import msvcrt
import keyboard
import numpy as np
import pandas as pd



def cleanLine(li):
        line=str(li)
        line = line.replace("b'","'")
        line = line.strip('\r')
        line = line.strip()
        line = line.replace("\\r","")
        line = line.replace("''","'")
        line = line.replace("'","")
        return line
    
def checkWrongSignal(tn,event,includeRaw):

    #i=0
    j=0
    tn.write('{"enableRawOutput": true, "format": "Json"}'.encode('ascii'))

    line=""
    line_pre = ""

    while 1==1:
        j=j+1
        if event.is_set():
            break     
        line_pre = line
        line=tn.read_until('\r'.encode('ascii'));
        line=cleanLine(str(line))
        if len(line) > 5:
            dict=json.loads(line);
            if "rawEeg" in dict:
                rawEntry=dict['rawEeg'];
                if includeRaw:
                    print(str(time.perf_counter()) + " line: " + str(line))
            elif "eegPower" in dict:
                print(str(time.perf_counter()) + " line: " + str(line))
            else:
                print(str(time.perf_counter()) + " line wrong: " + str(line))
            
    return 
            


def main():
    args = sys.argv[1:]
    includeRaw = False
    
    if len(args) == 1 and args[0] == '-raw':
        includeRaw = True

    tn=Telnet('localhost',13854);
    event = Event()
    x = threading.Thread(target=checkWrongSignal, args=(tn,event,includeRaw))
    x.start()
    msvcrt.getch()
    event.set()
    x.join()        

    tn.close();
    print("Stopped")        
        
        
if __name__ == "__main__":
    main()    




