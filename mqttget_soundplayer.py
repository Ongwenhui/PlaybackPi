import json
import AWSIoTPythonSDK.MQTTLib as AWSIoTPyMQTT
#from PIL import Image
from io import BytesIO
import numpy as np
import sounddevice as sd 
import soundfile as sf


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
        self.currentmasker = None
        self.maskerpath = "/home/pi/maskers/"
        self.maskergain = 1
        self.gainweight = 30
        self.maskerdiff =0.3
        

    def msgcallback(self, client, userdata, message):
        self.msgdict=json.loads(message.payload.decode('utf-8'))
        #print(msgdict['predictions'])
        print("Recommended Masker is: " + str(self.msgdict['predictions'][0]["id"]))
        print("Recommended Gain is: " + str(self.gainweight*self.msgdict['predictions'][0]["gain"]))
        # data, fs = sf.read(msgdict['predictions'][0]["id"]+'.wav', dtype='float32')  
        # sd.play(data, fs, device=1)
    def playmasker(self):
        if self.msgdict != None:
            if (self.msgdict['predictions'][0]["id"] != self.currentmasker) or (abs(self.msgdict['predictions'][0]["gain"]-self.maskergain)*self.gainweight>self.maskerdiff):
                self.maskergain = self.msgdict['predictions'][0]["gain"]
                self.data, self.fs = sf.read(self.maskerpath + self.msgdict['predictions'][0]["id"]+'.wav', dtype='float32')  
                sd.play(self.data*(self.gainweight*self.maskergain), self.fs, device=1,loop = True)
                # for item in self.data:
                #     #print("checking")
                #     if abs(item) > 1:
                #         print (item)
                self.currentmasker = self.msgdict['predictions'][0]["id"]
                print("Changing - Playing: "+ str(self.currentmasker)+" with gain: " +str(self.gainweight*self.maskergain))
                
            else:
                #print("Continuing to play: "+ str(self.currentmasker)+" with gain: " +str(self.gainweight*self.maskergain))
                pass
        else:
            pass

sp = soundplayer()

sp.MQTTClient.connectAsync()
print("connected")


while True:
    sp.MQTTClient.subscribeAsync(sp.mqttTOPIC, 0,messageCallback = sp.msgcallback)
    sp.playmasker()