import paho.mqtt.client as mqtt_client
import logging
import time
import threading

"""
wbec/lp/1/status  -> publish    
A - Charger ready, no vehicle
B - waiting for vehicle
C - charging

wbec/lp/1/enabled -> publish

wbec/lp/1/maxcurrent -> subscribe

wbec/lp/1/enable -> subscribe


"""

class mqtt():

    def onconnect(client, userdata, flags, rc):
        userdata.logger.debug("Connect successful with code " + str(rc))
        if rc==0:
            client.subscribe("wbec/lp/1/enable")
            client.subscribe("wbec/lp/1/maxcurrent")
            client.publish("wbec/lp/1/status", payload=userdata.wbs[0].get_state_as_letter(), qos=0, retain=True)
        else:
            userdata.logger.debug("Connect not working, error code" + rc)
        

    def onmessage(client, userdata, message):
        message_received=str(message.payload.decode("utf-8"))
        userdata.logger.debug("Message received, topic" + message.topic + " payload " + message_received)
	
        if message.topic == "wbec/lp/1/maxcurrent":
            userdata.wbs[0].set_current_preset(int(message_received))
            userdata.wbs[0].allow(message_received != "0")
            if(message_received != "0"):
                userdata.previous_current = int(message_received)
            #userdata.wbs[0].set_current_preset(int(message_received))
        if message.topic == "wbec/lp/1/enable":
            if message_received.lower() == "false":
                userdata.wbs[0].set_current_preset(0)
                userdata.wbs[0].allow(False)
            else: 
                userdata.wbs[0].allow(True)
                userdata.wbs[0].set_current_preset(userdata.previous_current)
                

            client.publish("wbec/lp/1/enabled", payload=message.payload, qos=0, retain=True)
        # Always share status
        client.publish("wbec/lp/1/status", payload=userdata.wbs[0].get_state_as_letter(), qos=0, retain=True)
        # client.publish("hdec", payload="topic " + message.topic +  " "+ "message received " + str(message.payload), qos=0, retain=False)
            
    def __init__(self, wbs, host, user, pwd):
        self.previous_current = 6
        self.logger = logging.getLogger("hdec") 
        self.logger.debug("Starting MQTT client " + str(wbs))
        self.wbs = wbs
        client = mqtt_client.Client("hdec")
        client.username_pw_set(user, password=pwd)
        client.user_data_set(self)
        client.on_message = mqtt.onmessage
        client.on_connect = mqtt.onconnect
        try:
            client.connect(host)
        except:
            self.logger.debug("onConnect failed")
        client.loop_start()
        self.logger.debug("MQTT Connected")
        def polling():
 
            while True:
                client.publish("wbec/lp/1/status", payload=wbs[0].get_state_as_letter(), qos=0, retain=True)
                time.sleep(30)
        poll=threading.Thread(target=polling)
        poll.start()
