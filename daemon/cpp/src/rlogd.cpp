#include <cstdlib>
#include "rlogd.h"
#include <iostream>
#include <functional>
#include <list>
#include <string>
#include <sqlite3.h>
#include "util.h"

using namespace std;

RLogd::RLogd(const string& database, const string& mqtt_hostname,
		const unsigned int mqtt_port, const string& mqtt_clientID, const string& deviceBaseName) :
		mqtt(mqtt_clientID, mqtt_hostname, mqtt_port), devBaseName(deviceBaseName) {
}

void RLogd::init() {
	mqtt.ConnectCallback = bind(&RLogd::onConnect, this);
	mqtt.DisconnectCallback = bind(&RLogd::onDisconnect, this);
	mqtt.ConnectionLostCallback = bind(&RLogd::onConnectionLost, this,
			placeholders::_1);
	mqtt.SubscribeCallback = bind(&RLogd::onSubscribe, this, placeholders::_1);
	mqtt.MessageCallback = bind(&RLogd::onMessage, this, placeholders::_1,
			placeholders::_2, placeholders::_3, placeholders::_4);
	mqtt.UnsubscribeCallback = bind(&RLogd::onUnsubscribe, this);

	try{
		mqtt.connect();
	} catch (runtime_error &e){
		cerr << "mqtt connect failed: " << e.what() << endl;;
	}
}

void RLogd::start(){
	list<string> topics = { "/devices/Switch 1/#", "/devices/Switch 2/#" };
	try{
		mqtt.unsubscribe(topics);
	} catch (runtime_error &e){
		cerr << "mqtt unsubscribe error: " << e.what() << endl;;
	}
}

void RLogd::stop() {
	try{
		mqtt.disconnect();
	} catch (runtime_error &e){
		cerr << "mqtt disconnect  error: " << e.what() << endl;;
	}
}


/*
 *     # try all device starting with DEVICE_NAME_BASE and try to talk to the smart meter if it exists (if smart meter is enabled).
    # if smart meter is found (or smartmeter is not enabled) try the first device starting with DEVICE_NAME_BASE and assume it is the rs485 adapter for the WR (make sure to skip smart meter adapter if present)
    def discover_device(self):
        smart_meter_device = -1 # to be excluded in the second run
        if self._smart_meter_enabled:
            log("Searching for device where the smart meter responds")
            for device_id in range(0, 100):
                log("Checking if %s%d exists ..." % (DEVICE_NAME_BASE, device_id))
                if os.path.exists("%s%d" % (DEVICE_NAME_BASE, device_id)):
                    smart_meter_device_name = "%s%d" % (DEVICE_NAME_BASE, device_id)
                    log("trying device: %s as smart meter device" % smart_meter_device_name)
                    self._smart_meter_serial_port = serial.Serial(smart_meter_device_name, baudrate = 9600, stopbits = serial.STOPBITS_ONE, timeout = 1)
                    if self.findSmartMeter():
                        log("Using %s for smart meter" % smart_meter_device_name)
                        smart_meter_device = device_id
                        break
        log("Searching rs485 device for WR")
        for device_id in range(0, 100):
            if device_id == smart_meter_device:
                continue
            log("Checking if %s%d exists..." % (DEVICE_NAME_BASE, device_id))
            if os.path.exists("%s%d" % (DEVICE_NAME_BASE, device_id)):
                WR_device_name = "%s%d" % (DEVICE_NAME_BASE, device_id)
                log("Using device: %s" % WR_device_name)
                self._WR_serial_port = serial.Serial(port=WR_device_name, baudrate = 9600, stopbits = serial.STOPBITS_ONE, timeout = 1)
                return
        log("Unable to find WR serial port")
 */


void RLogd::findDevices() {
	for(int i = 0; i < 10; i++){
		// TODO: dinf devices
	}
}

void RLogd::test() {
	if(invReader.openDevice("/dev/ttyUSB0"))
		while(true){
			auto ret = invReader.read();
			if(ret.size())
				for (auto c : ret)
					cout << "read:" << trim(c) << endl;;
		}
	else
		cerr << "can't open test device" << endl;

}

void RLogd::onConnect() {
	cout << "MQTT connected" << endl;
	mqtt.subscribe("/devices/RLog/controls/Erzeugung");
	mqtt.subscribe(string("/devices/RLog/controls/Nutzung"));
	list<string> topics = { "/devices/Switch 1/#", "/devices/Switch 2/#",
			"/devices/Switch 3/#" };
	mqtt.subscribe(topics);
}

void RLogd::onDisconnect() {
	cout << "MQTT disconnected" << endl;
}

void RLogd::onConnectionLost(string reason) {
	cout << "MQTT connection lost because of " << reason << endl;
}

void RLogd::onSubscribe(int QoS) {
	cout << "MQTT subscribed with QoS " << QoS << endl;
}

void RLogd::onMessage(std::string topic, std::string payload, int QoS,
		bool retained) {
	cout << string(retained ? "Retained " : "")
			<< "MQTT message received with QoS " << QoS << " on topic " << topic
			<< ": " << payload << endl;
}

void RLogd::onUnsubscribe() {
	cout << "MQTT unsubscribed with QoS " << endl;
}
