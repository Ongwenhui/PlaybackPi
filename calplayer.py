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
import argparse
import csv

# Create the parser
my_parser = argparse.ArgumentParser(description='choose track to play')

# Add the arguments
my_parser.add_argument('Track',
                       metavar='track',
                       type=str,
                       help='track to play')
my_parser.add_argument('LEQ',
                       metavar='leq',
                       type=str,
                       help='leq to play, accepts int only')
my_parser.add_argument('speakernum',
                       metavar='speakernum',
                       type=int,
                       help='number of speakers to play, 1-4 only')

args = my_parser.parse_args()

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

calibgains = readcsv('/home/pi/maskers/Calibrations_final_speaker.csv')
# print(calibgains)
LOCATION_ID = 'ntu-gazebo01'

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
        self.currentdoa = 0
        self.MQTTClient = AWSIoTPyMQTT.AWSIoTMQTTClient(self.mqttCLIENT_ID)
        self.MQTTClient.configureEndpoint(self.mqttENDPOINT, 8883)
        self.MQTTClient.configureCredentials(self.mqttPATH_TO_AMAZON_ROOT_CA_1, self.mqttPATH_TO_PRIVATE_KEY, self.mqttPATH_TO_CERTIFICATE)
        self.msgdict = {'predictions': [{'rank': 1, 'id': 'bird_00075', 'gain': 0.01793866604566574, 'score': 0.47396957874298096}, {'rank': 2, 'id': 'bird_00075', 'gain': 0.020203232765197754, 'score': 0.47391098737716675}, {'rank': 3, 'id': 'bird_00075', 'gain': 0.02149977907538414, 'score': 0.47387757897377014}, {'rank': 4, 'id': 'bird_00069', 'gain': 0.05129025876522064, 'score': 0.4719516634941101}, {'rank': 5, 'id': 'bird_00075', 'gain': 0.10646381229162216, 'score': 0.47165820002555847}, {'rank': 6, 'id': 'bird_00069', 'gain': 0.10134433209896088, 'score': 0.4705403745174408}, {'rank': 7, 'id': 'bird_00025', 'gain': 0.0057005020789802074, 'score': 0.470207154750824}, {'rank': 8, 'id': 'bird_00069', 'gain': 0.15140660107135773, 'score': 0.46911484003067017}, {'rank': 9, 'id': 'bird_00025', 'gain': 0.08437956869602203, 'score': 0.46776485443115234}, {'rank': 10, 'id': 'bird_00071', 'gain': 0.06381088495254517, 'score': 0.4665457308292389}, {'rank': 11, 'id': 'bird_00069', 'gain': 0.25197258591651917, 'score': 0.46620792150497437}, {'rank': 12, 'id': 'bird_00046', 'gain': 0.07355550676584244, 'score': 0.46558114886283875}], 'base_score': 0.33999258279800415, 'doa': self.currentdoa, 'from': 'ntu-gazebo01', 'timestamp': 1654067860.26, 'base_spl': 68.10846120156562}
        self.currentmasker = args.Track
        self.maskerpath = "/home/pi/maskers/"
        self.maskergain = 1
        self.gainweight = 1
        self.maskerdiff =0.5
        self.gainlimit = 1000
        self.alvingain = calibgains[args.Track+'.wav'][args.LEQ]
        self.buffersize = 20
        self.blocksize = 4096
        self.q = queue.Queue(maxsize=self.buffersize)
        self.q2 =queue.Queue()
        self.event = threading.Event()
        self.fadelength = 80
        self.maskercounter = 0
        self.currentmaskerorig = "bird_00075"
        self.maskergainorig = 1
        self.doadiff = 20


    def spatialize(self, masker, speakernum):

    #             0 deg
    #     [LF]----------[RF]
    #     |       ^       |
    #     |     [UMA]     |
    #     |               |
    #     |               |
    #     |               |
    #     [LB]----------[RB]
    
            
        masker = np.squeeze(masker)
        
        
        lf = 0
        lb = 0
        rb = 0
        rf = 0

        if speakernum == 1:
            lf = 1
        elif speakernum == 2:
            # lf = 1
            lb = 1
        elif speakernum == 3:
            # lf = 1
            # lb = 1
            rb = 1
        elif speakernum == 4:
            lf = 1
            lb = 1
            rb = 1
            rf = 1

        # lf = 0
        # lb = 0
        # rb = 0
        # rf = 0

        
        gains = np.array([rb, lb, lf, rf])
        
        # if normalize:
        #     gains = gains / np.sqrt(1 + 2*k*k)
    
        masker4c = masker[:, None] * gains[None, :] # (n_samples, 4)
        
        return masker4c        

    # def msgcallback(self, client, userdata, message):
    #     incomingmsg=json.loads(message.payload.decode('utf-8'))
    #     self.q2.put_nowait(incomingmsg)
    #     # print (incomingmsg)
    #     #print(msgdict['predictions'])
    #     print("Recommended Masker is: " + str(incomingmsg['predictions'][0]["id"]))
    #     print("Recommended Gain is: " + str(self.gainweight*incomingmsg['predictions'][0]["gain"]))
    #     # data, fs = sf.read(msgdict['predictions'][0]["id"]+'.wav', dtype='float32')  
    #     # sd.play(data, fs, device=1)
    def playmasker(self):
        self.q = queue.Queue(maxsize=self.buffersize)
        # newmasker = None
        # newweightedgain = None
        # newdoa = None
        # self.q = queue.Queue(maxsize=self.buffersize)
        # print(self.msgdict)
        # if not self.q2.empty():
        #     self.msgdict = self.q2.get_nowait()
        # if self.msgdict != None:
        #     print("starting playback again")
        #     print("masker counter=" + str(self.maskercounter))
        #     if (self.msgdict['predictions'][self.maskercounter]["id"] != self.currentmasker) or (abs(self.msgdict['predictions'][self.maskercounter]["gain"]-self.maskergain)*self.gainweight>self.maskerdiff) or (abs(self.currentdoa - self.msgdict["doa"])>self.doadiff):
        #         self.maskergain = self.msgdict['predictions'][self.maskercounter]["gain"]
        #         if self.maskergain*self.gainweight < self.gainlimit:
        #             self.weightedgain = self.maskergain*self.gainweight
        #         else:
        #             self.weightedgain = self.gainlimit
        #         self.currentmasker = self.msgdict['predictions'][self.maskercounter]["id"]
        #         self.currentdoa = self.msgdict["doa"]
        #         # self.currentmaskerorig = self.currentmasker
        # else:
        #     pass
        try:
            with sf.SoundFile(self.maskerpath + self.currentmasker+'.wav') as f:
                print("stream created using {} with gain: {} (LEQ = {}, speakers = {})".format(self.currentmasker,self.alvingain,args.LEQ, args.speakernum))
                stream = sd.OutputStream(
                    samplerate=f.samplerate, blocksize=self.blocksize,
                    device=7, channels=4,
                    callback=self.streamcallback, finished_callback=self.event.set)
                with stream:
                    timeout = self.blocksize * self.buffersize / f.samplerate
                    for _ in range(int(self.buffersize)):
                        data = self.spatialize(f.read(self.blocksize, always_2d=True)*self.alvingain, args.speakernum)
                        if not len(data):
                            break
                        self.q.put_nowait(data)  # Pre-fill queue
                        # print("queue pre-filled")
                    while len(data):
                #         if not self.q2.empty():
                #             self.msgdict = self.q2.get_nowait()
                            
                #             if (self.msgdict['predictions'][0]["id"] != self.currentmaskerorig) or (abs(self.msgdict['predictions'][0]["gain"]-self.maskergainorig)*self.gainweight>self.maskerdiff) or (abs(self.currentdoa - self.msgdict["doa"])>self.doadiff):
                #                 newgain = self.msgdict['predictions'][0]["gain"]
                #                 if newgain*self.gainweight < self.gainlimit:
                #                     newweightedgain = newgain*self.gainweight
                #                 else:
                #                     newweightedgain = self.gainlimit
                #                 newmasker = self.msgdict['predictions'][0]["id"]
                #                 self.maskercounter=0
                #                 print("masker counter=" + str(self.maskercounter))
                #                 newdoa = self.msgdict['doa']
                #             else:
                #                 pass
                #         else:
                #             pass
                #         if (newmasker != self.currentmasker and newmasker != None) or (newweightedgain != None and abs(newweightedgain-self.weightedgain)>self.maskerdiff) or (newdoa!=None and abs(self.currentdoa - newdoa)>self.doadiff):
                #             fnew = sf.SoundFile(self.maskerpath + newmasker + '.wav')
                #             print("Changing - Playing: {} with gain:{} at DOA: {}".format(newmasker,newweightedgain,newdoa))
                #             for i in range(self.fadelength):
                #                 track1 = self.spatialize(f.read(self.blocksize, always_2d=True)*(1-(i/self.fadelength))*self.weightedgain, self.currentdoa)
                #                 track2 = self.spatialize(fnew.read(self.blocksize, always_2d=True)*(i/self.fadelength)*newweightedgain, newdoa)
                #                 if len(track1) < len(track2) and not self.q.empty():
                #                     track1cut = np.zeros((self.blocksize,4))
                #                     track1cut[:len(track1)] = track1
                #                     track1cut[len(track1):].fill(0)
                #                     print("track ending")
                #                 else:
                #                     track1cut = track1
                #                 data = track1cut + track2
                #                 self.q.put(data, timeout=timeout)
                #             f = fnew
                #             self.currentmasker = newmasker
                #             self.currentmaskerorig = self.currentmasker
                #             self.weightedgain = newweightedgain
                #             self.maskergainorig=newgain
                #             self.currentdoa = newdoa

                #             # time.sleep(10)
                        # else:
                            # print("reading data")
                        data = self.spatialize(f.read(self.blocksize, always_2d=True)*self.alvingain,args.speakernum)
                        self.q.put(data, timeout=timeout)
                    self.event.wait()  # Wait until playback is finished
                # if self.maskercounter<4:
                #     self.maskercounter+=1
                # else:
                #     self.maskercounter=0
                # print("masker counter=" + str(self.maskercounter))
                # print("read done")
        except KeyboardInterrupt:
            exit
            #     self.data, self.fs = sf.read(self.maskerpath + self.msgdict['predictions'][0]["id"]+'.wav', dtype='float32')
                 
            #     sd.play((self.data)*(self.weightedgain), self.fs, device=1,loop = True)
            #     # for item in self.data:
            #     #     #print("checking")
            #     #     if abs(item) > 1:
            #     #         print (item)
            #     self.currentmasker = self.msgdict['predictions'][0]["id"]
            #     print("Changing - Playing: "+ str(self.currentmasker)+" with gain: " +str(self.weightedgain))
            #     time.sleep(10)
                
            # else:
            #     #print("Continuing to play: "+ str(self.currentmasker)+" with gain: " +str(self.gainweight*self.maskergain))
            #     pass
        # else:
        #     pass
    def streamcallback(self, outdata, frames, time, status):
        data = np.zeros((self.blocksize,1))
        assert frames == self.blocksize
        if status.output_underflow:
            print('Output underflow: increase blocksize?', file=sys.stderr)
            raise sd.CallbackAbort
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
            # try:
            #     while True:
            #         q.get_nowait()
            # except Empty:
            #     pass
            raise sd.CallbackStop
        else:
            outdata[:] = data
    # def soundplayerstream(maskerpath,inputtextdata= ""):

    #     self.q = queue.Queue(maxsize=buffersize)
    #     print("q is clear")
    #     while self.msgdict == None and inputtextdata =="":
    #         pass
    #     try:
    #         with sf.SoundFile(maskerpath + file1) as f:
    #             stream = sd.OutputStream(
    #                 samplerate=f.samplerate, blocksize=blocksize,
    #                 device=7, channels=f.channels,
    #                 callback=callback, finished_callback=event.set)
    #             with stream:
    #                 timeout = blocksize * buffersize / f.samplerate
    #                 if inputtextdata == "":
    #                     inputtextdata = self.q2.get_nowait()
    #                 q3.queue.clear()
    #                 q3.put_nowait(inputtextdata)
    #                 fadelength = 80

    #                 if inputtextdata == "file1":
    #                     whichfile = file1
    #                 elif inputtextdata == "file2":
    #                     whichfile = file2

    #                 f = sf.SoundFile(maskerpath + whichfile)
    #                 for _ in range(int(buffersize/2)):
    #                     data = f.read(blocksize, always_2d=True)
    #                     if not len(data):
    #                         break
    #                     q.put_nowait(data)  # Pre-fill queue
    #                 while len(data):
    #                     if not self.q2.empty():
    #                         inputtextdatanew = self.q2.get_nowait()
    #                         print("inputtextdatanew =" + inputtextdatanew)
    #                         q3.queue.clear()
    #                         q3.put_nowait(inputtextdatanew)
    #                         print("putting " + inputtextdatanew + " into q3")
    #                     else:
    #                         inputtextdatanew = ""
    #                     if inputtextdatanew == "file1" and inputtextdatanew != inputtextdata:
    #                         fnew = sf.SoundFile(maskerpath + file1)
    #                         for i in range(fadelength):
    #                             data = f.read(blocksize, always_2d=True)*(1-(i/fadelength)) + fnew.read(blocksize, always_2d=True)*(i/fadelength)
    #                             q.put(data, timeout=timeout)
    #                         f = fnew
    #                         inputtextdata = inputtextdatanew
    #                     elif inputtextdatanew == "file2" and inputtextdatanew != inputtextdata:
    #                         fnew = sf.SoundFile(maskerpath + file2)
    #                         for i in range(fadelength):
    #                             data = f.read(blocksize, always_2d=True)*(1-(i/fadelength)) + fnew.read(blocksize, always_2d=True)*(i/fadelength)
    #                             q.put(data, timeout=timeout)
    #                         f = fnew
    #                         inputtextdata = inputtextdatanew
    #                     else:
    #                         data = f.read(blocksize, always_2d=True)
    #                         q.put(data, timeout=timeout)
    #                 event.wait()  # Wait until playback is finished
    #             print("read done")
    #     except KeyboardInterrupt:
    #         exit
    def soundlooper(self):
        while True:
            self.playmasker()
    # def mqttlooper(self):
    #     while True:
    #         self.MQTTClient.subscribeAsync(self.mqttTOPIC, 0,messageCallback = self.msgcallback)
    #         time.sleep(10)




sp = soundplayer()

# sp.MQTTClient.connectAsync()
# print("connected")

# mqtt_thread = threading.Thread(
#         target=sp.mqttlooper,
#         name="mqtt",
#         args=(),
#         daemon=True,
#     )

soundlooper_thread = threading.Thread(
        target=sp.soundlooper,
        name="soundlooper",
        args=(),
        daemon=True,
    )

# mqtt_thread.start()
soundlooper_thread.start()
soundlooper_thread.join()
# mqtt_thread.join()

# sp.MQTTClient.subscribeAsync(sp.mqttTOPIC, 0,messageCallback = sp.msgcallback)
# sp.playmasker()