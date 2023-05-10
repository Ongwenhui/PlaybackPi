'''
Important notes: soundlooper() -> keeps playmasker() running
playmasker() -> plays selected masker from predictions
'''

import json
import AWSIoTPythonSDK.MQTTLib as AWSIoTPyMQTT
#from PIL import Image
from io import BytesIO
import numpy as np
import sounddevice as sd 
import soundfile as sf
import time 
import queue
import sys
import threading
import math
import csv
import pandas as pd
import random
from pydub import AudioSegment
import keyboard
import sys
import tty
import termios

varymaskers = False
MEOW = False

calibjsonpath = "/home/pi/mqtt_client/calib.json"

def interpolate(masker,gain):
    f = open(calibjsonpath, "r")
    # calib = f.read()
    # print(calib)
    calib = json.load(f)
    # # calib = json.loads(f.read())
    keepgoing = True
    counter = 0
    chosengain = 0
    while keepgoing == True:
        currval = abs(gain - calib[masker][counter])
        if counter < (len(calib[masker])-1):
            nextval = abs(gain - calib[masker][counter + 1])
        else: 
            nextval = abs(gain - calib[masker][0])
        if nextval >= currval:
            keepgoing = False
            chosengain = calib[masker][counter]
        if counter < (len(calib[masker])-1):
            counter += 1
        else:
            counter = 0
    if counter>0: 
        finaldb = counter -1 + 46
    else:
        finaldb = 46+37

    # print("chosengain = {}".format(chosengain))
    # print("counter -1 = {}".format(counter -1))
    return finaldb

def readcsv(csvfile):
    calibgains = {}
    with open(csvfile, 'r') as file:
        csvreader = csv.reader(file)
        header = next(csvreader)
        for row in csvreader:
            entrycount = 0
            currmasker = ""
            nextgain = 0
            for entry in row:
                if entrycount == 0:
                    calibgains[entry] = {}
                    currmasker = entry
                elif entrycount != 0 and (entrycount % 2) != 0:
                    nextgain = float(entry)
                elif entrycount != 0 and (entrycount % 2) == 0:
                    calibgains[currmasker][str(int(round(float(entry))))] = nextgain 
                entrycount += 1
    return calibgains

calibgains = readcsv('/home/pi/mqtt_client/Calibrations_final_speaker.csv')

# mqttENDPOINT = "a5i03kombapo4-ats.iot.ap-southeast-1.amazonaws.com"
# mqttCLIENT_ID = "AIMEGET"
# mqttcertfolder = "/home/pi/mqtt_client/certs/"
# mqttPATH_TO_CERTIFICATE = mqttcertfolder + "c86008d5f6f3eb115159777ba9da6c0b97bfdf2309c15020c8d1d2747e4f6bdc-certificate.pem.crt"
# mqttPATH_TO_PRIVATE_KEY = mqttcertfolder + "c86008d5f6f3eb115159777ba9da6c0b97bfdf2309c15020c8d1d2747e4f6bdc-private.pem.key"
# mqttPATH_TO_AMAZON_ROOT_CA_1 = mqttcertfolder + "AmazonRootCA1.pem"
# mqttTOPIC = "amss/prediction"
# mqttRANGE = 20

