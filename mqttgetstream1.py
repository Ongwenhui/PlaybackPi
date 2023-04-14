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


# mqttENDPOINT = "a5i03kombapo4-ats.iot.ap-southeast-1.amazonaws.com"
# mqttCLIENT_ID = "AIMEGET"
# mqttcertfolder = "/home/pi/mqtt_client/certs/"
# mqttPATH_TO_CERTIFICATE = mqttcertfolder + "c86008d5f6f3eb115159777ba9da6c0b97bfdf2309c15020c8d1d2747e4f6bdc-certificate.pem.crt"
# mqttPATH_TO_PRIVATE_KEY = mqttcertfolder + "c86008d5f6f3eb115159777ba9da6c0b97bfdf2309c15020c8d1d2747e4f6bdc-private.pem.key"
# mqttPATH_TO_AMAZON_ROOT_CA_1 = mqttcertfolder + "AmazonRootCA1.pem"
# mqttTOPIC = "amss/prediction"
# mqttRANGE = 20

class soundplayer:
    def __init__(self):
        self.mqttENDPOINT="a5i03kombapo4-ats.iot.ap-southeast-1.amazonaws.com"
        self.mqttCLIENT_ID= "AIMEGET"
        self.mqttcertfolder="/home/pi/mqtt_client/certs/"
        self.mqttPATH_TO_CERTIFICATE = self.mqttcertfolder + "c86008d5f6f3eb115159777ba9da6c0b97bfdf2309c15020c8d1d2747e4f6bdc-certificate.pem.crt"
        self.mqttPATH_TO_AMAZON_ROOT_CA_1 = self.mqttcertfolder + "AmazonRootCA1.pem"
        self.mqttPATH_TO_PRIVATE_KEY=self.mqttcertfolder + "c86008d5f6f3eb115159777ba9da6c0b97bfdf2309c15020c8d1d2747e4f6bdc-private.pem.key"
        self.mqttTOPIC="amss/prediction"
        self.mqttRANGE=20
        self.MQTTClient = AWSIoTPyMQTT.AWSIoTMQTTClient(self.mqttCLIENT_ID)
        self.MQTTClient.configureEndpoint(self.mqttENDPOINT, 8883)
        self.MQTTClient.configureCredentials(self.mqttPATH_TO_AMAZON_ROOT_CA_1, self.mqttPATH_TO_PRIVATE_KEY, self.mqttPATH_TO_CERTIFICATE)
        self.msgdict = None
        self.currentmasker = "bird_00075"
        self.maskerpath = "/home/pi/maskers/"
        self.maskergain = 1
        self.gainweight = 40
        self.maskerdiff =0.5
        self.gainlimit = 2
        self.weightedgain = 1
        self.buffersize = 20
        self.blocksize = 4096
        self.q = queue.Queue(maxsize=self.buffersize)
        self.q2 =queue.Queue()
        self.event = threading.Event()
        self.fadelength = 80
        self.maskercounter = 0
        self.currentmaskerorig = "bird_00075"
        self.maskergainorig = 1
        

    def msgcallback(self, client, userdata, message):
        incomingmsg=json.loads(message.payload.decode('utf-8'))
        self.q2.put_nowait(incomingmsg)
        # print (incomingmsg)
        #print(msgdict['predictions'])
        print("Recommended Masker is: " + str(incomingmsg['predictions'][0]["id"]))
        print("Recommended Gain is: " + str(self.gainweight*incomingmsg['predictions'][0]["gain"]))
        # data, fs = sf.read(msgdict['predictions'][0]["id"]+'.wav', dtype='float32')  
        # sd.play(data, fs, device=1)
    def playmasker(self):
        newmasker = None
        newweightedgain = None
        self.q = queue.Queue(maxsize=self.buffersize)
        print(self.msgdict)
        if not self.q2.empty():
            self.msgdict = self.q2.get_nowait()
        if self.msgdict != None:
            print("starting playback again")
            print("masker counter=" + str(self.maskercounter))
            if (self.msgdict['predictions'][self.maskercounter]["id"] != self.currentmasker) or (abs(self.msgdict['predictions'][self.maskercounter]["gain"]-self.maskergain)*self.gainweight>self.maskerdiff):
                self.maskergain = self.msgdict['predictions'][self.maskercounter]["gain"]
                if self.maskergain*self.gainweight < self.gainlimit:
                    self.weightedgain = self.maskergain*self.gainweight
                else:
                    self.weightedgain = self.gainlimit
                self.currentmasker = self.msgdict['predictions'][self.maskercounter]["id"]
                # self.currentmaskerorig = self.currentmasker
        else:
            pass
        try:
            with sf.SoundFile(self.maskerpath + self.currentmasker+'.wav') as f:
                print("stream created using " + self.currentmasker +" with gain: " + str(self.weightedgain))
                stream = sd.OutputStream(
                    samplerate=f.samplerate, blocksize=self.blocksize,
                    device=7, channels=f.channels,
                    callback=self.streamcallback, finished_callback=self.event.set)
                with stream:
                    timeout = self.blocksize * self.buffersize / f.samplerate
                    for _ in range(int(self.buffersize)):
                        data = f.read(self.blocksize, always_2d=True)*self.weightedgain
                        if not len(data):
                            break
                        self.q.put_nowait(data)  # Pre-fill queue
                        # print("queue pre-filled")
                    while len(data):
                        if not self.q2.empty():
                            self.msgdict = self.q2.get_nowait()
                            
                            if (self.msgdict['predictions'][0]["id"] != self.currentmaskerorig) or (abs(self.msgdict['predictions'][0]["gain"]-self.maskergainorig)*self.gainweight>self.maskerdiff):
                                newgain = self.msgdict['predictions'][0]["gain"]
                                if newgain*self.gainweight < self.gainlimit:
                                    newweightedgain = newgain*self.gainweight
                                else:
                                    newweightedgain = self.gainlimit
                                newmasker = self.msgdict['predictions'][0]["id"]
                                self.maskercounter=0
                                print("masker counter=" + str(self.maskercounter))
                            else:
                                pass
                        else:
                            pass
                        if (newmasker != self.currentmasker and newmasker != None) or (newweightedgain != None and abs(newweightedgain-self.weightedgain)>self.maskerdiff):
                            fnew = sf.SoundFile(self.maskerpath + newmasker + '.wav')
                            print("Changing - Playing: "+ str(newmasker)+" with gain: " +str(newweightedgain))
                            for i in range(self.fadelength):
                                track1 = f.read(self.blocksize, always_2d=True)*(1-(i/self.fadelength))*self.weightedgain
                                track2 = fnew.read(self.blocksize, always_2d=True)*(i/self.fadelength)*newweightedgain
                                if len(track1) < len(track2) and not self.q.empty():
                                    track1cut = np.zeros((self.blocksize,1))
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

                            # time.sleep(10)
                        else:
                            # print("reading data")
                            data = f.read(self.blocksize, always_2d=True)*self.weightedgain
                            self.q.put(data, timeout=timeout)
                    self.event.wait()  # Wait until playback is finished
                if self.maskercounter<4:
                    self.maskercounter+=1
                else:
                    self.maskercounter=0
                print("masker counter=" + str(self.maskercounter))
                print("read done")
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
    def mqttlooper(self):
        while True:
            self.MQTTClient.subscribeAsync(self.mqttTOPIC, 0,messageCallback = self.msgcallback)
            time.sleep(10)




sp = soundplayer()

sp.MQTTClient.connectAsync()
print("connected")

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
# mqtt_thread.join()

# sp.MQTTClient.subscribeAsync(sp.mqttTOPIC, 0,messageCallback = sp.msgcallback)
# sp.playmasker()