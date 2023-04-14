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

<<<<<<< HEAD
LOCATION_ID = 'ntu-gazebo01'

=======
>>>>>>> 06a7f4baa6e5d5db0600f4d213898415243edc8b
class soundplayer:
    def __init__(self):
        self.mqttENDPOINT="a5i03kombapo4-ats.iot.ap-southeast-1.amazonaws.com"
        self.mqttCLIENT_ID= "AIMEGET"
        self.mqttcertfolder="/home/pi/mqtt_client/certs/"
        self.mqttPATH_TO_CERTIFICATE = self.mqttcertfolder + "c86008d5f6f3eb115159777ba9da6c0b97bfdf2309c15020c8d1d2747e4f6bdc-certificate.pem.crt"
        self.mqttPATH_TO_AMAZON_ROOT_CA_1 = self.mqttcertfolder + "AmazonRootCA1.pem"
        self.mqttPATH_TO_PRIVATE_KEY=self.mqttcertfolder + "c86008d5f6f3eb115159777ba9da6c0b97bfdf2309c15020c8d1d2747e4f6bdc-private.pem.key"
<<<<<<< HEAD
        self.mqttTOPIC="amss/{}/prediction".format(LOCATION_ID)
=======
        self.mqttTOPIC="amss/prediction"
>>>>>>> 06a7f4baa6e5d5db0600f4d213898415243edc8b
        self.mqttRANGE=20
        self.MQTTClient = AWSIoTPyMQTT.AWSIoTMQTTClient(self.mqttCLIENT_ID)
        self.MQTTClient.configureEndpoint(self.mqttENDPOINT, 8883)
        self.MQTTClient.configureCredentials(self.mqttPATH_TO_AMAZON_ROOT_CA_1, self.mqttPATH_TO_PRIVATE_KEY, self.mqttPATH_TO_CERTIFICATE)
        self.msgdict = None
<<<<<<< HEAD
        self.currentmasker = 'bird_00075'
        self.currentdoa = 0
=======
        self.currentmasker = None
>>>>>>> 06a7f4baa6e5d5db0600f4d213898415243edc8b
        self.maskerpath = "/home/pi/maskers/"
        self.maskergain = 1
        self.gainweight = 40
        self.maskerdiff =0.5
        self.gainlimit = 2
<<<<<<< HEAD
        self.weightedgain = 1
=======
        self.weightedgain = 0
>>>>>>> 06a7f4baa6e5d5db0600f4d213898415243edc8b
        self.buffersize = 20
        self.blocksize = 2048
        self.q = queue.Queue(maxsize=self.buffersize)
        self.q2 =queue.Queue()
        self.event = threading.Event()
        self.fadelength = 80
        
<<<<<<< HEAD
    def spatialize(self, masker, angle, normalize=True, offset=0.0):
        # masker.shape = (n_samples,) 
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
        x = np.cos(anglerad)
        y = np.sin(anglerad)
        
        lf = 1 + x + y
        lb = 1 - x + y
        rb = 1 - x - y
        rf = 1 + x - y

        
        gains = np.array([rb, lb, lf, rf])
        
        if normalize:
            gains = gains / np.sqrt(8.0)
            
        masker4c = masker[:, None] * gains[None, :] # (n_samples, 4)
        
        return masker4c
    def msgcallback(self, client, userdata, message):
        incomingmsg=json.loads(message.payload.decode('utf-8'))
        self.q2.put_nowait(incomingmsg)
=======

    def msgcallback(self, client, userdata, message):
        incomingmsg=json.loads(message.payload.decode('utf-8'))
        self.q2.put_nowait(incomingmsg)
        # print (incomingmsg)
>>>>>>> 06a7f4baa6e5d5db0600f4d213898415243edc8b
        #print(msgdict['predictions'])
        print("Recommended Masker is: " + str(incomingmsg['predictions'][0]["id"]))
        print("Recommended Gain is: " + str(self.gainweight*incomingmsg['predictions'][0]["gain"]))
        # data, fs = sf.read(msgdict['predictions'][0]["id"]+'.wav', dtype='float32')  
        # sd.play(data, fs, device=1)
    def playmasker(self):
        newmasker = None
        newweightedgain = None
        self.q = queue.Queue(maxsize=self.buffersize)
        if not self.q2.empty():
            self.msgdict = self.q2.get_nowait()
<<<<<<< HEAD
            print(self.msgdict)
=======
>>>>>>> 06a7f4baa6e5d5db0600f4d213898415243edc8b
        if self.msgdict != None:
            if (self.msgdict['predictions'][0]["id"] != self.currentmasker) or (abs(self.msgdict['predictions'][0]["gain"]-self.maskergain)*self.gainweight>self.maskerdiff):
                self.maskergain = self.msgdict['predictions'][0]["gain"]
                if self.maskergain*self.gainweight < self.gainlimit:
                    self.weightedgain = self.maskergain*self.gainweight
                else:
                    self.weightedgain = self.gainlimit
