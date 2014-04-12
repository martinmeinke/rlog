#include <cstdlib>
#include "rlogd.h"
#include <iostream>
#include <functional>
#include <list>
#include <string>
#include <sqlite3.h>
#include <thread>
#include <future>
#include <chrono>
#include "util.h"
#include "log.h"


#define LOCATIONX "14.122994"
#define LOCATIONY "52.508519"

using namespace std;

RLogd::RLogd(const string& database, const string& mqtt_hostname,
		const unsigned int mqtt_port, const string& mqtt_clientID,
		const string& deviceBaseName, const string& inverterList) :
		mqtt(mqtt_clientID, mqtt_hostname, mqtt_port), devBaseName(
				deviceBaseName), invList(inverterList) {
}

void RLogd::init() {
	mqtt.ConnectCallback = bind(&RLogd::onConnect, this);
	mqtt.DisconnectCallback = bind(&RLogd::onDisconnect, this);
	mqtt.ConnectionLostCallback = bind(&RLogd::onConnectionLost, this, placeholders::_1);

	try{
		mqtt.connect();
	} catch (runtime_error &e){
		FILE_LOG(logERROR) << "mqtt connect failed: " << e.what();
	}
}

void RLogd::start(){
	findDevices();
}

void RLogd::stop() {
	try{
		mqtt.disconnect();
	} catch (runtime_error &e){
		FILE_LOG(logERROR) << "mqtt disconnect  error: " << e.what();
	}
}

void RLogd::findDevices() {
	FILE_LOG(logINFO) << "start discovering devices";
	bool smartMeterDeviceFound = false, inverterDeviceFound = false;
	for (unsigned short i = 0; (i < 10) and not (smartMeterDeviceFound and inverterDeviceFound); i++) {
		this_thread::sleep_for(chrono::milliseconds(200));
		if ((not smartMeterDeviceFound) and smReader.openDevice(devBaseName + toString<unsigned short>(i))) {
			smartMeterDeviceFound = true;
			FILE_LOG(logINFO) << "Discovered smart meter at " << devBaseName << i;
			continue;
		}
		if ((not inverterDeviceFound) and invReader.openDevice(devBaseName + toString<unsigned short>(i))) {
			if (invReader.findInverter(invList)) {
				inverterDeviceFound = true;
				FILE_LOG(logINFO) << "Discovered inverter at " << devBaseName << i;
			}
		}
	}
}


void RLogd::onConnect() {
	FILE_LOG(logINFO) << "MQTT connected";
	mqtt.publish("/devices/RLog/meta/name", "Rlog", 0, true);
	mqtt.publish("/devices/RLog/meta/locationX", LOCATIONX, 0, true);
	mqtt.publish("/devices/RLog/meta/locationY", LOCATIONY, 0, true);
}

void RLogd::onDisconnect() {
	FILE_LOG(logINFO) << "MQTT disconnected";
}

void RLogd::onConnectionLost(string reason) {
	FILE_LOG(logERROR) << "MQTT connection lost because of " << reason;
}
