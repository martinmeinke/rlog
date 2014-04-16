#include <string>
#include "mqtt.h"
#include "inverterReader.h"
#include "smartmeterReader.h"
#include <sqlite3.h>

#ifndef RLOGD_H
#define RLOGD_H

class RLogd {
public:
	explicit RLogd(const std::string& database = "/home/stephan/test.db",
			const std::string& mqtt_hostname = "localhost",
			const unsigned int mqtt_port = 1883,
			const std::string& mqtt_clientID = "MQTTRLOGD",
			const std::string& deviceBaseName = "/dev/ttyUSB",
			const std::string& inverterList = "1,2,3",
			const unsigned int timing = 10000,
			const unsigned short maxDeviceID = 1);
	void init();
	void start();
	void stop();

	static bool running;

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
	std::string database;
	unsigned int interval;
	unsigned short maxDevice;
	sqlite3 * db_connection = nullptr;
	sqlite3_stmt * insertDevice = nullptr;
	sqlite3_stmt * insertInverterTick = nullptr;
	sqlite3_stmt * inserSmartmeterTick = nullptr;
};

#endif