<<<<<<< HEAD
                self.currentdoa = self.msgdict["doa"]
                # self.currentdoa = 0
                # print(type(self.currentdoa))
                self.currentmasker = self.msgdict['predictions'][0]["id"]
        else:
            pass
        try:
            with sf.SoundFile(self.maskerpath + self.currentmasker+'.wav') as f:
                print("stream created using " + self.currentmasker + " at DOA: " + str(self.currentdoa))
                stream = sd.OutputStream(
                    samplerate=f.samplerate, blocksize=self.blocksize,
                    device=7, channels=4,
                    callback=self.streamcallback, finished_callback=self.event.set)
                with stream:
                    timeout = self.blocksize * self.buffersize / f.samplerate
                    for _ in range(int(self.buffersize)):
                        data = self.spatialize(f.read(self.blocksize, always_2d=True)*self.weightedgain, self.currentdoa)
                        if not len(data):
                            break
                        self.q.put_nowait(data)  # Pre-fill queue
                        # print("queue pre-filled")
                    while len(data):
                        if not self.q2.empty():
                            self.msgdict = self.q2.get_nowait()
                            if (self.msgdict['predictions'][0]["id"] != self.currentmasker) or (abs(self.msgdict['predictions'][0]["gain"]-self.maskergain)*self.gainweight>self.maskerdiff):
                                newgain = self.msgdict['predictions'][0]["gain"]
                                if newgain*self.gainweight < self.gainlimit:
                                    newweightedgain = newgain*self.gainweight
                                else:
                                    newweightedgain = self.gainlimit
                                newmasker = self.msgdict['predictions'][0]["id"]
                                newdoa = self.msgdict['doa']
                            else:
                                pass
                        else:
                            pass
                        if (newmasker != self.currentmasker and newmasker != None) or (newweightedgain != None and abs(newweightedgain-self.weightedgain)>self.maskerdiff):
                            fnew = sf.SoundFile(self.maskerpath + newmasker + '.wav')
                            print("Changing - Playing: "+ str(newmasker)+" with gain: " +str(newweightedgain) + " with DOA: " + str(newdoa))
                            for i in range(self.fadelength):
                                track1 = self.spatialize(f.read(self.blocksize, always_2d=True)*(1-(i/self.fadelength))*self.weightedgain, self.currentdoa)
                                track2 = self.spatialize(fnew.read(self.blocksize, always_2d=True)*(i/self.fadelength)*newweightedgain, newdoa)
                                if len(track1) < len(track2) and not self.q.empty():
                                    track1cut = np.zeros((2048,4))
                                    track1cut[:len(track1)] = track1
                                    track1cut[len(track1):].fill(0)
                                    print("track ending")
                                else:
                                    track1cut = track1
                                data = track1cut + track2
                                self.q.put(data, timeout=timeout)
                            f = fnew
                            self.currentmasker = newmasker
                            self.weightedgain = newweightedgain
                            self.currentdoa = newdoa

                            # time.sleep(10)
                        else:
                            # print("reading data")
                            data = self.spatialize(f.read(self.blocksize, always_2d=True)*self.weightedgain,self.currentdoa)
                            self.q.put(data, timeout=timeout)
                    self.event.wait()  # Wait until playback is finished
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

=======
                self.currentmasker = self.msgdict['predictions'][0]["id"]
            try:
                with sf.SoundFile(self.maskerpath + self.currentmasker+'.wav') as f:
                    print("stream created using " + self.currentmasker)
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
                                
                                if (self.msgdict['predictions'][0]["id"] != self.currentmasker) or (abs(self.msgdict['predictions'][0]["gain"]-self.maskergain)*self.gainweight>self.maskerdiff):
                                    newgain = self.msgdict['predictions'][0]["gain"]
                                    if newgain*self.gainweight < self.gainlimit:
                                        newweightedgain = newgain*self.gainweight
                                    else:
                                        newweightedgain = self.gainlimit
                                    newmasker = self.msgdict['predictions'][0]["id"]
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
                                        track1cut = np.zeros((2048,1))
                                        track1cut[:len(track1)] = track1
                                        track1cut[len(track1):].fill(0)
                                        print("track ending")
                                    else:
                                        track1cut = track1
                                    data = track1cut + track2
                                    self.q.put(data, timeout=timeout)
                                f = fnew
                                self.currentmasker = newmasker
                                self.weightedgain = newweightedgain

                                # time.sleep(10)
                            else:
                                # print("reading data")
                                data = f.read(self.blocksize, always_2d=True)*self.weightedgain
                                self.q.put(data, timeout=timeout)
                        self.event.wait()  # Wait until playback is finished
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
        else:
            pass
>>>>>>> 06a7f4baa6e5d5db0600f4d213898415243edc8b
    def streamcallback(self, outdata, frames, time, status):
        data = np.zeros((2048,1))
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