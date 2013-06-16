  /* BASE APPLICATION LOGIC & MQTT EVENT HANDLING */
  var Application = Backbone.View.extend({
    el: $("body"),
    container: $("#container"),
    roomLinks: $("#room-links > ul"),
    connectivity: $("#connectivity"),

    mqttClient: undefined,
    connectivityTimeoutId: undefined,

    initialize: function() {
      Settings.on('change:connectivity', this.connectivityChanged, this);
      Rooms.on('add', this.addRoom, this);
      Rooms.on('remove', this.removeRoom, this);
      _.bindAll(this, 'connect', 'connected', 'publish', 'publishForDevice', 'connectionLost', 'disconnect', 'disconnected');
      this.addRoom(Devices);
    },
    connectivityChanged: function(e){
      if(this.connectivityTimeoutId)
        clearTimeout(this.connectivityTimeoutId);
      console.log("Connectivity changed to: %s", e.get("connectivity"));
      this.connectivity.removeClass("visible");
      this.connectivity.html(e.get("connectivity"));
      this.connectivity.addClass("visible");
      var that = this; 
      this.connectivityTimeoutId = setTimeout(function(){that.connectivity.removeClass("visible")}, 5000);

    },
    addRoom: function(room) {
      var roomLinkView = new RoomLinkView({model: room});
      this.roomLinks.append(roomLinkView.render().$el);
    },
    removeRoom: function(room) {room.roomLink.close();},
    showView: function(view) {
      if (this.currentView)
        this.currentView.close();
      this.currentView = view;
      this.render(this.currentView);
    },
    render: function(view){
      this.container.html(view.render().$el);
      view.delegateEvents();
      view.finish();
    },
    reconnect: function(){
      console.log("Reconnecting");
      this.disconnect();
      this.connect(); 
    },
    connect: function() {
      Settings.set("connectivity", "connecting");
      this.mqttClient = new Messaging.Client(Settings.get("host"), parseInt(Settings.get("port")), "homA-web-"+Math.random().toString(36).substring(6));
      this.mqttClient.onConnectionLost = this.connectionLost;
      this.mqttClient.onMessageArrived = this.messageArrived;
      this.mqttClient.connect({onSuccess:this.connected});
    },
    connected: function(response){
      Settings.set("connectivity", "connected");
      this.mqttClient.subscribe('/devices/+/controls/+/meta/+', 0);
      this.mqttClient.subscribe('/devices/+/controls/+', 0);
      this.mqttClient.subscribe('/devices/+/meta/#', 0);
      window.onbeforeunload = function(){App.disconnect()};
    },
    disconnect: function() {
      if(Settings.get("connectivity") == "connected")
        this.mqttClient.disconnect(); 
    },
    disconnected: function() {
      Settings.set("connectivity", "disconnected");
      console.log("Connection terminated");

      for (var i = 0, l = Devices.length; i < l; i++)
        Devices.pop();        

      for (i = 0, l = Rooms.length; i < l; i++)
        Rooms.pop();        
    },
    connectionLost: function(response){ 
      if (response.errorCode !== 0) {
        console.log("onConnectionLost:"+response.errorMessage);
        setTimeout(function () {App.connect();}, 5000); // Schedule reconnect if this was not a planned disconnect
      }

      this.disconnected();
    },
    messageArrived: function(message){
      // Topic array parsing:
      // Received string:     /devices/$uniqueDeviceId/controls/$deviceUniqueControlId/meta/type
      // topic array index:  0/      1/              2/       3/                     4/   5/   6

      var payload = message.payloadString;
      var topic = message.destinationName.split("/");
      console.log("-----------RECEIVED-----------\nReceived: "+topic+":"+payload);    
      // Ensure the device for the message exists
      var device = Devices.get(topic[2]);
      if (device == null) {
        device = new Device({id: topic[2]});
        Devices.add(device);
        device.moveToRoom(undefined);
      } 
      if(topic[3] == "controls") {
        var control = device.controls.get(topic[4]);
        if (control == null) {
          control = new Control({id: topic[4]});
          device.controls.add(control);
          control.set("topic", "/devices/"+ topic[2] + "/controls/" + topic[4]);
        } 
        if(topic[5] == null)                                       // Control value   
          control.set("value", payload);
        else if (topic[5] == "meta" && topic[6] != null)           // Control meta 
          control.set(topic[6], payload);
      } else if(topic[3] == "meta" ) {                             // TODO: Could be moved to the setter to facilitate parsing
        if (topic[4] == "room")                                    // Device Room
          device.moveToRoom(payload);
        else if(topic[4] == "name")                                // Device name
          device.set('name', payload);
      }
     console.log("-----------/ RECEIVED-----------");
    },
    publish: function(topic, value) {
      value = value != undefined ? value : "";
      console.log("Publishing " + topic+":"+value);
      var message = new Messaging.Message(value);
      message.destinationName = topic+"/on";
      message.retained = true;
      this.mqttClient.send(message); 
    },
    publishForDevice: function(deviceId, subtopic, value) {
      this.publish("/devices/"+deviceId+subtopic, value);
    }
  });
