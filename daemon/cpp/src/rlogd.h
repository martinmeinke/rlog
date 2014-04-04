#include <string>
#include "mqtt.h"
#include "util.h"
#include <sqlite3.h>
#include <SerialStream.h>

#ifndef RLOGD_H
#define RLOGD_H

class RLogd {
public:
	explicit RLogd(const std::string& database = "/home/stephan/test.db",
			const std::string& mqtt_hostname = "localhost",
			const unsigned int mqtt_port = 1883,
			const std::string& mqtt_clientID = "MQTTRLOGD");
	void start();
	void stop();

private:
	void onConnect();
	void onDisconnect();
	void onConnectionLost(std::string reason);
	void onSubscribe(int QoS);
	void onUnsubscribe();
	void onMessage(std::string topic, std::string payload, int QoS,
			bool retained);

	MQTT_Client mqtt;
	LibSerial::SerialStream serial_WR;
	LibSerial::SerialStream serial_SM;
};

#endif