#LOCATION_ID = 'ntu-gazebo01'
LOCATION_ID = 'hollandclose'
optimaldistance = 1 #Punggol MSCP
numofspeakers = 4
class soundplayer:
    def __init__(self):
        self.mqttENDPOINT="a5i03kombapo4-ats.iot.ap-southeast-1.amazonaws.com"
        self.mqttCLIENT_ID= "AIMEGET"
        self.mqttcertfolder="/home/pi/mqtt_client/certs/"
        self.mqttPATH_TO_CERTIFICATE = self.mqttcertfolder + "c86008d5f6f3eb115159777ba9da6c0b97bfdf2309c15020c8d1d2747e4f6bdc-certificate.pem.crt"
        self.mqttPATH_TO_AMAZON_ROOT_CA_1 = self.mqttcertfolder + "AmazonRootCA1.pem"
        self.mqttPATH_TO_PRIVATE_KEY=self.mqttcertfolder + "c86008d5f6f3eb115159777ba9da6c0b97bfdf2309c15020c8d1d2747e4f6bdc-private.pem.key"
        self.mqttTOPIC="amss/{}/prediction".format(LOCATION_ID)
        self.mqttRANGE=20
        self.currentdoa = 90
        self.MQTTClient = AWSIoTPyMQTT.AWSIoTMQTTClient(self.mqttCLIENT_ID)
        self.MQTTClient.configureEndpoint(self.mqttENDPOINT, 8883)
        self.MQTTClient.configureCredentials(self.mqttPATH_TO_AMAZON_ROOT_CA_1, self.mqttPATH_TO_PRIVATE_KEY, self.mqttPATH_TO_CERTIFICATE)
        # self.msgdict = {'predictions': [{'rank': 1, 'id': 'bird_00075', 'gain': 0.01793866604566574, 'score': 0.47396957874298096}, {'rank': 2, 'id': 'bird_00075', 'gain': 0.020203232765197754, 'score': 0.47391098737716675}, {'rank': 3, 'id': 'bird_00075', 'gain': 0.02149977907538414, 'score': 0.47387757897377014}, {'rank': 4, 'id': 'bird_00069', 'gain': 0.05129025876522064, 'score': 0.4719516634941101}, {'rank': 5, 'id': 'bird_00075', 'gain': 0.10646381229162216, 'score': 0.47165820002555847}, {'rank': 6, 'id': 'bird_00069', 'gain': 0.10134433209896088, 'score': 0.4705403745174408}, {'rank': 7, 'id': 'bird_00025', 'gain': 0.0057005020789802074, 'score': 0.470207154750824}, {'rank': 8, 'id': 'bird_00069', 'gain': 0.15140660107135773, 'score': 0.46911484003067017}, {'rank': 9, 'id': 'bird_00025', 'gain': 0.08437956869602203, 'score': 0.46776485443115234}, {'rank': 10, 'id': 'bird_00071', 'gain': 0.06381088495254517, 'score': 0.4665457308292389}, {'rank': 11, 'id': 'bird_00069', 'gain': 0.25197258591651917, 'score': 0.46620792150497437}, {'rank': 12, 'id': 'bird_00046', 'gain': 0.07355550676584244, 'score': 0.46558114886283875}], 'base_score': 0.33999258279800415, 
        # 'doa': self.currentdoa, 'from': 'ntu-gazebo01', 'timestamp': 1654067860.26, 'base_spl': 68.10846120156562} if not MEOW else {'predictions': [{'rank': 1, 'id': 'meow', 'gain': 1, 'score': 0.47396957874298096}, {'rank': 2, 'id': 'meow', 'gain': 1, 'score': 0.47391098737716675}, {'rank': 3, 'id': 'meow', 'gain': 1, 'score': 0.47387757897377014}, {'rank': 4, 'id': 'meow', 'gain': 1, 'score': 0.4719516634941101}, {'rank': 5, 'id': 'meow', 'gain': 1, 'score': 0.47165820002555847}], 'base_score': 0.33999258279800415, 
        # 'doa': self.currentdoa, 'from': 'ntu-gazebo01', 'timestamp': 1654067860.26, 'base_spl': 68.10846120156562}
        self.fixedmasker = 'playing fixed masker = '
        self.msgdict = None
        self.currentmasker = "bird_00075" if not MEOW else "meow"
        self.maskerpath = "/home/pi/mqtt_client/maskers/"
        self.maskergain = 1.2
        self.gainweight = 1    
        self.maskerdiff =0.0001
        self.gainlimit = 1000
        self.weightedgain = 0
        self.buffersize = 20
        self.blocksize = 4096
        self.q = queue.Queue()#(maxsize=self.buffersize)
        self.q2 = queue.Queue()
        self.msgq = None
        self.msgqeval = None
        self.event = threading.Event()
        self.fadelength = 80
        self.maskercounter = 0
        self.currentmaskerorig = "bird_00075" if not MEOW else "meow"
        self.maskergainorig = 1
        self.doadiff = 20
        self.ambientspl = 68.1
        self.nexttrackmsg = 'playback starting...'
        self.beforeevaluationmsg = 'evaluation starting...'
        self.duringevaluationmsg = 'evaluation in progress, press any key to proceed to the next track.'
        self.endmsg = 'end of study'
        self.voicePromptGain = 0.1

    def insitucompensate(self, numofspeakers,distance):
        compensated = round(20*math.log10(distance) - 10*math.log10(numofspeakers))
        return compensated

    def insituMultiMaskercompensate(self, numofspeakers,distance,noOfMaskers):
        compensated = round(20*math.log10(distance) - 
                            10*math.log10(numofspeakers) -
                            20*math.log10(noOfMaskers))
        return compensated

    def spatialize(self, masker, angle, normalize=True, offset=-65, k=1.0):
        # masker.shape = (n_samples,)2
        # angle in degrees
        # offset in degrees
        
        # speaker locations assumed to be (RF, RB, LB, LF) i.e., (45, 135, 225, 315) deg
        # counting CW relative to the 0 deg line of the UMA
        # use offset to shift the speaker locations as needed
        
        '''
                0 deg
        [LF]----------[RF]
        |       ^       |
        |       |       |
        |     [UMA]     |
        |               |
        |               |
        [LB]----------[RB]
        
        
        e.g. if UMA is actually pointing at RF, then offset should be 45 deg
        i.e. set offset to negative of whereever UMA is pointing as if the UMA is pointing at 0 deg
        '''
            
        masker = np.squeeze(masker)
        
        anglerad = -np.deg2rad(angle + offset)
        x = k * np.cos(anglerad)
        y = k * np.sin(anglerad)
        
        lf = 1 + x + y # 1 + 1/2)
        lb = 1 - x + y
        rb = 1 - x - y
        rf = 1 + x - y

        # lf = 0
        # lb = 0
        # rb = 0
        # rf = 0

        
        gains = np.array([rb, lb, lf, rf])
        
        if normalize:
            gains = gains / np.sqrt(1 + 2*k*k)
    
        masker4c = masker[:, None] * gains[None, :] # (n_samples, 4)
        
        return masker4c        

    def msgcallback(self, client, userdata, message):
        print("GETTING PREDICTIONS FROM AWS")
        incomingmsg=json.loads(message.payload.decode('utf-8'))
        # self.q.put_nowait(incomingmsg)
        # self.q2.put_nowait(incomingmsg)
        print(incomingmsg)
        self.msgq = incomingmsg
        print(self.msgq['predictions'])
        print("Recommended Masker is: " + str(incomingmsg['predictions'][0]["id"]))
        print("Recommended Gain is: {} ({}dB)".format(incomingmsg['predictions'][0]["gain"], interpolate(incomingmsg['predictions'][0]["id"],incomingmsg['predictions'][0]["gain"])))
        print("BaseSPL is: {}".format(incomingmsg["base_spl"]))
        # data, fs = sf.read(msgdict['predictions'][0]["id"]+'.wav', dtype='float32')  
        # sd.play(data, fs, device=1)
    def ambient(self):
        time.sleep(30)
    def playfixedmasker(self, name):
        df = pd.read_csv(participantfilepath + f'participant_00{participantid}.csv')
        gainindex = 0
        for row in df.iterrows():
            if row[1][0] == name:
                fixedmastergain = row[1][1]
            gainindex += 1
        fixedmasker = name
        fixedmaskers, fs = sf.read(self.maskerpath + name)

        #compensated gain for distance and num of speakers
        compGain = math.pow(10,self.insitucompensate(numofspeakers,optimaldistance)/20)
        print('Compensated gain: {} dB'.format(20*math.log10(compGain)))
        print(self.maskerpath + fixedmasker)
        print('now playing fixed masker {} with gain: {} as DOA {}'.format(fixedmasker, fixedmastergain*compGain, self.currentdoa))

        sd.play(fixedmaskers*fixedmastergain*compGain, fs)
        sd.wait()

    def playfixedmaskereval(self, name):
        df = pd.read_csv(participantfilepath + f'participant_00{participantid}.csv')
        gainindex = 0
        for row in df.iterrows():
            if row[1][0] == name:
                fixedmastergain = row[1][1]
            gainindex += 1
        fixedmasker = name
        fixedmaskers, fs = sf.read(self.maskerpath + name)
        fixedmaskers = np.add(fixedmaskers*0.5,fixedmaskers*0.5)
        
        #compensated gain for distance and num of speakers
        compGain = math.pow(10,self.insitucompensate(numofspeakers,optimaldistance)/20)
        print('Compensated gain: {} dB'.format(20*math.log10(compGain)))
        print(self.maskerpath + fixedmasker)
        print('now playing fixed masker {} with gain: {} as DOA {}'.format(fixedmasker, fixedmastergain*compGain, self.currentdoa))
        
        while True:
            sd.play(fixedmaskers*fixedmastergain*compGain, fs, loop=True)
            if is_key_pressed():
                break
 
    def play4maskers(self):

        self.q = queue.Queue(maxsize=self.buffersize)
        newmasker = None
        newweightedgain = None
        newdoa = None
        self.msgdict = self.msgq
        self.msgqeval = self.msgdict
        #why q2?    
        if not self.q2.empty():
            self.msgdict = self.msgq
            self.ambientspl = self.msgdict["base_spl"]
            
        if self.msgdict != None: #If there is a prediction
            predictionlist =[]
            uniquepredictionlist = []
            for prediction in self.msgdict['predictions']:
                for indexes in range(7):
                    uniquepredictionlist.append(self.msgdict['predictions'][indexes]['rank'])
                    uniquepredictionlist.append(self.msgdict['predictions'][indexes]['id'])
            self.currentmasker1 = uniquepredictionlist[1]
            self.maskerindex1 = uniquepredictionlist[0]
            self.currentmasker2 = uniquepredictionlist[3]
            self.maskerindex2 = uniquepredictionlist[2]
            self.currentmasker3 = uniquepredictionlist[5]
            self.maskerindex3 = uniquepredictionlist[4]
            self.currentmasker4 = uniquepredictionlist[7]
            self.maskerindex4 = uniquepredictionlist[6]
            print('top 4 rated maskers = {}, {}, {}, {}'.format(self.currentmasker1, self.currentmasker2, self.currentmasker3, self.currentmasker4))
            print('index of top 4 maskers = {}, {}, {}, {}'.format(self.maskerindex1, self.maskerindex2, self.maskerindex3, self.maskerindex4))
            # if the masker to be played is not self.currentmasker, set self.maskergain to the gain of the masker to be played
            # self.currentmasker is set to bird_00075 by default
            if (self.msgdict['predictions'][self.maskerindex1]["id"] != self.currentmasker) or (self.msgdict['predictions'][self.maskerindex2]["id"] != self.currentmasker) or (self.msgdict['predictions'][self.maskerindex3]["id"] != self.currentmasker) or (self.msgdict['predictions'][self.maskerindex4]["id"] != self.currentmasker) or (abs(self.msgdict['predictions'][self.maskercounter]["gain"]-self.maskergain)*self.gainweight>self.maskerdiff) or (abs(self.currentdoa - self.msgdict["doa"])>self.doadiff):
                self.maskergain1 = self.msgdict['predictions'][self.maskerindex1]["gain"]
                self.maskergain2 = self.msgdict['predictions'][self.maskerindex2]["gain"]
                self.maskergain3 = self.msgdict['predictions'][self.maskerindex3]["gain"]
                self.maskergain4 = self.msgdict['predictions'][self.maskerindex4]["gain"]
                # if self.maskergain (set in previous step) less than gainlimit (set at 1000)
                if self.maskergain1*self.gainweight < self.gainlimit:
                    print("self.maskergain1 = {}".format(self.maskergain1))
                    # calculate amssgain
                    amssgain = interpolate(self.msgdict['predictions'][self.maskerindex1]["id"],self.maskergain) + self.insitucompensate(numofspeakers,optimaldistance)
                    # set amssgaint to min 45 and max 83
                    if amssgain >45 and amssgain <= 83:
                        pass
                    elif amssgain >83:
                        amssgain = 83
                    elif amssgain <46:
                        amssgain = 46
                    print('amss1gain = {}'.format(amssgain))
                    self.weightedgain1 = calibgains[self.msgdict['predictions'][self.maskerindex1]["id"]+'.wav'][str(amssgain)]
                    print("self.weightedgain1 = {}".format(self.weightedgain1))
                else:
                    self.weightedgain1 = self.gainlimit
                self.currentmasker1 = self.msgdict['predictions'][self.maskerindex1]["id"]
                self.currentdoa = self.msgdict["doa"]
                if self.maskergain2*self.gainweight < self.gainlimit:
                    print("self.maskergain2 = {}".format(self.maskergain2))
                    # calculate amssgain
                    amssgain = interpolate(self.msgdict['predictions'][self.maskerindex2]["id"],self.maskergain) + self.insitucompensate(numofspeakers,optimaldistance)
                    # set amssgaint to min 45 and max 83
                    if amssgain >45 and amssgain <= 83:
                        pass
                    elif amssgain >83:
                        amssgain = 83
                    elif amssgain <46:
                        amssgain = 46
                    print('amss2gain = {}'.format(amssgain))
                    self.weightedgain2 = calibgains[self.msgdict['predictions'][self.maskerindex2]["id"]+'.wav'][str(amssgain)]
                    print("self.weightedgain2 = {}".format(self.weightedgain2))
                else:
                    self.weightedgain2 = self.gainlimit
                self.currentmasker2 = self.msgdict['predictions'][self.maskerindex2]["id"]
                self.currentdoa = self.msgdict["doa"]
                if self.maskergain3*self.gainweight < self.gainlimit:
                    print("self.maskergain3 = {}".format(self.maskergain3))
                    # calculate amssgain
                    amssgain = interpolate(self.msgdict['predictions'][self.maskerindex3]["id"],self.maskergain) + self.insitucompensate(numofspeakers,optimaldistance)
                    # set amssgaint to min 45 and max 83
                    if amssgain >45 and amssgain <= 83:
                        pass
                    elif amssgain >83:
                        amssgain = 83
                    elif amssgain <46:
                        amssgain = 46
                    print('amss3gain = {}'.format(amssgain))
                    self.weightedgain3 = calibgains[self.msgdict['predictions'][self.maskerindex3]["id"]+'.wav'][str(amssgain)]
                    print("self.weightedgain3 = {}".format(self.weightedgain3))
                else:
                    self.weightedgain3 = self.gainlimit
                self.currentmasker3 = self.msgdict['predictions'][self.maskerindex3]["id"]
                self.currentdoa = self.msgdict["doa"]
                if self.maskergain4*self.gainweight < self.gainlimit:
                    print("self.maskergain4 = {}".format(self.maskergain4))
                    # calculate amssgain
                    amssgain = interpolate(self.msgdict['predictions'][self.maskerindex4]["id"],self.maskergain) + self.insitucompensate(numofspeakers,optimaldistance)
                    # set amssgaint to min 45 and max 83
                    if amssgain >45 and amssgain <= 83:
                        pass
                    elif amssgain >83:
                        amssgain = 83
                    elif amssgain <46:
                        amssgain = 46
                    print('amss4gain = {}'.format(amssgain))
                    self.weightedgain4 = calibgains[self.msgdict['predictions'][self.maskerindex4]["id"]+'.wav'][str(amssgain)]
                    print("self.weightedgain4 = {}".format(self.weightedgain4))
                else:
                    self.weightedgain4 = self.gainlimit
                self.currentmasker4 = self.msgdict['predictions'][self.maskerindex4]["id"]
                self.currentdoa = self.msgdict["doa"]
        else:
            pass
        try:
            f1, fs1 = sf.read(self.maskerpath + self.currentmasker1 +'.wav')
            f2, fs2 = sf.read(self.maskerpath + self.currentmasker2 +'.wav')
            f3, fs3 = sf.read(self.maskerpath + self.currentmasker3 +'.wav')
            f4, fs4 = sf.read(self.maskerpath + self.currentmasker4 +'.wav')
            print("stream created using {}, {}, {}, and {} with gain: {}, {}, {}, and {} at DOA: {}".format(self.currentmasker1,
                                                                                                            self.currentmasker2,
                                                                                                            self.currentmasker3,
                                                                                                            self.currentmasker4,
                                                                                                            self.weightedgain1,
                                                                                                            self.weightedgain2,
                                                                                                            self.weightedgain3,
                                                                                                            self.weightedgain4,
                                                                                                            self.currentdoa))
            
            #data1 = self.spatialize(f1*self.weightedgain1, self.currentdoa)
            #data2 = self.spatialize(f2*self.weightedgain2, self.currentdoa)
            #data3 = self.spatialize(f3*self.weightedgain2, self.currentdoa)
            #data4 = self.spatialize(f4*self.weightedgain2, self.currentdoa)

            data1 = f1*self.weightedgain1
            data2 = f2*self.weightedgain2
            data3 = f3*self.weightedgain3
            data4 = f4*self.weightedgain4 
            print('{},{},{},{}'.format(self.weightedgain1, self.weightedgain2, self.weightedgain3, self.weightedgain4))
            data = np.empty((len(data1),4))
            for length in range(len(data)):
                data[length][0] += data1[length]
                data[length][1] += data2[length]                
                data[length][2] += data3[length]                
                data[length][3] += data4[length]
            print(np.shape(data))
            compGain = math.pow(10,self.insitucompensate(numofspeakers,optimaldistance)/20)
            print('Compensated gain: {} dB'.format(20*math.log10(compGain)))
            sd.play(data*compGain, fs1)
            sd.wait()
            
        except KeyboardInterrupt:
            pass     
    def play4maskerseval(self):

        self.q = queue.Queue(maxsize=self.buffersize)
        newmasker = None
        newweightedgain = None
        newdoa = None
        self.msgdict = self.msgqeval
        #why q2?    
        if not self.q2.empty():
            self.msgdict = self.msgqeval
            self.ambientspl = self.msgdict["base_spl"]
            
        if self.msgdict != None: #If there is a prediction
            predictionlist =[]
            uniquepredictionlist = []
            for prediction in self.msgdict['predictions']:
                for indexes in range(7):
                    uniquepredictionlist.append(self.msgdict['predictions'][indexes]['rank'])
                    uniquepredictionlist.append(self.msgdict['predictions'][indexes]['id'])
            self.currentmasker1 = uniquepredictionlist[1]
            self.maskerindex1 = uniquepredictionlist[0]
            self.currentmasker2 = uniquepredictionlist[3]
            self.maskerindex2 = uniquepredictionlist[2]
            self.currentmasker3 = uniquepredictionlist[5]
            self.maskerindex3 = uniquepredictionlist[4]
            self.currentmasker4 = uniquepredictionlist[7]
            self.maskerindex4 = uniquepredictionlist[6]
            print('top 4 rated maskers = {}, {}, {}, {}'.format(self.currentmasker1, self.currentmasker2, self.currentmasker3, self.currentmasker4))
            print('index of top 4 maskers = {}, {}, {}, {}'.format(self.maskerindex1, self.maskerindex2, self.maskerindex3, self.maskerindex4))
            # if the masker to be played is not self.currentmasker, set self.maskergain to the gain of the masker to be played
            # self.currentmasker is set to bird_00075 by default
            if (self.msgdict['predictions'][self.maskerindex1]["id"] != self.currentmasker) or (self.msgdict['predictions'][self.maskerindex2]["id"] != self.currentmasker) or (self.msgdict['predictions'][self.maskerindex3]["id"] != self.currentmasker) or (self.msgdict['predictions'][self.maskerindex4]["id"] != self.currentmasker) or (abs(self.msgdict['predictions'][self.maskercounter]["gain"]-self.maskergain)*self.gainweight>self.maskerdiff) or (abs(self.currentdoa - self.msgdict["doa"])>self.doadiff):
                self.maskergain1 = self.msgdict['predictions'][self.maskerindex1]["gain"]
                self.maskergain2 = self.msgdict['predictions'][self.maskerindex2]["gain"]
                self.maskergain3 = self.msgdict['predictions'][self.maskerindex3]["gain"]
                self.maskergain4 = self.msgdict['predictions'][self.maskerindex4]["gain"]
                # if self.maskergain (set in previous step) less than gainlimit (set at 1000)
                if self.maskergain1*self.gainweight < self.gainlimit:
                    print("self.maskergain1 = {}".format(self.maskergain1))
                    # calculate amssgain
                    amssgain = interpolate(self.msgdict['predictions'][self.maskerindex1]["id"],self.maskergain) + self.insitucompensate(numofspeakers,optimaldistance)
                    # set amssgaint to min 45 and max 83
                    if amssgain >45 and amssgain <= 83:
                        pass
                    elif amssgain >83:
                        amssgain = 83
                    elif amssgain <46:
                        amssgain = 46
                    self.weightedgain1 = calibgains[self.msgdict['predictions'][self.maskerindex1]["id"]+'.wav'][str(amssgain)]
                    print("self.weightedgain1 = {}".format(self.weightedgain1))
                else:
                    self.weightedgain1 = self.gainlimit
                self.currentmasker1 = self.msgdict['predictions'][self.maskerindex1]["id"]
                self.currentdoa = self.msgdict["doa"]
                if self.maskergain2*self.gainweight < self.gainlimit:
                    print("self.maskergain2 = {}".format(self.maskergain2))
                    # calculate amssgain
                    amssgain = interpolate(self.msgdict['predictions'][self.maskerindex2]["id"],self.maskergain) + self.insitucompensate(numofspeakers,optimaldistance)
                    # set amssgaint to min 45 and max 83
                    if amssgain >45 and amssgain <= 83:
                        pass
                    elif amssgain >83:
                        amssgain = 83
                    elif amssgain <46:
                        amssgain = 46
                    self.weightedgain2 = calibgains[self.msgdict['predictions'][self.maskerindex2]["id"]+'.wav'][str(amssgain)]
                    print("self.weightedgain2 = {}".format(self.weightedgain2))
                else:
                    self.weightedgain2 = self.gainlimit
                self.currentmasker2 = self.msgdict['predictions'][self.maskerindex2]["id"]
                self.currentdoa = self.msgdict["doa"]
                if self.maskergain3*self.gainweight < self.gainlimit:
                    print("self.maskergain3 = {}".format(self.maskergain3))
                    # calculate amssgain
                    amssgain = interpolate(self.msgdict['predictions'][self.maskerindex3]["id"],self.maskergain) + self.insitucompensate(numofspeakers,optimaldistance)
                    # set amssgaint to min 45 and max 83
                    if amssgain >45 and amssgain <= 83:
                        pass
                    elif amssgain >83:
                        amssgain = 83
                    elif amssgain <46:
                        amssgain = 46
                    self.weightedgain3 = calibgains[self.msgdict['predictions'][self.maskerindex3]["id"]+'.wav'][str(amssgain)]
                    print("self.weightedgain3 = {}".format(self.weightedgain3))
                else:
                    self.weightedgain3 = self.gainlimit
                self.currentmasker3 = self.msgdict['predictions'][self.maskerindex3]["id"]
                self.currentdoa = self.msgdict["doa"]
                if self.maskergain4*self.gainweight < self.gainlimit:
                    print("self.maskergain4 = {}".format(self.maskergain4))
                    # calculate amssgain
                    amssgain = interpolate(self.msgdict['predictions'][self.maskerindex4]["id"],self.maskergain) + self.insitucompensate(numofspeakers,optimaldistance)
                    # set amssgaint to min 45 and max 83
                    if amssgain >45 and amssgain <= 83:
                        pass
                    elif amssgain >83:
                        amssgain = 83
                    elif amssgain <46:
                        amssgain = 46
                    self.weightedgain4 = calibgains[self.msgdict['predictions'][self.maskerindex4]["id"]+'.wav'][str(amssgain)]
                    print("self.weightedgain4 = {}".format(self.weightedgain4))
                else:
                    self.weightedgain4 = self.gainlimit
                self.currentmasker4 = self.msgdict['predictions'][self.maskerindex4]["id"]
                self.currentdoa = self.msgdict["doa"]
        else:
            pass
        try:
            f1, fs1 = sf.read(self.maskerpath + self.currentmasker1 +'.wav')
            f2, fs2 = sf.read(self.maskerpath + self.currentmasker2 +'.wav')
            f3, fs3 = sf.read(self.maskerpath + self.currentmasker3 +'.wav')
            f4, fs4 = sf.read(self.maskerpath + self.currentmasker4 +'.wav')
            print("stream created using {}, {}, {}, and {} with gain: {}, {}, {}, and {} at DOA: {}".format(self.currentmasker1,
                                                                                                            self.currentmasker2,
                                                                                                            self.currentmasker3,
                                                                                                            self.currentmasker4,
                                                                                                            self.weightedgain1,
                                                                                                            self.weightedgain2,
                                                                                                            self.weightedgain3,
                                                                                                            self.weightedgain4,
                                                                                                            self.currentdoa))
            
            #data1 = self.spatialize(f1*self.weightedgain1, self.currentdoa)
            #data2 = self.spatialize(f2*self.weightedgain2, self.currentdoa)
            #data3 = self.spatialize(f3*self.weightedgain2, self.currentdoa)
            #data4 = self.spatialize(f4*self.weightedgain2, self.currentdoa)

            data1 = f1*self.weightedgain1
            data2 = f2*self.weightedgain2
            data3 = f3*self.weightedgain3
            data4 = f4*self.weightedgain4 
            data = np.empty((len(data1),4))
            for length in range(len(data)):
                data[length][0] += data1[length]
                data[length][1] += data2[length]                
                data[length][2] += data3[length]                
                data[length][3] += data4[length]
            print(np.shape(data))
            compGain = math.pow(10,self.insitucompensate(numofspeakers,optimaldistance)/20)
            print('Compensated gain: {} dB'.format(20*math.log10(compGain)))
            while True:
                sd.play(data*compGain, fs1, loop=True)
                if is_key_pressed():
                    break
        except KeyboardInterrupt:
            pass        
    def play2maskers(self):
        self.q = queue.Queue()
        newmasker = None
        newweightedgain = None
        newdoa = None
        numOfMaskers = 2
        self.msgdict = self.msgq
        self.msgqeval = self.msgdict
        #why q2?    
        if not self.q2.empty():
            self.msgdict = self.msgq
            self.ambientspl = self.msgdict["base_spl"]

        if self.msgdict != None: #If there is a prediction
            predictionlist =[]
            uniquepredictionlist = []
            for prediction in self.msgdict['predictions']:
                for indexes in range(7):
                    predictionlist.append(self.msgdict['predictions'][indexes]['rank'])
                    predictionlist.append(self.msgdict['predictions'][indexes]['id'])
                for item in predictionlist:
                    if type(item) == str:
                        if item not in uniquepredictionlist:
                            uniquepredictionlist.append(item)
                            uniquepredictionlist.append(predictionlist.index(item)-1)
            print(uniquepredictionlist)
            self.currentmasker1 = uniquepredictionlist[0]
            self.maskerindex1 = uniquepredictionlist[1]
            self.currentmasker2 = uniquepredictionlist[2]
            print(self.currentmasker2)
            self.maskerindex2 = uniquepredictionlist[3]
            print('top 2 rated maskers = {}, {}'.format(self.currentmasker1, self.currentmasker2))
            print('index of top 2 maskers = {}, {}'.format(self.maskerindex1, self.maskerindex2))
            # if the masker to be played is not self.currentmasker, set self.maskergain to the gain of the masker to be played
            # self.currentmasker is set to bird_00075 by default
            if (self.msgdict['predictions'][self.maskerindex1]["id"] != self.currentmasker) or (self.msgdict['predictions'][self.maskerindex2]["id"] != self.currentmasker) or (abs(self.msgdict['predictions'][self.maskercounter]["gain"]-self.maskergain)*self.gainweight>self.maskerdiff) or (abs(self.currentdoa - self.msgdict["doa"])>self.doadiff):
                self.maskergain1 = self.msgdict['predictions'][self.maskerindex1]["gain"]
                self.maskergain2 = self.msgdict['predictions'][self.maskerindex2]["gain"]
                # if self.maskergain (set in previous step) less than gainlimit (set at 1000)
                if self.maskergain1*self.gainweight < self.gainlimit:
                    print("self.maskergain1 = {}".format(self.maskergain1))
                    # calculate amssgain
                    amssgain = interpolate(self.msgdict['predictions'][self.maskerindex1]["id"],self.maskergain) + self.insitucompensate(numofspeakers,optimaldistance)
                    # set amssgaint to min 45 and max 83
                    if amssgain >45 and amssgain <= 83:
                        pass
                    elif amssgain >83:
                        amssgain = 83
                    elif amssgain <46:
                        amssgain = 46
                    self.weightedgain1 = calibgains[self.msgdict['predictions'][self.maskerindex1]["id"]+'.wav'][str(amssgain)]
                    print("self.weightedgain1 = {}".format(self.weightedgain1))
                else:
                    self.weightedgain1 = self.gainlimit
                self.currentmasker1 = self.msgdict['predictions'][self.maskerindex1]["id"]
                self.currentdoa = self.msgdict["doa"]
                if self.maskergain2*self.gainweight < self.gainlimit:
                    print("self.maskergain2 = {}".format(self.maskergain2))
                    # calculate amssgain
                    amssgain = interpolate(self.msgdict['predictions'][self.maskerindex2]["id"],self.maskergain) + self.insitucompensate(numofspeakers,optimaldistance)
                    # set amssgaint to min 45 and max 83
                    if amssgain >45 and amssgain <= 83:
                        pass
                    elif amssgain >83:
                        amssgain = 83
                    elif amssgain <46:
                        amssgain = 46
                    self.weightedgain2 = calibgains[self.msgdict['predictions'][self.maskerindex2]["id"]+'.wav'][str(amssgain)]
                    print("self.weightedgain2 = {}".format(self.weightedgain2))
                else:
                    self.weightedgain2 = self.gainlimit
                self.currentmasker2 = self.msgdict['predictions'][self.maskerindex2-1]["id"]
                self.currentdoa = self.msgdict["doa"]
        else:
            pass
        try:
            f1, fs1 = sf.read(self.maskerpath + self.currentmasker1 +'.wav')
            f2, fs2 = sf.read(self.maskerpath + self.currentmasker2 +'.wav')
            print("stream created using {} and {} with gain: {} and {} at DOA: {}".format(self.currentmasker1,
                                                                                   self.currentmasker2,
                                                                                   self.weightedgain1,
                                                                                   self.weightedgain2,
                                                                                   self.currentdoa))
            #data1 = self.spatialize(f1*self.weightedgain1, self.currentdoa)
            #data2 = self.spatialize(f2*self.weightedgain2, self.currentdoa)
            data1 = f1*self.weightedgain1
            data2 = f2*self.weightedgain2
            data = np.empty((len(data1),4))
            for length in range(len(data)):
                data[length][0] += data1[length]
                data[length][1] += data1[length]                
                data[length][2] += data2[length]                
                data[length][3] += data2[length]
            print(np.shape(data))
            compGain = math.pow(10,self.insitucompensate(numofspeakers,optimaldistance)/20)
            print('Compensated gain: {} dB'.format(20*math.log10(compGain)))
            sd.play(data*compGain, fs1)
            sd.wait()
        except KeyboardInterrupt:
            pass

    def play2maskerseval(self):
        self.q = queue.Queue()
        newmasker = None
        newweightedgain = None
        newdoa = None
        numOfMaskers = 2
        self.msgdict = self.msgqeval

        #why q2?    
        if not self.q2.empty():
            self.msgdict = self.msgqeval
            self.ambientspl = self.msgdict["base_spl"]
        if self.msgdict != None: #If there is a prediction
            predictionlist =[]
            uniquepredictionlist = []
            for prediction in self.msgdict['predictions']:
                for indexes in range(7):
                    predictionlist.append(self.msgdict['predictions'][indexes]['rank'])
                    predictionlist.append(self.msgdict['predictions'][indexes]['id'])
                for item in predictionlist:
                    if type(item) == str:
                        if item not in uniquepredictionlist:
                            uniquepredictionlist.append(item)
                            uniquepredictionlist.append(predictionlist.index(item)-1)
            print(uniquepredictionlist)
            self.currentmasker1 = uniquepredictionlist[0]
            self.maskerindex1 = uniquepredictionlist[1]
            self.currentmasker2 = uniquepredictionlist[2]
            self.maskerindex2 = uniquepredictionlist[3]
            print('top 2 rated maskers = {}, {}'.format(self.currentmasker1, self.currentmasker2))
            print('index of top 2 maskers = {}, {}'.format(self.maskerindex1, self.maskerindex2))
            # if the masker to be played is not self.currentmasker, set self.maskergain to the gain of the masker to be played
            # self.currentmasker is set to bird_00075 by default
            if (self.msgdict['predictions'][self.maskerindex1]["id"] != self.currentmasker) or (self.msgdict['predictions'][self.maskerindex2]["id"] != self.currentmasker) or (abs(self.msgdict['predictions'][self.maskercounter]["gain"]-self.maskergain)*self.gainweight>self.maskerdiff) or (abs(self.currentdoa - self.msgdict["doa"])>self.doadiff):
                self.maskergain1 = self.msgdict['predictions'][self.maskerindex1]["gain"]
                self.maskergain2 = self.msgdict['predictions'][self.maskerindex2]["gain"]
                # if self.maskergain (set in previous step) less than gainlimit (set at 1000)
                if self.maskergain1*self.gainweight < self.gainlimit:
                    print("self.maskergain1 = {}".format(self.maskergain1))
                    # calculate amssgain
                    amssgain = interpolate(self.msgdict['predictions'][self.maskerindex1]["id"],self.maskergain) + self.insitucompensate(numofspeakers,optimaldistance)
                    # set amssgaint to min 45 and max 83
                    if amssgain >45 and amssgain <= 83:
                        pass
                    elif amssgain >83:
                        amssgain = 83
                    elif amssgain <46:
                        amssgain = 46
                    self.weightedgain1 = calibgains[self.msgdict['predictions'][self.maskerindex1]["id"]+'.wav'][str(amssgain)]
                    print("self.weightedgain1 = {}".format(self.weightedgain1))
                else:
                    self.weightedgain1 = self.gainlimit
                self.currentmasker1 = self.msgdict['predictions'][self.maskerindex1]["id"]
                self.currentdoa = self.msgdict["doa"]
                if self.maskergain2*self.gainweight < self.gainlimit:
                    print("self.maskergain2 = {}".format(self.maskergain2))
                    # calculate amssgain
                    amssgain = interpolate(self.msgdict['predictions'][self.maskerindex2]["id"],self.maskergain) + self.insitucompensate(numofspeakers,optimaldistance)
                    # set amssgaint to min 45 and max 83
                    if amssgain >45 and amssgain <= 83:
                        pass
                    elif amssgain >83:
                        amssgain = 83
                    elif amssgain <46:
                        amssgain = 46
                    self.weightedgain2 = calibgains[self.msgdict['predictions'][self.maskerindex2]["id"]+'.wav'][str(amssgain)]
                    print("self.weightedgain2 = {}".format(self.weightedgain2))
                else:
                    self.weightedgain2 = self.gainlimit
                self.currentmasker2 = self.msgdict['predictions'][self.maskerindex2-1]["id"]
                self.currentdoa = self.msgdict["doa"]
        else:
            pass
        try:
            f1, fs1 = sf.read(self.maskerpath + self.currentmasker1 +'.wav')
            f2, fs2 = sf.read(self.maskerpath + self.currentmasker2 +'.wav')
            print("stream created using {} and {} with gain: {} and {} at DOA: {}".format(self.currentmasker1,
                                                                                   self.currentmasker2,
                                                                                   self.weightedgain1,
                                                                                   self.weightedgain2,
                                                                                   self.currentdoa))
            #data1 = self.spatialize(f1*self.weightedgain1, self.currentdoa)
            #data2 = self.spatialize(f2*self.weightedgain2, self.currentdoa)
            data1 = f1*self.weightedgain1
            data2 = f2*self.weightedgain2
            data = np.empty((len(data1),4))
            for length in range(len(data)):
                data[length][0] += data1[length]
                data[length][1] += data1[length]                
                data[length][2] += data2[length]                
                data[length][3] += data2[length]
            print(np.shape(data))
            compGain = math.pow(10,self.insitucompensate(numofspeakers,optimaldistance)/20)
            print('Compensated gain: {} dB'.format(20*math.log10(compGain)))
            sd.play(data, fs1)
            while True:
                sd.play(data*compGain, fs1, loop=True)
                if is_key_pressed():
                    break
        except KeyboardInterrupt:
            pass

    def playmasker(self):
        self.q = queue.Queue(maxsize=self.buffersize)
        newmasker = None
        newweightedgain = None
        newdoa = None
        self.msgdict = self.msgq
        self.msgqeval = self.msgdict
        #why q2?    
        if not self.q2.empty():
            self.msgdict = self.msgq
            self.ambientspl = self.msgdict["base_spl"]
        
        if self.msgdict != None: #If there is a prediction
            #print("Here")
            print("starting playback again")
            # maskercounter: to get index of the masker from the dictionary, usually 0 for top masker
            print("masker counter=" + str(self.maskercounter))
            # if the masker to be played is not self.currentmasker, set self.maskergain to the gain of the masker to be played
            # self.currentmasker is set to bird_00075 by default
            if (self.msgdict['predictions'][self.maskercounter]["id"] != self.currentmasker) or (abs(self.msgdict['predictions'][self.maskercounter]["gain"]-self.maskergain)*self.gainweight>self.maskerdiff) or (abs(self.currentdoa - self.msgdict["doa"])>self.doadiff):
                self.maskergain = self.msgdict['predictions'][self.maskercounter]["gain"]
                predictionlist= [self.currentmasker, self.maskergain]
                appendlist = ['AMSS', predictionlist]         
                predictiondf.loc[len(predictiondf)] = appendlist
                # if self.maskergain (set in previous step) less than gainlimit (set at 1000)
                if self.maskergain*self.gainweight < self.gainlimit:
                    print("self.maskergain = {}".format(self.maskergain))
                    # print("self.msgdict['predictions'][self.maskercounter]['id']+'.wav' = {}".format(self.msgdict['predictions'][self.maskercounter]["id"]+'.wav'))
                    # print("round(self.ambientspl + 20*math.log10(self.maskergain)) = {}".format(round(self.ambientspl + 20*math.log10(self.maskergain))))
                    # calculate amssgain
                    amssgain = interpolate(self.msgdict['predictions'][self.maskercounter]["id"],self.maskergain) + self.insitucompensate(numofspeakers,optimaldistance)
                    # set amssgaint to min 45 and max 83
                    if amssgain >45 and amssgain <= 83:
                        pass
                    elif amssgain >83:
                        amssgain = 83
                    elif amssgain <46:
                        amssgain = 46
                    self.weightedgain = calibgains[self.msgdict['predictions'][self.maskercounter]["id"]+'.wav'][str(amssgain)]
                    #print("I'm Here")
                    print("AMSS Gain: {}".format(amssgain))
                    print("self.weightedgain = {}".format(self.weightedgain))
                else:
                    self.weightedgain = self.gainlimit
                self.currentmasker = self.msgdict['predictions'][self.maskercounter]["id"]
                self.currentdoa = self.msgdict["doa"]
                #print("Here")
                # self.currentmaskerorig = self.currentmasker
        else:
            pass
        try:
            # open currentmasker with soundfile
            with sf.SoundFile(self.maskerpath + (self.currentmasker if not MEOW else "meow") +'.wav') as f:
                print("stream created using {} with gain: {} at DOA: {}".format(self.currentmasker,self.weightedgain,self.currentdoa))
                stream = sd.OutputStream(
                    samplerate=f.samplerate, blocksize=self.blocksize,
                    device=7, channels=4,
                    callback=self.streamcallback, finished_callback=self.event.set)
                with stream:
                    timeout = self.blocksize * self.buffersize / f.samplerate * 1000
                    for _ in range(int(self.buffersize)):
                        data = self.spatialize(f.read(self.blocksize, always_2d=True)*self.weightedgain, self.currentdoa)
                        if not len(data):
                            break
                        self.q.put_nowait(data)  # Pre-fill queue
                        # print("queue pre-filled")
                    while len(data):
                        if not self.q2.empty():
                            self.msgdict = self.q2.get_nowait()
                            
                            if (self.msgdict['predictions'][0]["id"] != self.currentmaskerorig) or (abs(self.msgdict['predictions'][0]["gain"]-self.maskergainorig)*self.gainweight>self.maskerdiff) or (abs(self.currentdoa - self.msgdict["doa"])>self.doadiff):
                                newgain = self.msgdict['predictions'][0]["gain"]
                                newamssgain = interpolate(self.msgdict['predictions'][0]["id"],newgain) + self.insitucompensate(numofspeakers,optimaldistance)
                                print("newamssgain = {}".format(newamssgain))
                                if newamssgain >45 and newamssgain <= 83:
                                    pass
                                elif newamssgain >83:
                                    newamssgain = 83
                                elif newamssgain <46:
                                    newamssgain = 46
                                newweightedgain = calibgains[self.msgdict['predictions'][self.maskercounter]["id"]+'.wav'][str(newamssgain)]
                                
                                newmasker = self.msgdict['predictions'][0]["id"]
                                self.maskercounter=0
                                print("masker counter=" + str(self.maskercounter))
                                newdoa = self.msgdict['doa']
                            else:
                                pass
                        else:
                            pass
                        if (newmasker != self.currentmasker and newmasker != None) or (newweightedgain != None and abs(newweightedgain-self.weightedgain)>self.maskerdiff) or (newdoa!=None and abs(self.currentdoa - newdoa)>self.doadiff):
                            if MEOW:
                                newmasker = "meow"
                            fnew = sf.SoundFile(self.maskerpath + newmasker + '.wav')
                            print("Changing - Playing: {} with gain:{} at DOA: {}".format(newmasker,newweightedgain,newdoa))
                            for i in range(self.fadelength):
                                track1 = self.spatialize(f.read(self.blocksize, always_2d=True)*(1-(i/self.fadelength))*self.weightedgain, self.currentdoa)
                                track2 = self.spatialize(fnew.read(self.blocksize, always_2d=True)*(i/self.fadelength)*newweightedgain, newdoa)
                                if len(track1) < len(track2) and not self.q.empty():
                                    track1cut = np.zeros((self.blocksize,4))
                                    track1cut[:len(track1)] = track1
                                    track1cut[len(track1):].fill(0)
                                    print("track ending")
                                else:
                                    track1cut = track1
                                data = track1cut + track2
                                self.q.put(data, timeout=timeout)
                            f = fnew
                            self.currentmasker = newmasker
                            self.currentmaskerorig = self.currentmasker
                            self.weightedgain = newweightedgain
                            self.maskergainorig=newgain
                            self.currentdoa = newdoa

                            # time.sleep(10)
                        else:
                            # print("reading data")
                            #data = self.spatialize(f.read(self.blocksize, always_2d=True)*self.weightedgain,self.currentdoa)
                            #self.q.put(data, timeout=timeout)
                            compGain = math.pow(10,self.insitucompensate(numofspeakers,optimaldistance)/20)
                            print('Compensated gain: {} dB'.format(20*math.log10(compGain)))
                            data = f.read(self.blocksize, always_2d=True)*self.weightedgain*compGain
                            self.q.put(data, timeout=timeout)
                    self.event.wait()  # Wait until playback is finished
                if self.maskercounter<4 and varymaskers== True:
                    self.maskercounter+=1
                else:
                    self.maskercounter=0
                print("masker counter=" + str(self.maskercounter))
                print("read done")
        except KeyboardInterrupt:
            pass
        
    def playmaskereval(self):
        self.q = queue.Queue(maxsize=self.buffersize)
        newmasker = None
        newweightedgain = None
        newdoa = None
        self.msgdict = self.msgqeval
        
        #why q2?    
        if not self.q2.empty():
            self.msgdict = self.msgqeval
            self.ambientspl = self.msgdict["base_spl"]

        if self.msgdict != None: #If there is a prediction
            print("starting playback again")
            # maskercounter: to get index of the master from the dictionary, usually 0 for top masker
            print("masker counter=" + str(self.maskercounter))
            # if the masker to be played is not self.currentmasker, set self.maskergain to the gain of the masker to be played
            # self.currentmasker is set to bird_00075 by default
            if (self.msgdict['predictions'][self.maskercounter]["id"] != self.currentmasker) or (abs(self.msgdict['predictions'][self.maskercounter]["gain"]-self.maskergain)*self.gainweight>self.maskerdiff) or (abs(self.currentdoa - self.msgdict["doa"])>self.doadiff):
                self.maskergain = self.msgdict['predictions'][self.maskercounter]["gain"]
                # if self.maskergain (set in previous step) less than gainlimit (set at 1000)
                if self.maskergain*self.gainweight < self.gainlimit:
                    print("self.maskergain = {}".format(self.maskergain))
                    # print("self.msgdict['predictions'][self.maskercounter]['id']+'.wav' = {}".format(self.msgdict['predictions'][self.maskercounter]["id"]+'.wav'))
                    # print("round(self.ambientspl + 20*math.log10(self.maskergain)) = {}".format(round(self.ambientspl + 20*math.log10(self.maskergain))))
                    # calculate amssgain
                    amssgain = interpolate(self.msgdict['predictions'][self.maskercounter]["id"],self.maskergain) + self.insitucompensate(numofspeakers,optimaldistance)
                    # set amssgaint to min 45 and max 83
                    if amssgain >45 and amssgain <= 83:
                        pass
                    elif amssgain >83:
                        amssgain = 83
                    elif amssgain <46:
                        amssgain = 46
                    self.weightedgain = calibgains[self.msgdict['predictions'][self.maskercounter]["id"]+'.wav'][str(amssgain)]
                    print("self.weightedgain = {}".format(self.weightedgain))
                else:
                    self.weightedgain = self.gainlimit
                self.currentmasker = self.msgdict['predictions'][self.maskercounter]["id"]
                self.currentdoa = self.msgdict["doa"]
                # self.currentmaskerorig = self.currentmasker
        else:
            pass
        try:
            f, fs = sf.read(self.maskerpath + self.currentmasker +'.wav')
            data = self.spatialize(f*self.weightedgain, self.currentdoa)
            while True:
                print(self.currentmasker)
                print("Playing at self.weightedgain = {}".format(self.weightedgain))
                compGain = math.pow(10,self.insitucompensate(numofspeakers,optimaldistance)/20)
                print('Compensated gain: {} dB'.format(20*math.log10(compGain)))
                sd.play(f*self.weightedgain*compGain, fs, loop=True)
                if is_key_pressed():
                    break
        except KeyboardInterrupt:
            pass

        except KeyboardInterrupt:
            pass

    def streamcallback(self, outdata, frames, time, status):
        data = np.zeros((self.blocksize,1))
        assert frames == self.blocksize
        # if status.output_underflow:
        #     print('Output underflow: increase blocksize?', file=sys.stderr)
        #     raise sd.CallbackAbort
        assert not status
        try:
            data = self.q.get_nowait()
        except queue.Empty as e:
            print('Buffer is empty: increase buffersize?', file=sys.stderr)
            raise sd.CallbackAbort from e
        if len(data) < len(outdata) and not self.q.empty():
            outdata[:len(data)] = data
            outdata[len(data):].fill(0)
            print("track ending")
            raise sd.CallbackStop
        else:
            outdata[:] = data
    def streamcallbackeval(self, outdata, frames, time, status):
        data = np.zeros((self.blocksize,1))
        assert frames == self.blocksize
        # if status.output_underflow:
        #     print('Output underflow: increase blocksize?', file=sys.stderr)
        #     raise sd.CallbackAbort
        assert not status
        try:
            data = self.q.get_nowait()
        except queue.Empty as e:
            print('Buffer is empty: increase buffersize?', file=sys.stderr)
            raise sd.CallbackAbort from e
        if len(data) < len(outdata) and not self.q.empty():
            outdata[:len(data)] = data
            outdata[len(data):].fill(0)
        else:
            outdata[:] = data
       
    # save terminal settings

    def soundlooper(self):
        #wait for predictions to load first
        notprinted_flag = True
        while self.msgq == None:
            if notprinted_flag:
                print("Waiting for predictions")
                notprinted_flag = False
                
        print('predictions loaded, press any key to proceed')
        while True:
            if is_key_pressed():
                break
        
        nexttrack, nexttrackfs= sf.read(self.maskerpath + 'voiceNextTrack.wav')
        evaluation, evaluationfs = sf.read(self.maskerpath + 'voiceEval.wav')
        end, endfs = sf.read(self.maskerpath + 'voiceEnd.wav')
        for name in orderlist:
            order = 1
            print(order)
            order += 1
            if name == 'amss1':
                print(self.nexttrackmsg)
                sd.play(nexttrack*self.voicePromptGain, nexttrackfs)
                sd.wait()
                self.playmasker()
                print(self.beforeevaluationmsg)
                sd.play(evaluation*self.voicePromptGain, evaluationfs)
                sd.wait()
                print(self.duringevaluationmsg)
                self.playmaskereval()
            elif name == 'amss2':
                print(self.nexttrackmsg)
                sd.play(nexttrack*self.voicePromptGain, nexttrackfs)
                sd.wait()
                self.play2maskers()
                print(self.beforeevaluationmsg)
                sd.play(evaluation*self.voicePromptGain, evaluationfs)
                sd.wait()
                print(self.duringevaluationmsg)
                self.play2maskerseval()
            elif name == 'amss4':
                print(self.nexttrackmsg)
                sd.play(nexttrack*self.voicePromptGain, nexttrackfs)
                sd.wait()
                self.play4maskers()
                print(self.beforeevaluationmsg)
                sd.play(evaluation*self.voicePromptGain, evaluationfs)
                sd.wait()
                print(self.duringevaluationmsg)
                self.play4maskerseval()
            else:
                print(self.nexttrackmsg)
                sd.play(nexttrack*self.voicePromptGain , nexttrackfs)
                sd.wait()                
                self.playfixedmasker(name)
                print(self.beforeevaluationmsg)
                sd.play(evaluation*self.voicePromptGain, evaluationfs)
                sd.wait()
                print(self.duringevaluationmsg)
                self.playfixedmaskereval(name)
            predictiondf.to_csv(participantfilepath + f'participant_00{participantid}_predictions.csv')
        print(self.endmsg)
        sd.play(end*self.voicePromptGain, endfs)
        sd.wait()

    def mqttlooper(self):
        while True:
            self.MQTTClient.subscribeAsync(self.mqttTOPIC, 0,messageCallback = self.msgcallback)
            time.sleep(10)
   
def is_key_pressed():
    tty.setraw(sys.stdin.fileno())
    key = sys.stdin.read(1)
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key != ''

sp = soundplayer()

sp.MQTTClient.connectAsync()
print("connected")

participantid = input('Enter the id of the participant (3 digits): ')
participantfilepath = '/home/pi/mqtt_client/ParticipantOrder/'
data = pd.read_csv(participantfilepath + f'participant_00{participantid}.csv')
print(participantid)
orderlist = [data.columns[0]]
for i in data.iloc[:, 0]:
    orderlist.append(i)
print(orderlist)
predictiondf = pd.DataFrame(columns = ['AMSS', 'Predictions'])

settings = termios.tcgetattr(sys.stdin)

mqtt_thread = threading.Thread(
        target=sp.mqttlooper,
        name="mqtt",
        args=(),
        daemon=True,
    )

soundlooper_thread = threading.Thread(
        target=sp.soundlooper,
        name="soundlooper",
        args=(),
        daemon=True,
    )

mqtt_thread.start()
soundlooper_thread.start()
soundlooper_thread.join()
mqtt_thread.join()

# sp.MQTTClient.subscribeAsync(sp.mqttTOPIC, 0,messageCallback = sp.msgcallback)
# sp.playmasker()
