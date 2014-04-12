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
	running = true;
	if(findDevices()){
		this_thread::sleep_for(chrono::milliseconds(200));
		// main loop
		while(running){
			chrono::system_clock::time_point start = chrono::system_clock::now();
			auto inverterReading = async(&InverterReader::read, invReader);
			auto smartmeterReading = async(&SmartmeterReader::read, smReader);
			for(auto element : inverterReading.get())
				FILE_LOG(logDEBUG) << "got from inverter: " << element;
			for(auto element : smartmeterReading.get())
							FILE_LOG(logDEBUG) << "got from inverter: " << element;
			chrono::milliseconds duration = chrono::duration_cast<chrono::milliseconds>(chrono::system_clock::now() - start);
			if(duration > chrono::milliseconds(10000)){
				FILE_LOG(logDEBUG) << "timing critical. iteration took " << duration.count() / 1000 << " seconds";
			} else {
				this_thread::sleep_for(chrono::milliseconds(10000) - duration);
			}
		}
	}
}

void RLogd::stop() {
	running = false;
	try{
		mqtt.disconnect();
	} catch (runtime_error &e){
		FILE_LOG(logERROR) << "mqtt disconnect  error: " << e.what();
	}
}

bool RLogd::findDevices() {
	FILE_LOG(logINFO) << "start discovering devices";
	bool smartMeterDeviceFound = false, inverterDeviceFound = false;
	for (unsigned short i = 0; (i < 10) and not (smartMeterDeviceFound and inverterDeviceFound); i++) {
		this_thread::sleep_for(chrono::milliseconds(200));
		if ((not smartMeterDeviceFound) and smReader.openDevice(devBaseName + toString<unsigned short>(i))) {
			smartMeterDeviceFound = true;
			// fake 3 smart meter
			try{
				mqtt.publish("/devices/RLog/controls/VSM-102 (1)/meta/type", "text", 0, true);
				mqtt.publish("/devices/RLog/controls/VSM-102 (2)/meta/type", "text", 0, true);
				mqtt.publish("/devices/RLog/controls/VSM-102 (3)/meta/type", "text", 0, true);
			} catch (runtime_error &e){
				FILE_LOG(logERROR) << "mqtt publish error in " << __func__ << ": " << e.what();
			}
			FILE_LOG(logINFO) << "Discovered smart meter at " << devBaseName << i;
			continue;
		}
		if ((not inverterDeviceFound) and invReader.openDevice(devBaseName + toString<unsigned short>(i))) {
			if (invReader.findInverter(invList)) {
				inverterDeviceFound = true;
				try{
					for(auto element : split(invList, ','))
						mqtt.publish(string("/devices/RLog/controls/3002IN (") + element + string(")/meta/type"), "text", 0, true);
				}catch (runtime_error &e){
					FILE_LOG(logERROR) << "mqtt publish error in " << __func__ << ": " << e.what();
				}
				FILE_LOG(logINFO) << "Discovered inverter at " << devBaseName << i;
			}
		}
	}
	return smartMeterDeviceFound and inverterDeviceFound;
}


void RLogd::onConnect() {
	FILE_LOG(logINFO) << "MQTT connected";
	try{
		mqtt.publish("/devices/RLog/meta/name", "Rlog", 0, true);
		mqtt.publish("/devices/RLog/meta/locationX", LOCATIONX, 0, true);
		mqtt.publish("/devices/RLog/meta/locationY", LOCATIONY, 0, true);
	} catch (runtime_error &e){
		FILE_LOG(logERROR) << "mqtt publish error in " << __func__ << ": " << e.what();
	}
}

void RLogd::onDisconnect() {
	FILE_LOG(logINFO) << "MQTT disconnected";
}

void RLogd::onConnectionLost(string reason) {
	FILE_LOG(logERROR) << "MQTT connection lost because of " << reason;
}
