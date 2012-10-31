import thread, mosquitto, random

class mqtt():    
    def __init__(self, broker = "127.0.0.1", port = 1883):
        self.__broker = broker
        self.__port = port
        self._client = None
        self.__subscriptionsList = []
        self.__pendingSubscriptionsList = []
        self.__pendingUnsubscriptionsList = []
        self.__connected = False
    
    def subscribe(self, topic, QoS = 0):
        if(self.__connected):
            self._client.subscribe(topic, QoS)
            self.__subscriptionsList.append(topic)
            print "Subscribing to " + topic
        else:
            self.__pendingSubscriptionsList.append((topic, QoS))
            print "Client is not connected at the moment. Will subscribe on connection"
    
    def unsubscribe(self, topic):
        if(self.__connected):
            self.__subscriptionsList.remove(topic)
            self._client.unsubscribe(topic)
            print "Unsubscribing from " + topic
        else:
            self.__pendingUnsubscriptionsList.append(topic)
            print "Client is not connected at the moment. Will unsubscribe on connection"
            
    def publish(self, topic, message):
        self._client.publish(topic, message)
    
    # override this methods to add your functionality
    def on_connect(self, rc):
#        print "on_connect", rc
        pass
    
    def on_disconnect(self):
#        print "on_disconnect"
        pass
            
    def on_subscribe(self, mid, qos_list):
#        print "on_subscribe", mid, qos_list
        pass
        
    def on_unsubscribe(self, mid):
#        print "on_unsubscribe", mid
        pass
    
    def on_publish(self, mid):
#        print "on_publish", mid
        pass
            
    def on_message(self, msg):
#        print "Message received on topic " + msg.topic + " with QoS " + str(msg.qos) + " and payload " + msg.payload
        pass

    # actual MQTT callbacks
    def __on_connect(self, mosquitto_instance, rc):
        #rc 0 successful connect
        if rc == 0:
            print "MQTT Connected"
            self.__connected = True;
            while(len(self.__pendingSubscriptionsList) != 0):
                (topic, QoS) = self.__pendingSubscriptionsList.pop()
                print "executing pending subscription to " + topic + " with QoS " + str(QoS)
                self.subscribe(topic, QoS)
            while(len(self.__pendingUnsubscriptionsList) != 0):
                topic = self.__pendingUnsubscriptionsList.pop()
                print "executing pending unsubscription from " + topic
                self.unsubscribe(topic)
            self.on_connect(rc)
        else:
            print "We have an error here. Cleaning up ..."
            self.__cleanup()
                  
    def __on_disconnect(self, mosquitto_instance):
        self.__connected = False
        print "Disconnected successfully."
        self.on_disconnect()
            
    def __on_subscribe(self, mosquitto_instance, mid, qos_list):
        self.on_subscribe(mid, qos_list)
    
    def __on_unsubscribe(self,mosquitto_instance, mid):
        self.on_unsubscribe(mid)
    
    def __on_publish(self, mosquitto_instance, mid):
        self.on_publish(mid)
    
    def __on_message(self, mosquitto_instance, message):
        self.on_message(message)

    #called on exit
    # disconnect MQTT and clean up subscriptions
    def __cleanup(self):
        print "Ending and cleaning up"
        while(len(self.__subscriptionsList) != 0):
                topic = self.__subscriptionsList[0]
                self.unsubscribe(topic)
        self._client.disconnect()
    
    def loop(self):
        while self._client.loop(-1) == 0:
            pass
    
    def startMQTT(self):
        try: 
            client_uniq = "rlog" + str(random.randint(0, 1000))
            self._client = mosquitto.Mosquitto(client_uniq)
            
            #attach MQTT callbacks
            self._client.on_connect = self.__on_connect
            self._client.on_disconnect = self.__on_disconnect
            self._client.on_subscribe = self.__on_subscribe
            self._client.on_unsubscribe = self.__on_unsubscribe
            self._client.on_publish = self.__on_publish
            self._client.on_message = self.__on_message

            #connect to broker
            self._client.connect(self.__broker, self.__port, 60, True)
            
            #remain connected to broker 
              # stupid that it doesn't work w/o that silly loop
            thread.start_new_thread(self.loop, ())
    
        except (RuntimeError):
            print "uh-oh! time to die"
            self.__cleanup()
            
    def stopMQTT(self):
        self.__cleanup()
