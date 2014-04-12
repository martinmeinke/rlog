#include <string>
#include "mqtt.h"
#include "inverterReader.h"
#include "smartmeterReader.h"

#ifndef RLOGD_H
#define RLOGD_H

class RLogd {
public:
	explicit RLogd(const std::string& database = "/home/stephan/test.db",
			const std::string& mqtt_hostname = "localhost",
			const unsigned int mqtt_port = 1883,
			const std::string& mqtt_clientID = "MQTTRLOGD",
			const std::string& deviceBaseName = "/dev/ttyUSB",
			const std::string& inverterList = "1,2,3");
	void init();
	void start();
	void stop();

private:
	bool findDevices();
	void onConnect();
	void onDisconnect();
	void onConnectionLost(std::string reason);

	MQTT_Client mqtt;
	InverterReader invReader;
	SmartmeterReader smReader;
	std::string devBaseName;
	std::string invList;
};

#endif
