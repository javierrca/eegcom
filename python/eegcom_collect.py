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
from threading import Thread

def cleanLine(li):
        line=str(li)
        line = line.replace("b'","'")
        line = line.strip('\r')
        line = line.strip()
        line = line.replace("\\r","")
        line = line.replace("''","'")
        line = line.replace("'","")
        return line

def checkWrongSignal(tn):
    j=0
    wrongSignal= True
    
    while j<600 and wrongSignal:
        j=j+1
        line=tn.read_until('\r'.encode('ascii'));
        line=cleanLine(str(line))
        if len(line) > 2:
            try:
                dict=json.loads(line);
            except:
                continue
            if "eegPower" in dict:
                wrongSignal=False
            else: 
                wrongSignal=True
            
    return wrongSignal
        
def extract_raw(line,personName,questionCode,questionText,timediff):
    outputRawstr = ""
    try:
        dict=json.loads(line);
    except:
        dict=json.loads(line);
    if "rawEeg" in dict:
        rawEntry=dict['rawEeg'];
        outputRawstr=str(personName)+","+str(questionCode)+","+str(timediff)+ ","+ str(rawEntry)    
    return outputRawstr

    
def extract_power(line,personName,questionCode,questionText,timediff):
    outputstr = ""
    signalLevel=0
    blinkStrength=0;
    try:
        dict=json.loads(line);
    except:
        dict=json.loads(line);
    if "poorSignalLevel" in dict:
        signalLevel=dict['poorSignalLevel'];
    if "blinkStrength" in dict:
        blinkStrength=dict['blinkStrength'];
    if "eegPower" in dict:
        waveDict=dict['eegPower'];
        eSenseDict=dict['eSense'];
        outputstr=str(personName)+","+str(questionCode)+ ","+str(timediff)+ ","+ str(signalLevel)+","+str(blinkStrength)+"," + str(eSenseDict['attention']) + "," + str(eSenseDict['meditation']) + ","+str(waveDict['lowGamma'])+"," + str(waveDict['highGamma'])+","+ str(waveDict['highAlpha'])+","+str(waveDict['delta'])+","+ str(waveDict['highBeta'])+","+str(waveDict['lowAlpha'])+","+str(waveDict['lowBeta'])+ ","+str(waveDict['theta']);    
    return outputstr
    
class CollectThread(Thread):
    # constructor
    def __init__(self,personName,questionCode,questionText,event,tn,counter):
        # execute the base constructor
        Thread.__init__(self)
        # set a default value
        self.value = None
        self.personName = personName
        self.questionCode = questionCode
        self.questionText= questionText
        self.event = event
        self.tn=tn
        self.counter= counter
 
    # function executed in a new thread
    def run(self):
        self.value="OK"
        personName = self.personName
        questionCode = self.questionCode
        questionText = self.questionText
        event = self.event
        tn = self.tn
        
        tn.open('localhost',13854);

        i=0;
        tn.write('{"enableRawOutput": true, "format": "Json"}'.encode('ascii'));

        if event.is_set():
            tn.close();
            return
        
        outfile=personName + "_" + questionCode + "_EEGPOW_"+ str(self.counter) + ".csv";
        outfptr=open(outfile,'w');
        outputstr="person" +"," + "questionCode"+ ","+ "timediff"+ ","+ "signalLevel"+","+"blinkStrength"+"," + "attention" + "," + "meditation" + ","+ "lowGamma"+"," + "highGamma"+","+ "highAlpha"+","+"delta"+","+ "highBeta"+","+"lowAlpha"+"," +"lowBeta"+","+"theta";
        outfptr.write(outputstr+"\n");

        outRawfile=personName + "_" + questionCode + "_EEGRAW_"+ str(self.counter+1) + ".csv";
        outRawptr=open(outRawfile,'w');
        outputRawstr="person"+ "," + "questionCode"+ ","+"timediff"+ ","+ "rawEeg";
        outRawptr.write(outputRawstr+"\n");


        eSenseDict={'attention':0, 'meditation':0};
        waveDict={'lowGamma':0, 'highGamma':0, 'highAlpha':0, 'delta':0, 'highBeta':0, 'lowAlpha':0, 'lowBeta':0, 'theta':0};
        signalLevel=0;
        start=time.perf_counter ();
        
        print("Checking signal...")
        wrongSignal = checkWrongSignal(tn)
        if wrongSignal:
            print("No good signal")
            self.value="NCON"            
            outfptr.close()
            outRawptr.close()
            tn.close();
            return
        print("Good signal")  
        
        print(questionText+ '\n',end="\r")

        raw=[]
        emot=[]
        x=1    
       
        # collect the real time raw and power signals
        while x<COLLECT_SAMPLES:
            x=x+1
            line=tn.read_until('\r'.encode('ascii'));
            line=cleanLine(line)
            timediff=time.perf_counter ()-start;    
            if len(line) > 20:
                emot.append(extract_power(line,personName,questionCode,questionText,timediff))

            elif len(line) > 2 :
                raw.append(extract_raw(line,personName,questionCode,questionText,timediff))
            if event.is_set():
                x=COLLECT_SAMPLES - DELAY_RAW_SAMPLES
                event.clear()
        print("Saved RAW data delayed " + str(len(raw)))

        # collect the 5 seconds-delayed power signals
        x=1
        while x<DELAY_POWER_SAMPLES:
            x=x+1
            line=tn.read_until('\r'.encode('ascii'));
            line=cleanLine(line)
            # print("line: " + str(line))    
            timediff=time.perf_counter ()-start;    
            if len(line) > 20:
                # print(str(line))
                emot.append(extract_power(line,personName,questionCode,questionText,timediff))


        # print output files
        for line in raw:
                if outRawfile!="null":	
                    outRawptr.write(line+"\n");	        
        for line in emot:
                if outfile!="null":	
                    outfptr.write(line+"\n");		                

        outfptr.close()
        outRawptr.close()
        print("Saved POWER data delayed ")   
        tn.close();
        return
    
COLLECT_SAMPLES=3072
DELAY_RAW_SAMPLES =20
DELAY_POWER_SAMPLES=2560

def main():
    
    args = sys.argv[1:]
    filename = ""
    
    if len(args) == 1:
        filename = args[0]
    else:
        print("Error: No parameter specifying questions file name")
        sys.exit()

    print("Press any key to continue...")
    personName = input('Enter the name of the person: ')
    
    print("Connecting...")
    tn=Telnet()
    questions_ds = pd.read_csv(filename,sep=';')
    
    counter=100
    for index, q in questions_ds.iterrows():        
        questionCode=str(q[0])
        if (len(questionCode)==1):
            questionCode = "0" + questionCode
        questionText=str(q[1])

        event = Event()
        event.clear()
        print("\r")
        print("Question:" + questionCode )
        x = CollectThread(personName,questionCode,questionText,event,tn,counter)
        x.start()
        key = msvcrt.getch()
        if (key==b'f'):
            print("shutdown..")
            event.set()
            x.join()
            tn.close();
            sys.exit() 
        if (str(x.value) == 'OK' and x.is_alive()):
            # Sent event to stop thread
            event.set()
        x.join()        
        event.clear()
        counter=counter+2
    tn.close();
    print("completed")

if __name__ == "__main__":
    main()    





