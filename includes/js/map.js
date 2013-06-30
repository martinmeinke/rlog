function RlogInstance(){
    this.controls = {};
}; 
 
/* BASE APPLICATION LOGIC & MQTT EVENT HANDLING */
function Map(){
    var self = this;
    this.mqttClient = undefined;
    this.RlogInstances = {};
    this.reconnect = function(){
      console.log("Reconnecting");
      self.disconnect();
      self.connect(); 
    };
    this.connect = function(){
      self.mqttClient = new Messaging.Client("192.168.8.157", 18883, "rlog-web-"+Math.random().toString(36).substring(6));
      self.mqttClient.onConnectionLost = self.connectionLost;
      self.mqttClient.onMessageArrived = self.messageArrived;
      self.mqttClient.connect({onSuccess:self.connected});
    };
    this.connected = function(response){
      self.mqttClient.subscribe('/devices/+/controls/+/meta/+', 0);
      self.mqttClient.subscribe('/devices/+/controls/+', 0);
      self.mqttClient.subscribe('/devices/+/meta/#', 0);
      window.onbeforeunload = function(){self.disconnect()};
    };
    this.disconnect = function() {
      self.mqttClient.disconnect(); 
    };
    this.disconnected = function() {
      console.log("Connection terminated");      
    };
    this.connectionLost = function(response){ 
      if (response.errorCode !== 0) {
        console.log("onConnectionLost:"+response.errorMessage);
        setTimeout(function () {self.connect();}, 5000); // Schedule reconnect if this was not a planned disconnect
      }
      self.disconnected();
    };
    this.messageArrived = function(message){
      // Topic array parsing:
      // Received string:     /devices/$uniqueDeviceId/controls/$deviceUniqueControlId/meta/type
      // topic array index:  0/      1/              2/       3/                     4/   5/   6

      var payload = message.payloadString;
      var topic = message.destinationName.split("/");
      console.log("-----------RECEIVED-----------\nReceived: "+topic+":"+payload);
      var instance = self.RlogInstances[topic[2]];
      if (!instance){
        instance = new RlogInstance();
        console.log("made new instance");
      }
      if(topic[3] == "controls") {
        // Control value
        if (topic[4] && !topic[5]) {
            !instance.controls[topic[4]] ? instance.controls[topic[4]] = {"value" : payload} : instance.controls[topic[4]].value = payload;
            self.RlogInstances[topic[2]] = instance; 
        }
        // Control meta
        if(topic[5] == "meta"){       
          !instance.controls[topic[4]] ? instance.controls[topic[4]] = {} : instance.controls[topic[4]][topic[6]] = payload;
          instance.controls[topic[4]][topic[6]] = payload;           
          self.RlogInstances[topic[2]] = instance;
        }
      // Device meta
      } else if(topic[3] == "meta"){                                 
        instance[topic[4]] = payload;
      }
    };
};
var map = new Map();
map.connect();
