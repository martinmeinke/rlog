function RlogInstance(){
    this.controls = {};
}; 
 
/* BASE APPLICATION LOGIC & MQTT EVENT HANDLING */
function Map(containerName){
    var self = this;
    this.mqttClient = undefined;
    this.RlogInstances = {};
    this.openlayersMap = undefined;
    this.initOpenLayersMap = function(containerName){
        OpenLayers.ImgPath = "/static/img/OpenLayers/";
        this.openlayersMap = new OpenLayers.Map(document.getElementById(containerName), {allOverlays: true, theme: "/static/css/OpenLayers/style.css"});
        this.openlayersMap.addControl(new OpenLayers.Control.LayerSwitcher());
        
        // the SATELLITE layer has all 22 zoom level, so we add it first to
        // become the internal base layer that determines the zoom levels of the
        // map.
        var gsat = new OpenLayers.Layer.Google(
            "Google Satellite",
            {type: google.maps.MapTypeId.SATELLITE, numZoomLevels: 22, visibility: false}
        );
        var gphy = new OpenLayers.Layer.Google(
            "Google Physical",
            {type: google.maps.MapTypeId.TERRAIN, visibility: false}
        );
        var gmap = new OpenLayers.Layer.Google(
            "Google Streets", // the default
            {numZoomLevels: 20, visibility: false}
        );
        var ghyb = new OpenLayers.Layer.Google(
            "Google Hybrid",
            {type: google.maps.MapTypeId.HYBRID, numZoomLevels: 22, visibility: true}
        );

        this.openlayersMap.addLayers([ghyb, gsat, gphy, gmap]);

        // Google.v3 uses EPSG:900913 as projection, so we have to
        // transform our coordinates
        this.openlayersMap.setCenter(new OpenLayers.LonLat(10.2, 48.9)
                                    .transform(new OpenLayers.Projection("EPSG:4326"), 
                                               this.openlayersMap.getProjectionObject())
                                , 5);
    };
    this.reconnect = function(){
      console.log("Reconnecting");
      self.disconnect();
      self.connect(); 
    };
    this.connect = function(){
      self.mqttClient = new Messaging.Client("localhost", 18883, "rlog-web-"+Math.random().toString(36).substring(6));
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
      console.log("this is the new / updated one:", instance);
    };
    this.initOpenLayersMap(containerName);
};

var map = undefined;
$(document).ready(function() {
    map = new Map('mapDiv');
    map.connect();
});

